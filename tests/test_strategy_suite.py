"""Indicator math, frozen baskets, allocation and guard behavior on official fills."""
import json
from math import isfinite
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_support import ROOT, PACKAGE, verify_package
from phase3_support import load_baseline
from prepare_strategy_suite import select_basket

verify_package()
sys.path.insert(0, str(PACKAGE))
os.chdir(PACKAGE)
os.environ['TZ'] = 'UTC'
time.tzset()
import pandas as pd
from tradeSim.TradeSim import tradeSim
from tradeSim.StrategyHandler import StrategyHandler

Baseline = load_baseline()


def history(multiplier=1):
    prices, rows = 100.0, []
    dates = pd.bdate_range(end='2026-09-08', periods=180)
    for i, day in enumerate(dates):
        opened = prices
        prices *= 1 + multiplier * ([.004, -.003, .001, -.001, .002][i % 5])
        rows.append({'Date': str(day.date()), 'Open': opened, 'High': max(opened, prices) * 1.001,
                     'Low': min(opened, prices) * .999, 'Close': prices, 'Volume': 1000000})
    return rows


class SuiteMath(unittest.TestCase):
    def test_ema_and_rsi_reference_values(self):
        self.assertEqual(Baseline._ema([1, 2, 3], 3), [1, 1.5, 2.25])
        self.assertEqual(Baseline._rsi([5] * 30), 50)
        self.assertEqual(Baseline._rsi(list(range(1, 31))), 100)
        self.assertEqual(Baseline._rsi(list(range(30, 0, -1))), 0)

    def test_features_match_independent_pandas_and_aligned_beta(self):
        stock, benchmark = history(2), history()
        f = Baseline.suite_features(stock, benchmark, '2026-09-09')
        close = pd.Series([b['Close'] for b in stock])
        self.assertAlmostEqual(f['beta60'], 2)
        self.assertAlmostEqual(f['sma20'], close.iloc[-20:].mean())
        self.assertAlmostEqual(f['vol20'], close.pct_change().iloc[-20:].std())
        macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        self.assertAlmostEqual(f['macd'], macd.iloc[-1])
        self.assertAlmostEqual(f['macd_histogram'], (macd - macd.ewm(span=9, adjust=False).mean()).iloc[-1])
        self.assertAlmostEqual(f['ret20'], close.iloc[-1] / close.iloc[-21] - 1)

    def test_feature_history_rejects_future_duplicates_staleness_and_missing_data(self):
        good = history()
        bads = [good[:79], good + [{**good[-1], 'Date': '2026-09-09'}], good + good[-1:],
                good[:-20], good[:-1] + [{**good[-1], 'Close': float('nan')}]]
        for bad in bads:
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                Baseline.suite_features(bad, good, '2026-09-09')

    def test_scores_are_finite_for_all_ten_and_ensemble_ties_are_equal(self):
        f = Baseline.suite_features(history(), history(), '2026-09-09')
        for key in Baseline.SUITE_IDS:
            scores = Baseline.suite_scores({'AAA': f, 'BBB': f}, key)
            self.assertTrue(all(isfinite(x) for x in scores.values()))
            self.assertEqual(scores['AAA'], scores['BBB'])

    def test_sector_limit_and_deterministic_ties(self):
        symbols = [f'S{i:02}' for i in range(20)]
        sectors = {s: f'G{i // 4}' for i, s in enumerate(symbols)}
        basket = select_basket({s: 1 for s in reversed(symbols)}, sectors)
        self.assertEqual(basket, ['S00', 'S01', 'S04', 'S05', 'S08', 'S09', 'S12', 'S13', 'S16', 'S17'])
        with self.assertRaises(ValueError):
            select_basket({'AAA': 1, 'BBB': 2}, {'AAA': 'ONE', 'BBB': 'ONE'})


