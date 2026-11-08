"""Verify that failed entry does not itself liquidate an existing position."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_phase5 as phase5

path = phase5.ROOT / 'research/phase5-retention/DiversifiedBaseline.py'
spec = importlib.util.spec_from_file_location('RetentionStrategy', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RetentionBehavior(unittest.TestCase):
    def test_existing_holding_survives_entry_failure_but_risk_exit_sells(self):
        fixture = phase5.Phase5Execution(methodName='test_partial_fill_budget_and_no_duplicate_same_slot')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        with patch.object(phase5, 'Strategy', module.DiversifiedBaseline):
            first = fixture.handler()
            fixture.tick(first)
            held = fixture.sim.get_strategy_runner().get_total_stock_volume_by_symbol('AOT')
            self.assertGreater(held, 0)
            next_handler = fixture.handler()
            next_handler.strategy._build_plan('2026-09-09')
            next_handler.strategy.plan['targets'].pop('AOT', None)
            with patch.object(next_handler.strategy, '_exit_signal', return_value=None):
                decision = fixture.tick(next_handler, clock='10:20:01', flag='Buy')
            self.assertEqual(decision['target'], held)
            self.assertEqual(decision['requested_quantity'], 0)
            with patch.object(next_handler.strategy, '_exit_signal', return_value='volatility_stop'):
                decision = fixture.tick(next_handler, clock='10:35:01', flag='Buy')
            self.assertEqual(decision['side'], 'Sell')
            self.assertEqual(decision['reason'], 'volatility_stop')
            self.assertGreater(decision['filled_quantity'], 0)


if __name__ == '__main__':
    unittest.main()
