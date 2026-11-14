"""Independent numerical checks of Gaussian risk and fixed common targets."""
import json,pathlib,time
import numpy as np
import pandas as pd
from methods import moments,predict,losses
ROOT=pathlib.Path(__file__).resolve().parents[1]
def gaussian_check():
 rng=np.random.default_rng(913);b=rng.normal(size=(12,4));cov=b@b.T+.2*np.eye(12);selected=[0,3,7]
 target=[j for j in range(12) if j not in selected]
 coef=np.linalg.solve(cov[np.ix_(selected,selected)],cov[np.ix_(selected,target)])
 conditional=cov[np.ix_(target,target)]-cov[np.ix_(target,selected)]@coef
 x=rng.multivariate_normal(np.zeros(12),cov,size=100000);error=x[:,target]-x[:,selected]@coef
 sample=(error**2).sum(axis=1);expected=np.trace(conditional);se=sample.std(ddof=1)/np.sqrt(len(sample))
 result={'seed':913,'simulated_samples':len(x),'expected_total_squared_error':expected,'measured_total_squared_error':sample.mean(),'monte_carlo_standard_error':se,'z_error':(sample.mean()-expected)/se}
 (ROOT/'results/gaussian_identity.json').write_text(json.dumps(result,indent=2)+'\n');assert abs(result['z_error'])<5

def fixed_targets(dataset):
 frame=pd.read_csv(ROOT/f'data/{dataset}.csv',index_col=0);n=frame.shape[1];rows=[];design=[]
 splits=json.load(open(ROOT/f'results/{dataset}_random/splits.json'))
 for split in splits:
  seed=split['seed'];train=frame.loc[split['train_names']].to_numpy();test=frame.loc[split['test_names']].to_numpy()
  mu,cov=moments(train,split['alpha']);sd=np.maximum(np.nanstd(train,axis=0,ddof=1),1e-4)
  rng=np.random.default_rng(seed+500);target=rng.choice(n,size=max(2,round(n*.2)),replace=False);candidates=[j for j in range(n) if j not in target]
  ks=[k for k in [1,2,4,8,16] if k<=len(candidates)]
  for policy in ['a_opt','d_opt','random']:
   for draw in range(8 if policy=='random' else 1):
    remain=candidates.copy();q=[];post=cov.copy();rng=np.random.default_rng(seed*100+draw)
    if policy=='random':q=rng.permutation(remain).tolist()
    else:
     for _ in range(max(ks)):
      gain=np.sum(post[:,remain]**2,axis=0)/np.maximum(np.diag(post)[remain],1e-12)
      if policy=='d_opt':gain=np.diag(post)[remain]
      j=remain[int(np.argmax(gain))];q.append(j);remain.remove(j)
      post-=np.outer(post[:,j],post[j,:])/max(post[j,j],1e-12);post=(post+post.T)/2
    for k in ks:
     pp=predict(mu,cov,test,q[:k]);err=pp[:,target]-test[:,target]
     for i,model in enumerate(split['test_names']):rows.append(dict(dataset=dataset,condition='fixed_targets',seed=seed,draw=draw,method=policy+'_covariance',k=k,model=model,mae=float(np.abs(err[i]).mean()),mse=float((err[i]**2).mean()),standardized_mse=float(((err[i]/sd[target])**2).mean()),n_targets=len(target)))
     design.append(dict(seed=seed,draw=draw,method=policy,k=k,queries=frame.columns[q[:k]].tolist(),targets=frame.columns[target].tolist()))
 out=ROOT/f'results/{dataset}_fixed_targets';out.mkdir(exist_ok=True)
 pd.DataFrame(rows).to_csv(out/'model_losses.csv',index=False);(out/'designs.json').write_text(json.dumps(design,indent=2)+'\n')
if __name__=='__main__':
 gaussian_check()
 for dataset in ['mteb','open_llm']:fixed_targets(dataset)
 print('HUTIAN_WAKE: covariance identity and common-target diagnostics complete',flush=True)
