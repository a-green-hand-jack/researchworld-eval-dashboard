"""Primary reproducible experiments. All random streams are explicitly seeded."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import argparse, json, time, platform
from pathlib import Path
import numpy as np
import pandas as pd
from bt import load
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results'
PRIMARY=['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015']
EXTRA=['matched_human','matched_gpt4','mt_gpt4_consistent']
SEED=20261028

def metrics(theta,order):
 s=theta[order];m=len(s)
 return dict(boundary_reversal=float((np.diff(s)>1e-8).mean()),leader_loss=int(np.argmax(s)!=0),discordance=float(sum((s[i+1:]>s[i]+1e-8).sum() for i in range(m-1))/(m*(m-1)/2)))

def audit(name,bootstrap):
 start=time.monotonic();bt=load(name);f=bt.fit();order=np.argsort(-f.theta[:bt.m]);pairs=np.c_[order[:-1],order[1:]]
 rng=np.random.default_rng(SEED+sum(map(ord,name)));boot=[];boot_scores=[]
 ncl=bt.cluster.max()+1
 for rep in range(bootstrap):
  cw=np.bincount(rng.integers(0,ncl,size=ncl),minlength=ncl)
  bf=bt.fit(weights=cw[bt.cluster],init=f.theta);boot.append(bf.theta[pairs[:,0]]-bf.theta[pairs[:,1]]);boot_scores.append(bf.theta[:bt.m])
 boot=np.array(boot);cis=np.quantile(boot,[.025,.975],axis=0)
 np.savez_compressed(RES/f'bootstrap_{name}.npz',gaps=boot,scores=np.array(boot_scores),pairs=pairs,order=order)
 ranks=[]
 for rank,i in enumerate(order):
  ranks.append(dict(dataset=name,rank=rank+1,participant=bt.names[i],score=f.theta[i],exposure=int(((bt.a==i)|(bt.b==i)).sum()),score_lo=np.quantile(np.array(boot_scores)[:,i],.025),score_hi=np.quantile(np.array(boot_scores)[:,i],.975)))
 pd.DataFrame(ranks).to_csv(RES/f'ranking_{name}.csv',index=False)
 rows=[];witnesses={};traces=[]
 for j,(a,b) in enumerate(pairs):
  for kind in ['delete','flip']:
   for scope in ['all','direct']:
    result,ix,trace=bt.attack(f,a,b,kind,scope)
    result.update(dataset=name,boundary=j+1,a=str(bt.names[a]),b=str(bt.names[b]),kind=kind,scope=scope,ci_lo=cis[0,j],ci_hi=cis[1,j],boot_positive=float((boot[:,j]>0).mean()))
    rows.append(result);witnesses[f'{j+1}_{kind}_{scope}']=ix
    for k,gap in trace.items():traces.append(dict(boundary=j+1,kind=kind,scope=scope,k=k,post_gap=gap))
 pd.DataFrame(rows).to_csv(RES/f'attacks_{name}.csv',index=False);pd.DataFrame(traces).to_csv(RES/f'trace_{name}.csv',index=False)
 np.savez_compressed(RES/f'witnesses_{name}.npz',**witnesses)
 print(f'AUDIT {name}: {time.monotonic()-start:.2f}s',flush=True)
 return rows

def random_edits(name,reps):
 start=time.monotonic();bt=load(name);f=bt.fit();order=np.argsort(-f.theta[:bt.m]);rows=[]
 rng=np.random.default_rng(SEED+701+sum(map(ord,name)))
 for kind in ['delete','flip']:
  candidates=np.arange(bt.n) if kind=='delete' else np.flatnonzero(bt.y!=.5)
  for rep in range(reps):
   ix=rng.permutation(candidates)
   for alpha in [.001,.005,.01,.02,.05]:
    k=max(1,int(np.floor(alpha*bt.n)));nf=bt.edited_fit(ix[:k],kind,f)
    row=dict(dataset=name,kind=kind,rep=rep,alpha=alpha,k=k,actual_alpha=k/bt.n,grad_norm=nf.grad_norm)
    row.update(metrics(nf.theta,order));rows.append(row)
 pd.DataFrame(rows).to_csv(RES/f'random_{name}.csv',index=False)
 print(f'RANDOM {name}: {time.monotonic()-start:.2f}s',flush=True)
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--bootstrap',type=int,default=400);p.add_argument('--random-reps',type=int,default=200);p.add_argument('--datasets',nargs='+',default=PRIMARY+EXTRA);p.add_argument('--skip-random',action='store_true');args=p.parse_args()
 start=time.monotonic();allrows=[]
 for name in args.datasets:allrows.extend(audit(name,args.bootstrap))
 pd.DataFrame(allrows).to_csv(RES/'attacks.csv',index=False)
 if not args.skip_random:
  r=[]
  for name in args.datasets:
   if name in PRIMARY:r.extend(random_edits(name,args.random_reps))
  pd.DataFrame(r).to_csv(RES/'random.csv',index=False)
 metadata=dict(seed=SEED,bootstrap=args.bootstrap,random_reps=args.random_reps,datasets=args.datasets,seconds=time.monotonic()-start,python=platform.python_version(),cpu_count=os.cpu_count(),platform=platform.platform(),threads=1)
 (RES/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');print(metadata)
if __name__=='__main__':main()
