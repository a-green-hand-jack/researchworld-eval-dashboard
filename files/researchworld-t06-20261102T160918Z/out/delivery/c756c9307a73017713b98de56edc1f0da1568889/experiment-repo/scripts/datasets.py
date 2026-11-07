"""Canonical comparison rows. All model names sorted; y is the first model's win."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
@dataclass
class Data:
 name:str
 frame:pd.DataFrame
 def arrays(self):
  names=sorted(set(self.frame.a)|set(self.frame.b));idx={s:i for i,s in enumerate(names)}
  return self.frame.a.map(idx).to_numpy(),self.frame.b.map(idx).to_numpy(),self.frame.y.to_numpy(float),names

def canonical(d):
 d=d.copy();swap=d.a>d.b
 d.loc[swap,['a','b']]=d.loc[swap,['b','a']].to_numpy()
 d.loc[swap,'y']=1-d.loc[swap,'y'];assert (d.a<d.b).all();assert d.y.between(0,1).all()
 return d.reset_index(drop=True)
def arena(min_support=0,decisive=False):
 d=pd.read_csv(ROOT/'data/raw/arena55.csv',usecols=['id','model_a','model_b','winner_model_a','winner_model_b','winner_tie'])
 assert d.id.is_unique and (d[['winner_model_a','winner_model_b','winner_tie']].sum(axis=1)==1).all()
 f=pd.DataFrame(dict(a=d.model_a,b=d.model_b,y=d.winner_model_a+.5*d.winner_tie,cluster=d.id))
 if min_support:
  counts=pd.concat([f.a,f.b]).value_counts();keep=counts[counts>=min_support].index;f=f[f.a.isin(keep)&f.b.isin(keep)]
 if decisive:f=f[f.y!=.5]
 return Data('arena'+(f'_support{min_support}' if min_support else '')+('_decisive' if decisive else ''),canonical(f))
def mt(which,drop_inconsistent=False,expert_only=False):
 d=pd.read_parquet(ROOT/f'data/raw/mt_{which}.parquet',columns=['question_id','model_a','model_b','winner','judge','turn'])
 allowed=['model_a','model_b','tie','tie (inconsistent)'];assert d.winner.isin(allowed).all()
 if drop_inconsistent:d=d[d.winner!='tie (inconsistent)']
 if expert_only:d=d[d.judge.str.startswith('expert_')]
 f=pd.DataFrame(dict(a=d.model_a,b=d.model_b,y=d.winner.map({'model_a':1.,'model_b':0.,'tie':.5,'tie (inconsistent)':.5}),cluster=d.question_id,turn=d.turn,judge=d.judge))
 return Data('mt_'+which+('_consistent' if drop_inconsistent else '')+('_expert' if expert_only else ''),canonical(f))
def matched_mt(seed):
 h=mt('human').frame;j=mt('gpt4').frame;k=['cluster','a','b','turn']
 # Uniformly select one observed human judgment per cell. GPT-4 has one per cell.
 rng=np.random.default_rng(seed);h=h.iloc[rng.permutation(len(h))].drop_duplicates(k)
 j=j.merge(h[k],on=k,validate='one_to_one');h=h.merge(j[k],on=k,validate='one_to_one')
 h=h.sort_values(k).reset_index(drop=True);j=j.sort_values(k).reset_index(drop=True)
 assert h[k].equals(j[k]);return Data('matched_human',h),Data('matched_gpt4',j)
def nba(year):
 d=pd.read_csv(ROOT/'data/raw/nba.csv');d=d[(d._iscopy==0)&(d.lg_id=='NBA')&(d.is_playoffs==0)&(d.year_id==year)]
 assert d.game_id.is_unique
 f=pd.DataFrame(dict(a=d.team_id,b=d.opp_id,y=(d.game_result=='W').astype(float),cluster=d.date_game,date=pd.to_datetime(d.date_game),home=(d.game_location=='H').astype(float)-(d.game_location=='A').astype(float)))
 swap=f.a>f.b;f.loc[swap,'home']*=-1
 return Data(f'nba_{year}',canonical(f))
def primary():return [arena(),mt('human'),mt('gpt4')]+[nba(y) for y in range(2006,2016)]
