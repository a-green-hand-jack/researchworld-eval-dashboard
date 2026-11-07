"""Generate EVERY paper table, figure and result macro from measured files."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from data import ROOT

RESULT=ROOT/'results';PAPER=ROOT/'paper';TABLES=PAPER/'tables';FIG=PAPER/'figures'
COLORS={'Arena':'#2166ac','MT-human':'#d6604d','MT-GPT4':'#762a83','NBA':'#238b45'}


def tex(s):return str(s).replace('_',r'\_').replace('%',r'\%')
def bound(a,b):return str(int(a)) if a==b else f'[{int(a)}, {int(b)}]'
def wilson(success,n,z=1.959963984540054):
    p=success/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den
    delta=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-delta,mid+delta


def table(name,columns,heading,rows):
    text='\\begin{tabular}{'+columns+'}\n\\toprule\n'+heading+r' \\'+'\n\\midrule\n'
    text+='\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)
    text+='\n\\bottomrule\n\\end{tabular}\n'
    (TABLES/name).write_text(text)


def main():
    FIG.mkdir(exist_ok=True);TABLES.mkdir(exist_ok=True)
    s=pd.read_csv(RESULT/'summary.csv');r=pd.read_csv(RESULT/'random.csv')
    a=pd.read_csv(RESULT/'adjacent.csv');v=pd.read_csv(RESULT/'ablations.csv')
    m=pd.read_csv(RESULT/'matched.csv');w=pd.read_csv(RESULT/'winner.csv').set_index('panel')
    main=s[~s.panel.str.startswith('Matched')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'ps.fonttype':42})
    # Figure 1: conditional random-flip probabilities, independent permutations.
    fig,axs=plt.subplots(1,3,figsize=(7.2,2.8),sharey=True)
    groups=[['Arena'],['MT-human','MT-GPT4'],[f'NBA-{y}' for y in range(2010,2016)]]
    for ax,names,title in zip(axs,groups,['Crowdsourced preferences','Expert and model judgments','NBA regular seasons']):
        for ix,name in enumerate(names):
            d=r[(r.panel==name)&(r.fraction>0)]
            stats=d.groupby('fraction').pair_reversed.agg(['sum','count']).reset_index()
            xx=100*stats.fraction.to_numpy();yy=(stats['sum']/stats['count']).to_numpy()
            color=COLORS.get(name,plt.cm.viridis(.08+.16*ix))
            lo,hi=wilson(stats['sum'].to_numpy(),stats['count'].to_numpy())
            label=name.replace('NBA-','')
            ax.plot(xx,yy,'o-',markersize=3.5,color=color,label=label,lw=1.5)
            if len(names)<3:ax.fill_between(xx,lo,hi,color=color,alpha=.16)
        ax.set_xscale('log');ax.set_xlabel('Global reversal budget (%)',fontsize=10);ax.set_title(title,fontsize=10)
        ax.set_ylim(-.015,.57);ax.grid(alpha=.2);ax.legend(fontsize=9,frameon=False,ncol=2 if len(names)>2 else 1)
    axs[0].set_ylabel('Pair reversal probability',fontsize=11)
    fig.tight_layout();fig.savefig(FIG/'random.pdf',bbox_inches='tight');plt.close(fig)
    # Figure 2: the same certified intervals under two denominators.
    fig,axs=plt.subplots(1,2,figsize=(6.3,3.5),sharey=True)
    for ax,denom,title in zip(axs,['n','leader_n'],['All-record budget','Leader-support budget']):
        for ix,row in enumerate(main.itertuples()):
            color=COLORS.get(row.panel,COLORS['NBA'])
            low=100*row.lower_k/getattr(row,denom);high=100*row.k/getattr(row,denom)
            ax.plot([low,high],[ix,ix],color=color,lw=2)
            ax.plot(low,ix,'|',color=color,ms=8)
            ax.plot(high,ix,'o',color=color,ms=5,mfc=color if low==high else 'white')
        ax.set_xscale('log');ax.grid(axis='x',alpha=.2);ax.set_title(title)
        ax.set_xlabel('Reversal budget (%)')
    axs[0].set_yticks(np.arange(len(main)),main.panel);axs[0].invert_yaxis()
    fig.tight_layout();fig.savefig(FIG/'normalization.pdf',bbox_inches='tight');plt.close(fig)
    # Appendix figure: local influence prediction is checked against actual fits.
    fig,ax=plt.subplots(figsize=(4.8,3.5))
    for key,color in COLORS.items():
        select=a.panel.str.startswith('NBA') if key=='NBA' else a.panel.eq(key)
        d=a[select]
        ax.scatter(d.predicted_k,d.k,s=25,label=key,c=color,alpha=.8)
    d=a[a.panel.str.startswith('Matched')]
    ax.scatter(d.predicted_k,d.k,s=25,label='Matched MT',c='#777777',marker='x')
    high=max(a.k.max(),a.predicted_k.max())+5;ax.plot([0,high],[0,high],'k--',lw=.8)
    ax.set(xlabel='First-order predicted prefix',ylabel='First exactly refitted reversal prefix')
    ax.legend(frameon=False,fontsize=8);ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(FIG/'influence.pdf',bbox_inches='tight');plt.close(fig)
    # Data table.
    rows=[]
    for row in main.itertuples():
        rows.append([row.panel,f'{row.n:,}',row.m,f'{100*(1-row.decisive/row.n):.1f}',
            row.leader_n,f'{row.gap:.3f}',f'[{row.gap_lo:.3f}, {row.gap_hi:.3f}]'])
    table('data.tex','lrrrrrr',r'Panel & $N$ & $M$ & Tie (\%) & $n_\ell$ & $\widehat\Delta$ & Bootstrap 95\% interval',rows)
    rows=[]
    for row in main.itertuples():
        ww=w.loc[row.panel]
        rows.append([row.panel,bound(row.lower_k,row.k),bound(ww.lower_k,ww.upper_k),
            f'{row.global_pct:.4f}' if row.global_pct<.01 else f'{row.global_pct:.3f}',
            f'{row.leader_pct:.3f}',row.resolution_k])
    table('thresholds.tex','lrrrrr',r'Panel & Pair $K^*$ & Winner $K^*_{\rm win}$ & $100U/N$ & $100U/n_\ell$ & $U_{2s}$',rows)
    rows=[]
    for row in s.itertuples():
        rows.append([row.panel,row.direct_capacity,row.lower_k,row.k,row.safe_k+1,row.adaptive_k,row.incident_k,row.delete_k])
    table('methods.tex','lrrrrrrr',r'Panel & $W_{\ell r}$ & $L_{\rm dir}$ & $U$ & $L_{\rm curv}$ & Adaptive & Incident & Delete',rows)
    rows=[]
    for row in s[s.panel.str.startswith('Matched')].itertuples():
        rows.append([row.panel,f'{row.n:,}',f'{row.gap:.3f}',
            f'[{row.gap_lo:.3f}, {row.gap_hi:.3f}]',bound(row.lower_k,row.k),f'{row.global_pct:.3f}'])
    table('matched.tex','lrrrrr',r'Panel & $N$ & $\widehat\Delta$ & Bootstrap 95\% interval & $K^*$ & $100K^*/N$',rows)
    rows=[]
    for name in s.panel:
        d=r[(r.panel==name)&np.isclose(r.fraction,.01)]
        count=int(d.pair_reversed.sum());lo,hi=wilson(count,len(d))
        rows.append([name,f'{100*count/len(d):.1f}',f'[{100*lo:.1f}, {100*hi:.1f}]',
            f'{100*d.leader_lost.mean():.1f}',f'{d.kendall.mean():.4f}',f'[{d.kendall.quantile(.025):.4f}, {d.kendall.quantile(.975):.4f}]'])
    table('random.tex','lrrrrr',r'Panel & Pair (\%) & Wilson 95\% interval & Winner (\%) & Mean $D_K$ & Central 95\% $D_K$',rows)
    rows=[]
    for row in v.itertuples():rows.append([row.panel,tex(row.variant),tex(row.leader),f'{row.gap:.4f}',row.k])
    table('ablations.tex','lllrr',r'Panel & Variant & Fitted winner & Original-pair gap & $U$',rows)
    # Separate compact tables for every adjacent pair, all 83 rows.
    for name,d in a.groupby('panel',sort=False):
        rows=[[row.position,tex(row.first),tex(row.second),f'{row.gap:.3f}',
               bound(row.lower_k,row.k),row.predicted_k] for row in d.itertuples()]
        table('adjacent_'+name+'.tex','rllrrr',r'Position & Higher & Lower & Gap & $K^*$ & Pred.',rows)
    # Machine-generated numeric macros prevent stale text after a rerun.
    macros={}
    for row in s.itertuples():
        prefix=row.panel.replace('-','').replace('4','Four')
        for key,fmt in [('n',',d'),('m','d'),('k','d'),('resolution_k','d'),('lower_k','d'),
                        ('leader_n','d'),('direct_capacity','d'),('gap','.3f'),
                        ('gap_lo','.3f'),('gap_hi','.3f'),('global_pct','.4f'),('leader_pct','.2f')]:
            suffix=''.join(x.capitalize() for x in key.split('_'))
            macros[prefix+suffix]=format(getattr(row,key),fmt)
        macros[prefix+'BootReverse']=f'{100*row.bootstrap_pair_reverse:.1f}'
    run=json.loads((RESULT/'run.json').read_text());winrun=json.loads((RESULT/'winner_run.json').read_text())
    macros.update(Repeats=str(run['random_repeats']),BootstrapRepeats=str(run['bootstrap_repeats']),
        Seed=str(run['seed']),MatchedRepeats=str(run['matched_repeats']),MainSeconds=f"{run['seconds']:.1f}",
        WinnerSeconds=f"{winrun['seconds']:.1f}",PeakMiB=f"{run['peak_rss_kib']/1024:.1f}",
        AdjacentCount=str(len(a)),AdjacentTight=str(int(sum(a.lower_k==a.k))),
        AdjacentExactPrediction=str(int(sum(a.k==a.predicted_k))),
        AdjacentMAE=f'{np.mean(abs(a.k-a.predicted_k)):.2f}',
        AdjacentMaxError=str(int(max(abs(a.k-a.predicted_k)))),
        MatchedHumanMin=str(int(m[m.judge=='human'].k.min())),
        MatchedHumanMax=str(int(m[m.judge=='human'].k.max())),
        MatchedHumanMedian=f"{m[m.judge=='human'].k.median():.0f}",
        ArenaAdjacentMax=str(int(a[a.panel=='Arena'].k.max())),
        MainWinnerExact=str(int(w.loc[main.panel,'exact'].sum())),
        MainPairExact=str(int(sum(main.lower_k==main.k))))
    (PAPER/'numbers.tex').write_text('% Generated by src/report.py; do not edit.\n'+
        '\n'.join('\\expandafter\\def\\csname '+key+'\\endcsname{'+value+'}' for key,value in macros.items())+'\n')
    stats=dict(adjacent_count=len(a),adjacent_exact=int(sum(a.lower_k==a.k)),
        adjacent_prediction_exact=int(sum(a.k==a.predicted_k)),
        adjacent_prediction_mae=float(np.mean(abs(a.k-a.predicted_k))),
        matched_human_quantiles=m[m.judge=='human'].k.quantile([0,.025,.5,.975,1]).to_dict())
    (RESULT/'report_stats.json').write_text(json.dumps(stats,indent=2)+'\n')
    print(json.dumps(stats,indent=2))


if __name__=='__main__':main()
