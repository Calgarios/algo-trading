"""Execution invariants for the separately frozen alpha experiment."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_phase5 as base
spec = importlib.util.spec_from_file_location('AlphaStrategy', base.ROOT / 'research/phase5-alpha/DiversifiedBaseline.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaExecution(unittest.TestCase):
    def setUp(self):
        self.fixture = base.Phase5Execution(methodName='test_full_universe_can_trade_more_than_ten')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.config['phase5']['alpha_policy'] = 'breakout'
        self.patch = patch.object(base, 'Strategy', module.DiversifiedBaseline)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_retention_does_not_sell_for_small_target_reduction(self):
        f = self.fixture
        h = f.handler()
        f.tick(h)
        held = f.sim.get_strategy_runner().get_total_stock_volume_by_symbol('AOT')
        self.assertGreater(held, 100)
        h.strategy.plan['targets']['AOT'] = held - 100
        with patch.object(h.strategy, '_exit_signal', return_value=None):
            d = f.tick(h, clock='10:20:01', flag='Buy')
        self.assertEqual(d['requested_quantity'], 0)
        self.assertEqual(d['target'], held)

    def test_actual_position_cap_reduces_retained_holding(self):
        f = self.fixture
        h = f.handler()
        f.tick(h)
        held = f.sim.get_strategy_runner().get_total_stock_volume_by_symbol('AOT')
        h.strategy.config['max_position'] = .005
        h.strategy.rebalance_active = False
        with patch.object(h.strategy, '_exit_signal', return_value=None):
            d = f.tick(h, clock='10:20:01', flag='Buy')
        self.assertEqual(d['side'], 'Sell')
        self.assertGreater(d['filled_quantity'], 0)
        self.assertLess(d['target'], held)

    def test_portfolio_guard_reduces_actual_holdings(self):
        f = self.fixture
        handlers = {s: f.handler() for s in f.config['universe']}
        for s, h in handlers.items():
            f.tick(h, s=s)
        h = handlers['AOT']
        with patch.object(h.strategy, 'risk_target', return_value=(.35, 'hard_drawdown')), patch.object(h.strategy, '_exit_signal', return_value=None):
            d = f.tick(h, clock='10:20:01', flag='Buy')
        self.assertEqual(d['side'], 'Sell')
        self.assertGreater(d['filled_quantity'], 0)

    def test_high_friction_entry_is_rejected(self):
        h = self.fixture.handler()
        with patch.object(h.strategy, 'buy_price', return_value=10000):
            h.strategy._build_plan('2026-09-09')
        self.assertEqual(h.strategy.plan['selected'], [])
        self.assertTrue(all(not c['cost_hurdle'] for c in h.strategy.plan['checks'].values()))

    def test_relative_policy_retains_profit_until_trailing_exit(self):
        from types import SimpleNamespace
        lot = SimpleNamespace(get_actual_vol=lambda: 100,
                              get_buy_price=lambda: 100,
                              get_buy_time_str=lambda: '2026-09-01 10:00:00')
        obj = module.DiversifiedBaseline.__new__(module.DiversifiedBaseline)
        obj.handler = SimpleNamespace(get_stock_by_symbol=lambda symbol: [lot])
        obj.history = {'AOT': [{'Date': f'2026-09-{d:02}', 'Close': 112} for d in range(1, 9)]}
        obj.plan = {'features': {'AOT': {'sma60': 90, 'ret20': .1, 'atr14_fraction': .01}}}
        obj.config = {'phase5': {'alpha_policy': 'breakout'}}
        self.assertEqual(obj._exit_signal('AOT', 110, '2026-09-09', {}), 'mature_profit')
        obj.config['phase5']['alpha_policy'] = 'relative'
        self.assertIsNone(obj._exit_signal('AOT', 110, '2026-09-09', {}))
        obj.history['AOT'][-1]['Close'] = 120
        self.assertEqual(obj._exit_signal('AOT', 110, '2026-09-09', {}), 'trailing_trend_exit')

    def test_future_history_remains_rejected(self):
        f = self.fixture
        f.bars[-1]['Date'] = '2026-09-09'
        h = f.handler()
        h.strategy._build_plan('2026-09-09')
        self.assertEqual(h.strategy.plan['selected'], [])


if __name__ == '__main__':
    unittest.main()
