"""Render every manuscript figure from analyze.py CSVs; no new experiments."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from experiment import ROOT, METHODS
A=ROOT/'artifacts/analysis'; OUT=ROOT/'figures'; OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':9,'legend.fontsize':7,'axes.titlepad':8,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
agg=pd.read_csv(A/'summary_by_law.csv'); cells=pd.read_csv(A/'summary_cells.csv')
labels={'CLR-6':r'CLR $10^{-6}$','CLR-2':r'CLR $10^{-2}$','Coord':'Coordinate','Bonferroni':'Bonferroni','ScaledL2':'Scaled L2','MondrianL2':'Mondrian L2','WeightedL2':'Oracle weighted L2'}

def save(fig,name):
    fig.savefig(OUT/f'{name}.pdf'); fig.savefig(OUT/f'{name}.png',dpi=300); plt.close(fig)

def audit():
    z=agg[(agg.law=='zeros')&(agg.regime=='source')]; methods=METHODS[:-1]
    fig,axs=plt.subplots(1,2,figsize=(7,3.55),sharey=True,layout='constrained')
    for ax,metrics,legend in [(axs[0],['coverage','coverage_G1','coverage_B1'],['Marginal','Difficult group','Observed boundary']), (axs[1],['V','A_K','E_Q'],['Ambient mass','Supported-face mass','Mixed reference mass'])]:
        for j,(met,lab,col,marker) in enumerate(zip(metrics,legend,['#0072B2','#D55E00','#009E73'],['o','s','^'])):
            zz=z[z.metric==met].set_index('method').loc[methods]; x=zz['mean'].to_numpy(); y=np.arange(len(methods))+(j-1)*.21
            ax.errorbar(x,y,xerr=np.stack([x-zz.lo.to_numpy(),zz.hi.to_numpy()-x]),fmt=marker,color=col,ms=3.2,capsize=1.5,lw=.8,label=lab)
        ax.set_xlim(0,1.04); ax.set_xticks(np.arange(0,1.01,.2)); ax.grid(axis='x',alpha=.15); ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),frameon=False,handlelength=1,ncol=1)
    axs[0].set_yticks(np.arange(len(methods)),[labels.get(m,m) for m in methods]); axs[0].invert_yaxis(); axs[0].set_xlabel('Composition coverage (nominal 0.9)'); axs[1].set_xlabel('Normalized reference mass')
    axs[0].axvline(.9,color='0.4',ls='--',lw=.8)
    save(fig,'audit')

def shift():
    fig,axs=plt.subplots(1,2,figsize=(7,2.6),sharey=True)
    methods=['L2','ScaledL2','MondrianL2','WeightedL2','CLR-6']; colors=['#000000','#0072B2','#009E73','#D55E00','#CC79A7']; marks=['o','s','^','D','v']
    for ax,law,title in zip(axs,['interior','zeros'],['Interior law','Structural-zero mixture']):
        for j,(m,col,mk) in enumerate(zip(methods,colors,marks)):
            z=cells[(cells.regime=='shift')&(cells.law==law)&(cells.method==m)&(cells.metric=='coverage')].sort_values('K')
            xx=np.arange(3)+(j-2)*.055; yy=z['mean'].to_numpy()
            ax.errorbar(xx,yy,yerr=[yy-z.lo.to_numpy(),z.hi.to_numpy()-yy],label=labels.get(m,m),fmt=mk+'-',color=col,ms=3,lw=1,capsize=2)
        ax.axhline(.9,color='0.5',ls='--',lw=.8); ax.set_xticks(range(3),['3','5','10']); ax.set_xlabel('Number of components K'); ax.set_title(title); ax.set_ylim(.35,1.01); ax.grid(axis='y',alpha=.15)
    axs[0].set_ylabel('Shifted marginal coverage'); h,l=axs[0].get_legend_handles_labels(); fig.legend(h,l,loc='lower center',bbox_to_anchor=(.5,-.08),ncol=3,frameon=False)
    fig.tight_layout(rect=(0,.12,1,1)); save(fig,'shift')

def sensitivity():
    fig,ax=plt.subplots(figsize=(5.6,3.8)); z=agg[(agg.law=='zeros')&(agg.regime=='source')]
    colors=plt.get_cmap('tab10').colors
    for j,m in enumerate(METHODS[:-1]):
        zz=z[z.method==m].set_index('metric').loc[['E_rho25','E_Q','E_rho75']]; y=zz['mean'].to_numpy()
        ax.errorbar([.25,.5,.75],y,yerr=[y-zz.lo.to_numpy(),zz.hi.to_numpy()-y],fmt='o-',color=colors[j],label=labels.get(m,m),ms=3,lw=1,capsize=2)
    ax.set_xlabel(r'Full-simplex reference weight $\rho$'); ax.set_ylabel(r'Reference mass $E_{\rho}$'); ax.set_xlim(.2,.8); ax.set_ylim(0,1); ax.set_xticks([.25,.5,.75]); ax.grid(axis='y',alpha=.15)
    ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),frameon=False); fig.tight_layout(); save(fig,'sensitivity')

def strata():
    fig,ax=plt.subplots(figsize=(6.5,2.8))
    methods=['L2','ScaledL2','MondrianL2','CLR-6','CLR-2','Hellinger']; colors=['#000000','#0072B2','#009E73','#CC79A7','#E69F00','#D55E00']
    for j,(m,col) in enumerate(zip(methods,colors)):
        z=cells[(cells.regime=='source')&(cells.law=='zeros')&(cells.method==m)&(cells.metric=='coverage_B1')].sort_values('K'); y=z['mean'].to_numpy()
        ax.errorbar(np.arange(3)+(j-2.5)*.045,y,yerr=[y-z.lo.to_numpy(),z.hi.to_numpy()-y],fmt='o-',color=col,label=labels.get(m,m),ms=3,capsize=2,lw=1)
    ax.axhline(.9,color='0.5',ls='--',lw=.8); ax.set_xticks(range(3),['3','5','10']); ax.set_xlabel('Number of components K'); ax.set_ylabel('Observed-boundary coverage'); ax.set_ylim(0,1.01); ax.grid(axis='y',alpha=.15); ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),frameon=False); fig.tight_layout(); save(fig,'strata')

if __name__=='__main__':
    audit(); shift(); sensitivity(); strata()
    print('Generated audit, shift, sensitivity, strata: PDF + PNG from actual summaries.')
