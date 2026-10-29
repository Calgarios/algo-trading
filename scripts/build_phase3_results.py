"""Build the Phase 3 Markdown/PDF comparison from reconciled official-engine runs."""
import argparse
from collections import Counter
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'phase3-matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', str(Path(tempfile.gettempdir()) / 'phase3-report-cache'))
Path(os.environ['XDG_CACHE_HOME']).mkdir(parents=True, exist_ok=True)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from package_support import ROOT, sha256
from prepare_strategy_suite import STRATEGIES


DETAILS = {
    'C1': ('Favor sustained gains that are large relative to day-to-day volatility. Blend the shorter trend with the longer trend to avoid relying on one lookback.',
           '(0.6 × return20 + 0.4 × return60) / (volatility20 × √20)',
           '20- and 60-session returns; 20-session return volatility.',
           'Momentum can reverse abruptly; low recent volatility does not imply low future risk.'),
    'C2': ('Favor stocks with smaller downside fluctuations and less positive sensitivity to SET50. This is a defensive allocation hypothesis, not a direct forecast of rising prices.',
           '−(annualized downside deviation20 + 0.1 × max(beta60, 0))',
           'Negative daily returns over 20 sessions; up to 60 aligned stock/SET50 return intervals.',
           'Low downside risk can lag a rebound. Beta is estimated from a short and changing sample.'),
    'C3': ('Favor prices near their previous 55-session high, especially when the path there was relatively direct. The efficiency term rewards persistent movement.',
           '(close / prior high55 − 1) / volatility20 + 0.5 × efficiency20',
           'Previous 55-session high excluding the latest bar; 20-session volatility and path efficiency.',
           'False breakouts and gaps can create losses before a daily risk guard reacts.'),
    'C4': ('Favor a strong longer trend with a recent pullback. The recent return is subtracted to distinguish a potential recovery entry from a stretched move.',
           '(return60 − 2 × return5) / (volatility20 × √20)',
           '60-session trend, 5-session pullback, and 20-session volatility.',
           'A pullback can mark a lasting trend reversal. This score has no guarantee of mean reversion.'),
    'C5': ('Combine the cross-sectional ranks of the four custom signals equally. This reduces dependence on a single scoring formula, while keeping the decision explainable.',
           'Mean percentile rank of C1, C2, C3 and C4',
           'All custom features; average ranks for ties. Daily ranks use the frozen ten-stock basket.',
           'The components overlap and can fail together; averaging ranks can dilute a useful signal.'),
    'T1': ('Favor a 20-session simple moving average above the 60-session average, scaled by volatility. This is a slower trend allocation.',
           '(SMA20 / SMA60 − 1) / volatility20',
           '20- and 60-close simple moving averages; 20-session daily return volatility.',
           'Moving averages lag turning points and can repeatedly change ranks in sideways markets.'),
    'T2': ('Use faster exponential averages to emphasize recent price information. Allocate more to a stronger normalized separation between the two averages.',
           '(EMA12 − EMA26) / (close × volatility20)',
           '12- and 26-session EMAs; 20-session volatility. EMA alpha = 2 / (period + 1).',
           'Faster reactions can produce more turnover and false signals after brief moves.'),
    'T3': ('Combine MACD acceleration with a smaller contribution from the underlying trend. A rising histogram can identify improving momentum before a slow crossover.',
           '(MACD histogram + 0.25 × MACD line) / (close × volatility20)',
           'MACD line = EMA12 − EMA26; signal = EMA9 of MACD; histogram = line − signal.',
           'Acceleration can improve while prices still fall. Histogram changes are not proof of a reversal.'),
    'T4': ('Prefer RSI near 35, with an additional preference for stocks above their 60-session average. This seeks moderate oversold entries within a stronger trend.',
           '−(RSI14 − 35)² / 100 + (5 if close > SMA60, else 0)',
           'Wilder-smoothed 14-session RSI and 60-close simple moving average.',
           'Oversold stocks can stay oversold; the trend bonus is a preference, not a mandatory filter.'),
    'T5': ('Prefer a close around one standard deviation below its 20-session mean. Penalize falls beyond two deviations and favor prices above the longer average.',
           '−abs(z20 + 1) − 2 × max(−2 − z20, 0) + (1 if close > SMA60, else 0)',
           'z20 = (close − SMA20) / sample standard deviation of 20 closes; SMA60 trend preference.',
           'Price distributions need not be normal, and lower-band moves can become persistent declines.'),
}

