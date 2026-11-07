"""All statistical experiments. Seeds, raw repetition summaries, and aggregate CSVs."""
import argparse, json, pathlib, time
import numpy as np
import pandas as pd
from scipy.stats import beta, binom

ROOT=pathlib.Path(__file__).resolve().parents[1]
ALPHA=.05

def cp_table(n,alpha=.05):
    s=np.arange(n+1)
    lo=np.zeros(n+1);hi=np.ones(n+1)
    lo[1:]=beta.ppf(alpha/2,s[1:],n-s[1:]+1)
    hi[:-1]=beta.ppf(1-alpha/2,s[:-1]+1,n-s[:-1])
    return lo,hi

def paired_p(w,l):
    return binom.sf(w-1,w+l,.5)  # zero discordances gives p=1

def winner(counts,rng):
    # Random priorities are independent of outcomes and uniform over exact ties.
    return np.argmax(counts+rng.uniform(0,.1,size=counts.shape),axis=1)

def summarize(x):
    x=np.asarray(x,dtype=float)
    return float(x.mean()),float(x.std(ddof=1)/np.sqrt(len(x)))

def evaluate(counts,mu,n,rng,audit_counts=None,wins=None,losses=None,k_penalty=None):
    r,k=counts.shape;rows=np.arange(r);j=winner(counts,rng)
    s=counts[rows,j];target=np.broadcast_to(mu,(r,k))[rows,j]
    lo,hi=cp_table(n);bl,bh=cp_table(n,ALPHA/(k_penalty or k))
    report=s/n
    baseline=np.broadcast_to(mu,(r,k))[:,0]
    out=dict(optimism=report-target,reported_gain=report-counts[:,0]/n,
             actual_gain=target-baseline, selected_target=target,
             naive_cover=(lo[s]<=target)&(target<=hi[s]),naive_width=hi[s]-lo[s],
             simultaneous_cover=(bl[s]<=target)&(target<=bh[s]),
             simultaneous_width=bh[s]-bl[s],
             apparent_win=(s>counts[:,0]),
             wrong_apparent_win=(s>counts[:,0])&(target<=baseline))
    if audit_counts is not None:
        a=audit_counts[rows,j]
        out.update(audit_bias=a/n-target,audit_cover=(lo[a]<=target)&(target<=hi[a]),audit_width=hi[a]-lo[a])
    if wins is not None:
        p=paired_p(wins[rows,j],losses[rows,j]);null=target<=baseline+1e-12
        out.update(naive_false_superiority=(p<ALPHA)&null,
                   adjusted_false_superiority=(p<ALPHA/max(k-1,1))&null,
                   naive_superiority=(p<ALPHA),adjusted_superiority=(p<ALPHA/max(k-1,1)))
    summary={}
    for name,value in out.items():
        summary[name],summary[name+'_se']=summarize(value)
    return summary,out,j

def synthetic(repetitions):
    rng=np.random.default_rng(77301);summaries=[];raw=[]
    for rho in [0,.5,.9]:
      for n in [32,128,512]:
       # Generate max K once: all K analyses share nested candidate realizations.
       common_n=rng.binomial(n,rho,size=repetitions)
       common_s=rng.binomial(common_n,.3)
       private_n=n-common_n
       b=rng.binomial(private_n,.3)
       w=rng.binomial((private_n-b)[:,None],.3,size=(repetitions,64))
       l=rng.binomial(b[:,None],.7,size=(repetitions,64));w[:,0]=0;l[:,0]=0
       counts=common_s[:,None]+b[:,None]+w-l
       audit=rng.binomial(n,.3,size=(repetitions,64))
       for k in [1,4,16,64]:
        s,o,j=evaluate(counts[:,:k],np.full(k,.3),n,rng,audit[:,:k],w[:,:k],l[:,:k])
        s.update(rho=rho,n=n,k=k,repetitions=repetitions);summaries.append(s)
        raw.append(dict(rho=rho,n=n,k=k,winner=j.tolist(),optimism=o['optimism'].tolist()))
    pd.DataFrame(summaries).to_csv(ROOT/'results/synthetic.csv',index=False)
    (ROOT/'results/synthetic_repetitions.json').write_text(json.dumps(raw))

def load_matrix():
    mat=np.full((2048,24),-1,dtype=np.int8);seen=set();tokens=0;truncated=0
    for line in (ROOT/'data/responses.jsonl').open():
        r=json.loads(line);key=(r['position'],r['candidate'])
        if key in seen:raise RuntimeError('Duplicate response')
        seen.add(key);mat[key]=r['correct'];tokens+=r['tokens_evaluated'] or 0
        truncated+=bool(r['truncated'])
    if (mat<0).any():raise RuntimeError(f'Incomplete matrix: {len(seen)} / {mat.size}')
    if truncated:raise RuntimeError('Truncated prompts')
    np.savez_compressed(ROOT/'data/correctness.npz',correct=mat)
    return mat,dict(responses=len(seen),evaluated_tokens=tokens,truncated=truncated)

