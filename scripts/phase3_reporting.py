"""Independent accounting and explicitly scoped working eligibility checks."""
from collections import defaultdict, deque
from math import isclose, isfinite


FEE_RATE = .00157 * 1.07


class FillLedger:
    def __init__(self, initial_cash=10000000.0):
        self.cash = initial_cash
        self.fees = 0.0
        self.realized = 0.0
        self.lots = defaultdict(deque)
        self.completed = []
        self.symbols = set()
        self.fill_count = 0

    def apply(self, fill):
        symbol, side = fill['Symbol'], fill['Side']
        quantity, price = int(fill['Volume']), float(fill['Price'])
        if side not in ('Buy', 'Sell') or quantity <= 0 or quantity % 100 or not isfinite(price) or price <= 0:
            raise AssertionError('Invalid fill')
        amount = quantity * price
        commission = amount * .00157
        fee = commission + commission * .07
        self.fees += fee
        self.symbols.add(symbol)
        self.fill_count += 1
        order = str(fill['Order Number'])
        if side == 'Buy':
            self.cash -= amount + fee
            unit_cost = (amount + fee) / quantity
            existing = next((lot for lot in self.lots[symbol] if lot['order'] == order), None)
            if existing:
                if existing['remaining'] != existing['volume']:
                    raise AssertionError('Buy fill added after that lot was already sold')
                existing['unit_cost'] = ((existing['unit_cost'] * existing['volume'] + amount + fee)
                                         / (existing['volume'] + quantity))
                existing['volume'] += quantity
                existing['remaining'] += quantity
            else:
                self.lots[symbol].append({'symbol': symbol, 'order': order, 'volume': quantity,
                                         'remaining': quantity, 'unit_cost': unit_cost, 'pnl': 0.0})
        else:
            if quantity > sum(lot['remaining'] for lot in self.lots[symbol]):
                raise AssertionError('Fill ledger would short a stock')
            self.cash += amount - fee
            unit_proceeds = (amount - fee) / quantity
            remaining = quantity
            while remaining:
                lot = self.lots[symbol][0]
                closed = min(remaining, lot['remaining'])
                pnl = unit_proceeds * closed - lot['unit_cost'] * closed
                lot['pnl'] += pnl
                self.realized += pnl
                lot['remaining'] -= closed
                remaining -= closed
                if not lot['remaining']:
                    self.completed.append(dict(self.lots[symbol].popleft()))
        if self.cash < -1e-6:
            raise AssertionError('Fill ledger would borrow cash')

    def quantities(self):
        return {s: sum(lot['remaining'] for lot in lots) for s, lots in self.lots.items() if lots}

    def expected_payoff(self):
        counted = [lot['pnl'] for lot in self.completed if lot['pnl'] != 0]
        return sum(counted) / len(counted) if counted else None

    def reconcile(self, cash, holdings, nav, prices, round_trips, realized, payoff, raw_open_costs):
        quantities = self.quantities()
        actual = {h['Symbol']: h['Actual Volume'] for h in holdings if h['Actual Volume']}
        marked = self.cash + sum(q * prices[s] for s, q in quantities.items())
        comparisons = {'cash': (self.cash, cash), 'nav': (marked, nav),
                       'realized_pnl': (self.realized, realized),
                       'expected_payoff': (self.expected_payoff() or 0.0, payoff)}
        if quantities != actual or len(self.completed) != round_trips:
            raise AssertionError('Holdings/FIFO completion does not reconcile')
        for name, (expected, observed) in comparisons.items():
            if not isclose(expected, observed, rel_tol=1e-11, abs_tol=1e-5):
                raise AssertionError(f'{name} does not reconcile: {expected} != {observed}')
        for holding in holdings:
            cost = sum(lot['remaining'] * lot['unit_cost'] for lot in self.lots[holding['Symbol']])
            if not isclose(cost, raw_open_costs[holding['Symbol']], rel_tol=1e-11, abs_tol=1e-5):
                raise AssertionError('Open lot cost does not reconcile')
        return {'cash_from_fills': self.cash, 'nav_from_fills_and_closes': marked,
                'fees_thb': self.fees, 'realized_pnl_thb': self.realized,
                'fill_rows': self.fill_count, 'distinct_stocks': len(self.symbols),
                'completed_fifo_round_trips': len(self.completed),
                'expected_payoff_thb': self.expected_payoff(), 'reconciled': True}


def drawdown_pct(values):
    if not values or any(not isfinite(v) or v <= 0 for v in values):
        return None
    peak, worst = values[0], 0.0
    for value in values:
        peak = max(peak, value)
        worst = max(worst, (peak - value) / peak * 100)
    return worst


