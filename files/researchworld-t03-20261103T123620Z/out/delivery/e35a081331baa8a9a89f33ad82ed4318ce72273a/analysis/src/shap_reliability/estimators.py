"""Exact empirical interventional game and antithetic permutation estimator.

All cached coalition values are deterministic for the fixed model/background.
A fresh game is used for each run, including preprocessing-independent endpoints.
"""
import math,time
import numpy as np

class Game:
    def __init__(self,model,background,x,groups,batch_rows=8192):
        self.model=model; self.background=np.asarray(background); self.x=np.asarray(x)
        self.groups=groups; self.d=len(groups); self.batch_rows=batch_rows
        self.column_feature=np.zeros(len(x),int)
        for j,g in enumerate(groups): self.column_feature[g]=j
        self.cache={}; self.prediction_rows=0; self.predict_calls=0
    def predict(self,arr):
        self.prediction_rows+=len(arr); self.predict_calls+=1
        return np.asarray(self.model.predict_proba(np.asarray(arr,dtype=np.float64))[:,1],dtype=np.float64)
    def values(self,codes):
        codes=np.asarray(codes,dtype=np.int64)
        missing=np.array(sorted(set(codes.tolist())-self.cache.keys()),dtype=np.int64)
        b=len(self.background); step=max(1,self.batch_rows//b)
        for start in range(0,len(missing),step):
            chunk=missing[start:start+step]
            mask=((chunk[:,None]>>np.arange(self.d))&1).astype(bool)
            arr=np.where(mask[:,None,self.column_feature],self.x[None,None,:],self.background[None,:,:])
            vals=self.predict(arr.reshape(-1,len(self.x))).reshape(-1,b).mean(axis=1)
            self.cache.update(zip(chunk.tolist(),vals.tolist()))
        return np.array([self.cache[int(c)] for c in codes])
    def exact(self):
        allcodes=np.arange(1<<self.d,dtype=np.int64); values=self.values(allcodes)
        phi=np.zeros(self.d)
        for j in range(self.d):
            low=allcodes[(allcodes&(1<<j))==0]
            counts=np.bitwise_count(low)
            weights=np.array([1/(self.d*math.comb(self.d-1,k)) for k in range(self.d)])
            phi[j]=np.dot(weights[counts],values[low|(1<<j)]-values[low])
        return phi
    def permutation(self,n_permutations,seed,return_pairs=False):
        if n_permutations%2: raise ValueError('antithetic permutation count must be even')
        rng=np.random.default_rng(seed); paths=[]; permutations=[]
        for _ in range(n_permutations//2):
            p=rng.permutation(self.d)
            for order in (p,p[::-1]):
                path=np.concatenate([[0],np.cumsum(1<<order,dtype=np.int64)])
                paths.append(path); permutations.append(order)
        vals=self.values(np.asarray(paths).ravel()).reshape(n_permutations,self.d+1)
        contributions=np.zeros((n_permutations,self.d))
        for i,order in enumerate(permutations): contributions[i,order]=np.diff(vals[i])
        pairs=contributions.reshape(-1,2,self.d).mean(axis=1)
        return (pairs.mean(axis=0),pairs) if return_pairs else pairs.mean(axis=0)

def kernel_shap(game,budget,seed):
    import shap
    from shap.utils._legacy import DenseData
    # Explicit groups make stochastic Kernel SHAP operate on raw feature units.
    data=DenseData(game.background,[f'f{j}' for j in range(game.d)],game.groups)
    old=np.random.get_state(); np.random.seed(seed)
    try:
        explainer=shap.KernelExplainer(game.predict,data,link='identity')
        phi=explainer.shap_values(game.x[None,:],nsamples=budget,l1_reg=0,silent=True,gc_collect=False)[0]
        m=int(explainer.M); used=int(getattr(explainer,'nsamplesAdded',0))
        details={'kernel_sampled_coalitions':used,'varying_features':m,'exhaustive':bool(m<=1 or used==2**m-2)}
        if m>1:
            masks=explainer.maskMatrix[:used]
            design=masks[:,:-1]-masks[:,-1,None]
            weighted=design*np.sqrt(explainer.kernelWeights[:used,None])
            details.update(kernel_design_rank=int(np.linalg.matrix_rank(weighted)),kernel_design_columns=m-1,kernel_design_condition=float(np.linalg.cond(weighted)))
            if details['kernel_design_rank']<m-1:
                raise np.linalg.LinAlgError('Kernel SHAP constrained design is rank deficient')
    finally: np.random.set_state(old)
    return np.asarray(phi),details

def timed_run(game,estimator,budget,seed):
    wall=time.perf_counter(); cpu=time.process_time()
    if estimator=='permutation':
        n=max(2,2*(budget//(2*(game.d-1))))
        phi=game.permutation(n,seed); extra={'n_permutations':n,'unique_coalitions':len(game.cache),'coalition_coverage_complete':len(game.cache)==2**game.d,'exhaustive':False}
    elif estimator=='kernel': phi,extra=kernel_shap(game,budget,seed)
    elif estimator=='exact': phi=game.exact(); extra={'unique_coalitions':len(game.cache),'exhaustive':True}
    else: raise ValueError(estimator)
    return phi,dict(extra,wall_seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu,prediction_rows=game.prediction_rows,predict_calls=game.predict_calls)
