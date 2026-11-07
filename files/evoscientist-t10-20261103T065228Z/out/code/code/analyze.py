"""Aggregate raw paired repetitions, MC uncertainty, all paper tables/figures.
python code/analyze.py. No fabricated/manual figure values.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'artifacts'; T=A/'tables';T.mkdir(exist_ok=True)
F=ROOT/'figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'serif','font.size':9,'axes.spines.top':False,
 'axes.spines.right':False,'pdf.use14corefonts':True,'ps.useafm':True,'savefig.bbox':'tight'})
LABELS={'linear':'Linear','nonlinear':'U-shaped','sharp':'Sharp U','anticorrelated':'Anticorr.',
 'uninformative':'No information','rare':'Rare','galaxies':'Galaxies','forest':'Forest','shift':'Shift'}


def wilson(k,n):
    p=k/n;z=norm.ppf(.975);den=1+z*z/n
    c=(p+z*z/(2*n))/den;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return c-h,c+h


def aggregate():
    summaries=[];ratios=[]
    for suite in ['main','ablation','exact']:
        for file in sorted((A/suite).glob('*.csv')):
            d=pd.read_csv(file)
            scenario=str(d.scenario.iloc[0]);n=int(d.n.iloc[0]);N=int(d.N.iloc[0]);R=int(d.rep.nunique())
            for method,g in d.groupby('method',sort=False):
                lo,hi=wilson(int(g.covered.sum()),R)
                width=float(g.width.mean());se=float(g.width.std(ddof=1)/np.sqrt(R))
                summaries.append(dict(suite=suite,scenario=scenario,n=n,N=N,R=R,method=method,
                 coverage=g.covered.mean(),coverage_lo=lo,coverage_hi=hi,width=width,width_se=se,
                 width_lo=width-1.96*se,width_hi=width+1.96*se,
                 bias=float((g.center-g.theta).mean()),rmse=float(np.sqrt(np.mean((g.center-g.theta)**2)))))
            pivot=d.pivot(index='rep',columns='method',values='width')
            refs=['LabelCP','EBLabel'] if suite=='exact' else ['PPI++','EBLabel','LabelCP']
            for ref in refs:
                if ref not in pivot:continue
                b=pivot[ref].to_numpy();bm=b.mean()
                for method in pivot:
                    x=pivot[method].to_numpy();ratio=x.mean()/bm
                    se=np.std(x-ratio*b,ddof=1)/(bm*np.sqrt(R))
                    diff=x-b;ds=diff.std(ddof=1)/np.sqrt(R)
                    z=diff.mean()/ds if ds>0 else 0.
                    ratios.append(dict(suite=suite,scenario=scenario,n=n,N=N,R=R,method=method,reference=ref,
                     ratio=ratio,ratio_lo=ratio-1.96*se,ratio_hi=ratio+1.96*se,
                     difference=diff.mean(),difference_se=ds,p_one_sided=float(norm.cdf(z))))
    s=pd.DataFrame(summaries);r=pd.DataFrame(ratios)
    s.to_csv(T/'summary.csv',index=False);r.to_csv(T/'paired_ratios.csv',index=False)
    tests=[]
    for suite,sc,method,ref in [('main','nonlinear','Series4','PPI++'),('exact','sharp','CPRectHist','LabelCP')]:
        sub=r[(r.suite==suite)&(r.scenario==sc)&(r.method==method)&(r.reference==ref)].copy()
        order=np.argsort(sub.p_one_sided.to_numpy());p=sub.p_one_sided.to_numpy();adjusted=np.empty(len(sub));last=0.
        for j,i in enumerate(order):
            last=max(last,(len(sub)-j)*p[i]);adjusted[i]=min(1,last)
        sub['p_holm']=adjusted;sub['family']=suite+'_'+sc;tests.append(sub)
    pd.concat(tests).to_csv(T/'primary_holm.csv',index=False)
    return s,r


def single(df,**kwargs):
    sub=df
    for k,v in kwargs.items():sub=sub[sub[k]==v]
    if len(sub)!=1:raise ValueError((kwargs,len(sub)))
    return sub.iloc[0]


def coverage_text(row,ci=False):
    return f'{100*row.coverage:.2f}' + (f' [{100*row.coverage_lo:.2f}, {100*row.coverage_hi:.2f}]' if ci else '')


def ratio_text(row):
    return f'{row.ratio:.3f} [{row.ratio_lo:.3f}, {row.ratio_hi:.3f}]'


def tables(s,r):
    lines=[r'\begin{tabular}{lrrrrr}',r'\toprule',
     r'Law & $R$ & PPI++ width & Series/PPI++ & PPI++ cover (\%) & Series cover (\%)\\',r'\midrule']
    for sc in ['linear','nonlinear','anticorrelated','uninformative','rare','galaxies','forest']:
        b=single(s,suite='main',scenario=sc,n=1000,N=10000,method='PPI++')
        c=single(s,suite='main',scenario=sc,n=1000,N=10000,method='Series4')
        rr=single(r,suite='main',scenario=sc,n=1000,N=10000,method='Series4',reference='PPI++')
        lines.append(f'{LABELS[sc]} & {b.R} & {b.width:.5f} & {ratio_text(rr)} & {coverage_text(b,True)} & {coverage_text(c,True)}'+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (T/'asymptotic.tex').write_text('\n'.join(lines))
    lines=[r'\begin{tabular}{lrrrrr}',r'\toprule',
     r'Law $(n,N)$ & Label CP width & Learned CP width & Width ratio & Label cover (\%) & Learned cover (\%)\\',r'\midrule']
    configs=[('sharp',200,2000),('sharp',1000,10000),('sharp',4000,40000),('sharp',1000,1000),
             ('nonlinear',1000,10000),('galaxies',1000,10000),('forest',1000,10000)]
    for sc,n,N in configs:
        b=single(s,suite='exact',scenario=sc,n=n,N=N,method='LabelCP')
        c=single(s,suite='exact',scenario=sc,n=n,N=N,method='CPRectHist')
        rr=single(r,suite='exact',scenario=sc,n=n,N=N,method='CPRectHist',reference='LabelCP')
        lines.append(f'{LABELS[sc]} ({n},{N}) & {b.width:.5f} & {c.width:.5f} & {ratio_text(rr)} & {coverage_text(b,True)} & {coverage_text(c,True)}'+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}']
    (T/'exact.tex').write_text('\n'.join(lines))
    # Compact no-information/rare/shift safety comparison, same main trials.
    lines=[r'\begin{tabular}{llrrr}',r'\toprule',r'Law & Method & Width & Coverage (\%) & Wilson 95\% MC interval\\',r'\midrule']
    for sc,n,N in [('rare',200,2000),('shift',1000,10000)]:
        for method in ['LabelWald','PPI++','Series4','LabelCP','EBHist4']:
            row=single(s,suite='main',scenario=sc,n=n,N=N,method=method)
            lines.append(f'{LABELS[sc]} & {method} & {row.width:.5f} & {100*row.coverage:.2f} & [{100*row.coverage_lo:.2f}, {100*row.coverage_hi:.2f}]'+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}'];(T/'safety.tex').write_text('\n'.join(lines))
    # Full appendix per-suite CSV is authoritative; readable selected-method tables.
    for suite in ['main','exact','ablation']:
        sub=s[s.suite==suite]
        keep={'main':['LabelWald','LabelCP','PPI','PPI++','Hist4','CFHist4','Series4','Oracle','EBLabel','EBRaw','EBLinear','EBHist4'],
              'exact':['LabelCP','CPRectRawFull','CPRectRawSplit','CPRectHist','LabelCPSplit','EBLabel','EBHist4'],
              'ablation':['CFHist1','CFHist2','CFHist4','CFHist8','CFHist16','Series1','Series2','Series4','Series8','Series16']}[suite]
        lines=[r'\begin{longtable}{llrrrrr}',r'\caption{'+suite.capitalize()+r' suite: measured widths and marginal coverage uncertainty.}\label{tab:full'+suite+r'}\\',
         r'\toprule Setting & Method & $R$ & Width & Width MC SE & Cover (\%) & Wilson interval\\\midrule\endfirsthead',
         r'\toprule Setting & Method & $R$ & Width & Width MC SE & Cover (\%) & Wilson interval\\\midrule\endhead']
        for (sc,n,N),group in sub.groupby(['scenario','n','N'],sort=False):
            for method in keep:
                gg=group[group.method==method]
                if not len(gg):continue
                row=gg.iloc[0]
                lines.append(f'{LABELS[sc]} {n}/{N} & {method} & {row.R} & {row.width:.6f} & {row.width_se:.6f} & {100*row.coverage:.2f} & [{100*row.coverage_lo:.2f}, {100*row.coverage_hi:.2f}]'+r'\\')
        lines += [r'\bottomrule',r'\end{longtable}']
        (T/f'full_{suite}.tex').write_text('\n'.join(lines))


def figures(s,r):
    # Main paired width ratios and marginal empirical coverage.
    fig,axs=plt.subplots(1,2,figsize=(7.0,2.7))
    scenarios=['linear','nonlinear','uninformative','galaxies','forest'];xx=np.arange(len(scenarios))
    colors=['#1778ad','#cb6b23','#22845c'];methods=['Series4','CFHist4','Hist4']
    for j,(method,color) in enumerate(zip(methods,colors)):
        rr=[single(r,suite='main',scenario=sc,n=1000,N=10000,method=method,reference='PPI++') for sc in scenarios]
        ys=np.array([x.ratio for x in rr]);lo=ys-np.array([x.ratio_lo for x in rr]);hi=np.array([x.ratio_hi for x in rr])-ys
        axs[0].errorbar(xx+(j-1)*.14,ys,yerr=[lo,hi],fmt='o',ms=4,capsize=2,color=color,label=method)
        ss=[single(s,suite='main',scenario=sc,n=1000,N=10000,method=method) for sc in scenarios]
        yy=np.array([x.coverage for x in ss]);lo=yy-np.array([x.coverage_lo for x in ss]);hi=np.array([x.coverage_hi for x in ss])-yy
        axs[1].errorbar(xx+(j-1)*.14,yy,yerr=[lo,hi],fmt='o',ms=4,capsize=2,color=color)
    axs[0].axhline(1,color='gray',ls='--',lw=1);axs[1].axhline(.95,color='gray',ls='--',lw=1)
    axs[0].set_ylabel('Mean width / PPI++');axs[1].set_ylabel('Coverage')
    for ax in axs:ax.set_xticks(xx,[LABELS[x] for x in scenarios],rotation=20);ax.grid(axis='y',alpha=.2)
    axs[0].legend(fontsize=7,frameon=False);axs[1].set_ylim(.90,.99);fig.tight_layout()
    fig.savefig(F/'main.pdf');fig.savefig(F/'main.png',dpi=220);plt.close(fig)
    # Exact, compared with strongest label-only CP; includes negative results.
    fig,axs=plt.subplots(1,2,figsize=(7.0,2.7))
    configs=[('sharp',200,2000),('sharp',1000,10000),('sharp',4000,40000),('nonlinear',1000,10000),('galaxies',1000,10000),('forest',1000,10000)]
    xx=np.arange(len(configs));labs=['Sharp 200','Sharp 1k','Sharp 4k','U-shaped','Galaxies','Forest']
    for j,(method,color) in enumerate(zip(['CPRectHist','CPRectRawFull','EBHist4'],colors)):
        rr=[single(r,suite='exact',scenario=sc,n=n,N=N,method=method,reference='LabelCP') for sc,n,N in configs]
        yy=np.array([x.ratio for x in rr]);lo=yy-np.array([x.ratio_lo for x in rr]);hi=np.array([x.ratio_hi for x in rr])-yy
        axs[0].errorbar(xx+(j-1)*.15,yy,yerr=[lo,hi],fmt='o',ms=4,capsize=2,color=color,label=method)
    axs[0].axhline(1,color='gray',ls='--',lw=1);axs[0].set_ylabel('Mean width / full-label CP');axs[0].set_xticks(xx,labs,rotation=25)
    axs[0].legend(fontsize=6.8,frameon=False)
    for method,color in zip(['CPRectHist','LabelCP'],['#1778ad','#333333']):
        ss=[single(s,suite='exact',scenario=sc,n=n,N=N,method=method) for sc,n,N in configs]
        yy=np.array([x.coverage for x in ss]);lo=yy-np.array([x.coverage_lo for x in ss]);hi=np.array([x.coverage_hi for x in ss])-yy
        axs[1].errorbar(xx,yy,yerr=[lo,hi],fmt='o',ms=4,capsize=2,color=color,label=method)
    axs[1].axhline(.95,color='gray',ls='--',lw=1);axs[1].set_xticks(xx,labs,rotation=25);axs[1].set_ylabel('Coverage');axs[1].set_ylim(.93,1.005);axs[1].legend(fontsize=7,frameon=False)
    for ax in axs:ax.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(F/'exact.pdf');fig.savefig(F/'exact.png',dpi=220);plt.close(fig)
    # Ablation basis dimension vs ratio; separate suites, no choosing best.
    fig,axs=plt.subplots(1,2,figsize=(7.0,2.5))
    for ax,sc in zip(axs,['linear','nonlinear']):
        for prefix,color in [('Series','#1778ad'),('CFHist','#cb6b23')]:
            B=[1,2,4,8,16]
            rr=[single(r,suite='ablation',scenario=sc,n=1000,N=10000,method=f'{prefix}{b}',reference='PPI++') for b in B]
            yy=np.array([x.ratio for x in rr]);lo=yy-np.array([x.ratio_lo for x in rr]);hi=np.array([x.ratio_hi for x in rr])-yy
            ax.errorbar(B,yy,yerr=[lo,hi],fmt='o-',ms=4,capsize=2,color=color,label=prefix)
        ax.axhline(1,color='gray',ls='--',lw=1);ax.set_xscale('log',base=2);ax.set_xticks([1,2,4,8,16],[1,2,4,8,16]);ax.set_xlabel('Bins B ('+LABELS[sc]+')');ax.set_ylabel('Mean width / PPI++');ax.legend(frameon=False,fontsize=8);ax.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(F/'ablation.pdf');fig.savefig(F/'ablation.png',dpi=220);plt.close(fig)
    # Finite pool ratio / sample size sensitivity with analytic oracle reference.
    from generators import oracle_variances
    fig,ax=plt.subplots(figsize=(3.4,2.4))
    ns=[200,1000,4000]
    for method,color in [('Series4','#1778ad'),('CFHist4','#cb6b23')]:
        rr=[single(r,suite='main',scenario='nonlinear',n=n,N=10*n,method=method,reference='PPI++') for n in ns]
        yy=np.array([x.ratio for x in rr]);ax.errorbar(ns,yy,yerr=[yy-np.array([x.ratio_lo for x in rr]),np.array([x.ratio_hi for x in rr])-yy],fmt='o-',color=color,label=method,capsize=2)
    v=oracle_variances('nonlinear',1000,10000);oracle=np.sqrt(v['v_oracle']/v['v_affine'])
    ax.axhline(oracle,color='black',ls=':',label='Analytic oracle');ax.set_xscale('log');ax.set_xticks(ns,ns);ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter());ax.set_xlabel('Labeled sample size n (N=10n)');ax.set_ylabel('Mean width / PPI++');ax.legend(frameon=False,fontsize=7);ax.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(F/'sensitivity.pdf');fig.savefig(F/'sensitivity.png',dpi=220);plt.close(fig)


def facts(s,r):
    """Measured macros ensure prose numbers have a traceable generated origin."""
    f={}
    for sc in ['linear','nonlinear','galaxies','forest','rare','uninformative','anticorrelated']:
        rr=single(r,suite='main',scenario=sc,n=1000,N=10000,method='Series4',reference='PPI++')
        c=single(s,suite='main',scenario=sc,n=1000,N=10000,method='Series4')
        f[sc+'_series_reduction_pct']=100*(1-rr.ratio)
        f[sc+'_series_coverage_pct']=100*c.coverage
    for n,N in [(200,2000),(1000,10000),(4000,40000),(1000,1000)]:
        rr=single(r,suite='exact',scenario='sharp',n=n,N=N,method='CPRectHist',reference='LabelCP')
        f[f'sharp_{n}_{N}_reduction_pct']=100*(1-rr.ratio)
        f[f'sharp_{n}_{N}_reduction_lo_pct']=100*(1-rr.ratio_hi)
        f[f'sharp_{n}_{N}_reduction_hi_pct']=100*(1-rr.ratio_lo)
    for method in ['PPI++','LabelWald','Series4','LabelCP','EBHist4']:
        row=single(s,suite='main',scenario='rare',n=200,N=2000,method=method)
        f['rare200_'+method+'_coverage_pct']=100*row.coverage
    f['main_repetitions']=sum(x['R'] for x in json.loads((A/'main'/'manifest.json').read_text()))
    f['ablation_repetitions']=sum(x['R'] for x in json.loads((A/'ablation'/'manifest.json').read_text()))
    f['exact_repetitions']=sum(x['R'] for x in json.loads((A/'exact'/'manifest.json').read_text()))
    (T/'facts.json').write_text(json.dumps(f,indent=2))
    macros={'NonlinearGain':f['nonlinear_series_reduction_pct'],'LinearGain':f['linear_series_reduction_pct'],
     'GalaxyGain':f['galaxies_series_reduction_pct'],'ForestGain':f['forest_series_reduction_pct'],
     'ExactGain':f['sharp_1000_10000_reduction_pct'],'ExactGainLo':f['sharp_1000_10000_reduction_lo_pct'],
     'ExactGainHi':f['sharp_1000_10000_reduction_hi_pct'],'RareCoverage':f['rare200_PPI++_coverage_pct']}
    (T/'macros.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+f'{v:.2f}'+'}' for k,v in macros.items()))
    return f

def analytic_diagnostics():
    z=norm.ppf(.975);zc=norm.ppf(1-.05/6);c=.8
    out={'normal_critical':float(z),'component_critical':float(zc),
         'rare200_zero_probability':.994**200,'rare200_coverage_ceiling':1-.994**200}
    for k in [1,10]:
        for e in [.005,.05]:
            out[f'cp_ratio_limit_eps{e}_k{k}']=float(zc/z*(np.sqrt(.25/k)+2*np.sqrt((e/2)*(1-e/2)/c))/.5)
        d=.5*z/zc-.5/np.sqrt(k)
        out[f'positive_threshold_eps_k{k}']=float(1-np.sqrt(1-c*d*d)) if d>0 else None
    (T/'analytic_diagnostics.json').write_text(json.dumps(out,indent=2))

if __name__=='__main__':
    s,r=aggregate();tables(s,r);figures(s,r);f=facts(s,r);analytic_diagnostics()
    print(json.dumps(f,indent=2))
