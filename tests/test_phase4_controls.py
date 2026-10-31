"""Official-engine checks for the declared Phase 4 allocation controls."""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_support import ROOT, PACKAGE, verify_package
from phase3_support import load_baseline
from prepare_phase4_controls import CONTROL_SOURCE, make_configs

verify_package()
sys.path.insert(0, str(PACKAGE))
os.chdir(PACKAGE)
import pandas as pd
from tradeSim.TradeSim import tradeSim
from tradeSim.StrategyHandler import StrategyHandler
from test_strategy_suite import history

spec = importlib.util.spec_from_file_location('Phase4Control', ROOT / CONTROL_SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Control = module.DiversifiedBaseline


class AllocationControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sim = tradeSim('baseline', folder=self.tmp.name, current_date='2026-09-09')
        self.configs = make_configs(load_baseline())
        self.bars = history()

    def handler(self, key, config=None):
        config = copy.deepcopy(config or self.configs[key])
        with patch.object(StrategyHandler, 'load_json', return_value=config), patch.object(
                StrategyHandler, 'get_historical_data', return_value=copy.deepcopy(self.bars)):
            return StrategyHandler(Control, self.sim.get_strategy_runner(), str(ROOT / 'strategy'))

    def tick(self, handler, symbol='PTT', clock='10:05:01', volume=100000):
        price = round(self.bars[-1]['Close'] * 4) / 4
        row = {'ShareCode': symbol, 'TradeDateTime': pd.Timestamp('2026-09-09 ' + clock),
               'LastPrice': price, 'Volume': volume, 'Value': volume * price, 'Flag': 'Sell'}
        handler.process_row(row)
        self.sim.update_market_prices({symbol: price})
        return handler.strategy.last_decision

    def test_equal_weights_preserve_basket_and_normal_soft_hard_targets(self):
        for key in ('P-C2', 'P-C3'):
            for dd, target in [(0, .76), (2.01, .72), (4.01, .55)]:
                handler = self.handler(key)
                handler.strategy.opening_drawdown = dd
                handler.strategy._build_plan('2026-09-09')
                plan = handler.strategy.plan
                self.assertEqual(set(plan['selected']), set(self.configs[key]['suite']['basket']))
                self.assertEqual(set(plan['weights'].values()), {target / 10})
                self.assertAlmostEqual(sum(plan['weights'].values()), target)

    def test_passive_targets_are_prestart_and_match_original_first_plan(self):
        initial = self.configs['H-C3']['research_control']['initial_allocation']
        self.assertTrue(all(f['history_end'] < initial['date'] for f in initial['eligible'].values()))
        # Published pre-start basket order already captures the C3 day-one ranking.
        self.assertEqual(initial['selected'], self.configs['H-C3']['suite']['basket'])
        for rank, symbol in enumerate(initial['selected']):
            self.assertAlmostEqual(initial['weights'][symbol], .076 * (1.2 - .4 * rank / 9))

    def test_passive_ignores_later_signal_nav_and_guard_and_never_sells(self):
        handler = self.handler('H-C3')
        initial = copy.deepcopy(handler.strategy.config['research_control']['initial_allocation'])
        handler.strategy.opening_nav = 9000000
        handler.strategy.opening_drawdown = 10
        handler.strategy.history = {}
        handler.strategy._build_plan('2026-09-30')
        self.assertEqual(handler.strategy.plan['targets'], initial['targets'])
        self.assertEqual(handler.strategy.plan['drawdown_guard'], 'passive_fixed_quantities')
        self.assertTrue(handler.strategy.rebalance_active)
        with patch.object(handler, 'get_total_stock_volume_by_symbol', return_value=initial['targets']['PTT'] + 100):
            decision = self.tick(handler)
        self.assertEqual(decision['reason'], 'passive_hold')
        self.assertEqual(decision['requested_quantity'], 0)

    def test_passive_partial_buy_retries_actual_residual(self):
        handler = self.handler('H-C3')
        first = dict(self.tick(handler, volume=100))
        self.assertEqual(first['filled_quantity'], 100)
        second = self.tick(handler, clock='10:20:01', volume=100)
        self.assertEqual(second['side'], 'Buy')
        self.assertEqual(second['held_before'], 100)
        self.assertEqual(second['filled_quantity'], 100)
        self.assertEqual(second['target'], first['target'])

    def test_wide_band_suppresses_medium_gap_but_active_partial_intent_retries(self):
        seed = self.handler('R-C3')
        self.tick(seed)
        held = self.sim.get_strategy_runner().get_total_stock_volume_by_symbol('PTT')
        price = round(self.bars[-1]['Close'] * 4) / 4
        gap = int(60000 / price / 100) * 100
        wide = self.handler('B-C3')
        wide.strategy._build_plan('2026-09-09')
        wide.strategy.plan['targets']['PTT'] = held + gap
        self.assertEqual(self.tick(wide)['reason'], 'rebalance_band')
        narrow = self.handler('R-C3')
        narrow.strategy._build_plan('2026-09-09')
        narrow.strategy.plan['targets']['PTT'] = held + gap
        first = dict(self.tick(narrow, volume=100))
        self.assertEqual(first['filled_quantity'], 100)
        second = self.tick(narrow, clock='10:20:01', volume=100)
        self.assertEqual(second['requested_quantity'], first['requested_quantity'] - 100)

    def test_invalid_mode_future_or_changed_passive_targets_fail(self):
        for change in ('identity', 'future', 'target'):
            config = copy.deepcopy(self.configs['H-C3'])
            control = config['research_control']
            if change == 'identity':
                control['mode'] = 'equal_weight'
            elif change == 'future':
                control['initial_allocation']['eligible']['PTT']['history_end'] = '2026-09-09'
            else:
                control['initial_allocation']['targets']['PTT'] += 100
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.handler('H-C3', config)


if __name__ == '__main__':
    unittest.main()
