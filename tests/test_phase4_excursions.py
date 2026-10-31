"""Known quote paths and timestamp-boundary ambiguity in post-trade diagnostics."""
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from phase4_lot_excursions import quote_window, completed_excursions


class QuoteExcursions(unittest.TestCase):
    def test_known_adverse_and_favorable_price_path(self):
        result = quote_window(np.array([1, 2, 3, 4]), np.array([10, 8, 11, 10]), 1, 4, 10, 10, 10)
        self.assertAlmostEqual(result['mae_quote_pct'], -20)
        self.assertAlmostEqual(result['mfe_quote_pct'], 10)
        self.assertEqual(result['strictly_interior_ticks'], 2)

    def test_ambiguous_same_timestamp_endpoints_use_only_actual_fill_quotes(self):
        result = quote_window(np.array([1, 1, 2, 3, 3]), np.array([1, 99, 9, 2, 90]), 1, 3, 10, 11, 10)
        self.assertAlmostEqual(result['mae_quote_pct'], -10)
        self.assertAlmostEqual(result['mfe_quote_pct'], 10)
        self.assertEqual(result['strictly_interior_ticks'], 1)

    def test_no_interior_ticks_and_invalid_intervals(self):
        result = quote_window(np.array([1]), np.array([99]), 1, 1, 9.9, 9.8, 10)
        self.assertAlmostEqual(result['mae_quote_pct'], -2)
        self.assertEqual(result['mfe_quote_pct'], 0)
        self.assertEqual(result['strictly_interior_ticks'], 0)
        with self.assertRaises(ValueError):
            quote_window(np.array([1, 2]), np.array([10, 11]), 2, 1, 10, 11, 10)

    def test_utc_fill_times_align_with_bangkok_quotes_through_partial_exits(self):
        fills = [
            {'Symbol': 'AAA', 'Side': 'Buy', 'Volume': 200, 'Price': 10, 'Market Price': 9.9,
             'Order Number': 'buy', 'Timestamp': '2026-09-09 03:00:00'},
            {'Symbol': 'AAA', 'Side': 'Sell', 'Volume': 100, 'Price': 9, 'Market Price': 9.1,
             'Order Number': 'sell1', 'Timestamp': '2026-09-09 03:01:00'},
            {'Symbol': 'AAA', 'Side': 'Sell', 'Volume': 100, 'Price': 11, 'Market Price': 11.1,
             'Order Number': 'sell2', 'Timestamp': '2026-09-09 03:02:00'},
        ]
        times = np.array(['2026-09-09T10:00:00', '2026-09-09T10:01:00', '2026-09-09T10:02:00'], dtype='datetime64[ns]')
        result = completed_excursions(fills, {'AAA': (times, np.array([9.9, 8, 11.1]))})
        self.assertEqual(len(result['completed_lots']), 1)
        lot = result['completed_lots'][0]
        self.assertIn('T10:00:00', lot['first_buy_bangkok'])
        self.assertAlmostEqual(lot['mae_quote_pct'], -20)
        self.assertAlmostEqual(lot['mfe_quote_pct'], 11)


if __name__ == '__main__':
    unittest.main()
