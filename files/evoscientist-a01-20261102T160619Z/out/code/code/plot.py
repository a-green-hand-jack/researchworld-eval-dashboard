#!/usr/bin/env python3
"""Publication plots from saved CSVs only; also emit PNGs and editable vector PDFs."""
from pathlib import Path
import json,argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/figures'
COL={'mean':'#0072B2','median':'#D55E00','borda':'#009E73'}
plt.rcParams.update({'font.family':'serif','font.serif':['Times'],'font.sans-serif':['Helvetica'],'font.monospace':['Courier'],'text.usetex':True,'font.size':9,'axes.labelsize':9,'axes.titlesize':10,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.titlepad':8})

def finish(fig,name,spec):
    path=OUT/name;path.mkdir(parents=True,exist_ok=True)
    fig.savefig(path/'plot.pdf',bbox_inches='tight')
    # PDF uses LaTeX Type-1 fonts; PNG avoids a separate dvipng system dependency.
    with plt.rc_context({'text.usetex':False,'font.family':'DejaVu Serif','font.serif':['DejaVu Serif']}):
        for text in fig.findobj(matplotlib.text.Text):
            text.set_usetex(False);text.set_fontfamily('DejaVu Serif')
        fig.savefig(path/'plot.png',dpi=300,bbox_inches='tight')
    plt.close(fig)
    (path/'figure-spec.md').write_text('# Figure specification\n\n'+spec+'\n\nNumeric axes linear; mean blue, median vermilion, Borda green. All data from saved results; no fitted lines or invented values. PNG at 300 dpi; PDF vector.\n')
    (path/'plot.py').write_text("from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parents[3]\nsys.path.insert(0,str(ROOT/'code'))\nfrom plot import "+name+"\n"+name+"()\n")

def feasibility():
    fig,axes=plt.subplots(2,2,figsize=(7.0,4.5),sharex=True,sharey=True,layout='constrained')
    for row,name in enumerate(['helm','open_raw']):
        d=pd.read_csv(ROOT/f'artifacts/results_{name}.csv');m=int(d.m.iloc[0]);n=int(d.n.iloc[0])
        for col,rho in enumerate([.5,1.]):
            ax=axes[row,col]
            for rule in COL:
                k=d[(~d.strict)&(d.rho==rho)&(d.rule==rule)].K.to_numpy();bud=np.arange(n+1);rate=np.array([np.count_nonzero(k<=v)/m for v in bud]);assert np.all(np.diff(rate)>=0)
                ax.step(bud/n,rate,where='post',label=rule.capitalize(),color=COL[rule],lw=1.7)
            label='HELM (79 models, 57 subjects)' if name=='helm' else 'Open LLM (4,576 configurations, 6 tasks)'
            ax.set_title(label+'\n'+r'$\rho='+str(rho)+'$');ax.grid(axis='y',alpha=.22);ax.set_xlim(0,1);ax.set_ylim(0,1.02)
            if col==0:ax.set_ylabel('Fraction reaching shared first')
            if row==1:ax.set_xlabel('Allowed fraction of task edits (K/n)')
    axes[0,0].legend(loc='upper left',frameon=False)
    finish(fig,'feasibility','- chart_type: 2x2 step ECDF / all-target success curve\n- data_sources: results_helm.csv, results_open_raw.csv; shared first, rho=.5 and 1\n- x: allowed edited-task fraction, linear [0,1]\n- y: fraction of ALL targets attaining shared first within budget, linear [0,1.02]\n- infeasible cases: remain in denominator and never contribute\n- series: mean, median, Borda; one legend; no uncertainty (fixed cohort).')

def fixed_cohort():
    d=pd.read_csv(ROOT/'artifacts/fixed_cohort.csv');d=d[d.cohort=='triple'];fig,axes=plt.subplots(1,2,figsize=(7,2.5),sharey=True,layout='constrained')
    for ax,name,n in zip(axes,['helm','open_raw'],[57,6]):
        g=d[d.dataset==name].sort_values('rho')
        for rule in COL:
            col='mean_'+('median' if rule=='median' else rule)+'_K';ax.plot(g.rho,g[col]/n,'o-',lw=1.7,markersize=4,label=rule.capitalize(),color=COL[rule])
        ax.set_title(('HELM' if name=='helm' else 'Open LLM')+f': fixed N={int(g.targets.iloc[0]):,}');ax.set_xticks([.5,1.]);ax.set_xlim(.45,1.05);ax.set_ylim(0,1);ax.set_xlabel(r'Fraction of remaining headroom allowed ($\rho$)');ax.grid(axis='y',alpha=.22)
    axes[0].set_ylabel('Mean optimal edited-task fraction (K/n)');axes[0].legend(frameon=False,loc='upper right')
    finish(fig,'fixed_cohort','- chart_type: two-panel endpoint line comparison\n- data_sources: fixed_cohort.csv, triple cohort\n- rows: same jointly feasible, initially nonwinning targets selected at rho=.5; keep IDs at rho=1\n- x: rho=.5 and 1 (lines guide the eye, not interpolation claims)\n- y: mean optimal support fraction K/n, linear [0,1]\n- series: mean, median, Borda; bootstrap paired difference intervals in paper table, not pseudo training error bars here.')

def magnitude():
    d=pd.read_csv(ROOT/'artifacts/results_helm.csv');d=d[(~d.strict)&(d.rho==1)];k=d.pivot(index='i',columns='rule',values='K')/57;l=d.pivot(index='i',columns='rule',values='L1_min');r=d.pivot(index='i',columns='rule',values='rank');ids=r[(r[['mean','median']]>1).all(axis=1)].index
    fig,axes=plt.subplots(1,2,figsize=(7,2.7),layout='constrained')
    for ax,x,y,title,unit in [(axes[0],k.loc[ids,'mean'],k.loc[ids,'median'],'Task-count investment','K/n'),(axes[1],l.loc[ids,'mean'],l.loc[ids,'median'],'Magnitude investment','minimum L1 gain / n')]:
        limit=max(x.max(),y.max())*1.06;ax.scatter(x,y,s=17,alpha=.7,color='#0072B2',edgecolors='none');ax.plot([0,limit],[0,limit],ls='--',lw=1,color='0.4');ax.set_xlim(0,limit);ax.set_ylim(0,limit);ax.set_aspect('equal',adjustable='box');ax.set_xlabel('Mean rule: '+unit);ax.set_ylabel('Median rule: '+unit);ax.set_title(title);ax.grid(alpha=.15)
    finish(fig,'magnitude','- chart_type: two scatter panels with equality reference diagonal\n- data_sources: results_helm.csv, rho=1 shared first\n- rows: 77 targets initially nonwinning under both cardinal rules\n- left axes: mean-rule vs median-rule support K/n\n- right axes: separately optimized minimum normalized L1, not endpoint witness magnitude\n- all axes linear; equality diagonal specifically intended; no fit or confidence ellipse.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--figure',choices=['all','feasibility','fixed_cohort','magnitude'],default='all');args=p.parse_args()
    for name in ['feasibility','fixed_cohort','magnitude']:
        if args.figure in ['all',name]:globals()[name]()
if __name__=='__main__':main()
