"""Matched-design uncertainty, and numerical/modeling/selection controls."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import time,json
from pathlib import Path
import numpy as np
import pandas as pd
from bt import BT,load
from prepare import save,mt_frame
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results';SEED=20261028

def data_dict(bt,index=None):
 index=np.arange(bt.n) if index is None else index
 return dict(a=bt.a[index],b=bt.b[index],y=bt.y[index],cluster=bt.cluster[index],home=bt.z[index],names=bt.names)

def pair_rows(bt,fit,dataset,setting,cap=.05,allpairs=True):
 order=np.argsort(-fit.theta[:bt.m]);rows=[]
 pairs=list(zip(order[:-1],order[1:])) if allpairs else [(order[0],order[1])]
 for j,(a,b) in enumerate(pairs):
  for kind in ['delete','flip']:
   r,ix,_=bt.attack(fit,a,b,kind,cap=cap)
   r.update(dataset=dataset,setting=setting,boundary=j+1,kind=kind,a=bt.names[a],b=bt.names[b],home_coefficient=fit.theta[-1] if bt.home else np.nan)
   rows.append(r)
 return rows

def ablations():
 rows=[]
 for name in ['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015']:
  for ridge in [1e-4,.01,1.]:
   bt=load(name,ridge=ridge);f=bt.fit();rows.extend(pair_rows(bt,f,name,f'ridge_{ridge}'))
  bt0=load(name);d=data_dict(bt0,np.flatnonzero(bt0.y!=.5))
  if len(d['y'])<bt0.n:
   bt=BT(d);rows.extend(pair_rows(bt,bt.fit(),name,'decisive_only'))
  if name.startswith('nba'):
   bt=load(name,home=True);rows.extend(pair_rows(bt,bt.fit(),name,'home_covariate'))
 pd.DataFrame(rows).to_csv(RES/'ablations.csv',index=False)

def paired_bootstrap(reps=300):
 h=load('matched_human');g=load('matched_gpt4');assert np.array_equal(h.a,g.a) and np.array_equal(h.b,g.b) and np.array_equal(h.cluster,g.cluster)
 a=list(h.names).index('gpt-4');b=list(h.names).index('claude-v1');rng=np.random.default_rng(SEED+2001);rows=[]
 for rep in range(reps):
  cc=np.bincount(rng.integers(0,80,size=80),minlength=80);index=np.repeat(np.arange(h.n),cc[h.cluster])
  for typ,orig in [('human',h),('gpt4',g)]:
   bt=BT(data_dict(orig,index));f=bt.fit();gap=float(f.theta[a]-f.theta[b])
   for kind in ['delete','flip']:
    if gap<0:r=dict(k=0,alpha=0,local=0,gap=gap)
    else:r,_,_=bt.attack(f,a,b,kind,cap=.20)
    r.update(rep=rep,judge=typ,kind=kind,N=bt.n);rows.append(r)
 pd.DataFrame(rows).to_csv(RES/'paired_bootstrap.csv',index=False)
 # Extended cap is only to quantify the fixed matched leader-pair comparison.
 r=[]
 for typ,bt in [('human',h),('gpt4',g)]:
  f=bt.fit()
  for kind in ['delete','flip']:
   result,ix,_=bt.attack(f,a,b,kind,cap=.20);result.update(judge=typ,kind=kind);r.append(result)
 pd.DataFrame(r).to_csv(RES/'matched_extended.csv',index=False)

def annotation_selection(reps=50):
 h=mt_frame('human');g=mt_frame('gpt4');keys=['cluster','turn','lo','hi']
 for d in [h,g]:
  sw=d.a>d.b;d['lo']=np.where(sw,d.b,d.a);d['hi']=np.where(sw,d.a,d.b);d['yc']=np.where(sw,1-d.y,d.y)
 rng=np.random.default_rng(SEED+3001);rows=[]
 names=np.array(sorted(set(h.a)|set(h.b)));lookup={n:i for i,n in enumerate(names)}
 for rep in range(reps):
  hh=h.sample(frac=1,random_state=int(rng.integers(2**31))).drop_duplicates(keys)
  m=hh.merge(g,on=keys,suffixes=('_h','_g'),validate='one_to_one')
  d=dict(a=m.lo.map(lookup).to_numpy(),b=m.hi.map(lookup).to_numpy(),y=m.yc_h.to_numpy(float),cluster=m.cluster.to_numpy(),home=np.zeros(len(m)),names=names)
  bt=BT(d);f=bt.fit();a=lookup['gpt-4'];b=lookup['claude-v1']
  for kind in ['delete','flip']:
   r,_,_=bt.attack(f,a,b,kind,cap=.2);r.update(rep=rep,kind=kind);rows.append(r)
 pd.DataFrame(rows).to_csv(RES/'annotation_selection.csv',index=False)

def matched_subsample(reps=50,n=1200):
 # Size control keeps each source's own contestant population. It is descriptive,
 # not a randomized intervention on design. Disconnected graphs are reported.
 rows=[];rng=np.random.default_rng(SEED+4001)
 for name in ['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015']:
  orig=load(name)
  for rep in range(reps):
   index=np.sort(rng.choice(orig.n,n,replace=False));bt=BT(data_dict(orig,index));f=bt.fit()
   r=pair_rows(bt,f,name,'N1200',cap=.2,allpairs=False)
   for rr in r:rr.update(rep=rep,N=n,min_exposure=int(np.bincount(np.r_[bt.a,bt.b],minlength=bt.m).min()))
   rows.extend(r)
 pd.DataFrame(rows).to_csv(RES/'size_control.csv',index=False)

def validation():
 rows=[]
 for name in ['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015']:
  bt=load(name);f=bt.fit();order=np.argsort(-f.theta);rng=np.random.default_rng(SEED+5001)
  for kind in ['delete','flip']:
   for rep in range(100):
    j=int(rng.integers(bt.m-1));a,b=order[j:j+2];harm=bt.influence(f,a,b,kind);candidates=np.flatnonzero(harm>0);rank=candidates[np.argsort(-harm[candidates],kind='stable')]
    for alpha in [.001,.005,.01,.02,.05]:
     k=min(max(1,int(alpha*bt.n)),len(rank));ix=rank[:k];nf=bt.edited_fit(ix,kind,f)
     pred=harm[ix].sum();actual=(f.theta[a]-f.theta[b])-(nf.theta[a]-nf.theta[b])
     rows.append(dict(dataset=name,kind=kind,rep=rep,boundary=j+1,alpha=alpha,k=k,predicted_change=pred,actual_change=actual,error=actual-pred,grad_norm=nf.grad_norm))
 pd.DataFrame(rows).to_csv(RES/'approximation.csv',index=False)
 # Replay each primary witness from raw rows, independently of attack search.
 out=[]
 for name in ['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015','matched_human','matched_gpt4','mt_gpt4_consistent']:
  bt=load(name);f=bt.fit();d=pd.read_csv(RES/f'attacks_{name}.csv');witness=np.load(RES/f'witnesses_{name}.npz')
  for _,r in d[d.k.notna()].iterrows():
   ix=witness[f'{int(r.boundary)}_{r.kind}_{r.scope}'];a=list(bt.names).index(r.a);b=list(bt.names).index(r.b)
   weights=np.ones(bt.n);y=bt.y.copy()
   if r.kind=='delete':weights[ix]=0
   else:y[ix]=1-y[ix]
   nf=bt.fit(weights=weights,y=y)
   gap=nf.theta[a]-nf.theta[b];assert gap< -1e-8 and len(ix)==int(r.k) and len(np.unique(ix))==len(ix)
   assert abs(gap-r.post_gap)<2e-6
   out.append(dict(dataset=name,boundary=r.boundary,kind=r.kind,scope=r.scope,k=len(ix),gap=gap,grad_norm=nf.grad_norm))
 pd.DataFrame(out).to_csv(RES/'witness_validation.csv',index=False)

if __name__=='__main__':
 start=time.monotonic()
 for fun in [ablations,paired_bootstrap,annotation_selection,matched_subsample,validation]:
  t=time.monotonic();fun();print(fun.__name__,time.monotonic()-t,flush=True)
 (RES/'controls_metadata.json').write_text(json.dumps(dict(seconds=time.monotonic()-start,paired_reps=300,selection_reps=50,size_reps=50,approximation_reps=100,seed=SEED),indent=2)+'\n')
