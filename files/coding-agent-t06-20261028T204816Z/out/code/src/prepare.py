"""Prepare canonical row-level pair comparisons; raw conversations are never used."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed'

def save(name, frame):
 frame=frame.copy()
 names=sorted(set(frame.a)|set(frame.b)); lookup={v:k for k,v in enumerate(names)}
 a=frame.a.map(lookup).to_numpy();b=frame.b.map(lookup).to_numpy();y=frame.y.to_numpy(float)
 assert (a!=b).all(), name
 swap=a>b
 a,b=np.minimum(a,b),np.maximum(a,b);y=np.where(swap,1-y,y)
 home=frame.get('home',pd.Series(np.zeros(len(frame)))).to_numpy(float)
 home=np.where(swap,-home,home)
 clusters=pd.factorize(frame.cluster,sort=True)[0]
 np.savez_compressed(OUT/f'{name}.npz',a=a,b=b,y=y,cluster=clusters,home=home,names=np.array(names),row_id=frame.index.to_numpy())
 return dict(dataset=name,N=len(frame),M=len(names),ties=int((y==.5).sum()),clusters=len(set(clusters)),exposure_min=int(np.bincount(np.r_[a,b],minlength=len(names)).min()),exposure_max=int(np.bincount(np.r_[a,b],minlength=len(names)).max()))

def mt_frame(typ):
 d=pd.read_parquet(ROOT/f'data/raw/mt_{typ}.parquet',columns=['model_a','model_b','winner','question_id','turn','judge'])
 d['y']=d.winner.map({'model_a':1.,'model_b':0.,'tie':.5,'tie (inconsistent)':.5})
 assert d.y.notna().all()
 return d.rename(columns={'model_a':'a','model_b':'b','question_id':'cluster'})

def main():
 OUT.mkdir(exist_ok=True,parents=True);stats=[]
 d=pd.read_csv(ROOT/'data/raw/arena.csv',usecols=['id','model_a','model_b','winner_model_a','winner_model_b','winner_tie'])
 assert ((d.winner_model_a+d.winner_model_b+d.winner_tie)==1).all()
 d['y']=d.winner_model_a+.5*d.winner_tie;d['cluster']=np.arange(len(d));d=d.rename(columns={'model_a':'a','model_b':'b'});stats.append(save('arena',d))
 for typ in ['human','gpt4']:
  d=mt_frame(typ);stats.append(save('mt_'+typ,d))
  if typ=='gpt4': stats.append(save('mt_gpt4_consistent',d[d.winner!='tie (inconsistent)']))
 # Match evaluation units, keeping exactly one real human judgment and its GPT-4 counterpart.
 h,g=mt_frame('human'),mt_frame('gpt4')
 def canonical(d):
  d=d.copy();swap=d.a>d.b
  d['lo']=np.where(swap,d.b,d.a);d['hi']=np.where(swap,d.a,d.b);d['yc']=np.where(swap,1-d.y,d.y)
  return d
 h,g=canonical(h),canonical(g);keys=['cluster','turn','lo','hi']
 # fixed uniform within-unit human selection, independent of labels, seed 20261028
 h=h.sample(frac=1,random_state=20261028).drop_duplicates(keys)
 matched=h.merge(g,on=keys,suffixes=('_h','_g'),validate='one_to_one')
 matched.to_csv(OUT/'mt_matched_units.csv',index=False)
 for typ,suffix in [('human','h'),('gpt4','g')]:
  f=pd.DataFrame({'a':matched.lo,'b':matched.hi,'y':matched['yc_'+suffix],'cluster':matched.cluster})
  stats.append(save('matched_'+typ,f))
 d=pd.read_csv(ROOT/'data/raw/nba.csv');assert not d[d._iscopy==0].game_id.duplicated().any()
 for yr in [2013,2014,2015]:
  f=d[(d._iscopy==0)&(d.is_playoffs==0)&(d.year_id==yr)].copy()
  f['y']=(f.game_result=='W').astype(float);f['home']=f.game_location.map({'H':1.,'A':-1.,'N':0.});f['cluster']=f.date_game
  f=f.rename(columns={'team_id':'a','opp_id':'b'});stats.append(save(f'nba{yr}',f))
 pd.DataFrame(stats).to_csv(ROOT/'results/data_summary.csv',index=False)
 print(pd.DataFrame(stats).to_string(index=False))
if __name__=='__main__':main()
