#!/usr/bin/env python3
"""Render final presentation only, from committed analysis summary slices.
Run from any working directory: python3 presentation/render.py
Dependencies: numpy, pandas, matplotlib. No fitting or data downloads.
"""
from pathlib import Path
import json, hashlib, platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'presentation/inputs'
for rec in json.loads((ROOT/'presentation/provenance.json').read_text())['files']:
    assert hashlib.sha256((ROOT/rec['copied_path']).read_bytes()).hexdigest()==rec['sha256']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':8,'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':False,'savefig.facecolor':'white'})
D=pd.read_csv(IN/'primary/datasets.csv').set_index('dataset')
U=pd.read_csv(IN/'primary/uncertainty.csv').set_index('dataset')
C=pd.read_csv(IN/'primary/curves.csv')
R=pd.read_csv(IN/'robustness/datasets.csv').set_index('variant')
ORDER=['arena','mt_human','mt_gpt4']+[f'nba_{year}' for year in range(2006,2016)]
LABEL={'arena':'Arena','mt_human':'MT human','mt_gpt4':'MT GPT-4',**{f'nba_{y}':f'NBA {y}' for y in range(2006,2016)}}
COLOR={'arena':'#0072B2','mt_human':'#009E73','mt_gpt4':'#CC79A7',**{f'nba_{y}':'#666666' for y in range(2006,2016)}}
STRATEGIES=[('random','Uniform random','#0072B2','o'),('endpoint_random','Endpoint-only','#D55E00','s'),('influence','Influence','#009E73','^')]
# Fail rather than silently interpret upper limits as actual edit counts.
assert (C.actual_k_min==C.actual_k_max).all()
assert (C.budget_k==C.actual_k_max).all(), 'Update display/caption to disclose strategy saturation.'
assert np.allclose(D.attack_fraction,D.attack_k/D.N)
assert C[C.strategy=='influence'].pair_rate_mc_low.isna().all()
outputs=[]
def save(fig,name):
    for ext in ('pdf','png'):
        dest=ROOT/'figures'/f'{name}.{ext}'
        fig.savefig(dest,dpi=180,bbox_inches='tight',pad_inches=.07)
        outputs.append(str(dest.relative_to(ROOT)))
    plt.close(fig)
def interval(ax,x,lo,hi,y,color):
    ax.plot([lo,hi],[y,y],color=color,lw=1.5)
    ax.plot([lo,lo],[y-.09,y+.09],color=color,lw=.8)
    ax.plot([hi,hi],[y-.09,y+.09],color=color,lw=.8)
    ax.scatter(x,y,s=18,color=color,zorder=3)
# Main 1: log budgets and baseline uncertainty on separate aligned axes.
fig,(a,b)=plt.subplots(1,2,figsize=(5.5,4.3),gridspec_kw={'width_ratios':[1.1,1]},sharey=True)
for i,name in enumerate(ORDER):
    d,u=D.loc[name],U.loc[name];color=COLOR[name]
    a.scatter(100*d.attack_fraction,i,s=24,color=color,zorder=3)
    a.annotate(f'  k={int(d.attack_k)}',(100*d.attack_fraction,i),xytext=(4,0),textcoords='offset points',va='center',fontsize=8,color=color)
    interval(b,u.gap,u.gap_low,u.gap_high,i,color)
for ax in (a,b):
    ax.set_ylim(len(ORDER)-.5,-.75)
    ax.axhline(2.5,color='.8',lw=.7)
    ax.grid(axis='x',color='.9',lw=.5)
