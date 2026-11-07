"""Compact descriptive diagnostics from existing measured outputs; no model refitting."""
import gzip,hashlib,json,pathlib
import numpy as np
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[1]
R=ROOT/'results'
cohort=json.loads((R/'cohorts.json').read_text())['mteb']
models=pd.read_csv(R/'model_averages.csv');models=models[(models.dataset=='mteb')&(models.condition=='random')&(models.k==4)]
tails=[]
for method in ['a_opt_covariance','random_covariance']:
 g=models[models.method==method];assert not g.model.duplicated().any()
 row=dict(method=method,k=4,n_unique_models=len(g),mean_mae=float(g.mae.mean()))
 for label,q in [('q50',.5),('q75',.75),('q90',.9),('q95',.95),('maximum',1.)]:row[label+'_mae']=float(g.mae.quantile(q,interpolation='linear'))
 for point in [5,10]:row[f'n_mae_above_{point}_points']=int((g.mae>point/100).sum())
 worst=g.loc[g.mae.idxmax()];row['worst_model']=worst.model;tails.append(row)
pd.DataFrame(tails).to_csv(R/'diagnostic_model_tails.csv',index=False)
task=pd.read_csv(R/'mteb_task_errors.csv');task=task[(task.k==4)&(task.method=='covariance')&(~task.queried)].copy()
task['total_abs_error']=task.mae*task.n_models
bytask=task.groupby('task').agg(total_abs_error=('total_abs_error','sum'),target_model_appearances=('n_models','sum'),eligible_splits=('seed','nunique')).reset_index()
bytask['appearance_weighted_mae']=bytask.total_abs_error/bytask.target_model_appearances
bytask=bytask.sort_values(['appearance_weighted_mae','task'],ascending=[False,True])
bytask.to_csv(R/'diagnostic_unqueried_tasks.csv',index=False)
corr=pd.read_csv(R/'mteb_descriptive_correlation.csv',index_col=0);overlap=pd.read_csv(R/'mteb_pair_counts.csv',index_col=0)
pairs=[]
for i in range(len(corr)):
 for j in range(i+1,len(corr)):
  pairs.append(dict(task_a=corr.index[i],task_b=corr.index[j],pearson=float(corr.iloc[i,j]),overlap_models=int(overlap.iloc[i,j])))
pairs=pd.DataFrame(pairs);pairs.to_csv(R/'diagnostic_task_pairs.csv',index=False)
valid=pairs[pairs.pearson.notna()]
dep=dict(full_cohort_models=cohort['models'],benchmark_columns=len(corr),possible_distinct_pairs=len(pairs),finite_pairs=len(valid),minimum_required_overlap=20)
for name,values in [('pearson',valid.pearson),('overlap',valid.overlap_models)]:
 for label,q in [('minimum',0),('q10',.1),('median',.5),('q90',.9),('maximum',1.)]:dep[name+'_'+label]=float(values.quantile(q,interpolation='linear'))
