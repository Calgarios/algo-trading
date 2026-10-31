"""Diagnose frozen Phase 3 evidence without requiring the organizer package."""
import argparse
from collections import defaultdict
import csv
from datetime import date
import json
from math import isclose, isfinite
from pathlib import Path

from package_support import ROOT, sha256
from phase3_reporting import FEE_RATE, FillLedger, drawdown_pct, eligibility


def read_json(path):
    def invalid(value):
        raise ValueError(f'Nonfinite JSON value: {value}')
    return json.loads(Path(path).read_text(), parse_constant=invalid)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def close(actual, expected, label):
    if actual is None or expected is None:
        if actual is not expected:
            raise ValueError(f'{label}: missing value differs')
    elif (not isfinite(actual) or not isfinite(expected)
          or not isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-5)):
        raise ValueError(f'{label}: {actual} != {expected}')


def count(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f'{label}: expected nonnegative integer')
    return value


def validate_run(run):
    """Validate cumulative accounting and measurement anchors before attribution."""
    daily, config = run['daily'], run['configuration']
    days = config['days']
    if (not days or days != sorted(set(days))
            or [d['date'] for d in daily] != days):
        raise ValueError('Daily evidence must exactly cover unique ordered run dates')
    for day in days:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError('Noncanonical session date')
    capital = config['parameters']['initial_capital_thb']
    if not isfinite(capital) or capital <= 0:
        raise ValueError('Invalid initial capital')
    navs, exposures = [], []
    previous_fees, previous_lots = 0.0, 0
    for day in daily:
        if day['reconciled'] is not True:
            raise ValueError('Unreconciled daily evidence')
        nav, cash, p = day['nav'], day['cash'], day['performance']
        if (not isfinite(nav) or not isfinite(cash) or nav <= 0
                or cash < 0 or cash > nav):
            raise ValueError('Invalid daily NAV/cash')
        navs.append(nav)
        exposures.append((nav - cash) / nav)
        for key, expected in {
            'final_nav_thb': nav, 'final_cash_thb': cash,
            'net_return_pct': (nav / capital - 1) * 100,
            'official_max_drawdown_pct': drawdown_pct(navs),
            'initial_capital_max_drawdown_pct': drawdown_pct([capital] + navs),
            'aligned_first_close_return_pct': (nav / navs[0] - 1) * 100,
            'average_exposure': sum(exposures) / len(exposures),
            'excess_return_pp': p['net_return_pct'] - p['benchmark_return_pct'],
            'aligned_first_close_excess_pp': p['aligned_first_close_return_pct'] - p['benchmark_return_pct'],
        }.items():
            close(p[key], expected, key)
        close(day['exposure'], exposures[-1], 'daily exposure')
        close(p['realized_pnl_thb'] + p['unrealized_pnl_thb'], nav - capital, 'P&L identity')
        fees = p['fees_thb']
        lots = count(p['completed_fifo_round_trips'], 'completed lots')
        if not isfinite(fees) or fees < previous_fees or lots < previous_lots:
            raise ValueError('Cumulative fees/lots decreased or are invalid')
        previous_fees, previous_lots = fees, lots
    for key, value in daily[-1]['performance'].items():
        close(run['performance'][key], value, f'final {key}')
    # Re-evaluate eligibility from raw values, not rounded text in a report.
    if run['eligibility'] != eligibility(run['performance']):
        raise ValueError('Stored eligibility differs from recomputed working rules')
    detail = run['payoff_detail']
    wins, losses, flats = (count(detail[k], k) for k in ('winning_lots', 'losing_lots', 'flat_lots'))
    if wins + losses + flats != previous_lots:
        raise ValueError('Completed-lot counts disagree')
    for n, mean, sign in [(wins, detail['mean_win_thb'], 1), (losses, detail['mean_loss_thb'], -1)]:
        if (n == 0 and mean is not None) or (n and (mean is None or not isfinite(mean) or mean * sign <= 0)):
            raise ValueError('Invalid completed-lot mean/count')
    completed = wins * (detail['mean_win_thb'] or 0) + losses * (detail['mean_loss_thb'] or 0)
    close(run['performance']['expected_payoff_thb'], completed / (wins + losses) if wins + losses else None,
          'completed-lot expected payoff')
    return capital, completed