a.set_yticks(range(len(ORDER)),[LABEL[n] for n in ORDER]);a.set_xscale('log');a.set_xlim(.001,9)
a.set_xticks([.001,.01,.1,1],[ '0.001','0.01','0.1','1'])
a.set_xlabel('Found edits (% of all observations)\nlog scale')
a.set_title('(a) Found reversal budget',loc='left')
b.axvline(0,color='black',ls=':',lw=.9);b.set_xlim(U.gap_low.min()-.04,U.gap_high.max()+.04)
b.set_xlabel('Leader − runner score (logits)')
b.set_title('(b) Baseline score gap',loc='left')
fig.subplots_adjust(left=.13,right=.99,wspace=.15,bottom=.15,top=.91)
save(fig,'primary_stability')
# Main 2: strategy curves on selected LLM datasets, exact integer x axes.
fig,axs=plt.subplots(2,3,figsize=(5.5,4.25),sharey='row')
for j,name in enumerate(ORDER[:3]):
    n=int(D.loc[name,'N']);sub=C[C.dataset==name]
    for strategy,label,color,marker in STRATEGIES:
        g=sub[sub.strategy==strategy].sort_values('actual_k_min'); x=g.actual_k_min.to_numpy()
        a=axs[0,j]; y=100*g.pair_reversal_rate.to_numpy()
        a.plot(x,y,color=color,marker=marker,ms=3,lw=1,label=label)
        if strategy!='influence':
            a.vlines(x,100*g.pair_rate_mc_low,100*g.pair_rate_mc_high,color=color,lw=.8,alpha=.8)
        a=axs[1,j];a.plot(x,100*g.kendall_mean,color=color,marker=marker,ms=3,lw=1)
        if strategy!='influence':
            a.fill_between(x,100*g.kendall_q025,100*g.kendall_q975,color=color,alpha=.12,linewidth=0)
    ticks=sorted(set([1,int(.01*n),int(.05*n)]))
    for a in axs[:,j]:
        a.set_xscale('log');a.set_xlim(.85,int(.05*n)*1.17)
        a.set_xticks(ticks,[str(k) for k in ticks]);a.grid(axis='y',color='.9',lw=.5)
    axs[0,j].set_title(LABEL[name],pad=30)
    top=axs[0,j].secondary_xaxis('top',functions=(lambda x,n=n:100*x/n,lambda x,n=n:x*n/100))
    top.set_xticks([100*k/n for k in ticks[1:]],[f'{100*k/n:.3g}' for k in ticks[1:]]);top.tick_params(labelsize=7)
    top.set_xlabel('Budget (%)',labelpad=3)
    axs[1,j].set_xlabel('Actual edits k (log)')
axs[0,0].set_ylabel('Pair reversal (%)');axs[0,0].set_ylim(-4,104)
axs[1,0].set_ylabel('Kendall disagreement (%)');axs[1,0].set_ylim(bottom=-.2)
fig.legend(*axs[0,0].get_legend_handles_labels(),ncol=3,loc='lower center',bbox_to_anchor=(.52,-.015),frameon=False)
fig.subplots_adjust(left=.095,right=.99,bottom=.19,top=.78,hspace=.3,wspace=.13)
save(fig,'strategy_curves')
# Main 3: descriptive matched contrast and modeling conventions.
fixed=pd.read_csv(IN/'matched_fixedpair/replicates.csv')
pair=fixed.pivot(index='rep',columns='dataset',values='attack_fraction')
diff=100*(pair.matched_human-pair.matched_gpt4)
summary=json.loads((IN/'matched_fixedpair/difference.json').read_text())
assert len(diff)==summary['pairs']==500
assert np.isclose(diff.mean(),summary['mean_difference']*100)
fig,(a,b)=plt.subplots(1,2,figsize=(5.5,2.8),gridspec_kw={'width_ratios':[1.05,1]})
a.hist(diff,bins=np.linspace(-3.5,1,28),color='#0072B2',alpha=.75,edgecolor='white',lw=.3)
a.axvline(0,color='black',ls=':',lw=1)
a.axvline(diff.mean(),color='#D55E00',lw=1.4)
lo,hi=100*summary['q025'],100*summary['q975']; ymax=a.get_ylim()[1]
a.plot([lo,hi],[ymax*.73]*2,color='#D55E00',lw=2)
a.text(-3.4,ymax*.98,f'Mean {diff.mean():.2f} pp\n95% range [{lo:.2f}, {hi:.2f}]',va='top',fontsize=7)
a.set_xlabel('Human − GPT-4 found fraction\n(percentage points; fixed reference pair)')
a.set_ylabel('Question-bootstrap replicates')
a.set_title('(a) Matched MT schedule',loc='left')
variants=[('arena_ridge0.1',r'$\lambda=0.1$'),('arena',r'$\lambda=1$ (primary)'),('arena_ridge10.0',r'$\lambda=10$'),('arena_support500','Support ≥500'),('arena_decisive','No ties; pair flips')]
for i,(variant,label) in enumerate(variants):
    d=D.loc['arena'] if variant=='arena' else R.loc[variant]
    b.barh(i,d.attack_k,color='#0072B2' if variant!='arena_decisive' else '#D55E00',height=.52)
    b.text(d.attack_k+.2,i,f'{int(d.attack_k)} ({100*d.attack_fraction:.4f}%)',va='center',fontsize=7)
