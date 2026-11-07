"""Paired-row question sensitivity, rerunning selection in each outer bootstrap.

These are approximate empirical-bootstrap sensitivity intervals, separate from
exact finite-population audit intervals; there is no population coverage claim.
"""
import argparse,hashlib,json,pathlib,time,resource
import numpy as np
import pandas as pd
from analyze_disjoint import select


def main():
 p=argparse.ArgumentParser();p.add_argument('--matrix',required=True);p.add_argument('--partition',required=True);p.add_argument('--bootstraps',type=int,default=1000);p.add_argument('--inner-reps',type=int,default=2000);p.add_argument('--out',required=True);a=p.parse_args()
 f=pathlib.Path(a.matrix);d=np.load(f);S=d['scores'][d['pools']=='search'];A=d['scores'][d['pools']=='audit'];ids=d['candidate_ids'].tolist();part=json.loads(pathlib.Path(a.partition).read_text());order=[ids.index(c) for c in part['candidate_order'] if c in ids];S=S[:,order];A=A[:,order];K=S.shape[1]
 nvalues=[64,len(S)] if len(S)!=64 else [64]
 rng=np.random.default_rng(20261108);rows=[];start=time.perf_counter();cpu=time.process_time();out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w') as stream:
  for b in range(a.bootstraps):
   bs=S[rng.integers(0,len(S),size=len(S))];ba=A[rng.integers(0,len(A),size=len(A))];means=ba.mean(axis=0)
   for n in nvalues:
    if n==len(S):
     count=bs.sum(axis=0);ties=np.flatnonzero(count==count.max());w=np.zeros(K);w[ties]=1/len(ties);report=float(count.max()/n)
    else:
     counts=np.empty((a.inner_reps,K),dtype=np.int32)
     for r in range(a.inner_reps):counts[r]=bs[rng.choice(len(bs),n,replace=False)].sum(axis=0)
     winners=select(rng,counts);w=np.bincount(winners,minlength=K)/a.inner_reps;report=float(counts.max(axis=1).mean()/n)
    fresh=float(w@means)
    record=dict(bootstrap=b,n=n,k=K,search_report=report,selected_audit_accuracy=fresh,reused_minus_audit=report-fresh,audit_contrast_to_default=fresh-means[0])
    stream.write(json.dumps(record)+'\n');rows.append(record)
   stream.flush()
   if (b+1)%20==0:print(json.dumps(dict(bootstraps_completed=b+1,elapsed_wall_seconds=time.perf_counter()-start)),flush=True)
 x=pd.DataFrame(rows);summary=[]
 for n,g in x.groupby('n'):
  for metric in ['search_report','selected_audit_accuracy','reused_minus_audit','audit_contrast_to_default']:
   v=g[metric].to_numpy();summary.append(dict(n=int(n),k=K,metric=metric,bootstrap_mean=float(v.mean()),bootstrap_sd=float(v.std(ddof=1)),percentile_lower=float(np.quantile(v,.025)),percentile_upper=float(np.quantile(v,.975)),bootstraps=a.bootstraps,inner_reps=a.inner_reps,uncertainty='paired whole-row empirical bootstrap sensitivity; approximate, no finite-population coverage claim'))
 pd.DataFrame(summary).to_csv(out.with_suffix('.summary.csv'),index=False)
 meta=dict(matrix_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),master_seed=20261108,bootstraps=a.bootstraps,inner_reps=a.inner_reps,n_values=nvalues,k=K,wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,warnings=['Both question pools resampled as paired candidate vectors; no independence across prompt outcomes.','Ordinary empirical bootstrap omits finite-population correction; exact audit intervals are provided separately.','Inner Monte Carlo noise is retained in bootstrap variability; full-pool winner/tie mixtures are calculated exactly.'])
 out.with_suffix('.runtime.json').write_text(json.dumps(meta,indent=2)+'\n');print('HUTIAN_WAKE: question bootstrap complete '+json.dumps(meta),flush=True)
if __name__=='__main__':main()
