"""Build the visual Phase 4 research report from verified original-engine artifacts."""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import re
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'phase4-matplotlib'))
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

from package_support import ROOT, PACKAGE, sha256, verify_package
from phase4_diagnostics import analyze_bundle, analyze_run, read_json, write_json
from build_phase4_recovery import FILL_LOG, fill_slippage, verified_hashes
from run_phase4_comparisons import verify_declaration, PARITY_FILES
from run_phase4_control import declaration as reference_declaration
from phase4_lot_excursions import load_quotes, completed_excursions


ORDER = ['R76', 'C2', 'P-C2', 'C3', 'P-C3', 'H-C3', 'B-C3']
PAIRS = {'P-C2': 'C2', 'P-C3': 'C3', 'H-C3': 'C3', 'B-C3': 'C3'}
NAMES = {'R76': 'Alphabetical reference, 76% target', 'C2': 'Downside defence',
         'P-C2': 'C2 basket, equal weights', 'C3': 'Efficient breakout',
         'P-C3': 'C3 basket, equal weights', 'H-C3': 'C3 initial quantities, passive',
         'B-C3': 'C3 with 0.8% rebalance band'}
HYPOTHESES = {
    'P-C2': 'Replace daily ranked weights with equal weights in the same C2 basket; retain the guard and execution rules.',
    'P-C3': 'Replace daily ranked weights with equal weights in the same C3 basket; retain the guard and execution rules.',
    'H-C3': 'Freeze C3 initial quantities from pre-start features. Retry residual initial buys; do not sell or apply later daily de-risking.',
    'B-C3': 'Widen only the C3 rebalance activation band from 0.4% to 0.8% of opening NAV; continue actual residual fills once active.',
}
PALETTE = dict(zip(ORDER, ['#526772', '#3B6FAD', '#85A9D0', '#007F86', '#E1A035', '#8165B0', '#C96856']))


def compact(report, plans, raw):
    completed = raw['completed_lots']
    wins, losses = [l['pnl'] for l in completed if l['pnl'] > 0], [l['pnl'] for l in completed if l['pnl'] < 0]
    daily = [{'date': d['date'], 'nav': d['raw']['nav'], 'cash': d['raw']['cash'],
              **d['closing_risk'], 'performance': d['performance'],
              'target_exposure': d.get('target_exposure', .76),
              'drawdown_guard': d.get('drawdown_guard', 'reference_fixed_quantities'),
              'reconciled': d['reconciliation']['reconciled']} for d in report['daily']]
    return {**report, 'daily': daily,
            'payoff_detail': {'winning_lots': len(wins), 'losing_lots': len(losses),
                              'flat_lots': len(completed) - len(wins) - len(losses),
                              'mean_win_thb': sum(wins) / len(wins) if wins else None,
                              'mean_loss_thb': sum(losses) / len(losses) if losses else None},
            'initial_weights': plans[0]['plan'].get('weights', {}),
            'basket': plans[0]['plan']['selected']}


def load_run(folder, name, hashes=None):
    hashes = hashes or read_json(folder / 'reproducible-hashes.json')
    verified_hashes(folder, hashes)
    report, plans = read_json(folder / 'report.json'), read_json(folder / 'plans.json')
    days = report['configuration']['days']
    if ([p['date'] for p in plans] != days or len(days) != 16
            or sum(d['ticks'] for d in report['daily']) != 2906167):
        raise ValueError('Run does not cover the complete declared tick sample')
    for entry in plans:
        plan = entry['plan']
        if not plan['ready'] or len(plan['selected']) != 10:
            raise ValueError('Run contains an incomplete ten-name plan')
        if 'suite' in report['configuration']['parameters']:
            if any(f['history_end'] >= entry['date'] for f in plan['eligible'].values()):
                raise ValueError('Plan uses nonpast features')
    raw = analyze_bundle(folder, {**report, 'hashes': hashes})
    with (folder / FILL_LOG).open(newline='', encoding='utf-8-sig') as stream:
        concession = fill_slippage(csv.DictReader(stream))
    run = compact(report, plans, raw)
    run['name'] = name
    diagnostic = analyze_run(run)
    run.update({'raw_diagnostics': raw, 'fill_price_concession': concession,
                'diagnostics': diagnostic, 'hashes': hashes,
                'guard_days': dict(Counter(d['drawdown_guard'] for d in run['daily'])),
                'max_daily_seconds': max(read_json(folder / 'environment.json')['daily_seconds'].values())})
    return run


