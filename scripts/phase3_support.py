"""Local loading/compatibility checks; never imported by submitted strategy."""
import ast
import importlib.util

from package_support import ROOT


def load_baseline():
    path = ROOT / 'strategy/DiversifiedBaseline.py'
    spec = importlib.util.spec_from_file_location('DiversifiedBaseline', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DiversifiedBaseline


def check_submission_shape():
    path = ROOT / 'strategy/DiversifiedBaseline.py'
    files = list(path.parent.glob('*.py'))
    if files != [path]:
        raise AssertionError('Expected exactly one team strategy Python file')
    tree = ast.parse(path.read_text())
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    if len(classes) != 1 or classes[0].name != path.stem:
        raise AssertionError('Filename/class mismatch or extra class')
    if len(classes[0].bases) != 1 or ast.unparse(classes[0].bases[0]) != 'Strategy_template':
        raise AssertionError('Strategy must directly inherit the official template')
    permitted = {'datetime', 'math', 'strategy.Strategies_template'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(n.name not in permitted for n in node.names):
            raise AssertionError('Unexpected strategy import')
        if isinstance(node, ast.ImportFrom) and node.module not in permitted:
            raise AssertionError('Unexpected strategy import')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {
                'open', 'eval', 'exec', 'compile', '__import__'}:
            raise AssertionError('Forbidden strategy operation')
    return {'local_structure_checks': 'pass', 'organizer_validation': 'unknown',
            'registered_owner_verified': False}