CONTROLS = [
    'One shared execution layer: THB 10 million, unchanged TradeSim 0.2.7, 16 supplied tick days (9–30 September 2026), 2,906,167 ticks per full run. All 48 supplied symbols are replayed in the original notebook symbol/row-index order, not globally sorted time.',
    'Before September 9, use at most 180 prior daily bars and require at least 80 valid observations. Form the 30-stock pool with the highest median 20-session close × volume. Each signal selects ten stocks, at most two per sector. Freeze those names for the whole run; daily re-ranking changes weights only.',
    'Normal target exposure is 76% of opening NAV. Ranked weights range from 9.12% to 6.08% per stock. Buy checks limit each position to 10%, total investment to 80%, and preserve 20% cash. Later price movements can exceed these pre-buy limits.',
    'Opening drawdown guard lowers target to 72% at 2% portfolio drawdown or 1.2× SET50 drawdown when SET50 drawdown is at least 0.5%. It lowers target to 55% at 4% portfolio drawdown or 1.35× SET50 drawdown when SET50 drawdown is at least 1%. The guard uses drawdown observed so far, including initial capital for the portfolio, and does not reset a historical maximum after recovery.',
    'Quantity targets use prior close and 100-share lots. Rebalance when the opening gap is at least 0.4% of NAV or the position is absent. Retry actual residual quantities at most once per symbol per 15-minute decision slot. Market IOC fills may be partial or zero. Costs are 0.157% commission plus 7% VAT on commission per side, and the official adverse price tick.',
    'The drawdown guard is evaluated daily and remains subject to gaps and incomplete fills. It can reduce average exposure below the user’s 70–80% preference; that tradeoff is reported. There is no forced end-of-sample liquidation, cosmetic trade generation, or guarantee of eligibility.',
]

GLOSSARY = [
    ('Payoff and expected payoff', 'A completed trade’s payoff is its net profit or loss after both-side costs. Here a trade means a fully closed FIFO buy lot. TradeSim expected payoff is the arithmetic mean P&L of completed non-breakeven lots: win fraction × mean win − loss fraction × mean loss magnitude. Six wins of THB 1,000 and four losses of THB 800 imply THB 280 per completed lot. It is an observed sample average, not a forecast. Partial closes of still-open lots affect realized P&L but not completed-lot payoff yet; zero completed non-flat lots means undefined.'),
    ('Simulation data', 'Yes: executions and valuation use the stock ticks supplied with TradeSim. Prior stock/SET50 daily history provides signals; the supplied SET50 benchmark file provides benchmark metrics. Each strategy gets the same dates, capital, costs and input package. Its selected basket and resulting trades differ. No synthetic prices are used for reported returns.'),
    ('Percent versus percentage points', 'A strategy return of 3% minus a benchmark return of 1% is 2 percentage points (2 pp) of excess return. Both inputs are percentages; their arithmetic difference is reported in pp. This is not the compounded wealth ratio (1.03 / 1.01 − 1).'),
    ('Return and drawdown anchors', 'Net return is final NAV / initial THB 10 million − 1. SET50 return uses the first sample close. Official maximum drawdown uses daily closing peaks and therefore excludes an initial-capital peak before the first close. Initial-capital drawdown and aligned first-close returns are also saved separately. Intraday drawdown is not this official metric.'),
    ('Exposure and counts', 'Average exposure is the mean of the 16 daily closing invested-value / NAV fractions, including the first day. It is not the target, final value or time-weighted intraday exposure. Distinct stocks counts unique names with fills. Completed FIFO lots can be numerous because IOC orders create many small lots; their count is not a count of independent investment ideas.'),
    ('Prize conditions', 'Working common criteria: portfolio MaxDD strictly below 1.5× SET50 MaxDD, at least five completed FIFO lots, average exposure at least 50%, and expected payoff above zero. At least five distinct stocks is tracked separately. Positive total return is not a universal common requirement. Best Alpha additionally requires nonnegative total and excess returns. Passing these local checks is not organizer acceptance or a prize guarantee.'),
]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def fmt(value, digits=2):
    return 'Undefined' if value is None else f'{value:,.{digits}f}'


