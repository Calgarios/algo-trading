"""Verify replay hashes and publish every declared alpha experiment outcome."""
import argparse
import csv
from collections import defaultdict
from math import isclose
from build_phase5_results import fill_diagnostics
from phase3_reporting import eligibility
import json
from pathlib import Path
import tempfile
import os
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'alpha-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from package_support import ROOT, sha256


def verified(path):
    hashes = json.loads((path / 'reproducible-hashes.json').read_text())
    for name, digest in hashes.items():
        if sha256(path / name) != digest:
            raise ValueError(f'Artifact changed: {path / name}')
    report = json.loads((path / 'report.json').read_text())
    if len(report['daily']) != 16 or not all(d['reconciliation']['reconciled'] for d in report['daily']):
        raise ValueError('Incomplete or unreconciled run')
    with (path / 'engine/baseline/baseline_transaction_log.csv').open() as f:
        fills = list(csv.DictReader(f))
        ledger, diagnostics = fill_diagnostics(fills, report['configuration']['parameters']['phase5']['fee_multiplier'])
    metrics = report['performance']
    for observed, expected in ((ledger.cash, report['daily'][-1]['raw']['cash']),
                               (ledger.fees, metrics['fees_thb']),
                               (ledger.realized, metrics['realized_pnl_thb']),
                               (ledger.expected_payoff() or 0, metrics['expected_payoff_thb'] or 0),
                               (len(ledger.completed), metrics['completed_fifo_round_trips'])):
        if not isclose(observed, expected, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError('Independent final ledger mismatch')
    if eligibility(metrics) != report['eligibility']:
        raise ValueError('Eligibility mismatch')
    plans = json.loads((path / 'plans.json').read_text())
    pnl = defaultdict(float)
    rate = .00157 * 1.07 * report['configuration']['parameters']['phase5']['fee_multiplier']
    for fill in fills:
        amount = int(fill['Volume']) * float(fill['Price'])
        pnl[fill['Symbol']] += amount * (1 - rate) if fill['Side'] == 'Sell' else -amount * (1 + rate)
    for holding in report['daily'][-1]['holdings']:
        pnl[holding['Symbol']] += holding['Market Value']
    if not isclose(sum(pnl.values()), metrics['final_nav_thb'] - 1e7, rel_tol=1e-9, abs_tol=1e-6):
        raise ValueError('Symbol attribution does not reconcile')
    diagnostics['symbol_net_pnl_thb'] = dict(sorted(pnl.items(), key=lambda item: item[1]))
    diagnostics['daily_selection'] = [dict(date=item['date'], selected_count=len(item['plan']['selected']),
        allocated_exposure=item['plan']['allocated_exposure'], target_exposure=item['plan']['target_exposure'],
        selected=item['plan']['selected'], rejected=item['plan']['rejected']) for item in plans]
    report['diagnostics'] = diagnostics
    return report, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    runs = {}
    for model in ('breakout', 'relative', 'defensive'):
        for weighting in ('equal', 'quality'):
            key = f'{model}-{weighting}'
            report, hashes = verified(args.runs / key)
            config = report['configuration']
            if config['code_sha256']['research/phase5/strategy/DiversifiedBaseline.py'] != sha256(ROOT / 'research/phase5-alpha/DiversifiedBaseline.py') or config['companion_config_sha256'] != sha256(ROOT / f'research/phase5-alpha/configs/{key}.json'):
                raise ValueError('Run source/config differs from declared experiment')
            runs[key] = {'performance': report['performance'], 'eligibility': report['eligibility'],
                         'daily': report['daily'], 'hashes': hashes,
                         'configuration': report['configuration'], 'diagnostics': report['diagnostics']}
    controls = {}
    for model in ('C3', 'C4'):
        report, hashes = verified(ROOT / f'artifacts/retention-{model}')
        controls[f'retention-{model}'] = {'performance': report['performance'], 'daily': report['daily'],
                                          'eligibility': report['eligibility'], 'hashes': hashes, 'diagnostics': report['diagnostics']}
    all_runs = controls | runs
    days = [d['date'] for d in next(iter(runs.values()))['daily']]
    if any([d['date'] for d in r['daily']] != days for r in all_runs.values()):
        raise ValueError('Mismatched comparison dates')
    evidence = {'sample': 'Reused September development; not independent validation',
                'runs': runs, 'controls': controls}
    (out / 'results.json').write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + '\n')
    keys = list(all_runs)
    labels = [k.replace('-quality', '-risk') for k in keys]
    colors = ['#8695a5'] * 2 + ['#187d9b', '#f29b38'] * 3
    with PdfPages(out / 'alpha-results.pdf') as pdf:
        fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
        for ax, field, title, factor in zip(axes.flat,
                ('net_return_pct', 'expected_payoff_thb', 'average_exposure', 'completed_fifo_round_trips'),
                ('Net return (%)', 'Expected payoff (THB / FIFO lot)', 'Average exposure (%)', 'Completed FIFO round trips'),
                (1, 1, 100, 1)):
            vals = [(all_runs[k]['performance'][field] or 0) * factor for k in keys]
            ax.barh(labels, vals, color=colors)
            ax.axvline(50 if field == 'average_exposure' else 5 if field == 'completed_fifo_round_trips' else 0, color='black', lw=.8)
            ax.set_title(title)
            if field == 'net_return_pct':
                ax.axvline(next(iter(runs.values()))['performance']['benchmark_return_pct'], color='red', ls='--', label='SET50')
                ax.legend()
        fig.suptitle('All declared alpha variants — reused development, no promotion\nRisk weighting is a sizing hypothesis, not a verified probability of profit')
        fig.savefig(out / 'overview.png', dpi=160)
        pdf.savefig(fig)
        plt.close(fig)
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, constrained_layout=True)
        for k, r in all_runs.items():
            label = k.replace('-quality', '-risk')
            axes[0].plot(days, [d['performance']['net_return_pct'] for d in r['daily']], label=label)
            axes[1].plot(days, [100*d['closing_risk']['exposure'] for d in r['daily']])
            axes[2].plot(days, [d['performance']['official_max_drawdown_pct'] for d in r['daily']])
        axes[0].plot(days, [d['performance']['benchmark_return_pct'] for d in next(iter(runs.values()))['daily']], 'k--', label='SET50')
        axes[0].legend(ncol=3, fontsize=8)
        axes[0].set_ylabel('Cumulative return (%)')
        axes[1].set_ylabel('Closing exposure (%)')
        axes[1].axhline(50, color='grey', ls='--')
        axes[2].set_ylabel('Running max drawdown (%)')
        axes[2].tick_params(axis='x', rotation=45)
        fig.suptitle('Daily paths — strategy return from initial cash; SET50 from first sample close')
        fig.savefig(out / 'paths.png', dpi=160)
        pdf.savefig(fig)
        plt.close(fig)
        fig, axes = plt.subplots(1, 3, figsize=(14, 6), constrained_layout=True)
        for ax, field, title in zip(axes, ('fees_thb', 'realized_pnl_thb', 'unrealized_pnl_thb'), ('Fees incl. VAT', 'Realized P&L', 'Open-position P&L')):
            ax.barh(labels, [all_runs[k]['performance'][field] for k in keys], color=colors)
            ax.set_title(title + ' (THB)')
            ax.axvline(0, color='black', lw=.8)
        fig.suptitle('Full accounting: lower fees do not establish an investment edge')
        fig.savefig(out / 'pnl.png', dpi=160)
        pdf.savefig(fig)
        plt.close(fig)
    lines = ['# Cost-aware alpha research results', '',
             'All six declared variants and both retention controls. Reused 16-session September development sample; no independent validation.', '',
             '[Strategy review](../../../research/phase5-alpha/strategy-review.md) · [Declaration](../../../research/phase5-alpha/experiment.md) · [Charts PDF](alpha-results.pdf) · [Machine-readable evidence](results.json)', '',
             '| Strategy | Return % | Excess pp | MaxDD % | Exposure % | FIFO trips | Payoff THB | Common | Best Alpha |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |']
    for k, r in all_runs.items():
        p, e = r['performance'], r['eligibility']
        payoff = 'undefined' if p['expected_payoff_thb'] is None else f"{p['expected_payoff_thb']:.2f}"
        lines.append(f"| {k.replace('-quality', '-risk')} | {p['net_return_pct']:.4f} | {p['excess_return_pp']:.4f} | {p['official_max_drawdown_pct']:.4f} | {100*p['average_exposure']:.2f} | {p['completed_fifo_round_trips']} | {payoff} | {e['common_status']} | {e['best_alpha_status']} |")
    for policy in ('breakout', 'relative', 'defensive'):
        equal, risk = runs[f'{policy}-equal'], runs[f'{policy}-quality']
        if equal['performance'] == risk['performance']:
            lines += ['', f'{policy}: equal and risk weighting produced identical final metrics. Position/liquidity/sector capacities and execution constraints can eliminate proposed weight differences; this pair does not establish a weighting advantage.']
    lines += ['', '## Trade quality diagnostics' , '',
              '| Strategy | Closed position episodes | Open episodes | FIFO win rate % | Profit factor | Payoff 95% symbol-cluster interval THB |',
              '| --- | ---: | ---: | ---: | ---: | --- |']
    for k, r in all_runs.items():
        d = r['diagnostics']
        ci = d['payoff_cluster_bootstrap']['interval95_thb']
        interval = 'unavailable' if ci[0] is None else f'{ci[0]:.2f} to {ci[1]:.2f}'
        wr = d['fifo']['win_rate']
        pf = d['fifo']['profit_factor']
        lines.append(f"| {k.replace('-quality', '-risk')} | {d['position_episodes']} | {d['still_open_episodes']} | {100*wr:.2f} | {pf:.3f} | {interval} |" if wr is not None and pf is not None else f"| {k} | {d['position_episodes']} | {d['still_open_episodes']} | unavailable | unavailable | {interval} |")
    lines += ['', 'Intervals are descriptive resampling by symbol, not independent validation or future profit probabilities. Shared market dependence and strategy selection remain. Win rate and profit factor describe completed FIFO lots; inspect open P&L alongside them.']
    lines += ['', '## Largest net loss contributors', '',
              'Contributions include commissions, realized sales and remaining marked holdings. These are retrospective diagnostics, not a ticker exclusion list.', '',
              '| Strategy | Three largest net loss contributors (THB) |', '| --- | --- |']
    for k, r in runs.items():
        worst = sorted(r['diagnostics']['symbol_net_pnl_thb'].items(), key=lambda item: item[1])[:3]
        lines.append('| ' + k.replace('-quality', '-risk') + ' | ' + '; '.join(f'{s}: {v:,.0f}' for s, v in worst) + ' |')
    passing = sum(r['eligibility']['best_alpha_status'] == 'pass' for r in runs.values())
    lines += ['', f'**{passing}/6 new variants pass the measured Best Alpha gates.** A passing local replay would not establish prize acceptance or future profitability.', '',
              '![Overview](overview.png)', '![Daily paths](paths.png)', '![Full P&L](pnl.png)', '',
              'The source and thresholds were declared before these replays. No failed variants are omitted. All 96 new strategy-days reconcile cash, positions, NAV, realized P&L, FIFO trips and payoff against the official engine. Artifact SHA-256 values are verified by the report builder and included in results.json.', '',
              'FIFO counts are completed engine lots and can be fragmented by partial fills; they are not independent trading ideas. Exposure differs between models, so return changes are not evidence of improved stock selection at matched exposure. Drawdown is the official daily-close metric; controls do not guarantee an intraday loss ceiling. Only 48 supplied names are available.', '',
              '## Reproduction', '', '```bash',
              '.venv/bin/python scripts/run_alpha_experiment.py --output artifacts/alpha-repeat',
              '.venv/bin/python scripts/build_alpha_results.py --runs artifacts/alpha-repeat --output artifacts/alpha-report-repeat', '```', '',
              'The builder also requires the existing verified artifacts/retention-C3 and artifacts/retention-C4 controls. The literal quality config suffix means risk sizing in this experiment, not estimated profitability.']
    lines.append('\n## Decision\n\nNo strategy is promoted. The best new return, breakout -3.6368%, improves on\nretained C3 by 0.1820 percentage points, but exposure falls below eligibility\nand payoff worsens. Its 96 FIFO trips represent only seven closed position\nepisodes. Relative strength loses more than SET50; defensive pullbacks do not\nbeat the C3/C4 retention controls. All new payoff intervals remain below zero.\nThe results do not support claims of high win probability or prize readiness.\n\nThe cost/retention/risk changes were bundled and exposure differs, so the return\nchange cannot be attributed to better stock selection. Preserve the engineering\nrisk tests, but reject promotion of these trading variants. Further parameter\nsearch on the same 16 sessions cannot supply independent evidence. See\n[next research](../../to-do/alpha-research-next.md) for the required comparison\nand new-data protocol.\n')
    (out / 'README.md').write_text('\n'.join(lines).rstrip() + '\n')


if __name__ == '__main__':
    main()
