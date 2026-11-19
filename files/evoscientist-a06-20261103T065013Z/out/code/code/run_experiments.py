"""Execute all frozen known-truth, replay, and sensitivity cells on CPU."""
import argparse,hashlib,json,pathlib,time
import numpy as np
import pandas as pd
from scipy.stats import norm,binom,binomtest
from statistics import evaluate,cp_table
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
R=2000;B=999
METHODS=['Naive-Wilson','Simult-Hoeffding','Multiplier','Guarded-multiplier','Audit-Wilson','Audit-exact']

def sid(s):return int(hashlib.sha256(s.encode()).hexdigest()[:8],16)
def scalar(v):return v.item() if hasattr(v,'item') else v

def summary(meta,result,intervals):
    rows=[];base=dict(meta);base['R']=len(result['winner'])
    for name in METHODS:
      c=result[name+'__cover'].astype(float);w=result[name+'__width'];N=len(c)
      row=base|{'method':name,'coverage':c.mean(),'coverage_mcse':c.std(ddof=1)/np.sqrt(N),'mean_width':w.mean(),'width_mcse':w.std(ddof=1)/np.sqrt(N),'median_width':np.median(w),'p90_width':np.quantile(w,.9),'optimism':result['optimism'].mean(),'optimism_mcse':result['optimism'].std(ddof=1)/np.sqrt(N),'optimism_sd':result['optimism'].std(ddof=1),'audit_gap':result['audit_gap'].mean(),'remainder_optimism':result['remainder_optimism'].mean(),'tie_rate':result['tie'].mean(),'guard_rate':result['guard'].mean(),'zero_variance_rate':result['zero_var'].mean(),'naive_promotion':result['naive_promote'].mean(),'naive_false_promotion':np.mean(result['naive_promote']&result['nonpositive']),'honest_promotion':result['pair_promote'].mean(),'honest_false_promotion':np.mean(result['pair_promote']&result['nonpositive']),'nonpositive_frequency':result['nonpositive'].mean(),'paired_coverage':result['pair_cover'].mean(),'paired_width':result['pair_width'].mean(),'audit_remainder_coverage':result['audit_remainder_cover'].mean(),'audit_remainder_bias':result['audit_bias'].mean()}
      mc_interval=cp_table(N)[int(c.sum())]
      row['coverage_mc_ci_lower']=mc_interval[0];row['coverage_mc_ci_upper']=mc_interval[1]
      rows.append(row)
    return rows

def save_cell(meta,res,ci):
    name=meta['cell'];np.savez_compressed(OUT/'replications'/f'{name}.npz',**res)
    return summary(meta,res,ci)

