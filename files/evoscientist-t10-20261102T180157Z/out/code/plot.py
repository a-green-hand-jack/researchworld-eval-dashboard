"""Render all manuscript figures from computed CSVs only."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
COLORS=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9','#777777']
ORDER=['linear','quadratic','step','null','rare','galaxies','forest']
LABELS=[s.capitalize() for s in ORDER]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'axes.titlesize':10,
                     'axes.spines.top':False,'axes.spines.right':False,'axes.titlepad':9,
                     'legend.fontsize':8,'savefig.dpi':300,'pdf.fonttype':42,
                     'pgf.texsystem':'pdflatex','pgf.rcfonts':False,
                     'pgf.preamble':r'\usepackage{mathptmx}'})
def save(fig,name):
    p=ROOT/'figures'/name;p.mkdir(exist_ok=True)
    fig.savefig(p/'plot.png',dpi=300,bbox_inches='tight')
    # PGF/pdflatex produces embedded Type1 fonts required by ICML template.
    fig.savefig(p/'plot.pdf',bbox_inches='tight',backend='pgf');plt.close(fig)
def main():
    s=pd.read_csv(ROOT/'results'/'all_summary.csv',keep_default_na=False)
    p=pd.read_csv(ROOT/'results'/'paired_comparisons.csv',keep_default_na=False)
    fig,axs=plt.subplots(1,2,figsize=(7.2,2.9),layout='constrained')
    for name,label,color,marker in zip(ORDER,LABELS,COLORS,['o','s','^','v','D','P','X']):
        a=s[(s.scenario==name)&(s.method=='cf_rich')&(s.grid=='core')].sort_values('n')
        axs[0].errorbar(a.n,a.width_ratio_ppipp,yerr=1.96*a.ratio_se,color=color,marker=marker,markersize=3,capsize=2,label=label,lw=1)
        b=p[(p.scenario==name)&(p.method=='cp_strat2')&(p.reference=='cp')&(p.ratio==10)&p.n.isin([100,500,2000])].sort_values('n')
        axs[1].errorbar(b.n,b.width_ratio,yerr=1.96*b.se,color=color,marker=marker,markersize=3,capsize=2,label=label,lw=1)
    for ax in axs:
        ax.set_xscale('log');ax.set_xticks([100,500,2000],['100','500','2000'])
        ax.set_xlabel('Labeled sample size n (N = 10n)');ax.axhline(1,color='black',ls='--',lw=.8)
        ax.grid(axis='y',alpha=.2)
    axs[0].set_title('(a) Asymptotic: CF-rich / PPI++')
    axs[1].set_title('(b) Finite-sample: stratified / labeled exact')
    axs[0].set_ylabel('Ratio of mean interval widths')
    handles,labels=axs[0].get_legend_handles_labels()
    fig.legend(handles,labels,ncol=7,loc='outside lower center',frameon=False)
    save(fig,'efficiency')
    methods=['ppipp','cf_rich','cp','cp_strat2']; names=['PPI++','CF-rich','Exact labeled','Exact 2-stratum']
    colors=['#0072B2','#D55E00','#009E73','#CC79A7']
    fig,axs=plt.subplots(1,3,figsize=(7.2,2.5),layout='constrained',sharey=True)
    for ax,scenario in zip(axs,['step','rare','forest']):
        for method,label,color in zip(methods,names,colors):
            a=s[(s.scenario==scenario)&(s.method==method)&(s.ratio==10)].sort_values('n')
            ax.errorbar(a.n,a.coverage,yerr=np.maximum(0,np.array([a.coverage-a.cov_lo,a.cov_hi-a.coverage])),color=color,label=label,lw=1,marker='o',markersize=3,capsize=2)
        ax.set_xscale('log');ax.axhline(.95,color='black',ls='--',lw=.8)
        ax.set_title(scenario.capitalize());ax.set_xlabel('Labeled sample size n');ax.grid(axis='y',alpha=.2)
        ax.set_ylim(.2,1.015)
        ticks=[30,100,500,2000] if scenario!='forest' else [100,500,2000]
        ax.set_xticks(ticks,[str(x) for x in ticks]);ax.tick_params(axis='x',labelsize=8)
    axs[0].set_ylabel('Repeated-sampling coverage');axs[0].legend(loc='lower right',frameon=False)
    save(fig,'validity')
    # All-cell coverage heatmap; no clustering or row selection.
    ms=['wald','ppi','ppipp','ppipp_pkg','cf_linear','cf_poly2','cf_rich','insample_rich','cp','cp_strat2','eb_labeled','eb_ppi','eb_select','oracle']
    cells=[]
    for name in ORDER:
        sub=s[s.scenario==name][['scenario','n','ratio']].drop_duplicates().sort_values(['n','ratio'])
        cells += list(sub.itertuples(index=False,name=None))
    matrix=[]
    for name,n,r in cells:
        sub=s[(s.scenario==name)&(s.n==n)&(s.ratio==r)].set_index('method')
        matrix.append([sub.loc[m,'coverage'] if m in sub.index else np.nan for m in ms])
    arr=np.array(matrix);fig,ax=plt.subplots(figsize=(8.4,9.2),layout='constrained')
    cmap=plt.cm.viridis.copy();cmap.set_bad('#cccccc')
    im=ax.imshow(arr,vmin=0,vmax=1,aspect='auto',cmap=cmap)
    ax.set_yticks(range(len(cells)),[f'{a}, n={b}, N/n={c}' for a,b,c in cells],fontsize=7)
    ax.set_xticks(range(len(ms)),[m.replace('_',' ') for m in ms],rotation=45,ha='right',fontsize=8)
    ax.set_title('All cells: empirical coverage (nominal 0.95)')
    cb=fig.colorbar(im,ax=ax,shrink=.65);cb.set_label('Coverage');cb.set_ticks([0,.25,.5,.75,.95,1])
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if np.isfinite(arr[i,j]):
                ax.text(j,i,f'{arr[i,j]:.2f}',ha='center',va='center',fontsize=5.5,color='black' if arr[i,j]>.6 else 'white')
    save(fig,'coverage_all')
if __name__=='__main__':main()
