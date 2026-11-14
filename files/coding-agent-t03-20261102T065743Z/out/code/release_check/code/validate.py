"""Nontrivial independent checks on the target and cached implementation."""
from common import *
from explain import kernel
import itertools,json,joblib,shap,time
from scipy.special import expit
from threadpoolctl import threadpool_limits

def main():
 checks={}
 # Independent Shapley reference: enumerate permutation orders rather than subsets.
 rng=np.random.default_rng(501);d=6;v=rng.normal(size=2**d);p=np.zeros(d)
 for order in itertools.permutations(range(d)):
  mask=0
  for j in order:p[j]+=v[mask|(1<<j)]-v[mask];mask|=1<<j
 p/=720;checks['subset_vs_all_permutations_maxerror']=float(np.max(abs(p-exact_shap(v,d))))
 # Additive game recovered regardless of sampled masks when design full-rank.
 a=np.arange(1.,9.)/100;ids=np.arange(256);z=((ids[:,None]>>np.arange(8))&1);v=.2+z@a
 p,_,_=kernel(v,8,64,701);checks['additive_kernel_maxerror']=float(np.max(abs(p-a)))
 # Full coalition kernel result independently matches subset formula.
 v=rng.normal(size=256);p,_,_=kernel(v,8,254,702);checks['full_kernel_vs_formula_maxerror']=float(np.max(abs(p-exact_shap(v,8))))
 # Actual raw-data Kernel SHAP vs lookup game, including grouped categoricals.
 for ds in DATASETS:
  dat=joblib.load(ROOT/f'data/{ds}.joblib');d=len(dat['names']);x=dat['cases'][0:1];bg=dat['background'];active=np.flatnonzero(np.any(bg!=x[0],axis=0));budget=8*d
  for md in MODELS:
   art=joblib.load(ROOT/f'data/{ds}_{md}.joblib');game=np.load(ROOT/f'results/games/{ds}_{md}_00_b16.npz');v=game['v'];model=art['model']
   def f(z):return model.predict_proba(art['pre'].transform(z) if md=='logistic' else z)[:,1]
   np.random.seed(1234);ex=shap.KernelExplainer(f,bg,link='identity');live=ex.shap_values(x,nsamples=budget,l1_reg=0,silent=True)[0]
   cached,_,_=kernel(v,d,budget,1234,active=active)
   checks[f'{ds}_{md}_live_vs_cache_maxerror']=float(np.max(abs(live-cached)))
   checks[f'{ds}_{md}_prediction_vs_game_maxerror']=float(abs(f(x)[0]-v[-1]))
 assert max(checks.values())<1e-10,checks
 (ROOT/'results/validation.json').write_text(json.dumps(checks,indent=2));print(checks)
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