def synthetic():
    start=time.time();grid=[]
    for n in [16,32,64,128]:
      for rho in [0,.5,.9]:
       for gap in [0,.01,.05]:grid.append({'kind':'core','K':8,'n':n,'rho':rho,'gap':gap,'p0':.7,'m':128})
    for K in [1,2,4,16]:
      for rho in [0,.9]:grid.append({'kind':'K_stress','K':K,'n':64,'rho':rho,'gap':0,'p0':.7,'m':128})
    for p0 in [.3,.95]:
      for rho in [0,.9]:grid.append({'kind':'boundary','K':8,'n':16,'rho':rho,'gap':0,'p0':p0,'m':128})
    for n in [16,64]:grid.append({'kind':'duplicates','K':8,'n':n,'rho':1.,'gap':0,'p0':.7,'m':128})
    primary={'kind':'audit_size','K':8,'n':64,'rho':.5,'gap':0,'p0':.7,'m':128}
    grid.extend([primary|{'m':m} for m in [32,64]])
    grid.append(primary|{'kind':'independent_multiplier','independent':True})
    for n in [16,64]:
      grid.append(primary|{'kind':'B_sensitivity','n':n,'R':200,'B':3999})
      grid.append(primary|{'kind':'B_sensitivity_low','n':n,'R':200,'B':999})
    rows=[]
    for ix,meta0 in enumerate(grid):
      meta=meta0.copy();K=meta['K'];n=meta['n'];rho=meta['rho'];gap=meta['gap'];p0=meta['p0'];m=meta['m'];reps=meta.get('R',R);draws=meta.get('B',B)
      key=f'{K}_{rho}_{gap}_{p0}';rng=np.random.default_rng(1101+sid(key));p=np.full(K,p0)
      if gap:p[-1]+=gap
      # Fixed 256 rows so n and m contrasts share item vectors.
      common=rng.normal(size=(R,256,1));eps=rng.normal(size=(R,256,K))
      Y=(np.sqrt(rho)*common+np.sqrt(1-rho)*eps<=norm.ppf(p)[None,None,:]).astype(float)[:reps]
      S=Y[:,:n,:];A=Y[:,n:n+m,:]
      result,ci=evaluate(S,A,p,np.random.default_rng(5501+sid(key)),B=draws,independent=meta.get('independent',False))
      meta.update({'cell':f'syn_{ix:02d}','domain':'iid_population','B':draws})
      if K>1 and rho<1:
       corr=np.corrcoef(Y.reshape(-1,K),rowvar=False);meta['binary_correlation']=float(corr[np.triu_indices(K,1)].mean())
      else:meta['binary_correlation']=1. if rho==1 else np.nan
      meta['selection_regret']=float(np.mean(p.max()-p[result['winner']]))
      rows.extend(save_cell(meta,result,ci));print('synthetic',ix+1,'/',len(grid),'sec',round(time.time()-start,1),flush=True)
    # Finite-pool complement of primary iid setting.
    rng=np.random.default_rng(7711);p=np.full(8,.7);z=np.sqrt(.5)*rng.normal(size=(600,1))+np.sqrt(.5)*rng.normal(size=(600,8));Y=(z<=norm.ppf(p)).astype(float)
    rows+=finite(Y,'synthetic_finite',only_primary=True)
    pd.DataFrame(rows).to_csv(OUT/'synthetic_summary.csv',index=False)
    # Analytic independent all-equal benchmark, no simulation truth proxy.
    exact=[]
    for K in [1,2,4,8,16]:
      for n in [16,32,64,128]:
        expected_max=sum(1-binom.cdf(x,n,.7)**K for x in range(n))/n
        exact.append({'K':K,'n':n,'p':.7,'exact_independent_optimism':expected_max-.7})
    pd.DataFrame(exact).to_csv(OUT/'analytic_independent.csv',index=False)
    (OUT/'synthetic_runtime.json').write_text(json.dumps({'wall_s':time.time()-start,'cells':len(grid)+1,'R_default':R,'B_default':B},indent=2))
    # Holm audit for guaranteed-method below-nominal coverage across all cells.
    df=pd.DataFrame(rows);q=df[df.method.isin(['Simult-Hoeffding','Audit-exact'])].copy()
    q['p_undercoverage']=[binomtest(int(round(c*r)),int(r),.95,alternative='less').pvalue for c,r in zip(q.coverage,q.R)]
    order=np.argsort(q.p_undercoverage.to_numpy());ps=q.p_undercoverage.to_numpy()[order];adj=np.maximum.accumulate(np.minimum(1,ps*(len(ps)-np.arange(len(ps)))))
    q['holm_p']=1.;q.iloc[order,q.columns.get_loc('holm_p')]=adj;q.to_csv(OUT/'guarantee_audit.csv',index=False)

def finite(Y,domain,only_primary=False):
    N,Kall=Y.shape;replay=np.random.default_rng(3301);perms=np.array([replay.permutation(N) for _ in range(R)]);rows=[]
    subsets={1:[0],2:[0,7],4:[0,3,4,7],8:list(range(8))}
    tasks=[]
    if only_primary:tasks=[('finite_primary',64,128,list(range(8)),False)]
    else:
      for n in [16,32,64,128]:tasks.append(('n_grid',n,128,list(range(8)),False))
      for K in [1,2,4]:tasks.append(('K_grid',64,128,subsets[K],False))
      for m in [32,64]:tasks.append(('audit_size',64,m,list(range(8)),False))
      tasks.append(('independent_multiplier',64,128,list(range(8)),True))
      tasks.append(('no_FPC_multiplier',64,128,list(range(8)),False))
    for ix,(kind,n,m,subset,ind) in enumerate(tasks):
      X=Y[:,subset];S=X[perms[:,:n]];A=X[perms[:,n:n+m]]
      result,ci=evaluate(S,A,X.mean(0),np.random.default_rng(5501),N=N,total_success=X.sum(0),B=B,independent=ind)
      if kind=='no_FPC_multiplier':
        from statistics import multiplier_radius
        rad=multiplier_radius(S.astype(float),np.random.default_rng(5501),B=B,N=None)
        means=S.mean(1);winner=np.argmax(means,axis=1);ss=means[np.arange(R),winner]
        hh=np.sqrt(np.log(2*len(subset)/.05)/(2*n))
        for method,rr in [('Multiplier',rad),('Guarded-multiplier',np.where(result['guard'],hh,rad))]:
          endpoints=np.stack([np.maximum(0,ss-rr),np.minimum(1,ss+rr)],-1);ci[method]=endpoints
          result[method+'__cover']=(endpoints[:,0]<=result['target']+1e-12)&(endpoints[:,1]>=result['target']-1e-12)
          result[method+'__width']=endpoints[:,1]-endpoints[:,0]
      assert np.max(np.abs(result['remainder_optimism']-N/(N-n)*result['optimism']))<1e-12
      meta={'cell':domain+'_'+str(ix),'domain':domain,'kind':kind,'K':len(subset),'n':n,'m':m,'N':N,'B':B}
      rows.extend(save_cell(meta,result,ci));print(domain,kind,n,m,len(subset),flush=True)
    return rows

