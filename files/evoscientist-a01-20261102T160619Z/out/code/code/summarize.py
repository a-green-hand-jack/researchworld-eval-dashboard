#!/usr/bin/env python3
"""Derive every reported table/interval from saved target-level results."""
from pathlib import Path
import json,itertools
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
SEEDS=[17,29,43]
RULES=['mean','median','borda']
LABEL={'helm':'HELM','open_raw':'Open LLM','open_norm':'Open normalized','open_dedup':'Open deduplicated','open_available':'Open available'}

def bootstrap(v):
    v=np.asarray(v,float);means=[];intervals=[]
    if len(v)==0:return [None,None],[]
    for seed in SEEDS:
        rng=np.random.default_rng(seed)
        # Bounded batches avoid unnecessarily large temporary arrays.
        b=np.concatenate([v[rng.integers(len(v),size=(100,len(v)))].mean(axis=1) for _ in range(20)])
        means.extend(b.tolist());intervals.append(np.quantile(b,[.025,.975]).tolist())
    return np.quantile(means,[.025,.975]).tolist(),intervals

def frame(name):return pd.read_csv(ROOT/f'artifacts/results_{name}.csv')

def main():
    summary=[];paired=[];fixed=[];strata=[];heur=[];unique=[];baselines=[];cohortids={};magnitude={};sensitivity=[]
    data={name:frame(name) for name in ['helm','open_raw','open_norm','open_dedup','open_available','open_median_convention']}
    for name in ['helm','open_raw','open_norm','open_dedup','open_available']:
      d=data[name];m=int(d.m.iloc[0]);n=int(d.n.iloc[0])
      for (rho,strict,rule),g in d.groupby(['rho','strict','rule']):
        finite=g.K.notna();non=g['rank']>1
        summary.append(dict(dataset=name,rho=rho,strict=strict,rule=rule,models=m,tasks=n,feasible=int(finite.sum()),feasible_rate=float(finite.mean()),nonwinners=int(non.sum()),nonwinner_feasible=int((finite&non).sum()),median_K=float(g.K.median()),mean_K=float(g.K.mean()),mean_K_fraction=float(g.K.mean()/n),median_rank=float(g['rank'].median())))
      if name not in ['helm','open_raw']:continue
      shared=d[~d.strict]
      for rule in RULES:
        g=shared[(shared.rho==.5)&(shared.rule==rule)];b=g[g['rank']==1]
        baselines.append(dict(dataset=name,rule=rule,winners=b.model.tolist(),ties=len(b),score=float(b.base_score.iloc[0])))
      for rule in RULES:
        q=d[d.rule==rule].pivot(index=['i','rho'],columns='strict',values='K')
        unique.append(dict(dataset=name,rule=rule,feasibility_changed=int((q[False].notna()!=q[True].notna()).sum()),finite_support_changed=int(((q[False]!=q[True])&q[False].notna()&q[True].notna()).sum()),total=len(q)))
      for rho in [.25,.5,1.]:
        s=shared[shared.rho==rho];p=s.pivot(index='i',columns='rule',values='K');r=s.pivot(index='i',columns='rule',values='rank')
        for cohort in ['triple','pair_mean_median']:
          rules=RULES if cohort=='triple' else ['mean','median']
          ids=p[rules].dropna().index.intersection(r[(r[rules]>1).all(axis=1)].index)
          cohortids[f'{name}_{rho}_{cohort}']=ids.tolist()
          for less,more in [('mean','median'),('mean','borda'),('median','borda')] if cohort=='triple' else [('mean','median')]:
            delta=(p.loc[ids,more]-p.loc[ids,less])/n;ci,separate=bootstrap(delta)
            paired.append(dict(dataset=name,rho=rho,cohort=cohort,pair=f'{more}-minus-{less}',targets=len(ids),mean_delta=float(delta.mean()),median_delta=float(delta.median()),low=ci[0],high=ci[1],lower=int((delta<0).sum()),equal=int((delta==0).sum()),higher=int((delta>0).sum()),seed_intervals=json.dumps(separate)))
      for cohort in ['triple','pair_mean_median']:
        ids=cohortids[f'{name}_0.5_{cohort}']
        for rho in [.5,1.]:
          p=shared[shared.rho==rho].pivot(index='i',columns='rule',values='K').loc[ids]
          delta=(p['median']-p['mean'])/n;ci,separate=bootstrap(delta)
          fixed.append(dict(dataset=name,cohort=cohort,rho=rho,targets=len(ids),mean_mean_K=float(p['mean'].mean()),mean_median_K=float(p['median'].mean()),mean_borda_K=float(p['borda'].mean()) if cohort=='triple' else float('nan'),delta_K=float((p['median']-p['mean']).mean()),delta_fraction=float(delta.mean()),low=ci[0],high=ci[1],median_cheaper=int((delta<0).sum()),equal=int((delta==0).sum()),median_costlier=int((delta>0).sum()),seed_intervals=json.dumps(separate)))
      # Same fixed targets; does increasing cap reverse each target's rule ordering?
      ids=cohortids[f'{name}_0.5_triple'];p5=shared[shared.rho==.5].pivot(index='i',columns='rule',values='K').loc[ids];p1=shared[shared.rho==1].pivot(index='i',columns='rule',values='K').loc[ids]
      magnitude[name+'_cap_reversal']={'fixed_targets':len(ids),'strict_sign_reversals':int((((p5['median']-p5['mean'])<0)&((p1['median']-p1['mean'])>0)).sum()),'rho1_median_costlier':int((p1['median']>p1['mean']).sum())}
      ref=shared[(shared.rho==.5)&(shared.rule=='mean')].set_index('i')['rank'];percent=(ref-1)/(m-1)
      for (rho,rule),g in shared.groupby(['rho','rule']):
        for q in range(4):
          ids=percent[(percent>=q/4)&(percent<((q+1)/4) if q<3 else percent<=1)].index;sub=g[g.i.isin(ids)]
          strata.append(dict(dataset=name,rho=rho,rule=rule,quartile=q+1,targets=len(sub),feasible=int(sub.K.notna().sum()),mean_K_fraction=float(sub.K_fraction.mean())))
      for rho,g in shared[shared.rule=='borda'].groupby('rho'):
        g=g[g.K.notna()];excess=np.array([g[f'random_K_{seed}']-g.K for seed in SEEDS])
        heur.append(dict(dataset=name,rho=rho,targets=len(g),headroom_mean_excess=float((g.headroom_K-g.K).mean()),headroom_max_excess=float((g.headroom_K-g.K).max()),random_mean_excess=float(excess.mean()),random_seed_means=excess.mean(axis=1).tolist()))
    # Compare variants on retained identical IDs; competitor roster is separately changed.
    original=data['open_raw'];original=original[(~original.strict)&(original.rho==.5)]
    for variant in ['open_norm','open_dedup','open_available','open_median_convention']:
      for rule,g in data[variant].groupby('rule'):
        ref_rule='median' if 'median' in rule else rule
        base=original[original.rule==ref_rule].set_index('model');v=g.set_index('model');both=base.index.intersection(v.index);x=base.loc[both,'K'];y=v.loc[both,'K'];finite=x.notna()&y.notna()
        sensitivity.append(dict(variant=variant,rule=rule,targets=len(both),original_feasible=int(x.notna().sum()),variant_feasible=int(y.notna().sum()),both_feasible=int(finite.sum()),feasibility_changed=int((x.notna()!=y.notna()).sum()),support_changed=int(((x!=y)&finite).sum()),mean_K_change_finite_both=float((y[finite]-x[finite]).mean())))
    h=data['helm'];h=h[(~h.strict)&(h.rho==1)];k=h.pivot(index='i',columns='rule',values='K');l=h.pivot(index='i',columns='rule',values='L1_min');rank=h.pivot(index='i',columns='rule',values='rank');ids=rank[(rank[['mean','median']]>1).all(axis=1)].index
    magnitude['helm_rho1']={'targets':len(ids),'all_targets':len(k),'mean_L1':float(l.loc[ids,'mean'].mean()),'median_L1':float(l.loc[ids,'median'].mean()),'support_more_but_magnitude_less':int(((k.loc[ids,'median']>k.loc[ids,'mean'])&(l.loc[ids,'median']<l.loc[ids,'mean'])).sum()),'median_L1_less':int((l.loc[ids,'median']<l.loc[ids,'mean']).sum()),'median_support_more':int((k.loc[ids,'median']>k.loc[ids,'mean']).sum())}
    for filename,rows in [('primary_summary',summary),('paired_contrasts',paired),('fixed_cohort',fixed),('rank_strata',strata),('heuristics',heur),('unique_first',unique),('sensitivity_summary',sensitivity)]:pd.DataFrame(rows).to_csv(ROOT/f'artifacts/{filename}.csv',index=False,float_format='%.17g')
    (ROOT/'artifacts/cohort_ids.json').write_text(json.dumps(cohortids,indent=2));(ROOT/'artifacts/magnitude_summary.json').write_text(json.dumps(magnitude,indent=2));(ROOT/'artifacts/baseline_winners.json').write_text(json.dumps(baselines,indent=2))
    # LaTeX tables: no manual transcription of empirical numbers.
    out=ROOT/'paper/generated';out.mkdir(exist_ok=True)
    s=pd.DataFrame(summary)
    lines=['\\begin{tabular}{llrrr}','\\toprule','Panel & $\\rho$ & Mean & Median & Borda \\\\','\\midrule']
    for name in ['helm','open_raw']:
      for rho in [.25,.5,1.]:
        g=s[(s.dataset==name)&(s.rho==rho)&(~s.strict)].set_index('rule');m=int(g.models.iloc[0]);cells=[f"{int(g.at[r,'feasible'])}/{m}" for r in RULES]
        lines.append(f"{LABEL[name]} & {rho:g} & "+' & '.join(cells)+' \\\\')
    lines+=['\\bottomrule','\\end{tabular}'];(out/'feasibility.tex').write_text('\n'.join(lines))
    f=pd.DataFrame(fixed);lines=['\\begin{tabular}{llrrr}','\\toprule','Panel ($N$) & $\\rho$ & $K_{\\rm mean}$ & $K_{\\rm med}$ & Difference [95\\% interval] \\\\','\\midrule']
    for name in ['helm','open_raw']:
      for rho in [.5,1.]:
        q=f[(f.dataset==name)&(f.cohort=='triple')&(f.rho==rho)].iloc[0]
        lines.append(f"{LABEL[name]} ({int(q.targets)}) & {rho:g} & {q.mean_mean_K:.2f} & {q.mean_median_K:.2f} & {q.delta_fraction:.3f} [{q.low:.3f}, {q.high:.3f}] \\\\ ")
    lines+=['\\bottomrule','\\end{tabular}'];(out/'fixed_cohort.tex').write_text('\n'.join(lines))
    lines=['\\begin{tabular}{llrrrr}','\\toprule','Variant & Rule & $N$ & Feas. before & Feas. after & Changed $K$\\\\','\\midrule']
    names={'open_norm':'Normalized','open_dedup':'Deduplicated','open_available':'Available','open_median_convention':'Median convention'}
    for q in sensitivity:
        lines.append(f"{names[q['variant']]} & {q['rule'].replace('_',' ')} & {q['targets']} & {q['original_feasible']} & {q['variant_feasible']} & {q['support_changed']} \\\\ ")
    lines+=['\\bottomrule','\\end{tabular}'];(out/'sensitivity.tex').write_text('\n'.join(lines))
    print(pd.DataFrame(fixed).drop(columns='seed_intervals').to_string(index=False));print(json.dumps(magnitude,indent=2))
if __name__=='__main__':main()