def analyze_run(run):
    capital, completed = validate_run(run)
    p, detail = run['performance'], run['payoff_detail']
    net, fees = p['final_nav_thb'] - capital, p['fees_thb']
    daily, previous_nav, previous_fees = [], capital, 0.0
    for day in run['daily']:
        fee_change = day['performance']['fees_thb'] - previous_fees
        daily.append({'date': day['date'], 'net_pnl_change_thb': day['nav'] - previous_nav,
                      'return_from_previous_nav_pct': (day['nav'] / previous_nav - 1) * 100,
                      'fees_thb': fee_change, 'traded_notional_thb': fee_change / FEE_RATE,
                      'exposure': day['exposure'], 'target_exposure': day['target_exposure'],
                      'drawdown_guard': day['drawdown_guard']})
        previous_nav, previous_fees = day['nav'], day['performance']['fees_thb']
    win_pnl = detail['winning_lots'] * (detail['mean_win_thb'] or 0)
    loss_pnl = detail['losing_lots'] * (detail['mean_loss_thb'] or 0)
    nonflat = detail['winning_lots'] + detail['losing_lots']
    summary = {
        'name': run['name'], 'net_return_pct': p['net_return_pct'], 'net_pnl_thb': net,
        'realized_pnl_thb': p['realized_pnl_thb'], 'unrealized_pnl_thb': p['unrealized_pnl_thb'],
        'unrealized_loss_share_pct': p['unrealized_pnl_thb'] / net * 100
        if net < 0 and p['unrealized_pnl_thb'] < 0 else None,
        'fees_thb': fees, 'fee_drag_pp': fees / capital * 100,
        'same_fills_fee_added_back_return_pct': (net + fees) / capital * 100,
        'traded_notional_thb': fees / FEE_RATE,
        'traded_notional_over_initial_capital': fees / FEE_RATE / capital,
        'post_first_day_traded_notional_thb': (fees - daily[0]['fees_thb']) / FEE_RATE,
        'completed_lot_net_pnl_thb': completed,
        'partial_realization_on_open_lots_thb': p['realized_pnl_thb'] - completed,
        'completed_fifo_lots': p['completed_fifo_round_trips'],
        'expected_payoff_thb': p['expected_payoff_thb'],
        'nonflat_win_rate': detail['winning_lots'] / nonflat if nonflat else None,
        'profit_factor': win_pnl / -loss_pnl if loss_pnl < 0 else None,
        'official_excess_return_pp': p['excess_return_pp'],
        'aligned_first_close_excess_pp': p['aligned_first_close_excess_pp'],
        'average_exposure': p['average_exposure'],
        'common_status': run['eligibility']['common_status'],
        'best_alpha_status': run['eligibility']['best_alpha_status'],
    }
    return {'summary': summary, 'daily': daily,
            'largest_loss_days': sorted((d for d in daily if d['net_pnl_change_thb'] < 0),
                                        key=lambda d: (d['net_pnl_change_thb'], d['date']))[:3],
            'fixed_fill_fee_stress': [
                {'fee_multiplier': multiplier,
                 'net_return_pct': (net - fees * (multiplier - 1)) / capital * 100}
                for multiplier in (1.25, 1.5)],
            'raw_diagnostics': {'status': 'unavailable',
                                'reason': 'Recover the original hashed report, FIFO and fill log bundle'}}


