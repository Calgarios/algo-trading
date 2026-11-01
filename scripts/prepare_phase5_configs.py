"""Safe user entrypoint for the frozen Phase 5 configuration preparer.

Resolve output paths before the legacy preparer enters the official package;
never allow generated output inside the checksum-pinned distribution.
"""
import argparse
from pathlib import Path
import subprocess
import sys
from package_support import ROOT, PACKAGE


def safe_output(path):
    output=Path(path).resolve()
    if output==PACKAGE or PACKAGE in output.parents:
        raise ValueError('Generated configuration output cannot be inside the official package')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'research/phase5/configs')
    args=parser.parse_args()
    output=safe_output(args.output)
    subprocess.run([sys.executable,str(ROOT/'scripts/prepare_phase5.py'),'--output',str(output)],check=True,cwd=ROOT)

if __name__=='__main__':
    main()
