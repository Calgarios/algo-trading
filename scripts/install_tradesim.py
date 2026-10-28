"""Install the checksum-pinned ZIP locally without overwriting project files."""
import argparse
from pathlib import PurePosixPath
import zipfile

from package_support import PACKAGE, PROVENANCE, sha256, verify_package
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive')
    args = parser.parse_args()
    expected = json.loads(PROVENANCE.read_text())
    if sha256(args.archive) != expected['archive_sha256']:
        parser.error('Archive checksum differs from the inspected TradeSim 0.2.7 upload.')
    if PACKAGE.exists():
        verify_package()
        print(f'Already installed and verified: {PACKAGE}')
        return
    with zipfile.ZipFile(args.archive) as archive:
        for entry in archive.infolist():
            path = PurePosixPath(entry.filename)
            if entry.is_dir() or path.parts[0] == '__MACOSX' or path.name == '.DS_Store':
                continue
            if path.is_absolute() or '..' in path.parts or path.parts[0] != 'tradeSim0.2.7':
                parser.error(f'Unexpected archive path: {entry.filename}')
            dest = PACKAGE.joinpath(*path.parts[1:])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.read(entry))
    verify_package()
    print(f'Installed and verified: {PACKAGE}')


if __name__ == '__main__':
    main()
