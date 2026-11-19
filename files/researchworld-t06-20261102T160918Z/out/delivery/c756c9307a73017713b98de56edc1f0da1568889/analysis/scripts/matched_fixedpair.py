"""Original GPT-4 versus Claude contrast in matched question bootstrap.
Uses stored top-two search when it is the same pair; refits other replicates.
"""
import json
import numpy as np,pandas as pd
from datasets import ROOT,matched_mt
from bt import fit,influence
src=ROOT/'results/matched_bootstrap';aud=pd.read_csv(src/'audits.csv');rows=[]
for _,row in aud.iterrows():
 rep=int(row.rep);name=row.dataset;p=src/f'rep{rep:03d}'/name
 scores=pd.read_csv(p/'scores.csv').set_index('model').theta
 gap=float(scores['gpt-4']-scores['claude-v1']);k=row.attack_k
 if row.leader=='gpt-4' and row.runner=='claude-v1':pass
 elif gap<0:k=0
 else:
  h,j=matched_mt(20261102+rep);rng=np.random.default_rng(20261102+100000+rep);groups=h.frame.cluster.unique();draw=rng.choice(groups,len(groups),replace=True)
  d=h if name=='matched_human' else j;d.frame=pd.concat([d.frame[d.frame.cluster==g] for g in draw],ignore_index=True)
  a,b,y,names=d.arrays();t,_=fit(a,b,y,len(names));pair=(names.index('gpt-4'),names.index('claude-v1'));ix,_,_=influence(a,b,y,t,pair=pair)
  assert abs(t[pair[0]]-t[pair[1]]-gap)<1e-8
  cap=min(len(ix),int(.05*len(y)))
  def margin(k):
   z=y.copy();z[ix[:k]]=1-z[ix[:k]];u,_=fit(a,b,z,len(names),init=t);return u[pair[0]]-u[pair[1]]
  k=None
  if margin(cap)<-1e-10:
   lo=0;hi=cap
   while hi-lo>1:
    mid=(hi+lo)//2
    if margin(mid)<-1e-10:hi=mid
    else:lo=mid
   k=hi
 rows.append(dict(rep=rep,dataset=name,N=row.N,gap=gap,attack_k=k,attack_fraction=None if k is None else k/row.N))
d=pd.DataFrame(rows);out=ROOT/'results/summary/matched_fixedpair';out.mkdir(parents=True,exist_ok=True);d.to_csv(out/'replicates.csv',index=False)
p=d.pivot(index='rep',columns='dataset',values='attack_fraction');diff=p.matched_human-p.matched_gpt4
summary=dict(pairs=len(diff),complete_pairs=int(diff.notna().sum()),mean_difference=float(diff.mean()),median_difference=float(diff.median()),q025=float(diff.quantile(.025)),q975=float(diff.quantile(.975)),human_lower_fraction=float((diff<0).mean()),already_reversed_human=int(sum((d.dataset=='matched_human')&(d.gap<0))))
(out/'difference.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
