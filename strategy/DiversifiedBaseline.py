"""Deterministic monthly quantity targets; no research-harness dependencies."""
from datetime import date
from math import floor, isfinite

from strategy.Strategies_template import Strategy_template


class DiversifiedBaseline(Strategy_template):
    FEE_RATE = 0.00157 * 1.07

    def __init__(self, handler):
        super().__init__('baseline', 'DiversifiedBaseline', handler, '1min')
        self.config = handler.load_json('baseline.json')
        self._validate_config()
        self.history = {s: handler.get_historical_data(s, 60, '1D')
                        for s in self.config['universe']}
        self.opening_nav = handler.get_cash_balance() + sum(
            h['Market Value'] for h in handler.get_all_stocks_info())
        self.plan = None
        self.last_slot = None
        self.decision_sequence = 0
        self.last_decision = None

    def _validate_config(self):
        c = self.config
        if (c['version'] != 'baseline-v1' or not c['universe']
                or c['universe'] != sorted(set(c['universe']))
                or any(not isinstance(s, str) or not s or s == 'SET50' for s in c['universe'])):
            raise ValueError('Invalid baseline universe/version')
        if (type(c['positions']) is not int or not 5 <= c['positions'] <= 48
                or c['initial_capital_thb'] != 10000000
                or not 0 < c['target_exposure'] <= c['max_exposure'] < 1
                or not 0 < c['cash_reserve'] < 1
                or c['max_exposure'] + c['cash_reserve'] > 1
                or not c['target_exposure'] / c['positions'] <= c['max_position'] <= 1):
            raise ValueError('Invalid baseline sizing/risk configuration')

    @staticmethod
    def buy_price(last, day):
        # Verified 0.2.7 tick tables; sells are priced by the engine itself.
        bounds = (2, 5, 10, 25, 50, 100, 200, 400)
        ticks = ((.01, .02, .05, .10, .25, .25, .50, 1., 2.)
                 if day < '2026-11-16' else
                 (.01, .02, .02, .05, .10, .25, .50, 1., 2.))
        return round(last + ticks[sum(last >= b for b in bounds)], 2)

    def _build_plan(self, day):
        month = date.fromisoformat(day).replace(day=1)
        eligible, rejected = {}, {}
        for symbol, bars in self.history.items():
            try:
                parsed = [(date.fromisoformat(str(b['Date'])[:10]), float(b['Close']))
                          for b in bars]
                dates = [d for d, _ in parsed]
                if dates != sorted(set(dates)) or any(d >= date.fromisoformat(day) for d in dates):
                    raise ValueError('unordered, repeated or nonpast dates')
                prior = [(d, p) for d, p in parsed if d < month]
                if len(prior) < 20:
                    raise ValueError('fewer than 20 prior-month closes')
                prior = prior[-20:]
                if any(not isfinite(p) or p <= 0 for _, p in prior):
                    raise ValueError('invalid prior-month close')
                if (month - prior[-1][0]).days > 7:
                    raise ValueError('stale month anchor')
                eligible[symbol] = {'history': [{'date': str(d), 'close': p} for d, p in prior],
                                    'anchor_date': str(prior[-1][0]), 'anchor_close': prior[-1][1]}
            except (KeyError, TypeError, ValueError, OverflowError) as error:
                rejected[symbol] = str(error)
        selected = sorted(eligible)[:self.config['positions']]
        allocation = (self.config['initial_capital_thb'] * self.config['target_exposure']
                      / self.config['positions'])
        targets = {s: floor(allocation / eligible[s]['anchor_close'] / 100) * 100 for s in selected}
        self.plan = {'month': str(month), 'selected': selected, 'targets': targets,
                     'eligible': eligible, 'rejected': rejected, 'ready': len(selected) >= 5}

    def on_data(self, bar):
        timestamp = str(bar['Timestamp'])
        day = timestamp[:10]
        if self.plan is None:
            self._build_plan(day)
        hour, minute = map(int, timestamp[11:16].split(':'))
        clock = hour * 60 + minute
        start = next((a for a, b in ((605, 745), (875, 980)) if a <= clock < b), None)
        if start is None:
            return
        slot = (day, start, (clock - start) // 15)
        if slot == self.last_slot:
            return
        self.last_slot = slot  # Failed/zero-fill attempts also consume this slot.
        symbol = bar['ShareCode']
        self.decision_sequence += 1
        decision = {'timestamp': timestamp, 'symbol': symbol, 'month': self.plan['month'],
                    'reason': 'hold', 'requested_quantity': 0, 'filled_quantity': 0}
        self.last_decision = decision
        if symbol not in self.config['universe'] or not self.plan['ready']:
            decision['reason'] = 'unpermitted_symbol' if symbol not in self.config['universe'] else 'unavailable_plan'
            return
        try:
            last = float(bar['Close'])
        except (TypeError, ValueError):
            last = float('nan')
        if not isfinite(last) or last <= 0:
            decision['reason'] = 'invalid_price'
            return
        held = self.handler.get_total_stock_volume_by_symbol(symbol)
        cash = self.handler.get_cash_balance()
        holdings = self.handler.get_all_stocks_info()
        target = self.plan['targets'].get(symbol, 0)
        decision.update({'close': last, 'held_before': held, 'cash_before': cash, 'target': target})
        if held < 0 or held % 100 or not isfinite(cash) or cash < 0:
            raise ValueError('Invalid account state')
        if self.handler.get_open_orders():
            decision['reason'] = 'pending_order'
            return
        if held == target:
            decision['reason'] = 'at_target'
            return
        side = 'Sell' if held > target else 'Buy'
        quantity = abs(target - held)
        if side == 'Buy':
            if held == 0 and len(holdings) >= self.config['positions']:
                decision['reason'] = 'position_count_limit'
                return
            invested = sum(h['Actual Volume'] * (last if h['Symbol'] == symbol else h['Market Price'])
                           for h in holdings)
            nav = min(self.opening_nav, cash + invested)
            if not isfinite(nav) or nav <= 0 or not isfinite(invested):
                decision['reason'] = 'invalid_nav'
                return
            price = self.buy_price(last, day)
            cost = price * (1 + self.FEE_RATE)
            loss = cost - last
            position_limit = self.config['max_position']
            exposure_limit = self.config['max_exposure']
            reserve = self.config['cash_reserve']
            capacity = min(
                (cash - reserve * nav) / (cost - reserve * loss),
                (position_limit * nav - held * last) / (last + position_limit * loss),
                (exposure_limit * nav - invested) / (last + exposure_limit * loss),
            )
            quantity = min(quantity, max(0, floor(capacity / 100) * 100))
            decision.update({'nav_for_limits': nav, 'invested_before': invested,
                             'estimated_fill_price': price, 'unit_cost_including_fees': cost})
        quantity = int(quantity // 100 * 100)
        if quantity < 100:
            decision['reason'] = 'risk_or_lot_limit'
            return
        decision.update({'side': side, 'requested_quantity': quantity, 'reason': 'rebalance'})
        response = self.handler.create_order_at_market(quantity, side, symbol)
        after = self.handler.get_total_stock_volume_by_symbol(symbol)
        filled = after - held if side == 'Buy' else held - after
        decision.update({'response': str(response), 'response_type': type(response).__name__,
                         'accepted': isinstance(response, str) and 'successfully' in response.lower(),
                         'held_after': after, 'cash_after': self.handler.get_cash_balance(),
                         'filled_quantity': filled})
        if filled < 0 or filled > quantity or filled % 100:
            raise ValueError('Unexpected market IOC fill')
