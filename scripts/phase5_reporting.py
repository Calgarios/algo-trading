"""Independent Phase 5 accounting, including actual fee replay stresses."""
from collections import defaultdict, deque
from math import isclose, isfinite

class CostLedger:
    def __init__(self, initial_cash=10000000.0, fee_multiplier=1):
        self.fee_multiplier = fee_multiplier
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
        commission = amount * .00157 * self.fee_multiplier
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

