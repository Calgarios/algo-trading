"""Check or replay the predeclared R76 development control with frozen inputs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from package_support import ROOT, sha256, verify_package
from phase4_diagnostics import read_json, write_json


def declaration(root=ROOT):
    manifest = read_json(root / 'research/phase4/manifest.json')
    if manifest['id'] != 'R76' or manifest['sample_role'] != 'reused_development':
        raise ValueError('Only the declared R76 development experiment is supported')
    for path, digest in manifest['source_sha256'].items():
        if sha256(root / path) != digest:
            raise ValueError(f'Source changed after declaration: {path}')
    config = read_json(root / manifest['config'])
    reference = read_json(root / 'strategy/baseline.json')
    if config != {**reference, 'target_exposure': .76}:
        raise ValueError('R76 must change only target_exposure to 0.76')
    evidence = read_json(root / 'docs/result-data-visualisation/phase-3-results.json')
    if manifest['days'] != evidence['runs']['C1']['configuration']['days']:
        raise ValueError('R76 must use the same declared September development sessions')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Report prerequisites without creating a run')
    parser.add_argument('--output', type=Path, help='New experiment directory')
    args = parser.parse_args()
    if not args.check and args.output is None:
        parser.error('--output is required for a replay')
    manifest = declaration()
    try:
        package = verify_package()
        package_error = None
    except SystemExit as error:
        package, package_error = None, str(error)
    ready = package is not None and sys.version_info[:2] == (3, 13)
    if args.check:
        print(json.dumps({'id': 'R76', 'declaration_integrity': 'pass', 'ready_for_replay': ready,
                          'python_3_13': sys.version_info[:2] == (3, 13),
                          'package_error': package_error, 'sample_role': manifest['sample_role'],
                          'validation_period': None, 'final_evaluation_period': None}, indent=2))
        return
    if not ready:
        parser.error(package_error or 'Use Python 3.13 (validated with 3.13.5)')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    metadata = {'id': 'R76', 'sample_role': manifest['sample_role'], 'declaration': manifest,
                'manifest_sha256': sha256(ROOT / 'research/phase4/manifest.json'),
                'package': package, 'state': 'started'}
    write_json(output / 'experiment.json', metadata)
    with (output / 'replay.log').open('w') as log:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_phase3.py'),
                                 '--config', str(ROOT / manifest['config']),
                                 '--days', *manifest['days'], '--output', str(output / 'run')],
                                cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    metadata.update({'state': 'completed' if result.returncode == 0 else 'failed',
                     'exit_code': result.returncode})
    write_json(output / 'experiment.json', metadata)
    if result.returncode:
        raise SystemExit(f'R76 failed; retained evidence in {output}')
    print(f'R76 development run completed: {output / "run/report.json"}')


if __name__ == '__main__':
    main()
