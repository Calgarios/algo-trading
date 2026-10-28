"""Replay the official example with the official notebook's headless semantics."""
import argparse
import csv
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from package_support import PACKAGE, ROOT, sha256, verify_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory; existing paths are refused')
    parser.add_argument('--days', nargs='+', help='Contiguous sample dates in ascending order; default: all 16 days')
    args = parser.parse_args()
    provenance = verify_package()
    if sys.version_info[:2] != (3, 13):
        parser.error('Use Python 3.13 (validated with 3.13.5).')
    # Organizer tick_timestamp subtracts seven hours from naive Bangkok ticks.
    # UTC makes its epoch conversion deterministic across Linux hosts.
    os.environ['TZ'] = 'UTC'
    time.tzset()
    sys.path.insert(0, str(PACKAGE))
    import pandas as pd
    from tradeSim.TradeSim import tradeSim
    from tradeSim.StrategyHandler import StrategyHandler
    from strategy.Example_strategy import Example_strategy

    available = sorted(p.stem for p in (PACKAGE / 'marketInfo/ticks').glob('*.csv'))
    days = args.days or available
    if any(d not in available for d in days) or days != sorted(set(days)):
        parser.error('Dates must be unique available sample dates in ascending order.')
    if days != available[available.index(days[0]):available.index(days[-1]) + 1]:
        parser.error('Do not skip sample trading days within a run.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    code_files = ['scripts/run_phase2.py', 'scripts/package_support.py', 'requirements-phase2.txt']
    metadata = {
        'purpose': 'Phase 2 official example integration; not the Phase 3 strategy',
        'archive_sha256': provenance['archive_sha256'],
        'package_tree_sha256': provenance['tree_sha256'],
        'python': platform.python_version(),
        'dependencies': {p: importlib.metadata.version(p) for p in
                         ['numpy', 'pandas', 'python-dateutil', 'pytz', 'six', 'tzdata']},
        'code_sha256': {p: sha256(ROOT / p) for p in code_files},
        'days': days, 'team': 'example', 'initial_cash_thb': 10000000,
        'strategy': 'strategy.Example_strategy.Example_strategy',
        'event_order': 'notebook: sorted symbols, row-index round robin, original order within symbol',
        'timezone': 'UTC; raw tick times are naive Asia/Bangkok',
        'random_seed': None, 'randomness': 'No random operations in example or runner',
    }
    environment = {
        'platform': platform.platform(),
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'git_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
        'daily_seconds': {},
    }
    # Upstream history and benchmark readers use paths relative to cwd.
    os.chdir(PACKAGE)
    daily = []
    for day in days:
        started = time.perf_counter()
        frame = pd.read_csv(f'marketInfo/ticks/{day}.csv')
        frame['TradeDateTime'] = pd.to_datetime(frame['TradeDateTime'])
        if set(frame['TradeDateTime'].dt.strftime('%Y-%m-%d')) != {day}:
            raise ValueError(f'Mixed or unexpected dates in {day}')
        groups = {symbol: group.to_dict('records') for symbol, group in frame.groupby('ShareCode', sort=True)}
        sim = tradeSim('example', folder=str(output / 'engine'), current_date=day)
        runner = sim.get_strategy_runner()
        handlers = {s: StrategyHandler(Example_strategy, runner, str(PACKAGE / 'strategy')) for s in groups}
        for tick in range(max(map(len, groups.values()))):
            for symbol, rows in groups.items():
                if tick >= len(rows):
                    continue
                row = rows[tick]
                handlers[symbol].process_row(row)
                if not sim.isOrderbooksEmpty():
                    sim.isMatch(row)
                sim.update_market_prices({symbol: row['LastPrice']})
        sim.flushTransactionLog()
        sim.flushErrorLogger()
        sim.create_transaction_summarize('example')
        sim.save_summary_csv(pd.Timestamp(day).date(), university_start_date=days[0])
        sim.save_portfolio()
        info = runner.get_portfolio_info()
        holdings = runner.get_all_stocks_info()
        nav = runner.get_cash_balance() + sum(s['Market Value'] for s in holdings)
        if abs(nav - sim.portfolio.get_nav()) > 1e-6 or runner.get_cash_balance() < 0:
            raise AssertionError('Cash/holdings/NAV reconciliation failed')
        daily.append({'date': day, 'ticks': len(frame), 'metrics': info, 'holdings': holdings,
                      'raw': {'nav': sim.portfolio.get_nav(), 'cash': runner.get_cash_balance(),
                              'max_drawdown_pct': runner.get_max_draw_down(),
                              'average_exposure': runner.get_average_exposure(),
                              'expected_payoff': runner.get_expected_payoff()}})
        environment['daily_seconds'][day] = round(time.perf_counter() - started, 3)
        print(f'{day}: {len(frame):,} ticks, NAV {nav:,.2f}, {environment["daily_seconds"][day]:.2f}s', flush=True)

    fills_path = output / 'engine/example/example_transaction_log.csv'
    with fills_path.open() as stream:
        fills = list(csv.DictReader(stream))
    cash = 10000000.0
    quantities = {}
    total_fees = 0.0
    for fill in fills:
        amount = float(fill['Price']) * int(fill['Volume'])
        fee = amount * 0.00157 * 1.07
        total_fees += fee
        sign = 1 if fill['Side'] == 'Buy' else -1
        cash -= sign * amount + fee
        quantities[fill['Symbol']] = quantities.get(fill['Symbol'], 0) + sign * int(fill['Volume'])
        if quantities[fill['Symbol']] < 0 or cash < 0:
            raise AssertionError('Fill ledger violates cash/holdings constraints')
    final = daily[-1]['metrics']
    actual = {s['Symbol']: s['Actual Volume'] for s in daily[-1]['holdings']}
    if {s: q for s, q in quantities.items() if q} != actual or abs(cash - daily[-1]['raw']['cash']) > 1e-5:
        raise AssertionError('Independent fill ledger does not reconcile')
    summary = {'configuration': metadata, 'daily': daily,
               'reconciliation': {'cash_from_fills': cash, 'total_fees_thb': total_fees,
                                  'fill_rows': len(fills), 'distinct_traded_stocks': len(quantities)}}
    (output / 'report.json').write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n')
    (output / 'environment.json').write_text(json.dumps(environment, indent=2, sort_keys=True) + '\n')
    # Wall-clock log/summary columns vary; economic output is kept separate.
    deterministic = ['report.json', 'engine/example/example_portfolio.json',
                     'engine/example/example_transaction_log.csv']
    hashes = {p: sha256(output / p) for p in deterministic}
    (output / 'reproducible-hashes.json').write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n')
    print(json.dumps(hashes, indent=2))


if __name__ == '__main__':
    main()
