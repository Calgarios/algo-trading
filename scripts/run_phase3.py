"""Replay the team baseline through unchanged TradeSim and reconcile every day."""
import argparse
import csv
import importlib.metadata
import json
from math import isclose
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from package_support import PACKAGE, ROOT, sha256, verify_package
from phase3_reporting import FillLedger, benchmark_metrics, eligibility, performance
from phase3_support import check_submission_shape, load_baseline


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def markdown_report(report):
    metrics = report['performance']
    lines = ['# Phase 3 baseline reference', '',
             'Integration sample; working award rules, not competition acceptance.', '',
             '| Metric | Value |', '| --- | ---: |']
    for key, value in metrics.items():
        lines.append(f'| {key} | {"unknown" if value is None else format(value, ".8f")} |')
    lines += ['', '| Working criterion | Status |', '| --- | --- |']
    for key, check in report['eligibility']['checks'].items():
        lines.append(f'| {key} | {check["status"]} |')
    lines += ['', 'All daily cash, holdings, open cost, NAV, realized P&L, FIFO completion and payoff checks reconciled.',
              '', 'Official return uses initial cash; SET50 uses the first sample close. Official drawdown',
              'uses daily closes only. Initial-capital drawdown and aligned first-close returns are separate.',
              'No payoff is inferred when there are no non-breakeven completed lots.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    parser.add_argument('--days', nargs='+', help='Contiguous ordered sample dates; default all 16')
    args = parser.parse_args()
    provenance = verify_package()
    if sys.version_info[:2] != (3, 13):
        parser.error('Use Python 3.13 (validated with 3.13.5).')
    compatibility = check_submission_shape()
    config = json.loads((ROOT / 'strategy/baseline.json').read_text())
    with (PACKAGE / 'marketInfo/symbolSET50/Symbol_SET50.csv').open(encoding='utf-8-sig') as stream:
        universe = sorted(r['Symbol'] for r in csv.DictReader(stream))
    if config['universe'] != universe:
        parser.error('Companion universe differs from the pinned supplied constituents.')
    available = sorted(p.stem for p in (PACKAGE / 'marketInfo/ticks').glob('*.csv'))
    days = args.days or available
    if not days or any(d not in available for d in days) or days != sorted(set(days)):
        parser.error('Dates must be unique available sample dates in ascending order.')
    if days != available[available.index(days[0]):available.index(days[-1]) + 1]:
        parser.error('Do not skip sample trading days within a run.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ['TZ'] = 'UTC'
    time.tzset()
    sys.path.insert(0, str(PACKAGE))
    import pandas as pd
    from tradeSim.TradeSim import tradeSim
    from tradeSim.StrategyHandler import StrategyHandler
    strategy_class = load_baseline()
    code_files = ['strategy/DiversifiedBaseline.py', 'strategy/baseline.json',
                  'scripts/run_phase3.py', 'scripts/phase3_reporting.py', 'scripts/phase3_support.py',
                  'scripts/package_support.py', 'requirements-phase2.txt', 'docs/phase-3-baseline-spec.md']
    metadata = {
        'purpose': 'Phase 3 deterministic diversified integration baseline; not untouched validation',
        'archive_sha256': provenance['archive_sha256'], 'package_tree_sha256': provenance['tree_sha256'],
        'python': platform.python_version(),
        'dependencies': {p: importlib.metadata.version(p) for p in
                         ['numpy', 'pandas', 'python-dateutil', 'pytz', 'six', 'tzdata']},
        'code_sha256': {p: sha256(ROOT / p) for p in code_files}, 'days': days,
        'team': 'baseline', 'strategy': 'DiversifiedBaseline', 'parameters': config,
        'event_order': 'notebook: sorted symbols, row-index round robin, original order within symbol',
        'timezone': 'UTC logs; raw ticks and decision bars are naive Asia/Bangkok',
        'random_seed': None, 'randomness': 'No random operations',
    }
    environment = {'platform': platform.platform(),
                   'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
                   'daily_seconds': {}}
    benchmark_path = PACKAGE / 'marketInfo/benchmark/SET50.csv'
    benchmark_rows = list(csv.DictReader(benchmark_path.open())) if benchmark_path.exists() else []
    os.chdir(PACKAGE)  # Official history/benchmark paths are relative to cwd.
    ledger, daily, plans = FillLedger(), [], []
    decision_count = order_count = partial_count = zero_count = rejected_count = 0
    with (output / 'decisions.jsonl').open('w') as decision_log:
        for day in days:
            started = time.perf_counter()
            frame = pd.read_csv(f'marketInfo/ticks/{day}.csv')
            frame['TradeDateTime'] = pd.to_datetime(frame['TradeDateTime'])
            if set(frame['TradeDateTime'].dt.strftime('%Y-%m-%d')) != {day}:
                raise ValueError(f'Mixed dates in {day}')
            groups = {s: g.to_dict('records') for s, g in frame.groupby('ShareCode', sort=True)}
            if not set(groups) <= set(universe):
                raise ValueError('Tick symbols outside supplied universe')
            sim = tradeSim('baseline', folder=str(output / 'engine'), current_date=day)
            runner = sim.get_strategy_runner()
            handlers = {s: StrategyHandler(strategy_class, runner, str(ROOT / 'strategy')) for s in groups}
            seen_plans, plan = set(), None
            for tick in range(max(map(len, groups.values()))):
                for symbol, rows in groups.items():
                    if tick >= len(rows):
                        continue
                    row, handler = rows[tick], handlers[symbol]
                    before = handler.strategy.decision_sequence
                    handler.process_row(row)
                    if symbol not in seen_plans:
                        if plan is None:
                            plan = handler.strategy.plan
                        elif plan != handler.strategy.plan:
                            raise AssertionError('Symbol instances disagree on the daily plan')
                        seen_plans.add(symbol)
                    if handler.strategy.decision_sequence != before:
                        decision = handler.strategy.last_decision
                        decision_log.write(json.dumps(decision, sort_keys=True, allow_nan=False) + '\n')
                        decision_count += 1
                        if decision['requested_quantity']:
                            order_count += 1
                            partial_count += 0 < decision['filled_quantity'] < decision['requested_quantity']
                            zero_count += decision['filled_quantity'] == 0
                            rejected_count += not decision['accepted']
                    if not sim.isOrderbooksEmpty():
                        raise AssertionError('Baseline must not leave pending orders')
                    sim.update_market_prices({symbol: row['LastPrice']})
            plans.append({'date': day, 'plan': plan})
            for fill in sim.execution.tranLog.transaction_log:
                ledger.apply(fill)
            sim.flushTransactionLog()
            sim.flushErrorLogger()
            sim.create_transaction_summarize('baseline')
            sim.save_summary_csv(pd.Timestamp(day).date(), university_start_date=days[0])
            sim.save_portfolio()
            holdings = runner.get_all_stocks_info()
            prices = {s: rows[-1]['LastPrice'] for s, rows in groups.items()}
            # A missing closing quote for a held name is an error, not a fabricated valuation.
            reconciliation = ledger.reconcile(
                runner.get_cash_balance(), holdings, sim.portfolio.get_nav(), prices,
                runner.get_round_trip_count(), sim.portfolio.get_realized(), runner.get_expected_payoff(),
                {h['Symbol']: sum(lot.get_buy_price() * lot.get_actual_vol()
                                  for lot in sim.portfolio.get_stock_by_symbol(h['Symbol'])) for h in holdings})
            nav, cash = sim.portfolio.get_nav(), runner.get_cash_balance()
            concentration = max((h['Market Value'] / nav for h in holdings), default=0.0)
            daily.append({'date': day, 'ticks': len(frame), 'holdings': holdings,
                          'official_display_metrics': runner.get_portfolio_info(),
                          'raw': {'nav': nav, 'cash': cash, 'official_max_drawdown_pct': runner.get_max_draw_down(),
                                  'average_exposure': runner.get_average_exposure(),
                                  'official_expected_payoff_thb': runner.get_expected_payoff()},
                          'closing_risk': {'exposure': (nav - cash) / nav, 'largest_position': concentration,
                                           'above_buy_exposure_limit': (nav - cash) / nav > config['max_exposure'],
                                           'above_buy_position_limit': concentration > config['max_position']},
                          'reconciliation': reconciliation})
            benchmark = benchmark_metrics(benchmark_rows, days[:len(daily)])
            metrics = performance(daily, ledger, benchmark)
            for key, observed in [('official_max_drawdown_pct', runner.get_max_draw_down()),
                                  ('average_exposure', runner.get_average_exposure())]:
                if not isclose(metrics[key], observed, rel_tol=1e-10, abs_tol=1e-9):
                    raise AssertionError(f'Independent {key} differs from engine')
            if benchmark['complete']:
                for expected, observed in [(benchmark['return_pct'], sim.portfolio.benchmark_return),
                                           (benchmark['max_drawdown_pct'], sim.portfolio.benchmark_max_dd)]:
                    if not isclose(expected, observed, rel_tol=1e-10, abs_tol=1e-9):
                        raise AssertionError('Independent benchmark differs from engine')
            daily[-1]['eligibility'] = eligibility(metrics)
            environment['daily_seconds'][day] = round(time.perf_counter() - started, 3)
            print(f'{day}: {len(frame):,} ticks, NAV {nav:,.2f}, fills {ledger.fill_count}, '
                  f'{environment["daily_seconds"][day]:.2f}s', flush=True)
    report = {'configuration': metadata, 'compatibility': compatibility, 'daily': daily,
              'performance': metrics, 'eligibility': eligibility(metrics),
              'reconciliation': daily[-1]['reconciliation'],
              'execution': {'decisions': decision_count, 'order_attempts': order_count,
                            'partial_fills': partial_count, 'zero_fills': zero_count,
                            'rejected_responses': rejected_count},
              'limitations': ['Static supplied universe; no effective-dated membership',
                              'Latest marks across symbols are not synchronized',
                              'Local owner baseline is not a verified registered identity',
                              'Working rules and actual organizer acceptance remain unconfirmed']}
    write_json(output / 'report.json', report)
    write_json(output / 'plans.json', plans)
    write_json(output / 'fifo.json', {'completed': ledger.completed,
                                    'open': {s: list(lots) for s, lots in ledger.lots.items() if lots}})
    write_json(output / 'environment.json', environment)
    (output / 'report.md').write_text(markdown_report(report))
    paths = ['report.json', 'report.md', 'plans.json', 'fifo.json', 'decisions.jsonl',
             'engine/baseline/baseline_portfolio.json', 'engine/baseline/baseline_transaction_log.csv']
    write_json(output / 'reproducible-hashes.json', {p: sha256(output / p) for p in paths})
    print(json.dumps(metrics, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
