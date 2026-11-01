"""Phase 5 loading, causal calibration and uncertainty diagnostics."""
import ast
import importlib.util
import json
from math import sqrt, isfinite
from pathlib import Path
from package_support import ROOT

SOURCE = ROOT / 'research/phase5/strategy/DiversifiedBaseline.py'


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def load_strategy():
    spec = importlib.util.spec_from_file_location('Phase5Baseline', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DiversifiedBaseline


def check_shape():
    tree = ast.parse(SOURCE.read_text())
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    if len(classes) != 1 or classes[0].name != SOURCE.stem or ast.unparse(classes[0].bases[0]) != 'Strategy_template':
        raise AssertionError('Not a single official-template strategy class')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom) and node.module not in {
                'datetime', 'math', 'strategy.Strategies_template'}:
            raise AssertionError('Unexpected strategy import')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {
                'open', 'eval', 'exec', 'compile', '__import__'}:
            raise AssertionError('Forbidden strategy call')
    return {'local_structure_checks': 'pass', 'organizer_validation': 'unknown', 'registered_owner_verified': False}


def wilson(wins, n):
    if not n:
        return [None, None]
    z, p = 1.959963984540054, wins / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1+z*z/n)
    return [max(0, center-half), min(1, center+half)]


def distribution(values):
    n = len(values)
    if not n:
        return {'n': 0, 'mean_net': None, 'shrunk_mean_net': 0.0, 'se_net': None,
                'mean_95_interval': [None, None], 'win_rate': None, 'smoothed_win_rate': 0.5,
                'win_rate_wilson95': [None, None], 'profit_factor': None, 'mean_win': None,
                'mean_loss': None, 'worst_net': None}
    mean = sum(values)/n
    se = sqrt(sum((x-mean)**2 for x in values)/(n-1)/n) if n > 1 else None
    wins, losses = [x for x in values if x > 0], [x for x in values if x < 0]
    return {'n': n, 'mean_net': mean, 'shrunk_mean_net': n/(n+20)*mean, 'se_net': se,
            'mean_95_interval': [mean - 1.96*se, mean + 1.96*se] if se is not None else [None, None],
            'win_rate': len(wins)/n, 'smoothed_win_rate': (len(wins)+2)/(n+4),
            'win_rate_wilson95': wilson(len(wins), n),
            'profit_factor': sum(wins)/abs(sum(losses)) if losses else None,
            'mean_win': sum(wins)/len(wins) if wins else None,
            'mean_loss': sum(losses)/len(losses) if losses else None, 'worst_net': min(values)}


def calibrate(bars, start, strategy):
    """Five-session, non-overlapping next-open outcomes; rejects rather than filters future bars."""
    dates = [str(b['Date'])[:10] for b in bars]
    if dates != sorted(set(dates)) or any(d >= start for d in dates):
        raise ValueError('Calibration requires ordered, unique, strictly pre-start bars')
    for b in bars:
        if any(not isfinite(float(b[k])) or float(b[k]) <= 0 for k in ('Open','High','Low','Close')):
            raise ValueError('Invalid calibration OHLC')
    outcomes = []
    for origin in range(59, len(bars)-5, 5):
        prior = bars[origin-59:origin+1]
        close = float(prior[-1]['Close'])
        if close < sum(float(b['Close']) for b in prior)/60:
            continue
        entry, finish = bars[origin+1], bars[origin+5]
        buy = strategy.buy_price(float(entry['Open']), str(entry['Date'])[:10]) * (1 + strategy.FEE_RATE)
        sell = strategy.sell_price(float(finish['Close']), str(finish['Date'])[:10]) * (1 - strategy.FEE_RATE)
        outcomes.append({'signal_date': dates[origin], 'entry_date': dates[origin+1],
                         'exit_date': dates[origin+5], 'net_return': sell/buy-1})
    result = distribution([o['net_return'] for o in outcomes])
    result.update({'last_outcome_date': outcomes[-1]['exit_date'] if outcomes else None,
                   'history_start': dates[0] if dates else None, 'history_end': dates[-1] if dates else None})
    return result, outcomes
