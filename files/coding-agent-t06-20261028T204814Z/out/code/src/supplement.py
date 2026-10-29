"""Exact balanced checks and tie-policy/annotation sensitivity."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np,pandas as pd,json,itertools,time
from pathlib import Path
from bt import Data
from experiment import load
R=Path(__file__).resolve().parents[1]
def main():
 start=time.time();d=load('mt_gpt4');t=d.fit();order=np.argsort(-t);rows=[]
 for i,j in itertools.combinations(order,2):
  k=d.balanced_radius(i,j);ids,_=d.order(t,i,j,'wins')
  before=d.fit(wins=d.edited_wins(ids[:k-1]),start=t);after=d.fit(wins=d.edited_wins(ids[:k]),start=t)
  assert before[i]>=before[j]-1e-8 and after[i]<after[j]-1e-9
  rows.append({'i':d.names[i],'j':d.names[j],'win_margin':d.win_totals()[i]-d.win_totals()[j],'exact_k':k,'before_gap':before[i]-before[j],'after_gap':after[i]-after[j]})
 pd.DataFrame(rows).to_csv(R/'results/balanced_exact.csv',index=False)
 out=[]
 for name in ['mt_human','mt_gpt4']:
  d=load(name);f=d.frame
  variants={}
  if name=='mt_gpt4':variants['exclude_inconsistent']=f[~f.inconsistent]
  else:
   variants['experts_only']=f[f.judge.str.startswith('expert')]
   variants['dedup_judgment_key']=f.drop_duplicates(['a','b','cluster','turn','judge'])
  for label,ff in variants.items():
   dd=Data(label,ff.copy());tt=dd.fit();i,j=np.argsort(-tt)[:2];a=dd.audit(tt,i,j)
   out.append({'dataset':name,'variant':label,'n':dd.n,'leader':dd.names[i],'runner':dd.names[j],'k':a['k'],'gap':float(tt[i]-tt[j])})
 pd.DataFrame(out).to_csv(R/'results/supplement.csv',index=False)
 # Question-cluster bootstrap of the exact full GPT radius. Complete question blocks preserve balance.
 rng=np.random.default_rng(20261028+12000);out=[]
 for rep in range(1000):
  clusters=rng.choice(d.clusters,d.clusters,replace=True);ids=np.concatenate([np.flatnonzero(d.cluster==c) for c in clusters])
  dd=Data('gpt_boot',d.frame.iloc[ids].copy());i=np.where(dd.names=='gpt-4')[0][0];j=np.where(dd.names=='claude-v1')[0][0]
  margin=dd.win_totals()[i]-dd.win_totals()[j]
  k=dd.balanced_radius(i,j) if margin>0 else 0
  out.append({'rep':rep,'k':k,'margin':margin})
 pd.DataFrame(out).to_csv(R/'results/gpt_radius_bootstrap.csv',index=False)
 (R/'results/supplement_metadata.json').write_text(json.dumps({'seconds':time.time()-start,'bootstrap_seed':20261028+12000,'bootstrap_reps':1000},indent=2)+'\n')
 print(pd.read_csv(R/'results/supplement.csv').to_string(index=False));print(pd.DataFrame(out).k.quantile([.025,.5,.975]))
if __name__=='__main__':main()
