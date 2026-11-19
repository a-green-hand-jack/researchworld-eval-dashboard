"""Every paper table/figure is generated from stored repetition-level outputs."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results'; GEN=ROOT/'paper/generated';GEN.mkdir(exist_ok=True,parents=True)
NAMES={'linear_cont':'Linear, continuous','quadratic_cont':'Quadratic, continuous','linear_binary':'Linear, binary','quadratic_binary':'Quadratic, binary','threshold_binary':'Threshold, binary','null_binary':'Uninformative','binary_score':'Two-valued score','rare_binary':'Rare event','galaxies':'Galaxies','forest':'Forest','alphafold':'Protein disorder'}
ORDER=list(NAMES)
Z=norm.ppf(.975)

def wilson(k,n):
    p=k/n;den=1+Z**2/n;mid=(p+Z**2/(2*n))/den
    h=Z*np.sqrt(p*(1-p)/n+Z**2/(4*n*n))/den
    return mid-h,mid+h

def ratio_se(a,b):
    v=a.mean()/b.mean();se=np.std(a-v*b,ddof=1)/(np.sqrt(len(a))*b.mean())
    return v,se

def summarize():
    rows=[];metas=[];raw={}
    for f in sorted((RES/'raw').glob('*.json')):
        meta=json.loads(f.read_text());metas.append(meta)
        d=pd.read_csv(f.with_suffix('.csv.gz'));piv=d.pivot(index='rep',columns='method',values='width')
        raw[(meta['kind'],meta['case'],meta['n'],meta['N'])]=(meta,d,piv)
        for meth,g in d.groupby('method',sort=False):
            n=len(g);cl,ch=wilson(g.covered.sum(),n)
            row={k:meta[k] for k in ['kind','case','n','N','reps','seed','theta','seconds']}
            row.update(method=meth,coverage=g.covered.mean(),coverage_low=cl,coverage_high=ch,
                       width=g.width.mean(),width_se=g.width.std(ddof=1)/np.sqrt(n),
                       bias=((g.lo+g.hi)/2-meta['theta']).mean())
            for ref in ['PPI++','CF1','EB-label','EB-split1','Exact-binomial','CV1']:
                if ref not in piv:continue
                a,b=piv[meth].to_numpy(),piv[ref].to_numpy();ra,se=ratio_se(a,b)
                de=a-b
                lab=ref.replace('+','p').replace('-','_')
                row.update({f'ratio_{lab}':ra,f'ratio_{lab}_se':se,
                            f'diff_{lab}':de.mean(),f'diff_{lab}_se':de.std(ddof=1)/np.sqrt(n)})
            rows.append(row)
    df=pd.DataFrame(rows);df.to_csv(RES/'summary.csv',index=False)
    pd.DataFrame(metas).to_csv(RES/'cell_metadata.csv',index=False)
    return df,raw

def cell(df,case,n,method,ratio=10,kind=None):
    z=df[(df['case']==case)&(df.n==n)&(df.N==int(n*ratio))&(df.method==method)]
    if kind is not None:z=z[z.kind==kind]
    else:z=z[z.kind!='ablation']
    assert len(z)==1,(case,n,method,ratio,z)
    return z.iloc[0]

def covcompact(r):return f"{100*r.coverage:.2f} $\\pm$ {196*np.sqrt(r.coverage*(1-r.coverage)/r.reps):.2f}"

def cov(r):return f"{100*r.coverage:.2f} [{100*r.coverage_low:.2f}, {100*r.coverage_high:.2f}]"
def wi(r):
    e=1.96*r.width_se
    if e<1e-12:e=0.
    err=(f'{e:.5f}' if e>=.000005 or e==0 else f'{e:.1e}')
    return f"{r.width:.5f} $\\pm$ {err}"
def rat(r,ref='PPIpp'):
    v=r['ratio_'+ref]; e=1.96*r['ratio_'+ref+'_se']
    if e<1e-12:return f'{v:.3f}'
    if e<.00005:return f'{v:.4f} $\\pm$ {e:.1e}'
    dec=4 if 0<e<.0005 else 3
    return f"{v:.{dec}f} $\\pm$ {e:.{dec}f}"
def tab(path,cols,header,rows,small=True):
    s=('\\small\n' if small else '')+'\\begin{tabular}{'+cols+'}\n\\toprule\n'+header+' \\\\\n\\midrule\n'
    s+='\n'.join(' & '.join(row)+' \\\\' for row in rows)
    s+='\n\\bottomrule\n\\end{tabular}\n'
    if path in ['finite_all.tex','ablation.tex']:
        s=s.replace('tabular','longtable').replace('\\small','\\scriptsize')
        caption=('All finite-sample comparators; widths with 95\\% Monte Carlo errors, coverage with Wilson 95\\% intervals, and paired width ratios.' if path=='finite_all.tex' else 'All degree stress-test results; 5,000 repetitions per condition. Coverage intervals are Wilson 95\\% Monte Carlo intervals.')
        i=s.index('\\toprule\n');j=s.index('\\midrule\n')+len('\\midrule\n')
        block=s[i:j]
        s=s[:i]+'\\caption{'+caption+'}\\\\\n'+block+'\\endfirsthead\n'+block+'\\endhead\n'+s[j:]
        s='\\begingroup\n'+s+'\\endgroup\n'
    (GEN/path).write_text(s)

def tables(df):
    maincases=ORDER[:8]
    rows=[]
    for c in maincases:
        b=cell(df,c,800,'PPI++');a=cell(df,c,800,'CF3')
        rows.append([NAMES[c],covcompact(b),covcompact(a),rat(a),rat(a,'CF1')])
    tab('synthetic_main.tex','lrrrr','Law & PPI++ cov. (\\%) & CF3 cov. (\\%) & CF3/PPI++ & CF3/CF1',rows)
    rows=[]
    for c in ORDER[8:]:
        for n in [200,800]:
            b=cell(df,c,n,'PPI++');a=cell(df,c,n,'CF3')
            rows.append([NAMES[c],str(n),wi(b),covcompact(b),covcompact(a),rat(a)])
    tab('real_main.tex','llrrrr','Artifact & $n$ & PPI++ width & PPI++ cov. (\\%) & CF3 cov. (\\%) & CF3/PPI++ width',rows)
    rows=[]
    for c in ['quadratic_cont','null_binary','rare_binary']:
        for n in [200,800,3200,12800]:
            if not ((df['case']==c)&(df.n==n)&(df.N==10*n)).any():continue
            for m in (['Hoeffding']+(['Exact-binomial'] if c!='quadratic_cont' else [])+['EB-label','EB-raw','EB-split1','EB-split3']):
                a=cell(df,c,n,m)
                rows.append([NAMES[c] if m=='EB-label' else '',str(n) if m=='EB-label' else '',m,wi(a),cov(a),rat(a,'EB_label')])
    tab('finite_all.tex','lllrrr','Law & $n$ & Method & Width & Coverage (\\%) & Width / EB-label',rows)
    # Compact finite-sample primary table, at n=800 and large n.
    rows=[]
    for c in ['quadratic_cont','null_binary','rare_binary']:
        for n in [800,12800]:
            if not ((df['case']==c)&(df.n==n)&(df.N==10*n)).any():continue
            a=cell(df,c,n,'EB-split3');ref='EB-label' if c=='quadratic_cont' else 'Exact-binomial';b=cell(df,c,n,ref)
            rows.append([NAMES[c],str(n),wi(b),wi(a),covcompact(a),rat(a,ref.replace('-','_'))])
    tab('finite_main.tex','llrrrr','Law & $n$ & Baseline width & EB-split3 width & Cov. (\\%) & Width ratio',rows)
    # Full tables ensure every baseline, including adverse outcomes, remains inspectable.
    for n in [200,800]:
        rows=[]
        for c in ORDER:
            if not ((df['case']==c)&(df.n==n)&(df.N==10*n)).any():continue
            for m in ['Classical','PPI','PPI++','PPI++clip','CF1','CV3','CF3','Hoeffding','EB-label','EB-raw','EB-split1','EB-split3']+(['Exact-binomial'] if c not in ['linear_cont','quadratic_cont'] else []):
                a=cell(df,c,n,m)
                rows.append([NAMES[c] if m=='Classical' else '',m,wi(a),cov(a),rat(a)])
        # Split table per scenario to allow page breaks between artifacts.
        for c in ORDER:
            cr=[]
            for m in ['Classical','PPI','PPI++','PPI++clip','CF1','CV3','CF3','Hoeffding','EB-label','EB-raw','EB-split1','EB-split3']+(['Exact-binomial'] if c not in ['linear_cont','quadratic_cont'] else []):
                a=cell(df,c,n,m);cr.append([m,wi(a),cov(a),rat(a)])
            tab(f'full_{c}_{n}.tex','lrrr','Method & Width & Coverage (\\%) & Width / PPI++',cr)
    # Oracle variance checks, theoretical predictions vs actual cross-fit widths.
    rows=[]
    for c in ORDER[:8]:
        m=json.loads((RES/'raw'/f'synthetic_{c}_n800_r10.json').read_text())
        rho=10/11;v1=m['varY']-rho*m['explained1'];v3=m['varY']-rho*m['explained3'];vs=m['varY']-rho*m['varM']
        a=cell(df,c,800,'CF3')
        oracle_w=2*Z*np.sqrt(v3/800)
        rows.append([NAMES[c],f"{np.sqrt(v3/v1):.3f}",f"{np.sqrt(vs/v1):.3f}",f"{oracle_w:.5f}",wi(a)])
    tab('oracle.tex','lrrrr','Law & Cubic / linear oracle & All-score / linear bound & Cubic oracle width & CF3 width',rows)
    # Artifacts population projection headroom (descriptive only, not fit on full Y).
    rows=[]
    for c in ORDER[8:]:
        m=json.loads((RES/'raw'/f'real_{c}_n800_r10.json').read_text())
        ratio=np.sqrt((m['varY']-10/11*m['explained3'])/(m['varY']-10/11*m['explained1']))
        z=np.load(ROOT/'data'/f'{c}.npz')
        rows.append([NAMES[c],str(len(z['Y'])),f"{m['theta']:.6f}",f"{ratio:.4f}"])
    tab('artifacts.tex','lrrr','Artifact & Records & Empirical target & Cubic/linear oracle width',rows)
    if (df.kind=='ablation').any():
        rows=[]
        for c in ['linear_cont','quadratic_cont','null_binary']:
            for n in [50,200,800]:
                for deg in [1,2,3,7,15]:
                    a=cell(df,c,n,f'CV{deg}',kind='ablation')
                    rows.append([NAMES[c] if deg==1 else '',str(n) if deg==1 else '',str(deg),wi(a),cov(a),rat(a,'CV1')])
        tab('ablation.tex','lllrrr','Law & $n$ & Degree & Width & Coverage (\\%) & Width / degree one',rows)
    # Compute resources from run logs; main CPU counter is cumulative per worker.
    rr=[]
    for p in sorted((ROOT/'logs').glob('run_*.json')):
        z=json.loads(p.read_text())
        if z['suite']=='smoke':continue
        rr.append([z['suite'],str(len(z['tasks'])),str(z['reps']),f"{z['wall_seconds']:.1f}",f"{max(t['max_rss_kib'] for t in z['tasks'])/1024:.1f}"])
    tab('compute.tex','lrrrr','Suite & Cells & Repetitions/cell & Wall seconds & Max worker RSS (MiB)',rr)

def figures(df,raw):
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    cs=ORDER[:8];pos=np.arange(len(cs));methods=['PPI++','CF1','CV3','CF3'];colors=['#555555','#e69f00','#56b4e9','#0072b2']
    fig,axs=plt.subplots(2,1,figsize=(7.0,4.7),sharex=True)
    for j,(m,col) in enumerate(zip(methods,colors)):
        rr=[cell(df,c,800,m) for c in cs];x=pos+(j-1.5)*.16
        vals=np.array([r.coverage for r in rr]);low=np.array([r.coverage_low for r in rr]);high=np.array([r.coverage_high for r in rr])
        axs[0].errorbar(x,vals,yerr=[vals-low,high-vals],fmt='o',ms=3,capsize=2,color=col,label=m)
        ratios=np.array([r.ratio_PPIpp for r in rr]);se=np.array([r.ratio_PPIpp_se for r in rr])
        axs[1].errorbar(x,ratios,yerr=1.96*se,fmt='o',ms=3,capsize=2,color=col)
    axs[0].axhline(.95,ls='--',color='black',lw=.7);axs[1].axhline(1,ls='--',color='black',lw=.7)
    axs[0].set_ylabel('Coverage');axs[1].set_ylabel('Mean width / PPI++')
    axs[0].legend(ncol=4,loc='lower left',fontsize=8);axs[1].set_xticks(pos,['Linear\ncont.','Quadratic\ncont.','Linear\nbinary','Quadratic\nbinary','Threshold\nbinary','Null','Binary\nscore','Rare'])
    axs[0].set_ylim(.89,.975);axs[1].set_ylim(.25,1.13)
    fig.tight_layout();fig.savefig(GEN/'synthetic.pdf');plt.close(fig)
    if (df.kind=='ablation').any():
        fig,axs=plt.subplots(1,2,figsize=(6.8,2.5))
        for n,col in zip([50,200,800],['#d55e00','#0072b2','#009e73']):
            rr=[cell(df,'null_binary',n,f'CV{d}',kind='ablation') for d in [1,2,3,7,15]]
            axs[0].errorbar([1,2,3,7,15],[r.coverage for r in rr],yerr=np.array([[r.coverage-r.coverage_low for r in rr],[r.coverage_high-r.coverage for r in rr]]),fmt='o-',capsize=2,label=f'n={n}',color=col,ms=3)
            axs[1].errorbar([1,2,3,7,15],[r.ratio_CV1 for r in rr],yerr=[1.96*r.ratio_CV1_se for r in rr],fmt='o-',capsize=2,color=col,ms=3)
        axs[0].axhline(.95,ls='--',lw=.7,color='black');axs[1].axhline(1,ls='--',lw=.7,color='black')
        axs[0].set_ylabel('Coverage');axs[1].set_ylabel('Mean width / degree one');axs[0].legend(fontsize=8)
        for ax in axs:ax.set_xlabel('Legendre degree (null outcome)');ax.set_xticks([1,3,7,15])
        fig.tight_layout();fig.savefig(GEN/'ablation.pdf');plt.close(fig)
    # N/n sensitivity: oracle and actually observed ratios, include full n=800 main ratio10.
    fig,axs=plt.subplots(1,2,figsize=(6.8,2.6))
    for c,col in [('linear_cont','#e69f00'),('quadratic_cont','#0072b2'),('null_binary','#777777')]:
        rs=[r for r in [.25,1,4,10,40] if ((df['case']==c)&(df.n==800)&(df.N==int(800*r))&(df.kind=='synthetic')).any()]
        a=[cell(df,c,800,'CF3',r) for r in rs];b=[cell(df,c,800,'CF1',r) for r in rs]
        axs[0].errorbar(rs,[v.ratio_CF1 for v in a],yerr=[1.96*v.ratio_CF1_se for v in a],fmt='o-',label=NAMES[c],color=col,capsize=2,ms=3)
        axs[1].errorbar(rs,[v.coverage for v in a],yerr=np.array([[v.coverage-v.coverage_low for v in a],[v.coverage_high-v.coverage for v in a]]),fmt='o-',color=col,capsize=2,ms=3)
    axs[0].set_xscale('log');axs[1].set_xscale('log');axs[0].axhline(1,ls='--',lw=.7,color='black');axs[1].axhline(.95,ls='--',lw=.7,color='black')
    axs[0].set_ylabel('CF3 / CF1 mean width');axs[1].set_ylabel('CF3 coverage');axs[0].legend(fontsize=7)
    for ax in axs:ax.set_xlabel('Unlabeled / labeled sample size')
    fig.tight_layout();fig.savefig(GEN/'ratio.pdf');plt.close(fig)
    # Finite-sample tradeoff across n.
    fig,axs=plt.subplots(1,2,figsize=(6.8,2.6))
    for c,col in [('quadratic_cont','#0072b2'),('null_binary','#777777'),('rare_binary','#d55e00')]:
        ns=[n for n in [200,800,3200,12800] if ((df['case']==c)&(df.n==n)&(df.N==10*n)).any()]
        a=[cell(df,c,n,'EB-split3') for n in ns]
        axs[0].errorbar(ns,[v['ratio_EB_label' if c=='quadratic_cont' else 'ratio_Exact_binomial'] for v in a],yerr=[1.96*v['ratio_EB_label_se' if c=='quadratic_cont' else 'ratio_Exact_binomial_se'] for v in a],fmt='o-',capsize=2,label=NAMES[c],color=col,ms=3)
        axs[1].errorbar(ns,[v.coverage for v in a],yerr=np.array([[v.coverage-v.coverage_low for v in a],[v.coverage_high-v.coverage for v in a]]),fmt='o-',capsize=2,color=col,ms=3)
    for ax in axs:ax.set_xscale('log');ax.set_xlabel('Total labeled sample size')
    axs[0].axhline(1,ls='--',lw=.7,color='black');axs[1].axhline(.95,ls='--',lw=.7,color='black')
    axs[0].set_ylabel('EB-split3 / baseline mean width');axs[1].set_ylabel('EB-split3 coverage');axs[0].legend(fontsize=7)
    axs[1].set_ylim(.945,1.005)
    fig.tight_layout();fig.savefig(GEN/'finite.pdf');plt.close(fig)


def number_macros(df):
    values={}
    a=cell(df,'quadratic_cont',800,'CF3')
    values['QuadReduction']=f"{100*(1-a.ratio_PPIpp):.1f}"
    values['QuadRatio']=rat(a)
    values['QuadCoverage']=cov(a)+r'\%'
    for case,name in [('quadratic_binary','QuadBinaryReduction'),('threshold_binary','StepReduction')]:
        values[name]=f"{100*(1-cell(df,case,800,'CF3').ratio_PPIpp):.1f}"
    for case,n,m,key in [('quadratic_cont',200,'CV3','NaiveQuadCoverage'),('quadratic_cont',200,'CF3','SmallQuadCFCoverage'),('rare_binary',200,'CF3','RareSmallCoverage'),('rare_binary',800,'CF3','RareLargeCoverage')]:
        values[key]=cov(cell(df,case,n,m))+r'\%'
    a=cell(df,'null_binary',50,'CV15',kind='ablation')
    values['HighDegreeCoverage']=cov(a)+r'\%';values['HighDegreeRatio']=rat(a,'CV1')
    a=cell(df,'quadratic_cont',12800,'EB-split3');b=cell(df,'quadratic_cont',800,'EB-split3')
    values['FiniteReduction']=f"{100*(1-a.ratio_EB_label):.1f}"
    values['FiniteLargeRatio']=rat(a,'EB_label');values['FiniteSmallRatio']=rat(b,'EB_label')
    values['FiniteMidReduction']=f"{100*(1-cell(df,'quadratic_cont',3200,'EB-split3').ratio_EB_label):.1f}"
    values['FiniteLargeCoverage']=cov(a)+r'\%'
    metas=[json.loads(p.read_text()) for p in (RES/'raw').glob('*.json')]
    values['TotalRepetitions']=f"{sum(z['reps'] for z in metas):,}"
    values['TotalCells']=str(len(metas))
    (GEN/'numbers.tex').write_text('% Generated from actual repeated-sampling outputs.\n'+'\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in values.items())+'\n')
    (RES/'reported_numbers.json').write_text(json.dumps(values,indent=2))

if __name__=='__main__':
    d,raw=summarize();tables(d);figures(d,raw);number_macros(d)
    print(d.shape,'summary rows;',len(raw),'cells; generated tables and figures in',GEN)
