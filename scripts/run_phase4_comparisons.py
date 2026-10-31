"""Stage frozen replay sources and execute the declared Phase 4 controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import sys

from package_support import ROOT, PACKAGE, sha256, verify_package
from phase4_diagnostics import read_json, write_json
from prepare_phase4_controls import CONTROL_SOURCE, REPLAY_FILES


PARITY_FILES = ['decisions.jsonl', 'plans.json', 'fifo.json',
                'engine/baseline/baseline_portfolio.json', 'engine/baseline/baseline_transaction_log.csv']


def verify_declaration(configs):
    manifest = read_json(configs / 'manifest.json')
    for path, digest in manifest['source_sha256'].items():
        if sha256(ROOT / path) != digest:
            raise ValueError(f'Control source changed after declaration: {path}')
    for key, digest in manifest['config_sha256'].items():
        if sha256(configs / f'{key}.json') != digest:
            raise ValueError(f'Control configuration changed: {key}')
    return manifest


def stage_sources(stage):
    for path in REPLAY_FILES:
        destination = stage / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, destination)
    (stage / 'strategy').mkdir()
    shutil.copyfile(ROOT / CONTROL_SOURCE, stage / 'strategy/DiversifiedBaseline.py')
    (stage / '.local').mkdir()
    (stage / '.local/tradesim-0.2.7').symlink_to(PACKAGE, target_is_directory=True)


def replay(key, config, runner, output, days):
    with (output / f'{key}.log').open('w') as log:
        run = subprocess.run([sys.executable, str(runner), '--config', str(config),
                              '--output', str(output / key), '--days', *days],
                             cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    result = {'id': key, 'exit_code': run.returncode}
    if run.returncode == 0:
        report = read_json(output / key / 'report.json')
        result.update({'performance': report['performance'], 'eligibility': report['eligibility'],
                       'hashes': read_json(output / key / 'reproducible-hashes.json')})
    write_json(output / f'{key}-status.json', result)
    print(f'{key}: exit {run.returncode}', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--configs', type=Path, default=ROOT / 'research/phase4-controls/configs')
    args = parser.parse_args()
    verify_package()
    if sys.version_info[:2] != (3, 13):
        parser.error('Use Python 3.13')
    configs, output = args.configs.resolve(), args.output.resolve()
    manifest = verify_declaration(configs)
    output.mkdir(parents=True, exist_ok=False)
    stage = output / 'replay-source'
    stage_sources(stage)
    write_json(output / 'declaration.json', manifest)
    runner = stage / 'scripts/run_phase3.py'
    parity = output / 'parity'
    parity.mkdir()
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(replay, 'original-C3', ROOT / 'research/phase3-suite/C3.json',
                            ROOT / 'scripts/run_phase3.py', parity, manifest['days'][:2]),
                pool.submit(replay, 'R-C3', configs / 'R-C3.json', runner, parity, manifest['days'][:2])]
        results = [job.result() for job in jobs]
    if any(r['exit_code'] for r in results):
        raise SystemExit('Parity replay failed; retained all logs')
    for path in PARITY_FILES:
        if sha256(parity / 'original-C3' / path) != sha256(parity / 'R-C3' / path):
            raise SystemExit(f'Research copy changed reference behavior: {path}')
    if results[0]['performance'] != results[1]['performance']:
        raise SystemExit('Research copy changed reference performance')
    write_json(output / 'parity.json', {'status': 'pass', 'days': manifest['days'][:2],
                                      'identical_artifacts': PARITY_FILES,
                                      'identical_performance': True})
    print('Parity passed; starting paired controls', flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(replay, key, configs / f'{key}.json', runner, output, manifest['days'])
                for key in ('P-C2', 'P-C3', 'H-C3')]
        results = {result['id']: result for result in (job.result() for job in jobs)}
    write_json(output / 'status.json', results)
    if any(result['exit_code'] for result in results.values()):
        raise SystemExit('A paired control failed; band comparison not started')
    results['B-C3'] = replay('B-C3', configs / 'B-C3.json', runner, output, manifest['days'])
    write_json(output / 'status.json', results)
    if results['B-C3']['exit_code']:
        raise SystemExit('Band comparison failed; all evidence retained')


if __name__ == '__main__':
    main()
