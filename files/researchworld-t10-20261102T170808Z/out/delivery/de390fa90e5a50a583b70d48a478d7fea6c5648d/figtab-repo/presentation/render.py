#!/usr/bin/env python3
"""Render paired fixed-input evidence. No experiments or inferential fits run here."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

NAMES = {
 'linear':'Linear', 'quadratic':'Quadratic', 'sigmoid':'Sigmoid', 'no_signal':'No signal',
 'heavy_tail':'Heavy-tailed noise', 'bernoulli_quadratic':'Quadratic Bernoulli',
 'rare_binary':'Rare Bernoulli', 'galaxies':'Galaxies', 'forest':'Forest',
 'alphafold':'AlphaFold', 'bounded_quadratic':'Bounded quadratic',
 'label':'Label only', 'ppi':'PPI', 'ppi++':'PPI++',
 'scalar_unclipped':'Unclipped scalar', 'cf_linear':'Cross-fit linear',
 'cf_cubic':'Cross-fit cubic', 'plugin_cubic':'Plug-in cubic',
 'cf_degree12':'Cross-fit degree 12', 'plugin_degree12':'Plug-in degree 12',
 'eb_label':'EB label only', 'eb_ppi_full':'EB PPI (all labels)',
 'eb_ppi':'EB PPI (split)', 'eb_scalar':'EB scalar', 'eb_cubic':'EB cubic',
 'clopper_pearson':'Clopper-Pearson'}
STYLE = {
 'label':('#777777','o','-'), 'ppi':('#999999','v',':'),
 'ppi++':('#222222','s','-'), 'scalar_unclipped':('#009E73','d','--'),
 'cf_linear':('#56B4E9','^','-.'), 'cf_cubic':('#D55E00','o','-'),
 'plugin_cubic':('#CC79A7','v',':'),
 'cf_degree12':('#0072B2','P','--'), 'plugin_degree12':('#CC79A7','X',':'),
 'eb_label':('#222222','s','-'), 'eb_ppi_full':('#0072B2','^','--'),
 'eb_scalar':('#009E73','d','-.'), 'eb_cubic':('#D55E00','o','-'),
 'clopper_pearson':('#CC79A7','x',':')}


SHORT={**NAMES,'scalar_unclipped':'Scalar (unclip.)','cf_linear':'CF linear','cf_cubic':'CF cubic','cf_degree12':'CF degree 12','plugin_cubic':'Plug-in cubic','plugin_degree12':'Plug-in degree 12','eb_ppi_full':'EB PPI (full)','clopper_pearson':'CP'}

def load(results):
    s = pd.read_csv(results/'summary.csv',keep_default_na=False)
    p = pd.read_csv(results/'paired.csv',keep_default_na=False)
    keys = ['scenario','n','N','method']
    assert not s.duplicated(keys).any(), 'Duplicate summary cells'
    assert not p.duplicated(keys+['baseline']).any(), 'Duplicate paired cells'
    assert (s.reps >= 2).all() and (s.hits.between(0,s.reps)).all()
    assert np.isfinite(s[['coverage','coverage_lo','coverage_hi','mean_width','width_mcse']]).all().all()
    assert (s.mean_width >= 0).all() and (s.width_mcse >= 0).all()
    assert np.allclose(s.coverage,s.hits/s.reps)
    assert (s.coverage_lo <= s.coverage).all() and (s.coverage <= s.coverage_hi).all()
    assert np.isfinite(p[['width_ratio','ratio_lo','ratio_hi']]).all().all()
    assert ((s.N == 10*s.n)|(s.N == s.n)).all(), 'Unexpected sample-size ratio'
    return s,p


def grid(s,p,scenarios,methods,baseline,out,width):
    """Rows expose regimes; columns keep coverage beside width for each regime."""
    fig,axes=plt.subplots(len(scenarios),2,figsize=(width,1.35*len(scenarios)+.72),squeeze=False)
    for row,scenario in enumerate(scenarios):
        a,b=axes[row]
        allcov=[]; allratio=[1.]
        for j,m in enumerate(methods):
            g=s[(s.scenario==scenario)&(s.method==m)].sort_values('n')
            if g.empty: raise ValueError(f'Missing {scenario}/{m}')
            color,marker,ls=STYLE[m]
            # Small log-scale horizontal offsets expose otherwise overlapping intervals.
            factor=np.exp((j-(len(methods)-1)/2)*.025)
            x=g.n.to_numpy()*factor
            a.errorbar(x,g.coverage,yerr=np.vstack([g.coverage-g.coverage_lo,g.coverage_hi-g.coverage]),color=color,marker=marker,ls=ls,ms=3,lw=.9,capsize=1.7)
            allcov.extend(g.coverage_lo); allcov.extend(g.coverage_hi)
            if m==baseline:
                continue
            q=p[(p.scenario==scenario)&(p.method==m)&(p.baseline==baseline)].sort_values('n')
            if len(q)!=len(g) or not np.array_equal(q.n,g.n):
                raise ValueError(f'Missing pairing {scenario}/{m}/{baseline}')
            assert np.array_equal(q.reps,g.reps)
            b.errorbar(q.n.to_numpy()*factor,q.width_ratio,yerr=np.vstack([q.width_ratio-q.ratio_lo,q.ratio_hi-q.width_ratio]),color=color,marker=marker,ls=ls,ms=3,lw=.9,capsize=1.7)
            allratio.extend(q.ratio_lo); allratio.extend(q.ratio_hi)
        a.axhline(.95,color='.45',lw=.7,ls=':',zorder=0)
        b.axhline(1,color='.45',lw=.7,ls=':',zorder=0)
        lower=min(.90,min(allcov)-.012)
        a.set_ylim(max(0,lower),min(1.005,max(.978,max(allcov)+.008)))
        a.set_ylabel(NAMES[scenario]+'\nCoverage')
        margin=max(.04,(max(allratio)-min(allratio))*.12)
        b.set_ylim(max(0,min(allratio)-margin),max(allratio)+margin)
        if max(allratio)>5*min(allratio) and min(allratio)>0:
            b.set_yscale('log'); b.set_ylim(min(allratio)*.8,max(allratio)*1.2)
        b.set_ylabel('Mean width ratio')
        for ax in (a,b):
            ax.set_xscale('log'); ax.set_xticks(sorted(g.n.unique()),[str(v) for v in sorted(g.n.unique())]); ax.minorticks_off()
            ax.grid(axis='y',color='.9',lw=.45); ax.spines[['top','right']].set_visible(False)
        if row==0:
            a.set_title('Coverage (95% Monte Carlo intervals)')
            b.set_title('Width relative to '+NAMES[baseline])
        if row==len(scenarios)-1:
            a.set_xlabel('Labeled sample size n'); b.set_xlabel('Labeled sample size n')
    handles=[Line2D([],[],color=STYLE[m][0],marker=STYLE[m][1],ls=STYLE[m][2],lw=.9,ms=3,label=NAMES[m]) for m in methods]
    fig.legend(handles=handles,loc='upper center',ncol=min(len(methods),4),frameon=False,bbox_to_anchor=(.52,1.002))
    fig.tight_layout(rect=(0,0,1,.935),h_pad=.7,w_pad=1.1)
    fig.savefig(str(out)+'.pdf',metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(str(out)+'.png',dpi=180)
    plt.close(fig)


def fmt(x,digits=3):
    return f'{x:.{digits}f}'


def sci(x):
    a,b=f'{x:.1e}'.split('e')
    return '$'+a+r'\times 10^{'+str(int(b))+'}$'


def mean_mcse(g):
    return f'{g.mean_width:.4g} ('+sci(g.width_mcse)+')'


def coverage(g):
    return f'{g.coverage:.3f} [{g.coverage_lo:.3f}, {g.coverage_hi:.3f}]'


def tex_table(path,columns,rows,align):
    lines=['% Generated by presentation/render.py; do not edit numeric values.',
           r'\begin{tabular}{'+align+'}',r'\toprule',
           ' & '.join(columns)+r' \\',r'\midrule']
    lines += [' & '.join(map(str,row))+r' \\' for row in rows]
    lines += [r'\bottomrule',r'\end{tabular}']
    path.write_text('\n'.join(lines)+'\n')


def main_table(s,p,out):
    rows=[]
    scenarios=['linear','quadratic','sigmoid','no_signal','heavy_tail','bernoulli_quadratic','rare_binary','galaxies','forest','alphafold']
    for scenario in scenarios:
        a=s[(s.scenario==scenario)&(s.n==2000)&(s.N==20000)&(s.method=='ppi++')].squeeze()
        b=s[(s.scenario==scenario)&(s.n==2000)&(s.N==20000)&(s.method=='cf_cubic')].squeeze()
        q=p[(p.scenario==scenario)&(p.n==2000)&(p.N==20000)&(p.method=='cf_cubic')&(p.baseline=='ppi++')].squeeze()
        if not isinstance(a,pd.Series) or not isinstance(b,pd.Series) or not isinstance(q,pd.Series):
            raise ValueError('Missing n=2000 main table cell '+scenario)
        rows.append([NAMES[scenario],coverage(a),coverage(b),f'{q.width_ratio:.5f} $\\pm$ {1.96*q.ratio_mcse:.5f}'])
    tex_table(out/'main_results.tex',['Regime','PPI++ coverage','Cubic coverage','Width ratio'],rows,'lrrr')


def finite_table(s,p,out):
    rows=[]
    sub=s[s.scenario=='bounded_quadratic']
    for n in sorted(sub.n.unique()):
        for m in ['eb_label','eb_ppi_full','eb_scalar','eb_cubic']:
            g=sub[(sub.n==n)&(sub.method==m)].squeeze()
            if not isinstance(g,pd.Series): raise ValueError('Missing finite-sample table cell')
            if m=='eb_label': ratio='1 (reference)'
            else:
                q=p[(p.scenario=='bounded_quadratic')&(p.n==n)&(p.method==m)&(p.baseline=='eb_label')].squeeze()
                ratio=f'{q.width_ratio:.5f} $\\pm$ {1.96*q.ratio_mcse:.5f}'
            rows.append([n,SHORT[m],coverage(g),mean_mcse(g),ratio])
    tex_table(out/'finite_results.tex',['$n$','Method','Coverage','Mean (MCSE)','Width / EB label'],rows,'rlrrr')


def binary_table(s,out):
    rows=[]
    for scenario in ['bernoulli_quadratic','rare_binary','galaxies','forest','alphafold']:
        for n in ([100,2000] if scenario=='rare_binary' else [2000]):
            for m in ['clopper_pearson','eb_label','eb_ppi_full','eb_scalar','eb_cubic']:
                g=s[(s.scenario==scenario)&(s.n==n)&(s.method==m)].squeeze()
                if not isinstance(g,pd.Series): raise ValueError('Missing binary comparator')
                rows.append([NAMES[scenario],n,SHORT[m],coverage(g),mean_mcse(g)])
    tex_table(out/'binary_results.tex',['Regime','$n$','Method','Coverage','Mean (MCSE)'],rows,'lrlrr')


def full_table(s,out):
    lines=[r'% Generated from every summary row by presentation/render.py.',
           r'Coverage intervals are two-sided 95\% Wilson Monte Carlo intervals. Width is the mean; MCSE is its Monte Carlo standard error. All methods receive the same inputs per draw. Target coverage is 95\%. CF denotes cross-fitting; CP denotes Clopper--Pearson. Coverage scope is given in the method definitions.']
    order=['linear','quadratic','sigmoid','no_signal','heavy_tail','bernoulli_quadratic','rare_binary','galaxies','forest','alphafold','bounded_quadratic']
    assert set(s.scenario)<=set(order), 'Unmapped regime in full appendix'
    methods=list(NAMES); count=0
    for scenario in order:
        g=s[s.scenario==scenario].copy()
        if g.empty: continue
        lines += [r'{\setlength{\tabcolsep}{3pt}\begin{longtable}{rrrlrrr}',
                  r'\caption{Complete results: '+NAMES[scenario]+r'.}\\',
                  r'\toprule $n$ & $N$ & $R$ & Method & Coverage [95\% MC] & Width & MCSE \\',
                  r'\midrule\endfirsthead',
                  r'\multicolumn{7}{l}{\textbf{'+NAMES[scenario]+r' (continued)}}\\',
                  r'\toprule $n$ & $N$ & $R$ & Method & Coverage [95\% MC] & Width & MCSE \\',
                  r'\midrule\endhead',r'\bottomrule\endfoot']
        g['method_order']=g.method.map(lambda x:methods.index(x) if x in methods else len(methods))
        for _,v in g.sort_values(['n','N','method_order']).iterrows():
            mean=f'{v.mean_width:.5g}'
            if 'e' in mean: mean=sci(v.mean_width)
            lines.append(f'{v.n} & {v.N} & {v.reps} & {SHORT[v.method]} & {coverage(v)} & {mean} & {sci(v.width_mcse)}'+r' \\')
            count+=1
        lines += [r'\end{longtable}}']
    assert count==len(s)
    (out/'full_results.tex').write_text('\n'.join(lines)+'\n')


def forest(s,p,conditions,methods,baseline,out,width):
    fig,(a,b)=plt.subplots(1,2,figsize=(width, .33*len(conditions)+.75),sharey=True)
    for i,(scenario,n,N,label) in enumerate(conditions):
        for j,m in enumerate(methods):
            g=s[(s.scenario==scenario)&(s.n==n)&(s.N==N)&(s.method==m)]
            if g.empty:
                if m=='clopper_pearson' and scenario=='bounded_quadratic': continue
                raise ValueError(f'Missing forest cell {scenario}/{n}/{m}')
            if len(g)!=1: raise ValueError('Nonunique forest cell')
            v=g.iloc[0]; color,marker,_=STYLE[m]; y=i+(j-(len(methods)-1)/2)*.105
            a.errorbar(v.coverage,y,xerr=[[v.coverage-v.coverage_lo],[v.coverage_hi-v.coverage]],color=color,marker=marker,ms=3.1,lw=.85,capsize=1.5)
            if m==baseline: continue
            q=p[(p.scenario==scenario)&(p.n==n)&(p.N==N)&(p.method==m)&(p.baseline==baseline)]
            if len(q)!=1: raise ValueError('Missing forest pairing')
            q=q.iloc[0]
            b.errorbar(q.width_ratio,y,xerr=[[q.width_ratio-q.ratio_lo],[q.ratio_hi-q.width_ratio]],color=color,marker=marker,ms=3.1,lw=.85,capsize=1.5)
    a.set_yticks(range(len(conditions)),[v[3] for v in conditions]); a.invert_yaxis()
    a.axvline(.95,color='.4',ls=':',lw=.7); b.axvline(1,color='.4',ls=':',lw=.7)
    a.set_xlabel('Coverage'); b.set_xlabel('Mean width / '+NAMES[baseline])
    a.set_title('Target: 95%'); b.set_title('Paired width comparison')
    for ax in (a,b):
        ax.grid(axis='x',color='.9',lw=.5); ax.spines[['top','right']].set_visible(False)
    a.set_xlim(min(.90,a.get_xlim()[0]-.01),1.005)
    handles=[Line2D([],[],color=STYLE[m][0],marker=STYLE[m][1],ls='',ms=4,label=NAMES[m]) for m in methods]
    fig.legend(handles=handles,loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.5,1.015))
    fig.tight_layout(rect=(0,0,1,.85 if len(methods)>3 else .91),w_pad=.8)
    fig.savefig(str(out)+'.pdf',metadata={'CreationDate':None,'ModDate':None}); fig.savefig(str(out)+'.png',dpi=180); plt.close(fig)


def main_comparison(s,p,out,width):
    conditions=[(d,2000,20000,NAMES[d]) for d in ['quadratic','sigmoid','linear','no_signal','galaxies','forest','alphafold']]
    conditions.append(('rare_binary',100,1000,'Rare Bernoulli (n=100)'))
    forest(s,p,conditions,['ppi++','scalar_unclipped','cf_cubic'],'ppi++',out,width)


def finite_comparison(s,p,out,width):
    conditions=[('bounded_quadratic',n,10*n,f'Bounded quad. (n={n:,})') for n in [2000,10000]]
    conditions += [(d,2000,20000,NAMES[d]) for d in ['bernoulli_quadratic','galaxies','forest','alphafold']]
    conditions.append(('rare_binary',100,1000,'Rare Bernoulli (n=100)'))
    forest(s,p,conditions,['eb_label','eb_ppi_full','eb_scalar','eb_cubic','clopper_pearson'],'eb_label',out,width)


def finite_n(s,p,results,out,width):
    fig,(a,b)=plt.subplots(1,2,figsize=(width,2.25))
    theory=pd.read_csv(results/'theory.csv',keep_default_na=False)
    for d,color,marker in [('quadratic','#D55E00','o'),('linear','#0072B2','s'),('no_signal','#009E73','^')]:
        g=s[(s.scenario==d)&(s.n==2000)&(s.method=='cf_cubic')].sort_values('N')
        q=p[(p.scenario==d)&(p.n==2000)&(p.method=='cf_cubic')&(p.baseline=='ppi++')].sort_values('N')
        x=g.N/g.n
        a.errorbar(x,g.coverage,yerr=[g.coverage-g.coverage_lo,g.coverage_hi-g.coverage],color=color,marker=marker,ms=4,lw=.9,capsize=2,label=NAMES[d])
        b.errorbar(q.N/q.n,q.width_ratio,yerr=[q.width_ratio-q.ratio_lo,q.ratio_hi-q.width_ratio],color=color,marker=marker,ms=4,lw=0,elinewidth=.9,capsize=2)
        t=theory[theory.scenario==d].sort_values('n_over_N',ascending=False)
        b.plot(1/t.n_over_N,t.oracle_width_ratio_to_scalar,color=color,ls='--',lw=.85)
    a.axhline(.95,color='.45',ls=':',lw=.7); a.set_ylim(.93,.98); a.set_ylabel('Cubic coverage')
    b.axhline(1,color='.45',ls=':',lw=.7); b.set_ylabel('Cubic mean width / PPI++')
    for ax in (a,b):
        ax.set_xscale('log'); ax.set_xticks([1,10],['1','10']); ax.minorticks_off(); ax.set_xlabel('Unlabeled/labeled ratio N/n'); ax.spines[['top','right']].set_visible(False)
    fig.legend(*a.get_legend_handles_labels(),loc='upper center',ncol=3,frameon=False)
    fig.tight_layout(rect=(0,0,1,.87),w_pad=.8)
    fig.savefig(str(out)+'.pdf',metadata={'CreationDate':None,'ModDate':None}); fig.savefig(str(out)+'.png',dpi=180); plt.close(fig)


def tail_table(results,out):
    t=pd.read_csv(results/'tail_diagnostics.csv',keep_default_na=False); rows=[]
    for d in ['quadratic','no_signal','galaxies','forest','alphafold']:
        for m in ['cf_cubic','cf_degree12','plugin_degree12']:
            g=t[(t.scenario==d)&(t.n==100)&(t.N==1000)&(t.method==m)].iloc[0]
            rows.append([NAMES[d],SHORT[m],f'{g.width_median:.3f}',f'{g.width_p99:.3f}',f'{g.width_max:.3f}'])
    tex_table(out/'fit_tails.tex',['Regime','Method','Median','99th percentile','Maximum'],rows,'llrrr')


def assumptions_table(out):
    rows=[
        ['Label/PPI/scalar Wald','Controls h=0, S, or aS; finite second moments; consistent variance and applicable normal limit.','Asymptotic'],
        ['Cross-fit fixed basis','Prespecified Legendre basis; fixed dimension; nonsingular covariance; consistent coefficients/variance; finite second moments.','Asymptotic'],
        ['Bounded EB label/PPI','$Y,S\in[0,1]$; known control range; independent common-population iid draws; stated error allocation.','Finite sample'],
        ['Trained scalar/cubic EB','As above, with training independent of evaluation labels and bounded clipped control.','Finite sample'],
        ['Clopper--Pearson','Binary iid labels from the target population. Uses no predictor.','Finite sample'],
    ]
    tex_table(out/'method_assumptions.tex',['Family','Additional conditions','Coverage scope'],rows,'@{}p{1.25in}p{2.9in}p{1.0in}@{}')



def theory_table(results,out):
    t=pd.read_csv(results/'theory.csv',keep_default_na=False); rows=[]
    for _,g in t.iterrows():
        rows.append([NAMES[g.scenario],f'{g.n_over_N:g}',fmt(g.oracle_width_ratio_to_scalar),fmt(g.oracle_width_ratio_to_label)])
    tex_table(out/'oracle_ratios.tex',['Regime','$n/N$','Oracle / scalar','Oracle / label'],rows,'lrrr')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--width',type=float,default=5.5)
    ap.add_argument('--source-revision',required=True)
    ap.add_argument('--theory-only',action='store_true')
    args=ap.parse_args()
    assert len(args.source_revision)==40, "Use the full source revision"
    figout=args.out/'figures'; tabout=args.out/'tables'; metaout=args.out/'presentation'
    for d in [figout,tabout,metaout]: d.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'font.family':'DejaVu Sans'})
    theory_table(args.results,tabout)
    sources=['theory.csv']
    if not args.theory_only:
        s,p=load(args.results)
        sources+=['summary.csv','paired.csv','tail_diagnostics.csv','coverage_diagnostics.csv']
        main_s=s[s.N==10*s.n]; main_p=p[p.N==10*p.n]
        grid(main_s,main_p,['quadratic','sigmoid','linear','no_signal'],['ppi++','scalar_unclipped','cf_linear','cf_cubic'],'ppi++',figout/'synthetic',args.width)
        grid(main_s,main_p,['heavy_tail','bernoulli_quadratic','rare_binary'],['label','ppi++','cf_cubic','cf_degree12'],'ppi++',figout/'stress',args.width)
        grid(main_s,main_p,['galaxies','forest','alphafold'],['label','ppi++','scalar_unclipped','cf_cubic'],'ppi++',figout/'real',args.width)
        grid(main_s,main_p,['bounded_quadratic'],['eb_label','eb_ppi_full','eb_scalar','eb_cubic'],'eb_label',figout/'finite',args.width)
        main_comparison(s,p,figout/'main_comparison',args.width)
        finite_comparison(s,p,figout/'finite_comparison',args.width)
        finite_n(s,p,args.results,figout/'finite_n',args.width)
        tail_table(args.results,tabout)
        assumptions_table(tabout)
        main_table(main_s,main_p,tabout); finite_table(s,p,tabout); binary_table(s,tabout); full_table(s,tabout)
        s.to_csv(tabout/'all_cells.csv',index=False)
        p.to_csv(tabout/'all_paired.csv',index=False)
    manifest={'source_repository':'world/experiment-repo','source_revision':args.source_revision,'inputs':{f:hashlib.sha256((args.results/f).read_bytes()).hexdigest() for f in sources},'width_inches':args.width,'python':platform.python_version(),'matplotlib':matplotlib.__version__,'numpy':np.__version__,'pandas':pd.__version__}
    (metaout/'render_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__': main()
