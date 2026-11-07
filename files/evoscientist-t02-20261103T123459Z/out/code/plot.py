"""Generate paper figures from analyze.py outputs and actual per-update logs.
Curve bands are seed min--max, not confidence intervals; bars are95% intervals.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from analyze import ROOT, ci, curve, times

OUT=ROOT/'figures'
plt.rcParams.update({'font.size':8.5,'font.family':'DejaVu Sans','axes.spines.top':False,
                     'axes.spines.right':False,'axes.titlepad':8,'axes.labelsize':9,
                     'legend.fontsize':7,'figure.dpi':120,'savefig.dpi':300,
                     'pdf.fonttype':42,'ps.fonttype':42})
COLORS={32:'#440154',64:'#31688e',128:'#35b779',256:'#e6b42b'}


def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=300,bbox_inches='tight')
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)


def error(ax,x,obj,color,marker='o',label=None):
    ax.errorbar(x,obj['mean'],yerr=[[max(0.,obj['mean']-obj['lo'])],[max(0.,obj['hi']-obj['mean'])]],
                color=color,marker=marker,ms=4,capsize=2,lw=1,label=label)


def curves(ax,df,metric,color,label=None,clock=False,band=True,style='-'):
    curveset=[curve(r) for _,r in df.sort_values('seed').iterrows()]
    arr=np.stack([x[metric].to_numpy() for x in curveset])
    steps=curveset[0].step.to_numpy().astype(float)
    if clock:
        steps=steps*(-np.log1p(-.01*float(df.decay.iloc[0])))
    keep=steps>0
    ax.plot(steps[keep],arr.mean(0)[keep],color=color,lw=1.4,label=label,linestyle=style)
    if band:ax.fill_between(steps[keep],arr.min(0)[keep],arr.max(0)[keep],color=color,alpha=.12,lw=0)


def width(df):
    d=df[df.tag=='main']
    fig,axes=plt.subplots(1,2,figsize=(6.7,2.55),layout='constrained')
    for j,(key,color,label) in enumerate([('t_train','#3b6fb6','Train 99%'),('t_eval','#d86622','Held-out 99%')]):
        means=[]
        for h,g in d.groupby('width'):
            vals=times(g,key);xx=h*(1+(.09 if j else -.09))
            ev=g[key].notna().to_numpy()
            jitter=np.linspace(-.035,.035,len(g))
            axes[0].scatter(xx*(1+jitter[ev]),vals[ev],c=color,s=9,alpha=.6)
            axes[0].scatter(xx*(1+jitter[~ev]),vals[~ev],facecolors='none',edgecolors=color,s=18,marker='^')
            obj=ci(vals);error(axes[0],xx,obj,color,label=label if h==8 else None)
            means.append([xx,obj['mean']])
        m=np.array(means);axes[0].plot(m[:,0],m[:,1],color=color,lw=.8,alpha=.6)
    axes[0].axhline(19900,ls=':',c='.5',lw=.7)
    axes[0].set(xscale='log',yscale='log',xlabel='Hidden width h',ylabel='Restricted onset (updates)',ylim=(30,30000),title='(a) Interpolation and generalization')
    handles,labels=axes[0].get_legend_handles_labels()
    handles.append(Line2D([],[],color='.4',marker='^',markerfacecolor='none',linestyle='none',markersize=5))
    axes[0].legend(handles,labels+['Censored; onset unknown'],loc='lower left')
    for h,g in d.groupby('width'):
        axes[1].scatter(h*(1+np.linspace(-.05,.05,len(g))),g.final_eval_acc,s=12,alpha=.55,c='#d86622')
        error(axes[1],h,ci(g.final_eval_acc),'#d86622')
    axes[1].set(xscale='log',xlabel='Hidden width h',ylabel='Final held-out accuracy',ylim=(0,1.06),title='(b) Same 20,000-update budget')
    for ax in axes:
        ax.set_xscale('log',base=2)
        ax.set_xticks([8,16,32,64,128,256],labels=['8','16','32','64','128','256']);ax.grid(axis='y',alpha=.15)
    save(fig,'width')


def trajectories(df):
    fig,axes=plt.subplots(2,2,figsize=(6.7,4.1),layout='constrained')
    metrics=[('eval_acc','Held-out accuracy','linear'),('eval_loss','Held-out cross-entropy','log'),
             ('rule_energy_absolute','Nonconstant rule energy','log'),('residual_energy_absolute','Residual logit energy','log')]
    for ax,(metric,ylabel,yscale) in zip(axes.flat,metrics):
        for h in COLORS:
            d=df[(df.tag=='main')&(df.width==h)]
            curves(ax,d,metric,COLORS[h],f'h={h}',style={32:'-',64:'--',128:'-.',256:':'}[h])
        ax.set(xscale='log',yscale=yscale,xlabel='Gradient updates',ylabel=ylabel,xlim=(50,20000))
        ax.grid(alpha=.12)
        if metric=='eval_acc':ax.set_ylim(0,1.05);ax.legend(loc='lower right',ncol=2)
    for i,ax in enumerate(axes.flat):ax.set_title(f'({chr(97+i)}) '+['Prediction','Continuous loss','Oracle-aligned energy','Residual energy'][i])
    save(fig,'trajectories')


def clock(df):
    fig,axes=plt.subplots(2,2,figsize=(6.7,4.0),layout='constrained')
    cols={0:'#888888',.05:'#3b6fb6',.1:'#d86622',.2:'#389267'}
    for i,h in enumerate([32,128]):
        for wd in [0,.05,.1,.2]:
            d=df[(df.width==h)&(((df.tag=='main')&(df.decay==.1))|((df.tag=='decay')&(df.decay==wd)))]
            d=d[d.decay==wd]
            style={0:':',.05:'-',.1:'--',.2:'-.'}[wd]
            curves(axes[i,0],d,'eval_acc',cols[wd],f'λ={wd:g}',style=style)
            if wd:curves(axes[i,1],d,'eval_acc',cols[wd],f'λ={wd:g}',clock=True,style=style)
        axes[i,0].set(xscale='log',xlabel='Gradient updates',ylabel=f'h={h}: held-out accuracy',xlim=(50,20000),ylim=(0,1.05))
        axes[i,1].set(xlabel='Decay clock C = −t log(1−ηλ)',ylabel='Held-out accuracy',xlim=(0,10),ylim=(0,1.05))
        for ax in axes[i]:ax.grid(alpha=.12)
    axes[0,0].set_title('(a) Physical update time');axes[0,1].set_title('(b) Common clock horizon')
    axes[0,0].legend(loc='upper left',ncol=2)
    save(fig,'clock')


def normalization(df):
    fig,axes=plt.subplots(1,3,figsize=(6.7,2.3),layout='constrained')
    for i,(tag,col,label) in enumerate([('main','#3b6fb6','sqrt'),('mean','#d86622','mean'),('matched','#389267','matched mean')]):
        xs=[]; values=[[],[],[]]
        for h in [32,128]:
            d=df[(df.tag==tag)&(df.width==h)]; x=h*(1+(i-1)*.06);xs.append(x)
            for j,v in enumerate([d.initial_logit_rms,times(d,'t_eval'),d.final_eval_acc]):
                obj=ci(v);error(axes[j],x,obj,col,label=label if h==32 else None);values[j].append(obj['mean'])
        for j,ax in enumerate(axes):ax.plot(xs,values[j],color=col,lw=.7)
    for i,ax in enumerate(axes):
        ax.set_xscale('log',base=2);ax.set_xticks([32,128],labels=['32','128']);ax.set_xlabel('Width h');ax.grid(axis='y',alpha=.12)
        ax.set_title(['(a) Initial output scale','(b) Restricted 99% onset','(c) Final accuracy'][i])
    axes[0].set(yscale='log',ylabel='Centered logit RMS')
    axes[1].set(yscale='log',ylabel='Updates',ylim=(200,30000))
    axes[2].set(ylabel='Held-out accuracy',ylim=(0,1.05))
    axes[0].legend(loc='lower left',fontsize=6.4)
    save(fig,'normalization')


def controls(df):
    fig,axes=plt.subplots(1,2,figsize=(6.7,2.65),layout='constrained')
    categories=[('main',128,'Learned128'),('frozen',128,'Frozen128'),('shuffle',128,'Shuffled128'),
                ('capacitytrain',1024,'Learned1024'),('capacityfrozen',1024,'Frozen1024')]
    for i,(tag,h,label) in enumerate(categories):
        d=df[(df.tag==tag)&(df.width==h)]
        for ax,metric in zip(axes,['final_train_acc','final_eval_acc']):
            ax.scatter(i+np.linspace(-.08,.08,len(d)),d[metric],s=12,c='#3b6fb6',alpha=.5)
            error(ax,i,ci(d[metric]),'#3b6fb6')
    for ax in axes:
        ax.set(xticks=range(len(categories)),xticklabels=[v[2].replace('128','\n128').replace('1024','\n1024') for v in categories],ylim=(0,1.05),ylabel='Accuracy at 20,000 updates')
        ax.tick_params(axis='x',labelsize=7);ax.grid(axis='y',alpha=.12)
    axes[0].set_title('(a) Training');axes[1].set_title('(b) Held-out (shuffled arm: shuffled labels)')
    save(fig,'controls')


def robustness(df,groups):
    fig,axes=plt.subplots(1,2,figsize=(6.7,2.6),layout='constrained')
    tags=['main','middata','lowdata','modulus','subtract'];labels=['70%\ntrain','50%\ntrain','30%\ntrain','p=23','Subtract']
    for h,col in [(32,COLORS[32]),(128,COLORS[128])]:
        for i,tag in enumerate(tags):
            g=groups[(groups.tag==tag)&(groups.width==h)].iloc[0];d=df[(df.tag==tag)&(df.width==h)]
            x=i+(-.08 if h==32 else .08)
            error(axes[0],x,dict(mean=g.t_eval_events/8,lo=g.t_eval_wilson_lo,hi=g.t_eval_wilson_hi),col,label=f'h={h}' if i==0 else None)
            error(axes[1],x,ci(d.final_eval_acc),col)
    for ax in axes:
        ax.set(xticks=range(len(tags)),xticklabels=labels,ylim=(-.04,1.06));ax.grid(axis='y',alpha=.12)
    axes[0].set(ylabel='Sustained 99% event fraction',title='(a) Finite-budget transitions');axes[0].legend(loc='lower right')
    axes[1].set(ylabel='Final held-out accuracy',title='(b) Fixed-budget performance')
    save(fig,'robustness')


def main():
    OUT.mkdir(exist_ok=True)
    df=pd.read_csv(ROOT/'analysis/runs.csv');groups=pd.read_csv(ROOT/'analysis/groups.csv')
    width(df);trajectories(df);clock(df);normalization(df);controls(df);robustness(df,groups)
    print('Generated6 figures: PNG and PDF, from240 actual run logs.')

if __name__=='__main__':main()