def real():
    start=time.time();cfg=json.loads((ROOT/'data/config.json').read_text());N=cfg['N'];K=cfg['K']
    records=[json.loads(s) for s in (ROOT/'data/responses.jsonl').read_text().splitlines()];assert len(records)==N*K
    Y=np.full((N,K),-1,dtype=int);bad=np.zeros_like(Y)
    for r in records:
      assert Y[r['row'],r['prompt_id']]==-1
      Y[r['row'],r['prompt_id']]=r['correct'];bad[r['row'],r['prompt_id']]=r['format_failure']
    assert np.all(Y>=0);np.save(ROOT/'data/outcomes.npy',Y)
    # Independently rebuild parser scores from raw content.
    from collect import parse_answer
    cohort=json.loads((ROOT/'data/cohort.json').read_text())
    for r in records:
      item=cohort[r['row']];text=r['response']['choices'][0]['message'].get('content') or '';a=parse_answer(text,item['options']);assert int(a==item['answer'])==r['correct']
      reqtext=r['request']['messages'][0]['content'];assert 'cot_content' not in reqtext
    prompts=[]
    for j in range(K):
      rs=[r for r in records if r['prompt_id']==j]
      prompts.append({'prompt_id':j,'accuracy':Y[:,j].mean(),'correct':int(Y[:,j].sum()),'format_failures':int(bad[:,j].sum()),'length_finishes':sum(r['response']['choices'][0].get('finish_reason')=='length' for r in rs),'mean_completion_tokens':np.mean([r['response'].get('usage',{}).get('completion_tokens',0) for r in rs])})
    pd.DataFrame(prompts).to_csv(OUT/'prompt_summary.csv',index=False)
    corr=np.corrcoef(Y,rowvar=False);pd.DataFrame(corr).to_csv(OUT/'prompt_correlation.csv',index=False)
    rows=finite(Y,'real_cache');pd.DataFrame(rows).to_csv(OUT/'real_summary.csv',index=False)
    # Single precommitted replay illustration; not a prospectively blinded audit.
    perm=np.random.default_rng(4401).permutation(N);n=64;m=128;S=Y[perm[:n]];A=Y[perm[n:n+m]];j=int(np.argmax(S.mean(0)));x=int(A[:,j].sum());s=float(S[:,j].mean())
    from statistics import hg_table
    rem=hg_table(N-n,m,.025)[x];pool=n/N*s+(N-n)/N*rem
    plus=int(((A[:,j]==1)&(A[:,0]==0)).sum());minus=int(((A[:,j]==0)&(A[:,0]==1)).sum());tab=hg_table(N-n,m,.0125)
    dsel=float((S[:,j]-S[:,0]).mean());pair=[n/N*dsel+(N-n)/N*(tab[plus,0]-tab[minus,1]),n/N*dsel+(N-n)/N*(tab[plus,1]-tab[minus,0])]
    if j==0:pair=[0.,0.]
    report={'label':'precommitted replay illustration, not prospective audit','winner':j,'n':n,'m':m,'selection_score':s,'audit_score':x/m,'finite_pool_truth':float(Y[:,j].mean()),'remainder_score':float(Y[perm[n:],j].mean()),'pool_accuracy_interval_joint95':pool.tolist(),'remainder_accuracy_interval_975':rem.tolist(),'pool_baseline_difference_interval_joint95':pair,'pool_difference':float((Y[:,j]-Y[:,0]).mean()),'audit_discordant_plus':plus,'audit_discordant_minus':minus,'selection_ids':perm[:n].tolist(),'audit_ids':perm[n:n+m].tolist(),'promote':bool(pair[0]>0)}
    (OUT/'report_card.json').write_text(json.dumps(report,indent=2));(OUT/'real_runtime.json').write_text(json.dumps({'wall_s':time.time()-start,'mean_offdiag_binary_correlation':float(corr[np.triu_indices(K,1)].mean())},indent=2))
if __name__=='__main__':
    (OUT/'replications').mkdir(exist_ok=True)
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['synthetic','real']);a=p.parse_args();globals()[a.mode]()
