"""Known-truth correlated Bernoulli winner-selection experiments.

Counts are generated exactly without materializing rows. On each question a
Bernoulli(rho) switch chooses either one shared Uniform(0,1) across candidates
or independent uniforms. Thus means p are exact and equal-p outcome correlation
is rho. Unequal-p correlations are given in docs/synthetic-spec.md.
"""
import argparse, json, pathlib, time, platform, resource
import numpy as np
import pandas as pd
from scipy.stats import beta


def cp_table(n, alpha):
    x=np.arange(n+1)
    lo=np.zeros(n+1);hi=np.ones(n+1)
    lo[1:]=beta.ppf(alpha/2,x[1:],n-x[1:]+1)
    hi[:-1]=beta.ppf(1-alpha/2,x[:-1]+1,n-x[:-1])
    return lo,hi


def joint_counts(rng, reps, n, p, rho):
    """Independent replicates of n paired rows from specified mixture."""
    k=len(p); order=np.argsort(p); sorted_p=p[order]
    probs=np.diff(np.r_[0.,sorted_p,1.]);out=np.empty((reps,k),dtype=np.int32)
    common_n=rng.binomial(n,rho,size=reps)
    # The multinomial has a different sample size per replicate.
    common_bins=rng.multinomial(common_n,probs)
    common_success=np.cumsum(common_bins[:,:-1],axis=1)
    out[:,order]=common_success
    out+=rng.binomial((n-common_n)[:,None],p[None,:])
    return out


def run_cell(reps,n,k,rho,spread,seed,candidate_means=None,counts_fn=joint_counts):
    rng=np.random.default_rng(seed)
    # Candidate 0 is a frozen default; others range around its known quality.
    p=np.full(k,.4)
    if k>1: p[1:]=.4+np.linspace(-spread,spread,k-1) if k>2 else .4+spread
    if candidate_means is not None:
        p=np.asarray(candidate_means,dtype=float);assert len(p)==k
    counts=counts_fn(rng,reps,n,p,rho)
    # Uniform tie breaks, independent of holdout. Avoid first-index advantage.
    tie_random=rng.random(counts.shape)
    winner=np.argmax(counts+tie_random,axis=1)
    idx=np.arange(reps); selected=counts[idx,winner];truth=p[winner]
    # Independent audit observes just the frozen winner.
    hold=rng.binomial(n,truth)
    naive=cp_table(n,.05);sim=cp_table(n,.05/k)
    # Equal total question budget: split n questions into floor(n/2) search/rest audit.
    ns=n//2;nh=n-ns
    split_counts=counts_fn(rng,reps,ns,p,rho)
    split_win=np.argmax(split_counts+rng.random(split_counts.shape),axis=1)
    split_truth=p[split_win];split_audit=rng.binomial(nh,split_truth)
    split_ci=cp_table(nh,.05)
    # Equal total model-call budget: n*k calls, s*k+h calls with h=s approximately.
    cs=max(1,(n*k)//(k+1));ch=n*k-cs*k
    call_counts=counts_fn(rng,reps,cs,p,rho)
    call_win=np.argmax(call_counts+rng.random(call_counts.shape),axis=1)
    call_truth=p[call_win];call_audit=rng.binomial(ch,call_truth)
    call_ci=cp_table(ch,.05)
    # False superiority means reported positive claim although p_w<=p_default.
    # Marginal one-sided bounds at alpha/2 per side via a two-sided CP alpha=.10.
    pair=cp_table(n,.05) # each one-sided error .025; union <= .05 for frozen pair
    false=(truth<=p[0]+1e-12)
    decision_naive=(pair[0][selected]>pair[1][counts[:,0]]) & (winner!=0)
    decision_sim=(sim[0][selected]>sim[1][counts[:,0]]) & (winner!=0)
    metrics={
      'optimism_reused':selected/n-truth,
      'bias_independent_audit':hold/n-truth,
      'bias_split_question_budget':split_audit/nh-split_truth,
      'bias_split_call_budget':call_audit/ch-call_truth,
      'selected_quality':truth,'regret':p.max()-truth,
      'quality_split_question_budget':split_truth,'quality_split_call_budget':call_truth,
      'coverage_naive':(naive[0][selected]<=truth)&(truth<=naive[1][selected]),
      'coverage_simultaneous':(sim[0][selected]<=truth)&(truth<=sim[1][selected]),
      'coverage_independent_audit':(naive[0][hold]<=truth)&(truth<=naive[1][hold]),
      'coverage_split_question_budget':(split_ci[0][split_audit]<=split_truth)&(split_truth<=split_ci[1][split_audit]),
      'coverage_split_call_budget':(call_ci[0][call_audit]<=call_truth)&(call_truth<=call_ci[1][call_audit]),
      'width_naive':naive[1][selected]-naive[0][selected],
      'width_simultaneous':sim[1][selected]-sim[0][selected],
      'width_independent_audit':naive[1][hold]-naive[0][hold],
      'width_split_question_budget':split_ci[1][split_audit]-split_ci[0][split_audit],
      'width_split_call_budget':call_ci[1][call_audit]-call_ci[0][call_audit],
      'false_superiority_naive':false&decision_naive,
      'false_superiority_simultaneous':false&decision_sim,
      'selection_is_default':winner==0,
      'mse_reused':(selected/n-truth)**2,
      'mse_independent_audit':(hold/n-truth)**2,
      'mse_split_question_budget':(split_audit/nh-split_truth)**2,
      'mse_split_call_budget':(call_audit/ch-call_truth)**2,
    }
    rows=[]
    for name,v in metrics.items():
        v=np.asarray(v,dtype=float)
        rows.append(dict(n=n,k=k,rho=rho,spread=spread,reps=reps,seed=int(seed),metric=name,mean=float(v.mean()),mcse=float(v.std(ddof=1)/np.sqrt(reps))))
    return rows


def main():
 p=argparse.ArgumentParser();p.add_argument('--reps',type=int,default=10000);p.add_argument('--pilot',action='store_true');p.add_argument('--out',required=True);a=p.parse_args()
 specs=[(n,k,r,s) for n in [16,32,64,128,256,512] for k in [1,2,4,8,16,32,64,128] for r in [0.,.5,.9] for s in [0.,.08]]
 if a.pilot:specs=[(64,16,.5,0.),(512,128,.9,.08),(16,128,0.,0.)]
 seeds=np.random.SeedSequence(20261103).spawn(len(specs));out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 t0=time.perf_counter();c0=time.process_time()
 with out.open('w') as f:
  for i,(spec,ss) in enumerate(zip(specs,seeds)):
   start=time.perf_counter();rows=run_cell(a.reps,*spec,int(ss.generate_state(1)[0]))
   for row in rows:f.write(json.dumps(row)+'\n')
   f.flush();print(json.dumps(dict(cell=i+1,total=len(specs),spec=spec,wall_seconds=time.perf_counter()-start)),flush=True)
 summary=dict(reps=a.reps,cells=len(specs),wall_seconds=time.perf_counter()-t0,cpu_seconds=time.process_time()-c0,peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,python=platform.python_version(),numpy=np.__version__)
 out.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: synthetic complete '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
