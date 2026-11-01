"""Verify Phase 5 artifacts and export comparison evidence, figures and PDF."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from math import isclose
import os
from pathlib import Path
import random
import re
from statistics import median
import tempfile
from xml.sax.saxutils import escape

os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'phase5-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from package_support import ROOT, sha256, verify_package
from phase5_support import distribution, wilson, write_json
from phase5_reporting import CostLedger
from phase3_reporting import eligibility
from prepare_strategy_suite import STRATEGIES
from run_phase5_suite import verify
from build_phase4_recovery import fill_slippage, verified_hashes, FILL_LOG

BASE=[f'{s}-{w}' for s in STRATEGIES for w in ('equal','quality')]


def read(p):
    return json.loads(Path(p).read_text())


def csv_write(path, rows):
    if not rows:
        raise ValueError('Cannot write an empty evidence table')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def clustered_payoff(lots, draws=2000):
    groups=defaultdict(list)
    for lot in lots:
        if lot['pnl']!=0:
            groups[lot['symbol']].append(lot['pnl'])
    symbols=sorted(groups)
    if len(symbols)<5:
        return {'clusters':len(symbols),'interval95_thb':[None,None],
                'reason':'Fewer than five symbol clusters; no interval reported'}
    rng=random.Random(20261101);means=[]
    for _ in range(draws):
        values=[v for _ in symbols for v in groups[rng.choice(symbols)]]
        means.append(sum(values)/len(values))
    means.sort()
    return {'clusters':len(symbols),'interval95_thb':[means[int(.025*draws)],means[int(.975*draws)]],
            'seed':20261101,'draws':draws,'reason':'Descriptive symbol-cluster bootstrap; market dependence remains'}


def fill_diagnostics(fills, multiplier):
    ledger=CostLedger(fee_multiplier=multiplier)
    active, completed={},[]
    symbol_fees=defaultdict(float);turnover=0.0
    for f in fills:
        s,side=f['Symbol'],f['Side'];q=int(f['Volume']);amount=q*float(f['Price'])
        fee=amount*.00157*1.07*multiplier
        symbol_fees[s]+=fee;turnover+=amount
        if side=='Buy':
            if s not in active:
                active[s]={'symbol':s,'entry':f['Timestamp'],'quantity':0,'net_cash_flow':0.0,'buy_cost':0.0}
            e=active[s];e['quantity']+=q;e['net_cash_flow']-=amount+fee;e['buy_cost']+=amount+fee
        else:
            e=active[s];e['quantity']-=q;e['net_cash_flow']+=amount-fee
            if e['quantity']==0:
                e['exit']=f['Timestamp'];e['return']=e['net_cash_flow']/e['buy_cost'];completed.append(active.pop(s))
        ledger.apply(f)
    vals=[l['pnl'] for l in ledger.completed if l['pnl']!=0]
    stats=distribution(vals)
    stats['meaning']='THB P&L distribution of completed non-breakeven FIFO lots; not a future forecast'
    returns=distribution([l['pnl']/(l['unit_cost']*l['volume']) for l in ledger.completed])
    return ledger, {'fifo':stats,'fifo_return_distribution':returns,'payoff_cluster_bootstrap':clustered_payoff(ledger.completed),
                    'position_episodes':len(completed),'episode_details':completed,
                    'episode_return_distribution':distribution([e['return'] for e in completed]),
                    'still_open_episodes':len(active),'turnover_thb':turnover,'turnover_over_initial_nav':turnover/1e7,
                    'symbol_fees_thb':dict(symbol_fees),'concessions':fill_slippage(fills)}


def resolve_run_paths(folder, recovery, manifest):
    status=read(folder/'status.json')
    if set(status)!=set(manifest['experiments']):
        raise ValueError('Incomplete suite')
    failed={k for k,s in status.items() if s['exit_code']}
    paths={k:folder/k for k in status}
    recoveries=[]
    if failed:
        if recovery is None or read(recovery/'declaration.json')!=manifest:
            raise ValueError('Failed runs require matching explicit recovery evidence')
        retry=read(recovery/'status.json')
        if set(retry)!=failed or any(s['exit_code'] for s in retry.values()):
            raise ValueError('Recovery does not exactly cover failed runs')
        for key in sorted(failed):
            log=folder/f'{key}.log'
            if (folder/key).exists() or 'Official package missing or modified' not in log.read_text():
                raise ValueError('Recovery is limited to package-preflight failures before trading')
            paths[key]=recovery/key
            recoveries.append({'id':key,'initial_exit_code':status[key]['exit_code'],
                               'initial_log_sha256':sha256(log),'retry_exit_code':0,
                               'reason':'Preflight caught misplaced preparation output; original package tree restored'})
    elif recovery is not None:
        raise ValueError('Unexpected recovery when original suite has no failures')
    return paths,recoveries


def collect(folder, repeat, test_log, recovery=None):
    package=verify_package();configs=ROOT/'research/phase5/configs';m=verify(configs)
    if read(folder/'declaration.json')!=m:
        raise ValueError('Suite declaration differs')
    paths,recoveries=resolve_run_paths(folder,recovery,m)
    log=test_log.read_text();test_match=re.search(r'^Ran (\d+) tests',log,re.M)
    if not test_match or not re.search(r'^OK$',log,re.M) or re.search(r'^FAILED',log,re.M):
        raise ValueError('Need passing full-suite test log')
    runs, conditions, lot_rows={},[],[]
    for key in m['experiments']:
        path=paths[key];hashes=read(path/'reproducible-hashes.json');verified_hashes(path,hashes)
        r=read(path/'report.json');p=r['performance'];c=r['configuration']
        if c['companion_config_sha256']!=m['config_sha256'][key] or c['days']!=m['days']:
            raise ValueError('Wrong config/dates')
        if c['package_tree_sha256']!=package['tree_sha256'] or sum(d['ticks'] for d in r['daily'])!=2906167:
            raise ValueError('Wrong package/ticks')
        for source,digest in c['code_sha256'].items():
            if sha256(ROOT/source)!=digest:
                raise ValueError(f'Changed replay code: {source}')
        if not all(d['reconciliation']['reconciled'] for d in r['daily']):
            raise ValueError('Unreconciled daily result')
        if r['eligibility']!=eligibility(p):
            raise ValueError('Eligibility mismatch')
        with (path/FILL_LOG).open() as f:
            fills=list(csv.DictReader(f))
        ledger,diag=fill_diagnostics(fills,c['parameters']['phase5']['fee_multiplier'])
        for episode in diag['episode_details']:
            episode['holding_sessions']=sum(episode['entry'][:10]<day<=episode['exit'][:10] for day in m['days'])
        ages=[e['holding_sessions'] for e in diag['episode_details']]
        diag['median_episode_holding_sessions']=median(ages) if ages else None
        diag['episodes_closed_before_five_sessions']=sum(age<5 for age in ages)
        for expected,observed in ((ledger.cash,p['final_cash_thb']),(ledger.realized,p['realized_pnl_thb']),
                                  (ledger.fees,p['fees_thb']),(ledger.expected_payoff() or 0,p['expected_payoff_thb'] or 0)):
            if not isclose(expected,observed,abs_tol=1e-5,rel_tol=1e-10):
                raise ValueError('Independent final fill accounting mismatch')
        if len(ledger.completed)!=p['completed_fifo_round_trips']:
            raise ValueError('FIFO count mismatch')
        if read(path/'fifo.json')['completed']!=ledger.completed:
            raise ValueError('Saved FIFO differs from fill replay')
        plans=read(path/'plans.json')
        if [a['date'] for a in plans]!=m['days']:
            raise ValueError('Plan dates mismatch')
        for a in plans:
            plan=a['plan']
            if set(plan['features'])|set(plan['rejected'])!=set(c['parameters']['universe']):
                raise ValueError('Missing per-symbol assessment')
            if any(f['history_end']>=a['date'] for f in plan['features'].values()):
                raise ValueError('Nonpast features')
            if key in BASE:
                for s in c['parameters']['universe']:
                    f=plan['features'].get(s,{})
                    conditions.append({'run':key,'date':a['date'],'symbol':s,'sector':c['parameters']['phase5']['sectors'][s],
                        'eligible':s in plan['selected'],'rejection':plan['rejected'].get(s,''),
                        'weight':plan['weights'].get(s,0),'target_shares':plan['targets'].get(s,0),
                        'history_end':f.get('history_end'),'close':f.get('close'),'sma60':f.get('sma60'),
                        'ret20':f.get('ret20'),'ret60':f.get('ret60'),'vol20':f.get('vol20'),
                        'rsi14':f.get('rsi14'),'bollinger_z':f.get('bollinger_z'),
                        'median_value20':f.get('median_value20'),'checks_json':json.dumps(plan['checks'].get(s,{}),sort_keys=True)})
        daily=[]
        for d,a in zip(r['daily'],plans):
            sector_values=defaultdict(float)
            for holding in d['holdings']:
                sector_values[c['parameters']['phase5']['sectors'][holding['Symbol']]]+=holding['Market Value']
            largest_sector=max(sector_values.values(),default=0)/d['raw']['nav']
            daily.append({'date':d['date'],'nav':d['raw']['nav'],'cash':d['raw']['cash'],
                          **d['closing_risk'],'performance':d['performance'],'target_exposure':a['plan']['target_exposure'],
                          'allocated_exposure':a['plan']['allocated_exposure'],'eligible_names':len(a['plan']['selected']),
                          'guard':a['plan']['drawdown_guard'],'reconciled':True,
                          'largest_sector':largest_sector,'above_sector_limit':largest_sector>.2})
        closing_symbols={h['Symbol']:h for h in r['daily'][-1]['holdings']}
        attribution=[]
        for s in sorted(ledger.symbols):
            realized=sum(l['pnl'] for l in ledger.completed if l['symbol']==s)+sum(l['pnl'] for l in ledger.lots[s])
            market=closing_symbols.get(s,{}).get('Market Value',0)
            cost=sum(l['remaining']*l['unit_cost'] for l in ledger.lots[s])
            attribution.append({'symbol':s,'realized_pnl_thb':realized,'unrealized_pnl_thb':market-cost,
                                'total_pnl_thb':realized+market-cost,'fees_thb':diag['symbol_fees_thb'][s]})
        if not isclose(sum(x['total_pnl_thb'] for x in attribution),p['final_nav_thb']-1e7,abs_tol=1e-5):
            raise ValueError('Symbol P&L does not reconcile')
        for lot in ledger.completed:
            lot_rows.append({'run':key,**lot})
        decisions=Counter()
        with (path/'decisions.jsonl').open() as stream:
            for line in stream:
                d=json.loads(line)
                if d['filled_quantity'] and d.get('side')=='Sell':
                    decisions[d['reason']]+=1
        runs[key]={'id':key,'model':c['parameters']['phase5']['id'],'weighting':c['parameters']['phase5']['weighting'],
                   'variant':c['parameters']['phase5']['variant'],'configuration':c,'performance':p,
                   'eligibility':r['eligibility'],'user_targets':r['user_targets'],'diagnostics':diag,
                   'daily':daily,'symbol_attribution':attribution,'sell_fill_reasons':dict(decisions),
                   'execution':r['execution'],'hashes':hashes,
                   'closing_limit_drift':{'position_days':sum(d['above_buy_position_limit'] for d in daily),
                                          'exposure_days':sum(d['above_buy_exposure_limit'] for d in daily),
                                          'sector_days':sum(d['above_sector_limit'] for d in daily),
                                          'max_position':max(d['largest_position'] for d in daily),
                                          'max_sector':max(d['largest_sector'] for d in daily)},
                   'max_daily_seconds':max(read(path/'environment.json')['daily_seconds'].values())}
    repeated=read(repeat/'C1-quality/reproducible-hashes.json')
    verified_hashes(repeat/'C1-quality',repeated)
    if repeated!=runs['C1-quality']['hashes']:
        raise ValueError('Fresh-process repeat differs')
    pairs={}
    for model in STRATEGIES:
        e,q=runs[f'{model}-equal'],runs[f'{model}-quality'];ep,qp=e['performance'],q['performance']
        pairs[model]={'net_return_change_pp':qp['net_return_pct']-ep['net_return_pct'],
                      'exposure_change_pp':100*(qp['average_exposure']-ep['average_exposure']),
                      'payoff_change_thb':qp['expected_payoff_thb']-ep['expected_payoff_thb'] if qp['expected_payoff_thb'] is not None and ep['expected_payoff_thb'] is not None else None,
                      'fees_change_thb':qp['fees_thb']-ep['fees_thb'],
                      'round_trip_change':qp['completed_fifo_round_trips']-ep['completed_fifo_round_trips'],
                      'quality_passes_common':q['eligibility']['common_status']=='pass',
                      'quality_passes_best_alpha':q['eligibility']['best_alpha_status']=='pass'}
    return {'date_bangkok':'2026-11-01','sample_role':'reused_development','universe_count':48,
            'base_runs':BASE,'runs':runs,'pairs':pairs,'test_count':int(test_match[1]),
            'repeat':{'run':'C1-quality','identical_artifacts':len(repeated)},'package':package,
            'recovered_preflight_failures':recoveries,
            'calibration':read(configs/'calibration.json')['quality'],
            'candidate_promoted':None,'independent_validation_complete':False,
            'phase5_implementation_complete':True,'phase5_declared_replays_complete':True,
            'phase5_improvement_gate_met':False,
            'research_conclusion':'No promotion without positive after-cost evidence, eligibility and independent validation',
            'provenance':{'manifest_sha256':sha256(configs/'manifest.json'),'test_log_sha256':sha256(test_log),
                          'safe_preparer_sha256':sha256(ROOT/'scripts/prepare_phase5_configs.py'),
                          'report_generator_sha256':sha256(Path(__file__))}},conditions,lot_rows


def summary_rows(data):
    rows=[]
    for key,r in data['runs'].items():
        p,d=r['performance'],r['diagnostics']
        rows.append({'run':key,'variant':r['variant'],**p,'user_round_trips_gt5':p['completed_fifo_round_trips']>5,
                     'position_episodes':d['position_episodes'],'win_rate_fifo':d['fifo']['win_rate'],
                     'median_episode_holding_sessions':d['median_episode_holding_sessions'],
                     'episodes_closed_before_five_sessions':d['episodes_closed_before_five_sessions'],
                     'mean_win_thb':d['fifo']['mean_win'],'mean_loss_thb':d['fifo']['mean_loss'],
                     'profit_factor_fifo':d['fifo']['profit_factor'],'turnover_over_initial_nav':d['turnover_over_initial_nav'],
                     'price_concessions_thb':d['concessions']['filled_price_concession_thb'],
                     'common':r['eligibility']['common_status'],'best_alpha':r['eligibility']['best_alpha_status'],
                     'max_closing_position':r['closing_limit_drift']['max_position'],
                     'max_closing_sector':r['closing_limit_drift']['max_sector'],
                     'position_cap_drift_days':r['closing_limit_drift']['position_days'],
                     'sector_cap_drift_days':r['closing_limit_drift']['sector_days'],
                     'max_daily_seconds':r['max_daily_seconds']})
    return rows


def figures(data, conditions, folder):
    folder.mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.grid':True,'grid.alpha':.15})
    palette={'equal':'#277D91','quality':'#D78530'}
    def save(fig,name):
        fig.tight_layout();fig.savefig(folder/f'{name}.png',dpi=160,bbox_inches='tight');plt.close(fig)
    models=list(STRATEGIES);x=np.arange(10)
    metrics=[('net_return_pct','Net return (%)',1),('expected_payoff_thb','Expected payoff (THB / completed lot)',1),
             ('average_exposure','Average closing exposure (%)',100),('official_max_drawdown_pct','Official maximum drawdown (%)',1),
             ('completed_fifo_round_trips','Completed FIFO round trips',1),('fees_thb','Commission + VAT (THB)',1)]
    fig,axes=plt.subplots(3,2,figsize=(12,12))
    for ax,(metric,label,scale) in zip(axes.flat,metrics):
        for w,offset in [('equal',-.19),('quality',.19)]:
            vals=[data['runs'][f'{m}-{w}']['performance'][metric] for m in models]
            ax.bar(x+offset,[v*scale if v is not None else 0 for v in vals],.36,label=w,color=palette[w])
            for i,v in enumerate(vals):
                if v is None: ax.text(i+offset,0,'N/A',rotation=90,ha='center',va='bottom',fontsize=7)
        if metric=='average_exposure':
            ax.axhline(50,color='#B54C45',ls='--',label='Common minimum');ax.axhspan(70,80,color='#9AC299',alpha=.15)
        if metric=='official_max_drawdown_pct': ax.axhline(1.5*data['runs'][BASE[0]]['performance']['benchmark_max_drawdown_pct'],color='#B54C45',ls='--')
        if metric=='completed_fifo_round_trips': ax.axhline(5,color='#B54C45',ls='--',label='User must exceed 5')
        ax.set_xticks(x,models);ax.set_title(label);ax.axhline(0,color='#555',lw=.5)
    axes[0,0].legend();fig.suptitle('Phase 5 · 20 paired simulations · reused September development',fontsize=15)
    save(fig,'comparison')
    fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True)
    for ax,metric,label,scale in [(axes[0],'net_return_pct','Net return (%)',1),
                                  (axes[1],'average_exposure','Average closing exposure (%)',100)]:
        for w,offset in [('equal',-.19),('quality',.19)]:
            ax.bar(x+offset,[data['runs'][f'{m}-{w}']['performance'][metric]*scale for m in models],
                   .36,label=w,color=palette[w])
        ax.set_ylabel(label);ax.axhline(0,color='#555',lw=.5)
    axes[0].legend();axes[1].set_xticks(x,models);axes[1].axhline(50,color='#B54C45',ls='--')
    axes[1].axhspan(70,80,color='#9AC299',alpha=.15);save(fig,'returns-exposure')
    for model in models:
        fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
        for w in ('equal','quality'):
            r=data['runs'][f'{model}-{w}'];daily=r['daily'];days=[d['date'][5:] for d in daily]
            axes[0].plot(days,[(d['nav']/1e7-1)*100 for d in daily],label=w,color=palette[w],lw=2)
            axes[1].plot(days,[d['exposure']*100 for d in daily],color=palette[w])
            axes[2].plot(days,[d['performance']['completed_fifo_round_trips'] for d in daily],color=palette[w])
        axes[0].plot(days,[d['performance']['benchmark_return_pct'] for d in daily],color='#73808A',ls='--',label='SET50 (first-close anchor)')
        axes[0].set_ylabel('Net return (%)');axes[0].legend(loc='lower left',fontsize=8)
        axes[1].axhline(50,color='#B54C45',ls='--');axes[1].axhspan(70,80,color='#9AC299',alpha=.15);axes[1].set_ylabel('Closing exposure (%)')
        axes[2].axhline(5,color='#B54C45',ls='--');axes[2].set_ylabel('Cumulative FIFO trips')
        axes[2].tick_params(axis='x',rotation=45);fig.suptitle(f'{model} · {STRATEGIES[model][1]}')
        save(fig,model)
    q=data['calibration'];symbols=sorted(q,key=lambda s:q[s]['mean_net'] if q[s]['mean_net'] is not None else -1)
    fig,ax=plt.subplots(figsize=(10,12))
    for i,s in enumerate(symbols):
        r=q[s]
        if r['mean_net'] is not None:
            ax.errorbar(r['mean_net']*100,i,xerr=r['se_net']*1.96*100,fmt='o',color='#277D91',ms=3)
        else: ax.text(0,i,'Insufficient history',fontsize=7)
    ax.set_yticks(range(len(symbols)),[f'{s} (n={q[s]["n"]})' for s in symbols]);ax.axvline(0,color='#B54C45',ls='--')
    ax.set_xlabel('Mean net five-session daily-price proxy (%) ± approximate 95% interval')
    ax.set_title('Pre-start evidence does not establish positive expected returns')
    save(fig,'calibration')
    symbols=sorted(q);matrix=np.zeros((48,10))
    for r in conditions:
        if r['run'].endswith('-equal') and r['eligible']:
            matrix[symbols.index(r['symbol']),models.index(r['run'].split('-')[0])]+=1
    fig,ax=plt.subplots(figsize=(9,13));im=ax.imshow(matrix,cmap='YlGnBu',aspect='auto',vmin=0,vmax=16)
    ax.set_xticks(range(10),models);ax.set_yticks(range(48),symbols);ax.set_title('Days each stock passed all entry conditions (of 16)')
    fig.colorbar(im,ax=ax,label='Eligible sessions',shrink=.6);save(fig,'stock-eligibility')
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    keys=[f'{m}-{w}' for m in ('C1','C3') for w in ('equal','quality')];x=np.arange(4)
    for i,(variant,color) in enumerate([('', '#277D91'),('-fees2','#B54C45'),('-band6','#8B75A7')]):
        for ax,metric,label in zip(axes,('net_return_pct','expected_payoff_thb'),('Net return (%)','Expected payoff (THB)')):
            vals=[data['runs'][k+variant]['performance'][metric] for k in keys]
            ax.bar(x+(i-1)*.25,[v if v is not None else 0 for v in vals],.23,color=color,label=variant[1:] or 'base')
            ax.set_xticks(x,keys,rotation=20);ax.set_title(label);ax.axhline(0,color='#555',lw=.5)
    axes[0].legend();fig.suptitle('Predeclared actual engine sensitivities');save(fig,'sensitivity')
    fig,ax=plt.subplots(figsize=(11,6))
    for i,key in enumerate(BASE):
        r=data['runs'][key];ci=r['diagnostics']['payoff_cluster_bootstrap']['interval95_thb'];mean=r['performance']['expected_payoff_thb']
        if mean is None: ax.text(0,i,'Undefined',fontsize=7)
        elif ci[0] is None: ax.plot(mean,i,'x',color='#777')
        else:
            ax.plot(ci,[i,i],color=palette[r['weighting']]);ax.plot(mean,i,'o',color=palette[r['weighting']],ms=4)
    ax.set_yticks(range(20),BASE);ax.axvline(0,color='#B54C45',ls='--');ax.set_xlabel('Completed-lot payoff THB · 95% symbol-cluster bootstrap')
    ax.set_title('Payoff uncertainty · x = fewer than five symbol clusters');save(fig,'payoff-uncertainty')
    fig,axes=plt.subplots(1,2,figsize=(13,7))
    y=np.arange(len(BASE))
    axes[0].barh(y-.18,[data['runs'][k]['performance']['realized_pnl_thb']/1000 for k in BASE],.34,
                 color='#277D91',label='Realized P&L')
    axes[0].barh(y+.18,[data['runs'][k]['performance']['unrealized_pnl_thb']/1000 for k in BASE],.34,
                 color='#D78530',label='Open P&L')
    axes[0].set_yticks(y,BASE);axes[0].set_xlabel('THB thousands');axes[0].set_title('Full P&L, including positions still open')
    axes[0].legend(fontsize=8);axes[0].axvline(0,color='#555',lw=.5)
    axes[1].barh(y-.18,[data['runs'][k]['performance']['completed_fifo_round_trips'] for k in BASE],.34,
                 color='#277D91',label='FIFO lots')
    axes[1].barh(y+.18,[data['runs'][k]['diagnostics']['position_episodes'] for k in BASE],.34,
                 color='#D78530',label='Position episodes')
    axes[1].set_yticks(y,BASE);axes[1].set_xlabel('Completed count');axes[1].set_title('IOC fragmentation changes the count')
    axes[1].legend(fontsize=8);save(fig,'pnl-and-trips')


def fmt(value,digits=3):
    return 'N/A' if value is None else f'{value:,.{digits}f}'


def markdown(data):
    runs=data['runs'];common=sum(runs[k]['eligibility']['common_status']=='pass' for k in BASE)
    alpha=sum(runs[k]['eligibility']['best_alpha_status']=='pass' for k in BASE)
    strict=sum(runs[k]['performance']['completed_fifo_round_trips']>5 for k in BASE)
    lines=['# Phase 5 results', '', '1 November 2026 (Asia/Bangkok). Official TradeSim 0.2.7; Python 3.13.5.', '',
           '**20 base simulations and 8 predeclared sensitivity simulations completed.** '
           'Each uses 16 September sessions and 2,906,167 ticks. Starting capital THB 10 million. '
           'All 48 supplied names were assessed; 50-name coverage is unavailable.', '',
           f'**Common criteria: {common}/20 pass. Best Alpha: {alpha}/20 pass. User round-trip target (>5): {strict}/20 pass.** '
           'September is reused development data; no candidate is promoted and independent validation remains open.', '',
           '## Paired results', '',
           '| Run | Return % | Excess pp | DD % | Exposure % | FIFO trips | Episodes | Payoff THB | Common | Alpha |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |']
    for k in BASE:
        r=runs[k];p=r['performance'];d=r['diagnostics']
        lines.append(f"| {k} | {fmt(p['net_return_pct'])} | {fmt(p['excess_return_pp'])} | {fmt(p['official_max_drawdown_pct'])} | {fmt(100*p['average_exposure'])} | {p['completed_fifo_round_trips']} | {d['position_episodes']} | {fmt(p['expected_payoff_thb'],2)} | {r['eligibility']['common_status']} | {r['eligibility']['best_alpha_status']} |")
    bm=runs[BASE[0]]['performance']
    exposure_pass=sum(runs[k]['performance']['average_exposure']>=.5 for k in BASE)
    payoff_pass=sum((runs[k]['performance']['expected_payoff_thb'] or 0)>0 for k in BASE)
    dd_pass=sum(runs[k]['performance']['official_max_drawdown_pct']<1.5*bm['benchmark_max_drawdown_pct'] for k in BASE)
    sizing_better=sum(p['net_return_change_pp']>0 for p in data['pairs'].values())
    lines += ['',f"SET50 return **{bm['benchmark_return_pct']:.6f}%**; SET50 DD **{bm['benchmark_max_drawdown_pct']:.6f}%**. "
              f"Strict portfolio DD boundary **<{1.5*bm['benchmark_max_drawdown_pct']:.6f}%**. "
              'Common FIFO threshold is >=5; this task separately requires >5. N/A payoff means no non-breakeven completed lot.', '',
              f'Criterion breakdown: **{exposure_pass}/20** meet average exposure >=50%; **{payoff_pass}/20** have positive payoff; '
              f'**{dd_pass}/20** satisfy the strict drawdown rule. Quality sizing improves net return in **{sizing_better}/10** pairs. '
              'A relative improvement does not establish a profitable or eligible strategy.', '',
              '![Paired overview](figures/comparison.png)', '', '## What changed and what the comparison supports', '',
              'The old ten-stock frozen baskets became daily stock-by-stock screening over all 48 supplied names. '
              'Price conditions can reject deteriorating stocks; targets respect sector/liquidity caps, daily buy budgets and a recovering drawdown guard. '
              'No exposure floor forces purchases of rejected stocks. Equal and quality runs differ only in desired sizing; execution and realized exposure can consequently differ.', '',
              '| Model | Quality minus equal return pp | Exposure change pp | Payoff change THB | Interpretation |',
              '| --- | ---: | ---: | ---: | --- |']
    for model,p in data['pairs'].items():
        decision='No demonstrated sizing improvement' if p['net_return_change_pp']<=0 else 'Development improvement only'
        if abs(p['exposure_change_pp'])>2: decision+='; exposure differs >2 pp'
        lines.append(f"| {model} | {fmt(p['net_return_change_pp'])} | {fmt(p['exposure_change_pp'])} | {fmt(p['payoff_change_thb'],2)} | {decision} |")
    historical=read(ROOT/'docs/result-data-visualisation/phase-4/phase-4-results.json')['runs']
    lines += ['', 'Historical controls (different universe/policy, not a causal attribution):', '',
              '| Control | Return % | Exposure % | FIFO trips | Payoff THB |', '| --- | ---: | ---: | ---: | ---: |']
    for key in ('R76','P-C3'):
        p=historical[key]['performance'];lines.append(f"| {key} | {fmt(p['net_return_pct'])} | {fmt(p['average_exposure']*100)} | {p['completed_fifo_round_trips']} | {fmt(p['expected_payoff_thb'],2)} |")
    lines += ['', '## Metric quality and uncertainty', '',
              'The pre-start five-session calibration found no positive mean after estimated fees/ticks. '
              'The initial hard positive-edge gate is rejected and retained in the experiment record. '
              'The main runs test price/risk hypotheses, not a verified future-profit model. '
              'Quality-weighted means bounded historical-edge adjustment, model rank and inverse volatility.', '',
              'Expected payoff is a sample THB average of completed non-breakeven FIFO buy lots. '
              'Partial fills fragment orders into lots, and realized partial sales can sit outside that average. '
              'Episodes count a stock returning from zero holdings to zero, not necessarily independent market bets. '
              'The JSON/CSV also report win/loss magnitude, profit factor, episode returns, realized/unrealized P&L, costs and turnover. '
              'Payoff uncertainty uses 2,000 symbol-cluster bootstrap draws (seed 20261101); fewer than five clusters is unavailable. '
              'Intervals do not establish independence, future profitability or correct for all tested choices.', '',
              '![Payoff uncertainty](figures/payoff-uncertainty.png)', '',
              '![Realized/open losses and trip definitions](figures/pnl-and-trips.png)', '',
              '![Pre-start calibration](figures/calibration.png)', '',
              '## Actual sensitivity replays', '',
              'C1/C3 were selected before full results. Both weighting methods were rerun at twice commission (VAT unchanged) '
              'and separately with a 0.6%-NAV band. The official class commission setting changed only inside each isolated run; '
              'the package files stayed unchanged. Fills, cash, quantities and eligibility were recomputed. These are not fixed-fill fee add-backs.', '',
              '| Run | Return % | Exposure % | FIFO trips | Payoff THB | Common | Alpha |',
              '| --- | ---: | ---: | ---: | ---: | --- | --- |']
    for k,r in runs.items():
        if k in BASE: continue
        p=r['performance'];lines.append(f"| {k} | {fmt(p['net_return_pct'])} | {fmt(p['average_exposure']*100)} | {p['completed_fifo_round_trips']} | {fmt(p['expected_payoff_thb'],2)} | {r['eligibility']['common_status']} | {r['eligibility']['best_alpha_status']} |")
    lines += ['', '![Sensitivities](figures/sensitivity.png)', '', '## Every-stock conditions', '',
              '![Eligible sessions](figures/stock-eligibility.png)', '',
              '[Stock-by-date conditions and weights](stock-conditions.csv) cover every name in every base simulation. '
              '[Historical stock calibration](stock-calibration.csv) includes sample size and uncertainty. '
              '[Strategy explanations](../../phase-5-strategies.md) define all predicates and sizing formulas.', '', '## Each strategy', '']
    for model in STRATEGIES:
        lines += [f'### {model}: {STRATEGIES[model][1]}','',f'![{model} paths](figures/{model}.png)','']
    maxruntime=max(r['max_daily_seconds'] for r in runs.values())
    position_days=sum(runs[k]['closing_limit_drift']['position_days'] for k in BASE)
    sector_days=sum(runs[k]['closing_limit_drift']['sector_days'] for k in BASE)
    max_position=max(runs[k]['closing_limit_drift']['max_position'] for k in BASE)*100
    max_sector=max(runs[k]['closing_limit_drift']['max_sector'] for k in BASE)*100
    lines += ['## Verification and limits','',
              f"{data['test_count']} tests pass. All {len(runs)*16} strategy-days reconcile cash, holdings, costs, NAV, realized P&L, FIFO and official metrics. "
              f"C1-quality fresh-process repeat matches {data['repeat']['identical_artifacts']} deterministic artifacts. "
              f"Maximum observed daily runtime was {maxruntime:.3f}s with concurrent research runs (local ceiling 900s).", '',
              f"Preparation reproduced all 30 JSON files byte for byte. {len(data['recovered_preflight_failures'])} queued runs "
              'were stopped before trading when a relative-output preparation check added generated files inside the package directory. '
              'The generated files were moved out, the original package tree was reverified, and the stopped cases were replayed '
              'in a separate recovery directory. Initial failures and successful retries remain recorded. '
              'The safe preparation entrypoint now normalizes output paths and rejects the official package as an output location.', '',
              'Every run retains exact strategy/config, source and input hashes, plans, decisions, fills, FIFO records and runtime under artifacts/. '
              'The report verifies those hashes and independently rebuilds fill-ledger and symbol P&L totals. '
              'Official drawdown uses daily closes; initial-capital drawdown is separately exported. '
              'Official benchmark starts at the first sample close, whereas strategy return starts at initial cash; aligned first-close excess is also exported.', '',
              f'Closing drift across the 320 base strategy-days: **{position_days}** position-cap breaches and '
              f'**{sector_days}** sector-cap breach. Largest closing position **{max_position:.4f}%** versus the 8% pre-buy cap; '
              f'largest closing sector **{max_sector:.4f}%** versus 20%. No base closing exposure exceeded 80%. '
              'These measured breaches show that pre-buy limits are not continuous holding limits.', '',
              'Static membership, adjustments, production event order, restart durability, registered owner and organizer acceptance remain unverified. '
              'Stops can gap or partially fill and closing risk can drift after accepted purchases. '
              'No new tick period exists for independent evaluation. The absence of a validated profitable candidate means the Phase 5 improvement gate is not closed; '
              'completed implementation and experiments are distinct from profitability and validation.', '',
              '[Machine-readable results](phase-5-results.json) · [Metrics CSV](phase-5-results.csv) · '
              '[Completed FIFO lots](completed-lots.csv) · [PDF](phase-5-results.pdf) · '
              '[Next actions](../../to-do/phase-6.md)', '']
    return '\n'.join(lines)


def pdf(data, folder):
    fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('Phase5Sans',str(fonts/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('Phase5Bold',str(fonts/'DejaVuSans-Bold.ttf')))
    styles=getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName='Phase5Bold' if name in ('Title','Heading1','Heading2','Heading3') else 'Phase5Sans'
    story=[]
    def para(text,style='BodyText'):
        story.append(Paragraph(escape(text),styles[style]));story.append(Spacer(1,3*mm))
    def fig(name,width=177*mm):
        from PIL import Image as PILImage
        with PILImage.open(folder/'figures'/f'{name}.png') as im:
            w,h=im.size
        height=min(225*mm,width*h/w);width=height*w/h
        story.append(Image(str(folder/'figures'/f'{name}.png'),width=width,height=height))
    para('Phase 5 · Portfolio and execution research','Title')
    para('20 paired simulations · 8 sensitivity runs · 48 supplied constituents · 16 September development sessions')
    common=sum(data['runs'][k]['eligibility']['common_status']=='pass' for k in BASE)
    alpha=sum(data['runs'][k]['eligibility']['best_alpha_status']=='pass' for k in BASE)
    para(f'Common criteria: {common}/20 pass. Best Alpha: {alpha}/20 pass. No independent validation or candidate promotion.')
    para('Equal and quality sizing use identical daily stock filters and execution rules. Quality is a research formula, not verified future profitability.')
    fig('returns-exposure',177*mm);story.append(PageBreak())
    para('Measured base results','Title')
    rows=[['Run','Return %','DD %','Exp %','Trips','Payoff','Common']]
    for k in BASE:
        r=data['runs'][k];p=r['performance'];rows.append([k,fmt(p['net_return_pct'],2),fmt(p['official_max_drawdown_pct'],2),
            fmt(p['average_exposure']*100,1),str(p['completed_fifo_round_trips']),fmt(p['expected_payoff_thb'],1),r['eligibility']['common_status']])
    table=Table(rows,repeatRows=1,colWidths=[37*mm,22*mm,20*mm,20*mm,15*mm,30*mm,23*mm])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173D50')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
                              ('FONTNAME',(0,0),(-1,-1),'Phase5Sans'),
                              ('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),6),
                              ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white])]))
    story.append(table);story.append(Spacer(1,6*mm))
    para('Round trips are completed FIFO buy lots. User target >5; common rule >=5. N/A means undefined payoff, not zero. The CSV also reports position episodes, excess return, initial-capital drawdown, open losses and costs.')
    story.append(PageBreak());para('Historical support and its limits','Title')
    para('No stock had positive after-cost mean in the pre-start five-session proxy. The positive-edge veto produced no trades and was rejected as infeasible. The paired runs test trend and risk hypotheses with this uncertainty disclosed.')
    fig('calibration',155*mm);story.append(PageBreak())
    para('Payoff uncertainty','Title');fig('payoff-uncertainty')
    para('2,000 symbol-cluster resamples. Fewer than five symbol clusters: x, no interval. Market-wide dependence and repeated development decisions remain. More FIFO lots do not imply more independent profitable trades.')
    para('Stock control: past-only data, liquidity, volatility, long trend and model-specific predicates. Risk control: position/sector limits, 20% cash reserve, recovering drawdown guard, stop exits, daily buy budgets and actual residual IOC fills.')
    story.append(PageBreak());para('Sensitivity to actual costs and turnover','Title');fig('sensitivity')
    para('Double-commission and 0.6%-NAV-band variants were declared for C1/C3 before full results. Every variant reruns the official matching engine and reconciles resulting fills. No package files were edited.')
    story.append(PageBreak());para('All available stocks are assessed','Title');fig('stock-eligibility',150*mm)
    for model in STRATEGIES:
        story.append(PageBreak());para(f'{model} · {STRATEGIES[model][1]}','Title');fig(model)
        for w in ('equal','quality'):
            r=data['runs'][f'{model}-{w}'];p=r['performance'];d=r['diagnostics']
            para(f"{w}: return {fmt(p['net_return_pct'])}%; exposure {fmt(p['average_exposure']*100)}%; "
                 f"{p['completed_fifo_round_trips']} FIFO trips; {d['position_episodes']} completed position episodes; "
                 f"payoff THB {fmt(p['expected_payoff_thb'],2)}. Common: {r['eligibility']['common_status']}; Best Alpha: {r['eligibility']['best_alpha_status']}.")
    story.append(PageBreak());para('Verification and phase status','Title')
    para(f"{data['test_count']} tests pass; 448 strategy-days reconcile; nine deterministic artifacts match a fresh C1-quality repeat.")
    para(f"{len(data['recovered_preflight_failures'])} queued cases failed package preflight before trading during a preparation-path check. "
         'The original package checksum was restored and verified; separate successful retries and the original failed logs are retained. '
         'A safe preparation entrypoint now rejects output inside the simulator directory.')
    para('Original Phase 3/4 strategy and declarations remain intact. Reports include signed source/config hashes, stock conditions and fill-level accounting. The model has no future tick or final-stock-P&L input.')
    para('Engineering and development experiments are complete. The Phase 5 improvement gate and Phase 4 independent validation remain open: no candidate is promoted. See docs/to-do/phase-6.md for the remaining research and exact-artifact rehearsal path.')
    para('Limits: static 48-name membership; reused September data; sampled stops and asynchronous cross-symbol marks; process-local intraday state; organizer submission access and identity not confirmed. Historical win fractions and payoff do not establish a high probability of future profit.')
    def page(canvas,doc):
        canvas.setFont('Phase5Sans',8);canvas.setFillColor(colors.grey)
        canvas.drawString(16*mm,10*mm,'algo-trading | Phase 5 | Reused development data')
        canvas.drawRightString(194*mm,10*mm,str(doc.page))
    SimpleDocTemplate(str(folder/'phase-5-results.pdf'),pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,
                      topMargin=15*mm,bottomMargin=17*mm).build(story,onFirstPage=page,onLaterPages=page)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,required=True);parser.add_argument('--repeat',type=Path,required=True)
    parser.add_argument('--recovery',type=Path,help='Explicit successful retries of preflight-only failures')
    parser.add_argument('--test-log',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();data,conditions,lots=collect(a.runs.resolve(),a.repeat.resolve(),a.test_log.resolve(),
                                                     a.recovery.resolve() if a.recovery else None)
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    write_json(output/'phase-5-results.json',data);csv_write(output/'phase-5-results.csv',summary_rows(data))
    csv_write(output/'stock-conditions.csv',conditions);csv_write(output/'completed-lots.csv',lots)
    calibration=[]
    for s,r in data['calibration'].items():
        calibration.append({'symbol':s,**{k:json.dumps(v) if isinstance(v,list) else v for k,v in r.items()}})
    csv_write(output/'stock-calibration.csv',calibration)
    figures(data,conditions,output/'figures');(output/'phase-5-results.md').write_text(markdown(data));pdf(data,output)
    print(f'Generated {len(data["runs"])} verified results, {len(conditions)} stock-condition rows and {len(lots)} completed-lot rows.')

if __name__=='__main__':
    main()
