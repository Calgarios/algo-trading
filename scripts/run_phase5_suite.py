"""Run frozen Phase 5 comparisons without overwriting or dropping failed outcomes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
from package_support import ROOT, sha256, verify_package
from phase5_support import write_json


def verify(configs):
    m=json.loads((configs/'manifest.json').read_text())
    for p,h in m['source_sha256'].items():
        if sha256(ROOT/p)!=h:
            raise ValueError(f'Source changed after declaration: {p}')
    for name,h in m['config_sha256'].items():
        if sha256(configs/f'{name}.json')!=h:
            raise ValueError(f'Config changed: {name}')
    if sha256(configs/'calibration.json')!=m['calibration_sha256']:
        raise ValueError('Calibration changed')
    return m


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--configs',type=Path,default=ROOT/'research/phase5/configs')
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--only',nargs='+')
    parser.add_argument('--days',nargs='+')
    args=parser.parse_args()
    verify_package()
    m=verify(args.configs.resolve())
    keys=args.only or m['experiments']
    if not set(keys)<=set(m['experiments']) or not 1<=args.workers<=6:
        parser.error('Invalid experiments/workers')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    write_json(output/'declaration.json',m)
    def run(key):
        with (output/f'{key}.log').open('w') as f:
            r=subprocess.run([sys.executable,str(ROOT/'scripts/run_phase5.py'),'--output',str(output/key),
                              '--config',str(args.configs.resolve()/f'{key}.json'),'--days',*(args.days or m['days'])],
                             cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        result={'id':key,'exit_code':r.returncode}
        if r.returncode==0:
            report=json.loads((output/key/'report.json').read_text())
            result.update({'performance':report['performance'],'eligibility':report['eligibility']})
        return result
    status={}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(run,key):key for key in keys}
        for job in as_completed(jobs):
            result=job.result();status[result['id']]=result
            write_json(output/'status.json',status)
            print(f"{result['id']}: exit {result['exit_code']}",flush=True)
    if any(r['exit_code'] for r in status.values()):
        raise SystemExit('Failed runs retained; inspect logs')

if __name__=='__main__':
    main()