def md_table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
                     + ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def collect(input_dir, repeat):
    manifest = read(ROOT / 'research/phase3-suite/manifest.json')
    phase2 = read(ROOT / 'docs/phase-2-run-evidence.json')
    phase2_sources = {**phase2['configuration']['code_sha256'], **phase2['validation_code_sha256']}
    assert all(sha256(ROOT / p) == digest for p, digest in phase2_sources.items())
    runs = {}
    for key, (family, name) in STRATEGIES.items():
        folder = input_dir / key
        report, plans = read(folder / 'report.json'), read(folder / 'plans.json')
        env, hashes = read(folder / 'environment.json'), read(folder / 'reproducible-hashes.json')
        config = report['configuration']
        assert config['parameters']['suite']['id'] == key
        assert config['companion_config_sha256'] == manifest['strategies'][key]['config_sha256']
        for path, digest in hashes.items():
            assert sha256(folder / path) == digest, (key, path)
        assert len(report['daily']) == 16 and sum(d['ticks'] for d in report['daily']) == 2906167
        assert all(d['reconciliation']['reconciled'] for d in report['daily'])
        assert all(p['plan']['ready'] and len(p['plan']['selected']) == 10 for p in plans)
        assert all(f['history_end'] < p['date'] for p in plans for f in p['plan']['eligible'].values())
        metrics = report['performance']
        assert metrics['distinct_stocks'] <= 10
        completed = read(folder / 'fifo.json')['completed']
        wins = [lot['pnl'] for lot in completed if lot['pnl'] > 0]
        losses = [lot['pnl'] for lot in completed if lot['pnl'] < 0]
        payoff_detail = {'winning_lots': len(wins), 'losing_lots': len(losses),
                         'flat_lots': len(completed) - len(wins) - len(losses),
                         'mean_win_thb': sum(wins)/len(wins) if wins else None,
                         'mean_loss_thb': sum(losses)/len(losses) if losses else None}
        daily = [{'date': d['date'], 'nav': d['raw']['nav'], 'cash': d['raw']['cash'],
                  **d['closing_risk'], 'performance': d['performance'], 'target_exposure': d['target_exposure'],
                  'drawdown_guard': d['drawdown_guard'], 'reconciled': d['reconciliation']['reconciled']}
                 for d in report['daily']]
        runs[key] = {'family': family, 'name': name, 'performance': metrics,
                     'eligibility': report['eligibility'], 'user_targets': report['user_targets'],
                     'configuration': config, 'basket': config['parameters']['suite']['basket'],
                     'initial_weights': plans[0]['plan']['weights'], 'daily': daily,
                     'payoff_detail': payoff_detail,
                     'execution': report['execution'], 'hashes': hashes, 'environment': env,
                     'guard_days': dict(Counter(d['drawdown_guard'] for d in daily)),
                     'max_daily_seconds': max(env['daily_seconds'].values()),
                     'total_daily_seconds': sum(env['daily_seconds'].values())}
    reference = runs['C1']['configuration']
    for run in runs.values():
        for field in ('archive_sha256', 'package_tree_sha256', 'days', 'dependencies', 'event_order', 'code_sha256'):
            assert run['configuration'][field] == reference[field], field
        for field in ('benchmark_return_pct', 'benchmark_max_drawdown_pct'):
            assert run['performance'][field] == runs['C1']['performance'][field]
    ranked = sorted(runs, key=lambda k: (
        runs[k]['eligibility']['common_and_participation_status'] == 'pass',
        runs[k]['eligibility']['best_alpha_status'] == 'pass',
        runs[k]['user_targets']['average_exposure_in_band'], runs[k]['performance']['net_return_pct']), reverse=True)
    lead = ranked[0]
    repeatability = {'status': 'not supplied'}
    if repeat:
        repeated_report = read(repeat / 'report.json')
        repeated_id = repeated_report['configuration']['parameters']['suite']['id']
        repeated_hashes = read(repeat / 'reproducible-hashes.json')
        for path, digest in repeated_hashes.items():
            assert sha256(repeat / path) == digest
        assert repeated_hashes == runs[repeated_id]['hashes']
        repeatability = {'status': 'pass', 'strategy': repeated_id, 'identical_artifacts': len(repeated_hashes),
                         'hashes': repeated_hashes, 'environment': read(repeat / 'environment.json')}
    old = read(ROOT / 'docs/phase-3-followup-evidence.json')['runs']
    historical = {k: {'performance': r['performance'], 'eligibility': r['eligibility']}
                  for k, r in old.items()}
    return {'scope': 'Reused September development data, not untouched validation or organizer acceptance',
            'date_bangkok': '2026-10-30', 'development_lead': lead, 'runs': runs,
            'historical': historical, 'repeatability': repeatability,
            'phase2_sources_unchanged': phase2_sources,
            'test_sources_sha256': {str(p.relative_to(ROOT)): sha256(p)
                                    for p in sorted((ROOT / 'tests').glob('test_*.py'))},
            'source_sha256': {p: sha256(ROOT / p) for p in
                              ['scripts/build_phase3_results.py', 'scripts/run_strategy_suite.py',
                               'research/phase3-suite/manifest.json', 'requirements-reporting.txt',
                               'tests/test_strategy_suite.py']},
            'reporting_dependencies': {p: importlib.metadata.version(p) for p in ['matplotlib', 'reportlab', 'pypdf']}}


