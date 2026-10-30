"""Freeze ten strategy baskets using only history before the shared start date."""
import argparse
import csv
import json
import os
from pathlib import Path
import sys
import time

from package_support import PACKAGE, ROOT, sha256, verify_package
from phase3_support import load_baseline


STRATEGIES = {
    'C1': ('Custom', 'Risk-adjusted momentum'), 'C2': ('Custom', 'Downside defence'),
    'C3': ('Custom', 'Efficient breakout'), 'C4': ('Custom', 'Trend pullback'),
    'C5': ('Custom', 'Balanced ensemble'), 'T1': ('Indicator', 'SMA trend'),
    'T2': ('Indicator', 'EMA trend'), 'T3': ('Indicator', 'MACD acceleration'),
    'T4': ('Indicator', 'RSI pullback'), 'T5': ('Indicator', 'Bollinger reversion'),
}


def select_basket(scores, sectors):
    selected, counts = [], {}
    for symbol in sorted(scores, key=lambda s: (-scores[s], s)):
        sector = sectors[symbol]
        if counts.get(sector, 0) >= 2:
            continue
        selected.append(symbol)
        counts[sector] = counts.get(sector, 0) + 1
        if len(selected) == 10:
            break
    if len(selected) != 10:
        raise ValueError('Insufficient sector diversity for ten-stock basket')
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-09-09')
    parser.add_argument('--output', type=Path, default=ROOT / 'research/phase3-suite')
    args = parser.parse_args()
    provenance = verify_package()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ['TZ'] = 'UTC'
    time.tzset()
    sys.path.insert(0, str(PACKAGE))
    from tradeSim.TradeSim import tradeSim
    strategy = load_baseline()
    config = json.loads((ROOT / 'strategy/baseline.json').read_text())
    config.update({'target_exposure': .76})
    with (PACKAGE / 'marketInfo/symbolSET50/Symbol_SET50.csv').open(encoding='utf-8-sig') as stream:
        sectors = {r['Symbol']: r['Sector'] for r in csv.DictReader(stream)}
    os.chdir(PACKAGE)
    # Metadata-only reader; never supplies a decision with future CSV rows.
    sim = tradeSim('suite-inspection', folder=str(ROOT / 'artifacts/suite-preparation'), current_date=args.start)
    runner = sim.get_strategy_runner()
    benchmark = runner.get_historical_data('SET50', 180, '1D')
    features, rejected = {}, {}
    for symbol in config['universe']:
        try:
            features[symbol] = strategy.suite_features(runner.get_historical_data(symbol, 180, '1D'), benchmark, args.start)
        except (ValueError, KeyError, TypeError) as error:
            rejected[symbol] = str(error)
    liquid = sorted(features, key=lambda s: (-features[s]['median_value20'], s))[:30]
    pool = {s: features[s] for s in liquid}
    plans = {}
    for key, (family, name) in STRATEGIES.items():
        scores = strategy.suite_scores(pool, key)
        basket = select_basket(scores, sectors)
        parameters = {**config, 'suite': {'id': key, 'family': family, 'name': name,
                                         'start_date': args.start, 'basket': basket,
                                         'sectors': {s: sectors[s] for s in basket}}}
        path = output / f'{key}.json'
        path.write_text(json.dumps(parameters, indent=2, sort_keys=True, allow_nan=False) + '\n')
        plans[key] = {'name': name, 'family': family, 'basket': basket,
                      'initial_scores': scores, 'config_sha256': sha256(path)}
    manifest = {'start_date': args.start, 'data': provenance, 'eligible_features': features,
                'rejected': rejected, 'liquidity_pool': liquid, 'strategies': plans,
                'source_sha256': {p: sha256(ROOT / p) for p in
                                  ['strategy/DiversifiedBaseline.py', 'scripts/prepare_strategy_suite.py',
                                   'docs/phase-3-ten-strategy-spec.md']},
                'no_future_information': 'Historical handler calls strictly before start date; baskets frozen for run'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({k: v['basket'] for k, v in plans.items()}, indent=2))


if __name__ == '__main__':
    main()
