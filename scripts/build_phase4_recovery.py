"""Report recovered Phase 3 raw evidence and the newly replayed R76 control."""
import argparse
from collections import defaultdict
import csv
from math import isfinite
from pathlib import Path
from statistics import median

from package_support import ROOT, sha256, verify_package
from phase4_diagnostics import analyze_bundle, read_json, write_json
from run_phase4_control import declaration


FILL_LOG = 'engine/baseline/baseline_transaction_log.csv'


def fill_slippage(fills):
    """Observed price concession to the fill-time quote; not a counterfactual run."""
    by_symbol = defaultdict(float)
    rows = 0
    for fill in fills:
        price, quote, volume = float(fill['Price']), float(fill['Market Price']), int(fill['Volume'])
        if (fill['Type'] != 'Market' or fill['Side'] not in ('Buy', 'Sell')
                or not isfinite(price) or not isfinite(quote) or min(price, quote) <= 0
                or volume <= 0 or volume % 100):
            raise ValueError('Expected valid market IOC fill and fill-time quote')
        amount = (price - quote if fill['Side'] == 'Buy' else quote - price) * volume
        if amount < -1e-7:
            raise ValueError('Unexpected favorable fill under the pinned adverse-tick model')
        by_symbol[fill['Symbol']] += amount
        rows += 1
    return {'filled_price_concession_thb': sum(by_symbol.values()),
            'by_symbol_thb': dict(sorted(by_symbol.items())), 'fill_rows': rows,
            'basis': 'TransactionLog Market Price = Order.fill_market_price = execution tick LastPrice',
            'limitation': 'Same observed fills only; excludes opportunity cost and endogenous changes in fills/cash'}


def verified_hashes(folder, expected):
    for path, digest in expected.items():
        if sha256(folder / path) != digest:
            raise ValueError(f'Artifact hash mismatch: {folder.name}/{path}')
    return dict(expected)


def lot_summary(raw):
    ages = [lot['holding_sessions'] for lot in raw['completed_lots']]
    return {'completed_lots': len(ages),
            'min_holding_sessions': min(ages) if ages else None,
            'median_holding_sessions': median(ages) if ages else None,
            'max_holding_sessions': max(ages) if ages else None,
            'meaning': 'First fill to final close, counting subsequent replay sessions; excludes still-open lots'}


