"""Freeze all-universe Phase 5 calibration and twenty paired configurations."""
import argparse
import csv
import json
import os
from pathlib import Path
import sys
from package_support import ROOT, PACKAGE, sha256, verify_package
from phase5_support import load_strategy, check_shape, calibrate, write_json
from prepare_strategy_suite import STRATEGIES

SOURCES = ['research/phase5/strategy/DiversifiedBaseline.py','scripts/phase5_support.py',
           'scripts/prepare_phase5.py','scripts/run_phase5.py','scripts/run_phase5_suite.py',
           'scripts/phase5_reporting.py','scripts/phase3_reporting.py','scripts/package_support.py',
           'docs/phase-5-research-spec.md','requirements-phase2.txt']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'research/phase5/configs')
    args=parser.parse_args()
    package=verify_package()
    sys.path.insert(0,str(PACKAGE))
    cls=load_strategy()
    check_shape()
    base=json.loads((ROOT/'strategy/baseline.json').read_text())
    with (PACKAGE/'marketInfo/symbolSET50/Symbol_SET50.csv').open(encoding='utf-8-sig') as f:
        sectors={r['Symbol']:r['Sector'] for r in csv.DictReader(f)}
    if sorted(sectors)!=base['universe']:
        raise ValueError('Universe differs from verified sample')
    days=sorted(p.stem for p in (PACKAGE/'marketInfo/ticks').glob('*.csv'))
    from tradeSim.TradeSim import tradeSim
    os.chdir(PACKAGE)
    sim=tradeSim('phase5-calibration',folder=str(ROOT/'artifacts/phase5-calibration'),current_date=days[0])
    quality, outcomes={},{}
    for s in base['universe']:
        quality[s],outcomes[s]=calibrate(sim.get_historical_data(s,500,'1D'),days[0],cls)
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Refusing to overwrite a declaration')
    base.update({'positions':len(sectors),'target_exposure':.76,'max_position':.08})
    hashes, experiments={},[]
    for key in STRATEGIES:
        for weighting in ('equal','quality'):
            variants=[('base',1,.004)]
            if key in ('C1','C3'):
                variants += [('fees2',2,.004),('band6',1,.006)]
            for variant,fees,band in variants:
                name=f'{key}-{weighting}' + (f'-{variant}' if variant!='base' else '')
                config={**base,'phase5':{'id':key,'name':STRATEGIES[key][1],'weighting':weighting,
                        'start_date':days[0],'sectors':sectors,'quality':quality,'sector_cap':.2,
                        'fee_multiplier':fees,'rebalance_band':band,'daily_buy_budget':.15,
                        'variant':variant}}
                write_json(output/f'{name}.json',config)
                hashes[name]=sha256(output/f'{name}.json')
                experiments.append(name)
    write_json(output/'calibration.json',{'start_date':days[0],'quality':quality,'outcomes':outcomes,
               'basis':'Pre-start daily-bar proxy, not executable validation or probability calibration'})
    write_json(output/'manifest.json',{'declared_date_bangkok':'2026-11-01','sample_role':'reused_development',
               'days':days,'experiments':experiments,'source_sha256':{p:sha256(ROOT/p) for p in SOURCES},
               'config_sha256':hashes,'calibration_sha256':sha256(output/'calibration.json'),'package':package,
               'universe_count':len(sectors),'validation_period':None,'final_evaluation_period':None})
    print(f'Declared {len(experiments)} runs; calibrated {len(quality)} names')

if __name__=='__main__':
    main()
