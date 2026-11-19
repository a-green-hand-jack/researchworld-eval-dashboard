"""Execute CPU-only audit; all numerical paper inputs originate here.
Seeds: main controls 20261102+dataset index; bootstrap 7300+index; matching 100..119.
"""
import argparse, json, platform, time
from pathlib import Path
import numpy as np
import pandas as pd
from bt import BT, witness, disagreement
from prepare import load, encode
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)


def audit_one(df,names,ridge=1.,home=False,targets=None):
 m=BT(df.a,df.b,df.y,names,ridge,df.home if home else None);f=m.fit()
 a,b=m.targets(f) if targets is None else targets
 incident=(m.a==a)|(m.b==a)|(m.a==b)|(m.b==b);binary=m.y!=.5
 E=int(incident.sum());benefit=m.benefits(f,a,b)
 order=np.argsort(-benefit,kind='stable');order=order[binary[order]&(benefit[order]>1e-14)]
 k,cache,ids=witness(m,f,a,b,order,cap=int(.2*binary.sum()))
 data=dict(n=len(df),m=m.m,leader=names[a],challenger=names[b],a=a,b=b,E=E,direct=int((((m.a==a)&(m.b==b))|((m.a==b)&(m.b==a))).sum()),gap=f.theta[a]-f.theta[b],k=k,global_pct=None if k is None else 100*k/len(df),exposure_pct=None if k is None else 100*k/E,components=m.components,edges=len(m.n),binary=int(binary.sum()),ridge=ridge,incident_k=None if ids is None else int(incident[ids].sum()),refit_gap=None if k is None else cache[k].theta[a]-cache[k].theta[b],prior_gap=None if k is None else cache[k-1].theta[a]-cache[k-1].theta[b],predicted_k=None)
 if len(order):
  cumulative=np.cumsum(benefit[order]);cross=np.where(cumulative>data['gap'])[0]
  if len(cross):data['predicted_k']=int(cross[0]+1)
 return m,f,a,b,incident,binary,benefit,order,k,ids,data

