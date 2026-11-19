"""Independent pre-delivery checks; no study outputs are modified.

Run: python3 review/check_synthetic.py /hutian/experiment /hutian/figtab
The exact check uses binomial tail probabilities, not the study's CP code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import binom

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('experiment',type=Path)
parser.add_argument('presentation',type=Path)
parser.add_argument('--archive-revision',help='Exact paper revision when both input paths are archives of one delivery')
parser.add_argument('--output',type=Path,default=Path('review/synthetic-check.json'))
args=parser.parse_args()
experiment,presentation=args.experiment,args.presentation
revisions=({'paper':args.archive_revision} if args.archive_revision else {name:subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip() for name,path in [('experiment',experiment),('figtab',presentation)]})
d = pd.read_csv(experiment / 'results/synthetic-summary.csv')
assert len(d) == 7200 and not d.duplicated(['n','k','rho','spread','metric']).any()
assert d.groupby(['n','k','rho','spread']).size().eq(25).all()
assert d.reps.eq(20000).all()
assert np.isfinite(d[['mean','mcse']]).all().all()
assert (d.mcse >= 0).all()
for name in ['synthetic-summary.csv','synthetic-validation.json']:
    assert (experiment/'results'/name).read_bytes() == (presentation/'presentation/inputs'/name).read_bytes()

# P(max_j X_j <= x) = BinomCDF(x;n,p)^K for independent equal candidates.
# CP contains p iff both binomial tails at the realized count exceed alpha/2.
checks=[]
for n in sorted(d.n.unique()):
    x=np.arange(n+1)
    for k in sorted(d.k.unique()):
        mass=np.diff(np.r_[0.,binom.cdf(x,int(n),.4)**int(k)])
        values={'optimism_reused':np.dot(mass,x/n-.4)}
        for metric,alpha in [('coverage_naive',.05),('coverage_simultaneous',.05/k)]:
            contains=(binom.cdf(x,int(n),.4)>=alpha/2)&(binom.sf(x-1,int(n),.4)>=alpha/2)
            values[metric]=mass[contains].sum()
        for metric,exact in values.items():
            r=d[(d.n==n)&(d.k==k)&(d.rho==0)&(d.spread==0)&(d.metric==metric)].iloc[0]
            z=(r['mean']-exact)/r.mcse if r.mcse else 0.
            assert abs(z)<5, (n,k,metric,z)
            checks.append({'n':int(n),'k':int(k),'metric':metric,'exact':float(exact),'measured':float(r['mean']),'mcse':float(r.mcse),'z':float(z)})

# Invariants across the full grid.
p=d.pivot(index=['n','k','rho','spread'],columns='metric',values='mean')
assert (p.coverage_simultaneous>=p.coverage_naive-1e-14).all()
assert (p.width_simultaneous>=p.width_naive-1e-14).all()
assert (p.false_superiority_simultaneous<=p.false_superiority_naive+1e-14).all()
pmax=np.where(p.index.get_level_values('k')==1,.4,.4+p.index.get_level_values('spread'))
assert np.max(abs(p.selected_quality+p.regret-pmax))<1e-12

# Table full-precision fields must select the correct metric and cost protocol.
t=pd.read_csv(presentation/'tables/synthetic-methods.csv')
for _,r in t.iterrows():
    cell=p.loc[(r.n,r.k,r.rho,r.spread)]
    suffix=r.method
    bias='optimism_reused' if suffix in ['naive','simultaneous'] else 'bias_'+suffix
    quality='quality_'+suffix if suffix.startswith('split_') else 'selected_quality'
    for field,metric in [('bias_pp',bias),('coverage_pp','coverage_'+suffix),('width_pp','width_'+suffix),('quality_pp',quality)]:
        assert abs(r[field]-100*cell[metric])<1e-7,(r.method,field)
    assert r.model_calls == r.search_questions*r.k+r.audit_questions

out={
 'scope':'Pre-delivery synthetic evidence check only; not approval of a paper version',
 'revisions':revisions,
 'inputs_sha256':{str(path.relative_to(experiment)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [experiment/'results/synthetic-summary.csv']},
 'result_rows':len(d),'cells':len(p),'exact_null_comparisons':len(checks),
 'max_absolute_z':max(abs(r['z']) for r in checks),'table_rows_checked':len(t),
 'passed':['Grid and summary integrity','Presentation input byte equality','Independent binomial-tail exact null comparisons','Interval nesting, decision monotonicity, regret identity','All table means and call costs'],
 'exact_checks':checks,
}
args.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='exact_checks'},indent=2))
