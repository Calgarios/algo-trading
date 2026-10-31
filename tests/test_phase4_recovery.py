"""Economic checks for price concessions measured from verified fill-time quotes."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_phase4_recovery import fill_slippage


def fill(symbol='AAA', side='Buy', volume=100, price=10.1, quote=10):
    return {'Symbol': symbol, 'Side': side, 'Volume': volume, 'Price': price,
            'Market Price': quote, 'Type': 'Market'}


class FillPriceConcession(unittest.TestCase):
    def test_buys_and_sells_both_contribute_adverse_price_cost(self):
        result = fill_slippage([fill(), fill(side='Sell', volume=200, price=9.95),
                                fill(symbol='BBB', volume=300, price=20.1, quote=20)])
        self.assertAlmostEqual(result['by_symbol_thb']['AAA'], 20)
        self.assertAlmostEqual(result['by_symbol_thb']['BBB'], 30)
        self.assertAlmostEqual(result['filled_price_concession_thb'], 50)
        self.assertEqual(result['fill_rows'], 3)

    def test_invalid_quotes_sides_quantities_and_nonmarket_fills_fail(self):
        for fields in ({'Market Price': None}, {'Market Price': float('nan')},
                       {'Market Price': 0}, {'Side': 'Unknown'}, {'Volume': 150},
                       {'Volume': 0}, {'Type': 'Limit'}, {'Price': 9.9}):
            with self.subTest(fields=fields), self.assertRaises((TypeError, ValueError)):
                fill_slippage([{**fill(), **fields}])


if __name__ == '__main__':
    unittest.main()
