"""Generate every empirical table, figure and numeric macro in the paper."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .attacks import RULES, aggregate
from .run_experiments import load, SEED

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
GEN = ROOT / "paper/generated"
FIG = ROOT / "paper/figures"
LABEL = dict(mean="Mean", median="Median", geometric="Geometric", minimum="Minimum")
DS = dict(helm="HELM--MMLU", oll="Open LLM", oll_raw="Open LLM (raw)", oll_all_entries="Open LLM (all entries)")
CAP = dict(perfect="Unit", observed="Observed")
COLOR = dict(mean="#0072B2", median="#D55E00", geometric="#009E73", minimum="#CC79A7")

def tex_table(name, columns, rows, align=None):
    align = align or ("l" + "r"*(len(columns)-1))
    s = "\\begin{tabular}{"+align+"}\n\\toprule\n" + " & ".join(columns)+" \\\\\n\\midrule\n"
    s += "\n".join(" & ".join(map(str,r))+" \\\\" for r in rows)
    s += "\n\\bottomrule\n\\end{tabular}\n"
    (GEN / f"{name}.tex").write_text(s)

def esc(s):
    return str(s).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")

def group_range(values, organizations, rng, b=2000):
    groups = pd.DataFrame(dict(v=values, g=organizations)).groupby("g").v.agg(["sum", "count"])
    idx = rng.integers(len(groups), size=(b, len(groups)))
    boot = groups['sum'].values[idx].sum(axis=1)/groups['count'].values[idx].sum(axis=1)
    return np.quantile(boot, [.025, .975])

def main():
    GEN.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":9,
                         "axes.spines.top":False,"axes.spines.right":False,
                         "pdf.fonttype":42, "savefig.bbox":"tight"})
    s = pd.read_csv(OUT/"support.csv")
    mass = pd.read_csv(OUT/"mass.csv")
    base = s.query("common and margin==0 and rho==1")
    rng = np.random.default_rng(SEED+2)
    numbers={}; summary={}
    def number(name, value, fmt=".1f"):
        numbers[name] = format(value, fmt)
    audit=json.loads((OUT/"data_audit.json").read_text())
    number("HelmN",audit['helm_shape'][0],"d");number("HelmD",audit['helm_shape'][1],"d")
    number("OllN",audit['oll_shape'][0],"d");number("OllD",audit['oll_shape'][1],"d")
    number("OllRawN",load('oll')[1]['raw_rows'],"d");number("OllDuplicates",audit['oll_duplicate_names_removed'],"d")
    number("OllFlagged",audit['oll_flagged'],"d")
    support_rows=[]; mass_rows=[]; uncertainty=[]; cohort=[]; tie=[]
    for dataset in ["helm","oll"]:
        fr,md=load(dataset); d=fr.shape[1]
        z=base.query("dataset==@dataset and cap=='perfect'")
        number("HelmCommon" if dataset=="helm" else "OllCommon",z.model.nunique(),"d")
        for cap in ["perfect","observed"]:
            z=base.query("dataset==@dataset and cap==@cap")
            p=z.pivot(index="model",columns="rule",values="k")
            q=mass.query("dataset==@dataset and cap==@cap and common").pivot(index="model",columns="rule",values="mass")
            less=(p['median']<p['mean']).mean(); more=(p['median']>p['mean']).mean()
            support_rows.append([DS[dataset],CAP[cap]]+[f"{p[r].mean():.2f}" for r in RULES]+[f"{100*less:.1f}",f"{100*more:.1f}"])
            mass_rows.append([DS[dataset],CAP[cap]]+[f"{100*q[r].mean():.2f}" for r in RULES]+[f"{100*(q['median']<q['mean']-1e-12).mean():.2f}"])
            stem=("Helm" if dataset=="helm" else "Oll")+("Unit" if cap=="perfect" else "Observed")
            for r in RULES:
                number(stem+LABEL[r]+"K",p[r].mean(),".2f")
                number(stem+LABEL[r]+"Mass",100*q[r].mean(),".2f")
            number(stem+"MedLess",100*less);number(stem+"MedMore",100*more)
            number(stem+"MassLess",100*(q['median']<q['mean']-1e-12).mean(),".2f")
            number(stem+"OneMean",100*(p['mean']<=1).mean())
            number(stem+"OneMedian",100*(p['median']<=1).mean())
            groups=[md['organization'][m] for m in p.index]
            delta=(p['median']-p['mean']).values/d
            lo,hi=group_range(delta,groups,rng)
            task=pd.read_csv(OUT/'task_bootstrap.csv').query('dataset==@dataset and cap==@cap')
            tlo,thi=task.mean_delta_fraction.quantile([.025,.975])
            uncertainty.append([DS[dataset],CAP[cap],f"{100*delta.mean():.2f}",
                                f"[{100*lo:.2f}, {100*hi:.2f}]", f"[{100*tlo:.2f}, {100*thi:.2f}]"])
            summary[stem]=dict(n=len(p), d=d, mean_support=p.mean().to_dict(),
                median_support=p.median().to_dict(), mean_mass=q.mean().to_dict(),
                median_cheaper_fraction=float(less), median_costlier_fraction=float(more),
                delta_fraction=float(delta.mean()),organization_range=[float(lo),float(hi)],
                task_range=[float(tlo),float(thi)],organizations=len(set(groups)))
            rank=z.drop_duplicates('model').set_index('model').mean_rank
            target=p.loc[rank[rank<=int(np.ceil(.2*len(fr)))].index]
            cohort.append([DS[dataset]+" top 20\\%",CAP[cap],len(target),
                            f"{target['mean'].mean():.2f}",f"{target['median'].mean():.2f}",
                            f"{100*(target['median']<target['mean']).mean():.1f}"])
            strict=s.query("dataset==@dataset and cap==@cap and rho==1 and margin==0.000001 and common").pivot(index='model',columns='rule',values='k')
            tie.append([DS[dataset],CAP[cap],sum((strict!=p).any(axis=1)),
                        f"{strict['mean'].mean():.2f}",f"{strict['median'].mean():.2f}",
                        f"{100*(strict['median']<strict['mean']).mean():.1f}"])
    tex_table("support",["Panel","Ceiling","Mean","Median","Geom.","Min.",r"$K_{\rm med}<K_{\rm mean}$ (\%)",r"$>$ (\%)"],support_rows,"llrrrrrr")
    tex_table("mass",["Panel","Ceiling","Mean","Median","Geom.","Min.",r"$C_{\rm med}<C_{\rm mean}$ (\%)"],mass_rows,"llrrrrr")
    tex_table("uncertainty",["Panel","Ceiling",r"$100\overline{\Delta K/d}$","Owner reweighting","Task resampling"],uncertainty,"llrrr")
    for dataset in ["oll_raw","oll_all_entries"]:
        for cap in ['perfect','observed']:
            p=base.query('dataset==@dataset and cap==@cap').pivot(index='model',columns='rule',values='k')
            cohort.append([DS[dataset],CAP[cap],len(p),f"{p['mean'].mean():.2f}",f"{p['median'].mean():.2f}",f"{100*(p['median']<p['mean']).mean():.1f}"])
            if dataset=='oll_raw' and cap=='observed':
                number('OllRawObservedMedLess',100*(p['median']<p['mean']).mean())
    tex_table("cohorts",["Panel / cohort","Ceiling","Targets","Mean $K$","Median $K$",r"Median cheaper (\%)"],cohort,"llrrrr")
    tex_table("ties",["Panel","Ceiling","Any $K$ changed","Mean $K$","Median $K$",r"Median cheaper (\%)"],tie,"llrrrr")
    # Source and incumbent audit.
    leader_rows=[]
    for dataset in ['helm','oll']:
        fr,_=load(dataset)
        for rule in RULES:
            scores=pd.Series(aggregate(fr.values,rule),index=fr.index)
            best=scores.max(); winners=scores.index[scores>=best-1e-12].tolist()
            leader_rows.append([DS[dataset],LABEL[rule],f"{best:.6f}",esc(', '.join(winners))])
    tex_table("leaders",["Panel","Rule","Maximum","Entry / model"],leader_rows,"llrp{6.1cm}")
    b=pd.read_csv(OUT/"baselines.csv")
    baseline_rows=[]
    for dataset in ['helm','oll']:
        for cap in ['perfect','observed']:
            for rule in RULES:
                z=b.query('dataset==@dataset and cap==@cap and rho==1 and rule==@rule')
                opt=base.query('dataset==@dataset and cap==@cap and rule==@rule').k.mean()
                se=float(np.sqrt((z.random_mean_k_se**2).sum())/len(z))
                random_label=(f"${z.random_mean_k.mean():.2f}\\pm{se:.2f}$" if dataset=='helm' else f"{z.random_mean_k.mean():.2f}")
                baseline_rows.append([DS[dataset],CAP[cap],LABEL[rule],f"{opt:.2f}",f"{z.weak_k.mean():.2f}",random_label])
                if dataset=='helm' and cap=='observed' and rule=='median':
                    number('HelmObservedMedianWeakK',z.weak_k.mean(),'.2f')
    tex_table("baselines",["Panel","Ceiling","Rule","Optimal","Lowest first","Random order"],baseline_rows,"lllrrr")
    w=pd.read_csv(OUT/'weighting.csv');wr=[]
    for cap in ['perfect','observed']:
        p=w.query('rho==1 and cap==@cap').pivot(index='model',columns='weighting',values='k')
        # Common nonleaders under macro and micro for this sensitivity only.
        z=w.query('rho==1 and cap==@cap'); score=z.pivot(index='model',columns='weighting',values='baseline')
        keep=(score<score.max(axis=0)-1e-12).all(axis=1);p=p.loc[keep]
        wr.append([CAP[cap],len(p),f"{p.macro.mean():.2f}",f"{p.micro.mean():.2f}",f"{100*(p.macro!=p.micro).mean():.1f}"])
    tex_table('weighting',['Ceiling','Targets','Macro mean $K$','Micro mean $K$',r'Different $K$ (\%)'],wr,'lrrrr')

    # Figure 1: finite-census vulnerability curves, both ceiling models.
    fig,axes=plt.subplots(2,2,figsize=(6.6,4.5),sharex='row',sharey=True)
    for i,dataset in enumerate(['helm','oll']):
        for j,cap in enumerate(['perfect','observed']):
            ax=axes[i,j];z=base.query('dataset==@dataset and cap==@cap'); d=int(z.d.iloc[0])
            for rule in RULES:
                k=z[z.rule==rule].k.values
                budget=np.arange(d+1)
                ax.step(budget/d,[(k<=q).mean() for q in budget],where='post',label=LABEL[rule],color=COLOR[rule])
            ax.set_title(f"{DS[dataset].replace('--','–')}: {CAP[cap].lower()} ceiling")
            ax.grid(alpha=.15);ax.set_ylim(-.02,1.02);ax.set_xlim(0,1)
            if j==0:ax.set_ylabel('Fraction reaching first place')
            if i==1:ax.set_xlabel('Task budget / number of tasks')
    axes[0,0].legend(loc='lower right',fontsize=7)
    fig.tight_layout();fig.savefig(FIG/'frontiers.pdf');plt.close(fig)

    # Figure 2: full-budget feasibility as response strength varies.
    fig,axes=plt.subplots(1,2,figsize=(6.6,2.35),sharey=True)
    for ax,dataset in zip(axes,['helm','oll']):
        for cap in ['perfect','observed']:
            for rule in ['mean','median']:
                z=s.query('dataset==@dataset and cap==@cap and margin==0 and common')
                g=z.groupby('rho').apply(lambda a:(a.k<=a.d).mean(),include_groups=False)
                ax.plot(g.index,g.values,marker='o' if rule=='mean' else 's',markersize=3,
                        linestyle='-' if cap=='perfect' else '--',color=COLOR[rule],label=f'{LABEL[rule]}, {CAP[cap].lower()}')
        ax.set_title(DS[dataset].replace('--','–'));ax.grid(alpha=.15)
        ax.set_xlabel(r'Response strength $\rho$');ax.set_ylim(-.02,1.02)
    axes[0].set_ylabel('Feasible with all tasks');axes[1].legend(fontsize=6.7,loc='upper left')
    fig.tight_layout();fig.savefig(FIG/'reachability.pdf');plt.close(fig)

    # Figure 3: pointwise relation between support and continuous mass.
    fig,axes=plt.subplots(1,2,figsize=(6.6,2.35),sharey=True)
    for ax,dataset in zip(axes,['helm','oll']):
        z=mass.query("dataset==@dataset and cap=='perfect' and common")
        for rule in RULES:
            v=np.sort(z[z.rule==rule].mass.values)
            ax.step(100*v,np.arange(1,len(v)+1)/len(v),where='post',color=COLOR[rule],label=LABEL[rule])
        ax.set_xlabel('Average score increase (percentage points)')
        ax.set_xlim(left=0)
        ax.set_title(DS[dataset].replace('--','–'));ax.grid(alpha=.15)
    axes[0].set_ylabel('Fraction reaching first place');axes[1].legend(fontsize=7)
    fig.tight_layout();fig.savefig(FIG/'mass.pdf');plt.close(fig)

    # Figure 4 (appendix): paired support differences across task perturbations.
    tb=pd.read_csv(OUT/'task_bootstrap.csv')
    fig,axes=plt.subplots(1,2,figsize=(6.6,2.3),sharey=True)
    for ax,dataset in zip(axes,['helm','oll']):
        for cap,col in [('perfect','#4C78A8'),('observed','#F58518')]:
            v=100*tb.query('dataset==@dataset and cap==@cap').mean_delta_fraction.values
            ax.hist(v,bins=25,alpha=.55,label=CAP[cap],color=col)
        ax.axvline(0,color='k',linewidth=.7);ax.set_xlabel(r'$100\,\overline{(K_{\rm med}-K_{\rm mean})/d}$')
        ax.set_title(DS[dataset].replace('--','–'))
    axes[0].set_ylabel('Task resamples');axes[1].legend(fontsize=7)
    fig.tight_layout();fig.savefig(FIG/'task_perturbations.pdf');plt.close(fig)

    # Mixed overhead/mass objective: exact simultaneous minima for mean and odd median.
    mixed=[];crossovers=[]
    helm_d=load('helm')[0].shape[1]
    fig,ax=plt.subplots(figsize=(4.4,1.95))
    for cap,col in [('perfect','#4C78A8'),('observed','#F58518')]:
        p=base.query("dataset=='helm' and cap==@cap").pivot(index='model',columns='rule',values='k')
        q=mass.query("dataset=='helm' and cap==@cap and common").pivot(index='model',columns='rule',values='mass').loc[p.index]
        ds=(p['median']-p['mean']).values/helm_d
        dc=(q['median']-q['mean']).values
        vals=[]
        for lam in np.linspace(0,1,201):
            delta=lam*ds+(1-lam)*dc
            more=float((delta>1e-12).mean());less=float((delta<-1e-12).mean())
            vals.append(more)
            mixed.append(dict(cap=cap,lam=lam,median_more=more,median_less=less,mean_delta=float(delta.mean())))
        switch=(ds>0)&(dc<0)
        cs=-dc[switch]/(ds[switch]-dc[switch])
        # Draw the exact constant intervals, rather than rounding change points
        # to the saved diagnostic grid. Isolated equality points are step edges.
        edges=np.unique(np.r_[0.,cs,1.])
        mids=(edges[:-1]+edges[1:])/2
        heights=[float((lam*ds+(1-lam)*dc>1e-12).mean()) for lam in mids]
        ax.stairs(heights,edges,baseline=None,label=CAP[cap],color=col)
        for mid,val in zip(p.index[switch],cs):crossovers.append(dict(cap=cap,model=mid,crossover=float(val)))
        if cap=='perfect':
            number('MixedSwitchers',int(switch.sum()),'d')
            for name,val in zip(['MixedQOne','MixedMedian','MixedQThree'],np.quantile(cs,[.25,.5,.75])):
                number(name,val,'.3f')
    ax.set_ylim(-.02,1.02);ax.set_xlim(0,1);ax.grid(alpha=.15)
    ax.set_xlabel(r'Task-overhead weight $\lambda$');ax.set_ylabel('Median costs more (fraction)')
    ax.legend(fontsize=7,loc='upper left');fig.tight_layout();fig.savefig(FIG/'mixed_cost.pdf');plt.close(fig)
    pd.DataFrame(mixed).to_csv(OUT/'mixed_cost.csv',index=False,float_format='%.15g')
    pd.DataFrame(crossovers).to_csv(OUT/'mixed_crossovers.csv',index=False,float_format='%.15g')

    # Additional exact percentages used in narrative.
    for dataset in ['helm','oll']:
        stem='Helm' if dataset=='helm' else 'Oll'
        for cap in ['perfect','observed']:
            for rho in [.25,.5,.75]:
                for rule in ['mean','median']:
                    z=s.query('dataset==@dataset and cap==@cap and rho==@rho and margin==0 and common and rule==@rule')
                    name=stem+('Unit' if cap=='perfect' else 'Observed')+('Quarter' if rho==.25 else 'Half' if rho==.5 else 'ThreeQuarter')+LABEL[rule]+'Feasible'
                    number(name,100*(z.k<=z.d).mean())
    rt=json.loads((OUT/'runtime.json').read_text())
    number('RunWallSeconds',rt['wall_seconds'],'.1f');number('RunCpuSeconds',rt['process_cpu_seconds'],'.1f')
    number('RunPeakMiB',rt['peak_rss_kib']/1024,'.1f')
    wa=json.loads((OUT/'witness_audit.json').read_text());number('WitnessCases',wa['checked_cases'],'d')
    mf=json.loads((ROOT/'data/manifest.json').read_text());number('RawFiles',len(mf['files']),'d');number('RawMB',sum(e['bytes'] for e in mf['files'])/1e6,'.2f')
    macros='%% Generated by python -m src.report; do not edit empirical numbers.\n'
    macros+='\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in numbers.items())+'\n'
    (GEN/'numbers.tex').write_text(macros)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # Human-readable summary records all generated cells with units.
    pd.DataFrame(support_rows,columns=['panel','ceiling','mean_K','median_K','geometric_K','minimum_K','median_cheaper_pct','median_costlier_pct']).to_csv(OUT/'table_support.csv',index=False)
    pd.DataFrame(mass_rows,columns=['panel','ceiling','mean_C_pp','median_C_pp','geometric_C_pp','minimum_C_pp','median_cheaper_pct']).to_csv(OUT/'table_mass.csv',index=False)
    print(f'Generated {len(numbers)} numeric macros, tables and 5 figures')

if __name__=='__main__':
    main()