class SuiteExecution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = json.loads((ROOT / 'strategy/baseline.json').read_text())
        self.config['target_exposure'] = .76
        self.config['suite'] = {'id': 'C2', 'start_date': '2026-09-09',
                                'basket': self.config['universe'][:10]}
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date='2026-09-09')
        self.bars = history()
        self.handler = self.make_handler()

    def make_handler(self):
        with patch.object(StrategyHandler, 'load_json', return_value=self.config), patch.object(
                StrategyHandler, 'get_historical_data', return_value=self.bars):
            return StrategyHandler(Baseline, self.sim.get_strategy_runner(), str(ROOT / 'strategy'))

    def tick(self, symbol='AOT', clock='10:05:01', volume=100000, handler=None):
        handler = handler or self.handler
        price = self.bars[-1]['Close']
        row = {'ShareCode': symbol, 'TradeDateTime': pd.Timestamp('2026-09-09 ' + clock),
               'LastPrice': round(price * 4) / 4, 'Volume': volume, 'Value': price * volume, 'Flag': 'Sell'}
        handler.process_row(row)
        self.sim.update_market_prices({symbol: row['LastPrice']})
        return handler.strategy.last_decision

    def test_weights_target_76_percent_and_ten_distinct_stock_limit(self):
        for symbol in self.config['suite']['basket']:
            self.tick(symbol=symbol, handler=self.make_handler())
        self.assertEqual(len(self.sim.portfolio.get_all_stocks_info()), 10)
        decision = self.tick(symbol='WHA')
        self.assertEqual(decision['reason'], 'outside_frozen_basket')
        plan = self.handler.strategy.plan
        self.assertAlmostEqual(sum(plan['weights'].values()), .76)
        self.assertLessEqual(max(plan['weights'].values()), .10)
        nav = self.sim.portfolio.get_nav()
        exposure = (nav - self.sim.portfolio.get_cash_balance()) / nav
        self.assertTrue(.70 <= exposure <= .80)

    def test_soft_and_hard_guard_override_exposure_preference(self):
        for dd, target, reason in [(0, .76, 'normal'), (2.01, .72, 'soft_drawdown'), (4.01, .55, 'hard_drawdown')]:
            handler = self.make_handler()
            handler.strategy.opening_drawdown = dd
            self.tick(handler=handler)
            self.assertEqual(handler.strategy.plan['target_exposure'], target)
            self.assertEqual(handler.strategy.plan['drawdown_guard'], reason)

    def test_relative_guard_uses_only_previously_available_benchmark(self):
        handler = self.make_handler()
        handler.strategy.config['suite']['start_date'] = '2026-08-01'
        # The two final observations represent known history, not future sample closes.
        handler.strategy.benchmark_history[-2] = {**self.bars[-2], 'Close': 100}
        handler.strategy.benchmark_history[-1] = {**self.bars[-1], 'Close': 98}
        bm = [float(b['Close']) for b in handler.strategy.benchmark_history if b['Date'] >= '2026-08-01']
        dd = Baseline._drawdown(bm)
        handler.strategy.opening_drawdown = 1.36 * dd
        self.tick(handler=handler)
        self.assertEqual(handler.strategy.plan['drawdown_guard'], 'hard_drawdown')

    def test_rebalance_band_and_partial_intent_retries(self):
        first = dict(self.tick(volume=100))
        self.assertEqual(first['filled_quantity'], 100)
        second = self.tick(clock='10:20:01', volume=100)
        self.assertEqual(second['requested_quantity'], first['requested_quantity'] - 100)
        # A reconstructed handler sees a near-target holding and suppresses tiny trades.
        self.tick(clock='10:35:01')
        handler = self.make_handler()
        decision = self.tick(handler=handler)
        self.assertIn(decision['reason'], ('rebalance_band', 'at_target'))

    def test_incomplete_history_does_not_trade(self):
        self.bars = self.bars[-30:]
        handler = self.make_handler()
        self.assertEqual(self.tick(handler=handler)['reason'], 'unavailable_plan')
        self.assertFalse(handler.strategy.plan['ready'])


if __name__ == '__main__':
    unittest.main()
