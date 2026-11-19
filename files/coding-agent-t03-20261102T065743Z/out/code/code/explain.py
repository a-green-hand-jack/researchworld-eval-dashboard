"""Replicate actual SHAP KernelExplainer against exact cached coalition payoffs."""
from common import *
import time,json,warnings,argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from threadpoolctl import threadpool_limits

def kernel(v,d,budget,seed,l1=0,active=None):
 import shap
 np.random.seed(seed)
 active=np.arange(d) if active is None else np.asarray(active)
 bits=(1<<active.astype(np.int64));m=len(active)
 def game(z):return v[np.rint(z).astype(np.int64)@bits]
 exp=shap.KernelExplainer(game,np.zeros((1,m)),link='identity')
 with warnings.catch_warnings(record=True) as ws:
  warnings.simplefilter('always')
  smallphi=exp.shap_values(np.ones((1,m)),nsamples=budget,l1_reg=l1,silent=True)[0]
  phi=np.zeros(d);phi[active]=smallphi
 return phi,int(exp.nsamplesAdded) if m>1 else 0,[str(w.message) for w in ws]

def permutation(v,d,budget,seed,active=None):
 rng=np.random.default_rng(seed);active=np.arange(d) if active is None else np.asarray(active);m=len(active)
 if m<=1:
  out=np.zeros(d)
  if m:out[active[0]]=v[-1]-v[0]
  return out,0
 pairs=max(1,min(budget,2**m-2)//(2*(m-1)))
 result=np.zeros(d);bits=1<<np.arange(d,dtype=np.int64)
 for _ in range(pairs):
  p=rng.permutation(active)
  for order in (p,p[::-1]):
   path=np.r_[0,np.cumsum(bits[order])]
   result[order]+=np.diff(v[path])
 return result/(2*pairs),2*pairs*(m-1)

def worker(args):
 ds,md,case,default=args
 with threadpool_limits(limits=1):
  game=np.load(ROOT/f'results/games/{ds}_{md}_{case:02d}_b16.npz');v=game['v'];ref=game['phi'];d=len(ref)
  import joblib
  dat=joblib.load(ROOT/f'data/{ds}.joblib');active=np.flatnonzero(np.any(dat['background']!=dat['cases'][case],axis=0))
  outfile=ROOT/f"results/runs/{ds}_{md}_{case:02d}{'_default' if default else ''}.npz"
  if outfile.exists():return {'cached':str(outfile)}
  t=time.perf_counter();cpu=time.process_time();di=DATASETS.index(ds);mi=MODELS.index(md)
  nbud=1 if default else len(MULTIPLIERS);phis=np.zeros((2 if not default else 1,nbud,N_REPEATS,d));cost=np.zeros(phis.shape[:-1],dtype=int);warns=[]
  for bi,c in enumerate([128] if default else MULTIPLIERS):
   budget=min(c*d,2**d-2)
   for r in range(N_REPEATS):
    seed=seed_for(di,mi,case,c,r,10)
    phis[0,bi,r],cost[0,bi,r],ws=kernel(v,d,budget,seed,'num_features(10)' if default else 0,active)
    if ws:warns.extend(ws)
    if not default:phis[1,bi,r],cost[1,bi,r]=permutation(v,d,budget,seed_for(di,mi,case,c,r,20),active)
  outfile.parent.mkdir(parents=True,exist_ok=True)
  np.savez_compressed(outfile,phi=phis,ref=ref,cost=cost,budgets=np.minimum(np.array([128] if default else MULTIPLIERS)*d,2**d-2),seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu,warnings=np.array(warns,dtype=str),active=active)
  return {'dataset':ds,'model':md,'case':case,'default':default,'seconds':time.perf_counter()-t,'warnings':len(warns)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--datasets',nargs='+',default=DATASETS);ap.add_argument('--cases',type=int,default=N_CASES);ap.add_argument('--default',action='store_true');ap.add_argument('--models',nargs='+',default=MODELS);a=ap.parse_args()
 args=[(ds,md,i,a.default) for ds in a.datasets for md in a.models for i in range(a.cases)]
 with ProcessPoolExecutor(max_workers=a.workers) as ex:
  for r in ex.map(worker,args):print(json.dumps(r),flush=True)
if __name__=='__main__':main()
