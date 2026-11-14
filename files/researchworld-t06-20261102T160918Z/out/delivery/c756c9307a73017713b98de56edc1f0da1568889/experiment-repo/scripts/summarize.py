"""Analysis-owner numerical evidence tables; presentation owner renders final figures."""
import json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import beta
from datasets import ROOT

def binom_interval(success,total):
 # Exact Clopper-Pearson Monte Carlo interval, not sampling uncertainty.
 lo=0. if success==0 else beta.ppf(.025,success,total-success+1)
 hi=1. if success==total else beta.ppf(.975,success+1,total-success)
 return lo,hi

def summarize(folder):
 audits=[];curves=[];boots=[]
 files=sorted(folder.rglob('audit.json'))
 if not files:
  # Matched per-replicate directories are deliberately not shipped. The
  # consolidated audits retain every paired statistic needed here.
  a=pd.read_csv(folder/'audits.csv')
  if not folder.name.startswith('matched'):
   raise RuntimeError(f'Missing detailed primary evidence in {folder}')
  a['variant']=[f'rep{int(r):03d}/{n}' for r,n in zip(a.rep,a.dataset)]
  dest=ROOT/'results/summary'/folder.name;dest.mkdir(parents=True,exist_ok=True)
  a.to_csv(dest/'datasets.csv',index=False)
  return a
 for p in files:
  d=json.loads(p.read_text());d['variant']=str(p.parent.relative_to(folder));audits.append(d)
  q=pd.read_csv(p.parent/'curves.csv')
  for (strategy,k),g in q.groupby(['strategy','budget_k']):
   n=len(g);success=int(g.pair_reversed.sum());lo,hi=binom_interval(success,n) if strategy!='influence' else (np.nan,np.nan)
   curves.append(dict(dataset=d['dataset'],variant=d['variant'],strategy=strategy,budget_k=k,budget_fraction=k/d['N'],actual_k_min=int(g.actual_k.min()),actual_k_max=int(g.actual_k.max()),runs=n,pair_reversal_rate=success/n,pair_rate_mc_low=lo,pair_rate_mc_high=hi,winner_change_rate=g.winner_changed.mean(),margin_mean=g.margin.mean(),margin_q025=g.margin.quantile(.025),margin_q975=g.margin.quantile(.975),kendall_mean=g.kendall_distance.mean(),kendall_q025=g.kendall_distance.quantile(.025),kendall_q975=g.kendall_distance.quantile(.975),linear_margin_abs_error_max=abs(g.margin-g.linear_margin).max()))
  b=pd.read_csv(p.parent/'bootstrap.csv') if (p.parent/'bootstrap.csv').stat().st_size>2 else pd.DataFrame()
  if len(b):
   boots.append(dict(dataset=d['dataset'],variant=d['variant'],runs=len(b),gap=d['gap'],gap_low=b.margin.quantile(.025),gap_high=b.margin.quantile(.975),gap_sd=b.margin.std(),gap_over_sd=d['gap']/b.margin.std(),original_leader_loses_rate=b.winner_changed.mean(),fixed_pair_reversal_rate=b.pair_reversed.mean()))
 dest=ROOT/'results/summary'/folder.name;dest.mkdir(parents=True,exist_ok=True)
 pd.DataFrame(audits).to_csv(dest/'datasets.csv',index=False);pd.DataFrame(curves).to_csv(dest/'curves.csv',index=False);pd.DataFrame(boots).to_csv(dest/'uncertainty.csv',index=False)
 return pd.DataFrame(audits)
if __name__=='__main__':
 for name in ['primary','robustness','matched','matched_bootstrap']:
  p=ROOT/'results'/name
  if (p/'audits.csv').exists():
   a=summarize(p);print(name,len(a),'datasets')
   if name.startswith('matched'):
    a['rep']=a.variant.str.extract(r'rep(\d+)').astype(int)
    h=a[a.dataset=='matched_human'].set_index('rep');j=a[a.dataset=='matched_gpt4'].set_index('rep')
    diff=h.attack_fraction-j.attack_fraction
    tab=dict(n=len(diff),complete_pairs=int(diff.notna().sum()),censored_pairs=int(diff.isna().sum()),mean_difference=float(diff.mean()),q025=float(diff.quantile(.025)),median=float(diff.median()),q975=float(diff.quantile(.975)),human_lower_fraction_among_complete=float((diff.dropna()<0).mean()))
    pd.DataFrame(dict(human_fraction=h.attack_fraction,gpt4_fraction=j.attack_fraction,difference=diff,human_gap=h.gap,gpt4_gap=j.gap,human_leader=h.leader,gpt4_leader=j.leader,N=h.N)).to_csv(ROOT/'results/summary'/name/'paired_replicates.csv')
    p=ROOT/'results/summary'/name/'paired_difference.json';p.write_text(json.dumps(tab,indent=2)+'\n');print(tab)
