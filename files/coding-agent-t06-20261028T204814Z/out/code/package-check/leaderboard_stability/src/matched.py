"""Identical, balanced MT-Bench schedules with one judgment per shared cell."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from pathlib import Path
import pandas as pd,numpy as np,json,time
from bt import Data
R=Path(__file__).resolve().parents[1];SEED=20261028

def main(reps=500):
 start=time.time();h=pd.read_csv(R/'data/processed/mt_human.csv');g=pd.read_csv(R/'data/processed/mt_gpt4.csv')
 keys=['a','b','cluster','turn'];groups=h.groupby(keys,sort=True).indices
 gg={tuple(row[k] for k in keys):i for i,row in g.iterrows()}
 cells={}
 for key in groups:
  if key in gg:cells.setdefault(key[:2],[]).append(key)
 size=min(map(len,cells.values()));rng=np.random.default_rng(SEED+9000);rows=[];checks=[]
 for rep in range(reps):
  hi=[];gi=[]
  for pair,keys_pair in sorted(cells.items()):
   for ix in rng.choice(len(keys_pair),size,replace=False):
    key=keys_pair[ix];hi.append(int(rng.choice(groups[key])));gi.append(gg[key])
  for label,frame,ids in [('human',h,hi),('gpt4',g,gi)]:
   d=Data(label,frame.iloc[ids].copy());t=d.fit();order=np.argsort(-t);i,j=order[:2]
   radii=[d.balanced_radius(i,v) for v in order[1:]];top_radius=min(x for x in radii if x is not None)
   a=np.where(d.names=='gpt-4')[0][0];b=np.where(d.names=='claude-v1')[0][0];pair_radius=d.balanced_radius(a,b) if t[a]>t[b] else 0
   rows.append({'rep':rep,'design':label,'n':d.n,'per_pair':size,'leader':d.names[i],'runner':d.names[j],'top_radius':top_radius,'pair_radius':pair_radius,'win_margin':float(d.win_totals()[a]-d.win_totals()[b]),'theta_gap':float(t[a]-t[b]),'ties':int(np.sum(d.y==.5))})
   # Independent numerical verification of the exact formula.
   ids_edit,_=d.order(t,a,b,'wins')
   if pair_radius>0:
    before=d.fit(wins=d.edited_wins(ids_edit[:pair_radius-1]),start=t)
    after=d.fit(wins=d.edited_wins(ids_edit[:pair_radius]),start=t)
    assert before[a]-before[b]>=-1e-8 and after[a]-after[b]<-1e-9
   if rep==0:
    d.frame.to_csv(R/f'data/processed/matched_example_{label}.csv',index=False)
  if (rep+1)%100==0:print(rep+1,flush=True)
 pd.DataFrame(rows).to_csv(R/'results/matched.csv',index=False)
 (R/'results/matched_metadata.json').write_text(json.dumps({'seed':SEED+9000,'reps':reps,'per_pair':size,'shared_cells':len(groups),'seconds':time.time()-start},indent=2)+'\n')
if __name__=='__main__':main()
