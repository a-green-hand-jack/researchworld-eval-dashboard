#!/usr/bin/env python3
"""Known-population synthetic experiments. No LLM outputs are simulated as real."""
import argparse,json,pathlib,time
import numpy as np
import pandas as pd
from scipy.special import ndtri
from statistics_core import intervals,paired_decision
ROOT=pathlib.Path(__file__).resolve().parents[1]

def conditions():
    rows=[]
    for k in [1,4,16,64]:
        for rho in [0.,.5,.9]: rows.append(dict(regime='tied',n=128,k=k,rho=rho,p=.6))
    for n in [32,512]: rows.append(dict(regime='tied',n=n,k=16,rho=.5,p=.6))
    for n in [32,128,512]: rows.append(dict(regime='separated',n=n,k=16,rho=.5,p=.6))
    for n in [32,128]: rows.append(dict(regime='boundary',n=n,k=16,rho=.5,p=.99))
    rows.append(dict(regime='duplicates',n=128,k=64,rho=1.,p=.6))
    return rows

def generate(rng,c):
    n,k,rho=c['n'],c['k'],c['rho']
    mu=np.linspace(.5,.7,k) if c['regime']=='separated' else np.full(k,c['p'])
    latent=np.sqrt(rho)*rng.standard_normal((n,1))+np.sqrt(1-rho)*rng.standard_normal((n,k))
    x=(latent<ndtri(mu)).astype(float)
    return x,mu

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--reps',type=int,default=1500); ap.add_argument('--bootstrap',type=int,default=499); args=ap.parse_args()
    start=time.time(); rows=[]; dec=[]; summaries=[]
    for ci,c in enumerate(conditions()):
        rng=np.random.default_rng(1907+ci)
        for rep in range(args.reps):
            x,mu=generate(rng,c); bands,j=intervals(x,rng,args.bootstrap)
            base={**c,'condition':ci,'rep':rep,'selected':j,'optimism':float(x[:,j].mean()-mu[j]),'selected_mu':float(mu[j]),'regret':float(mu.max()-mu[j])}
            for method,(lo,hi,jm) in bands.items():
                rows.append({**base,'method':method,'coverage':int(lo<=mu[jm]<=hi),'width':hi-lo,'lower':lo,'upper':hi,'target':mu[jm]})
            jj,lower=paired_decision(x,rng,args.bootstrap)
            for method,l in lower.items():
                dec.append({**c,'condition':ci,'rep':rep,'method':method,'claim':int(l>0),'false_claim':int(l>0 and mu[jj]<=mu[0]+1e-12),'true_delta':mu[jj]-mu[0]})
        print(f"condition={ci} {c} elapsed={time.time()-start:.1f}s",flush=True)
    result=ROOT/'artifacts/results'; result.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(rows); df.to_csv(result/'synthetic_replicates.csv.gz',index=False)
    keys=['condition','regime','n','k','rho','p','method']
    s=df.groupby(keys).agg(coverage=('coverage','mean'),width=('width','mean'),optimism=('optimism','mean'),optimism_sd=('optimism','std'),regret=('regret','mean'),reps=('rep','count')).reset_index()
    s['coverage_mcse']=np.sqrt(s.coverage*(1-s.coverage)/s.reps); s['optimism_mcse']=s.optimism_sd/np.sqrt(s.reps)
    s.to_csv(result/'synthetic_summary.csv',index=False)
    dd=pd.DataFrame(dec); dd.to_csv(result/'synthetic_decisions.csv.gz',index=False)
    dd.groupby(keys).agg(claim_rate=('claim','mean'),false_claim_rate=('false_claim','mean'),true_delta=('true_delta','mean'),reps=('rep','count')).reset_index().to_csv(result/'synthetic_decision_summary.csv',index=False)
    (ROOT/'logs/synthetic_run.json').write_text(json.dumps({'seconds':time.time()-start,'reps':args.reps,'bootstrap':args.bootstrap,'conditions':conditions(),'seed_rule':'1907 + condition index','note':'latent Gaussian rho, not observed Bernoulli correlation'},indent=2))
    print('DONE',time.time()-start)
if __name__=='__main__': main()
