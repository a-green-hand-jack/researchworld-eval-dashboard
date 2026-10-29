"""Exploratory simultaneous bootstrap contrasts and graph diagnostics."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from bt import load
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results'
rows=[];graphs=[]
for name in ['arena','mt_human','mt_gpt4','nba2013','nba2014','nba2015','matched_human','matched_gpt4']:
 bt=load(name);fit=bt.fit();z=np.load(RES/f'bootstrap_{name}.npz');scores=z['scores'];order=z['order'];p=z['pairs']
 a,b=np.triu_indices(bt.m,k=1);diff=scores[:,a]-scores[:,b];base=fit.theta[a]-fit.theta[b];se=np.std(diff,axis=0,ddof=1)
 maxstat=np.max(np.abs((diff-base)/se),axis=1);q=np.quantile(maxstat,.95)
 for j,(i,k) in enumerate(p):
  stderr=np.std(scores[:,i]-scores[:,k],ddof=1);gap=fit.theta[i]-fit.theta[k]
  rows.append(dict(dataset=name,boundary=j+1,gap=gap,se=stderr,critical=q,sim_lo=gap-q*stderr,sim_hi=gap+q*stderr))
 graph=coo_matrix((np.ones(bt.n),(bt.a,bt.b)),shape=(bt.m,bt.m));ncomp,_=connected_components(graph,directed=False)
 ev=np.linalg.eigvalsh(fit.hessian+bt.gauge)
 graphs.append(dict(dataset=name,components=ncomp,min_hessian_eigenvalue=ev.min(),max_baseline_grad=fit.grad_norm))
pd.DataFrame(rows).to_csv(RES/'simultaneous.csv',index=False);pd.DataFrame(graphs).to_csv(RES/'graph_diagnostics.csv',index=False)
print(pd.DataFrame(rows).groupby('dataset').sim_lo.apply(lambda s:(s>0).sum()).to_string())