def analyze_fills(fills, report):
    """Keep engine fill order; attribute P&L using FIFO and final market values."""
    capital = report['configuration']['parameters']['initial_capital_thb']
    days = report['configuration']['days']
    day_index = {day: i for i, day in enumerate(days)}
    ledger = FillLedger(capital)
    symbols = defaultdict(lambda: FillLedger(capital))
    notional, entry_days, previous_days = defaultdict(float), {}, {}
    lots = []
    for fill in fills:
        symbol, order = fill['Symbol'], str(fill['Order Number'])
        day = str(fill['Timestamp'])[:10]
        # Cross-symbol timestamps need not be sorted in notebook replay.
        if day not in day_index or day < previous_days.get(symbol, day):
            raise ValueError('Fill date outside run or backwards within a symbol')
        previous_days[symbol] = day
        before = len(ledger.completed)
        ledger.apply(fill)
        symbols[symbol].apply(fill)
        notional[symbol] += int(fill['Volume']) * float(fill['Price'])
        if fill['Side'] == 'Buy':
            entry_days.setdefault((symbol, order), day)
        for lot in ledger.completed[before:]:
            entry = entry_days[(symbol, lot['order'])]
            lots.append({**lot, 'first_buy_date': entry, 'completion_date': day,
                         'holding_sessions': day_index[day] - day_index[entry],
                         'net_return_on_buy_cost_pct': lot['pnl'] / (lot['unit_cost'] * lot['volume']) * 100})
    metrics = report['performance']
    for actual, expected, label in [
        (ledger.cash, metrics['final_cash_thb'], 'cash'),
        (ledger.fees, metrics['fees_thb'], 'fees'),
        (ledger.realized, metrics['realized_pnl_thb'], 'realized P&L'),
        (ledger.expected_payoff(), metrics['expected_payoff_thb'], 'payoff'),
        (len(lots), metrics['completed_fifo_round_trips'], 'completed lots'),
        (len(ledger.symbols), metrics['distinct_stocks'], 'distinct stocks'),
    ]:
        close(actual, expected, label)
    holdings = report['daily'][-1]['holdings']
    if len({h['Symbol'] for h in holdings}) != len(holdings):
        raise ValueError('Duplicate final holding')
    quantities = {h['Symbol']: h['Actual Volume'] for h in holdings if h['Actual Volume']}
    if ledger.quantities() != quantities:
        raise ValueError('Final holdings differ from fills')
    marks = {h['Symbol']: h['Market Value'] for h in holdings}
    if any(not isfinite(v) or v < 0 for v in marks.values()):
        raise ValueError('Invalid final market value')
    close(ledger.cash + sum(marks.values()), metrics['final_nav_thb'], 'marked NAV')
    attributed = []
    for symbol, book in sorted(symbols.items()):
        open_cost = sum(lot['unit_cost'] * lot['remaining'] for lot in book.lots[symbol])
        unrealized = marks.get(symbol, 0) - open_cost
        attributed.append({'symbol': symbol, 'realized_pnl_thb': book.realized,
                           'unrealized_pnl_thb': unrealized, 'net_pnl_thb': book.realized + unrealized,
                           'fees_thb': book.fees, 'traded_notional_thb': notional[symbol],
                           'open_market_value_thb': marks.get(symbol, 0),
                           'completed_fifo_lots': len(book.completed),
                           'expected_payoff_thb': book.expected_payoff()})
    close(sum(s['net_pnl_thb'] for s in attributed), metrics['final_nav_thb'] - capital, 'symbol P&L total')
    return {'status': 'available', 'symbols': attributed, 'completed_lots': lots,
            'intraday_adverse_excursion': None, 'slippage_attribution': None,
            'limitation': 'Adverse excursion and slippage attribution require decision/tick evidence'}, ledger


def analyze_bundle(folder, run):
    required = ['report.json', 'fifo.json', 'engine/baseline/baseline_transaction_log.csv']
    for path in required:
        if sha256(folder / path) != run['hashes'][path]:
            raise ValueError(f'Raw artifact differs from committed hash: {path}')
    report, fifo = read_json(folder / 'report.json'), read_json(folder / 'fifo.json')
    if report['configuration'] != run['configuration'] or report['performance'] != run['performance']:
        raise ValueError('Raw report differs from compact evidence')
    with (folder / required[-1]).open(newline='', encoding='utf-8-sig') as stream:
        result, ledger = analyze_fills(csv.DictReader(stream), report)
    expected = {'completed': ledger.completed,
                'open': {s: list(lots) for s, lots in ledger.lots.items() if lots}}
    if fifo != expected:
        raise ValueError('Replayed FIFO differs from recorded artifact')
    result['verified_sha256'] = {path: run['hashes'][path] for path in required}
    return result


def collect(evidence, runs=None):
    results, reference = {}, None
    for key, run in sorted(evidence['runs'].items()):
        config = run['configuration']
        identity = {k: config[k] for k in ('days', 'archive_sha256', 'package_tree_sha256',
                                           'dependencies', 'event_order', 'code_sha256')}
        identity['initial_capital_thb'] = config['parameters']['initial_capital_thb']
        if reference is not None and reference != identity:
            raise ValueError(f'Non-comparable experiment inputs: {key}')
        reference = identity
        result = analyze_run(run)
        if runs is not None and (runs / key).exists():
            result['raw_diagnostics'] = analyze_bundle(runs / key, run)
        results[key] = result
    if not results:
        raise ValueError('No experiments in evidence')
    return {'schema_version': 1, 'sample_role': 'reused_development',
            'decision': 'retain_reference_revise_research', 'validation_complete': False,
            'runs': results}


