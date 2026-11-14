"""Executed row-label reversal study. Deterministic outputs and checkpoint files."""
import argparse,json,time,platform,sys
from pathlib import Path
import numpy as np,pandas as pd,scipy
from scipy.stats import pearsonr
from datasets import primary,arena,mt,matched_mt,ROOT
from bt import fit,order,influence,metrics,graph
BUDGETS=[.001,.0025,.005,.01,.02,.05]

def refit(a,b,y,t,indices,ridge):
 z=y.copy();z[indices]=1-z[indices]
 return fit(a,b,z,len(t),ridge,init=t)[0]
def threshold(a,b,y,t,ridge=1.,limit=.05):
 rank,gain,pair=influence(a,b,y,t,ridge)
 cap=min(len(rank),int(np.floor(limit*len(y))))
 if not cap:return dict(k=None,fraction=None,linear_k=None,cap=cap),rank,gain,pair
 gap=t[pair[0]]-t[pair[1]]
 cs=np.cumsum(gain[rank[:cap]])
 linear=int(np.searchsorted(cs,gap)+1);linear=linear if linear<=cap else None
 # This is a search for a successful prefix, not a global robustness certificate.
 def margin(k):
  u=refit(a,b,y,t,rank[:k],ridge);return float(u[pair[0]]-u[pair[1]])
 if margin(cap)>=-1e-10:return dict(k=None,fraction=None,linear_k=linear,cap=cap),rank,gain,pair
 lo=0;hi=cap
 while hi-lo>1:
  mid=(lo+hi)//2
  if margin(mid)<-1e-10:hi=mid
  else:lo=mid
 # Record adjoining endpoint margins. No claim of monotonicity/global optimum.
 return dict(k=hi,fraction=hi/len(y),linear_k=linear,cap=cap,margin_at_k=margin(hi),margin_at_previous=margin(hi-1)),rank,gain,pair

