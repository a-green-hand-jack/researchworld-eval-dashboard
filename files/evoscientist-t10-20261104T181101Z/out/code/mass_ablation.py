"""Exploratory post-audit ablation, not in locked confirmatory families.
Isolate mass uncertainty by HOLDING RESPONSE ERROR ALLOCATION FIXED at alpha/(2K).
Uses identical regenerated inputs for sharp-tail cells with n=500 and N/n=1,5,20,100.
"""
import json
import numpy as np
import pandas as pd
from run_experiments import ROOT, SEEDS, design, sample
from intervals import cp, counts8, aggregate
from summarize import latex_scientific


def main():
    rows, summaries = [], []
    for cell in [c for c in design() if c['cell_id'] in [10,27,28,29]]:
        for seed in SEEDS:
            rng=np.random.default_rng(np.random.SeedSequence([seed,cell['cell_id']]))
            for offset in range(0,cell['reps_per_seed'],40):
                b=min(40,cell['reps_per_seed']-offset)
                y,sl,su=sample(rng,b,cell['n'],cell['N'],cell['scenario'])
                c,t=counts8(sl,y)
                c,t=aggregate(c,'tails'),aggregate(t,'tails')
                a,z=cp(t,c,.05/4)
                low=np.maximum(0.,(a*.5).sum(1)-1e-10)
                high=np.minimum(1.,(z*.5).sum(1)+1e-10)
                rows.append(pd.DataFrame({'cell_id':cell['cell_id'],'seed':seed,'rep':np.arange(offset,offset+b),'N':cell['N'],
                                         'low':low,'high':high,'width':high-low,'covered':((low<=.5)&(.5<=high)).astype(int)}))
    allrows=pd.concat(rows,ignore_index=True)
    allrows.to_csv(ROOT/'mass_ablation_raw.csv.gz',index=False,float_format='%.15g')
    for cid,g in allrows.groupby('cell_id'):
        cell=next(c for c in design() if c['cell_id']==cid)
        slug=f"{cid:02d}_{cell['scenario']}_n500_N{cell['N']}"
        raw=pd.read_csv(ROOT/'results'/(slug+'.csv.gz'))
        wide=raw.pivot(index=['seed','rep'],columns='method',values='width')
        a=g.set_index(['seed','rep']).sort_index()
        wide=wide.sort_index()
        diff=wide.cp_tails-a.width
        summaries.append(dict(cell_id=cid,n=500,N=cell['N'],reps=len(g),unknown_width=wide.cp_tails.mean(),
                              matched_width=a.width.mean(),reallocated_width=wide.oracle_mass_cp.mean(),coverage=a.covered.mean(),
                              mass_gap=diff.mean(),mass_gap_mcse=diff.std(ddof=1)/np.sqrt(len(diff)),
                              realloc_gap=(a.width-wide.oracle_mass_cp).mean()))
    out=pd.DataFrame(summaries).sort_values('N')
    out.to_csv(ROOT/'mass_ablation_summary.csv',index=False)
    rows=[r'\begin{tabular}{rrrrrr}',r'\toprule $N/n$ & Unknown weights & Known (matched) & Known (reallocated) & Mass gap & MC SE \\\midrule']
    for _,r in out.iterrows():
        rows.append(f'{r.N/500:.0f} & {r.unknown_width:.4f} & {r.matched_width:.4f} & {r.reallocated_width:.4f} & {r.mass_gap:.4f} & ${latex_scientific(r.mass_gap_mcse)}$'+r' \\')
    rows+=[r'\bottomrule\end{tabular}']
    (ROOT/'generated'/'mass_ablation.tex').write_text('\n'.join(rows))
    print(out.to_string(index=False))


if __name__=='__main__':main()
