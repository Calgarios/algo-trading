"""Causal estimation, full-universe risk controls and official-engine execution."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from package_support import ROOT, PACKAGE, verify_package
from phase5_support import calibrate, distribution, wilson, check_shape, load_strategy
from phase5_reporting import CostLedger
from phase3_reporting import eligibility
verify_package()
sys.path.insert(0,str(PACKAGE))
os.chdir(PACKAGE)
import pandas as pd
from tradeSim.TradeSim import tradeSim
from tradeSim.StrategyHandler import StrategyHandler
from tradeSim.CommissionService import commissionService
from test_strategy_suite import history
Strategy=load_strategy()


class Phase5Mathematics(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(check_shape()['local_structure_checks'],'pass')

    def test_empirical_metrics_hand_calculation(self):
        r=distribution([.03,.01,-.02,0])
        self.assertAlmostEqual(r['mean_net'],.005)
        self.assertAlmostEqual(r['shrunk_mean_net'],.005/6)
        self.assertEqual(r['smoothed_win_rate'],.5)
        self.assertEqual(r['profit_factor'],2)
        self.assertLess(wilson(5,10)[0],.5)
        self.assertGreater(wilson(5,10)[1],.5)
        self.assertIsNone(distribution([])['mean_net'])

    def test_calibration_next_open_costs_nonoverlap_and_strict_causality(self):
        bars=history()
        stats,outcomes=calibrate(bars,'2026-09-09',Strategy)
        self.assertGreater(stats['n'],12)
        byday={b['Date']:b for b in bars}
        first=outcomes[0]
        expected=Strategy.sell_price(byday[first['exit_date']]['Close'],first['exit_date'])*(1-Strategy.FEE_RATE)
        expected/=Strategy.buy_price(byday[first['entry_date']]['Open'],first['entry_date'])*(1+Strategy.FEE_RATE)
        self.assertAlmostEqual(first['net_return'],expected-1)
        for a,b in zip(outcomes,outcomes[1:]):
            self.assertLess(a['exit_date'],b['entry_date'])
        self.assertTrue(all(o['signal_date']<o['entry_date']<=o['exit_date']<'2026-09-09' for o in outcomes))
        for bad in (bars+[{**bars[-1],'Date':'2026-09-09'}],bars+bars[-1:],list(reversed(bars))):
            with self.assertRaises(ValueError):
                calibrate(bad,'2026-09-09',Strategy)

    def test_tick_price_math_matches_engine_at_boundaries(self):
        for day in ('2026-09-09','2026-11-16'):
            for price in (1.99,2,5,10,25,50,100,200,400):
                for side,fun in [('Buy',Strategy.buy_price),('Sell',Strategy.sell_price)]:
                    self.assertAlmostEqual(fun(price,day),commissionService.market_fill_price(price,side,day))

    def test_allocation_respects_sector_position_and_cash_without_forcing_exposure(self):
        raw={f'S{i}':i+1 for i in range(15)}
        sectors={s:'A' if i<10 else 'B' for i,s in enumerate(raw)}
        caps={s:.08 for s in raw}
        weights=Strategy.allocate(raw,caps,sectors,.2,.76)
        self.assertAlmostEqual(sum(weights.values()),.4)
        for s,w in weights.items():
            self.assertLessEqual(w,.08+1e-12)
        self.assertAlmostEqual(sum(w for s,w in weights.items() if sectors[s]=='A'),.2)
        self.assertEqual(weights,Strategy.allocate(dict(reversed(list(raw.items()))),caps,sectors,.2,.76))
        self.assertEqual(Strategy.allocate({}, {}, {}, .2, .76),{})

    def test_equal_allocation_when_caps_inactive(self):
        raw={str(i):1 for i in range(20)}
        w=Strategy.allocate(raw,{s:.08 for s in raw},{s:s for s in raw},.2,.76)
        for value in w.values():
            self.assertAlmostEqual(value,.038)

    def test_missing_and_bad_history_block_signal(self):
        bars=history()
        for bad in (bars[:20],bars+[{**bars[-1],'Date':'2026-09-09'}],bars[:-10],bars+bars[-1:]):
            with self.assertRaises(ValueError):
                Strategy.suite_features(bad,bars,'2026-09-09')

    def test_common_five_is_distinct_from_user_more_than_five(self):
        m={'distinct_stocks':5,'completed_fifo_round_trips':5,'average_exposure':.5,
           'expected_payoff_thb':1,'net_return_pct':0,'excess_return_pp':0,
           'official_max_drawdown_pct':2.999,'benchmark_max_drawdown_pct':2}
        self.assertEqual(eligibility(m)['best_alpha_status'],'pass')
        self.assertFalse(m['completed_fifo_round_trips']>5)
        m['official_max_drawdown_pct']=3
        self.assertEqual(eligibility(m)['common_status'],'fail')


class Phase5Execution(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.sim=tradeSim('baseline',folder=self.tmp.name,current_date='2026-09-09')
        self.config=json.loads((ROOT/'research/phase5/configs/C1-equal.json').read_text())
        self.bars=history()
        # Deterministic signal fixture; never used as return evidence.
        self.config['phase5']['sectors']={s:f'G{i//4}' for i,s in enumerate(self.config['universe'])}
        for q in self.config['phase5']['quality'].values():
            q.update({'n':40,'shrunk_mean_net':.002,'se_net':.003,'last_outcome_date':'2026-09-08'})

    def handler(self):
        with patch.object(StrategyHandler,'load_json',return_value=copy.deepcopy(self.config)),patch.object(
                StrategyHandler,'get_historical_data',return_value=copy.deepcopy(self.bars)):
            return StrategyHandler(Strategy,self.sim.get_strategy_runner(),str(ROOT/'research/phase5/strategy'))

    def tick(self,h,s='AOT',clock='10:05:01',volume=100000,price=None,flag='Sell'):
        price=price or round(self.bars[-1]['Close']*4)/4
        row={'ShareCode':s,'TradeDateTime':pd.Timestamp('2026-09-09 '+clock),'LastPrice':price,
             'Volume':volume,'Value':volume*price,'Flag':flag}
        h.process_row(row);self.sim.update_market_prices({s:price})
        return h.strategy.last_decision

    def test_full_universe_can_trade_more_than_ten(self):
        handlers={s:self.handler() for s in self.config['universe']}
        for s,h in handlers.items():
            self.tick(h,s=s)
        holdings=self.sim.portfolio.get_all_stocks_info()
        self.assertGreater(len(holdings),10)
        nav=self.sim.portfolio.get_nav()
        self.assertLessEqual(sum(h['Market Value'] for h in holdings)/nav,.8)
        self.assertGreaterEqual(self.sim.portfolio.get_cash_balance()/nav,.2)
        self.assertTrue(all(h['Market Value']/nav<=.08 for h in holdings))
        plans=[h.strategy.plan for h in handlers.values()]
        self.assertTrue(all(p==plans[0] for p in plans))

    def test_partial_fill_budget_and_no_duplicate_same_slot(self):
        h=self.handler();a=dict(self.tick(h,volume=100))
        self.assertEqual(a['filled_quantity'],100)
        self.tick(h,clock='10:05:02',volume=100)
        self.assertEqual(h.strategy.decision_sequence,1)
        b=self.tick(h,clock='10:20:01',volume=100)
        self.assertEqual(b['requested_quantity'],a['requested_quantity']-100)
        self.assertEqual(b['filled_quantity'],100)
        self.assertEqual(self.sim.get_open_orders(),[])

    def test_no_opposite_liquidity_does_not_imply_fill(self):
        h=self.handler();d=self.tick(h,flag='Buy')
        self.assertEqual(d['filled_quantity'],0)
        self.assertGreater(d['requested_quantity'],0)

    def test_rejected_order_does_not_invent_a_position(self):
        h=self.handler()
        with patch.object(h,'create_order_at_market',return_value='rejected'):
            d=self.tick(h)
        self.assertEqual(d['filled_quantity'],0)
        self.assertFalse(d['accepted'])
        self.assertEqual(self.sim.portfolio.get_all_stocks_info(),[])

    def test_risk_exit_retries_partial_and_latches_reentry(self):
        h=self.handler();self.tick(h)
        d=self.tick(h,clock='10:20:01',price=80,volume=100,flag='Buy')
        self.assertEqual(d['side'],'Sell');self.assertEqual(d['filled_quantity'],100)
        d=self.tick(h,clock='10:35:01',price=80,flag='Buy')
        self.assertEqual(d['held_after'],0)
        d=self.tick(h,clock='10:50:01')
        self.assertEqual(d['requested_quantity'],0)
        self.assertEqual(h.strategy.exit_reason,'trend_failure')

    def test_guard_recovers_from_current_drawdown_and_invalid_history_liquidates(self):
        h=self.handler()
        self.assertEqual(h.strategy.risk_target(3.1,2)[0],.35)
        self.assertEqual(h.strategy.risk_target(1.8,2)[0],.55)
        self.assertEqual(h.strategy.risk_target(.1,2)[0],.76)
        self.tick(h)
        h2=self.handler();h2.strategy.history['AOT']=[]
        d=self.tick(h2,clock='10:20:01',flag='Buy')
        self.assertEqual(d['side'],'Sell')
        self.assertEqual(d['reason'],'invalid_history_exit')

    def test_fee_stress_ledger_matches_actual_engine(self):
        original=commissionService.comm
        self.addCleanup(setattr,commissionService,'comm',original)
        commissionService.comm=original*2
        self.config['phase5']['fee_multiplier']=2
        h=self.handler();self.tick(h)
        self.tick(h,clock='10:20:01',price=80,flag='Buy')
        ledger=CostLedger(fee_multiplier=2)
        for f in self.sim.execution.tranLog.transaction_log:
            ledger.apply(f)
        self.assertAlmostEqual(ledger.cash,self.sim.portfolio.get_cash_balance())
        self.assertAlmostEqual(ledger.realized,self.sim.portfolio.get_realized())
        self.assertEqual(len(ledger.completed),self.sim.get_strategy_runner().get_round_trip_count())

    def test_quality_weights_use_no_future_calibration(self):
        self.config['phase5']['quality']['AOT']['last_outcome_date']='2026-09-09'
        with self.assertRaises(ValueError):
            self.handler()

if __name__=='__main__':
    unittest.main()
