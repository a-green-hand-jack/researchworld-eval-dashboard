"""Recompute all paired comparisons, uncertainty, tables and prose macros.
No new observations are generated here. All reads preserve literal 'null'.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import binom
from scipy.special import logsumexp
ROOT=Path(__file__).resolve().parent
ORDER=['linear','quadratic','step','null','rare','galaxies','forest']
LABELS={'linear':'Linear','quadratic':'Quadratic','step':'Step','null':'Null','rare':'Rare','galaxies':'Galaxies','forest':'Forest'}
FINITE=['cp','eb_labeled','eb_ppi','eb_select','cp_strat2']

def read(p):return pd.read_csv(p,keep_default_na=False)
def holm_log(logps):
    logps=np.asarray(logps,float); order=np.argsort(logps); out=np.empty(len(logps))
    out[order]=np.minimum(0,np.maximum.accumulate(logps[order]+np.log(len(logps)-np.arange(len(logps)))))
    return out

def scientific_log(logp):
    z=logp/np.log(10); exponent=int(np.floor(z))
    return f'{10**(z-exponent):.8f}e{exponent:+d}'

def main():
    s=pd.concat([read(ROOT/'results'/'summary.csv'),read(ROOT/'results'/'stratified_summary.csv')],ignore_index=True)
    assert len(s)==442 and len(s[s.method=='cp'])==32
    s['tier']=np.where(s.method.isin(FINITE),'finite',np.where(s.method=='oracle','oracle','asymptotic'))
    # Exact lower-tail probabilities and Holm adjustment in log space.
    s['under_logp']=[logsumexp(binom.logpmf(np.arange(int(round(x.coverage*x.reps))+1),int(x.reps),.95)) for x in s.itertuples()]
    s['under_logholm']=0.
    for tier,g in s.groupby('tier'):
        s.loc[g.index,'under_logholm']=holm_log(g.under_logp)
    for prefix,logcol in [('under_p','under_logp'),('under_holm','under_logholm')]:
        s[prefix]=np.exp(s[logcol])
        s[prefix+'_scientific']=[scientific_log(z) for z in s[logcol]]
        s[prefix+'_below_float']=s[logcol]<np.log(np.nextafter(0.,1.))
    s['under_log10p']=s.under_logp/np.log(10)
    s['under_log10holm']=s.under_logholm/np.log(10)
    s.to_csv(ROOT/'results'/'all_summary.csv',index=False)
    pairs=[]; counts={}; rawall=[]
    for p in sorted((ROOT/'results'/'raw').glob('*.gz')):
        a=read(p); b=read(ROOT/'results'/'supplement_raw'/p.name)
        d=pd.concat([a,b],ignore_index=True)
        n=int(d.n.iloc[0]); N=int(d.N.iloc[0]); scenario=d.scenario.iloc[0]
        assert len(d.rep.unique())==2000
        assert np.all((d.lower>=0)&(d.upper<=1)&(d.lower<=d.upper))
        assert np.all(d.covered==((d.lower<=d.truth)&(d.truth<=d.upper)).astype(int))
        pivot=d.pivot(index='rep',columns='method',values='width')
        assert not pivot.isna().any().any()
        for method in pivot:
            for ref in ['ppipp','cp','eb_labeled','eb_ppi']:
                w=pivot[method].to_numpy(); v=pivot[ref].to_numpy(); ratio=w.mean()/v.mean()
                se=np.std((w-ratio*v)/v.mean(),ddof=1)/np.sqrt(len(w))
                pairs.append(dict(scenario=scenario,n=n,N=N,ratio=N/n,method=method,reference=ref,
                                  width_ratio=ratio,se=se,lo=ratio-1.96*se,hi=ratio+1.96*se))
        counts[p.name]=len(d); rawall.append(d)
    pair=pd.DataFrame(pairs);pair.to_csv(ROOT/'results'/'paired_comparisons.csv',index=False)
    def row(name,n,method,ratio=10):return s[(s.scenario==name)&(s.n==n)&(s.ratio==ratio)&(s.method==method)].iloc[0]
    def pr(name,n,method,reference):return pair[(pair.scenario==name)&(pair.n==n)&(pair.ratio==10)&(pair.method==method)&(pair.reference==reference)].iloc[0]
    def write(name,lines): (ROOT/'tables'/name).write_text('\n'.join(lines)+'\n')
    # Main paired asymptotic table at n=2000.
    lines=[r'\begin{tabular}{lrrrrr}',r'\toprule',r' & \multicolumn{2}{c}{PPI++ (unrestricted)} & \multicolumn{3}{c}{Cross-fit rich} \\',r'Distribution & Width & Coverage & Width ratio (MC SE) & Coverage & Wilson 95\% interval \\',r'\midrule']
    for name in ORDER:
        a=row(name,2000,'ppipp');b=row(name,2000,'cf_rich')
        lines.append(f"{LABELS[name]} & {a.width:.5f} & {a.coverage:.4f} & {b.width_ratio_ppipp:.4f} ({b.ratio_se:.4f}) & {b.coverage:.4f} & [{b.cov_lo:.4f}, {b.cov_hi:.4f}] \\\\")
    lines += [r'\bottomrule',r'\end{tabular}'];write('main_asymptotic.tex',lines)
    # Exact-tier results: ratio paired to ordinary CP, no cross-tier superiority.
    lines=[r'\begin{tabular}{lrrrrr}',r'\toprule',r' & \multicolumn{2}{c}{Exact labeled binomial} & \multicolumn{3}{c}{Exact two-stratum} \\',r'Distribution & Width & Coverage & Width ratio (MC SE) & Coverage & Wilson 95\% interval \\',r'\midrule']
    for name in ORDER:
        a=row(name,2000,'cp');b=row(name,2000,'cp_strat2');c=pr(name,2000,'cp_strat2','cp')
        lines.append(f"{LABELS[name]} & {a.width:.5f} & {a.coverage:.4f} & {c.width_ratio:.4f} ({c.se:.4f}) & {b.coverage:.4f} & [{b.cov_lo:.4f}, {b.cov_hi:.4f}] \\\\")
    lines += [r'\bottomrule',r'\end{tabular}'];write('main_exact.tex',lines)
    # Component ablation at n=500, including negative-control in-sample fitting.
    ms=['ppipp','cf_linear','cf_poly2','cf_rich','insample_rich']
    lines=[r'\begin{tabular}{llrrr}',r'\toprule',r'Law & Recipe & Width ratio & MC SE & Coverage \\',r'\midrule']
    for name in ['quadratic','step','galaxies','forest']:
        for method in ms:
            a=row(name,500,method)
            label={'ppipp':'PPI++','cf_linear':'CF scalar','cf_poly2':'CF polynomial','cf_rich':'CF rich','insample_rich':'In-sample (unsafe)'}[method]
            lines.append(f'{LABELS[name]} & {label} & {a.width_ratio_ppipp:.4f} & {a.ratio_se:.4f} & {a.coverage:.4f} \\\\')
    lines += [r'\bottomrule',r'\end{tabular}'];write('ablation.tex',lines)
    # Full results all cells, compact longtable for auditability.
    lines=[r'\begin{longtable}{llrrrrr}',r'\caption{All repeated-sampling results; each row has 2000 repetitions. MC SE is the standard error of mean width; paired comparisons are additionally available in CSV.}\label{tab:full}\\',r'\toprule',r'Law, $n$, $N/n$ & Method & Coverage & Wilson lower & Wilson upper & Width & MC SE \\',r'\midrule\endfirsthead',r'\toprule Law, $n$, $N/n$ & Method & Coverage & Wilson lower & Wilson upper & Width & MC SE \\\midrule\endhead']
    for name in ORDER:
        group=s[s.scenario==name].sort_values(['n','ratio','method'])
        for a in group.itertuples():
            method=a.method.replace('_',r'\_')
            lines.append(f'{LABELS[name]}, {a.n}, {a.ratio} & {method} & {a.coverage:.4f} & {a.cov_lo:.4f} & {a.cov_hi:.4f} & {a.width:.5f} & {a.width_se:.5f} \\\\')
    lines+=[r'\bottomrule',r'\end{longtable}'];write('full_results.tex',lines)
    macros=[]
    def macro(key,value):macros.append('\\newcommand{\\'+key+'}{'+str(value)+'}')
    a=row('quadratic',2000,'cf_rich');b=row('step',2000,'cf_rich'); c=pr('step',2000,'cp_strat2','cp');d=row('rare',30,'cf_rich')
    macro('QuadSaving',f'{100*(1-a.width_ratio_ppipp):.1f}')
    macro('StepSaving',f'{100*(1-b.width_ratio_ppipp):.1f}')
    macro('ExactSaving',f'{100*(1-c.width_ratio):.1f}')
    macro('ExactSavingLo',f'{100*(1-c.hi):.2f}')
    macro('ExactSavingHi',f'{100*(1-c.lo):.2f}')
    macro('StepCoverage',f'{100*b.coverage:.2f}')
    macro('RareCoverage',f'{100*d.coverage:.2f}')
    macro('RareCoverageLo',f'{100*d.cov_lo:.2f}')
    macro('RareCoverageHi',f'{100*d.cov_hi:.2f}')
    macro('ExactStepWidth',f"{row('step',2000,'cp_strat2').width:.5f}")
    macro('CPstepWidth',f"{row('step',2000,'cp').width:.5f}")
    macro('ExactStepRatio',f'{c.width_ratio:.4f}')
    macro('ExactStepRatioSE',f'{c.se:.4f}')
    macro('StepCoverageLo',f'{100*b.cov_lo:.2f}')
    macro('StepCoverageHi',f'{100*b.cov_hi:.2f}')
    macro('GalaxyIncrease',f"{100*(row('galaxies',2000,'cf_rich').width_ratio_ppipp-1):.2f}")
    macro('ForestIncrease',f"{100*(row('forest',2000,'cf_rich').width_ratio_ppipp-1):.2f}")
    macro('EBstepSaving',f"{100*(1-pr('step',2000,'eb_select','eb_labeled').width_ratio):.2f}")
    macro('EBstepRatioCP',f"{pr('step',2000,'eb_select','cp').width_ratio:.3f}")
    macro('FiniteTests',len(s[s.tier=='finite']))
    macro('FiniteRejects',int(((s.tier=='finite')&(s.under_holm<.05)).sum()))
    macro('AsymTests',len(s[s.tier=='asymptotic']))
    macro('AsymRejects',int(((s.tier=='asymptotic')&(s.under_holm<.05)).sum()))
    macro('TotalIntervals',f'{sum(counts.values()):,}')
    macro('RunSeconds',f"{json.loads((ROOT/'results'/'config.json').read_text())['wall_seconds']:.1f}")
    macro('SupplementSeconds',f"{json.loads((ROOT/'results'/'stratified_config.json').read_text())['wall_seconds']:.1f}")
    write('numbers.tex',macros)
    # Five independent consecutive MC blocks: descriptive stability, not extra data.
    raw=pd.concat(rawall,ignore_index=True); raw['block']=raw.rep//400
    raw.groupby(['scenario','n','N','method','block'],sort=False).agg(coverage=('covered','mean'),width=('width','mean'),reps=('rep','count')).reset_index().to_csv(ROOT/'results'/'block_stability.csv',index=False)
    qa={'cells':len(counts),'unique_repetitions':64000,'reported_intervals':sum(counts.values()),
        'no_invalid_endpoints':True,'pairing':'identical replicate indices; same arrays in one all_intervals call; supplemental deterministic replay',
        'finite_undercoverage_holm_rejections':int(((s.tier=='finite')&(s.under_holm<.05)).sum()),
        'asymptotic_undercoverage_holm_rejections':int(((s.tier=='asymptotic')&(s.under_holm<.05)).sum()),
        'note':'seconds in summary are cumulative per-cell elapsed; NOT per-method runtime.'}
    (ROOT/'results'/'quality_checks.json').write_text(json.dumps(qa,indent=2))
    print(json.dumps(qa,indent=2));print('\n'.join(macros))

if __name__=='__main__':main()