def primary(ds,repeats,boots):
 baselines=[];controls=[];randoms=[];uncert=[];adj=[];runtime=[];ranks=[];witness_rows=[]
 for ix,(name,(df,names)) in enumerate(ds.items()):
  t=time.perf_counter(); res=audit_one(df,names);m,f,a,b,incident,binary,benefit,order,k,ids,data=res
  baselines.append(dict(dataset=name,**data));print(name,data,flush=True)
  for rank,i in enumerate(np.argsort(-f.theta[:m.m])):
   ranks.append(dict(dataset=name,rank=rank+1,participant=names[i],score=f.theta[i],appearances=int(((m.a==i)|(m.b==i)).sum())))
  if ids is not None:
   for i in ids:witness_rows.append(dict(dataset=name,row_index=int(i),row_id=df.iloc[i].row_id,a=names[m.a[i]],b=names[m.b[i]],original_y=m.y[i],new_y=1-m.y[i],benefit=benefit[i]))
  rng=np.random.default_rng(20261102+ix)
  all_pool=np.flatnonzero(binary);local_pool=np.flatnonzero(binary&incident);positive_local=np.flatnonzero(binary&incident&(benefit>0))
  # Controls evaluated at identical k as influence witness. Edge matched controls keep exact edge edit counts.
  edgecounts=[] if ids is None else list(zip(*np.unique(m.edge[ids],return_counts=True)))
  if k is not None:
   for rep in range(repeats):
    for method,pool in [('uniform',all_pool),('incident_random',local_pool),('incident_adverse',positive_local),('edge_matched',None)]:
     if pool is None:
      chosen=np.concatenate([rng.choice(np.flatnonzero(binary&(m.edge==e)),int(n),replace=False) for e,n in edgecounts])
     else:
      if k>len(pool):continue
      chosen=rng.choice(pool,k,replace=False)
     ff=m.fit(w=m.flipped_w(chosen),start=f.theta)
     controls.append(dict(dataset=name,method=method,rep=rep,k=k,gap=ff.theta[a]-ff.theta[b],success=int(ff.theta[a]-ff.theta[b]<-1e-7),top1_changed=int(np.max(ff.theta[:m.m])-ff.theta[a]>1e-7)))
   # outcome/edge-preserving controls are algebraically identical; verify 10 concrete replacements.
   groups=[(e,y,int(np.sum((m.edge[ids]==e)&(np.where(m.sign[ids]==1,m.y[ids],1-m.y[ids])==y)))) for e in np.unique(m.edge[ids]) for y in [0.,1.]]
   for rep in range(10):
    chosen=np.concatenate([rng.choice(np.flatnonzero(binary&(m.edge==e)&(np.where(m.sign==1,m.y,1-m.y)==y)),n,replace=False) for e,y,n in groups if n])
    assert np.array_equal(m.flipped_w(chosen),m.flipped_w(ids))
  # Conditional dose responses; random orders are nested over budgets, repeated independently.
  for rep in range(repeats):
   uniform=rng.permutation(all_pool);local=rng.permutation(local_pool);adverse=rng.permutation(positive_local)
   for frac in [.005,.01,.02,.05,.1,.2]:
    kk=max(1,int(np.ceil(frac*data['E'])))
    for method,seq in [('uniform',uniform),('incident_random',local),('incident_adverse',adverse),('influence',order)]:
     if method=='influence' and rep>0:continue
     if kk>len(seq):continue
     ff=m.fit(w=m.flipped_w(seq[:kk]),start=f.theta)
     randoms.append(dict(dataset=name,method=method,rep=rep,k=kk,local_budget=frac,gap=ff.theta[a]-ff.theta[b],success=int(ff.theta[a]-ff.theta[b]<-1e-7),top1_changed=int(np.max(ff.theta[:m.m])-ff.theta[a]>1e-7),disagreement=disagreement(f.theta[:m.m],ff.theta[:m.m])))
  # Fixed target bootstrap, resampling question clusters for MT, rows for others.
  brng=np.random.default_rng(7300+ix);ug,inv=np.unique(df.cluster.astype(str),return_inverse=True)
  for rep in range(boots):
   counts=brng.multinomial(len(ug),np.full(len(ug),1/len(ug)));weights=counts[inv]
   nn,ww=m.counts(weights=weights);ff=m.fit(n=nn,w=ww,start=f.theta)
   row=dict(dataset=name,rep=rep,gap=ff.theta[a]-ff.theta[b],positive=int(ff.theta[a]-ff.theta[b]>1e-7),leader_same=int(np.max(ff.theta[:m.m])-ff.theta[a]<=1e-7),witness_k=np.nan,bootstrap_n=int(weights.sum()),witness_status='not_in_first30')
   # Recompute witness on first 30 bootstrap samples only when original leader still beats original runner.
   if rep<30:
    row['witness_status']='already_reversed' if row['gap']<-1e-7 else 'numerical_tie'
   if rep<30 and row['gap']>1e-7:
    expanded=np.repeat(np.arange(len(df)),weights.astype(int));sub=df.iloc[expanded].reset_index(drop=True)
    rr=audit_one(sub,names,targets=(a,b));row['witness_k']=rr[-1]['k'];row['witness_E']=rr[-1]['E']
    row['witness_status']='found_on_resampled_slots' if rr[-1]['k'] is not None else 'search_failed'
   uncert.append(row)
  # Secondary descriptive all-adjacent audit: no multiple-testing p-values or population claims.
  ranking=np.argsort(-f.theta[:m.m],kind='stable')
  for j in range(len(ranking)-1):
   aa,bb=map(int,ranking[j:j+2]);ben=m.benefits(f,aa,bb);seq=np.argsort(-ben,kind='stable');seq=seq[binary[seq]&(ben[seq]>1e-14)]
   kk,cc,ii=witness(m,f,aa,bb,seq,cap=int(.2*binary.sum()))
   ee=int(((m.a==aa)|(m.a==bb)|(m.b==aa)|(m.b==bb)).sum())
   adj.append(dict(dataset=name,rank=j+1,leader=names[aa],challenger=names[bb],gap=f.theta[aa]-f.theta[bb],k=kk,E=ee,n=len(df),global_pct=None if kk is None else kk/len(df)*100,exposure_pct=None if kk is None else kk/ee*100))
  runtime.append(dict(dataset=name,seconds=time.perf_counter()-t,fit_count=m.fit_count,max_gradient=m.max_grad))
  for filename,rows in [('baseline',baselines),('controls',controls),('random_curves',randoms),('uncertainty',uncert),('adjacent',adj),('runtime',runtime),('rankings',ranks),('witness_rows',witness_rows)]:pd.DataFrame(rows).to_csv(OUT/f'{filename}.csv',index=False)
 return baselines

