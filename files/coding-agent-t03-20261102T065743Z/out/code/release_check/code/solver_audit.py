"""POST HOC numerical-solver audit prompted by extreme low-budget estimates.
Same masks/payoffs; replace normal equations by SVD least squares, no extra payoff budget.
"""
from common import *
import shap,joblib,time,warnings,json
from threadpoolctl import threadpool_limits
from concurrent.futures import ProcessPoolExecutor

def worker(args):
 ds,md,case=args
 with threadpool_limits(limits=1):
  path=ROOT/f'results/solver/{ds}_{md}_{case:02d}.npz'
  if path.exists():return
  a=np.load(ROOT/f'results/runs/{ds}_{md}_{case:02d}.npz');v=np.load(ROOT/f'results/games/{ds}_{md}_{case:02d}_b16.npz')['v'];active=a['active'];d=len(a['ref']);m=len(active);bits=1<<active
  def f(z):return v[np.rint(z).astype(np.int64)@bits]
  stable=np.zeros((N_REPEATS,d));ranks=[];conditions=[];matches=[];cpu=time.process_time();t=time.perf_counter()
  for r in range(N_REPEATS):
   np.random.seed(seed_for(DATASETS.index(ds),MODELS.index(md),case,2,r,10));ex=shap.KernelExplainer(f,np.zeros((1,m)),link='identity')
   with warnings.catch_warnings():
    warnings.simplefilter('ignore');p=ex.shap_values(np.ones((1,m)),nsamples=min(2*d,2**d-2),l1_reg=0,silent=True)[0]
   full=np.zeros(d);full[active]=p;matches.append(float(np.max(abs(full-a['phi'][0,0,r]))))
   mask=ex.maskMatrix[:ex.nsamplesAdded];w=ex.kernelWeights[:ex.nsamplesAdded];delta=float(np.ravel(ex.fx-ex.fnull)[0]);y=np.ravel(ex.ey[:ex.nsamplesAdded])-float(np.ravel(ex.fnull)[0]);X=mask[:,:-1]-mask[:,[-1]];rhs=y-mask[:,-1]*delta
   sw=np.sqrt(w);coeff,resid,rank,svals=np.linalg.lstsq(sw[:,None]*X,sw*rhs,rcond=None)
   pp=np.r_[coeff,delta-coeff.sum()];pp[abs(pp)<1e-10]=0;stable[r,active]=pp;ranks.append(rank);conditions.append(float(svals[0]/svals[-1]) if svals[-1]>0 else float('inf'))
  path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,phi=stable,ref=a['ref'],rank=np.array(ranks),condition=np.array(conditions),active=active,replay_error=np.array(matches),cpu_seconds=time.process_time()-cpu,seconds=time.perf_counter()-t)
 return {'dataset':ds,'model':md,'case':case}

def summarize():
 import pandas as pd
 from analyze import metrics,interval,fmt,LABEL,TAB,OUT
 rows=[];max_replay=0
 for ds,md,case in __import__('itertools').product(DATASETS,MODELS,range(N_CASES)):
  a=np.load(ROOT/f'results/runs/{ds}_{md}_{case:02d}.npz');s=np.load(ROOT/f'results/solver/{ds}_{md}_{case:02d}.npz');max_replay=max(max_replay,float(s['replay_error'].max()))
  for label,p in [('Package',a['phi'][0,0]),('SVD',s['phi'])]:
   met,err,_,_=metrics(p,a['ref']);rows.append(dict(dataset=ds,model=md,case=case,solver=label,numeric=float(met['numeric']),joint=float(met['joint']),top3=float(met['top3']),extreme=float((err>1).mean()),rank_deficient=float((s['rank']<len(s['active'])-1).mean())))
 df=pd.DataFrame(rows);df.to_csv(OUT/'solver_per_case.csv',index=False)
 lines=[r'\begin{tabular}{llrrrr}',r'\toprule',r'Data & Solver & Numeric & Top-3 & Joint & $E>1$ \\',r'\midrule']
 for ds in DATASETS:
  for solver in ['Package','SVD']:
   g=df[(df.dataset==ds)&(df.solver==solver)].groupby('case')[['numeric','top3','joint','extreme']].mean()
   lines.append(f'{LABEL[ds]} & {solver} & '+' & '.join(fmt(interval(g[k])) for k in g)+r' \\')
 lines.extend([r'\bottomrule',r'\end{tabular}']);(TAB/'solver.tex').write_text('\n'.join(lines))
 info={'max_replay_error':max_replay,'n_runs':len(df)//2*64,'extreme_package_count':int(round(df[df.solver=='Package'].extreme.sum()*64)),'extreme_svd_count':int(round(df[df.solver=='SVD'].extreme.sum()*64)),'rank_deficient_count':int(round(df[df.solver=='Package'].rank_deficient.sum()*64)),'cpu_seconds':sum(float(np.load(p)['cpu_seconds']) for p in (ROOT/'results/solver').glob('*.npz'))}
 assert max_replay==0,info
 (OUT/'solver.json').write_text(json.dumps(info,indent=2));print(info)
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=4) as ex:
  for r in ex.map(worker,[(ds,md,i) for ds in DATASETS for md in MODELS for i in range(N_CASES)]):print(json.dumps(r),flush=True)
 summarize()
