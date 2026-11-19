"""Auxiliary correctness checks and independent-probe precision (pilot seeds only)."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import experiment as e

def main():
    cfg=json.loads((e.ROOT/'config.json').read_text()); rows=[]
    for p in sorted((e.ROOT/'artifacts/pilot').glob('*_fit.npz')):
        z=np.load(p); seed,k,law=p.stem.replace('_fit','').split('_'); seed=int(seed); k=int(k)
        q={m:z['q_'+m] for m in e.METHODS if 'q_'+m in z}
        a,_=e.probe_masses(z['beta'],q,z['sigma'],k,seed,law,cfg['nx'],cfg['nfull'],cfg['nface'],pool=0)
        b,_=e.probe_masses(z['beta'],q,z['sigma'],k,seed,law,cfg['nx'],cfg['nfull'],cfg['nface'],pool=1)
        for mi,m in enumerate(e.METHODS):
            aa=.8*a[mi,0]+.2*a[mi,1]; bb=.8*b[mi,0]+.2*b[mi,1]
            rows.append(dict(seed=seed,K=k,law=law,method=m,dV=abs(aa[0]-bb[0]),dAK=abs(aa[-1]-bb[-1]),dQ=abs(.5*(aa[0]-bb[0])+.5*(aa[1:]-bb[1:]).mean())))
    t=pd.DataFrame(rows); t.to_csv(e.ROOT/'artifacts/pilot/independent_MC.csv',index=False)
    # Generator-only mean/dispersion sanity checks. They do not tune a predictor.
    diagnostics=[]
    for k in cfg['dimensions']:
        for law in cfg['laws']:
            x,y,b,mu=e.generate(100000,k,law,.5,e.rng(999990,k,law,6))
            m=mu.copy()
            if law=='zeros':
                face=mu.copy(); face[:,-1]=0; face/=face.sum(1,keepdims=True)
                m=.65*mu+.35*face
            g=x[:,2].astype(int)
            diagnostics.append(dict(K=k,law=law,max_abs_mean_residual=float(abs((y-m).mean(0)).max()),zero_prevalence=float(b.mean()),n=100000,MSE_G0=float(np.sum((y[g==0]-m[g==0])**2,1).mean()),MSE_G1=float(np.sum((y[g==1]-m[g==1])**2,1).mean())))
    pd.DataFrame(diagnostics).to_csv(e.ROOT/'artifacts/pilot/generator_diagnostics.csv',index=False)
    print(t[['dV','dAK','dQ']].describe().to_string())
    print(pd.DataFrame(diagnostics).to_string(index=False))

if __name__=='__main__': main()
