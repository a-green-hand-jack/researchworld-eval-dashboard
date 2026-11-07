"""Full finite-background coalition tables. No approximate reference values."""
from common import *
import joblib,time,json,os,resource,argparse
from scipy.special import expit
from threadpoolctl import threadpool_limits
from concurrent.futures import ProcessPoolExecutor,as_completed

def compute_game(ds,md,case,bgsize=16):
 dat=joblib.load(ROOT/f'data/{ds}.joblib');art=joblib.load(ROOT/f'data/{ds}_{md}.joblib')
 x=dat['cases'][case];d=len(x);bg=dat['background64'][:bgsize];v=np.zeros(2**d)
 t=time.perf_counter();cpu=time.process_time();batch=2048
 for start in range(0,2**d,batch):
  ids=np.arange(start,min(start+batch,2**d),dtype=np.uint32)
  masks=((ids[:,None]>>np.arange(d))&1).astype(bool)
  if md=='logistic':
   bc=art['background64_contrib'][:bgsize];xc=art['case_contrib'][case]
   logits=(masks.astype(float)@(xc[None,:]-bc).T)+bc.sum(axis=1)[None,:]+art['intercept']
   v[start:start+len(ids)]=expit(logits).mean(axis=1)
  else:
   hybrid=np.where(masks[:,None,:],x[None,None,:],bg[None,:,:]).reshape(-1,d)
   v[start:start+len(ids)]=art['model'].predict_proba(hybrid)[:,1].reshape(-1,bgsize).mean(axis=1)
 phi=exact_shap(v,d)
 out=ROOT/f'results/games/{ds}_{md}_{case:02d}_b{bgsize}.npz';out.parent.mkdir(exist_ok=True,parents=True)
 elapsed=time.perf_counter()-t;cput=time.process_time()-cpu
 np.savez_compressed(out,v=v,phi=phi,seconds=elapsed,cpu_seconds=cput,bgsize=bgsize,d=d,case_id=dat['caseids'][case])
 return dict(dataset=ds,model=md,case=case,bgsize=bgsize,seconds=elapsed,cpu_seconds=cput,efficiency_error=float(abs(phi.sum()-(v[-1]-v[0]))),file=str(out.relative_to(ROOT)))

def worker(args):
 with threadpool_limits(limits=1):return compute_game(*args)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--datasets',nargs='+',default=DATASETS);ap.add_argument('--cases',type=int,default=N_CASES);ap.add_argument('--sensitivity',action='store_true');a=ap.parse_args()
 todo=[]
 for ds in a.datasets:
  for md in MODELS:
   for i in range(a.cases):
    for b in ([4,64] if a.sensitivity else [16]):
     if not (ROOT/f'results/games/{ds}_{md}_{i:02d}_b{b}.npz').exists():todo.append((ds,md,i,b))
 t=time.perf_counter()
 with ProcessPoolExecutor(max_workers=a.workers) as ex:
  futures=[ex.submit(worker,args) for args in todo]
  for f in as_completed(futures):
   row=f.result();print(json.dumps(row),flush=True)
 print(json.dumps({'wall_seconds':time.perf_counter()-t,'new_games':len(todo)}),flush=True)
if __name__=='__main__':main()
