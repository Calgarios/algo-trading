"""Summarize supplied data coverage and ordering without changing any rows."""
import argparse
import json
from pathlib import Path

from package_support import PACKAGE, verify_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    provenance = verify_package()
    import pandas as pd
    market = PACKAGE / 'marketInfo'
    universe = pd.read_csv(market / 'symbolSET50/Symbol_SET50.csv')
    symbols = set(universe['Symbol'].str.strip())
    result = {'package_tree_sha256': provenance['tree_sha256'],
              'universe': sorted(symbols), 'ticks': [], 'history': {}}
    for path in sorted((market / 'ticks').glob('*.csv')):
        df = pd.read_csv(path)
        stamps = pd.to_datetime(df['TradeDateTime'])
        backwards = int((df.assign(_time=stamps).groupby('ShareCode')['_time'].diff() < pd.Timedelta(0)).sum())
        result['ticks'].append({
            'file': path.name, 'rows': len(df), 'columns': list(df.columns),
            'first': str(stamps.min()), 'last': str(stamps.max()),
            'symbols': sorted(df['ShareCode'].unique()),
            'outside_universe': sorted(set(df['ShareCode']) - symbols),
            'null_cells': int(df.isna().sum().sum()),
            'nonpositive_price': int((df['LastPrice'] <= 0).sum()),
            'negative_volume': int((df['Volume'] < 0).sum()),
            'duplicate_rows': int(df.duplicated().sum()),
            'backwards_timestamps_within_symbol': backwards,
            'globally_sorted': bool(stamps.is_monotonic_increasing),
            'flags': {str(k): int(v) for k, v in df['Flag'].value_counts().items()},
        })
    folders = [market / 'daily_history', *sorted((market / 'intraday_history').iterdir())]
    for folder in folders:
        if not folder.is_dir():
            continue
        files = []
        for path in sorted(folder.glob('*.csv')):
            df = pd.read_csv(path)
            key = 'Date' if 'Date' in df else 'Timestamp'
            dates = pd.to_datetime(df[key])
            files.append({'symbol': path.stem, 'rows': len(df), 'first': str(dates.min()), 'last': str(dates.max()),
                          'columns': list(df.columns)})
        result['history'][folder.relative_to(market).as_posix()] = files
    result['benchmark'] = pd.read_csv(market / 'benchmark/SET50.csv').to_dict('records')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(f'Audited {sum(d["rows"] for d in result["ticks"]):,} ticks in {len(result["ticks"])} days; {len(symbols)} universe entries')


if __name__ == '__main__':
    main()