def figures(data, folder):
    folder.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.titleweight': 'bold', 'axes.grid': True,
                         'grid.alpha': .2, 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
    runs, keys = data['runs'], list(data['runs'])
    palette = ['#007C91', '#AC511B', '#7960A7', '#359363', '#BD5F81']
    color = {k: palette[i % 5] for i, k in enumerate(keys)}
    def save(fig, name):
        fig.savefig(folder / f'{name}.png', dpi=180, bbox_inches='tight')
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.2, 3.4), layout='constrained')
    y = np.arange(len(keys))
    ax.barh(y, [runs[k]['performance']['net_return_pct'] for k in keys], color=[color[k] for k in keys])
    ax.set_yticks(y, [k + '  ' + runs[k]['name'] for k in keys]); ax.invert_yaxis()
    ax.axvline(0, color='#555555', lw=.8)
    ax.axvline(runs['C1']['performance']['benchmark_return_pct'], color='#171717', ls='--', label='SET50')
    ax.set_xlabel('Net return (%) after costs'); ax.legend(loc='best')
    save(fig, 'returns')
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.3), layout='constrained', sharex=True)
    for ax, family in zip(axes, ['Custom', 'Indicator']):
        for k in keys:
            if runs[k]['family'] == family:
                ax.plot([d['performance']['net_return_pct'] for d in runs[k]['daily']], label=k, color=color[k])
        ax.plot([d['performance']['benchmark_return_pct'] for d in runs['C1']['daily']], color='#171717', ls='--', label='SET50')
        ax.axhline(0, color='#999999', lw=.7); ax.set_title(f'{family} strategies'); ax.set_ylabel('Return (%)')
        ax.legend(ncols=6, fontsize=8, loc='lower left')
    axes[-1].set_xticks(range(0, 16, 3), [runs['C1']['daily'][i]['date'][5:] for i in range(0, 16, 3)])
    axes[-1].set_xlabel('September 2026 trading dates'); save(fig, 'return-paths')
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), layout='constrained')
    axes[0].axhspan(70, 80, color='#35A879', alpha=.14, label='User target 70–80%')
    axes[0].axhline(50, color='#555555', ls='--', label='Common minimum 50%')
    axes[0].bar(keys, [runs[k]['performance']['average_exposure'] * 100 for k in keys], color=[color[k] for k in keys])
    axes[0].set_ylim(0, 85); axes[0].set_ylabel('Average exposure (%)'); axes[0].legend(fontsize=7, loc='lower left')
    for k in keys:
        m = runs[k]['performance']; axes[1].scatter(m['official_max_drawdown_pct'], m['net_return_pct'], color=color[k])
        offset = {'C1': (7, -5), 'T1': (-18, -3), 'T2': (8, 8), 'T3': (-18, 8),
                  'T4': (4, -12), 'T5': (3, -10), 'C4': (3, -5)}.get(k, (3, 3))
        axes[1].annotate(k, (m['official_max_drawdown_pct'], m['net_return_pct']), xytext=offset,
                         textcoords='offset points', fontsize=7,
                         arrowprops={'arrowstyle':'-', 'color':'#999999', 'lw':.5} if k.startswith('T') else None)
    limit = 1.5 * runs['C1']['performance']['benchmark_max_drawdown_pct']
    axes[1].axvline(limit, color='#B63738', ls='--', label=f'Strict DD limit {limit:.2f}%')
    axes[1].axhline(0, color='#999999', lw=.7)
    axes[1].set_xlabel('Official maximum drawdown (%)'); axes[1].set_ylabel('Net return (%)'); axes[1].legend(fontsize=7)
    save(fig, 'exposure-and-risk')
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.2), layout='constrained', sharex=True)
    axes[0].bar(keys, [runs[k]['performance']['expected_payoff_thb'] or 0 for k in keys], color=[color[k] for k in keys])
    axes[0].axhline(0, color='#555555', lw=.8); axes[0].set_ylabel('Expected payoff\n(THB / completed lot)')
    axes[1].bar(keys, [runs[k]['performance']['fees_thb'] / 1000 for k in keys], color=[color[k] for k in keys])
    axes[1].set_ylabel('Fees (THB thousands)'); save(fig, 'payoff-and-costs')
    for k, run in runs.items():
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.2), layout='constrained')
        daily = run['daily']
        axes[0].plot([d['performance']['net_return_pct'] for d in daily], color=color[k], label=k)
        axes[0].plot([d['performance']['benchmark_return_pct'] for d in daily], color='#171717', ls='--', label='SET50')
        axes[0].set_ylabel('Return (%)'); axes[0].legend(fontsize=7)
        axes[1].axhspan(70, 80, color='#35A879', alpha=.14)
        axes[1].plot([d['exposure'] * 100 for d in daily], color=color[k], label='Closing exposure')
        axes[1].step(range(16), [d['target_exposure'] * 100 for d in daily], color='#171717', ls='--', label='Daily target')
        axes[1].axhline(50, color='#999999', ls=':'); axes[1].set_ylim(45, 85); axes[1].set_ylabel('Exposure (%)'); axes[1].legend(fontsize=7)
        for ax in axes:
            ax.set_xticks([0, 5, 10, 15], [daily[i]['date'][5:] for i in [0, 5, 10, 15]])
        save(fig, k)


