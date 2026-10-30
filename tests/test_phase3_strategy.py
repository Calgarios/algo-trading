"""Controlled strategy scenarios using the unchanged official matching engine."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_support import ROOT, PACKAGE, verify_package
from phase3_support import check_submission_shape, load_baseline
from phase3_reporting import FillLedger

verify_package()
os.chdir(PACKAGE)
os.environ['TZ'] = 'UTC'
time.tzset()
sys.path.insert(0, str(PACKAGE))
import pandas as pd
from tradeSim.TradeSim import tradeSim
from tradeSim.StrategyHandler import StrategyHandler
from tradeSim.CommissionService import commissionService

Baseline = load_baseline()


class BaselineContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.day = '2026-09-09'
        self.history = [{'Date': str(d.date()), 'Close': 42.0}
                        for d in pd.bdate_range('2026-08-01', '2026-08-31')]
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date=self.day)
        self.handler = self.make_handler()

    def make_handler(self, histories=None):
        with patch.object(StrategyHandler, 'get_historical_data',
                          side_effect=lambda symbol, n, timeframe: (histories or {}).get(symbol, self.history)):
            return StrategyHandler(Baseline, self.sim.get_strategy_runner(), str(ROOT / 'strategy'))

    def tick(self, clock='10:05:01', volume=100000, price=42, flag='Sell', symbol='AOT', handler=None):
        handler = handler or self.handler
        row = {'ShareCode': symbol, 'TradeDateTime': pd.Timestamp(f'{self.day} {clock}'),
               'LastPrice': price, 'Volume': volume, 'Value': price * volume, 'Flag': flag}
        handler.process_row(row)
        self.sim.isMatch(row)
        self.sim.update_market_prices({symbol: price})
        return handler.strategy.last_decision

    def test_partial_fill_retries_actual_deficit_only_next_slot(self):
        first = dict(self.tick(volume=350))
        self.assertEqual(first['filled_quantity'], 300)
        self.assertEqual(first['requested_quantity'], 16600)
        self.tick('10:05:02')
        self.assertEqual(self.handler.strategy.decision_sequence, 1)
        second = self.tick('10:20:01', volume=100)
        self.assertEqual(second['requested_quantity'], 16300)
        self.assertEqual(second['filled_quantity'], 100)
        self.assertEqual(self.sim.get_open_orders(), [])

    def test_auction_and_zero_liquidity_do_not_imply_fills(self):
        self.tick(volume=100, flag='Buy')  # No opposite-side allowance.
        self.assertEqual(self.handler.strategy.last_decision['filled_quantity'], 0)
        self.tick('10:20:01', flag='ATC')
        self.assertEqual(self.handler.strategy.last_decision['filled_quantity'], 0)
        self.tick('10:35:01', volume=99)
        self.assertEqual(self.handler.strategy.last_decision['filled_quantity'], 0)
        self.tick('10:50:01', volume=100)
        self.assertEqual(self.handler.strategy.last_decision['filled_quantity'], 100)

    def test_equal_targets_hold_without_churn(self):
        self.tick()
        second = self.tick('10:20:01')
        self.assertEqual(second['reason'], 'at_target')
        self.assertEqual(len(self.sim.execution.tranLog.transaction_log), 1)

    def test_missing_short_stale_invalid_and_future_history_pause(self):
        invalid = [[], self.history[:10],
                   [{'Date': '2026-07-01', 'Close': 42}] * 20,
                   self.history[:-1] + [{'Date': '2026-08-31', 'Close': float('nan')}],
                   self.history + [{'Date': self.day, 'Close': 42}]]
        for bars in invalid:
            self.history = bars
            handler = self.make_handler()
            decision = self.tick(handler=handler)
            self.assertEqual(decision['reason'], 'unavailable_plan')
            self.assertEqual(decision['requested_quantity'], 0)

    def test_history_selection_is_identical_across_symbol_instances(self):
        other = self.make_handler()
        self.tick(handler=self.handler)
        self.tick(symbol='ADVANC', handler=other)
        self.assertEqual(self.handler.strategy.plan, other.strategy.plan)
        self.assertEqual(len(self.handler.strategy.plan['targets']), 10)
        self.assertLess(max(b['date'] for v in self.handler.strategy.plan['eligible'].values()
                            for b in v['history']), '2026-09-01')

    def test_intra_month_history_does_not_change_targets(self):
        self.tick()
        original = self.handler.strategy.plan
        self.history += [{'Date': '2026-09-08', 'Close': 99999}]
        later = self.make_handler()
        self.tick(handler=later)
        self.assertEqual(original, later.strategy.plan)

    def test_momentum_ranking_uses_only_prior_month_closes_and_stable_ties(self):
        rising = [dict(b) for b in self.history]
        rising[-20]['Close'] = 21
        rising += [{'Date': '2026-09-08', 'Close': 1}]
        handler = self.make_handler({'WHA': rising})
        handler.strategy.config['selection'] = 'momentum20'
        self.tick(handler=handler)
        self.assertEqual(handler.strategy.plan['selected'][0], 'WHA')
        self.assertEqual(handler.strategy.plan['selected'][1:3], ['ADVANC', 'AOT'])
        self.assertEqual(handler.strategy.plan['eligible']['WHA']['momentum20'], 1)
        self.assertEqual(handler.strategy.plan['targets']['WHA'], 16600)

    def test_daily_reload_rebuilds_plan_without_duplicate_target(self):
        self.tick()
        self.sim.save_summary_csv(pd.Timestamp(self.day).date(), university_start_date=self.day)
        self.sim.save_portfolio()
        self.day = '2026-09-10'
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date=self.day)
        self.handler = self.make_handler()
        decision = self.tick()
        self.assertEqual(decision['reason'], 'at_target')
        self.assertEqual(self.sim.execution.tranLog.transaction_log, [])

    def test_month_change_sells_excess_and_fifo_reconciles(self):
        self.tick()
        ledger = FillLedger()
        ledger.apply(self.sim.execution.tranLog.transaction_log[0])
        self.day = '2026-10-01'
        self.sim.current_date = pd.Timestamp(self.day).date()
        self.history = [{'Date': str(d.date()), 'Close': 84.0}
                        for d in pd.bdate_range('2026-09-01', '2026-09-30')]
        self.handler = self.make_handler()
        decision = self.tick(price=84, flag='Buy')
        self.assertEqual((decision['side'], decision['requested_quantity']), ('Sell', 8300))
        ledger.apply(self.sim.execution.tranLog.transaction_log[-1])
        self.assertEqual(len(ledger.completed), 0)  # Half of original lot remains.
        self.assertEqual(ledger.quantities(), {'AOT': 8300})
        self.assertAlmostEqual(ledger.cash, self.sim.portfolio.get_cash_balance())
        self.assertAlmostEqual(ledger.realized, self.sim.portfolio.get_realized())

    def test_removed_name_liquidates_and_completes_fifo(self):
        self.tick()
        ledger = FillLedger()
        ledger.apply(self.sim.execution.tranLog.transaction_log[0])
        self.handler = self.make_handler({'AOT': []})
        decision = self.tick('10:20:01', price=43, flag='Buy')
        self.assertEqual(decision['side'], 'Sell')
        self.assertEqual(decision['held_after'], 0)
        ledger.apply(self.sim.execution.tranLog.transaction_log[-1])
        self.assertEqual(len(ledger.completed), 1)
        self.assertAlmostEqual(ledger.expected_payoff(), self.sim.portfolio.get_expected_payoff())

    def test_prebuy_position_cap_includes_cost_reduction_in_nav(self):
        # Lower account equity makes the fixed-capital target exceed the 10% cap.
        self.sim.portfolio.cashbalance = 2100000
        self.handler = self.make_handler()
        decision = self.tick()
        nav = self.sim.portfolio.get_nav()
        self.assertLess(decision['requested_quantity'], decision['target'])
        self.assertLessEqual(decision['held_after'] * 42, nav * .10)
        self.assertGreaterEqual(decision['cash_after'], nav * .20)

    def test_cash_and_exposure_limits_at_conservative_opening_nav(self):
        # Exercise capacity math on a deliberately constrained account snapshot.
        self.sim.portfolio.cashbalance = 2050000
        self.handler = self.make_handler()
        self.handler.strategy.opening_nav = 10000000
        # min(opening NAV, current marked NAV) must prevent oversized allocation.
        decision = self.tick()
        self.assertEqual(decision['nav_for_limits'], 2050000)
        self.assertLessEqual(decision['held_after'] * 42, self.sim.portfolio.get_nav() * .1)

    def test_cash_reserve_and_portfolio_exposure_constrain_last_purchase(self):
        symbols = self.handler.strategy.config['universe'][:10]
        for symbol in symbols[:9]:
            self.tick(symbol=symbol, handler=self.make_handler())
        # A cash withdrawal here is only a fixture to put exposure close to 80%.
        self.sim.portfolio.cashbalance = 1600000
        handler = self.make_handler()
        decision = self.tick(symbol=symbols[-1], handler=handler)
        nav = self.sim.portfolio.get_nav()
        cash = self.sim.portfolio.get_cash_balance()
        self.assertGreater(decision['requested_quantity'], 0)
        self.assertLess(decision['requested_quantity'], decision['target'])
        self.assertGreaterEqual(cash, .20 * nav)
        self.assertLessEqual((nav - cash) / nav, .80)
        again = self.tick('10:20:01', symbol=symbols[-1], handler=handler)
        self.assertEqual(again['reason'], 'risk_or_lot_limit')

    def test_new_selection_waits_for_position_slot_to_be_freed(self):
        symbols = self.handler.strategy.config['universe'][:10]
        for symbol in symbols:
            self.tick(symbol=symbol, handler=self.make_handler())
        replacement = self.handler.strategy.config['universe'][10]
        handler = self.make_handler({'AOT': []})
        decision = self.tick(symbol=replacement, handler=handler)
        self.assertEqual(decision['reason'], 'position_count_limit')
        self.assertEqual(len(self.sim.portfolio.get_all_stocks_info()), 10)

    def test_pending_orders_block_new_intents(self):
        with patch.object(self.handler, 'get_open_orders', return_value=[{'order': 'pending'}]):
            decision = self.tick()
        self.assertEqual(decision['reason'], 'pending_order')
        self.assertEqual(self.sim.execution.tranLog.transaction_log, [])

    def test_unpermitted_symbol_and_invalid_price_cannot_order(self):
        decision = self.tick(symbol='SET50')
        self.assertEqual(decision['reason'], 'unpermitted_symbol')
        self.handler.strategy.on_data({'ShareCode': 'AOT', 'Timestamp': '2026-09-09 10:20:00', 'Close': float('nan')})
        self.assertEqual(self.handler.strategy.last_decision['reason'], 'invalid_price')
        self.assertEqual(self.sim.execution.tranLog.transaction_log, [])

    def test_outside_execution_windows_cannot_order(self):
        for clock in ['10:04:59', '12:25:00', '14:34:59', '16:20:00']:
            self.tick(clock)
        self.assertEqual(self.handler.strategy.decision_sequence, 0)

    def test_buy_price_matches_official_transition_and_bands(self):
        for day in ['2026-11-15', '2026-11-16']:
            for price in [1, 2, 5, 10, 25, 50, 100, 200, 400]:
                self.assertEqual(Baseline.buy_price(price, day), commissionService.market_fill_price(price, 'Buy', day))
                self.assertEqual(Baseline.sell_price(price, day), commissionService.market_fill_price(price, 'Sell', day))

    def enable_exits(self, handler=None):
        handler = handler or self.handler
        handler.strategy.config['exit_policy'] = {
            'take_profit_net': .02, 'stop_loss_net': .04, 'max_holding_sessions': 10}

    def test_profit_exit_is_net_of_both_sides_costs(self):
        self.enable_exits()
        self.tick()
        decision = self.tick('10:20:01', price=43.25, flag='Buy')
        self.assertEqual(decision['reason'], 'at_target')
        self.assertLess(decision['estimated_net_liquidation_return'], .02)
        decision = self.tick('10:35:01', price=44, flag='Buy')
        self.assertEqual(decision['reason'], 'take_profit')
        self.assertEqual(decision['held_after'], 0)
        self.assertGreater(self.sim.portfolio.get_expected_payoff(), 0)
        decision = self.tick('10:50:01', price=42)
        self.assertEqual(decision['reason'], 'same_day_reentry_blocked')

    def test_partial_stop_loss_remains_exit_only_for_the_day(self):
        self.enable_exits()
        self.tick()
        decision = self.tick('10:20:01', price=40, flag='Buy', volume=100)
        self.assertEqual(decision['reason'], 'stop_loss')
        self.assertEqual(decision['filled_quantity'], 100)
        decision = self.tick('10:35:01', price=42, flag='Buy')
        self.assertEqual(decision['reason'], 'stop_loss')
        self.assertEqual(decision['held_after'], 0)
        self.assertLess(self.sim.portfolio.get_expected_payoff(), 0)

    def test_time_exit_uses_trading_sessions_and_survives_daily_reload(self):
        self.tick()
        self.sim.save_summary_csv(pd.Timestamp(self.day).date(), university_start_date=self.day)
        self.sim.save_portfolio()
        self.day = '2026-09-23'
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date=self.day)
        self.history += [{'Date': str(d.date()), 'Close': 42.0}
                         for d in pd.bdate_range('2026-09-01', '2026-09-22')]
        self.handler = self.make_handler()
        self.enable_exits()
        decision = self.tick(flag='Buy', volume=100)
        self.assertEqual(decision['reason'], 'holding_period')
        self.assertEqual(decision['holding_sessions'], 10)
        self.assertEqual(decision['filled_quantity'], 100)
        self.sim.save_summary_csv(pd.Timestamp(self.day).date(), university_start_date='2026-09-09')
        self.sim.save_portfolio()
        self.day = '2026-09-24'
        self.history += [{'Date': '2026-09-23', 'Close': 42.0}]
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date=self.day)
        self.handler = self.make_handler()
        self.enable_exits()
        decision = self.tick(flag='Buy')
        self.assertEqual(decision['reason'], 'holding_period')
        self.assertEqual(decision['held_after'], 0)

    def test_missing_plan_does_not_disable_price_risk_exits(self):
        self.tick()
        self.history = []
        self.handler = self.make_handler()
        self.enable_exits()
        decision = self.tick('10:20:01', price=39, flag='Buy')
        self.assertEqual(decision['reason'], 'stop_loss')
        self.assertIsNone(decision['holding_sessions'])
        self.assertEqual(decision['held_after'], 0)

    def test_old_entry_outside_history_still_expires_with_ten_observed_sessions(self):
        self.tick()
        self.day = '2026-10-01'
        self.sim.current_date = pd.Timestamp(self.day).date()
        self.history = [{'Date': str(d.date()), 'Close': 42.0}
                        for d in pd.bdate_range('2026-09-14', '2026-09-30')]
        self.handler = self.make_handler()
        self.enable_exits()
        decision = self.tick(flag='Buy')
        self.assertEqual(decision['reason'], 'holding_period')
        self.assertGreaterEqual(decision['holding_sessions'], 10)
        self.assertEqual(decision['held_after'], 0)

    def test_partial_sale_nav_uses_saved_market_value_for_other_symbols(self):
        # The engine restores a partially sold lot's Market Price using start
        # volume; its stored Market Value is the correct prior closing mark.
        self.tick(symbol='AOT')
        self.enable_exits()
        self.tick('10:20:01', symbol='AOT', price=44, flag='Buy', volume=8300)
        self.sim.save_summary_csv(pd.Timestamp(self.day).date(), university_start_date=self.day)
        self.sim.save_portfolio()
        self.day = '2026-09-10'
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date=self.day)
        other = self.make_handler()
        stocks = self.sim.portfolio.get_all_stocks_info()
        marked = sum(h['Market Value'] for h in stocks)
        self.assertNotEqual(marked, sum(h['Actual Volume'] * h['Market Price'] for h in stocks))
        decision = self.tick(symbol='ADVANC', handler=other)
        self.assertEqual(decision['invested_before'], marked)

    def test_local_submission_shape(self):
        self.assertEqual(check_submission_shape()['local_structure_checks'], 'pass')


if __name__ == '__main__':
    unittest.main()