def collect(suite, controls, r76, test_log):
    package = verify_package()
    manifest = verify_declaration(ROOT / 'research/phase4-controls/configs')
    if read_json(controls / 'declaration.json') != manifest:
        raise ValueError('Comparison used a different declaration')
    parity = read_json(controls / 'parity.json')
    if parity['status'] != 'pass' or parity['identical_artifacts'] != PARITY_FILES:
        raise ValueError('Parity prerequisite has not passed')
    for path in PARITY_FILES:
        if sha256(controls / 'parity/original-C3' / path) != sha256(controls / 'parity/R-C3' / path):
            raise ValueError('Parity evidence changed')
    original = read_json(ROOT / 'docs/result-data-visualisation/phase-3-results.json')
    # Historical recovery is verified afresh, including strategies not carried into the small research set.
    for key, run in original['runs'].items():
        verified_hashes(suite / key, run['hashes'])
    runs = {'R76': load_run(r76 / 'run', NAMES['R76'])}
    r76_declaration = reference_declaration()
    r76_receipt = read_json(r76 / 'experiment.json')
    if (r76_receipt['state'] != 'completed' or r76_receipt['exit_code'] != 0
            or r76_receipt['declaration'] != r76_declaration
            or runs['R76']['configuration']['companion_config_sha256'] !=
            r76_declaration['source_sha256'][r76_declaration['config']]):
        raise ValueError('R76 differs from its completed predeclared experiment')
    for key in ('C2', 'C3'):
        runs[key] = load_run(suite / key, NAMES[key], original['runs'][key]['hashes'])
    statuses = read_json(controls / 'status.json')
    if set(statuses) != set(PAIRS) or any(s['exit_code'] != 0 for s in statuses.values()):
        raise ValueError('A declared comparison is missing or failed')
    for key in PAIRS:
        run = load_run(controls / key, NAMES[key])
        config = run['configuration']
        if config['companion_config_sha256'] != manifest['config_sha256'][key]:
            raise ValueError(f'Changed configuration: {key}')
        for path, digest in config['code_sha256'].items():
            expected = ('research/phase4-controls/strategy/DiversifiedBaseline.py'
                        if path == 'strategy/DiversifiedBaseline.py' else path)
            if digest != manifest['source_sha256'][expected]:
                raise ValueError(f'Changed replay source: {key}/{path}')
        runs[key] = run
    runs = {key: runs[key] for key in ORDER}
    quotes = load_quotes(PACKAGE, manifest['days'])
    for key, run in runs.items():
        folder = r76 / 'run' if key == 'R76' else suite / key if key in ('C2', 'C3') else controls / key
        with (folder / FILL_LOG).open(newline='', encoding='utf-8-sig') as stream:
            excursions = completed_excursions(csv.DictReader(stream), quotes)
        if len(excursions['completed_lots']) != run['performance']['completed_fifo_round_trips']:
            raise ValueError('Completed-lot excursion count differs from reconciled accounting')
        run['completed_quote_excursions'] = excursions
        run['raw_diagnostics']['slippage_attribution'] = 'Observed quote concession in fill_price_concession'
        run['raw_diagnostics']['intraday_adverse_excursion'] = 'Completed-lot gross quote paths in completed_quote_excursions'
        run['raw_diagnostics']['limitation'] = 'Quote excursions are not executable P&L or portfolio intraday drawdown'
    reference = runs['C3']['configuration']
    for key, run in runs.items():
        for field in ('days', 'archive_sha256', 'package_tree_sha256', 'dependencies', 'event_order', 'python'):
            if run['configuration'][field] != reference[field]:
                raise ValueError(f'Incomparable input: {key}/{field}')
    paired = {}
    for key, base in PAIRS.items():
        p, b = runs[key]['performance'], runs[base]['performance']
        exposure_gap = (p['average_exposure'] - b['average_exposure']) * 100
        delta = p['net_return_pct'] - b['net_return_pct']
        if abs(exposure_gap) > 2:
            decision = 'inconclusive_exposure_difference'
        elif delta <= 0:
            decision = 'reject_change_on_current_development_evidence'
        else:
            decision = 'retain_as_development_hypothesis_only'
        paired[key] = {'reference': base, 'net_return_change_pp': delta,
                       'exposure_change_pp': exposure_gap, 'exposure_comparable': abs(exposure_gap) <= 2,
                       'fees_change_thb': p['fees_thb'] - b['fees_thb'],
                       'completed_lots_change': p['completed_fifo_round_trips'] - b['completed_fifo_round_trips'],
                       'decision': decision, 'candidate_promoted': False}
    log = test_log.read_text()
    match = re.search(r'^Ran (\d+) tests', log, re.M)
    if not match or not re.search(r'^OK$', log, re.M) or re.search(r'^FAILED', log, re.M):
        raise ValueError('Provide the completed passing full-suite test log')
    return {'date_bangkok': '2026-10-30', 'sample_role': 'reused_development',
            'phase4_development_work_complete': True, 'phase4_validation_complete': False,
            'candidate_promoted': None, 'runs': runs, 'paired_comparisons': paired,
            'historical_original_reference': original['historical']['retained'],
            'historical_recovery': {'runs': 10, 'identical_artifacts': 90}, 'parity': parity,
            'test_count': int(match[1]), 'package': package,
            'blocked_work': ['Independent chronological validation and final evaluation: no additional permitted ticks',
                             'Effective-dated membership and broader-universe validation: membership history absent',
                             'Final-selection replay sensitivity: no qualified candidate to freeze'],
            'provenance': {'test_log_sha256': sha256(test_log),
                           'control_manifest_sha256': sha256(ROOT / 'research/phase4-controls/configs/manifest.json'),
                           'phase3_evidence_sha256': sha256(ROOT / 'docs/result-data-visualisation/phase-3-results.json'),
                           'code_sha256': {p: sha256(ROOT / p) for p in ('scripts/build_phase4_results.py',
                                         'scripts/build_phase4_recovery.py', 'scripts/phase4_diagnostics.py',
                                         'scripts/phase3_reporting.py', 'scripts/run_phase4_comparisons.py',
                                         'scripts/phase4_lot_excursions.py')}}}


