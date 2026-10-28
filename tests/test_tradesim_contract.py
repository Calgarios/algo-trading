"""Black-box checks against the checksum-verified, unmodified organizer engine."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_support import PACKAGE, verify_package

verify_package()
os.chdir(PACKAGE)
os.environ['TZ'] = 'UTC'
time.tzset()
sys.path.insert(0, str(PACKAGE))
import pandas as pd
from tradeSim.TradeSim import tradeSim
from tradeSim.StrategyHandler import StrategyHandler
from tradeSim.CommissionService import commissionService as Costs
from strategy.Strategies_template import Strategy_template


class Probe(Strategy_template):
    def __init__(self, handler):
        super().__init__('probe', 'Probe', handler, '1min')
        self.action = lambda bar: None
        self.bars = []

    def on_data(self, bar):
        self.bars.append(dict(bar))
        self.action(bar)


class Contract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sim = tradeSim('probe', folder=self.tmp.name, current_date='2026-09-09')
        self.runner = self.sim.get_strategy_runner()
        self.handlers = {s: StrategyHandler(Probe, self.runner) for s in ['AOT', 'PTT']}
        self.counter = 0

    def tick(self, action=None, symbol='AOT', price=42, volume=1000, flag='Sell', timestamp=None):
        self.counter += 1
        h = self.handlers[symbol]
        h.strategy.action = (lambda bar: action(h, bar)) if action else lambda bar: None
        h.process_row({'ShareCode': symbol, 'TradeDateTime': pd.Timestamp(timestamp or '2026-09-09 10:00:00') + pd.Timedelta(seconds=self.counter),
                       'LastPrice': price, 'Volume': volume, 'Value': price * volume, 'Flag': flag})
        self.sim.isMatch(h._current_row)
        self.sim.update_market_prices({symbol: price})

    def quantity(self, symbol='AOT'):
        return self.runner.get_total_stock_volume_by_symbol(symbol)

    def test_market_partial_fill_and_ioc(self):
        self.tick(lambda h, b: h.create_order_at_market(1000, 'Buy', 'AOT'), volume=350)
        self.assertEqual(self.quantity(), 300)
        self.assertEqual(self.sim.get_open_orders(), [])
        self.tick()
        self.assertEqual(self.quantity(), 300)

    def test_tick_volume_shared_by_market_orders(self):
        self.tick(lambda h, b: [h.create_order_at_market(200, 'Buy', 'AOT') for _ in range(2)], volume=350)
        self.assertEqual(self.quantity(), 300)

    def test_limit_at_close_never_waits_for_later_tick(self):
        self.tick(lambda h, b: h.create_order_to_limit(100, b['Close'], 'Buy', 'AOT'))
        self.assertEqual(self.quantity(), 0)
        self.assertEqual(self.sim.get_open_orders(), [])
        self.tick(price=41)
        self.assertEqual(self.quantity(), 0)

    def test_limit_price_improvement_and_partial_fill(self):
        self.tick(lambda h, b: h.create_order_to_limit(1000, 43, 'Buy', 'AOT'), volume=350)
        fill = self.sim.execution.tranLog.transaction_log[0]
        self.assertEqual((fill['Price'], fill['Volume']), (42.25, 300))
        self.assertEqual(fill['Placed'], fill['Timestamp'])
        self.tick()
        self.assertEqual(self.quantity(), 300)

    def test_invalid_limit_rejected(self):
        self.tick(lambda h, b: h.create_order_to_limit(100, 42.01, 'Buy', 'AOT'))
        self.assertEqual(self.quantity(), 0)
        self.assertIn('not a valid price', self.sim.error_logger.error_log[0]['message'])

    def test_auctions_and_sub_lot_ticks_never_fill(self):
        self.tick()  # Seed cumulative capacity so auction rejection is independently exercised.
        for flag in ['OPEN1_E', 'OPEN2_E', 'ATC']:
            self.tick(lambda h, b: (h.create_order_at_market(100, 'Buy', 'AOT'), h.create_order_to_limit(100, 43, 'Buy', 'AOT')), flag=flag)
        self.tick(lambda h, b: h.create_order_at_market(100, 'Buy', 'AOT'), volume=99)
        self.assertEqual(self.quantity(), 0)

    def test_day_cap_is_opposite_flag_volume(self):
        self.tick(volume=250)
        self.tick(lambda h, b: h.create_order_at_market(1000, 'Buy', 'AOT'), flag='Buy')
        self.assertEqual(self.quantity(), 200)
        self.tick(lambda h, b: h.create_order_at_market(100, 'Buy', 'AOT'), flag='Buy')
        self.assertEqual(self.quantity(), 200)

    def test_full_requested_cash_is_checked_before_partial_fill(self):
        self.tick(lambda h, b: h.create_order_at_market(1000000, 'Buy', 'AOT'), volume=100)
        self.assertEqual(self.quantity(), 0)
        self.assertIn('Insufficient cash', self.sim.error_logger.error_log[0]['message'])

    def test_no_short_nonlot_or_index_orders(self):
        self.tick(lambda h, b: (h.create_order_at_market(100, 'Sell', 'AOT'),
                               h.create_order_at_market(150, 'Buy', 'AOT'),
                               h.create_order_to_limit(100, 1000, 'Buy', 'SET50')))
        self.assertEqual(self.quantity(), 0)
        self.assertEqual(len(self.sim.error_logger.error_log), 3)

    def test_cross_symbol_market_rejected_and_limit_tried_once(self):
        self.tick(symbol='PTT')  # Seed PTT's day capacity.
        self.tick(lambda h, b: h.create_order_at_market(100, 'Buy', 'PTT'))
        self.assertEqual(self.quantity('PTT'), 0)
        self.tick(lambda h, b: h.create_order_to_limit(100, 43, 'Buy', 'PTT'))
        self.assertEqual(len(self.sim.get_open_orders()), 1)
        self.tick(symbol='PTT', price=44)
        self.assertEqual(self.sim.get_open_orders(), [])
        self.tick(symbol='PTT', price=42)
        self.assertEqual(self.quantity('PTT'), 0)

    def test_sell_limit_and_fee_cash_nav_fifo_reconcile(self):
        self.tick(lambda h, b: h.create_order_at_market(300, 'Buy', 'AOT'))
        buy_cost = 300 * 42.25 * (1 + .00157 * 1.07)
        self.assertAlmostEqual(self.runner.get_cash_balance(), 10000000 - buy_cost)
        self.assertAlmostEqual(self.sim.portfolio.get_nav(), 10000000 - buy_cost + 300 * 42)
        self.tick(lambda h, b: h.create_order_to_limit(100, 43, 'Sell', 'AOT'), flag='Buy', price=43)
        self.assertEqual(self.quantity(), 300)  # last price limit cannot sell
        self.tick(lambda h, b: h.create_order_to_limit(100, 42.75, 'Sell', 'AOT'), flag='Buy', price=43)
        self.assertEqual(self.runner.get_round_trip_count(), 0)
        self.tick(lambda h, b: h.create_order_at_market(200, 'Sell', 'AOT'), flag='Buy', price=43)
        pnl = 300 * 42.75 * (1 - .00157 * 1.07) - buy_cost
        self.assertEqual(self.quantity(), 0)
        self.assertEqual(self.runner.get_round_trip_count(), 1)
        self.assertEqual(self.runner.get_sell_order_count(), 2)
        self.assertAlmostEqual(self.runner.get_cash_balance(), 10000000 + pnl)
        self.assertAlmostEqual(self.runner.get_expected_payoff(), pnl)

    def test_other_symbol_fill_keeps_original_placed_time(self):
        self.tick(symbol='PTT')
        self.tick(lambda h, b: h.create_order_to_limit(100, 43, 'Buy', 'PTT'))
        self.tick(symbol='PTT')
        fill = self.sim.execution.tranLog.transaction_log[0]
        self.assertEqual(self.quantity('PTT'), 100)
        self.assertNotEqual(fill['Placed'], fill['Timestamp'])

    def test_tick_table_transition_and_sell_boundaries(self):
        for price, old_buy, old_sell, new_buy, new_sell in [
            (5, 5.05, 4.98, 5.02, 4.98), (10, 10.1, 9.95, 10.05, 9.98),
            (25, 25.25, 24.9, 25.1, 24.95), (50, 50.25, 49.75, 50.25, 49.9),
            (100, 100.5, 99.75, 100.5, 99.75), (200, 201, 199.5, 201, 199.5)]:
            with self.subTest(price=price):
                for day, buy, sell in [('2026-11-15', old_buy, old_sell), ('2026-11-16', new_buy, new_sell)]:
                    self.assertEqual(Costs.market_fill_price(price, 'Buy', day), buy)
                    self.assertEqual(Costs.market_fill_price(price, 'Sell', day), sell)
        self.assertFalse(Costs.is_valid_tick_price(42.1, '2026-11-15'))
        self.assertTrue(Costs.is_valid_tick_price(42.1, '2026-11-16'))

    def test_callback_is_each_tick_with_forming_bar(self):
        self.tick(price=42, volume=100)
        self.tick(price=43, volume=200)
        bars = self.handlers['AOT'].strategy.bars
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0]['Timestamp'], bars[1]['Timestamp'])
        self.assertEqual((bars[1]['Open'], bars[1]['High'], bars[1]['Low'], bars[1]['Close'], bars[1]['Volume']), (42, 43, 42, 43, 300))
        self.assertNotIn('Flag', bars[1])

    def test_history_excludes_entire_current_day_and_future(self):
        # Short intraday files begin after the first sample day.
        self.assertEqual(self.runner.get_historical_data('AOT', 1000, '1min'), [])
        self.sim.current_date = pd.Timestamp('2026-09-30').date()
        for timeframe in ['1D', '1min', '5min']:
            bars = self.runner.get_historical_data('AOT', 1000, timeframe)
            self.assertTrue(bars)
            key = 'Date' if timeframe == '1D' else 'Timestamp'
            self.assertLess(max(pd.Timestamp(b[key]) for b in bars), pd.Timestamp('2026-09-30'))
            self.assertLessEqual(len(bars), 1000)
        self.sim.current_date = None
        self.assertEqual(self.runner.get_historical_data('AOT', 10), [])
        with self.assertRaises(ValueError):
            self.runner.get_historical_data('AOT', 10, '2min')

    def test_daily_save_reload_and_metric_windows(self):
        self.tick(lambda h, b: h.create_order_at_market(100, 'Buy', 'AOT'))
        self.sim.save_summary_csv(pd.Timestamp('2026-09-09').date(), university_start_date='2026-09-09')
        self.sim.save_portfolio()
        saved_cash = self.runner.get_cash_balance()
        self.sim = tradeSim('probe', folder=self.tmp.name, current_date='2026-09-10')
        self.runner = self.sim.get_strategy_runner()
        self.assertAlmostEqual(self.runner.get_cash_balance(), saved_cash)
        self.assertEqual(self.quantity(), 100)
        self.assertIsNone(self.runner.get_benchmark_return())
        self.assertEqual(len(self.sim.portfolio.daily_snapshots), 1)
        self.sim.update_market_prices({'AOT': 40})
        self.sim.save_summary_csv(pd.Timestamp('2026-09-10').date(), university_start_date='2026-09-09')
        snapshots = self.sim.portfolio.daily_snapshots
        self.assertAlmostEqual(self.runner.get_average_exposure(), sum(d['invested_value'] / d['nav'] for d in snapshots) / 2)
        self.assertAlmostEqual(self.runner.get_max_draw_down(), (snapshots[0]['nav'] - snapshots[1]['nav']) / snapshots[0]['nav'] * 100)
        self.assertAlmostEqual(self.runner.get_benchmark_return(), (1081.8 / 1083.06 - 1) * 100)

    def test_known_limitation_multiple_limits_can_exceed_day_cap(self):
        # Characterize upstream behavior, not an endorsed execution rule.
        self.tick(volume=100)
        self.tick(lambda h, b: [h.create_order_to_limit(100, 43, 'Buy', 'AOT') for _ in range(2)], flag='Buy', volume=1000)
        self.assertEqual(self.quantity(), 200)
        self.assertEqual(self.sim.day_volume_left('AOT')[0], -100)


if __name__ == '__main__':
    unittest.main()
