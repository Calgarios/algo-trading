"""Provenance and local paths for the unmodified organizer distribution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / '.local' / 'tradesim-0.2.7'
PROVENANCE = ROOT / 'docs' / 'tradesim-0.2.7-provenance.json'


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha256(p)
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.name != '.DS_Store'}


def tree_hash(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def verify_package():
    expected = json.loads(PROVENANCE.read_text())
    actual = inventory(PACKAGE)
    if len(actual) != expected['file_count'] or tree_hash(actual) != expected['tree_sha256']:
        raise SystemExit('Official package missing or modified. Run scripts/install_tradesim.py with the original ZIP.')
    return expected
