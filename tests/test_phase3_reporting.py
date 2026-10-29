"""Independent economic examples and scoring boundary checks."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from phase3_reporting import FillLedger, benchmark_metrics, drawdown_pct, eligibility


def fill(side, quantity, price, order='1', symbol='AOT'):
    return {'Side': side, 'Volume': quantity, 'Price': price, 'Order Number': order, 'Symbol': symbol}


class Reporting(unittest.TestCase):
    def test_fifo_partial_closes_and_both_sides_fees(self):
        ledger = FillLedger(100000)
        ledger.apply(fill('Buy', 300, 10, '1'))
        ledger.apply(fill('Buy', 200, 12, '2'))
        ledger.apply(fill('Sell', 200, 11, '3'))
        self.assertEqual(len(ledger.completed), 0)
        self.assertIsNone(ledger.expected_payoff())
        ledger.apply(fill('Sell', 200, 13, '4'))
        self.assertEqual(len(ledger.completed), 1)
        self.assertEqual(ledger.quantities(), {'AOT': 100})
        # First buy lot: 200 sold at 11, remaining 100 at 13; both sides taxed.
        fees = (3000 + 2400 + 2200 + 2600) * .0016799
        payoff = (2200 + 1300) * (1 - .0016799) - 3000 * (1 + .0016799)
        self.assertAlmostEqual(ledger.fees, fees)
        self.assertAlmostEqual(ledger.cash, 100000 - 3000 - 2400 + 2200 + 2600 - fees)
        self.assertAlmostEqual(ledger.expected_payoff(), payoff)
        self.assertAlmostEqual(ledger.realized, payoff + 1300 * (1 - .0016799) - 1200 * (1 + .0016799))

    def test_multiple_fills_of_one_buy_order_are_one_fifo_lot(self):
        ledger = FillLedger()
        ledger.apply(fill('Buy', 100, 10))
        ledger.apply(fill('Buy', 200, 11))
        ledger.apply(fill('Sell', 300, 12, '2'))
        self.assertEqual(len(ledger.completed), 1)
        self.assertEqual(ledger.completed[0]['volume'], 300)

    def test_breakeven_completion_has_undefined_payoff(self):
        ledger = FillLedger()
        # Construct a mathematically exact flat net lot in the accounting fixture.
        ledger.completed = [{'pnl': 0.0}]
        self.assertIsNone(ledger.expected_payoff())
        ledger.completed += [{'pnl': 300.0}, {'pnl': -100.0}]
        self.assertEqual(ledger.expected_payoff(), 100.0)

    def test_illegal_short_cash_and_nonlot_fills_fail(self):
        for bad in [fill('Sell', 100, 10), fill('Buy', 100, 1000000),
                    fill('Buy', 150, 10), fill('Buy', 100, float('nan'))]:
            with self.subTest(fill=bad), self.assertRaises(AssertionError):
                FillLedger(1000).apply(bad)

    def test_benchmark_requires_every_date_and_ignores_future_rows(self):
        days = ['2026-09-09', '2026-09-10', '2026-09-11']
        rows = [{'Date': d, 'Close': p} for d, p in zip(days, [100, 90, 95])]
        result = benchmark_metrics(rows + [{'Date': '2026-09-12', 'Close': 999}], days)
        self.assertAlmostEqual(result['return_pct'], -5)
        self.assertEqual(result['max_drawdown_pct'], 10)
        for incomplete in [[], rows[:2], rows[1:], rows + rows[:1],
                           rows[:2] + [{'Date': days[-1], 'Close': float('nan')}]]:
            self.assertFalse(benchmark_metrics(incomplete, days)['complete'])
            self.assertIsNone(benchmark_metrics(incomplete, days)['return_pct'])

    def test_drawdown_anchors_are_distinct(self):
        self.assertAlmostEqual(drawdown_pct([100, 90, 95, 89]), 11)
        self.assertAlmostEqual(drawdown_pct([90, 95, 89]), 6 / 95 * 100)

    def test_strict_unrounded_thresholds_and_separate_stock_count(self):
        metrics = {'distinct_stocks': 5, 'completed_fifo_round_trips': 5,
                   'average_exposure': .5, 'expected_payoff_thb': .00001,
                   'net_return_pct': 0, 'excess_return_pp': 0,
                   'official_max_drawdown_pct': 1.499999, 'benchmark_max_drawdown_pct': 1}
        self.assertEqual(eligibility(metrics)['best_alpha_status'], 'pass')
        for key, value in [('distinct_stocks', 4), ('completed_fifo_round_trips', 4),
                           ('average_exposure', .4999999), ('expected_payoff_thb', 0),
                           ('net_return_pct', -.00001), ('excess_return_pp', -.00001),
                           ('official_max_drawdown_pct', 1.5)]:
            with self.subTest(key=key):
                result = eligibility({**metrics, key: value})
                self.assertEqual(result['best_alpha_status'], 'fail')
        result = eligibility({**metrics, 'completed_fifo_round_trips': 0, 'expected_payoff_thb': None})
        self.assertEqual(result['checks']['distinct_stocks']['status'], 'pass')
        self.assertEqual(result['checks']['completed_fifo_round_trips']['status'], 'fail')
        self.assertEqual(result['checks']['expected_payoff_thb']['status'], 'unknown')

    def test_missing_nonfinite_and_zero_benchmark_are_unknown(self):
        for bm in [None, 0, float('nan')]:
            result = eligibility({'official_max_drawdown_pct': 0, 'benchmark_max_drawdown_pct': bm})
            self.assertEqual(result['checks']['relative_drawdown']['status'], 'unknown')
            self.assertEqual(result['best_alpha_status'], 'unknown')
            self.assertEqual(result['competition_acceptance'], 'unknown')


if __name__ == '__main__':
    unittest.main()