def benchmark_metrics(rows, days):
    """Require every requested date; the engine can return zero for missing data."""
    closes = {}
    try:
        for row in rows:
            day = str(row['Date'])[:10]
            if day not in days:
                continue
            price = float(row['Close'])
            if day in closes or not isfinite(price) or price <= 0:
                raise ValueError('Duplicate or invalid benchmark close')
            closes[day] = price
        if set(closes) != set(days) or not days:
            raise ValueError('Incomplete benchmark dates')
    except (ValueError, TypeError, KeyError):
        return {'return_pct': None, 'max_drawdown_pct': None, 'complete': False}
    values = [closes[d] for d in days]
    return {'return_pct': (values[-1] / values[0] - 1) * 100,
            'max_drawdown_pct': drawdown_pct(values), 'complete': True}


def eligibility(metrics):
    """Working thresholds only; values must be unrounded and fractions explicit."""
    checks = {}

    def check(key, value, threshold, passed, reason=None):
        known = value is not None and isfinite(value) and reason is None
        checks[key] = {'value': value if value is not None and isfinite(value) else None,
                       'threshold': threshold, 'status': ('pass' if passed else 'fail') if known else 'unknown'}
        if reason:
            checks[key]['reason'] = reason

    rules = [('distinct_stocks', '>= 5', lambda x: x >= 5),
             ('completed_fifo_round_trips', '>= 5', lambda x: x >= 5),
             ('average_exposure', '>= 0.50', lambda x: x >= .50),
             ('expected_payoff_thb', '> 0', lambda x: x > 0),
             ('net_return_pct', '>= 0', lambda x: x >= 0),
             ('excess_return_pp', '>= 0', lambda x: x >= 0)]
    for key, threshold, predicate in rules:
        value = metrics.get(key)
        check(key, value, threshold, predicate(value) if value is not None else False)
    portfolio_dd, benchmark_dd = metrics.get('official_max_drawdown_pct'), metrics.get('benchmark_max_drawdown_pct')
    reason = None
    if benchmark_dd is None or not isfinite(benchmark_dd):
        reason = 'Benchmark drawdown unavailable'
    elif benchmark_dd <= 0:
        reason = 'Zero-benchmark-drawdown interpretation awaits organizer confirmation'
    check('relative_drawdown', portfolio_dd, '< 1.5 * benchmark_max_drawdown_pct',
          portfolio_dd is not None and benchmark_dd is not None and portfolio_dd < 1.5 * benchmark_dd, reason)
    checks['relative_drawdown']['benchmark_max_drawdown_pct'] = (
        benchmark_dd if benchmark_dd is not None and isfinite(benchmark_dd) else None)

    def combined(keys):
        states = [checks[k]['status'] for k in keys]
        return 'fail' if 'fail' in states else 'unknown' if 'unknown' in states else 'pass'

    common = ['distinct_stocks', 'completed_fifo_round_trips', 'average_exposure',
              'expected_payoff_thb', 'relative_drawdown']
    return {'basis': 'Working award rules; current organizer confirmation pending',
            'checks': checks, 'common_status': combined(common),
            'best_alpha_status': combined(list(checks)), 'competition_acceptance': 'unknown'}


def performance(daily, ledger, benchmark, initial_cash=10000000):
    navs = [d['raw']['nav'] for d in daily]
    exposures = [(d['raw']['nav'] - d['raw']['cash']) / d['raw']['nav'] for d in daily]
    net = (navs[-1] / initial_cash - 1) * 100
    bm = benchmark['return_pct']
    return {'net_return_pct': net, 'benchmark_return_pct': bm,
            'excess_return_pp': net - bm if bm is not None else None,
            'official_max_drawdown_pct': drawdown_pct(navs),
            'initial_capital_max_drawdown_pct': drawdown_pct([initial_cash] + navs),
            'benchmark_max_drawdown_pct': benchmark['max_drawdown_pct'],
            'aligned_first_close_return_pct': (navs[-1] / navs[0] - 1) * 100,
            'aligned_first_close_excess_pp': ((navs[-1] / navs[0] - 1) * 100 - bm) if bm is not None else None,
            'average_exposure': sum(exposures) / len(exposures),
            'distinct_stocks': len(ledger.symbols), 'completed_fifo_round_trips': len(ledger.completed),
            'expected_payoff_thb': ledger.expected_payoff(), 'fees_thb': ledger.fees,
            'final_nav_thb': navs[-1], 'final_cash_thb': ledger.cash}
