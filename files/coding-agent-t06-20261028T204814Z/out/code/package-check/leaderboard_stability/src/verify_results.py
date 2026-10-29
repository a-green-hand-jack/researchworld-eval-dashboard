"""Independent real-data refits, saved witness checks, and generated-PDF audit."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from bt import Data
from experiment import load
R=Path(__file__).resolve().parents[1]
def main():
 attacks=json.load(open(R/'results/attacks.json'));checks=[]
 for rec in attacks:
  if rec['mode']!='influence':continue
  d=load(rec['dataset']);t=d.fit();i=np.where(d.names==rec['leader'])[0][0];j=np.where(d.names==rec['runner'])[0][0]
  ids=np.array(rec['edited_ids']);assert len(set(ids))==rec['k'];assert np.all(d.y[ids]!=.5)
  def refit(w):
   def fun(v):
    z=d.X@v
    return np.sum(d.count*np.logaddexp(0,z)-w*z)+.001*np.dot(v,v)/2,d.X.T@(d.count*expit(z)-w)+.001*v
   opt=minimize(fun,np.zeros(d.m),jac=True,method='BFGS',options={'gtol':1e-8,'maxiter':1000})
   return opt.x-opt.x.mean(),np.max(np.abs(fun(opt.x)[1])),bool(opt.success),str(opt.message)
  v,res,ok,msg=refit(d.wins);vv,res2,ok2,msg2=refit(d.edited_wins(ids));before=d.fit(wins=d.edited_wins(ids[:-1]),start=t)
  assert np.max(np.abs(v-t))<1e-5
  assert v[i]>v[j] and vv[i]<vv[j] and before[i]>=before[j]-1e-9
  assert max(res,res2)<1e-5
  checks.append({'dataset':d.name,'k':len(ids),'initial_gap_independent':v[i]-v[j],'changed_gap_independent':vv[i]-vv[j],'max_gradient_independent':float(max(res,res2)),'fit_difference':float(np.max(np.abs(v-t))),'bfgs_success':[ok,ok2],'bfgs_messages':[msg,msg2]})
 m=pd.read_csv(R/'results/matched.csv');w=m.pivot(index='rep',columns='design',values='pair_radius');assert (w.gpt4>w.human).all();assert (m.n==1485).all()
 ex=pd.read_csv(R/'results/balanced_exact.csv');assert len(ex)==15;assert (ex.before_gap>=-1e-8).all() and (ex.after_gap<0).all()
 summary={'independent_checks':checks,'matched_panels':len(w),'exact_full_gpt_pair_checks':len(ex)}
 (R/'results/verification.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
