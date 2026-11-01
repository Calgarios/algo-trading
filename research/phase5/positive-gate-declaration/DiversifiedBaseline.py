"""Phase 5 full supplied-universe research strategy; official-template only."""
from datetime import date
from math import floor, isfinite, sqrt
from strategy.Strategies_template import Strategy_template


class DiversifiedBaseline(Strategy_template):
    FEE_RATE = .00157 * 1.07

    def __init__(self, handler):
        super().__init__('baseline', 'DiversifiedBaseline', handler, '1min')
        self.config = handler.load_json('baseline.json')
        self._validate_config()
        self.FEE_RATE *= self.config['phase5'].get('fee_multiplier', 1)
        self.history = {s: handler.get_historical_data(s, 180, '1D') for s in self.config['universe']}
        self.benchmark_history = handler.get_historical_data('SET50', 180, '1D')
        self.opening_holdings = handler.get_all_stocks_info()
        self.opening_nav = handler.get_cash_balance() + sum(h['Market Value'] for h in self.opening_holdings)
        self.peak = max(self.config['initial_capital_thb'], handler.get_portfolio_info().get('Max NAV') or 0,
                        self.opening_nav)
        self.opening_drawdown = (1 - self.opening_nav / self.peak) * 100
        self.plan = None
        self.last_slot = None
        self.decision_sequence = 0
        self.last_decision = None
        self.exit_reason = None
        self.sold_today = False
        self.rebalance_active = None
        self.bought_value = 0.0

    def _validate_config(self):
        c, p = self.config, self.config['phase5']
        if (c['universe'] != sorted(set(c['universe'])) or not 5 <= len(c['universe']) <= 50
                or c['positions'] != len(c['universe']) or c['initial_capital_thb'] != 10000000
                or p['id'] not in self.SUITE_IDS or p['weighting'] not in ('equal', 'quality')
                or not 0 < c['target_exposure'] <= c['max_exposure'] <= .8
                or c['cash_reserve'] < .2 or c['max_exposure'] + c['cash_reserve'] > 1
                or not 0 < c['max_position'] <= .08 or not 0 < p['sector_cap'] <= .25
                or p['fee_multiplier'] not in (1, 2) or not .002 <= p['rebalance_band'] <= .008
                or set(p['sectors']) != set(c['universe']) or set(p['quality']) != set(c['universe'])
                or not 0 < p['daily_buy_budget'] <= .2):
            raise ValueError('Invalid Phase 5 configuration')
        for q in p['quality'].values():
            if q.get('last_outcome_date') and q['last_outcome_date'] >= p['start_date']:
                raise ValueError('Quality calibration contains future outcomes')

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

    @staticmethod
    def entry_signal(f, model):
        signals = {
            'C1': f['ret20'] > 0 and f['ret60'] > 0,
            'C2': f['downside20'] < .35 and f['beta60'] < 1.2,
            'C3': f['close'] >= .96 * f['high55'] and f['ret20'] > 0 and f['efficiency20'] >= .15,
            'C4': f['ret60'] > 0 and -.04 <= f['ret5'] <= .015,
            'T1': f['sma20'] >= f['sma60'] and f['close'] >= f['sma20'],
            'T2': f['ema12'] >= f['ema26'] and f['close'] >= f['ema26'],
            'T3': f['macd'] > 0 and f['macd_histogram'] > 0,
            'T4': 35 <= f['rsi14'] <= 60 and f['ret5'] <= .01,
            'T5': -1.75 <= f['bollinger_z'] <= 0,
        }
        signals['C5'] = sum(signals[k] for k in ('C1', 'C2', 'C3', 'C4')) >= 2
        return signals[model]

    @classmethod
    def stock_checks(cls, f, q, model):
        return {
            'quality_sample': q['n'] >= 12,
            'positive_net_edge': q.get('shrunk_mean_net', 0) > 0,
            'historical_win_support': q.get('smoothed_win_rate', 0) >= .5,
            'liquidity': f['median_value20'] >= 20000000,
            'volatility': 0 < f['vol20'] <= .05,
            'long_trend': f['close'] >= f['sma60'],
            'avoid_deterioration': f['ret20'] > -.03,
            'model_signal': cls.entry_signal(f, model),
        }

    @staticmethod
    def allocate(raw, caps, sectors, sector_cap, target):
        """Proportional water fill with hard position/sector capacities; no forced cash use."""
        weights = {s: 0.0 for s in raw}
        active = set(raw)
        for _ in range(len(raw) + 2):
            room = target - sum(weights.values())
            if room <= 1e-12 or not active:
                break
            total = sum(raw[s] for s in sorted(active))
            proposal = {s: room * raw[s] / total for s in sorted(active)}
            sector_used = {g: sum(w for s, w in weights.items() if sectors[s] == g)
                           for g in set(sectors.values())}
            factors = [1.0]
            for s in sorted(active):
                factors.append(max(0, caps[s] - weights[s]) / proposal[s])
            for g in sorted(set(sectors[s] for s in active)):
                addition = sum(v for s, v in proposal.items() if sectors[s] == g)
                factors.append(max(0, sector_cap - sector_used[g]) / addition)
            scale = min(factors)
            for s, delta in proposal.items():
                weights[s] += scale * delta
            active = {s for s in active if caps[s] - weights[s] > 1e-12
                      and sector_cap - sum(w for t, w in weights.items() if sectors[t] == sectors[s]) > 1e-12}
        return weights

    def risk_target(self, dd, bm_dd):
        if dd >= 3 or (bm_dd is not None and bm_dd >= 1 and dd >= 1.3 * bm_dd):
            return .35, 'hard_drawdown'
        if dd >= 1.5 or (bm_dd is not None and bm_dd >= 1 and dd >= 1.15 * bm_dd):
            return .55, 'soft_drawdown'
        return self.config['target_exposure'], 'normal'

    def _build_plan(self, day):
        p = self.config['phase5']
        if day < p['start_date']:
            raise ValueError('Calibration unavailable at requested date')
        features, rejected, checks = {}, {}, {}
        for symbol, bars in self.history.items():
            try:
                f = self.suite_features(bars, self.benchmark_history, day)
                # Extra range-consistency check; malformed bars never imply safety.
                if any(float(b['Low']) > min(float(b['Open']), float(b['Close']))
                       or float(b['High']) < max(float(b['Open']), float(b['Close'])) for b in bars):
                    raise ValueError('Inconsistent OHLC range')
                tr = [max(float(b['High']) - float(b['Low']), abs(float(b['High']) - float(a['Close'])),
                          abs(float(b['Low']) - float(a['Close']))) for a, b in zip(bars[-15:-1], bars[-14:])]
                f['atr14_fraction'] = self._mean(tr) / f['close']
                checks[symbol] = self.stock_checks(f, p['quality'][symbol], p['id'])
                features[symbol] = f
                if not all(checks[symbol].values()):
                    rejected[symbol] = ','.join(k for k, passed in checks[symbol].items() if not passed)
            except (ValueError, KeyError, TypeError, OverflowError) as error:
                rejected[symbol] = str(error)
        eligible = {s: f for s, f in features.items() if s not in rejected}
        scores = self.suite_scores(eligible, p['id'])
        ordered = sorted(scores, key=lambda s: (-scores[s], s))
        bm = [float(b['Close']) for b in self.benchmark_history if p['start_date'] <= str(b['Date'])[:10] < day]
        bm_dd = self._drawdown(bm) if bm else None
        target, guard = self.risk_target(self.opening_drawdown, bm_dd)
        raw = {}
        for s in ordered:
            if p['weighting'] == 'equal':
                raw[s] = 1.0
            else:
                q, f = p['quality'][s], features[s]
                confidence = min(2, max(.25, q['shrunk_mean_net'] / max(q['se_net'], .002)))
                # Tied scores have equal rank weights.
                rank = sum(v < scores[s] for v in scores.values()) / max(len(scores) - 1, 1)
                raw[s] = (.75 + .5 * rank) * confidence / max(f['vol20'], .01)
        caps = {s: min(self.config['max_position'], .01 * features[s]['median_value20'] / self.opening_nav)
                for s in ordered}
        weights = self.allocate(raw, caps, p['sectors'], p['sector_cap'], target)
        targets = {s: floor(self.opening_nav * weights[s] / features[s]['close'] / 100) * 100 for s in ordered}
        self.plan = {'month': day[:7] + '-01', 'date': day, 'strategy_id': p['id'],
                     'weighting': p['weighting'], 'selected': ordered, 'targets': targets, 'weights': weights,
                     'eligible': eligible, 'features': features, 'checks': checks, 'rejected': rejected,
                     'scores': scores, 'ready': True, 'target_exposure': target,
                     'allocated_exposure': sum(weights.values()), 'drawdown_guard': guard,
                     'opening_portfolio_drawdown_pct': self.opening_drawdown,
                     'prior_benchmark_drawdown_pct': bm_dd}

    def _exit_signal(self, symbol, last, day, decision):
        lots = self.handler.get_stock_by_symbol(symbol)
        if not lots:
            return None
        quantity = sum(lot.get_actual_vol() for lot in lots)
        cost = sum(lot.get_buy_price() * lot.get_actual_vol() for lot in lots)
        net = quantity * self.sell_price(last, day) * (1 - self.FEE_RATE) / cost - 1
        opened = min(lot.get_buy_time_str()[:10] for lot in lots)
        age = sum(opened <= str(b['Date'])[:10] < day for b in self.history[symbol])
        f = self.plan['features'].get(symbol)
        decision.update({'estimated_net_liquidation_return': net, 'holding_sessions': age})
        if not f:
            return 'invalid_history_exit'
        if last < f['sma60'] * .985 or f['ret20'] < -.05:
            return 'trend_failure'
        if net <= -max(.02, 2.5 * f['atr14_fraction']):
            return 'volatility_stop'
        friction = 1 - self.sell_price(last, day) * (1 - self.FEE_RATE) / (self.buy_price(last, day) * (1 + self.FEE_RATE))
        if age >= 5 and net >= max(.01, 2 * friction):
            return 'mature_profit'
        return None

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
        self.last_slot = slot
        symbol = bar['ShareCode']
        self.decision_sequence += 1
        decision = {'timestamp': timestamp, 'symbol': symbol, 'month': self.plan['month'],
                    'reason': 'hold', 'requested_quantity': 0, 'filled_quantity': 0}
        self.last_decision = decision
        if symbol not in self.config['universe']:
            decision['reason'] = 'unpermitted_symbol'
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
        invested = sum(h['Actual Volume'] * last if h['Symbol'] == symbol else h['Market Value'] for h in holdings)
        marked_nav = cash + invested
        nav = min(self.opening_nav, marked_nav)
        if held < 0 or held % 100 or not isfinite(cash) or cash < 0 or not isfinite(nav) or nav <= 0:
            raise ValueError('Invalid account state')
        if self.handler.get_open_orders():
            decision['reason'] = 'pending_order'
            return
        p = self.config['phase5']
        live_dd = (1 - marked_nav / max(self.peak, marked_nav)) * 100
        live_target, guard = self.risk_target(live_dd, self.plan['prior_benchmark_drawdown_pct'])
        scale = min(1, live_target / self.plan['target_exposure'])
        target = floor(target * scale / 100) * 100
        self.exit_reason = self.exit_reason or self._exit_signal(symbol, last, day, decision)
        if self.exit_reason:
            target = 0
        decision.update({'close': last, 'held_before': held, 'cash_before': cash, 'target': target,
                         'target_weight': self.plan['weights'].get(symbol, 0), 'drawdown_guard': guard,
                         'estimated_current_drawdown_pct': live_dd, 'exit_reason': self.exit_reason})
        emergency = bool(self.exit_reason or target == 0 or scale < 1 or
                         held * last > self.config['max_position'] * nav)
        if self.rebalance_active is None:
            self.rebalance_active = held == 0 or abs(target - held) * last >= p['rebalance_band'] * self.opening_nav
        if not self.rebalance_active and not emergency:
            decision['reason'] = 'rebalance_band'
            return
        if held == target:
            decision['reason'] = 'at_target'
            return
        side = 'Sell' if held > target else 'Buy'
        quantity = abs(target - held)
        if side == 'Buy':
            if self.sold_today or self.exit_reason:
                decision['reason'] = 'same_day_reentry_blocked'
                return
            price = self.buy_price(last, day)
            cost = price * (1 + self.FEE_RATE)
            loss = cost - last
            sector = p['sectors'][symbol]
            sector_value = sum(h['Actual Volume'] * last if h['Symbol'] == symbol else h['Market Value']
                               for h in holdings if p['sectors'][h['Symbol']] == sector)
            position_limit = self.config['max_position']
            reserve = self.config['cash_reserve']
            exposure_limit = min(self.config['max_exposure'], live_target + .04)
            cap = min((cash - reserve * nav) / (cost - reserve * loss),
                      (position_limit * nav - held * last) / (last + position_limit * loss),
                      (exposure_limit * nav - invested) / (last + exposure_limit * loss),
                      (p['sector_cap'] * nav - sector_value) / (last + p['sector_cap'] * loss))
            initial = day == p['start_date']
            budget = (self.config['target_exposure'] if initial else p['daily_buy_budget']) * self.opening_nav
            symbol_budget = budget / max(len(self.plan['selected']), 1)
            cap = min(cap, (symbol_budget - self.bought_value) / cost)
            quantity = min(quantity, max(0, floor(cap / 100) * 100))
            decision.update({'nav_for_limits': nav, 'invested_before': invested,
                             'estimated_fill_price': price, 'unit_cost_including_fees': cost})
        quantity = int(quantity // 100 * 100)
        if quantity < 100:
            decision['reason'] = 'risk_budget_or_lot_limit'
            return
        decision.update({'side': side, 'requested_quantity': quantity,
                         'reason': self.exit_reason if side == 'Sell' and self.exit_reason else 'rebalance'})
        if side == 'Sell':
            self.sold_today = True
        response = self.handler.create_order_at_market(quantity, side, symbol)
        after = self.handler.get_total_stock_volume_by_symbol(symbol)
        filled = after - held if side == 'Buy' else held - after
        decision.update({'response': str(response), 'response_type': type(response).__name__,
                         'accepted': isinstance(response, str) and 'successfully' in response.lower(),
                         'held_after': after, 'cash_after': self.handler.get_cash_balance(), 'filled_quantity': filled})
        if side == 'Buy':
            self.bought_value += filled * cost
        if filled < 0 or filled > quantity or filled % 100:
            raise ValueError('Unexpected market IOC fill')
