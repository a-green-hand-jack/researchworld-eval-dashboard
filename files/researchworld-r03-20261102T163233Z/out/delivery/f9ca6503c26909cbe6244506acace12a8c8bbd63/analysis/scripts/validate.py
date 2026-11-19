"""Check delivered numerical evidence and reconstruct one held-out prediction."""
import gzip,json,pathlib
import numpy as np
import pandas as pd
from methods import moments,predict,losses
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read_json(path):
 if path.exists():return json.loads(path.read_text())
 with gzip.open(str(path)+'.gz','rt') as f:return json.load(f)
s=pd.read_csv(ROOT/'results/summary.csv')
assert np.isfinite(s[['mae','rmse','standardized_rmse','mae_lo','mae_hi']]).all().all()
assert ((s.mae>=0)&(s.rmse+1e-12>=s.mae)&(s.mae_hi>=s.mae_lo)).all()
for folder in (ROOT/'results').iterdir():
 if not folder.is_dir() or folder.name.startswith('pilot'):continue
 p=folder/'model_losses.csv';p=p if p.exists() else pathlib.Path(str(p)+'.gz')
 if not p.exists():continue
 x=pd.read_csv(p)
 assert x[['mae','mse','standardized_mse']].notna().all().all()
 assert (x.n_targets>0).all()
 if (folder/'splits.json').exists():
  for split in read_json(folder/'splits.json'):
   tr=set(split['train_names']);va=set(split['validation_names']);te=set(split['test_names'])
   assert not(tr&va or tr&te or va&te)
  dataset=x.dataset.iloc[0];n=pd.read_csv(ROOT/f'data/{dataset}.csv',index_col=0).shape[1]
  assert (x.n_targets==n-x.k).all()
 for design in read_json(folder/'designs.json'):
  assert len(design['queries'])==design['k']==len(set(design['queries']))
  if 'targets' in design:assert not(set(design['queries'])&set(design['targets']))
# Reconstruct a reported cell from its saved train identities and query design.
out=ROOT/'results/mteb_random';frame=pd.read_csv(ROOT/'data/mteb.csv',index_col=0)
split=read_json(out/'splits.json')[0]
d=next(v for v in read_json(out/'designs.json') if v['seed']==0 and v['method']=='a_opt_covariance' and v['k']==4)
train=frame.loc[split['train_names']].to_numpy();test=frame.loc[split['test_names']].to_numpy();mu,cov=moments(train,split['alpha'])
q=[frame.columns.get_loc(t) for t in d['queries']];prediction=predict(mu,cov,test,q);sd=np.nanstd(train,axis=0,ddof=1)
expected=losses(test,prediction,q,sd)['mae']
p=out/'model_losses.csv';p=p if p.exists() else pathlib.Path(str(p)+'.gz');record=pd.read_csv(p);record=record[(record.seed==0)&(record.method=='a_opt_covariance')&(record.k==4)].set_index('model').loc[split['test_names']]
assert np.allclose(expected,record.mae.to_numpy(),rtol=0,atol=1e-12)
(ROOT/'results/validation.json').write_text(json.dumps({'summary_rows':len(s),'checks':['finite losses and nonempty targets','budget and unique-query invariants','disjoint model identities','fixed-target/query separation','manual reconstruction of primary held-out k=4 predictions'],'passed':True},indent=2)+'\n')
print('All numerical artifact and reconstruction checks passed.')