def one(data,out,random_reps=200,bootstrap_reps=300,ridge=1.,seed=20261102,endpoint_reps=50,validate=100):
 out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();a,b,y,names=data.arrays();m=len(names);N=len(y)
 t,diag=fit(a,b,y,m,ridge);th,rank,gain,pair=threshold(a,b,y,t,ridge)
 audit=dict(dataset=data.name,N=N,m=m,ties=int(sum(y==.5)),decisive=int(sum(y!=.5)),clusters=int(data.frame.cluster.nunique()),ridge=ridge,leader=names[pair[0]],runner=names[pair[1]],gap=float(t[pair[0]]-t[pair[1]]),**graph(a,b,m),**diag,**{'attack_'+k:v for k,v in th.items()})
 pd.DataFrame(dict(model=names,theta=t,rank=np.argsort(np.argsort(-t))+1,support=np.bincount(a,minlength=m)+np.bincount(b,minlength=m))).to_csv(out/'scores.csv',index=False)
 rng=np.random.default_rng(seed);decisive=np.flatnonzero(y!=.5)
 ks=sorted(set([1]+[max(1,int(np.floor(q*N))) for q in BUDGETS]))
 rows=[]
 def add(strategy,rep,perm,k):
  inds=perm[:k];u=refit(a,b,y,t,inds,ridge)
  rows.append(dict(dataset=data.name,strategy=strategy,rep=rep,budget_k=k,budget_fraction=k/N,actual_k=len(inds),linear_margin=float(t[pair[0]]-t[pair[1]]-gain[inds].sum()),**metrics(u,t,pair)))
 for k in ks:add('influence',0,rank,k)
 for rep in range(random_reps):
  perm=rng.permutation(decisive)
  for k in ks:add('random',rep,perm,k)
 # Simple endpoint-only baseline, sign chosen to weaken initial leading contrast.
 c=np.zeros(m);c[pair[0]]=1;c[pair[1]]=-1
 eligible=np.flatnonzero((y!=.5)&((1-2*y)*(c[a]-c[b])<0))
 for rep in range(endpoint_reps):
  perm=rng.permutation(eligible)
  for k in ks:add('endpoint_random',rep,perm,k)
 pd.DataFrame(rows).to_csv(out/'curves.csv',index=False)
 # Bootstrap clusters, not repeated question-turn judgments independently.
 groups,code=np.unique(data.frame.cluster.astype(str),return_inverse=True);boot=[]
 for rep in range(bootstrap_reps):
  counts=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)));w=counts[code]
  u,dd=fit(a,b,y,m,ridge,weights=w,init=t)
  boot.append(dict(dataset=data.name,rep=rep,leader=names[order(u)[0]],gradient_max=dd['gradient_max'],**metrics(u,t,pair)))
 pd.DataFrame(boot).to_csv(out/'bootstrap.csv',index=False)
 # Actual one-label refits on representative influence ranks (and random rows).
 if validate and len(rank):
  ix=np.unique(np.concatenate([rank[np.linspace(0,len(rank)-1,min(validate//2,len(rank)),dtype=int)],rng.choice(decisive,min(validate//2,len(decisive)),replace=False)]))
  actual=[]
  for i in ix:
   u=refit(a,b,y,t,np.array([i]),ridge)
   actual.append(dict(row=int(i),predicted_reduction=float(gain[i]),actual_reduction=float((t[pair[0]]-t[pair[1]])-(u[pair[0]]-u[pair[1]]))))
  vd=pd.DataFrame(actual);vd.to_csv(out/'influence_validation.csv',index=False)
  audit.update(influence_r=float(pearsonr(vd.predicted_reduction,vd.actual_reduction).statistic),influence_max_abs_error=float(abs(vd.predicted_reduction-vd.actual_reduction).max()))
 audit['elapsed_seconds']=time.perf_counter()-start
 (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps(audit),flush=True);return audit

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['pilot','primary','robustness','matched','matched_bootstrap'],default='pilot');p.add_argument('--out',default='results/pilot');p.add_argument('--random',type=int,default=200);p.add_argument('--bootstrap',type=int,default=300);p.add_argument('--replicates',type=int,default=100);p.add_argument('--seed',type=int,default=20261102);args=p.parse_args()
 out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True)
 (out/'run.json').write_text(json.dumps(dict(arguments=vars(args),python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,platform=platform.platform()),indent=2)+'\n')
 audits=[]
 if args.mode in ['pilot','primary']:
  datasets=primary()
  if args.mode=='pilot':datasets=[datasets[0],datasets[1],datasets[-1]]
  for z,d in enumerate(datasets):audits.append(one(d,out/d.name,args.random,args.bootstrap,seed=args.seed+z))
 elif args.mode=='robustness':
  datasets=[arena(),mt('human'),mt('gpt4')]
  for z,d in enumerate(datasets):
   for r in [.1,10.]:audits.append(one(d,out/(d.name+f'_ridge{r}'),min(args.random,100),args.bootstrap,ridge=r,seed=args.seed+z))
  for z,d in enumerate([arena(500),arena(decisive=True),mt('gpt4',drop_inconsistent=True),mt('human',expert_only=True)]):audits.append(one(d,out/d.name,min(args.random,100),args.bootstrap,seed=args.seed+10+z))
 elif args.mode in ['matched','matched_bootstrap']:
  # Paired same-cell data. Human selection uncertainty; GPT-4 labels remain fixed.
  for rep in range(args.replicates):
   h,j=matched_mt(args.seed+rep)
   if args.mode=='matched_bootstrap':
    rng=np.random.default_rng(args.seed+100000+rep);groups=h.frame.cluster.unique();draw=rng.choice(groups,len(groups),replace=True)
    h.frame=pd.concat([h.frame[h.frame.cluster==g] for g in draw],ignore_index=True)
    j.frame=pd.concat([j.frame[j.frame.cluster==g] for g in draw],ignore_index=True)
   for d in [h,j]:
    aud=one(d,out/f'rep{rep:03d}'/d.name,args.random,0,seed=args.seed+rep,endpoint_reps=0,validate=0);aud['rep']=rep;audits.append(aud)
 pd.DataFrame(audits).to_csv(out/'audits.csv',index=False)
 print('HUTIAN_WAKE: '+args.mode+' completed; results in '+str(out),flush=True)
if __name__=='__main__':main()