def heterogeneous(repetitions):
    # Secondary analysis, specified before the real locked audit.
    rng=np.random.default_rng(77302);rows=[];n=128;k=64
    for gap in [0,.02,.05,.15]:
        mu=np.full(k,.3);mu[1]+=gap
        b=rng.binomial(n,.3,size=repetitions)
        w=rng.binomial((n-b)[:,None],mu[None,:],size=(repetitions,k))
        l=rng.binomial(b[:,None],1-mu[None,:],size=(repetitions,k));w[:,0]=0;l[:,0]=0
        counts=b[:,None]+w-l;aud=rng.binomial(n,mu,size=(repetitions,k))
        sr,out,j=evaluate(counts,mu,n,rng,aud,w,l)
        sr.update(gap=gap,n=n,k=k,repetitions=repetitions)
        for key,val in dict(oracle_regret=mu.max()-mu[j],optimal_selection=(mu[j]==mu.max())).items():
            sr[key],sr[key+'_se']=summarize(val)
        rows.append(sr)
    pd.DataFrame(rows).to_csv(ROOT/'results/heterogeneous.csv',index=False)

def real(repetitions):
    mat,metadata=load_matrix();dev=mat[:1024];audit=mat[1024:]
    rng=np.random.default_rng(88302)
    order=np.r_[0,np.random.default_rng(5539).permutation(np.arange(1,24))]
    summaries=[];raw={}; budget=[];call_budget=[]
    for n in [32,64,128,256]:
      ids=rng.integers(0,len(dev),size=(repetitions,n))
      a_ids=rng.integers(0,len(dev),size=(repetitions,n))
      sampled=dev[ids][:,:,order]
      counts=sampled.sum(axis=1);ac=dev[a_ids][:,:,order].sum(axis=1)
      w=((sampled==1)&(sampled[:,:,[0]]==0)).sum(axis=1)
      l=((sampled==0)&(sampled[:,:,[0]]==1)).sum(axis=1)
      for k in [1,4,8,16,24]:
        mu=dev[:,order[:k]].mean(axis=0)
        s,o,j=evaluate(counts[:,:k],mu,n,rng,ac[:,:k],w[:,:k],l[:,:k])
        # A genuinely separate item set: only its uncertainty is included here.
        # This is not a population-coverage experiment with known truth.
        weights=np.bincount(j,minlength=k)/repetitions
        weighted_audit=audit[:,order[:k]]@weights
        auditref=counts[np.arange(repetitions),j]/n-audit[:,order[:k]].mean(axis=0)[j]
        s['audit_referenced_optimism'],s['audit_referenced_optimism_mcse']=summarize(auditref)
        s['audit_referenced_optimism_audit_se']=float(weighted_audit.std(ddof=1)/np.sqrt(len(audit)))
        s['weighted_audit_accuracy']=float(weighted_audit.mean())
        s.update(n=n,k=k,repetitions=repetitions);summaries.append(s)
        raw[f'n{n}_k{k}_optimism']=o['optimism']
        raw[f'n{n}_k{k}_winner']=order[j]
      full_target=o['selected_target'].copy()
      # Equal total question budget: split n rows into n/2 tuning and n/2 audit.
      nh=n//2;tc=sampled[:,:nh,:].sum(axis=1);hc=sampled[:,nh:,:].sum(axis=1)
      mu=dev[:,order].mean(axis=0)
      s,o,j=evaluate(tc,mu,nh,rng,hc)
      s['quality_difference'],s['quality_difference_se']=summarize(o['selected_target']-full_target)
      s.update(total_n=n,tune_n=nh,audit_n=nh,k=24,repetitions=repetitions)
      budget.append(s)
      # Precisely equal number of model calls, audit only the selected program.
      h=24*int(np.ceil(n/24));t=n-int(np.ceil(n/24))
      tc=sampled[:,:t,:].sum(axis=1)
      hd=dev[rng.integers(0,len(dev),size=(repetitions,h))][:,:,order]
      hc=hd.sum(axis=1);j=winner(tc,rng);rows=np.arange(repetitions)
      hs=hc[rows,j];target=mu[j];cl,ch=cp_table(h)
      vals=dict(audit_bias=hs/h-target,audit_cover=(cl[hs]<=target)&(target<=ch[hs]),
                audit_width=ch[hs]-cl[hs],selected_target=target,actual_gain=target-mu[0],
                quality_difference=target-full_target)
      sr=dict(total_calls=24*n,reuse_n=n,tune_n=t,audit_n=h,k=24)
      for key,value in vals.items():sr[key],sr[key+'_se']=summarize(value)
      call_budget.append(sr)
    pd.DataFrame(summaries).to_csv(ROOT/'results/real_replay.csv',index=False)
    pd.DataFrame(budget).to_csv(ROOT/'results/budget.csv',index=False)
    pd.DataFrame(call_budget).to_csv(ROOT/'results/call_budget.csv',index=False)
    np.savez_compressed(ROOT/'results/real_repetitions.npz',**raw)
    # Primary locked audit (candidate frozen before reading audit outcomes).
    scores=dev[:128].mean(axis=0);chosen=int(np.argmax(scores))
    frozen=json.loads((ROOT/'logs/locked_choice.json').read_text())
    if chosen!=frozen['candidate'] or frozen['audit_responses_observed']!=0:
        raise RuntimeError('Locked-audit integrity check failed')
    s=int(audit[:,chosen].sum());lo,hi=cp_table(len(audit));w=int(((audit[:,chosen]==1)&(audit[:,0]==0)).sum())
    l=int(((audit[:,chosen]==0)&(audit[:,0]==1)).sum())
    # Exact paired-difference CI by Bonferroni on two discordance probabilities.
    dl,dh=cp_table(len(audit),.025)
    primary=dict(candidate=chosen,tune_n=128,audit_n=len(audit),tune_score=float(scores[chosen]),
        baseline_tune=float(scores[0]),audit_score=s/len(audit),audit_successes=s,
        audit_ci=[float(lo[s]),float(hi[s])],baseline_audit=float(audit[:,0].mean()),
        paired_wins=w,paired_losses=l,paired_p=float(paired_p(w,l)),
        audit_gain=(w-l)/len(audit),paired_gain_ci=[float(dl[w]-dh[l]),float(dh[w]-dl[l])])
    corr=np.corrcoef(dev.T);off=corr[np.triu_indices(24,1)]
    metadata.update(primary=primary,candidate_order=order.tolist(),
        mean_pair_correlation=float(off.mean()),min_pair_correlation=float(off.min()),max_pair_correlation=float(off.max()),
        development_means=dev.mean(axis=0).tolist(),audit_means=audit.mean(axis=0).tolist(),
        dev_accuracy_range=[float(dev.mean(axis=0).min()),float(dev.mean(axis=0).max())])
    (ROOT/'results/real_metadata.json').write_text(json.dumps(metadata,indent=2))
    # Program duplication: same counts, identical selected accuracy, but raw K penalty.
    dup=[];n=128
    idx=np.random.default_rng(11003).integers(0,len(dev),size=(repetitions,n))
    counts=dev[idx].sum(axis=1)
    for penalty in [24,192]:
        sr,_,_=evaluate(counts,dev.mean(axis=0),n,np.random.default_rng(22003),k_penalty=penalty)
        sr.update(k_penalty=penalty,n=n);dup.append(sr)
    pd.DataFrame(dup).to_csv(ROOT/'results/duplication.csv',index=False)
    # Paired difference covariance measures shared difficulty, no claimed effective K estimator.
    pd.DataFrame(corr).to_csv(ROOT/'results/candidate_correlations.csv',index=False)