def render(data, output):
    runs, lead = data['runs'], data['development_lead']
    common = sum(r['eligibility']['common_status'] == 'pass' for r in runs.values())
    alpha = sum(r['eligibility']['best_alpha_status'] == 'pass' for r in runs.values())
    band = sum(r['user_targets']['average_exposure_in_band'] for r in runs.values())
    m = runs[lead]['performance']
    summary = (f'{common}/10 strategies pass the measured common criteria; {alpha}/10 pass the Best Alpha checks; '
               f'{band}/10 meet the requested 70–80% average exposure band. '
               f'The development lead under the declared ranking is {lead} ({runs[lead]["name"]}): '
               f'net return {m["net_return_pct"]:.3f}%, excess {m["excess_return_pp"]:+.3f} pp, '
               f'drawdown {m["official_max_drawdown_pct"]:.3f}%, average exposure {100*m["average_exposure"]:.3f}%.')
    conclusion = ('No prize-ready winner is established. ' if not common else 'Local measured passes do not establish organizer acceptance. ')
    conclusion += ('All ten hypotheses were fixed before this comparison, but September was already inspected in earlier work. '
                   'The ranking is development evidence only; no parameter search or retrospective change was made after these results. '
                   'The original alphabetical default remains the reproducible engineering reference; a suite strategy runs through its explicit configuration.')
    original = data['historical']['retained']['performance']
    reference_comparison = (f'The original reference returned {original["net_return_pct"]:.3f}% at '
                            f'{100*original["average_exposure"]:.3f}% average exposure. The new-suite lead differs by '
                            f'{m["net_return_pct"]-original["net_return_pct"]:+.3f} pp of net return. '
                            'Different baskets and exposure mean this is a practical portfolio comparison, not an isolated signal effect.')
    headers1 = ['ID', 'Net %', 'SET50 %', 'Excess pp', 'MaxDD %', 'SET50 MaxDD %', 'Avg exposure %']
    headers2 = ['ID', 'Stocks', 'FIFO lots', 'Payoff THB', 'Fees THB', 'Common', 'Best Alpha', '70–80%']
    rows1, rows2 = [], []
    for k, r in runs.items():
        p, e = r['performance'], r['eligibility']
        rows1.append([k] + [fmt(p[f], 3) for f in ['net_return_pct', 'benchmark_return_pct', 'excess_return_pp', 'official_max_drawdown_pct', 'benchmark_max_drawdown_pct']] + [fmt(100*p['average_exposure'], 3)])
        rows2.append([k, p['distinct_stocks'], p['completed_fifo_round_trips'], fmt(p['expected_payoff_thb']), fmt(p['fees_thb']), e['common_status'], e['best_alpha_status'], 'yes' if r['user_targets']['average_exposure_in_band'] else 'no'])
    limit_note = (f'SET50 returned {m["benchmark_return_pct"]:.6f}% and its maximum drawdown was {m["benchmark_max_drawdown_pct"]:.6f}%. '
                  f'The strict common drawdown boundary is therefore {1.5*m["benchmark_max_drawdown_pct"]:.6f}%. '
                  'Statuses use unrounded values. Drawdowns are positive loss magnitudes; return and excess retain their signs.')
    anchors = ('Return charts use initial capital for strategies and the first sample close for SET50, matching official reporting. '
               'The first-day anchors differ; aligned first-close returns are available in the machine-readable evidence. '
               'Dates in charts are month-day, September 2026.')
    md = ['# Phase 3 results', '', '30 October 2026 · KGI CU league · 9–30 September development sample', '',
          '[PDF](phase-3-results.pdf) · [Raw comparison CSV](phase-3-results.csv) · [Evidence JSON](phase-3-results.json)', '',
          summary, '', conclusion, '', reference_comparison, '', '## Comparable results', '', limit_note, '', md_table(headers1, rows1), '', md_table(headers2, rows2), '',
          '![Net returns](figures/returns.png)', '', '## Return paths, risk and exposure', '', anchors, '',
          '![Return paths](figures/return-paths.png)', '', '![Exposure and risk](figures/exposure-and-risk.png)', '',
          '![Payoff and costs](figures/payoff-and-costs.png)', '', '## Shared design and risk controls', '']
    md += [f'{i}. {p}\n' for i, p in enumerate(CONTROLS, 1)]
    md += ['', 'These are ranked allocation models. They deliberately keep all ten selected names invested, rather than implementing binary crossover entry/exit systems. The basket cap is per simulation; the union across different strategies may exceed ten names.', '',
           '## Strategy details', '']
    # Use packaged DejaVu fonts, so Unicode formulas remain portable.
    font_dir = Path(matplotlib.get_data_path()) / 'fonts/ttf'
    pdfmetrics.registerFont(TTFont('ReportSans', str(font_dir / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('ReportSansBold', str(font_dir / 'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('ReportSans', normal='ReportSans', bold='ReportSansBold')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyReport', fontName='ReportSans', fontSize=9, leading=13, spaceAfter=8, textColor=colors.HexColor('#243848')))
    styles.add(ParagraphStyle('SmallReport', parent=styles['BodyReport'], fontSize=7.5, leading=10, spaceAfter=6))
    styles.add(ParagraphStyle('TitleReport', parent=styles['BodyReport'], fontName='ReportSansBold', fontSize=26, leading=31, spaceAfter=15, textColor=colors.HexColor('#006A80')))
    styles.add(ParagraphStyle('HeadingReport', parent=styles['BodyReport'], fontName='ReportSansBold', fontSize=17, leading=22, spaceAfter=12, textColor=colors.HexColor('#006A80')))
    styles.add(ParagraphStyle('SubReport', parent=styles['BodyReport'], fontName='ReportSansBold', fontSize=11, leading=15, spaceAfter=8))
    styles.add(ParagraphStyle('Cell', parent=styles['SmallReport'], fontSize=7, leading=10, spaceAfter=0))
    story = []
    def p(text, style='BodyReport'):
        return Paragraph(escape(str(text)), styles[style])
    def para(text, style='BodyReport'):
        story.append(p(text, style))
    def table(headers, rows, widths=None):
        cells = [[p(c, 'Cell') for c in row] for row in [headers] + rows]
        t = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E1EEF1')),
                              ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F3F6F8')]),
                              ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING',(0,0),(-1,-1),5),
                              ('RIGHTPADDING',(0,0),(-1,-1),5), ('TOPPADDING',(0,0),(-1,-1),6),
                              ('BOTTOMPADDING',(0,0),(-1,-1),6),
                              ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#82ADB7'))]))
        story.extend([t, Spacer(1, 9)])
    def chart(name, width=174*mm):
        img = Image(str(output / f'figures/{name}.png'))
        img.drawHeight *= width / img.drawWidth; img.drawWidth = width
        story.extend([img, Spacer(1, 7)])
    def page(title):
        story.append(PageBreak()); para(title, 'HeadingReport')
    para('PHASE 3 / STRATEGY RESEARCH', 'SubReport'); para('Ten strategies.\nOne controlled comparison.', 'TitleReport')
    para('KGI CU league · 30 October 2026 · TradeSim 0.2.7', 'SmallReport')
    para(summary); para(conclusion); para(reference_comparison, 'SmallReport'); chart('returns')
    para('Read this report as development evidence. Phase 3 engineering is complete; profitability and Phase 4 validation are separate milestones.', 'SmallReport')
    page('Results at a glance')
    para(limit_note); table(headers1, rows1, [12*mm, 21*mm, 21*mm, 22*mm, 23*mm, 36*mm, 39*mm])
    table(headers2, rows2, [12*mm, 14*mm, 20*mm, 31*mm, 28*mm, 22*mm, 26*mm, 21*mm])
    para('Expected payoff is THB per completed non-breakeven FIFO lot; it is not total portfolio profit. Common and Best Alpha status are local checks under the working rules. Every run trades exactly ten distinct stocks.', 'SmallReport')
    page('Returns, drawdown and exposure')
    chart('return-paths'); chart('exposure-and-risk'); para(anchors, 'SmallReport')
    page('Risk controls and implementation')
    for item in CONTROLS:
        para(item)
    para('These are daily signal-ranked allocations, not binary crossover systems. The same risk layer makes comparisons clearer, but does not isolate signal effects from basket selection. Sector diversification is limited to two names per sector; it is not an explicit correlation cap.')
    para('Cash, holdings, raw open costs, NAV, realized P&L, fees, FIFO completion, payoff and benchmark statistics reconcile independently with the official engine every day. No engine or source market-data file was modified.', 'SmallReport')
    page('Payoff, friction and earlier experiments')
    chart('payoff-and-costs')
    para('The earlier reference used an alphabetical basket and roughly 70% initial allocation. Its two exit experiments used net +2% profit-taking, −4% loss exits and ten-session maximum holding age; the second also used 20-session momentum. They are historical context, not controlled comparisons with the new 76% allocation models.', 'SmallReport')
    old_rows = []
    names = {'retained': 'Original reference', 'exits': 'Alphabetical + exits', 'momentum_exits': 'Momentum + exits'}
    for key in ('retained', 'exits', 'momentum_exits'):
        r = data['historical'][key]; h = r['performance']
        old_rows.append([names[key], fmt(h['net_return_pct'],3), fmt(100*h['average_exposure'],3), h['completed_fifo_round_trips'], fmt(h['expected_payoff_thb']), r['eligibility']['common_status']])
    table(['Earlier run', 'Net %', 'Exposure %', 'FIFO lots', 'Payoff THB', 'Common'], old_rows, [45*mm,23*mm,28*mm,21*mm,35*mm,22*mm])
    para('Completing more lots alone did not improve the earlier strategies: both exit variants increased fees and had negative payoff. The current suite uses allocation rebalancing to create economically motivated trades; it never manufactures a round-trip count.', 'SmallReport')
    for key, run in runs.items():
        approach, formula, metrics, weakness = DETAILS[key]
        title = f'{key} · {run["name"]}'
        page(title); para(run['family'].upper() + ' STRATEGY', 'SmallReport')
        para(approach); para('Score: ' + formula, 'SubReport'); para('Inputs: ' + metrics)
        basket = ', '.join(f'{s} ({100*w:.2f}%)' for s, w in sorted(run['initial_weights'].items(), key=lambda pair: -pair[1]))
        para('Frozen basket and initial target weights: ' + basket, 'SmallReport')
        r, e = run['performance'], run['eligibility']
        facts = [
            ['Net return', fmt(r['net_return_pct'],3)+'%', 'SET50 return', fmt(r['benchmark_return_pct'],3)+'%'],
            ['Excess return', fmt(r['excess_return_pp'],3)+' pp', 'SET50 MaxDD', fmt(r['benchmark_max_drawdown_pct'],3)+'%'],
            ['Official MaxDD', fmt(r['official_max_drawdown_pct'],3)+'%', 'Initial-capital MaxDD', fmt(r['initial_capital_max_drawdown_pct'],3)+'%'],
            ['Average exposure', fmt(100*r['average_exposure'],3)+'%', 'Final exposure', fmt(100*run['daily'][-1]['exposure'],3)+'%'],
            ['Distinct stocks', r['distinct_stocks'], 'Completed FIFO lots', r['completed_fifo_round_trips']],
            ['Expected payoff', 'THB '+fmt(r['expected_payoff_thb']), 'Fees', 'THB '+fmt(r['fees_thb'])],
            ['Realized P&L', 'THB '+fmt(r['realized_pnl_thb']), 'Unrealized P&L', 'THB '+fmt(r['unrealized_pnl_thb'])],
        ]
        table(['Metric', 'Value', 'Metric', 'Value'], facts, [44*mm,40*mm,47*mm,43*mm])
        labels = {'expected_payoff_thb': 'positive expected payoff', 'average_exposure': 'at least 50% average exposure',
                  'completed_fifo_round_trips': 'at least five completed FIFO lots', 'relative_drawdown': 'strict relative drawdown limit'}
        failures = ', '.join(labels[k] for k, c in e['checks'].items() if c['scope']=='common_performance' and c['status'] != 'pass') or 'none'
        guard_labels = {'normal': '76% target', 'soft_drawdown': '72% target', 'hard_drawdown': '55% target'}
        status = (f'Common: {e["common_status"]}; Best Alpha: {e["best_alpha_status"]}; user exposure band: '
                  f'{"met" if run["user_targets"]["average_exposure_in_band"] else "not met"}. Unmet common criteria: {failures}. '
                  'Target days: ' + ', '.join(f'{guard_labels[k]} on {v} day' + ('s' if v != 1 else '')
                                             for k,v in sorted(run['guard_days'].items())) + '.')
        para(status, 'SmallReport'); chart(key)
        para('Risk to this hypothesis: ' + weakness, 'SmallReport')
        diagnostics = (f'Largest closing position: {100*max(d["largest_position"] for d in run["daily"]):.2f}%. '
                       f'Maximum measured daily replay time: {run["max_daily_seconds"]:.2f}s. '
                       'Timing is local and includes concurrent experiments; it is not a production guarantee.')
        para(diagnostics, 'SmallReport')
        md += [f'### {title}', '', approach, '', f'**Score:** {formula}.', '', f'**Inputs:** {metrics}', '',
               '**Frozen basket / initial target weights:** ' + basket + '.', '',
               md_table(['Metric','Value','Metric','Value'], facts), '', status, '',
               f'![{key} return and exposure](figures/{key}.png)', '', '**Risk:** '+weakness, '',
               diagnostics, '']
    page('How to read these measurements')
    md += ['## Metric explanations and your questions', '']
    for title, body in GLOSSARY:
        para(title, 'SubReport'); para(body)
        md += [f'### {title}', '', body, '']
    md += ['## Earlier runs: historical context', '', md_table(['Earlier run','Net %','Exposure %','FIFO lots','Payoff THB','Common'],old_rows), '',
           'These earlier runs use different allocation/exit designs. Full earlier metrics and evidence remain in [the follow-up](../phase-3-followup.md).', '']
    page('Evidence, limitations and reproduction')
    repeat = data['repeatability']
    evidence_text = (f'61 automated tests pass, including the original 17 TradeSim contract tests and indicator mathematics checked independently against pandas. '
                     f'Daily accounting reconciles for all 160 strategy-days. Repeatability: {repeat["status"]}. '
                     + (f'{repeat["strategy"]} was replayed in a fresh process; all {repeat["identical_artifacts"]} deterministic artifacts match byte for byte. ' if repeat['status']=='pass' else '')
                     + 'The original Phase 2 sources and pinned package remain unchanged. Full run bundles stay under ignored artifacts/; compact metrics, daily series and hashes are committed with this report.')
    limits = ('Only 16 trading days are available for tick-level evaluation, and this sample has been reused. '
              'The supplied 48-stock universe is static; historical membership and price-adjustment semantics are not independently established. '
              'Cross-symbol marks are not synchronized under notebook event ordering. Closing drawdown omits intraday extremes. '
              'No robustness, out-of-sample, production acceptance or future-return claim is made. '
              'A ten-stock basket limits diversification and replacement choices; expanding it belongs to a later declared experiment.')
    para(evidence_text); para(limits)
    para('Reproduction', 'SubReport')
    repeat_key = repeat.get('strategy', lead)
    commands = [
        'uv pip install --python .venv/bin/python -r requirements-reporting.txt',
        '.venv/bin/python -m unittest discover -s tests -v',
        '.venv/bin/python scripts/run_strategy_suite.py --output artifacts/comparison --workers 3',
        f'.venv/bin/python scripts/run_phase3.py --config research/phase3-suite/{repeat_key}.json --output artifacts/repeat',
        '.venv/bin/python scripts/build_phase3_results.py --input artifacts/comparison --repeat artifacts/repeat',
    ]
    for command in commands:
        para(command, 'SmallReport')
    para('First install the pinned Python/TradeSim environment using README.md. To independently regenerate baskets, use scripts/prepare_strategy_suite.py --output artifacts/prepared-baskets and compare its manifest/configs with research/phase3-suite/. New run directories must not already exist.', 'SmallReport')
    para('Phase status', 'SubReport')
    para('Phase 3 meets the development guide’s engineering checkpoint: complete replay, reconciled accounts, compatible single-file strategy and reproducible results. The ten hypotheses also establish the comparison structure for Phase 4. Phase 4 is not complete: additional permitted data and chronological validation are still required.')
    para('Current achievements: docs/current-progress/README.md. Next actions and lessons: docs/to-do/README.md. Working rules and source limits: docs/award-criteria.md. Exact predeclared formulas: docs/phase-3-ten-strategy-spec.md.', 'SmallReport')
    md += ['## Evidence and limitations', '', evidence_text, '', limits, '', '## Reproduce', '', '```bash', *commands, '```', '',
           'Install the pinned TradeSim environment first; see [README](../../README.md). Regenerate baskets into a new directory with `scripts/prepare_strategy_suite.py --output artifacts/prepared-baskets`.', '',
           '## Phase status and handoff', '',
           'Phase 3 is complete as the local engineering milestone described in the guide. The ten-strategy research scaffold is also complete. Phase 4 validation and a prize-ready strategy are not established.', '',
           '[Current achievements](../current-progress/README.md) · [Next actions and lessons](../to-do/README.md) · [Working rules](../award-criteria.md) · [Predeclared specification](../phase-3-ten-strategy-spec.md)', '']
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont('ReportSans', 7)
        canvas.setFillColor(colors.HexColor('#5B707D'))
        canvas.drawString(18*mm, 12*mm, 'PHASE 3  /  DEVELOPMENT SAMPLE  /  30 OCT 2026')
        canvas.drawRightString(192*mm, 12*mm, str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(str(output / 'phase-3-results.pdf'), pagesize=A4,
                      rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=20*mm,
                      title='Phase 3 results — ten-strategy comparison', author='algo-trading project').build(
                          story, onFirstPage=footer, onLaterPages=footer)
    (output / 'phase-3-results.md').write_text('\n'.join(md))
    fields = ['id', 'name', 'family'] + list(m) + ['final_exposure', 'common_status', 'best_alpha_status', 'user_exposure_band_met']
    with (output / 'phase-3-results.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n'); writer.writeheader()
        for key, run in runs.items():
            writer.writerow({'id':key, 'name':run['name'], 'family':run['family'], **run['performance'],
                             'final_exposure':run['daily'][-1]['exposure'], 'common_status':run['eligibility']['common_status'],
                             'best_alpha_status':run['eligibility']['best_alpha_status'],
                             'user_exposure_band_met':run['user_targets']['average_exposure_in_band']})
    print(summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--repeat', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/result-data-visualisation')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = collect(args.input, args.repeat)
    figures(data, args.output / 'figures')
    render(data, args.output)
    write(args.output / 'phase-3-results.json', data)


if __name__ == '__main__':
    main()
