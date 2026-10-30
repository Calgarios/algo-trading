"""Run independently isolated official-engine experiments with bounded concurrency."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

from package_support import ROOT, sha256
from prepare_strategy_suite import STRATEGIES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--configs', type=Path, default=ROOT / 'research/phase3-suite')
    parser.add_argument('--workers', type=int, default=3, choices=(1, 2, 3))
    args = parser.parse_args()
    output, configs = args.output.resolve(), args.configs.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((configs / 'manifest.json').read_text())
    for path, digest in manifest['source_sha256'].items():
        if sha256(ROOT / path) != digest:
            raise SystemExit(f'Suite source changed after declaration/preparation: {path}')
    for key in STRATEGIES:
        if sha256(configs / f'{key}.json') != manifest['strategies'][key]['config_sha256']:
            raise SystemExit(f'Configuration changed: {key}')

    def execute(key):
        started = time.perf_counter()
        with (output / f'{key}.log').open('w') as log:
            run = subprocess.run([sys.executable, str(ROOT / 'scripts/run_phase3.py'),
                                  '--config', str(configs / f'{key}.json'), '--output', str(output / key)],
                                 cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        result = {'id': key, 'exit_code': run.returncode, 'seconds': round(time.perf_counter() - started, 3)}
        if run.returncode == 0:
            report = json.loads((output / key / 'report.json').read_text())
            result['performance'] = report['performance']
            result['common_status'] = report['eligibility']['common_status']
            result['best_alpha_status'] = report['eligibility']['best_alpha_status']
            result['user_targets'] = report['user_targets']
        return result

    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(execute, key) for key in STRATEGIES]
        for future in as_completed(futures):
            result = future.result()
            results[result['id']] = result
            (output / 'suite-status.json').write_text(json.dumps(results, indent=2, sort_keys=True, allow_nan=False) + '\n')
            print(json.dumps(result, allow_nan=False), flush=True)
    if any(r['exit_code'] for r in results.values()):
        raise SystemExit('One or more experiments failed; inspect their logs.')


if __name__ == '__main__':
    main()