def paired_call_budget(repetitions):
    # Final-validation correction: a paired audit costs 2h, not h.
    # Separate RNG leaves every original experiment's draws unchanged.
    dev=np.load(ROOT/'data/correctness.npz')['correct'][:1024]
    rng=np.random.default_rng(88303);k=24;mu=dev.mean(axis=0);summaries=[]
    for n in [32,64,128,256]:
        removed=int(np.ceil(2*n/k));t=n-removed;h=(k//2)*removed
        tune=dev[rng.integers(0,len(dev),size=(repetitions,t))].sum(axis=1)
        j=winner(tune,rng);rows=np.arange(repetitions)
        audit=dev[rng.integers(0,len(dev),size=(repetitions,h))]
        chosen=audit[rows,:,j];base=audit[:,:,0]
        # Advanced indexing above gives (repetitions,h), checked explicitly.
        assert chosen.shape==(repetitions,h)
        w=((chosen==1)&(base==0)).sum(axis=1)
        l=((chosen==0)&(base==1)).sum(axis=1)
        pv=paired_p(w,l);target=mu[j];s=chosen.sum(axis=1);cl,ch=cp_table(h)
        values=dict(false_superiority=(pv<ALPHA)&(target<=mu[0]+1e-12),
            superiority=(pv<ALPHA),selected_target=target,actual_gain=target-mu[0],
            audit_bias=s/h-target,audit_cover=(cl[s]<=target)&(target<=ch[s]),
            audit_width=ch[s]-cl[s])
        out=dict(total_calls=k*t+2*h,reuse_n=n,tune_n=t,audit_n_per_configuration=h,
                 winner_audit_calls=h,baseline_audit_calls=h,k=k,repetitions=repetitions)
        assert out['total_calls']==k*n
        for key,value in values.items():out[key],out[key+'_se']=summarize(value)
        summaries.append(out)
    pd.DataFrame(summaries).to_csv(ROOT/'results/paired_call_budget.csv',index=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['synthetic','real','all'],default='all')
    p.add_argument('--repetitions',type=int,default=4000);a=p.parse_args();start=time.time()
    if a.mode in ['synthetic','all']:
        synthetic(a.repetitions);heterogeneous(a.repetitions)
    if a.mode in ['real','all']:
        real(a.repetitions);paired_call_budget(a.repetitions)
    with (ROOT/'logs/analysis_runs.jsonl').open('a') as f:
        f.write(json.dumps(dict(mode=a.mode,repetitions=a.repetitions,elapsed_seconds=time.time()-start))+'\n')

if __name__=='__main__':main()
