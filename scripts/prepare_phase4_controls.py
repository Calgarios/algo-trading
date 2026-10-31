"""Prepare the four declared controls from frozen pre-start Phase 3 features."""
import argparse
import copy
from math import floor
from pathlib import Path
import sys

from package_support import ROOT, PACKAGE, sha256, verify_package
from phase3_support import load_baseline
from phase4_diagnostics import read_json, write_json


REPLAY_FILES = ['scripts/run_phase3.py', 'scripts/phase3_reporting.py', 'scripts/phase3_support.py',
                'scripts/package_support.py', 'scripts/prepare_strategy_suite.py', 'requirements-phase2.txt',
                'docs/phase-3-baseline-spec.md', 'docs/phase-3-exit-experiment.md', 'docs/award-criteria.md',
                'docs/phase-3-ten-strategy-spec.md', 'docs/tradesim-0.2.7-provenance.json']
CONTROL_SOURCE = 'research/phase4-controls/strategy/DiversifiedBaseline.py'


def make_configs(strategy):
    prepared = read_json(ROOT / 'research/phase3-suite/manifest.json')
    for path, digest in prepared['source_sha256'].items():
        if sha256(ROOT / path) != digest:
            raise ValueError(f'Frozen Phase 3 preparation source changed: {path}')
    configs = {}
    for key, reference, mode in [('P-C2', 'C2', 'equal_weight'), ('P-C3', 'C3', 'equal_weight'),
                                 ('H-C3', 'C3', 'hold_initial'), ('B-C3', 'C3', 'wide_band'),
                                 ('R-C3', 'C3', 'ranked')]:
        config = read_json(ROOT / f'research/phase3-suite/{reference}.json')
        config['research_control'] = {'id': key, 'mode': mode}
        if mode == 'hold_initial':
            features = {s: copy.deepcopy(prepared['eligible_features'][s]) for s in config['suite']['basket']}
            if any(f['history_end'] >= config['suite']['start_date'] for f in features.values()):
                raise ValueError('Passive preparation contains nonpast features')
            scores = strategy.suite_scores(features, 'C3')
            ordered = sorted(scores, key=lambda s: (-scores[s], s))
            weights = {s: .76 / 10 * (1.2 - .4 * rank / 9) for rank, s in enumerate(ordered)}
            targets = {s: floor(10000000 * weights[s] / features[s]['close'] / 100) * 100 for s in ordered}
            config['research_control']['initial_allocation'] = {
                'date': config['suite']['start_date'], 'selected': ordered, 'eligible': features,
                'weights': weights, 'targets': targets, 'scores': scores}
        configs[key] = config
    return configs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'research/phase4-controls/configs')
    args = parser.parse_args()
    verify_package()
    sys.path.insert(0, str(PACKAGE))
    configs = make_configs(load_baseline())
    args.output.mkdir(parents=True, exist_ok=False)
    for key, config in configs.items():
        write_json(args.output / f'{key}.json', config)
    paths = [*REPLAY_FILES, CONTROL_SOURCE, 'scripts/run_phase4_comparisons.py',
             'scripts/prepare_phase4_controls.py', 'scripts/phase4_diagnostics.py',
             'docs/phase-4-control-implementation.md', 'docs/phase-4-research-spec.md',
             'research/phase3-suite/manifest.json', 'research/phase3-suite/C2.json', 'research/phase3-suite/C3.json']
    write_json(args.output / 'manifest.json', {
        'declared_date_bangkok': '2026-10-30', 'sample_role': 'reused_development',
        'experiments': ['P-C2', 'P-C3', 'H-C3', 'B-C3'], 'parity_control': 'R-C3',
        'source_sha256': {p: sha256(ROOT / p) for p in paths},
        'config_sha256': {key: sha256(args.output / f'{key}.json') for key in configs},
        'days': read_json(ROOT / 'research/phase4/manifest.json')['days'],
        'validation_period': None, 'final_evaluation_period': None})
    print(f'Prepared {len(configs)} frozen control configurations at {args.output}')


if __name__ == '__main__':
    main()
