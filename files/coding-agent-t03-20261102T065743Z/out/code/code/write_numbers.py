"""Render experiment-derived LaTeX macros, avoiding manual transcription."""
from common import *
import json,pandas as pd
r=json.loads((ROOT/'results/analysis/report.json').read_text());df=pd.read_csv(ROOT/'results/analysis/summary.csv');case=pd.read_csv(ROOT/'results/analysis/per_case.csv')
lines=[]
def macro(k,v):lines.append("\\newcommand{\\"+k+"}{"+str(v)+"}")
def pct(k,v):macro(k,f'{100*v:.1f}'+r'\%')
def ci(k,vals):macro(k,f'{100*vals[0]:.1f}'+r'\% ['+f'{100*vals[1]:.1f}, {100*vals[2]:.1f}'+']')
for c,name in [(2,'Low'),(8,'Medium'),(32,'Large'),(128,'High')]:
 for method,mn in [('kernel','Kernel'),('permutation','Perm')]:
  for key,kn in [('numeric','Numeric'),('top3','Rank'),('joint','Joint'),('sign','Sign'),('numeric005','Strict'),('numeric020','Lenient')]:
   ci(mn+name+kn,r['overall'][f'{method}_{c}'][key])
 ci('WrongAgree'+name,r['pair_diagnostics'][str(c)]['wrong_given_top3_agreement'])
# Other data-derived summaries.
for c,name in [(2,'Low'),(8,'Medium'),(32,'Large'),(128,'High')]:
 sub=df[(df.method=='kernel')&(df.c==c)]
 pct('CellMin'+name,sub.joint.min());pct('CellMax'+name,sub.joint.max())
 count=int(round(case[(case.method=='kernel')&(case.c==c)].certified.sum()));macro('Certified'+name,count)
macro('MainRuns',f'{2*3*3*N_CASES*4*N_REPEATS:,}')
macro('KernelRuns',f'{3*3*N_CASES*4*N_REPEATS:,}')
macro('DefaultRuns',f'{3*N_CASES*N_REPEATS:,}')
macro('GameCount',r['runtime']['games']['files']);macro('BackgroundGameCount',r['runtime']['background']['files']*3*8)
macro('TotalCpuHours',f"{sum(r['runtime'][k]['cpu_seconds'] for k in ['games','runs','background','solver'])/3600:.2f}")
macro('GamesCpuHours',f"{r['runtime']['games']['cpu_seconds']/3600:.2f}")
macro('ReferenceEfficiency',f"{r['runtime']['max_reference_efficiency_error']:.2g}")
macro('TimeMin',f"{1000*r['timing']['online_seconds_min']:.1f}")
macro('TimeMax',f"{1000*r['timing']['online_seconds_max']:.1f}")
w=json.loads((ROOT/'results/analysis/warnings.json').read_text());macro('WarningCount',len(w))
macro('TiedCases',int(((case.method=='kernel')&(case.c==2)&(case.gap<1e-12)).sum()))
# Exact full-enumeration checks.
errs=[]
for ds in ['pima','acs']:
 for md in MODELS:
  for i in range(N_CASES):
   a=np.load(ROOT/f'results/runs/{ds}_{md}_{i:02d}.npz');errs.append(float(np.max(abs(a['phi'][0,3]-a['ref']))))
macro('ExhaustiveError',f'{max(errs):.2g}')
solver=json.loads((ROOT/'results/analysis/solver.json').read_text())
macro('SolverRuns',f"{solver['n_runs']:,}")
macro('ExtremePackage',solver['extreme_package_count'])
macro('ExtremeSvd',solver['extreme_svd_count'])
macro('DeficientDesigns',f"{solver['rank_deficient_count']:,}")
for md,mn in [('logistic','LR'),('boosting','HGB')]:
 for key,kn in [('numeric','Numeric'),('repeat_top3','Repeat')]:
  ci('Default'+mn+kn,r['defaults'][md][key])
(ROOT/'paper/numbers.tex').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