def markdown(report):
    lines = ['# Phase 4 development diagnostics', '',
             'Derived from frozen Phase 3 evidence; no new simulation or validation run.', '',
             'Decision: **retain the engineering reference; revise research**. '
             'No candidate is promoted. September remains reused development data.', '',
             '## Loss attribution', '',
             '| ID | Net % | Realized THB | Unrealized THB | Fees THB | Fee-added-back % | Traded / initial NAV |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for key, run in report['runs'].items():
        s = run['summary']
        lines.append(f'| {key} | {s["net_return_pct"]:.4f} | {s["realized_pnl_thb"]:,.2f} | '
                     f'{s["unrealized_pnl_thb"]:,.2f} | {s["fees_thb"]:,.2f} | '
                     f'{s["same_fills_fee_added_back_return_pct"]:.4f} | '
                     f'{s["traded_notional_over_initial_capital"]:.4f} |')
    summaries = [r['summary'] for r in report['runs'].values()]
    negative = sum(s['same_fills_fee_added_back_return_pct'] < 0 for s in summaries)
    lines += ['', f'{negative}/{len(summaries)} remain negative after recorded commission/VAT is added back. '
              'Execution prices still include slippage. This is an accounting identity, not a cost-free replay.', '',
              'Traded notional = fees / 0.0016799, counting buys plus sells, including initial deployment. '
              'It is not round-trip turnover. Post-first-day notional and fee stresses are in the JSON.', '',
              '## Return anchors and completed lots', '',
              '| ID | Official excess pp | First-close excess pp | Completed lots | Payoff THB | Open partial realized THB |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for key, run in report['runs'].items():
        s = run['summary']
        payoff = 'Undefined' if s['expected_payoff_thb'] is None else f'{s["expected_payoff_thb"]:,.2f}'
        lines.append(f'| {key} | {s["official_excess_return_pp"]:.4f} | '
                     f'{s["aligned_first_close_excess_pp"]:.4f} | {s["completed_fifo_lots"]} | '
                     f'{payoff} | {s["partial_realization_on_open_lots_thb"]:,.2f} |')
    lines += ['', 'Official return includes the portfolio first day, whereas SET50 starts at its first close. '
              'The aligned column starts both at the first close; neither is a matched-basket control.', '',
              'Completed-lot payoff excludes breakeven lots and partial sales of lots still open. '
              'Open partial realized P&L is total realized P&L minus completed-lot P&L. '
              'Lot counts are not independent investment decisions.', '',
              '## Largest daily losses', '',
              '| ID | Session | NAV change THB | Day fees THB | Closing exposure % |',
              '| --- | --- | ---: | ---: | ---: |']
    for key, run in report['runs'].items():
        for day in run['largest_loss_days']:
            lines.append(f'| {key} | {day["date"]} | {day["net_pnl_change_thb"]:,.2f} | '
                         f'{day["fees_thb"]:,.2f} | {day["exposure"] * 100:.3f} |')
    lines += ['', 'Daily P&L uses the preceding close, or initial capital on the first day. '
              'All 16 days remain development evidence; these are not separate validation folds.', '',
              '## Evidence coverage', '']
    for key, run in report['runs'].items():
        raw = run['raw_diagnostics']
        lines.append(f'- {key}: symbol/lot diagnostics {raw["status"]}.')
    lines += ['', 'Raw bundle mode checks committed hashes and reconciles fills, FIFO, cash, holdings and '
              'symbol P&L. Without those bundles, symbol/lot attribution and holding ages remain unknown. '
              'Intraday adverse excursion and slippage attribution additionally require decision/tick evidence.', '',
              'The JSON retains every daily observation, both fixed-fill fee stresses, inputs and script hashes. '
              'The +25%/+50% fee stresses keep quantities and prices fixed; they do not simulate execution responses.', '',
              'See [research protocol](../phase-4-research-spec.md) for declared controls, data requirements '
              'and acceptance criteria. No fresh engine run or untouched validation is claimed.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'docs/result-data-visualisation/phase-3-results.json')
    parser.add_argument('--runs', type=Path, help='Optional original Phase 3 suite directory, containing C1/ etc.')
    parser.add_argument('--output', type=Path, required=True, help='New output directory; never overwritten')
    args = parser.parse_args()
    if args.runs is not None and not args.runs.is_dir():
        parser.error('--runs must be an existing suite directory')
    if args.output.exists():
        parser.error('Output directory already exists; choose a new experiment path')
    report = collect(read_json(args.evidence), args.runs)
    report['provenance'] = {'evidence_sha256': sha256(args.evidence),
                            'code_sha256': {path: sha256(ROOT / path) for path in
                                           ('scripts/phase4_diagnostics.py', 'scripts/phase3_reporting.py',
                                            'scripts/package_support.py')},
                            'fee_rate': FEE_RATE}
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'diagnostics.json', report)
    (args.output / 'README.md').write_text(markdown(report))
    rows = [{'id': key, **run['summary']} for key, run in report['runs'].items()]
    with (args.output / 'summary.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} development diagnostics to {args.output}')


if __name__ == '__main__':
    main()
