#!/usr/bin/env python3
"""Render committed analysis summaries; no experiments are run here."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import numpy as np
import pandas as pd
from scipy.stats import beta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
D = pd.read_csv(ROOT/'presentation/inputs/synthetic-summary.csv')
NS = [16,32,64,128,256,512]
KS = [1,2,4,8,16,32,64,128]
RHOS = [0.,.5,.9]
METHODS = {
 'naive': ('Reused CP', '#D55E00', 'o', '-'),
 'simultaneous': ('Simultaneous CP', '#0072B2', 's', '--'),
 'independent_audit': ('Extra audit', '#009E73', '^', '-.'),
 'split_question_budget': ('Question split', '#CC79A7', 'D', ':'),
 'split_call_budget': ('Call split', '#6B5B00', 'v', (0,(5,1))),
}
plt.rcParams.update({'font.size':9,'axes.titlesize':9,'axes.labelsize':9,
 'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
 'font.family':'DejaVu Sans','pdf.fonttype':42,'ps.fonttype':42,
 'axes.spines.top':False,'axes.spines.right':False,'axes.axisbelow':True,
 'savefig.dpi':180,'lines.linewidth':1.25,'lines.markersize':3.5})


def select(metric, **kw):
    x=D[D.metric.eq(metric)]
    for k,v in kw.items(): x=x[x[k].eq(v)]
    return x


def interval(q, event=False):
    """95% marginal MC intervals: exact binomial or normal mean ±1.96 MCSE."""
    mu=q['mean'].to_numpy(); se=q.mcse.to_numpy()
    if not event: return mu-1.96*se,mu+1.96*se
    r=q.reps.to_numpy(); c=np.rint(mu*r).astype(int)
    assert np.max(np.abs(c-mu*r))<1e-6
    lo=np.zeros(len(q));hi=np.ones(len(q))
    a=c>0;lo[a]=beta.ppf(.025,c[a],r[a]-c[a]+1)
    a=c<r;hi[a]=beta.ppf(.975,c[a]+1,r[a]-c[a])
    return lo,hi


def curve(ax,q,x,color,marker,ls,label,event=False,scale=100):
    q=q.sort_values(x);lo,hi=interval(q,event)
    ax.plot(q[x],scale*q['mean'],color=color,marker=marker,ls=ls,label=label)
    ax.fill_between(q[x],scale*lo,scale*hi,color=color,alpha=.14,lw=0)


def logaxis(ax,which='k'):
    vals=KS if which=='k' else NS
    ax.set_xscale('log',base=2)
    shown=[1,4,16,128] if which=='k' else [16,32,128,512]
    ax.set_xticks(vals,labels=[str(v) if v in shown else '' for v in vals])
    ax.set_xlim(vals[0]*.9,vals[-1]*1.1)
    ax.grid(axis='y',color='#e4e4e4',lw=.5)
    ax.set_xlabel('Bank size K' if which=='k' else 'Questions n')


def save(fig,name):
    for ext in ['pdf','png']: fig.savefig(ROOT/f'figures/{name}.{ext}',facecolor='white')
    plt.close(fig)


def method_handles(keys):
    return [Line2D([],[],color=METHODS[k][1],marker=METHODS[k][2],ls=METHODS[k][3],label=METHODS[k][0]) for k in keys]


def selection():
    fig,axs=plt.subplots(2,3,figsize=(5.5,4.5),sharex=True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.11,top=.88,wspace=.34,hspace=.45)
    for j,rho in enumerate(RHOS):
        top,bottom=axs[:,j]
        top.set_title(f'({chr(97+j)}) ρ = {rho:g}')
        for n,color,marker,ls in [(32,'#762A83','o','-'),(128,'#9970AB','s','--'),(512,'#444444','^',':')]:
            curve(top,select('optimism_reused',n=n,rho=rho,spread=0),'k',color,marker,ls,f'n = {n}')
        top.axhline(0,color='0.5',lw=.7)
        top.set_ylim(-.6,27);top.set_yticks([0,10,20]);top.set_ylabel('Score optimism (pp)' if j==0 else '')
        bottom.set_title(f'({chr(100+j)}) n = 64')
        for key in ['naive','simultaneous','independent_audit']:
            label,color,marker,ls=METHODS[key]
            curve(bottom,select('coverage_'+key,n=64,rho=rho,spread=0),'k',color,marker,ls,label,event=True)
        bottom.axhline(95,color='0.3',ls=(0,(3,2)),lw=.8)
        bottom.set_ylim(0,101);bottom.set_yticks([0,25,50,75,95])
        bottom.set_ylabel('Coverage (%)' if j==0 else '')
        logaxis(top);top.set_xlabel('');logaxis(bottom)
    axs[0,0].legend(loc='upper left',frameon=False)
    fig.legend(handles=method_handles(['naive','simultaneous','independent_audit']),loc='upper center',bbox_to_anchor=(.5,.986),ncol=3,frameon=False)
    save(fig,'synthetic-selection')


def budgets():
    fig,axs=plt.subplots(2,3,figsize=(5.5,4.8),sharex=True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.19,top=.82,wspace=.34,hspace=.46)
    for j,rho in enumerate(RHOS):
        a,b=axs[:,j]
        a.set_title(f'({chr(97+j)}) ρ = {rho:g}')
        for key in METHODS:
            label,col,mark,ls=METHODS[key]
            curve(a,select('width_'+key,k=32,rho=rho,spread=.08),'n',col,mark,ls,label)
        a.set_ylim(0,85);a.set_yticks([0,20,40,60,80]);a.set_ylabel('Interval width (pp)' if j==0 else '')
        for key,metric in [('naive','selected_quality'),('split_question_budget','quality_split_question_budget'),('split_call_budget','quality_split_call_budget')]:
            label,col,mark,ls=METHODS[key]
            if key=='naive': label='Full search (3 methods)';col='#333333'
            curve(b,select(metric,k=32,rho=rho,spread=.08),'n',col,mark,ls,label)
        b.axhline(48,color='.5',lw=.7,ls='--')
        b.set_ylim(42,48.5);b.set_yticks([42,44,46,48])
        b.set_title(f'({chr(100+j)}) Selected quality')
        b.set_ylabel('Selected quality (%)' if j==0 else '')
        logaxis(a,'n');a.set_xlabel('');logaxis(b,'n')
    fig.legend(handles=method_handles(list(METHODS)),loc='upper center',bbox_to_anchor=(.5,.99),ncol=3,frameon=False)
    handles, labels = axs[1,0].get_legend_handles_labels()
    labels[0] = 'Full search quality'
    fig.legend(handles, labels, loc='lower center',bbox_to_anchor=(.5,.005),ncol=3,frameon=False,fontsize=8)
    save(fig,'synthetic-budgets')


def decisions():
    fig,axs=plt.subplots(1,3,figsize=(5.5,2.6),sharey=True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.23,top=.70,wspace=.30)
    for j,(ax,rho) in enumerate(zip(axs,RHOS)):
        for key in ['naive','simultaneous']:
            label,col,mark,ls=METHODS[key]
            curve(ax,select('false_superiority_'+key,n=512,rho=rho,spread=0),'k',col,mark,ls,label,event=True)
        ax.axhline(5,color='.3',ls=(0,(3,2)),lw=.8)
        ax.set_ylim(-.3,11.2);ax.set_yticks([0,5,10]);logaxis(ax)
        ax.set_title(f'({chr(97+j)}) ρ = {rho:g}')
    axs[0].set_ylabel('False-superiority frequency (%)')
    handles=method_handles(['naive','simultaneous'])+[Line2D([],[],color='.3',ls='--',lw=.8,label='5% frozen-pair error bound')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,1.),ncol=2,frameon=False)
    save(fig,'synthetic-decisions')


def heatmap(metric,name,label,cmap,vmin,vmax):
    fig,axs=plt.subplots(2,3,figsize=(5.5,4.8),sharex=True,sharey=True)
    fig.subplots_adjust(left=.11,right=.85,bottom=.12,top=.89,wspace=.18,hspace=.54)
    for i,spread in enumerate([0,.08]):
        for j,rho in enumerate(RHOS):
            ax=axs[i,j];q=select(metric,spread=spread,rho=rho)
            a=q.pivot(index='n',columns='k',values='mean').loc[NS,KS]
            im=ax.imshow(a.to_numpy()*100,origin='lower',aspect='auto',cmap=cmap,vmin=vmin,vmax=vmax,interpolation='nearest')
            ax.set_title(f'({chr(97+3*i+j)}) ρ = {rho:g}\nspread = {spread:g}')
            ax.set_xticks(range(len(KS)),labels=[str(v) if v in [1,4,16,128] else '' for v in KS]);ax.set_yticks(range(len(NS)),labels=NS)
            if i==1:ax.set_xlabel('Bank size K')
            if j==0:ax.set_ylabel('Questions n')
            if metric=='coverage_naive':
                # Mark cells whose complete marginal MC interval is below 95%.
                lo,hi=interval(q,event=True)
                for (_,row),u in zip(q.iterrows(),hi):
                    if u<.95:ax.plot(KS.index(int(row.k)),NS.index(int(row.n)),'.',color='white',ms=2.5)
    cax=fig.add_axes([.88,.16,.022,.65]);fig.colorbar(im,cax=cax,label=label)
    save(fig,name)


def mse():
    fig,axs=plt.subplots(2,3,figsize=(5.5,4.8),sharex=True,sharey=True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.12,top=.79,wspace=.34,hspace=.65)
    for i,spread in enumerate([0,.08]):
        for j,rho in enumerate(RHOS):
            ax=axs[i,j]
            for key,metric in [('naive','mse_reused'),('independent_audit','mse_independent_audit'),('split_question_budget','mse_split_question_budget'),('split_call_budget','mse_split_call_budget')]:
                label,col,mark,ls=METHODS[key];q=select(metric,k=32,rho=rho,spread=spread)
                curve(ax,q,'n',col,mark,ls,label,scale=10000)
            ax.set_yscale('log');ax.set_ylim(3,1700)
            ax.set_yticks([10,100,1000],labels=['10','100','1000'])
            ax.set_title(f'({chr(97+3*i+j)}) ρ = {rho:g}\nspread = {spread:g}')
            logaxis(ax,'n')
            if i==0:ax.set_xlabel('')
            if j==0:ax.set_ylabel('Score MSE (pp²)')
    fig.legend(handles=method_handles(['naive','independent_audit','split_question_budget','split_call_budget']),loc='upper center',bbox_to_anchor=(.5,.99),ncol=2,frameon=False)
    save(fig,'synthetic-mse')


def tables():
    records=[];tex=[]
    tex += [r'\begin{tabular}{lrrrrr}',r'\toprule',r'Report & Bias (pp) & Coverage (\%) & Width (pp) & Quality (\%) & Calls \\',r'\midrule']
    for n,k,rho,spread in [(64,16,.5,0.),(128,32,.5,.08)]:
        tex += [rf'\multicolumn{{6}}{{l}}{{\textit{{$n={n}, K={k}, \rho={rho:g}$; spread ${spread:g}$}}}} \\']
        def get(metric):
            q=select(metric,n=n,k=k,rho=rho,spread=spread)
            assert len(q)==1
            return float(q.iloc[0]['mean']),float(q.iloc[0].mcse)
        for key in METHODS:
            if key in ['naive','simultaneous']:bias='optimism_reused';quality='selected_quality';s=n;h=0
            elif key=='independent_audit':bias='bias_'+key;quality='selected_quality';s=n;h=n
            else:
                bias='bias_'+key;quality='quality_'+key
                s=n//2 if key=='split_question_budget' else max(1,n*k//(k+1));h=n-s if key=='split_question_budget' else n*k-s*k
            metrics={'bias':get(bias),'coverage':get('coverage_'+key),'width':get('width_'+key),'quality':get(quality)}
            row=dict(n=n,k=k,rho=rho,spread=spread,method=key,search_questions=s,audit_questions=h,model_calls=s*k+h)
            for metric,(mean,se) in metrics.items():row[metric+'_pp']=100*mean;row[metric+'_mcse_pp']=100*se
            records.append(row)
            formatted=[]
            for metric in ['bias','coverage','width','quality']:
                mean,se=metrics[metric]
                # Constant selected truth has no sampling variability.
                se=0 if abs(se)<1e-12 else se
                formatted.append(f'{100*mean:.2f} ({100*se:.3f})')
            tex += [METHODS[key][0]+' & '+' & '.join(formatted)+f' & {s*k+h:,}'+r' \\']
        tex += [r'\midrule']
    tex[-1]=r'\bottomrule';tex+=[r'\end{tabular}']
    (ROOT/'tables/synthetic-methods.tex').write_text('\n'.join(tex)+'\n')
    pd.DataFrame(records).to_csv(ROOT/'tables/synthetic-methods.csv',index=False,float_format='%.10g')
    # Preview the actual publication table source at 8 pt in a 5.5-inch text area.
    with tempfile.TemporaryDirectory(prefix='figtab-table-') as tmp:
        subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',
                        '-output-directory='+tmp,'presentation/table-preview.tex'],
                       cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
        shutil.copyfile(Path(tmp)/'table-preview.pdf',ROOT/'tables/synthetic-methods-preview.pdf')
        subprocess.run(['pdftoppm','-singlefile','-r','180','-png',
                        str(Path(tmp)/'table-preview.pdf'),str(Path(tmp)/'table-preview')],check=True)
        shutil.copyfile(Path(tmp)/'table-preview.png',ROOT/'tables/synthetic-methods-preview.png')



def validate():
    manifest=json.loads((ROOT/'presentation/provenance.json').read_text())
    for name,digest in manifest['sha256'].items():
        assert hashlib.sha256((ROOT/'presentation/inputs'/name).read_bytes()).hexdigest()==digest,name
    assert len(D)==288*25 and (D.reps==20000).all()
    assert not D.duplicated(['n','k','rho','spread','metric']).any()
    assert np.isfinite(D[['mean','mcse']].to_numpy()).all()
    assert (D.mcse>=0).all()
    for metric in D.metric.unique():
        assert len(select(metric))==288
        if metric.startswith(('coverage_','false_superiority_')):interval(select(metric),event=True)


if __name__=='__main__':
    validate()
    selection();budgets();decisions()
    heatmap('optimism_reused','synthetic-optimism-grid','Mean optimism (pp)','magma',-.2,33)
    heatmap('coverage_naive','synthetic-coverage-grid','Naive interval coverage (%)','viridis',0,100)
    mse();tables()
    print('Rendered 6 figures and 1 table from verified committed inputs.')
