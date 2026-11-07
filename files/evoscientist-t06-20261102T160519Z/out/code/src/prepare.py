"""Prepare provenance-preserving edge lists; no prompt/answer text is retained."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def encode(df):
 df=df.copy(); names=sorted(set(df.model_a)|set(df.model_b)); mapping={n:i for i,n in enumerate(names)}
 df['a']=df.model_a.map(mapping);df['b']=df.model_b.map(mapping)
 return df,names

def load():
 raw=ROOT/'data/raw'; ds={};eda=[]
 def add(name,df,raw_n,design):
  assert not df.y.isna().any() and not (df.model_a==df.model_b).any()
  df,names=encode(df);df=df.reset_index(drop=True)
  ds[name]=(df,names)
  eda.append(dict(dataset=name,design=design,raw_rows=raw_n,n=len(df),m=len(names),ties=int((df.y==.5).sum()),unique_clusters=df.cluster.nunique(),duplicate_row_ids=int(df.row_id.duplicated().sum())))
 arena=pd.concat(pd.read_csv(raw/'arena.csv',usecols=['id','model_a','model_b','winner_model_a','winner_model_b','winner_tie'],chunksize=10000),ignore_index=True)
 assert (arena[['winner_model_a','winner_model_b','winner_tie']].sum(axis=1)==1).all()
 arena['y']=arena.winner_model_a+.5*arena.winner_tie;arena['row_id']=arena.id.astype(str);arena['cluster']=arena.row_id
 counts=pd.concat([arena.model_a,arena.model_b]).value_counts();keep=counts[counts>=100].index
 add('arena',arena[arena.model_a.isin(keep)&arena.model_b.isin(keep)],len(arena),'crowd')
 for typ in ['human','gpt4']:
  df=pd.read_parquet(raw/f'mt_{typ}.parquet')
  df['y']=df.winner.map({'model_a':1.,'model_b':0.,'tie':.5,'tie (inconsistent)':.5})
  df['row_id']=[f'{typ}:{i}' for i in range(len(df))];df['cluster']=df.question_id.astype(str)
  df['cell']=df.question_id.astype(str)+'|'+df.model_a+'|'+df.model_b+'|'+df.turn.astype(str)
  add('mt_'+typ,df,len(df),'expert' if typ=='human' else 'model-judge')
 nba=pd.read_csv(raw/'nba.csv');assert nba.game_id.nunique()==63157
 unique=nba[nba._iscopy==0].copy();assert unique.game_id.is_unique
 for year in [2013,2014,2015]:
  df=unique[unique.year_id==year].copy();df['model_a']=df.team_id;df['model_b']=df.opp_id
  df['y']=df.game_result.map({'W':1.,'L':0.});df['row_id']=df.game_id;df['cluster']=df.game_id
  df['home']=df.game_location.map({'H':1.,'A':-1.,'N':0.})
  add(f'nba{year}',df,len(df),'sports')
 return ds,pd.DataFrame(eda)

if __name__=='__main__':
 ds,eda=load();out=ROOT/'data/processed';out.mkdir(exist_ok=True)
 for name,(df,names) in ds.items():
  cols=[c for c in ['row_id','a','b','y','cluster','cell','home','question_id','turn','judge','model_a','model_b'] if c in df]
  df[cols].to_csv(out/f'{name}.csv',index=False)
  (out/f'{name}_names.json').write_text(json.dumps(names))
 eda.to_csv(ROOT/'artifacts/eda.csv',index=False);print(eda.to_string(index=False))
