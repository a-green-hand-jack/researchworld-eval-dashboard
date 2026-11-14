"""True online calls; cache lookup timings are never labeled deployment runtimes."""
from common import *
import joblib,time,json,shap
from threadpoolctl import threadpool_limits

def main():
 rows=[]
 for ds in DATASETS:
  dat=joblib.load(ROOT/f'data/{ds}.joblib');d=len(dat['names']);x=dat['cases'][:1];bg=dat['background']
  for md in MODELS:
   art=joblib.load(ROOT/f'data/{ds}_{md}.joblib')
   for c in MULTIPLIERS:
    for r in range(5):
     nrows=[0]
     def f(z):
      nrows[0]+=len(z)
      return art['model'].predict_proba(art['pre'].transform(z) if md=='logistic' else z)[:,1]
     np.random.seed(seed_for(DATASETS.index(ds),MODELS.index(md),c,r,70))
     t=time.perf_counter();cpu=time.process_time();ex=shap.KernelExplainer(f,bg,link='identity');p=ex.shap_values(x,nsamples=min(c*d,2**d-2),l1_reg=0,silent=True)[0]
     rows.append(dict(dataset=ds,model=md,c=c,r=r,seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu,model_rows=nrows[0],interior_coalitions=int(ex.nsamplesAdded),active=int(ex.M)))
 (ROOT/'results/timing.json').write_text(json.dumps(rows,indent=2));print('completed',len(rows),flush=True)
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
