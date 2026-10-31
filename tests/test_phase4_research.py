"""Accounting, evidence-integrity and declaration checks without TradeSim imports."""
import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_support import ROOT, sha256
from phase4_diagnostics import (analyze_bundle, analyze_fills, analyze_run, collect,
                                read_json, write_json)
from run_phase4_control import declaration


def fill(symbol, side, quantity, price, order, timestamp):
    return {'Symbol': symbol, 'Side': side, 'Volume': quantity, 'Price': price,
            'Order Number': order, 'Timestamp': timestamp}


def accounting_example():
    # Cross-symbol clocks go backwards within a day, as in notebook replay.
    fills = [fill('AAA', 'Buy', 100, 10, 'a1', '2026-09-09 10:30:00'),
             fill('BBB', 'Buy', 100, 20, 'b1', '2026-09-09 10:00:00'),
             fill('AAA', 'Buy', 200, 12, 'a2', '2026-09-09 14:30:00'),
             fill('AAA', 'Sell', 200, 11, 'a3', '2026-09-10 10:00:00'),
             fill('BBB', 'Sell', 100, 21, 'b2', '2026-09-11 10:00:00')]
    # 100 of AAA's second lot remain; a 100-share board lot on every fill.
    fee = .0016799
    fees = 9700 * fee  # 1,000 + 2,000 + 2,400 + 2,200 + 2,100.
    cash = 10000 - 1100 - fees
    realized = (2200 + 2100) * (1 - fee) - (1000 + 1200 + 2000) * (1 + fee)
    completed = (1100 * (1 - fee) - 1000 * (1 + fee)
                 + 2100 * (1 - fee) - 2000 * (1 + fee))
    report = {'configuration': {'parameters': {'initial_capital_thb': 10000},
                                'days': ['2026-09-09', '2026-09-10', '2026-09-11']},
              'performance': {'final_cash_thb': cash, 'final_nav_thb': cash + 1400,
                              'fees_thb': fees, 'realized_pnl_thb': realized,
                              'expected_payoff_thb': completed / 2,
                              'completed_fifo_round_trips': 2, 'distinct_stocks': 2},
              'daily': [{'holdings': [{'Symbol': 'AAA', 'Actual Volume': 100, 'Market Value': 1400}]}]}
    return fills, report


class AggregateDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = read_json(ROOT / 'docs/result-data-visualisation/phase-3-results.json')

    def test_all_recorded_runs_and_160_days_validate(self):
        result = collect(self.evidence)
        self.assertEqual(len(result['runs']), 10)
        self.assertEqual(sum(len(r['daily']) for r in result['runs'].values()), 160)
        self.assertFalse(result['validation_complete'])
        self.assertTrue(all(r['raw_diagnostics']['status'] == 'unavailable' for r in result['runs'].values()))

    def test_c3_loss_decomposition_and_fee_stress(self):
        result = analyze_run(self.evidence['runs']['C3'])
        s = result['summary']
        self.assertAlmostEqual(s['net_pnl_thb'], -358950.1938965, places=5)
        self.assertAlmostEqual(s['same_fills_fee_added_back_return_pct'], -3.39045, places=7)
        self.assertAlmostEqual(s['traded_notional_thb'], 11849035, places=4)
        self.assertAlmostEqual(s['partial_realization_on_open_lots_thb'], -4946.4769365, places=5)
        self.assertAlmostEqual(result['fixed_fill_fee_stress'][1]['net_return_pct'], -3.6890279084475)
        self.assertAlmostEqual(sum(d['net_pnl_change_thb'] for d in result['daily']), s['net_pnl_thb'])
        self.assertAlmostEqual(sum(d['fees_thb'] for d in result['daily']), s['fees_thb'])
        self.assertEqual(result['largest_loss_days'][0]['date'], '2026-09-30')

    def test_official_and_aligned_excess_keep_different_anchors(self):
        s = analyze_run(self.evidence['runs']['C3'])['summary']
        self.assertGreater(s['official_excess_return_pp'], 0)
        self.assertLess(s['aligned_first_close_excess_pp'], 0)
        self.assertEqual(s['common_status'], 'fail')

    def test_missing_duplicate_out_of_order_or_unreconciled_days_fail(self):
        for kind in ('missing', 'duplicate', 'order', 'unreconciled'):
            run = copy.deepcopy(self.evidence['runs']['C3'])
            if kind == 'missing':
                run['daily'].pop()
            elif kind == 'duplicate':
                run['daily'][1]['date'] = run['daily'][0]['date']
            elif kind == 'order':
                run['daily'].reverse()
            else:
                run['daily'][0]['reconciled'] = False
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                analyze_run(run)

    def test_bad_accounting_payoff_and_eligibility_fail(self):
        for kind in ('pnl', 'fees', 'payoff', 'counts', 'status', 'nan'):
            run = copy.deepcopy(self.evidence['runs']['C3'])
            if kind == 'pnl':
                run['daily'][1]['performance']['realized_pnl_thb'] += 10
            elif kind == 'fees':
                run['daily'][1]['performance']['fees_thb'] = 0
            elif kind == 'payoff':
                run['payoff_detail']['mean_win_thb'] += 10
            elif kind == 'counts':
                run['payoff_detail']['flat_lots'] += 1
            elif kind == 'status':
                run['eligibility']['common_status'] = 'pass'
            else:
                run['daily'][1]['nav'] = float('nan')
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                analyze_run(run)

    def test_different_package_or_capital_cannot_be_pooled(self):
        for field in ('archive_sha256', 'capital'):
            evidence = copy.deepcopy(self.evidence)
            config = evidence['runs']['T5']['configuration']
            if field == 'capital':
                config['parameters']['initial_capital_thb'] *= 2
            else:
                config[field] = 'different'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Non-comparable'):
                collect(evidence)

    def test_cli_outputs_are_deterministic_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / name for name in ('first', 'repeat')]
            for path in paths:
                subprocess.run([sys.executable, str(ROOT / 'scripts/phase4_diagnostics.py'),
                                '--output', str(path)], check=True, capture_output=True)
            for name in ('diagnostics.json', 'summary.csv', 'README.md'):
                self.assertEqual((paths[0] / name).read_bytes(), (paths[1] / name).read_bytes())
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/phase4_diagnostics.py'),
                                     '--output', str(paths[0])], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already exists', result.stderr)