b.set_yticks(range(5),[v[1] for v in variants]);b.invert_yaxis();b.set_xlim(0,18);b.set_xticks([0,5,10,15]);b.set_xlabel('Found successful edits k')
b.set_title('(b) Arena conventions',loc='left')
fig.subplots_adjust(left=.09,right=.99,bottom=.24,top=.87,wspace=.83)
save(fig,'controls')
# Appendix: every sports season, no selected showcase season.
fig,axs=plt.subplots(5,2,figsize=(5.5,7.2),sharey=True)
for ax,name in zip(axs.flat,ORDER[3:]):
    for strategy,label,color,marker in STRATEGIES:
        g=C[(C.dataset==name)&(C.strategy==strategy)].sort_values('actual_k_min')
        ax.plot(g.actual_k_min,100*g.pair_reversal_rate,color=color,marker=marker,ms=2,lw=.8,label=label)
        if strategy!='influence': ax.vlines(g.actual_k_min,100*g.pair_rate_mc_low,100*g.pair_rate_mc_high,color=color,lw=.6)
    ax.set_title(f'{name[-4:]} (N={int(D.loc[name,"N"]):,})',fontsize=8)
    ax.set_xscale('log');ax.set_xticks([1,10,50],['1','10','50']);ax.set_ylim(-4,104);ax.grid(axis='y',color='.9',lw=.5)
for a in axs[-1]:a.set_xlabel('Actual edits k',fontsize=7)
for a in axs[:,0]:a.set_ylabel('Pair reversals (%)',fontsize=7)
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='lower center',ncol=3,frameon=False)
fig.subplots_adjust(left=.08,right=.99,top=.96,bottom=.09,hspace=.55,wspace=.14)
save(fig,'nba_strategy_curves')
# Tables are fragments: paper owns floats, placement, numbering and narrative.
def texwrite(name,lines):
    (ROOT/'tables'/name).write_text('\n'.join(lines)+'\n');outputs.append('tables/'+name)
def row(values): return ' & '.join(map(str,values))+r' \\'
lines=[r'\begin{tabular}{lrrrrrr}',r'\toprule',row(['Ranking','$N$','$M$','Decisive','Found $k$','$100k/N$ (\%)','Gap [95\% range]']),r'\midrule']
for name in ORDER:
    d,u=D.loc[name],U.loc[name]
    lines.append(row([LABEL[name],f'{int(d.N):,}',int(d.m),f'{int(d.decisive):,}',int(d.attack_k),f'{100*d.attack_fraction:.4f}',f'{u.gap:.3f} [{u.gap_low:.3f}, {u.gap_high:.3f}]']))
lines += [r'\bottomrule',r'\end{tabular}'];texwrite('primary.tex',lines)
lines=[r'\begin{tabular}{llrrrr}',r'\toprule',row(['Ranking','Original leader $>$ runner','$N$','Ties (\%)','Min support','Clusters']),r'\midrule']
for name in ORDER:
    d=D.loc[name];leader=d.leader;runner=d.runner
    if name=='arena':leader='GPT-4-1106';runner='GPT-4-0125'
    if name.startswith('mt_'):leader='GPT-4';runner='Claude-v1'
    lines.append(row([LABEL[name],leader+' $>$ '+runner,f'{int(d.N):,}',f'{100*d.ties/d.N:.1f}',int(d.min_support),f'{int(d.clusters):,}']))