def figures(data, folder):
    folder.mkdir()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.titleweight': 'bold', 'axes.labelcolor': '#243848',
                         'axes.titlesize': 11, 'figure.facecolor': 'white', 'axes.grid': True,
                         'grid.alpha': .15, 'grid.linestyle': '-'})
    runs = data['runs']
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(folder / f'{name}.png', dpi=180, bbox_inches='tight')
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(9.5, 4))
    values = [runs[k]['performance']['net_return_pct'] for k in ORDER]
    ax.barh(ORDER[::-1], values[::-1], color=[PALETTE[k] for k in ORDER[::-1]])
    for i, v in enumerate(values[::-1]):
        ax.text(v - .04, i, f'{v:.3f}%', ha='right', va='center', fontsize=9)
    ax.axvline(runs['C3']['performance']['benchmark_return_pct'], color='#666666', ls='--', label='SET50')
    ax.set_xlim(min(min(values), -4.1) - .9, .1)
    ax.set_xlabel('Net return after recorded costs (%)'); ax.set_title('Development results: all declared controls retained')
    ax.legend(loc='lower right'); save(fig, 'returns')
    dates = [d['date'][5:] for d in runs['C3']['daily']]
    x = np.arange(len(dates))
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    for ax, keys in zip(axes, [('R76', 'C2', 'P-C2'), ('R76', 'C3', 'P-C3', 'H-C3', 'B-C3')]):
        for key in keys:
            ax.plot(x, [d['performance']['net_return_pct'] for d in runs[key]['daily']], label=key, color=PALETTE[key])
        ax.plot(x, [d['performance']['benchmark_return_pct'] for d in runs['C3']['daily']], '--', color='#666666', label='SET50')
        ax.set_ylabel('Cumulative return (%)'); ax.legend(ncol=3, fontsize=8)
    axes[0].set_title('C2 controls'); axes[1].set_title('C3 controls')
    axes[1].set_xticks(x[::2], dates[::2]); save(fig, 'return-paths')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].axvspan(70, 80, color='#DDEEDC', label='Requested band')
    axes[0].barh(ORDER[::-1], [100 * runs[k]['performance']['average_exposure'] for k in ORDER[::-1]],
                 color=[PALETTE[k] for k in ORDER[::-1]])
    axes[0].set_xlim(50, 82); axes[0].set_xlabel('Average closing exposure (%)'); axes[0].legend(fontsize=8)
    for i, key in enumerate(ORDER[::-1]):
        p = runs[key]['performance']
        axes[1].scatter(p['official_max_drawdown_pct'], i, color=PALETTE[key], marker='o')
        axes[1].scatter(p['initial_capital_max_drawdown_pct'], i, color=PALETTE[key], marker='x')
    axes[1].scatter([], [], label='Official close-based', color='#526772', marker='o')
    axes[1].scatter([], [], label='Initial-capital anchor', color='#526772', marker='x')
    boundary = 1.5 * runs['C3']['performance']['benchmark_max_drawdown_pct']
    axes[1].axvline(boundary, ls='--', color='#B34B41', label=f'Strict boundary {boundary:.3f}%')
    axes[1].set_yticks(range(7), ORDER[::-1]); axes[1].set_xlim(0, boundary + .5)
    axes[1].set_xlabel('Maximum drawdown (%)'); axes[1].legend(fontsize=7, loc='lower right')
    save(fig, 'exposure-risk')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    fees = [runs[k]['performance']['fees_thb'] / 1000 for k in ORDER]
    concession = [runs[k]['fill_price_concession']['filled_price_concession_thb'] / 1000 for k in ORDER]
    axes[0].bar(ORDER, fees, color='#007F86', label='Commission / VAT')
    axes[0].bar(ORDER, concession, bottom=fees, color='#E1A035', label='Fill-price concession')
    axes[0].set_ylabel('THB thousands'); axes[0].set_title('Observed costs at actual fills'); axes[0].legend(fontsize=8)
    for i, key in enumerate(ORDER):
        payoff = runs[key]['performance']['expected_payoff_thb']
        if payoff is None:
            axes[1].text(i, 0, 'Undefined', rotation=90, ha='center', va='bottom', fontsize=8)
        else:
            axes[1].bar(i, payoff, color=PALETTE[key])
    axes[1].set_xticks(range(7), ORDER); axes[1].axhline(0, color='#777777', lw=.7)
    axes[1].set_ylim(top=400); axes[1].set_ylabel('THB per completed non-flat lot'); axes[1].set_title('Expected payoff')
    for ax in axes: ax.tick_params(axis='x', rotation=30)
    save(fig, 'costs-payoff')
    keys = ['C2', 'P-C2', 'C3', 'P-C3', 'H-C3', 'B-C3']
    symbols = sorted(set().union(*(set(runs[k]['basket']) for k in keys)))
    lookup = {k: {s['symbol']: s['net_pnl_thb'] / 1000 for s in runs[k]['raw_diagnostics']['symbols']} for k in keys}
    matrix = np.array([[lookup[k].get(s, np.nan) for k in keys] for s in symbols])
    fig, ax = plt.subplots(figsize=(9, 7))
    vmax = float(np.nanmax(np.abs(matrix)))
    im = ax.imshow(matrix, cmap='RdYlGn', vmin=-vmax, vmax=vmax, aspect='auto')
    for i in range(len(symbols)):
        for j in range(len(keys)):
            ink = 'white' if abs(matrix[i, j]) > .75 * vmax else '#243848'
            ax.text(j, i, '-' if np.isnan(matrix[i, j]) else f'{matrix[i,j]:.1f}',
                    ha='center', va='center', fontsize=8, color=ink)
    ax.set_xticks(range(len(keys)), keys); ax.set_yticks(range(len(symbols)), symbols); ax.grid(False)
    ax.set_title('Net symbol P&L (THB thousands); dash = not held'); fig.colorbar(im, ax=ax, shrink=.8)
    save(fig, 'symbol-attribution')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)
    for key, run in runs.items():
        lots = {(l['symbol'], l['order']): l for l in run['raw_diagnostics']['completed_lots']}
        excursions = run['completed_quote_excursions']['completed_lots']
        if not excursions:
            continue
        outcomes = [lots[(l['symbol'], l['order'])]['net_return_on_buy_cost_pct'] for l in excursions]
        ages = [lots[(l['symbol'], l['order'])]['holding_sessions'] for l in excursions]
        axes[0].scatter([l['mae_quote_pct'] for l in excursions], outcomes, color=PALETTE[key], alpha=.7, label=key)
        axes[1].scatter(ages, outcomes, color=PALETTE[key], alpha=.7, label=key)
    axes[0].set_xlabel('Maximum adverse quote excursion (%, gross)')
    axes[0].set_ylabel('Completed-lot net return (%)')
    axes[1].set_xlabel('Holding sessions to FIFO completion')
    for ax in axes:
        ax.axhline(0, color='#777777', lw=.7)
        ax.legend(fontsize=7, ncol=2)
    save(fig, 'lot-paths')
    for key, base in PAIRS.items():
        fig, axes = plt.subplots(2, 1, figsize=(9.5, 4.6), sharex=True)
        for model in (base, key):
            axes[0].plot(x, [d['performance']['net_return_pct'] for d in runs[model]['daily']], color=PALETTE[model], label=model)
            axes[1].plot(x, [100*d['exposure'] for d in runs[model]['daily']], color=PALETTE[model], label=model)
        axes[0].set_ylabel('Net return (%)'); axes[0].legend(ncol=2)
        axes[1].axhspan(70, 80, color='#DDEEDC', alpha=.7); axes[1].set_ylabel('Closing exposure (%)')
        axes[1].set_xticks(x[::2], dates[::2]); axes[0].set_title(f'{key} versus {base}')
        save(fig, key)