class RawDiagnostics(unittest.TestCase):
    def test_fifo_partial_realization_symbol_pnl_and_session_age(self):
        fills, report = accounting_example()
        result, ledger = analyze_fills(fills, report)
        by_symbol = {s['symbol']: s for s in result['symbols']}
        fee = .0016799
        self.assertAlmostEqual(by_symbol['AAA']['realized_pnl_thb'], -4400 * fee)
        self.assertAlmostEqual(by_symbol['AAA']['unrealized_pnl_thb'], 200 - 1200 * fee)
        self.assertAlmostEqual(by_symbol['BBB']['net_pnl_thb'], 100 - 4100 * fee)
        self.assertEqual([lot['holding_sessions'] for lot in result['completed_lots']], [1, 2])
        self.assertEqual(ledger.quantities(), {'AAA': 100})
        self.assertIsNone(result['intraday_adverse_excursion'])
        self.assertIsNone(result['slippage_attribution'])

    def test_multiple_buy_fills_are_one_lot_and_zero_completions_are_unknown(self):
        fills = [fill('AAA', 'Buy', 100, 10, 'a1', '2026-09-09 10:00:00'),
                 fill('AAA', 'Buy', 100, 12, 'a1', '2026-09-09 10:00:01')]
        fee = 2200 * .0016799
        report = {'configuration': {'parameters': {'initial_capital_thb': 10000}, 'days': ['2026-09-09']},
                  'performance': {'final_cash_thb': 7800 - fee, 'final_nav_thb': 10200 - fee,
                                  'fees_thb': fee, 'realized_pnl_thb': 0, 'expected_payoff_thb': None,
                                  'completed_fifo_round_trips': 0, 'distinct_stocks': 1},
                  'daily': [{'holdings': [{'Symbol': 'AAA', 'Actual Volume': 200, 'Market Value': 2400}]}]}
        result, ledger = analyze_fills(fills, report)
        self.assertEqual(len(ledger.lots['AAA']), 1)
        self.assertIsNone(result['symbols'][0]['expected_payoff_thb'])
        self.assertEqual(result['completed_lots'], [])

    def test_missing_fills_bad_marks_and_out_of_period_timestamps_fail(self):
        for kind in ('missing', 'mark', 'date', 'backwards', 'duplicate_holding'):
            fills, report = accounting_example()
            if kind == 'missing':
                fills.pop()
            elif kind == 'mark':
                report['daily'][-1]['holdings'][0]['Market Value'] += 1
            elif kind == 'date':
                fills[0]['Timestamp'] = '2026-09-08 10:00:00'
            elif kind == 'backwards':
                fills[0]['Timestamp'] = '2026-09-10 10:00:00'
            else:
                report['daily'][-1]['holdings'] *= 2
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                analyze_fills(fills, report)

    def test_raw_bundle_requires_original_hashes_and_fifo_reconciliation(self):
        fills, report = accounting_example()
        _, ledger = analyze_fills(fills, report)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder / 'engine/baseline/baseline_transaction_log.csv'
            path.parent.mkdir(parents=True)
            with path.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(fills[0]))
                writer.writeheader()
                writer.writerows(fills)
            write_json(folder / 'report.json', report)
            fifo = {'completed': ledger.completed, 'open': {'AAA': list(ledger.lots['AAA'])}}
            write_json(folder / 'fifo.json', fifo)
            run = {**report, 'hashes': {name: sha256(folder / name) for name in
                                       ('report.json', 'fifo.json', 'engine/baseline/baseline_transaction_log.csv')}}
            self.assertEqual(analyze_bundle(folder, run)['status'], 'available')
            fifo['completed'][0]['pnl'] += 1
            write_json(folder / 'fifo.json', fifo)
            with self.assertRaisesRegex(ValueError, 'committed hash'):
                analyze_bundle(folder, run)
            run['hashes']['fifo.json'] = sha256(folder / 'fifo.json')
            with self.assertRaisesRegex(ValueError, 'FIFO differs'):
                analyze_bundle(folder, run)


class ResearchDeclaration(unittest.TestCase):
    def test_control_changes_only_exposure_and_is_development(self):
        manifest = declaration()
        self.assertEqual(manifest['sample_role'], 'reused_development')
        self.assertEqual(len(manifest['days']), 16)
        self.assertIsNone(manifest['periods']['validation'])
        self.assertIsNone(manifest['periods']['final_evaluation'])

    def test_source_mutation_is_refused(self):
        manifest = read_json(ROOT / 'research/phase4/manifest.json')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in [*manifest['source_sha256'], 'research/phase4/manifest.json']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            with (root / 'research/phase4/R76.json').open('a') as stream:
                stream.write(' ')
            with self.assertRaisesRegex(ValueError, 'Source changed'):
                declaration(root)


if __name__ == '__main__':
    unittest.main()
