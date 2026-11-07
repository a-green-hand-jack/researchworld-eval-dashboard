"""Exact target drift across independent background samples, no estimator noise."""
from common import *
import joblib,time,json
from threadpoolctl import threadpool_limits
from scipy.special import expit
from concurrent.futures import ProcessPoolExecutor

def worker(args):
 ds,md,case=args
 with threadpool_limits(limits=1):
  dat=joblib.load(ROOT/f'data/{ds}.joblib');art=joblib.load(ROOT/f'data/{ds}_{md}.joblib');x=dat['cases'][case];d=len(x);train=dat['Xtrain'];masks=((np.arange(2**d)[:,None]>>np.arange(d))&1).astype(bool)
  out=np.zeros((3,8,d));t=time.perf_counter();cpu=time.process_time()
  for bi,b in enumerate([4,16,64]):
   for r in range(8):
    rng=np.random.default_rng(seed_for(DATASETS.index(ds),case,bi,r,995));bg=train[rng.choice(len(train),b,replace=False)]
    hybrid=np.where(masks[:,None,:],x[None,None,:],bg[None,:,:]).reshape(-1,d)
    if md=='logistic':pred=art['model'].predict_proba(art['pre'].transform(hybrid))[:,1]
    else:pred=art['model'].predict_proba(hybrid)[:,1]
    out[bi,r]=exact_shap(pred.reshape(-1,b).mean(axis=1),d)
  p=ROOT/f'results/background/{ds}_{md}_{case:02d}.npz';p.parent.mkdir(exist_ok=True,parents=True)
  np.savez_compressed(p,phi=out,seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu)
  return dict(dataset=ds,model=md,case=case,seconds=time.perf_counter()-t)
if __name__=='__main__':
 args=[(ds,md,i) for ds in ['pima','acs'] for md in MODELS for i in range(8)]
 with ProcessPoolExecutor(max_workers=6) as ex:
  for r in ex.map(worker,args):print(json.dumps(r),flush=True)
