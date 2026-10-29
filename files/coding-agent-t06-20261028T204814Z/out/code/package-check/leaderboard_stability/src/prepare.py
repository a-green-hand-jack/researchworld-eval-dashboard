"""Produce minimal outcome-only tables; no response text is redistributed."""
from pathlib import Path
import pandas as pd, numpy as np, hashlib, json
R=Path(__file__).resolve().parents[1]
def save(name,d):
 d=d.copy(); same=d.a==d.b;nself=int(same.sum());d=d.loc[~same].copy()
 rev=d.a>d.b
 a=d.a.copy();d.loc[rev,'a']=d.loc[rev,'b'];d.loc[rev,'b']=a[rev];d.loc[rev,'y']=1-d.loc[rev,'y']
 d.reset_index(drop=True).to_csv(R/'data/processed'/f'{name}.csv',index=False)
 print(name,len(d),'self excluded',nself,'models',len(set(d.a)|set(d.b)),'ties',int((d.y==.5).sum()),flush=True)
 return {'dataset':name,'n':len(d),'self_excluded':nself,'ties':int((d.y==.5).sum())}
def main():
 (R/'data/processed').mkdir(exist_ok=True,parents=True);log=[]
 a=pd.read_csv(R/'data/raw/arena.csv',usecols=['id','model_a','model_b','prompt','winner_model_a','winner_model_b','winner_tie'])
 assert (a[['winner_model_a','winner_model_b','winner_tie']].sum(axis=1)==1).all();assert a.id.is_unique
 d=pd.DataFrame({'a':a.model_a,'b':a.model_b,'y':a.winner_model_a+.5*a.winner_tie,'cluster':a.prompt.map(lambda v:hashlib.sha256(v.encode()).hexdigest()[:24]),'record_id':a.id.astype(str)})
 log.append(save('arena',d))
 for name in ['mt_human','mt_gpt4']:
  a=pd.read_parquet(R/f'data/raw/{name}.parquet');assert set(a.winner)<=set(['model_a','model_b','tie','tie (inconsistent)'])
  d=pd.DataFrame({'a':a.model_a,'b':a.model_b,'y':a.winner.map({'model_a':1.,'model_b':0.,'tie':.5,'tie (inconsistent)':.5}),'cluster':a.question_id.astype(str),'record_id':np.arange(len(a)).astype(str),'turn':a.turn,'judge':a.judge,'inconsistent':a.winner=='tie (inconsistent)'})
  log.append(save(name,d))
 a=pd.read_csv(R/'data/raw/nba.csv')
 for yr in [2014,2015]:
  s=a[(a._iscopy==0)&(a.year_id==yr)&(a.is_playoffs==0)&(a.lg_id=='NBA')].copy();assert s.game_id.is_unique
  d=pd.DataFrame({'a':s.team_id,'b':s.opp_id,'y':(s.game_result=='W').astype(float),'cluster':s.date_game,'record_id':s.game_id})
  log.append(save(f'nba{yr}',d))
 (R/'results/preparation.json').write_text(json.dumps(log,indent=2)+'\n')
if __name__=='__main__':main()
