"""Training-only regularized covariance prediction and benchmark design.
No test scores are accepted by fit or order. Values are scores in [-1,1]; correlation scores may be negative.
"""
import numpy as np

def moments(x,shrink=.2):
    mask=np.isfinite(x);mu=np.nanmean(x,axis=0)
    if not np.isfinite(mu).all():raise ValueError('A training column is entirely missing')
    centered=np.where(mask,x-mu,0.)
    counts=mask.astype(float).T@mask.astype(float)
    cov=(centered.T@centered)/np.maximum(counts-1,1)
    # Pairwise deletion can yield an indefinite covariance. PSD projection is explicit.
    val,vec=np.linalg.eigh((cov+cov.T)/2)
    psd=(vec*np.maximum(val,0))@vec.T
    diag=np.maximum(np.diag(psd),1e-8)
    return mu,(1-shrink)*psd+shrink*np.diag(diag)

def order(cov,policy,max_k,rng):
    n=len(cov);remaining=list(range(n));chosen=[];post=cov.copy()
    if policy=='random':return rng.permutation(n)[:max_k].tolist()
    if policy=='variance':return np.argsort(-np.diag(cov))[:max_k].tolist()
    if policy=='correlation':
        sd=np.sqrt(np.diag(cov));cor=cov/np.outer(sd,sd)
        return np.argsort(-np.mean(cor**2,axis=1))[:max_k].tolist()
    for _ in range(max_k):
        # A-optimal: total posterior variance reduction, including the observed
        # coordinate's variance which becomes zero. D-optimal: max variance.
        gain=np.sum(post[:,remaining]**2,axis=0)/np.maximum(np.diag(post)[remaining],1e-12)
        if policy=='d_opt':gain=np.diag(post)[remaining]
        j=remaining[int(np.argmax(gain))];chosen.append(j);remaining.remove(j)
        post-=np.outer(post[:,j],post[j,:])/max(post[j,j],1e-12)
        post=(post+post.T)/2
    return chosen

def predict(mu,cov,x,selected,kind='covariance',train=None,ridge=1.):
    n=len(x);pred=np.tile(mu,(n,1))
    if not selected:return pred
    s=np.array(selected)
    if kind=='covariance':
        coef=np.linalg.solve(cov[np.ix_(s,s)],cov[s,:])
        pred+=(x[:,s]-mu[s])@coef
    elif kind=='ability':
        # Rank-one model, fit by SVD of mean-imputed standardized training data.
        sd=np.sqrt(np.diag(cov));z=np.nan_to_num((train-mu)/sd)
        _,_,vt=np.linalg.svd(z,full_matrices=False);loading=vt[0]
        latent=((x[:,s]-mu[s])/sd[s])@loading[s]/(loading[s]@loading[s]+.01)
        pred+=latent[:,None]*loading[None,:]*sd[None,:]
    elif kind=='ridge':
        # Missing features get training means; each target uses its observed rows.
        z=np.nan_to_num(train[:,s]-mu[s]);q=x[:,s]-mu[s]
        for j in range(len(mu)):
            obs=np.isfinite(train[:,j]);a=z[obs];y=train[obs,j]-mu[j]
            coef=np.linalg.solve(a.T@a+ridge*np.eye(len(s)),a.T@y)
            pred[:,j]+=q@coef
    elif kind!='mean':raise ValueError(kind)
    pred=np.clip(pred,-1,1)
    pred[:,s]=x[:,s]
    return pred

def losses(x,pred,selected,sd):
    target=np.isfinite(x);target[:,selected]=False
    error=np.where(target,pred-x,np.nan)
    return dict(mae=np.nanmean(np.abs(error),axis=1),mse=np.nanmean(error**2,axis=1),
                standardized_mse=np.nanmean((error/sd)**2,axis=1),
                n_targets=target.sum(axis=1))

def factor_covariance(train,rank=4,steps=20):
    mu=np.nanmean(train,axis=0);sd=np.nanstd(train,axis=0);sd=np.maximum(sd,1e-4)
    obs=np.isfinite(train);z=np.nan_to_num((train-mu)/sd);filled=z.copy()
    for _ in range(steps):
        u,s,v=np.linalg.svd(filled,full_matrices=False)
        low=(u[:,:rank]*s[:rank])@v[:rank]
        filled=np.where(obs,z,low)
    cov=np.cov(low,rowvar=False)*np.outer(sd,sd)
    resid=np.nanmean(np.where(obs,(z-low)**2,np.nan),axis=0)*sd**2
    return mu,cov+np.diag(np.maximum(resid,1e-6))
