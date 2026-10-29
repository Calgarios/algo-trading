"""Deterministic monthly quantity targets; no research-harness dependencies."""
from datetime import date
from math import floor, isfinite, sqrt

from strategy.Strategies_template import Strategy_template


class DiversifiedBaseline(Strategy_template):
    FEE_RATE = 0.00157 * 1.07

    def __init__(self, handler):
        super().__init__('baseline', 'DiversifiedBaseline', handler, '1min')
        self.config = handler.load_json('baseline.json')
        self._validate_config()
        suite = self.config.get('suite')
        symbols = suite['basket'] if suite else self.config['universe']
        self.history = {s: handler.get_historical_data(s, 180 if suite else 60, '1D') for s in symbols}
        self.benchmark_history = handler.get_historical_data('SET50', 180, '1D') if suite else []
        self.opening_nav = handler.get_cash_balance() + sum(
            h['Market Value'] for h in handler.get_all_stocks_info())
        self.plan = None
        self.last_slot = None
        self.decision_sequence = 0
        self.last_decision = None
        self.exit_reason = None
        self.sold_today = False
        self.rebalance_active = None
        if suite:
            info = handler.get_portfolio_info()
            peak = max(self.config['initial_capital_thb'], info.get('Max NAV') or 0, self.opening_nav)
            self.opening_drawdown = max(handler.get_max_draw_down() or 0,
                                        (peak - self.opening_nav) / peak * 100)

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
        exits = c.get('exit_policy')
        if exits is not None and (
                not 0 < exits['take_profit_net'] < 1 or not 0 < exits['stop_loss_net'] < 1
                or type(exits['max_holding_sessions']) is not int
                or not 1 <= exits['max_holding_sessions'] <= 40):
            raise ValueError('Invalid exit policy')
        if c.get('selection', 'alphabetical') not in ('alphabetical', 'momentum20'):
            raise ValueError('Unsupported selection rule')
        suite = c.get('suite')
        if suite and (suite['id'] not in self.SUITE_IDS or len(suite['basket']) != 10
                      or len(set(suite['basket'])) != 10 or not set(suite['basket']) <= set(c['universe'])
                      or c['positions'] != 10 or c['target_exposure'] != .76 or c.get('exit_policy') is not None):
            raise ValueError('Invalid ten-stock comparison configuration')

    SUITE_IDS = ('C1', 'C2', 'C3', 'C4', 'C5', 'T1', 'T2', 'T3', 'T4', 'T5')

    @staticmethod
    def _mean(values):
        return sum(values) / len(values)

    @staticmethod
    def _std(values):
        mean = sum(values) / len(values)
        return sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1))

    @staticmethod
    def _ema(values, period):
        result = [values[0]]
        alpha = 2 / (period + 1)
        for value in values[1:]:
            result.append(alpha * value + (1 - alpha) * result[-1])
        return result

    @staticmethod
    def _rsi(values, period=14):
        changes = [b - a for a, b in zip(values, values[1:])]
        gain = sum(max(x, 0) for x in changes[:period]) / period
        loss = sum(max(-x, 0) for x in changes[:period]) / period
        for change in changes[period:]:
            gain = ((period - 1) * gain + max(change, 0)) / period
            loss = ((period - 1) * loss + max(-change, 0)) / period
        return 50.0 if gain == loss == 0 else 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)

    @staticmethod
    def _drawdown(values):
        peak, worst = values[0], 0.0
        for value in values:
            peak = max(peak, value)
            worst = max(worst, (peak - value) / peak * 100)
        return worst

    @classmethod
    def suite_features(cls, bars, benchmark, day):
        """Pure, prior-data-only features shared by preparation and daily decisions."""
        def checked(records):
            if len(records) < 80:
                raise ValueError('Need at least 80 prior daily bars')
            dates = [str(b['Date'])[:10] for b in records]
            if dates != sorted(set(dates)) or any(d >= day for d in dates):
                raise ValueError('Nonpast, duplicated or unordered history')
            if (date.fromisoformat(day) - date.fromisoformat(dates[-1])).days > 7:
                raise ValueError('Stale history')
            for b in records:
                if any(not isfinite(float(b[k])) or float(b[k]) <= 0 for k in ('Open', 'High', 'Low', 'Close')):
                    raise ValueError('Invalid OHLC price')
                if not isfinite(float(b['Volume'])) or float(b['Volume']) < 0:
                    raise ValueError('Invalid history volume')
            return dates, [float(b['Close']) for b in records]
        dates, closes = checked(bars)
        bm_dates, bm_closes = checked(benchmark)
        returns = [b / a - 1 for a, b in zip(closes, closes[1:])]
        stock_returns = dict(zip(zip(dates, dates[1:]), returns))
        bm_returns = dict(zip(zip(bm_dates, bm_dates[1:]), [b / a - 1 for a, b in zip(bm_closes, bm_closes[1:])]))
        aligned = sorted(stock_returns.keys() & bm_returns.keys())[-60:]
        if len(aligned) < 40:
            raise ValueError('Need 40 aligned stock/SET50 returns')
        x, y = [bm_returns[d] for d in aligned], [stock_returns[d] for d in aligned]
        mx, my = cls._mean(x), cls._mean(y)
        variance = sum((v - mx) ** 2 for v in x)
        beta = sum((a - mx) * (b - my) for a, b in zip(x, y)) / variance if variance else 0.0
        vol = cls._std(returns[-20:])
        sma20, sma60 = cls._mean(closes[-20:]), cls._mean(closes[-60:])
        ema12, ema26 = cls._ema(closes, 12), cls._ema(closes, 26)
        macd = [a - b for a, b in zip(ema12, ema26)]
        path = sum(abs(b - a) for a, b in zip(closes[-21:-1], closes[-20:]))
        turnovers = sorted(float(b['Close']) * float(b['Volume']) for b in bars[-20:])
        return {'history_start': dates[0], 'history_end': dates[-1], 'bars': len(bars),
                'close': closes[-1], 'ret5': closes[-1] / closes[-6] - 1,
                'ret20': closes[-1] / closes[-21] - 1, 'ret60': closes[-1] / closes[-61] - 1,
                'vol20': vol, 'downside20': sqrt(cls._mean([min(r, 0) ** 2 for r in returns[-20:]])) * sqrt(252),
                'beta60': beta, 'aligned_returns': len(aligned),
                'high55': max(float(b['High']) for b in bars[-56:-1]),
                'efficiency20': abs(closes[-1] - closes[-21]) / path if path else 0.0,
                'sma20': sma20, 'sma60': sma60, 'ema12': ema12[-1], 'ema26': ema26[-1],
                'macd': macd[-1], 'macd_histogram': macd[-1] - cls._ema(macd, 9)[-1],
                'rsi14': cls._rsi(closes),
                'bollinger_z': (closes[-1] - sma20) / max(cls._std(closes[-20:]), 1e-8),
                'median_value20': (turnovers[9] + turnovers[10]) / 2}

    @classmethod
    def suite_scores(cls, features, strategy_id):
        if strategy_id == 'C5':
            totals = {s: 0.0 for s in features}
            for component in ('C1', 'C2', 'C3', 'C4'):
                scores = cls.suite_scores(features, component)
                ordered = sorted(scores, key=lambda s: (scores[s], s))
                for symbol in ordered:
                    # Average percentile for tied scores, independent of symbol.
                    rank = (sum(v < scores[symbol] for v in scores.values())
                            + (sum(v == scores[symbol] for v in scores.values()) - 1) / 2)
                    totals[symbol] += rank / max(len(scores) - 1, 1) / 4
            return totals
        scores = {}
        for symbol, f in features.items():
            vol, close = max(f['vol20'], 1e-8), f['close']
            scores[symbol] = {
                'C1': (.6 * f['ret20'] + .4 * f['ret60']) / (vol * sqrt(20)),
                'C2': -(f['downside20'] + .1 * max(f['beta60'], 0)),
                'C3': (close / f['high55'] - 1) / vol + .5 * f['efficiency20'],
                'C4': (f['ret60'] - 2 * f['ret5']) / (vol * sqrt(20)),
                'T1': (f['sma20'] / f['sma60'] - 1) / vol,
                'T2': (f['ema12'] - f['ema26']) / (close * vol),
                'T3': (f['macd_histogram'] + .25 * f['macd']) / (close * vol),
                'T4': -(f['rsi14'] - 35) ** 2 / 100 + (5 if close > f['sma60'] else 0),
                'T5': -abs(f['bollinger_z'] + 1) - 2 * max(-2 - f['bollinger_z'], 0)
                      + (1 if close > f['sma60'] else 0),
            }[strategy_id]
        return scores

    def _build_suite_plan(self, day):
        suite = self.config['suite']
        features, rejected = {}, {}
        for symbol, bars in self.history.items():
            try:
                features[symbol] = self.suite_features(bars, self.benchmark_history, day)
            except (KeyError, TypeError, ValueError, OverflowError) as error:
                rejected[symbol] = str(error)
        try:
            bm = [float(b['Close']) for b in self.benchmark_history
                  if suite['start_date'] <= str(b['Date'])[:10] < day]
            bm_dd = self._drawdown(bm) if bm and all(isfinite(x) and x > 0 for x in bm) else None
        except (KeyError, TypeError, ValueError):
            bm_dd = None
        pf_dd = self.opening_drawdown
        target, guard = .76, 'normal'
        if pf_dd >= 2 or (bm_dd is not None and bm_dd >= .5 and pf_dd >= 1.2 * bm_dd):
            target, guard = .72, 'soft_drawdown'
        if pf_dd >= 4 or (bm_dd is not None and bm_dd >= 1 and pf_dd >= 1.35 * bm_dd):
            target, guard = .55, 'hard_drawdown'
        scores = self.suite_scores(features, suite['id'])
        ordered = sorted(scores, key=lambda s: (-scores[s], s))
        weights = {s: target / 10 * (1.2 - .4 * rank / 9) for rank, s in enumerate(ordered)}
        targets = {s: floor(self.opening_nav * weights[s] / features[s]['close'] / 100) * 100 for s in ordered}
        self.plan = {'month': day[:7] + '-01', 'date': day, 'strategy_id': suite['id'],
                     'selected': ordered, 'targets': targets, 'weights': weights, 'eligible': features,
                     'scores': scores, 'rejected': rejected, 'ready': len(features) == 10,
                     'target_exposure': target, 'drawdown_guard': guard,
                     'opening_portfolio_drawdown_pct': pf_dd, 'prior_benchmark_drawdown_pct': bm_dd}

    @staticmethod
    def buy_price(last, day):
        # Verified 0.2.7 tick tables; sells are priced by the engine itself.
        bounds = (2, 5, 10, 25, 50, 100, 200, 400)
        ticks = ((.01, .02, .05, .10, .25, .25, .50, 1., 2.)
                 if day < '2026-11-16' else
                 (.01, .02, .02, .05, .10, .25, .50, 1., 2.))
        return round(last + ticks[sum(last >= b for b in bounds)], 2)

    @staticmethod
    def sell_price(last, day):
        bounds = (2, 5, 10, 25, 50, 100, 200, 400)
        ticks = ((.01, .02, .05, .10, .25, .25, .50, 1., 2.)
                 if day < '2026-11-16' else
                 (.01, .02, .02, .05, .10, .25, .50, 1., 2.))
        return round(last - ticks[sum(last > b for b in bounds)], 2)

    def _exit_signal(self, symbol, last, day, decision):
        policy = self.config.get('exit_policy')
        if policy is None:
            return None
        lots = self.handler.get_stock_by_symbol(symbol)
        if not lots:
            return None
        quantity = sum(lot.get_actual_vol() for lot in lots)
        cost = sum(lot.get_buy_price() * lot.get_actual_vol() for lot in lots)
        proceeds = quantity * self.sell_price(last, day) * (1 - self.FEE_RATE)
        net = proceeds / cost - 1
        # Official buy-time strings use host timezone; SET sessions stay on the
        # same calendar date in UTC and Bangkok. Runner fixes TZ=UTC.
        opened = min(lot.get_buy_time_str()[:10] for lot in lots)
        dates = [str(b['Date'])[:10] for b in self.history[symbol]]
        # Observed sessions are a lower bound when the entry is older than the
        # bounded history. Ten observed later sessions still prove expiry.
        age = (sum(opened <= d < day for d in dates)
               if dates and dates == sorted(set(dates)) and opened <= dates[-1]
               and all(d < day for d in dates) else None)
        decision.update({'estimated_net_liquidation_return': net, 'oldest_lot_date': opened,
                         'holding_sessions': age})
        if net <= -policy['stop_loss_net']:
            return 'stop_loss'
        if net >= policy['take_profit_net']:
            return 'take_profit'
        if age is not None and age >= policy['max_holding_sessions']:
            return 'holding_period'
        return None

    def _build_plan(self, day):
        if self.config.get('suite'):
            self._build_suite_plan(day)
            return
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
        if self.config.get('selection') == 'momentum20':
            for item in eligible.values():
                item['momentum20'] = item['history'][-1]['close'] / item['history'][0]['close'] - 1
            ranked = sorted(eligible, key=lambda s: (-eligible[s]['momentum20'], s))
        else:
            ranked = sorted(eligible)
        selected = ranked[:self.config['positions']]
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
        if symbol not in self.config['universe']:
            decision['reason'] = 'unpermitted_symbol'
            return
        if self.config.get('suite') and symbol not in self.config['suite']['basket']:
            decision['reason'] = 'outside_frozen_basket'
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
        self.exit_reason = self.exit_reason or self._exit_signal(symbol, last, day, decision)
        if self.exit_reason and held:
            target = 0
            decision['target'] = 0
            decision['exit_reason'] = self.exit_reason
        elif not self.plan['ready']:
            decision['reason'] = 'unavailable_plan'
            return
        if self.config.get('suite'):
            decision.update({'strategy_id': self.config['suite']['id'], 'target_weight': self.plan['weights'][symbol],
                             'drawdown_guard': self.plan['drawdown_guard']})
            if self.rebalance_active is None:
                self.rebalance_active = held == 0 or abs(target - held) * last >= .004 * self.opening_nav
            if not self.rebalance_active:
                decision['reason'] = 'rebalance_band'
                return
        if held == target:
            decision['reason'] = 'at_target'
            return
        side = 'Sell' if held > target else 'Buy'
        quantity = abs(target - held)
        if side == 'Buy':
            if self.config.get('exit_policy') and (self.sold_today or self.exit_reason):
                decision['reason'] = 'same_day_reentry_blocked'
                return
            if held == 0 and len(holdings) >= self.config['positions']:
                decision['reason'] = 'position_count_limit'
                return
            invested = sum(h['Actual Volume'] * last if h['Symbol'] == symbol else h['Market Value']
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
        decision.update({'side': side, 'requested_quantity': quantity,
                         'reason': self.exit_reason if side == 'Sell' and self.exit_reason else 'rebalance'})
        if side == 'Sell':
            self.sold_today = True  # Includes rejected/zero-fill sell attempts.
        response = self.handler.create_order_at_market(quantity, side, symbol)
        after = self.handler.get_total_stock_volume_by_symbol(symbol)
        filled = after - held if side == 'Buy' else held - after
        decision.update({'response': str(response), 'response_type': type(response).__name__,
                         'accepted': isinstance(response, str) and 'successfully' in response.lower(),
                         'held_after': after, 'cash_after': self.handler.get_cash_balance(),
                         'filled_quantity': filled})
        if filled < 0 or filled > quantity or filled % 100:
            raise ValueError('Unexpected market IOC fill')