(R/'diagnostic_dependence.json').write_text(json.dumps(dep,indent=2)+'\n')
s=pd.read_csv(R/'summary.csv');scale=s[(s.dataset=='mteb')&(s.condition=='random')&(s.k==4)].copy()
scale.to_csv(R/'diagnostic_normalized_and_seed.csv',index=False)
budgets=pd.DataFrame({'k':[1,2,4,8,16]});budgets['total_tasks']=32;budgets['k_over_N']=budgets.k/32;budgets['natural_targets']=32-budgets.k;budgets['fixed_targets']=6;budgets['fixed_query_candidates']=26
budgets.to_csv(R/'diagnostic_budget_denominators.csv',index=False)
inputs=['model_averages.csv','mteb_task_errors.csv','mteb_descriptive_correlation.csv','mteb_pair_counts.csv','summary.csv','cohorts.json']
definitions={
 'model_tails':'Primary MTEB k=4; each unique held-out model is one unit. Input model_averages already averages random query draws within model/split then held-out appearances. Quantiles use pandas linear interpolation; thresholds are strict >. These are descriptive empirical quantiles, not predictive coverage intervals.',
 'task_errors':'Primary MTEB covariance/A-opt k=4, unqueried tasks only. Sum each eligible split mean absolute error times its test-model count, divide by total target-model appearances. Eligible split count and appearances are reported; appearances may repeat the same models and are not independent units. Tasks always queried have no unqueried error estimate and are omitted. Task ranking is conditional on selection and split availability, not a causal comparison of inherent benchmark difficulty.',
 'correlations':'Full primary 233-row, 32-task cohort; Pearson over pairwise observed rows, minimum 20 observations, each distinct unordered off-diagonal task pair counted once. Related task pairs are not independent. This is descriptive only and was not reused for predictive fits.',
 'normalized_error':'Use summary.csv standardized_rmse: errors divide by each split training-only observed task sample standard deviation (ddof=1, floor 1e-4), mean squared over unqueried tasks within model, average query draws and repeated appearances, equal average over unique models, then square root. Intervals transform existing model-bootstrap MSE bounds. Seed MAE ranges are min/max of per-split test-model mean MAE, not confidence intervals and not the headline unique-model-weighted estimand.',
 'denominators':'Natural primary budget k has 32-k targets. Fixed-target diagnostic holds round(0.2*32)=6 tasks out, leaving 26 eligible candidates. k/N always uses original 32. No fitting or bootstrap is rerun.',
 'inputs':[{ 'path':'results/'+name,'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest()} for name in inputs]}
(R/'diagnostic_definitions.json').write_text(json.dumps(definitions,indent=2)+'\n')
lines=['# Compact numerical diagnostics','','Generated by `scripts/diagnostic_summary.py` from existing measured outputs; no new fit or uncertainty run. All raw MAE quantities below are multiplied by 100 for score points. Definitions and input hashes are in `results/diagnostic_definitions.json`.','','## Unique-model error tails at primary MTEB k=4','','| Policy + covariance predictor | Unique models | Median | 90th percentile | 95th percentile | Maximum | MAE >5 points | MAE >10 points |','|---|---:|---:|---:|---:|---:|---:|---:|']
for t in tails:
 lines.append(f"| {t['method']} | {t['n_unique_models']} | {100*t['q50_mae']:.3f} | {100*t['q90_mae']:.3f} | {100*t['q95_mae']:.3f} | {100*t['maximum_mae']:.3f} | {t['n_mae_above_5_points']} | {t['n_mae_above_10_points']} |")
lines+=['','Query draws are averaged within model/split, then held-out appearances within model. Each model is counted once. These quantiles describe this evaluated cohort and do not guarantee individual-model error. The maximum-error model is '+', '.join(t['method']+': `'+t['worst_model']+'`' for t in tails)+'.','','## Largest observed unqueried task errors under A-optimal k=4','','| Task | Appearance-weighted MAE | Eligible splits | Target-model appearances |','|---|---:|---:|---:|']
for t in bytask.head(5).itertuples():lines.append(f'| {t.task} | {100*t.appearance_weighted_mae:.3f} | {t.eligible_splits} | {t.target_model_appearances} |')
lines+=['','These task means weight each eligible split by its test-model count. Split/model appearances repeat observations and do not define an independent sample size. Always-queried tasks have no unqueried diagnostic; rankings depend on the selector. The complete task summary is supplied as CSV.','','## Descriptive dependence and overlap','',f"Across the full 233-row primary cohort there are {dep['finite_pairs']} finite Pearson values among {dep['possible_distinct_pairs']} distinct task pairs (minimum allowed overlap 20). Correlations range from {dep['pearson_minimum']:.4f} to {dep['pearson_maximum']:.4f}, median {dep['pearson_median']:.4f} (10th/90th percentiles {dep['pearson_q10']:.4f}/{dep['pearson_q90']:.4f}). Pairwise overlap ranges from {dep['overlap_minimum']:.0f} to {dep['overlap_maximum']:.0f} models, median {dep['overlap_median']:.1f}. These pairwise-observed, full-cohort descriptions are not training fits and are not independent task observations.",'','## Training-scale-normalized error and partition sensitivity at k=4','','| Method | Standardized RMSE [descriptive interval] | Seed mean-MAE range (points) |','|---|---:|---:|']
for t in scale.itertuples():lines.append(f'| {t.method} | {t.standardized_rmse:.3f} [{t.standardized_rmse_lo:.3f}, {t.standardized_rmse_hi:.3f}] | {100*t.seed_mae_min:.3f}–{100*t.seed_mae_max:.3f} |')
lines+=['','A-optimal versus random normalized RMSE is 0.520 versus 0.545; the relative advantage is much smaller than the corresponding raw RMSE contrast (6.011 versus 9.600 score points). Error-scale choice therefore matters. Marginal bootstrap bounds are not a paired significance test.','','Normalized RMSE is dimensionless and uses each training split’s observed-task sample standard deviations. Bootstrap bounds and model/draw averaging follow the primary protocol. Seed ranges describe ten per-split means, share models and training data, and are not inferential intervals.','','## Denominators and computational cost','','At k=4 the natural target set has 28 tasks, with k/N=4/32=0.125. The fixed-target check has six targets and 26 eligible query candidates. The budget-denominator CSV gives all tested k, including k=16 (half the original task set).','','The requested algebraic costs are correct for this dense implementation: moments/PSD O(MN²+N³), greedy k-step selection O(kN²), coefficient setup O(k³+Nk²), one new model O(Nk) after setup, and dense working memory O(MN+N²). See THEORY.md for assumptions, validation overhead and distinction from actual benchmark execution costs.','']
(ROOT/'notes/DIAGNOSTIC_SUMMARY.md').write_text('\n'.join(lines))
print('\n'.join(lines))
