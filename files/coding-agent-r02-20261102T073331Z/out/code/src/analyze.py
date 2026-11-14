"""Produce every paper table, figure, and numeric result macro from raw runs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import t, norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'paper'/'generated';OUT.mkdir(exist_ok=True)
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
df=pd.read_csv(ROOT/'results'/'runs.csv')
df['vmix']=(df.v2+df.v1)/2
METRICS=['coverage','g0','g1','boundary','interior','v2','v1','vmix','clr_infinite',
         'hgz_g0_zero_infinite','n_cal_g0_zero']
METHODS=['Max','L2','H','CLR','CLR-e3','H-scale','H-group','H-Z','H-GZ','Oracle','Coord','Bonf','H-weight','CLR-e2','CLR-e4']
LABEL={'CLR-e3':r'CLR$_{10^{-3}}$', 'CLR-e2':r'CLR$_{10^{-2}}$', 'CLR-e4':r'CLR$_{10^{-4}}$'}
SC={'dense':'Dense','hetero':'Heterogeneous','zeros':'Zeros','mixed':'Mixed','shift':'Shift'}
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'figure.dpi':160,'savefig.bbox':'tight'})
rows=[]
for (sc,k,m),d in df.groupby(['scenario','k','method']):
    for metric in METRICS:
        v=d[metric].dropna();n=len(v)
        if n==0:continue
        mean=v.mean();se=v.std(ddof=1)/np.sqrt(n);half=t.ppf(.975,n-1)*se
        rows.append(dict(scenario=sc,k=k,method=m,metric=metric,n=n,mean=mean,se=se,
                         half=half,lo=max(0,mean-half),hi=min(1,mean+half) if mean<=1 else mean+half,
                         sd=v.std(ddof=1),q05=v.quantile(.05),q95=v.quantile(.95)))
summary=pd.DataFrame(rows)
summary.to_csv(ROOT/'results'/'summary.csv',index=False)

def entry(sc,k,m,metric):
    return summary[(summary.scenario==sc)&(summary.k==k)&(summary.method==m)&(summary.metric==metric)].iloc[0]
def val(sc,k,m,metric):return entry(sc,k,m,metric)['mean']
def cell(sc,k,m,metric):
    r=entry(sc,k,m,metric)
    return f"${r['mean']:.3f}\\,{{\\scriptstyle\\pm {r['half']:.3f}}}$"
def label(m):return LABEL.get(m,m)
def table(name,header,lines):
    (OUT/name).write_text(header+'\n'+'\n'.join(lines)+'\n\\bottomrule\n\\end{tabular}\n')

# Main geometry table: all main score types; controls in appendix.
geom=['Max','L2','H','CLR','CLR-e3','H-group','H-Z','H-GZ','Oracle']
lines=[]
for m in geom:
    cells=[label(m)]
    for sc in ['dense','zeros']:
        cells += [cell(sc,3,m,x) for x in ['coverage','v2','v1']]
    lines.append(' & '.join(cells)+r' \\')
table('geometry.tex',r'\begin{tabular}{lcccccc}\toprule'+
      '\n'+r' & \multicolumn{3}{c}{Dense} & \multicolumn{3}{c}{Zeros ($\pi=.15$)} \\'+
      '\n'+r'Method & Coverage & $V_2$ & $V_1$ & Coverage & $V_2$ & $V_1$ \\\midrule',lines)

lines=[]
for m in ['H','CLR-e3','H-scale','H-group','H-Z','H-GZ','Oracle','H-weight']:
    cells=[label(m)]+[cell('mixed',8,m,x) for x in ['coverage','g1','boundary']]
    cells += [cell('shift',8,m,x) for x in ['coverage','g1']]
    lines.append(' & '.join(cells)+r' \\')
table('reliability.tex',r'\begin{tabular}{lccccc}\toprule'+
      '\n'+r' & \multicolumn{3}{c}{Mixed, $K=8$} & \multicolumn{2}{c}{Shift, $K=8$} \\'+
      '\n'+r'Method & Marginal & $G=1$ & Boundary & Marginal & $G=1$ \\\midrule',lines)

# Complete compact appendix tables, all methods and all dimensions.
for sc in SC:
    lines=[]
    for k in [3,8,20]:
        lines.append(r'\multicolumn{6}{l}{$K='+str(k)+r'$} \\')
        for m in METHODS:
            cells=[label(m)]+[cell(sc,k,m,x) for x in ['coverage','g0','g1']]
            cells += [cell(sc,k,m,'boundary') if sc not in ['dense','hetero'] else '--']
            cells += [cell(sc,k,m,'vmix') if k==3 else '--']
            lines.append(' & '.join(cells)+r' \\')
        if k!=20:lines.append(r'\midrule')
    table('full_'+sc+'.tex',r'\begin{tabular}{lccccc}\toprule'+
          '\n'+r'Method & Marginal & $G=0$ & $G=1$ & Boundary & $V_{1/2}$ \\\midrule',lines)

# Paired, repetition-level contrasts; no pooled-test binomial errors.
contrasts=[]
for sc,k,a,b,metric in [
    ('dense',3,'H','CLR','v2'),('zeros',3,'H','CLR-e3','v2'),
    ('mixed',3,'H-GZ','H','boundary'),('mixed',8,'H-group','H','g1'),
    ('shift',8,'H-weight','H','coverage'),('hetero',3,'H-group','H','vmix'),
    ('mixed',3,'H-GZ','H-group','vmix')]:
    aa=df[(df.scenario==sc)&(df.k==k)&(df.method==a)].set_index('rep')[metric]
    bb=df[(df.scenario==sc)&(df.k==k)&(df.method==b)].set_index('rep')[metric]
    d=aa-bb;h=t.ppf(.975,len(d)-1)*d.std(ddof=1)/np.sqrt(len(d))
    contrasts.append(dict(scenario=sc,k=k,a=a,b=b,metric=metric,mean=d.mean(),half=h,
                          lo=d.mean()-h,hi=d.mean()+h))
pd.DataFrame(contrasts).to_csv(ROOT/'results'/'paired_contrasts.csv',index=False)

# Macro names are deterministic, with result values entirely data-derived.
macros=[]
for prefix,sc,k,m,metric in [
    ('DenseH','dense',3,'H','coverage'),('DenseCoord','dense',20,'Coord','coverage'),
    ('DenseBonf','dense',20,'Bonf','coverage'),('HeteroHOne','hetero',3,'H','g1'),
    ('HeteroGroupOne','hetero',3,'H-group','g1'),('HeteroOracleOne','hetero',3,'Oracle','g1'),
    ('ZerosHBoundary','zeros',3,'H','boundary'),('ZerosHZBoundary','zeros',3,'H-Z','boundary'),
    ('ZerosClrVolume','zeros',3,'CLR-e3','v2'),('ZerosSmoothVolume','zeros',3,'CLR-e2','v2'),
    ('MixedHBoundary','mixed',3,'H','boundary'),('MixedHZBoundary','mixed',3,'H-Z','boundary'),
    ('MixedHGZBoundary','mixed',3,'H-GZ','boundary'),('MixedGroupBoundary','mixed',3,'H-group','boundary'),
    ('MixedSmoothBoundary','mixed',3,'CLR-e3','boundary'),('MixedSmoothBigBoundary','mixed',3,'CLR-e2','boundary'),
    ('MixedHGZSize','mixed',3,'H-GZ','vmix'),('MixedGroupSize','mixed',3,'H-group','vmix'),
    ('MixedOracleSize','mixed',3,'Oracle','vmix'),('MixedHGZOne','mixed',3,'H-GZ','g1'),
    ('MixedHScaleOne','mixed',3,'H-scale','g1'),('ShiftH','shift',3,'H','coverage'),
    ('ShiftWeighted','shift',3,'H-weight','coverage'),('ShiftGroup','shift',3,'H-group','coverage'),
    ('ShiftWeightedOne','shift',3,'H-weight','g1')]:
    macros.append('\\newcommand{\\'+prefix+'}{'+cell(sc,k,m,metric)+'}')
for i,c in enumerate(contrasts):
    macros.append(r'\newcommand{\Contrast'+chr(65+i)+'}{'+f"${c['mean']:.3f}\\pm {c['half']:.3f}$"+'}')
for name,sc in [('MixedCollapse','mixed'),('ShiftCollapse','shift'),('ZerosCollapse','zeros')]:
    subset=df[(df.scenario==sc)&(df.k==3)&(df.method=='CLR')]
    h=subset.clr_infinite.sum();n=len(subset);z=norm.ppf(.975)
    c=(h/n+z*z/(2*n))/(1+z*z/n);half=z*np.sqrt(h/n*(1-h/n)/n+z*z/(4*n*n))/(1+z*z/n)
    macros.append('\\newcommand{\\'+name+'}{'+f'{int(h)}/{n}'+r' (95\% Wilson interval '+f'[{c-half:.3f}, {c+half:.3f}])'+'}')
meta=json.loads((ROOT/'results'/'metadata.json').read_text())
macros.append(r'\newcommand{\MainSeconds}{'+f"{meta['elapsed_seconds']:.1f}"+'}')
macros.append(r'\newcommand{\PeakRSS}{'+f"{meta['maxrss_child_kib']/1024:.1f}"+'}')
subset=df[(df.scenario=='mixed')&(df.k==3)&(df.method=='H-GZ')]
macros.append(r'\newcommand{\SparseInfinite}{'+str(int(subset.hgz_g0_zero_infinite.sum()))+'}')
macros.append(r'\newcommand{\SparseMean}{'+f'{subset.n_cal_g0_zero.mean():.2f}'+'}')
(OUT/'numbers.tex').write_text('\n'.join(macros)+'\n')

# Figure 1: raw CLR atom transition and exact coverage with score Monte Carlo.
sweep=pd.read_csv(ROOT/'results'/'boundary_sweep.csv')
fig,axes=plt.subplots(1,2,figsize=(6.8,2.65))
for n,col in zip([99,499,1999],['#3274a1','#e1812c','#3a923a']):
    d=sweep[sweep.n==n]
    for ax,metric,exact in zip(axes,['collapse','coverage'],['collapse_exact','coverage_exact']):
        ax.plot(d.p,d[exact],color=col,label=f'n={n}')
        err=1.96*d[metric+'_se']
        errors=np.array([np.minimum(err,d[metric]),np.minimum(err,1-d[metric])])
        if metric=='collapse':
            z=norm.ppf(.975); r=d.repeats; ph=d.collapse
            cc=(ph+z*z/(2*r))/(1+z*z/r)
            hh=z*np.sqrt(ph*(1-ph)/r+z*z/(4*r*r))/(1+z*z/r)
            errors=np.maximum(0,np.array([ph-(cc-hh),(cc+hh)-ph]))
        ax.errorbar(d.p,d[metric],yerr=errors,
                    fmt='o',ms=2.6,color=col,linewidth=.7,capsize=1.4)
for ax in axes:
    ax.axvline(.1,color='gray',ls=':',lw=.8);ax.set_xlabel(r'Boundary probability $\pi$')
axes[0].set_ylabel(r'$P(\widehat q=\infty)$');axes[0].legend(frameon=False,fontsize=7)
axes[1].set_ylabel('Marginal coverage');axes[1].axhline(.9,color='gray',ls='--',lw=.7)
fig.tight_layout();fig.savefig(FIG/'transition.pdf');plt.close(fig)

# Figure 2: conditional diagnostics, no data-dependent subgroup searches.
fig,axes=plt.subplots(1,3,figsize=(7,2.85),sharey=True)
ms=['H','CLR-e3','H-scale','H-group','H-Z','H-GZ','Oracle']
for ax,k in zip(axes,[3,8,20]):
    for j,(metric,col,lab) in enumerate([('coverage','#3274a1','Marginal'),('g1','#e1812c','G=1'),('boundary','#c03d3e','Boundary')]):
        data=[entry('mixed',k,m,metric) for m in ms]
        ax.errorbar(np.arange(len(ms))+(j-1)*.17,[r['mean'] for r in data],
                    yerr=[r['half'] for r in data],fmt='o',ms=3,color=col,label=lab,capsize=1.5,lw=.8)
    ax.axhline(.9,color='gray',ls='--',lw=.8);ax.set_title(f'K={k}')
    ax.set_xticks(range(len(ms)),[label(m) for m in ms],rotation=65,ha='right',fontsize=7)
    ax.set_ylim(-.03,1.04)
axes[0].set_ylabel('Coverage in Mixed')
axes[0].legend(frameon=False,fontsize=7,loc='lower right')
fig.tight_layout();fig.savefig(FIG/'conditional.pdf');plt.close(fig)

# Figure 3: same underlying conditional laws, shifted group proportions.
fig,ax=plt.subplots(figsize=(6.8,2.65))
ms=['H','CLR-e3','H-scale','H-group','H-Z','H-GZ','H-weight','Oracle']
for j,(k,col) in enumerate(zip([3,8,20],['#3274a1','#e1812c','#3a923a'])):
    data=[entry('shift',k,m,'coverage') for m in ms]
    ax.errorbar(np.arange(len(ms))+(j-1)*.16,[r['mean'] for r in data],
                yerr=[r['half'] for r in data],fmt='o',ms=4,color=col,label=f'K={k}',capsize=2,lw=.8)
ax.axhline(.9,color='gray',ls='--',lw=.8);ax.set_ylabel('Marginal coverage under shift')
ax.set_xticks(range(len(ms)),[label(m) for m in ms]);ax.legend(frameon=False,ncol=3,fontsize=8)
fig.tight_layout();fig.savefig(FIG/'shift.pdf');plt.close(fig)

# Appendix: efficiency preference depends on explicitly chosen stratum weights.
fig,axes=plt.subplots(1,2,figsize=(6.8,2.7))
lam=np.linspace(0,1,101)
for ax,sc in zip(axes,['zeros','mixed']):
    for m in ['Max','H','CLR-e3','H-group','H-Z','H-GZ','Oracle']:
        ax.plot(lam,lam*val(sc,3,m,'v2')+(1-lam)*val(sc,3,m,'v1'),label=label(m),lw=1.3)
    ax.set_title(SC[sc]);ax.set_xlabel(r'Interior weight $\lambda$')
axes[0].set_ylabel(r'$V_\lambda=\lambda V_2+(1-\lambda)V_1$')
axes[1].legend(frameon=False,fontsize=7,ncol=2)
fig.tight_layout();fig.savefig(FIG/'volume_weights.pdf');plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(7,2.6))
for ax,metric in zip(axes,['boundary','v2','v1']):
    for sc,col in [('zeros','#3274a1'),('mixed','#e1812c')]:
        methods=['CLR-e4','CLR-e3','CLR-e2']
        data=[entry(sc,3,m,metric) for m in methods]
        ax.errorbar([1e-4,1e-3,1e-2],[r['mean'] for r in data],yerr=[r['half'] for r in data],
                    fmt='o-',color=col,ms=3,label=SC[sc],capsize=2)
    ax.set_xscale('log');ax.set_xlabel(r'Smoothing $\epsilon$')
    ax.set_ylabel({'boundary':'Boundary coverage','v2':r'$V_2$','v1':r'$V_1$'}[metric])
axes[0].legend(frameon=False,fontsize=8)
fig.tight_layout();fig.savefig(FIG/'smoothing.pdf');plt.close(fig)

print(summary[(summary.k==3)&(summary.method.isin(['H','H-Z','H-GZ','H-group','Oracle']))&
              (summary.metric.isin(['coverage','boundary','vmix']))].to_string(index=False))
print('All figures, tables, and result macros generated from final runs.csv.')