lines += [r'\bottomrule',r'\end{tabular}'];texwrite('datasets.tex',lines)
lines=[r'\begin{tabular}{lrrrrrr}',r'\toprule',row(['Ranking','$k$','Random (\%)','Endpoint (\%)','Influence (\%)','Winner (\%)','Kendall (\%)']),r'\midrule']
for name in ORDER:
    g=C[(C.dataset==name)&(C.budget_k==int(.01*D.loc[name,'N']))].set_index('strategy')
    assert len(g)==3
    random=g.loc['random'];endpoint=g.loc['endpoint_random'];inf=g.loc['influence']
    lines.append(row([LABEL[name],int(inf.budget_k),f'{100*random.pair_reversal_rate:.1f}',f'{100*endpoint.pair_reversal_rate:.1f}',f'{100*inf.pair_reversal_rate:.1f}',f'{100*inf.winner_change_rate:.1f}',f'{100*inf.kendall_mean:.2f}']))
lines += [r'\bottomrule',r'\end{tabular}'];texwrite('one_percent.tex',lines)
variants=[('arena_ridge0.1','Arena: $\lambda=0.1$'),('arena','Arena: $\lambda=1$'),('arena_ridge10.0','Arena: $\lambda=10$'),('arena_support500','Arena: support $\geq500$'),('arena_decisive','Arena: no ties (pair flips)'),('mt_human_ridge0.1','MT human: $\lambda=0.1$'),('mt_human','MT human: $\lambda=1$'),('mt_human_ridge10.0','MT human: $\lambda=10$'),('mt_human_expert','MT human: expert only'),('mt_gpt4_ridge0.1','MT GPT-4: $\lambda=0.1$'),('mt_gpt4','MT GPT-4: $\lambda=1$'),('mt_gpt4_ridge10.0','MT GPT-4: $\lambda=10$'),('mt_gpt4_consistent','MT GPT-4: consistent only')]
lines=[r'\begin{tabular}{lrrrr}',r'\toprule',row(['Convention','$N$','$M$','Found $k$','$100k/N$ (\%)']),r'\midrule']
for v,label in variants:
    d=D.loc[v] if v in D.index else R.loc[v]
    lines.append(row([label,f'{int(d.N):,}',int(d.m),int(d.attack_k),f'{100*d.attack_fraction:.4f}']))
lines += [r'\bottomrule',r'\end{tabular}'];texwrite('conventions.tex',lines)
lines=[r'\begin{tabular}{lrrr}',r'\toprule',row(['Matched statistic / resampling','Runs','Mean difference (pp)','95\% range (pp)']),r'\midrule']
for path,label,key in [('matched/paired_difference.json','Reselected pair / human labels','n'),('matched_bootstrap/paired_difference.json','Reselected pair / joint questions','n'),('matched_fixedpair/difference.json','Fixed reference pair / joint questions','pairs')]:
    s=json.loads((IN/path).read_text())
    lines.append(row([label,s[key],f'{100*s["mean_difference"]:.2f}',f'[{100*s["q025"]:.2f}, {100*s["q975"]:.2f}]']))
lines += [r'\bottomrule',r'\end{tabular}'];texwrite('matched.tex',lines)
# Exact integer/fraction budget mapping also documents actual strategy use.
lines=[r'\begin{tabular}{lp{4.1in}}',r'\toprule',row(['Ranking','Actual edits $k$ (percentage of all observations)']),r'\midrule']
for name in ORDER:
    g=C[(C.dataset==name)&(C.strategy=='influence')].sort_values('budget_k')
    lines.append(row([LABEL[name],'; '.join(f'{int(r.budget_k)} ({100*r.budget_fraction:.4f}\\%)' for r in g.itertuples())]))
lines += [r'\bottomrule',r'\end{tabular}'];texwrite('budgets.tex',lines)
(ROOT/'presentation/render_manifest.json').write_text(json.dumps({'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__,'outputs':outputs},indent=2)+'\n')
print(f'Rendered {len(outputs)} outputs; all input hashes and budget checks passed.')