def collect(suite, control):
    package = verify_package()
    manifest = declaration()
    evidence = read_json(ROOT / 'docs/result-data-visualisation/phase-3-results.json')
    recovered = {}
    for key, original in sorted(evidence['runs'].items()):
        folder = suite / key
        hashes = verified_hashes(folder, original['hashes'])
        raw = analyze_bundle(folder, original)
        with (folder / FILL_LOG).open(newline='', encoding='utf-8-sig') as stream:
            slippage = fill_slippage(csv.DictReader(stream))
        raw['slippage_attribution'] = 'Observed fill-time price concession is in fill_price_concession'
        raw['limitation'] = 'Intraday adverse excursions and entry-quality causality are not established'
        p = original['performance']
        capital = original['configuration']['parameters']['initial_capital_thb']
        recovered[key] = {'identical_artifacts': len(hashes), 'hashes': hashes,
                          'performance': p, 'raw_diagnostics': raw, 'lot_summary': lot_summary(raw),
                          'fill_price_concession': slippage,
                          'same_fills_fees_and_concession_added_back_return_pct':
                          (p['final_nav_thb'] - capital + p['fees_thb']
                           + slippage['filled_price_concession_thb']) / capital * 100}
    experiment = read_json(control / 'experiment.json')
    if (experiment['state'] != 'completed' or experiment['exit_code'] != 0
            or experiment['declaration'] != manifest
            or experiment['manifest_sha256'] != sha256(ROOT / 'research/phase4/manifest.json')):
        raise ValueError('R76 is incomplete or does not match its pre-run declaration')
    folder = control / 'run'
    hashes = read_json(folder / 'reproducible-hashes.json')
    if set(hashes) != set(evidence['runs']['C1']['hashes']):
        raise ValueError('R76 bundle is incomplete')
    verified_hashes(folder, hashes)
    report = read_json(folder / 'report.json')
    config = report['configuration']
    if config['parameters'] != read_json(ROOT / manifest['config']):
        raise ValueError('R76 used different parameters')
    if config['companion_config_sha256'] != manifest['source_sha256'][manifest['config']]:
        raise ValueError('R76 companion hash differs from declaration')
    for key, digest in config['code_sha256'].items():
        if sha256(ROOT / key) != digest:
            raise ValueError(f'R76 source changed: {key}')
    for key in ('archive_sha256', 'package_tree_sha256', 'days', 'dependencies', 'event_order', 'python'):
        if config[key] != evidence['runs']['C1']['configuration'][key]:
            raise ValueError(f'R76 comparison input differs: {key}')
    if not all(d['reconciliation']['reconciled'] for d in report['daily']):
        raise ValueError('R76 contains an unreconciled session')
    # Reuse the same full FIFO reconciliation as the historical raw bundles.
    raw = analyze_bundle(folder, {**report, 'hashes': hashes})
    with (folder / FILL_LOG).open(newline='', encoding='utf-8-sig') as stream:
        slippage = fill_slippage(csv.DictReader(stream))
    raw['slippage_attribution'] = 'Observed fill-time price concession is in fill_price_concession'
    raw['limitation'] = 'Intraday adverse excursions and entry-quality causality are not established'
    p = report['performance']
    baseline = evidence['historical']['retained']['performance']
    comparisons = {}
    for key in ('C2', 'C3'):
        candidate = recovered[key]['performance']
        exposure_gap = (candidate['average_exposure'] - p['average_exposure']) * 100
        comparisons[key] = {
            'candidate_minus_R76_net_return_pp': candidate['net_return_pct'] - p['net_return_pct'],
            'candidate_minus_R76_average_exposure_pp': exposure_gap,
            'exposure_gap_within_two_pp': abs(exposure_gap) <= 2,
            'causal_signal_attribution': False,
            'reason': 'Baskets, quantity anchors and guard policies differ; paired controls remain pending'}
    return {'sample_role': 'reused_development', 'validation_complete': False,
            'package': package, 'recovered_runs': recovered,
            'R76': {'performance': p, 'eligibility': report['eligibility'],
                    'user_targets': report['user_targets'], 'raw_diagnostics': raw,
                    'fill_price_concession': slippage, 'lot_summary': lot_summary(raw),
                    'hashes': hashes, 'configuration': config,
                    'daily': [{'date': d['date'], 'performance': d['performance'],
                               'closing_risk': d['closing_risk']} for d in report['daily']],
                    'max_daily_seconds': max(read_json(folder / 'environment.json')['daily_seconds'].values()),
                    'net_return_change_from_original_pp': p['net_return_pct'] - baseline['net_return_pct'],
                    'average_exposure_change_from_original_pp':
                    (p['average_exposure'] - baseline['average_exposure']) * 100},
            'comparisons': comparisons,
            'decision': 'retain_original_reference_no_candidate_promoted',
            'provenance': {'phase3_evidence_sha256': sha256(ROOT / 'docs/result-data-visualisation/phase-3-results.json'),
                           'R76_manifest_sha256': sha256(ROOT / 'research/phase4/manifest.json'),
                           'code_sha256': {path: sha256(ROOT / path) for path in
                                          ('scripts/build_phase4_recovery.py', 'scripts/phase4_diagnostics.py',
                                           'scripts/phase3_reporting.py', 'scripts/package_support.py',
                                           'scripts/run_phase4_control.py')},
                           'slippage_source_sha256': {path: sha256(ROOT / '.local/tradesim-0.2.7' / path)
                                                     for path in ('tradeSim/Order.py', 'tradeSim/TransactionLog.py')}}}


