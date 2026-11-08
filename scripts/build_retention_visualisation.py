"""Build visual evidence from the verified Phase 5 retention replays."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'retention-mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from package_support import ROOT, sha256


def load(control, new, expected):
    hashes=json.loads((new/'reproducible-hashes.json').read_text())
    if hashes!=expected['hashes']:
        raise ValueError('Run hash manifest differs from committed results')
    for path,digest in hashes.items():
        if sha256(new/path)!=digest:
            raise ValueError(f'Changed artifact: {new/path}')
    report=json.loads((new/'report.json').read_text())
    if report['performance']!=expected['retention'] or control['performance']!=expected['control']:
        raise ValueError('Metrics differ from committed comparison')
    if any(not d['reconciliation']['reconciled'] for d in report['daily']):
        raise ValueError('Unreconciled daily record')
    days=[d['date'] for d in report['daily']]
    if days!=[d['date'] for d in control['daily']] or len(days)!=16:
        raise ValueError('Incomparable session dates')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--c3',type=Path,default=ROOT/'artifacts/retention-C3')
    parser.add_argument('--c4',type=Path,default=ROOT/'artifacts/retention-C4')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    base=json.loads((ROOT/'docs/result-data-visualisation/phase-5/phase-5-results.json').read_text())['runs']
    evidence=json.loads((ROOT/'docs/result-data-visualisation/phase-5-retention/results.json').read_text())
    runs={k:load(base[k+'-equal'],path.resolve(),evidence[k]) for k,path in [('C3',args.c3),('C4',args.c4)]}
    colors=['#287C91','#D38431'];labels=['Original equal','Retention'];models=['C3','C4'];x=np.arange(2)
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.16,'font.size':10})
    def save(fig,name):
        fig.tight_layout();fig.savefig(out/name,dpi=180,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for ax,(field,title,scale) in zip(axes.flat,[('net_return_pct','Net return (%)',1),('average_exposure','Average exposure (%)',100),('official_max_drawdown_pct','Maximum drawdown (%)',1),('completed_fifo_round_trips','Completed FIFO round trips',1)]):
        for j,kind in enumerate(('control','retention')):
            vals=[evidence[k][kind][field]*scale for k in models]
            ax.bar(x+(j-.5)*.36,vals,.36,label=labels[j],color=colors[j])
            for i,v in enumerate(vals): ax.annotate(f'{v:.0f}' if field=='completed_fifo_round_trips' else f'{v:.2f}',(i+(j-.5)*.36,v),xytext=(0,4 if v>=0 else -13),textcoords='offset points',ha='center',fontsize=8)
        ax.set_xticks(x,models);ax.set_title(title);ax.axhline(0,color='#444',lw=.5)
        if field=='average_exposure':ax.axhline(50,ls='--',color='#b54c45',label='Common minimum')
        if field=='official_max_drawdown_pct':ax.axhline(6.1492438092,ls='--',color='#b54c45',label='Strict limit')
        if field=='completed_fifo_round_trips':ax.axhline(5,ls='--',color='#b54c45',label='Must exceed 5')
    axes[0,0].legend();fig.suptitle('C3 and C4: original vs retention · September development sample',fontsize=13);save(fig,'overview.png')
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for ax,(field,title) in zip(axes.flat,[('expected_payoff_thb','Expected payoff per completed lot (THB)'),('fees_thb','Commission and VAT (THB)'),('realized_pnl_thb','Realized P&L (THB)'),('unrealized_pnl_thb','Open-position P&L (THB)')]):
        for j,kind in enumerate(('control','retention')):
            ax.bar(x+(j-.5)*.36,[evidence[k][kind][field] for k in models],.36,label=labels[j],color=colors[j])
        ax.set_xticks(x,models);ax.set_title(title);ax.axhline(0,color='#444',lw=.5)
    axes[0,0].legend();fig.suptitle('Payoff, costs and losses · negative payoff fails common criteria',fontsize=13);save(fig,'payoff-costs.png')
    for k in models:
        fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
        for j,(kind,daily) in enumerate((('Original equal',base[k+'-equal']['daily']),('Retention',runs[k]['daily']))):
            dates=[d['date'][5:] for d in daily];perf=[d['performance'] for d in daily]
            axes[0].plot(dates,[p['net_return_pct'] for p in perf],label=kind,color=colors[j],lw=2)
            axes[1].plot(dates,[100*p['average_exposure'] for p in perf],label=kind,color=colors[j],lw=2)
            axes[2].plot(dates,[p['completed_fifo_round_trips'] for p in perf],label=kind,color=colors[j],lw=2)
        axes[0].plot(dates,[p['benchmark_return_pct'] for p in perf],ls='--',color='#777',label='SET50, first-close anchor')
        axes[0].set_ylabel('Net return (%)');axes[0].legend(fontsize=8);axes[1].set_ylabel('Running average exposure (%)');axes[1].axhline(50,ls='--',color='#b54c45');axes[2].set_ylabel('Cumulative FIFO trips');axes[2].axhline(5,ls='--',color='#b54c45');axes[2].tick_params(axis='x',rotation=45);fig.suptitle(f'{k}: daily paths');save(fig,k.lower()+'-paths.png')
    font=Path(matplotlib.get_data_path())/'fonts/ttf';pdfmetrics.registerFont(TTFont('RetentionSans',str(font/'DejaVuSans.ttf')));pdfmetrics.registerFont(TTFont('RetentionBold',str(font/'DejaVuSans-Bold.ttf')))
    styles=getSampleStyleSheet()
    for name in styles.byName:styles[name].fontName='RetentionBold' if name.startswith('Heading') or name=='Title' else 'RetentionSans'
    story=[]
    def para(t,style='BodyText'):story.append(Paragraph(t,styles[style]));story.append(Spacer(1,4*mm))
    def pic(name,width=175*mm):
        from PIL import Image as PILImage
        with PILImage.open(out/name) as im:w,h=im.size
        story.append(Image(str(out/name),width=width,height=width*h/w))
    para('Phase 5 retention comparison','Title');para('C3 and C4: original equal-weight controls and retention-only research variants. All runs use 16 September 2026 development sessions.')
    para('Both retention runs meet the exposure, round-trip and drawdown thresholds. Both still have negative expected payoff and negative total return, so neither passes common criteria or Best Alpha.');pic('overview.png');story.append(PageBreak())
    para('Costs and complete P&amp;L','Title');para('Fees fall in both retention runs, but open-position losses rise. Payoff is calculated on fully completed non-breakeven FIFO lots; partial fills can create multiple lots from a single position episode.');pic('payoff-costs.png');story.append(PageBreak())
    for k in models:
        para(k+' daily paths','Title');para('Return starts from initial cash; SET50 starts at its first sample close. Exposure is the running average of daily closes. The red lines mark the 50% exposure minimum and five FIFO lots.');pic(k.lower()+'-paths.png');story.append(PageBreak())
    para('Interpretation and evidence','Title');para('C3 retention improves net return by 0.318 percentage points but has a slightly worse payoff and a larger open loss. C4 retention worsens return by 0.185 points despite lower fees. Exposure increases by 16.17 and 20.60 percentage points respectively, so comparisons are not exposure matched.')
    para('The strategy retains opening quantities when entry eligibility fails; existing stops, profit exits, risk scaling and execution rules continue. Risk limits can drift, exits can be partial, and same-day restart state is not durable. No sample-end liquidation is forced.')
    para('All 32 strategy-days reconcile cash, holdings, fees, NAV and FIFO with the official engine. The targeted test confirms that a failed entry does not force a sale and a volatility stop can still sell. Results reuse September development data; additional permitted ticks and effective-dated membership are needed for independent validation. No candidate is promoted.')
    def footer(canvas,doc):canvas.setFont('RetentionSans',8);canvas.drawString(16*mm,10*mm,'Phase 5 retention | Reused development data');canvas.drawRightString(194*mm,10*mm,str(doc.page))
    SimpleDocTemplate(str(out/'retention-results.pdf'),pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=15*mm,bottomMargin=17*mm).build(story,onFirstPage=footer,onLaterPages=footer)
    (out/'data.json').write_text(json.dumps({'runs':evidence,'days':{k:[{'date':d['date'],'performance':d['performance']} for d in runs[k]['daily']] for k in models}},indent=2,sort_keys=True)+'\n')
    print('Generated four figures, a five-page PDF, and daily data from verified replay artifacts.')

if __name__=='__main__':main()