def ablations(ds):
 out=[]
 for name,(df,names) in ds.items():
  for label,rr,sub,home in [('ridge_0.1',.1,df,False),('ridge_10',10.,df,False),('drop_ties',1.,df[df.y!=.5].reset_index(drop=True),False)]:
   if label=='drop_ties' and not (df.y==.5).any():continue
   res=audit_one(sub,names,ridge=rr,home=home);out.append(dict(dataset=name,ablation=label,**res[-1]))
  if name.startswith('nba'):
   res=audit_one(df,names,home=True);out.append(dict(dataset=name,ablation='home_covariate',home_coefficient=res[1].theta[-1],**res[-1]))
 pd.DataFrame(out).to_csv(OUT/'ablations.csv',index=False)


def matched(ds):
 human,hn=ds['mt_human'];gpt,gn=ds['mt_gpt4'];assert hn==gn
 shared=sorted(set(human.cell)&set(gpt.cell));assert gpt.cell.is_unique
 gp=gpt.set_index('cell').loc[shared].reset_index()
 rows=[]
 for seed in range(100,120):
  hp=human[human.cell.isin(shared)].groupby('cell',sort=True).sample(n=1,random_state=seed).sort_values('cell').reset_index(drop=True)
  assert hp.cell.tolist()==gp.cell.tolist()
  for label,df in [('mt_human_cell',hp),('mt_gpt4_cell',gp)]:
   if label=='mt_gpt4_cell' and seed>100:continue
   res=audit_one(df,hn);rows.append(dict(dataset=label,seed=seed,**res[-1]))
 # Cohort/size control: Arena top-six pool is smaller than human N; use GPT N=2400, strictly below pool.
 arena,an=ds['arena'];full=audit_one(arena,an);top=np.argsort(-full[1].theta)[:6];keep=[an[i] for i in top]
 sub=arena[arena.model_a.isin(keep)&arena.model_b.isin(keep)].copy();requested_n=len(gpt)
 assert requested_n<len(sub)
 selected_sets=set()
 for seed in range(100,120):
  sampled=sub.sample(n=requested_n,replace=False,random_state=seed)
  import hashlib
  row_set_hash=hashlib.sha256('|'.join(sorted(sampled.row_id.astype(str))).encode()).hexdigest()
  assert row_set_hash not in selected_sets;selected_sets.add(row_set_hash)
  sampled,names=encode(sampled);sampled=sampled.reset_index(drop=True)
  res=audit_one(sampled,names);rows.append(dict(dataset='arena_top6_n2400',seed=seed,row_set_hash=row_set_hash,**res[-1]))
 pd.DataFrame(rows).to_csv(OUT/'matched.csv',index=False)
 (OUT/'matching_protocol.json').write_text(json.dumps(dict(shared_cells=len(shared),human_cells=int(human.cell.nunique()),gpt_cells=int(gpt.cell.nunique()),arena_top6_pool_n=len(sub),arena_requested_n=requested_n,arena_actual_n=requested_n,arena_unique_row_sets=len(selected_sets),arena_top6_names=keep,seeds=list(range(100,120))),indent=2))


def main():
 p=argparse.ArgumentParser();p.add_argument('--repeats',type=int,default=100);p.add_argument('--bootstrap',type=int,default=200);args=p.parse_args()
 start=time.perf_counter();ds,eda=load();eda.to_csv(OUT/'eda.csv',index=False)
 primary(ds,args.repeats,args.bootstrap);ablations(ds);matched(ds)
 (OUT/'run_metadata.json').write_text(json.dumps(dict(repeats=args.repeats,bootstrap=args.bootstrap,python=platform.python_version(),platform=platform.platform(),total_seconds=time.perf_counter()-start,cpu_only=True,bootstrap_witness_repeats=30),indent=2))
 print('complete',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
