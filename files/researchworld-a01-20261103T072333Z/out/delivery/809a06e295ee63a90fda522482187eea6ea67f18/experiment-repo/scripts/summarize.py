"""Descriptive cohort summaries and paired comparisons, no sampling inference."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def random_summary(g):
    """Stopping cost is full cohort when requested; optimum-budget success is reachable-only."""
    return dict(random_success_at_optimum_reachable=g.random_success_at_k.mean(),
                random_success_at_optimum_n=int(g.random_success_at_k.notna().sum()),
                random_expected_censored_k=g.random_expected_censored_k.mean(),
                random_expected_censored_k_n=int(g.random_expected_censored_k.notna().sum()))

def common_challenger_ids(df):
    """Remove the union of primary co-first incumbents once per score/rival design."""
    primary=df[(df.ceiling=='unit') & (df.alpha==1) & (~df.strict)]
    result={}
    for dataset,g in primary.groupby('dataset'):
        p=g.pivot(index='model',columns='rule',values='k')
        result[dataset]=set(p.index[~p.eq(0).any(axis=1)])
    return result


def main():
    files=[p for p in (ROOT/'results').glob('attacks_*.csv')]
    df=pd.concat([pd.read_csv(p) for p in files],ignore_index=True)
    df['reachable']=df.k.notna()
    summary=[]
    keys=['dataset','rule','ceiling','alpha','strict']
    for key,g in df.groupby(keys):
        rec=dict(zip(keys,key));rec.update(n=len(g),reachable=int(g.reachable.sum()),infeasible=int((g.status=='infeasible').sum()),unresolved=int(g.status.isin(['bounded','solver_failure']).sum()),baseline_winners=int((g.k==0).sum()),median_k_reachable=g.k.median(),q25_k_reachable=g.k.quantile(.25),q75_k_reachable=g.k.quantile(.75),mean_k_reachable=g.k.mean(),median_fraction_reachable=g.k_fraction.median(),**random_summary(g))
        summary.append(rec)
    pd.DataFrame(summary).to_csv(ROOT/'results/summary.csv',index=False)
    curve=[]
    for key,g in df.groupby(keys):
        for k in range(int(g.n_tasks.iloc[0])+1):
            curve.append(dict(zip(keys,key),budget=k,budget_fraction=k/g.n_tasks.iloc[0],n=len(g),reached=int((g.k<=k).sum()),fraction=float((g.k<=k).mean())))
    pd.DataFrame(curve).to_csv(ROOT/'results/budget_curves.csv',index=False)
    paired=[]
    for key,g in df.groupby(['dataset','ceiling','alpha','strict']):
        p=g.pivot(index='model',columns='rule',values='k')
        for a in p.columns:
            for b in p.columns:
                if a>=b:continue
                v=p[[a,b]].dropna()
                paired.append(dict(zip(['dataset','ceiling','alpha','strict'],key),rule_a=a,rule_b=b,both_reachable=len(v),a_lower=int((v[a]<v[b]).sum()),same=int((v[a]==v[b]).sum()),a_higher=int((v[a]>v[b]).sum()),median_a_minus_b=float((v[a]-v[b]).median()),only_a_reachable=int((p[a].notna()&p[b].isna()).sum()),only_b_reachable=int((p[a].isna()&p[b].notna()).sum())))
    pd.DataFrame(paired).to_csv(ROOT/'results/paired_rules.csv',index=False)
    # Same challenger cohort across rules, removing the union of incumbent winners only.
    challengers=[];challenger_pairs=[];challenger_curves=[]
    fixed_challengers=common_challenger_ids(df)
    for key,g in df.groupby(['dataset','ceiling','alpha','strict']):
        p=g.pivot(index='model',columns='rule',values='k')
        selected=p.index[p.index.isin(fixed_challengers[key[0]])]
        sub=g[g.model.isin(selected)]
        for rule,r in sub.groupby('rule'):
            challengers.append(dict(zip(['dataset','ceiling','alpha','strict'],key),rule=rule,n=len(r),reachable=int(r.k.notna().sum()),median_k_reachable=r.k.median(),mean_k_reachable=r.k.mean(),**random_summary(r)))
        for rule,r in sub.groupby('rule'):
            for budget in range(int(r.n_tasks.iloc[0])+1):
                challenger_curves.append(dict(zip(['dataset','ceiling','alpha','strict'],key),rule=rule,cohort='common_challengers',budget=budget,budget_fraction=budget/r.n_tasks.iloc[0],n=len(r),reached=int((r.k<=budget).sum()),fraction=float((r.k<=budget).mean())))
        p=p.loc[selected]
        for i,a in enumerate(p.columns):
            for b in p.columns[i+1:]:
                v=p[[a,b]].dropna()
                challenger_pairs.append(dict(zip(['dataset','ceiling','alpha','strict'],key),rule_a=a,rule_b=b,n_challengers=len(p),both_reachable=len(v),a_lower=int((v[a]<v[b]).sum()),same=int((v[a]==v[b]).sum()),a_higher=int((v[a]>v[b]).sum()),median_a_minus_b=float((v[a]-v[b]).median()),only_a_reachable=int((p[a].notna()&p[b].isna()).sum()),only_b_reachable=int((p[a].isna()&p[b].notna()).sum())))
    pd.DataFrame(challenger_curves).to_csv(ROOT/'results/challenger_budget_curves.csv',index=False)
    pd.DataFrame(challengers).to_csv(ROOT/'results/challenger_summary.csv',index=False)
    pd.DataFrame(challenger_pairs).to_csv(ROOT/'results/challenger_paired_rules.csv',index=False)
    # Rule-specific initial ranks: report rank percentiles to separate existing competitiveness.
    df['rank_band']=pd.cut((df.baseline_rank-1)/(df.n_models-1),[-.001,.1,.5,1],labels=['top10pct','middle40pct','bottom50pct'])
    bands=df.groupby(keys+['rank_band'],observed=True).agg(n=('model','size'),reachable=('reachable','sum'),median_k_reachable=('k','median'),mean_k_reachable=('k','mean')).reset_index()
    bands.to_csv(ROOT/'results/rank_strata.csv',index=False)
    print(f'Summarized {len(df)} measured rows from {len(files)} files')
if __name__=='__main__':main()