def fmt(v, n=3):
    return 'Undefined' if v is None else f'{v:,.{n}f}'


def render(data, output):
    runs = data['runs']
    eligible = sum(r['eligibility']['common_status'] == 'pass' for r in runs.values())
    summary = (f'{eligible}/7 compared portfolios pass the common criteria. No candidate is promoted. '
               'The declared development comparisons are complete; independent chronological validation remains blocked.')
    pc3 = runs['P-C3']['performance']
    finding = (f'P-C3, equal weights in the C3 basket, has common status {runs["P-C3"]["eligibility"]["common_status"]}: '
               f'{pc3["completed_fifo_round_trips"]} completed lots and THB {pc3["expected_payoff_thb"]:.2f} expected payoff. '
               f'Its net return is {pc3["net_return_pct"]:.6f}%, versus R76 at '
               f'{runs["R76"]["performance"]["net_return_pct"]:.6f}%. It fails Best Alpha and does not beat R76.')
    status = ('Phase 4 is not fully complete. The engineering, diagnostics and declared September experiments are complete. '
              'No additional permitted tick period or effective-dated membership is available, so the validation checkpoint '
              'cannot be certified. The original reference remains the fallback; entry into Phase 5 is not a claim of validated alpha.')
    headers = ['ID', 'Net %', 'Excess pp', 'MaxDD %', 'Exposure %', 'FIFO', 'Payoff THB']
    rows = [[k, fmt(runs[k]['performance']['net_return_pct']), fmt(runs[k]['performance']['excess_return_pp']),
             fmt(runs[k]['performance']['official_max_drawdown_pct']), fmt(100*runs[k]['performance']['average_exposure']),
             runs[k]['performance']['completed_fifo_round_trips'], fmt(runs[k]['performance']['expected_payoff_thb'], 2)] for k in ORDER]
    def md_table(h, rr):
        return '\n'.join(['| '+' | '.join(map(str,h))+' |', '| '+' | '.join(['---']*len(h))+' |']
                         + ['| '+' | '.join(map(str,r))+' |' for r in rr])
    md = ['# Phase 4 results', '', '30 October 2026 · KGI CU league · September development sample', '',
          '[PDF](phase-4-results.pdf) · [CSV](phase-4-results.csv) · [Evidence JSON](phase-4-results.json)', '',
          summary, '', finding, '', status, '', '![Returns](figures/returns.png)', '', '## Comparable metrics', '', md_table(headers, rows), '',
          'SET50 return and drawdown: −4.099496% and 4.099496%. The strict portfolio drawdown boundary is 6.149244%. '
          'Exposure is the mean of 16 daily closes. Payoff is per completed non-breakeven FIFO lot, not a forecast.', '',
          '## Paths, risk and costs', '', '![Return paths](figures/return-paths.png)', '',
          '![Exposure and drawdown](figures/exposure-risk.png)', '', '![Costs and payoff](figures/costs-payoff.png)', '',
          'Official portfolio return starts at initial capital; SET50 starts at its first sample close. '
          'First-close-aligned excess and initial-capital drawdown are retained separately in the tables below and JSON. '
          'Price concession is measured against the execution tick quote. Fixed-fill add-backs and fee stresses do not simulate changed execution.', '',
          '## Symbol attribution', '', '![Symbol P&L](figures/symbol-attribution.png)', '']
    font_dir = Path(matplotlib.get_data_path()) / 'fonts/ttf'
    pdfmetrics.registerFont(TTFont('Phase4Sans', str(font_dir / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('Phase4Bold', str(font_dir / 'DejaVuSans-Bold.ttf')))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('P4Body', fontName='Phase4Sans', fontSize=9, leading=13, spaceAfter=8, textColor=colors.HexColor('#243848')))
    styles.add(ParagraphStyle('P4Small', parent=styles['P4Body'], fontSize=7.5, leading=10))
    styles.add(ParagraphStyle('P4Title', parent=styles['P4Body'], fontName='Phase4Bold', fontSize=26, leading=31, textColor=colors.HexColor('#006A80'), spaceAfter=16))
    styles.add(ParagraphStyle('P4Heading', parent=styles['P4Title'], fontSize=17, leading=22))
    story = []
    def p(text, small=False):
        story.append(Paragraph(escape(str(text)), styles['P4Small' if small else 'P4Body']))
    def heading(text, first=False):
        if not first: story.append(PageBreak())
        story.append(Paragraph(escape(text), styles['P4Title' if first else 'P4Heading']))
    def chart(name, width=174*mm):
        img = Image(str(output / f'figures/{name}.png'))
        img.drawHeight *= width / img.drawWidth; img.drawWidth = width
        story.extend([img, Spacer(1, 8)])
    def table(h, rr, widths):
        cells = [[Paragraph(escape(str(c)), styles['P4Small']) for c in row] for row in [h]+rr]
        t = Table(cells, colWidths=[w*mm for w in widths], repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E1EEF1')),
                              ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F8')]),
                              ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),5),
                              ('RIGHTPADDING',(0,0),(-1,-1),5), ('TOPPADDING',(0,0),(-1,-1),5),
                              ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.extend([t, Spacer(1,10)])
    heading('Phase 4\nEvidence before complexity', True)
    p('KGI CU league | 30 October 2026 | TradeSim 0.2.7', True)
    p(summary); p(finding); p(status); chart('returns')
    p('Seven portfolios: the 76% reference, C2/C3 and four predeclared controls. The original 70% reference remains historical context. All results are development evidence.', True)
    heading('Results and eligibility')
    table(headers, rows, [17,22,23,24,28,18,42])
    eligibility_rows = [[k, runs[k]['eligibility']['common_status'], runs[k]['eligibility']['best_alpha_status'],
                         fmt(runs[k]['performance']['aligned_first_close_excess_pp']),
                         fmt(runs[k]['performance']['initial_capital_max_drawdown_pct'])] for k in ORDER]
    table(['ID','Common','Best Alpha','Aligned excess pp','Initial-capital DD %'], eligibility_rows,[20,31,33,45,45])
    p('The benchmark returned -4.099496%, with 4.099496% maximum drawdown. Portfolio drawdown must be strictly below 6.149244%. All portfolios trade ten distinct names. Common criteria require at least five completed lots, at least 50% average exposure, positive payoff and the drawdown test. Best Alpha adds nonnegative total and excess return.', True)
    p('The user exposure preference is 70-80%. Undefined payoff means there are no completed non-flat lots; it is not zero profit. Completed FIFO lots are not independent investment decisions.', True)
    historical = data['historical_original_reference']['performance']
    reference_note = (f'The original 70%-target reference returned {historical["net_return_pct"]:.6f}% '
                      f'at {historical["average_exposure"]*100:.6f}% average exposure. '
                      f'R76 changes net return by {runs["R76"]["performance"]["net_return_pct"]-historical["net_return_pct"]:+.6f} pp. '
                      'The original remains the engineering fallback; neither reference has completed-lot payoff evidence.')
    p(reference_note, True)
    md += ['## Additional anchors and eligibility', '', md_table(['ID','Common','Best Alpha','Aligned excess pp','Initial-capital DD %'], eligibility_rows), '']
    md += [reference_note, '']
    heading('Daily return paths'); chart('return-paths')
    p('All portfolios receive the same 2,906,167 ticks, 16 sessions and costs in notebook symbol/row-index order. Portfolio and benchmark initial anchors differ; use the aligned metrics alongside official results. Cross-symbol marks are not synchronized.', True)
    heading('Risk, exposure and trading costs'); chart('exposure-risk'); chart('costs-payoff')
    p('Drawdown uses daily closes; it does not describe intraday troughs. The passive control deliberately omits the daily de-risking guard. Costs here are observed commission/VAT and adverse price ticks, not a fitted transaction-cost model.', True)
    heading('Where the losses occurred'); chart('symbol-attribution')
    p('Every cell includes realized and unrealized P&L after costs. A dash means the symbol was not held. Symbol totals reconcile to portfolio P&L; the CSV/JSON keep the full attribution and completed-lot outcomes.', True)
    for key, base in PAIRS.items():
        r, c, pmetrics = runs[key], data['paired_comparisons'][key], runs[key]['performance']
        decision = c['decision'].replace('_', ' ')
        explanation = (f'Net return change versus {base}: {c["net_return_change_pp"]:+.6f} pp; '
                       f'average exposure change: {c["exposure_change_pp"]:+.6f} pp; '
                       f'commission/VAT change: THB {c["fees_change_thb"]:+,.2f}. Decision: {decision}. No promotion.')
        facts = [['Net return', fmt(pmetrics['net_return_pct'])+'%', 'Average exposure',fmt(pmetrics['average_exposure']*100)+'%'],
                 ['Official drawdown',fmt(pmetrics['official_max_drawdown_pct'])+'%', 'SET50 excess',fmt(pmetrics['excess_return_pp'])+' pp'],
                 ['Completed lots',pmetrics['completed_fifo_round_trips'],'Expected payoff',fmt(pmetrics['expected_payoff_thb'],2)+' THB'],
                 ['Realized P&L',fmt(pmetrics['realized_pnl_thb'],2),'Unrealized P&L',fmt(pmetrics['unrealized_pnl_thb'],2)]]
        heading(f'{key}: {NAMES[key]}'); p(HYPOTHESES[key]); table(['Metric','Value','Metric','Value'],facts,[43,44,43,44])
        p(explanation); chart(key)
        note = ('The passive comparison changes both ongoing allocation and the guard. It cannot isolate the value of reranking alone. No terminal sales were forced.' if key=='H-C3'
                else 'The basket, initial capital, cost model and execution order match the paired reference. Guard triggers can differ as portfolio paths diverge; this is part of the resulting behavior.')
        p(note,True)
        p('Guard days: '+', '.join(f'{k}: {v}' for k,v in r['guard_days'].items())+f'. Maximum local daily runtime: {r["max_daily_seconds"]:.3f}s.', True)
        md += [f'## {key}: {NAMES[key]}','',HYPOTHESES[key],'',md_table(['Metric','Value','Metric','Value'],facts),'',explanation,'',f'![{key} comparison](figures/{key}.png)','',note,'']
    heading('Completed lots: price paths and holding horizons')
    chart('lot-paths')
    excursion_note = ('Each dot is one completed FIFO buy lot, not an independent investment idea. '
                      'Quote MAE/MFE use the first buy through final close, relative to the gross average buy fill price. '
                      'Known entry/exit quotes and strictly interior timestamps exclude ambiguous other ticks at the same boundary times. '
                      'Quotes include auctions; commissions, exit slippage and shrinking quantities after partial sales are not modeled by this path measure. '
                      'This is retrospective diagnosis, never a strategy input or an executable liquidation return. Still-open lots are excluded.')
    p(excursion_note)
    p('A positive payoff on completed lots can coexist with a negative portfolio return because most loss may remain unrealized. Compare realized and unrealized P&L and the symbol heatmap before drawing an entry-quality conclusion.',True)
    md += ['## Completed-lot price paths','', '![Completed-lot paths](figures/lot-paths.png)','',excursion_note,'']
    heading('Verification, boundaries and phase status')
    evidence = (f'{data["test_count"]} tests pass. All 90 deterministic artifacts from ten restored Phase 3 runs match their committed hashes. '
                'The research copy passes a two-day parity check for five behavioral artifacts and all performance metrics. '
                'All 112 strategy-days in this seven-portfolio comparison reconcile; the official package and Phase 3 reference sources remain unchanged.')
    p(evidence); p(status)
    p('The September sample has been repeatedly inspected. Parameter changes and rankings here do not establish out-of-sample expectancy. Validation and final evaluation periods remain unassigned until additional permitted ticks and effective-dated membership are supplied. The static 48-stock universe cannot establish historical membership.',True)
    p('The declared 15-name expansion is blocked on its membership requirement. Actual replay sensitivity to costs/lookbacks/liquidity is a final-selection task; no qualified candidate is available to freeze. Fixed-fill fee stresses of +25% and +50% remain diagnostic arithmetic and are saved in JSON.',True)
    p('Portfolio intraday drawdown, production event ordering, restart durability, registered owner and organizer acceptance remain unresolved. Completed-lot quote excursions do not resolve those questions. Local runtime is measured, not a production guarantee.',True)
    heading('Handoff: what is finished and what comes next')
    handoff = [['Completed','Archive recovery; engine tests; 90-artifact reproduction; symbol/FIFO/cost diagnostics; R76 and four declared controls; visual report and retained outcomes.'],
               ['Blocked Phase 4 work','Obtain permitted additional tick periods, effective-dated membership and adjustment/publication semantics; declare chronological development/validation/final periods before inspecting results.'],
               ['Decision','Keep the original engineering reference. Retain only explicitly labeled development hypotheses; no qualified or robustly profitable candidate is established.'],
               ['Before candidate promotion','Validate a frozen candidate against R76 and its paired control, positive payoff/common criteria and 70-80% exposure. If evidence fails, revise the hypothesis and retain the fallback.'],
               ['Phase 5 continuation','The guide permits work from a retained baseline. Keep the original fallback and P-C3 as a research comparator; study sizing, guard recovery, concentration drift and turnover. Phase 4 validation stays open.']]
    table(['Status','Action / evidence'],handoff,[36,138])
    p('Continue from docs/current-progress/README.md and docs/to-do/README.md. Frozen declarations are in research/phase4/ and research/phase4-controls/configs/. Full logs, exact strategy/config bundles and raw fills are in ignored artifacts/.',True)
    md += ['## Verification and phase status','',evidence,'',status,'','## Handoff','',md_table(['Status','Action / evidence'],handoff),'',
           'See [current progress](../../current-progress/README.md) and [next actions](../../to-do/README.md). '
           'Full run bundles stay under ignored artifacts; this report is reproducible with scripts/build_phase4_results.py.', '']
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont('Phase4Sans',7); canvas.setFillColor(colors.HexColor('#5B707D'))
        canvas.drawString(18*mm,12*mm,'PHASE 4 / SEPTEMBER DEVELOPMENT / 30 OCT 2026')
        canvas.drawRightString(192*mm,12*mm,str(doc.page)); canvas.restoreState()
    SimpleDocTemplate(str(output/'phase-4-results.pdf'),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,
                      topMargin=16*mm,bottomMargin=20*mm,title='Phase 4 research results',author='algo-trading project').build(story,onFirstPage=footer,onLaterPages=footer)
    (output/'phase-4-results.md').write_text('\n'.join(md))
    with (output/'phase-4-results.csv').open('w',newline='') as stream:
        fields=['id','name',*runs['C3']['performance'],'common_status','best_alpha_status']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for key,run in runs.items():
            writer.writerow({'id':key,'name':run['name'],**run['performance'],
                             'common_status':run['eligibility']['common_status'],'best_alpha_status':run['eligibility']['best_alpha_status']})
    write_json(output/'phase-4-results.json',data)
    print(summary)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',type=Path,required=True)
    parser.add_argument('--controls',type=Path,required=True)
    parser.add_argument('--r76',type=Path,required=True)
    parser.add_argument('--test-log',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Output exists; preserve prior report and select a new directory')
    data=collect(args.suite.resolve(),args.controls.resolve(),args.r76.resolve(),args.test_log.resolve())
    args.output.mkdir(parents=True,exist_ok=False)
    figures(data,args.output/'figures')
    render(data,args.output)


if __name__=='__main__':
    main()
