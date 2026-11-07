"""Validate outputs and quantify only Monte Carlo uncertainty, not score uncertainty."""
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from analysis import ROOT,TOL
from summarize import common_challenger_ids

def main():
    frames=[pd.read_csv(p) for p in (ROOT/'results').glob('attacks_*.csv')]
    df=pd.concat(frames,ignore_index=True)
    assert not df.duplicated(['dataset','model','rule','ceiling','alpha','strict']).any()
    assert (df.k.dropna()>=0).all() and (df.k.dropna()<=df.loc[df.k.notna(),'n_tasks']).all()
    assert (df.k.dropna()%1==0).all()
    assert (df.k.isna()==df.status.isin(['infeasible','solver_failure'])).all()
    assert not df.status.isin(['bounded','solver_failure']).any()
    unit=df[df.ceiling=='unit'].pivot(index=['dataset','model','rule','strict'],columns='alpha',values='k').fillna(np.inf)
    values=unit.reindex(sorted(unit.columns),axis=1).to_numpy()
    assert (values[:,1:]<=values[:,:-1]).all()
    ceilings=df.pivot(index=['dataset','model','rule','alpha','strict'],columns='ceiling',values='k').fillna(np.inf)
    if 'observed' in ceilings:
        assert (ceilings['unit']<=ceilings['observed']).all()
    p=df.pivot(index=['dataset','model','rule','alpha','ceiling'],columns='strict',values='k').fillna(np.inf)
    if False in p and True in p:
        assert (p[True]>=p[False]).all()
    rng=np.random.default_rng(5726);checks=0
    for dataset in df.dataset.unique():
        mat=pd.read_csv(ROOT/f'data/processed/{dataset}.csv',index_col=0)
        sample=df[(df.dataset==dataset)&df.k.notna()].sample(min(100,int(((df.dataset==dataset)&df.k.notna()).sum())),random_state=5726)
        for _,row in sample.iterrows():
            X=mat.to_numpy().copy();t=mat.index.get_loc(row.model)
            ceiling=np.ones(X.shape[1]) if row.ceiling=='unit' else X.max(axis=0)
            tasks=json.loads(row.selected_tasks);idx=mat.columns.get_indexer(tasks)
            assert len(idx)==row.k
            X[t,idx]+=row.alpha*(ceiling[idx]-X[t,idx])
            if row.rule=='borda':s=(rankdata(X,axis=0,method='average')-1).sum(axis=1)
            elif row.rule=='mean':s=X.mean(axis=1)
            elif row.rule=='median':s=np.median(X,axis=1)
            elif row.rule=='minimum':s=X.min(axis=1)
            else:s=X.prod(axis=1)**(1/X.shape[1])
            assert s[t]>=np.max(np.delete(s,t))+(TOL if row.strict else -TOL)
            checks+=1
    uncertainty=[]
    for _,row in df[df.random_reps>0].iterrows():
        p=row.random_success_at_k;n=row.random_reps;z=1.959963984540054
        center=(p+z*z/(2*n))/(1+z*z/n)
        half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
        uncertainty.append(dict(dataset=row.dataset,model=row.model,rule=row.rule,alpha=row.alpha,ceiling=row.ceiling,reps=n,p_estimate=p,p_wilson95_low=max(0,center-half),p_wilson95_high=min(1,center+half)))
    pd.DataFrame(uncertainty).to_csv(ROOT/'results/random_baseline_uncertainty.csv',index=False)
    aggregate=[]
    requested=df[df.random_requested]
    assert requested.random_expected_censored_k.notna().all()
    infeasible=requested.status.eq('infeasible')
    assert (requested.loc[infeasible,'random_expected_censored_k']==requested.loc[infeasible,'n_tasks']+1).all()
    selected=common_challenger_ids(df)
    common=requested[requested.apply(lambda row:row.model in selected[row.dataset],axis=1)]
    baseline_cohorts=pd.concat([requested.assign(cohort='full_cohort'),common.assign(cohort='common_challengers')],ignore_index=True)
    for key,g in baseline_cohorts.groupby(['dataset','rule','alpha','ceiling','cohort']):
        sampled=g[g.random_reps>0];N=len(g);M=len(sampled)
        n_tasks=int(g.n_tasks.iloc[0]);reps=0
        width=0.;p_width=0.
        if M:
            assert sampled.random_reps.nunique()==1
            reps=int(sampled.random_reps.iloc[0])
            # Exact infeasible targets contribute constants; only M sampled targets add MC error.
            width=(n_tasks+1)*math.sqrt(M*math.log(40)/(2*reps*N*N))
            p_width=math.sqrt(math.log(40)/(2*reps*M))
        estimate=float(g.random_expected_censored_k.mean())
        aggregate.append(dict(zip(['dataset','rule','alpha','ceiling','cohort'],key),n_targets=N,n_reachable_targets=int(g.k.notna().sum()),n_expectation_targets=int(g.random_expected_censored_k.notna().sum()),n_infeasible_exact=int(g.status.eq('infeasible').sum()),n_sampled_targets=M,reps_per_sampled_target=reps,mean_random_censored_k=estimate,mc_hoeffding95_low=max(0,estimate-width),mc_hoeffding95_high=min(n_tasks+1,estimate+width),n_success_at_optimum_targets=int(g.random_success_at_k.notna().sum()),mean_random_p_at_optimum_reachable=float(g.random_success_at_k.mean()),mc_p_hoeffding95_halfwidth=p_width))
    pd.DataFrame(aggregate).to_csv(ROOT/'results/random_baseline_aggregate_uncertainty.csv',index=False)
    report=dict(records=len(df),independent_winner_recomputations=checks,duplicate_records=0,unresolved_optima=0,checks=['integer feasible task budgets','gain-fraction monotonicity','unit versus observed ceiling monotonicity','strict versus co-first monotonicity','independent aggregation including full Borda reranking'],mc_interpretation='Wilson intervals for per-target random-order success; conservative Hoeffding intervals for cohort means. Random-order variability only, conditional on exact published score matrix. Six-task baselines are exhaustive and have no MC error.')
    (ROOT/'results/diagnostics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
