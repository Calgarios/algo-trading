"""Replay the declared cost-aware alpha research copy against official TradeSim."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import shutil
import subprocess
import sys
from package_support import ROOT, PACKAGE, sha256, verify_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    verify_package()
    output = args.output.resolve()
    if output == PACKAGE or PACKAGE in output.parents:
        parser.error('Output cannot be inside the official package')
    source = ROOT / 'research/phase5-alpha/DiversifiedBaseline.py'
    declaration = (ROOT / 'research/phase5-alpha/experiment.md').read_text()
    expected = re.search(r'Staged strategy SHA-256: ([0-9a-f]{64})', declaration)
    if not expected or sha256(source) != expected.group(1):
        raise SystemExit('Research source does not match the experiment declaration')
    output.mkdir(parents=True, exist_ok=False)
    stage = output / 'stage'
    stage.mkdir()
    for name in ('scripts', 'docs', 'strategy', 'research'):
        shutil.copytree(ROOT / name, stage / name)
    shutil.copyfile(ROOT / 'requirements-phase2.txt', stage / 'requirements-phase2.txt')
    (stage / '.local').mkdir()
    (stage / '.local/tradesim-0.2.7').symlink_to(PACKAGE, target_is_directory=True)
    shutil.copyfile(source, stage / 'research/phase5/strategy/DiversifiedBaseline.py')
    print('Research source SHA-256:', sha256(source), flush=True)
    def run(model):
        with (output / f'{model}.log').open('w') as log:
            result = subprocess.run([sys.executable, str(stage / 'scripts/run_phase5.py'),
                                     '--config', str(ROOT / f'research/phase5-alpha/configs/{model}.json'),
                                     '--output', str(output / model)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        print(f'{model}: exit {result.returncode}', flush=True)
        return result.returncode
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(run, tuple(f'{p}-{w}' for p in ('breakout', 'relative', 'defensive') for w in ('equal', 'quality'))))
    if any(statuses):
        raise SystemExit('At least one replay failed; inspect retained logs.')


if __name__ == '__main__':
    main()
