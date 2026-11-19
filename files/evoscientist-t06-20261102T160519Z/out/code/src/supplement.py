"""Supplementary threat-model / fixed-target checks, specified after initial code audit."""
import json,time
from pathlib import Path
import numpy as np,pandas as pd
from scipy.linalg import solve
from scipy.special import expit
from bt import BT
from prepare import load
from run import audit_one
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts'

def deletion(m,f,a,b):
 c=np.zeros(m.d);c[a]=1;c[b]=-1
 v=solve(f.hessian,c,assume_a='pos',check_finite=False)
 canonical_y=np.where(m.sign==1,m.y,1-m.y)
 score=-(expit(m.X@f.theta)[m.edge]-canonical_y)*(m.X@v)[m.edge]
 order=np.argsort(-score,kind='stable');order=order[score[order]>1e-14][:int(.2*len(m.y))]
 cache={0:f}
 def refit(k):
  if k not in cache:
   idx=order[:k];nn=m.n-np.bincount(m.edge[idx],minlength=len(m.n));ww=m.w-np.bincount(m.edge[idx],weights=canonical_y[idx],minlength=len(m.n));cache[k]=m.fit(n=nn,w=ww,start=f.theta)
  return cache[k].theta[a]-cache[k].theta[b]
 hi=1;lo=0
 if not len(order):return None,None
 while True:
  hi=min(hi,len(order))
  if refit(hi)<-1e-7:break
  if hi==len(order):return None,None
  lo=hi;hi*=2
 while hi-lo>1:
  mid=(hi+lo)//2
  if refit(mid)<-1e-7:hi=mid
  else:lo=mid
 refit(hi-1)
 return hi,refit(hi)

def main():
 t=time.perf_counter();ds,eda=load();methods=[];fixed=[];verification=[]
 saved=pd.read_csv(OUT/'witness_rows.csv');base=pd.read_csv(OUT/'baseline.csv').set_index('dataset')
 for name,(df,names) in ds.items():
  rr=audit_one(df,names);m,f,a,b,incident,binary,benefit,order,k,ids,data=rr
  kd,gd=deletion(m,f,a,b)
  methods.append(dict(dataset=name,method='deletion_static',k=kd,refit_gap=gd,n=len(df),E=int(incident.sum())))
  # Exact finite refit every step, relinearizing at the new optimum; select each row at most once.
  available=binary.copy();selected=[];current=f
  for step in range(int(.2*binary.sum())):
   scores=m.benefits(current,a,b);scores[~available]=-np.inf;i=int(np.argmax(scores))
   if scores[i]<=0:break
   selected.append(i);available[i]=False;current=m.fit(w=m.flipped_w(np.array(selected)),start=current.theta)
   if current.theta[a]-current.theta[b]<-1e-7:break
  success=current.theta[a]-current.theta[b]<-1e-7
  methods.append(dict(dataset=name,method='adaptive_flip',k=len(selected) if success else None,refit_gap=current.theta[a]-current.theta[b],n=len(df),E=int(incident.sum())))
  # Fresh original-row implementation reconstructs saved primary witnesses.
  altered=df.copy();subset=saved[saved.dataset==name];idx=subset.row_index.to_numpy(int)
  assert len(idx)==len(np.unique(idx)) and np.all(altered.iloc[idx].y!=.5)
  assert altered.iloc[idx].row_id.astype(str).tolist()==subset.row_id.astype(str).tolist()
  altered.loc[idx,'y']=1-altered.loc[idx,'y'];fresh=BT(altered.a,altered.b,altered.y,names).fit()
  margin=fresh.theta[a]-fresh.theta[b]
  assert margin<-1e-7 and abs(margin-base.loc[name,'refit_gap'])<1e-7
  verification.append(dict(dataset=name,original_row_refit_gap=margin,stored_refit_gap=base.loc[name,'refit_gap'],max_gradient=fresh.grad,distinct_decisive_edits=len(idx),pass_check=True))
  variants=[('ridge_0.1',df,.1,False),('ridge_10',df,10.,False)]
  if (df.y==.5).any():variants.append(('drop_ties',df[df.y!=.5].reset_index(drop=True),1.,False))
  if name=='mt_gpt4':variants.append(('exclude_inconsistent',df[df.winner!='tie (inconsistent)'].reset_index(drop=True),1.,False))
  if name.startswith('nba'):variants.append(('home_covariate',df,1.,True))
  for label,sub,ridge,home in variants:
   mm=BT(sub.a,sub.b,sub.y,names,ridge,sub.home if home else None);ff=mm.fit();gap=ff.theta[a]-ff.theta[b]
   if gap<-1e-7:
    fixed.append(dict(dataset=name,ablation=label,leader=names[a],challenger=names[b],gap=gap,k=0,status='already_reversed',n=len(sub)));continue
   if abs(gap)<=1e-7:
    fixed.append(dict(dataset=name,ablation=label,leader=names[a],challenger=names[b],gap=gap,k=np.nan,status='numerical_tie',n=len(sub)));continue
   res=audit_one(sub,names,ridge=ridge,home=home,targets=(a,b));fixed.append(dict(dataset=name,ablation=label,**res[-1],status='found' if res[-1]['k'] is not None else 'search_failed'))
 pd.DataFrame(methods).to_csv(OUT/'method_comparison.csv',index=False)
 pd.DataFrame(fixed).to_csv(OUT/'fixed_target_ablations.csv',index=False)
 pd.DataFrame(verification).to_csv(OUT/'witness_verification.csv',index=False)
 (OUT/'supplement_metadata.json').write_text(json.dumps(dict(seconds=time.perf_counter()-t,exhaustive_search=False,primary_targets_frozen=True),indent=2))
 print('supplement complete',time.perf_counter()-t)
if __name__=='__main__':main()