def markdown(result):
    p = result['R76']['performance']
    value = lambda v: 'Undefined' if v is None else f'{v:,.4f}'
    lines = ['# Phase 4 restored-engine results', '',
             '30 October 2026 (Asia/Bangkok). Same September 9–30 development sample; '
             'no untouched validation or candidate promotion.', '',
             'The reuploaded archive matches the original checksum and 536-file tree. '
             'All ten Phase 3 runs were replayed; all nine deterministic artifacts per run '
             'match the committed hashes (90/90). Wall-clock runtime is excluded.', '',
             '## R76: original reference with only the target raised to 76%', '',
             '| Metric | Measured |', '| --- | ---: |']
    for label, key in (
        ('Net return (%)', 'net_return_pct'), ('SET50 excess return (pp)', 'excess_return_pp'),
        ('First-close-aligned excess (pp)', 'aligned_first_close_excess_pp'),
        ('Official maximum drawdown (%)', 'official_max_drawdown_pct'),
        ('Initial-capital maximum drawdown (%)', 'initial_capital_max_drawdown_pct'),
        ('SET50 return (%)', 'benchmark_return_pct'), ('SET50 maximum drawdown (%)', 'benchmark_max_drawdown_pct'),
        ('Average closing exposure (%)', 'average_exposure'), ('Distinct stocks', 'distinct_stocks'),
        ('Completed FIFO lots', 'completed_fifo_round_trips'), ('Expected payoff (THB)', 'expected_payoff_thb'),
        ('Commission/VAT (THB)', 'fees_thb'), ('Realized P&L (THB)', 'realized_pnl_thb'),
        ('Unrealized P&L (THB)', 'unrealized_pnl_thb'),
    ):
        observed = p[key] * 100 if key == 'average_exposure' else p[key]
        formatted = str(observed) if key in ('distinct_stocks', 'completed_fifo_round_trips') else value(observed)
        lines.append(f'| {label} | {formatted} |')
    lines += ['', f'Common criteria: **{result["R76"]["eligibility"]["common_status"]}**; '
              f'Best Alpha: **{result["R76"]["eligibility"]["best_alpha_status"]}**. '
              'No sample-end liquidation or artificial round trips.', '',
              f'Against the original 70%-target reference, net return changes by '
              f'{result["R76"]["net_return_change_from_original_pp"]:+.6f} pp and '
              f'average exposure changes by {result["R76"]["average_exposure_change_from_original_pp"]:+.6f} pp.', '',
              '| Candidate | Net return minus R76 (pp) | Average exposure minus R76 (pp) | Within 2 pp exposure |',
              '| --- | ---: | ---: | --- |']
    for key, c in result['comparisons'].items():
        lines.append(f'| {key} | {c["candidate_minus_R76_net_return_pp"]:+.6f} | '
                     f'{c["candidate_minus_R76_average_exposure_pp"]:+.6f} | '
                     f'{c["exposure_gap_within_two_pp"]} |')
    lines += ['', 'These are portfolio comparisons. Different baskets, quantity anchors and guard policies '
              'prevent attributing the differences to signals. Equal-weight and passive paired controls remain pending.', '',
              '## Actual fills: costs and completed-lot horizons', '',
              '| ID | Fees THB | Price concession THB | Fees/concession added back % | Completed lots | Median holding sessions |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for key, run in result['recovered_runs'].items():
        lines.append(f'| {key} | {run["performance"]["fees_thb"]:,.2f} | '
                     f'{run["fill_price_concession"]["filled_price_concession_thb"]:,.2f} | '
                     f'{run["same_fills_fees_and_concession_added_back_return_pct"]:.6f} | '
                     f'{run["lot_summary"]["completed_lots"]} | '
                     f'{value(run["lot_summary"]["median_holding_sessions"])} |')
    lines += ['', 'Price concession is quantity × (fill price − fill-time quote) for buys, and '
              'quantity × (quote − fill price) for sells. The verified engine records the execution '
              'tick LastPrice in `Market Price`. Adding these costs back keeps fills and final marks fixed; '
              'it is not a zero-cost replay, future-profit forecast or estimate of opportunity cost.', '',
              'Holding sessions count from the first buy fill to final lot completion. Partial and still-open '
              'lots are excluded from the completed-lot median. Counts are not independent trading ideas.', '',
              '## Largest symbol losses', '',
              '| ID | Symbol | Net P&L THB | Realized THB | Unrealized THB |',
              '| --- | --- | ---: | ---: | ---: |']
    for key, run in {**result['recovered_runs'], 'R76': result['R76']}.items():
        for s in sorted(run['raw_diagnostics']['symbols'], key=lambda s: s['net_pnl_thb'])[:3]:
            lines.append(f'| {key} | {s["symbol"]} | {s["net_pnl_thb"]:,.2f} | '
                         f'{s["realized_pnl_thb"]:,.2f} | {s["unrealized_pnl_thb"]:,.2f} |')
    lines += ['', 'All symbol P&L reconciles to total P&L. JSON/CSV retain every symbol and completed lot, '
              'including winners. Intraday adverse excursions and entry-quality causality are not established.', '',
              '## Decision and remaining work', '',
              '**Retain the original engineering reference; no candidate is promoted.** '
              'Inspect the symbol/lot evidence before implementing the declared P-C2, P-C3, H-C3 and B-C3 '
              'comparisons. Fresh chronological validation still needs additional permitted ticks and '
              'effective-dated membership. Restoring this archive supplies no new tick period.', '',
              'See the [experiment log](../phase-4-experiments.md) and '
              '[frozen research protocol](../phase-4-research-spec.md).', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; retain previous evidence and choose a new directory')
    result = collect(args.suite.resolve(), args.control.resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'results.json', result)
    (args.output / 'README.md').write_text(markdown(result))
    runs = {**result['recovered_runs'], 'R76': result['R76']}
    for filename, field in [('symbols.csv', 'symbols'), ('completed-lots.csv', 'completed_lots')]:
        rows = [{'id': key, **row} for key, run in runs.items() for row in run['raw_diagnostics'][field]]
        with (args.output / filename).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f'Wrote recovered evidence and R76 results to {args.output}')


if __name__ == '__main__':
    main()
