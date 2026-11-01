"""Report diagnostics must preserve accounting and distinguish lots from episodes."""
import copy
from contextlib import chdir
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_phase5_results import fill_diagnostics, clustered_payoff, resolve_run_paths
from phase5_support import write_json
from prepare_phase5_configs import safe_output
from package_support import PACKAGE


def fill(order,side,qty,price,when,symbol='AAA'):
    return {'Order Number':order,'Side':side,'Symbol':symbol,'Volume':qty,'Price':price,
            'Market Price':price-.1 if side=='Buy' else price+.1,'Type':'Market','Timestamp':when}


class Phase5ReportTests(unittest.TestCase):
    def test_fifo_fragmentation_is_not_counted_as_independent_episodes(self):
        fills=[fill('a','Buy',100,10,'2026-09-09 03:05:00'),
               fill('b','Buy',200,10,'2026-09-09 03:20:00'),
               fill('c','Sell',100,11,'2026-09-10 03:05:00'),
               fill('d','Sell',200,11,'2026-09-10 03:20:00')]
        ledger,d=fill_diagnostics(fills,1)
        self.assertEqual(len(ledger.completed),2)
        self.assertEqual(d['position_episodes'],1)
        self.assertEqual(d['still_open_episodes'],0)
        self.assertAlmostEqual(d['episode_details'][0]['net_cash_flow'],ledger.realized)
        self.assertIsNone(d['payoff_cluster_bootstrap']['interval95_thb'][0])

    def test_partial_sale_and_open_episode_are_not_completed(self):
        fills=[fill('a','Buy',300,10,'2026-09-09 03:05:00'),fill('b','Sell',100,11,'2026-09-10 03:05:00')]
        ledger,d=fill_diagnostics(fills,2)
        self.assertEqual(len(ledger.completed),0)
        self.assertEqual(d['position_episodes'],0)
        self.assertEqual(d['still_open_episodes'],1)
        self.assertIsNone(d['fifo']['mean_net'])
        self.assertGreater(ledger.realized,0)
        self.assertAlmostEqual(ledger.fees,(3000+1100)*.00157*1.07*2)

    def test_symbol_cluster_interval_deterministic_and_degenerate_case(self):
        lots=[{'symbol':str(i),'pnl':10} for i in range(6)]
        a=clustered_payoff(lots);b=clustered_payoff(copy.deepcopy(lots))
        self.assertEqual(a,b)
        self.assertEqual(a['interval95_thb'],[10,10])
        self.assertIsNone(clustered_payoff(lots[:4])['interval95_thb'][0])

    def test_empty_fills_are_undefined_payoff(self):
        ledger,d=fill_diagnostics([],1)
        self.assertEqual(ledger.cash,10000000)
        self.assertEqual(d['turnover_over_initial_nav'],0)
        self.assertIsNone(d['fifo']['win_rate'])
        self.assertEqual(d['position_episodes'],0)

    def test_preparation_output_cannot_modify_official_package(self):
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp):
            self.assertEqual(safe_output('relative-output'),Path(tmp)/'relative-output')
        for path in (PACKAGE,PACKAGE/'artifacts/configs'):
            with self.assertRaises(ValueError):
                safe_output(path)

    def test_recovery_requires_exact_preflight_failure_set_and_no_partial_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/'original';recovery=Path(tmp)/'recovery'
            original.mkdir();recovery.mkdir()
            manifest={'experiments':['a','b']}
            write_json(original/'status.json',{'a':{'exit_code':0},'b':{'exit_code':1}})
            write_json(recovery/'status.json',{'b':{'exit_code':0}})
            write_json(recovery/'declaration.json',manifest)
            (original/'b.log').write_text('Official package missing or modified. Run installer.')
            paths,failures=resolve_run_paths(original,recovery,manifest)
            self.assertEqual(paths['a'],original/'a');self.assertEqual(paths['b'],recovery/'b')
            self.assertEqual(failures[0]['initial_exit_code'],1)
            with self.assertRaises(ValueError):
                resolve_run_paths(original,None,manifest)
            (original/'b').mkdir()
            with self.assertRaises(ValueError):
                resolve_run_paths(original,recovery,manifest)

if __name__=='__main__':
    unittest.main()
