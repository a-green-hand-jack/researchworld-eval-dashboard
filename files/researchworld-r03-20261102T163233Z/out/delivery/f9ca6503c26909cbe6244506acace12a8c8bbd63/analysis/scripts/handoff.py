"""Write an analysis handoff directly from measured summary files."""
import pathlib,json
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=pd.read_csv(ROOT/'results/summary.csv');e=pd.read_csv(ROOT/'results/paired_effects.csv');c=json.load(open(ROOT/'results/cohorts.json'))
lines=['# Numerical handoff','', 'This is analysis evidence for the report and presentation owners, not a manuscript section. Authoritative numeric files are results/summary.csv and results/paired_effects.csv; methods and caveats are in notes/PROTOCOL.md. Errors below are multiplied by 100 (score percentage points, including correlation scales); intervals are descriptive unique-model bootstrap intervals, not independent-lineage population confidence claims.','', '## Cohorts','']
for label in ['mteb','mteb_wide','mteb_mixed']:
 a=c[label];lines.append(f"- {label}: {a['models']} historical rows × {a['tasks']} tasks; {a['complete_models']} complete rows; density {a['density']:.3f}; exact per-task modal dataset revision = {a['exact_modal_dataset_revision']}.")
a=json.load(open(ROOT/'results/open_llm_audit.json'));lines += [f"- Open LLM: {a['final_models']} rows × {a['tasks']} raw-score benchmarks after flagged/name/precision/commit-SHA filtering.",'','## Primary prediction and selection comparisons','','| Dataset | k | Predictor and policy | MAE [interval] | RMSE | Models |','|---|---:|---|---:|---:|---:|']
for ds,ks in [('mteb',[0,1,2,4,8,16]),('open_llm',[0,1,2,4])]:
 for k in ks:
  for method in (['a_opt_mean'] if k==0 else ['a_opt_covariance','d_opt_covariance','random_covariance','a_opt_ridge','a_opt_factor4']):
   r=s[(s.dataset==ds)&(s.condition=='random')&(s.k==k)&(s.method==method)].iloc[0]
   lines.append(f"| {ds} | {k} | {method} | {100*r.mae:.3f} [{100*r.mae_lo:.3f}, {100*r.mae_hi:.3f}] | {100*r.rmse:.3f} | {int(r.unique_test_models)} |")
lines+=['','## Robustness and fixed targets','','| Dataset | Condition | k | A-opt MAE | Random MAE | Paired improvement [interval] |','|---|---|---:|---:|---:|---:|']
for ds,cond,k in [('mteb',q,k) for q in ['random','provider','missing30','missing60','dense_history','fixed_targets'] for k in [4,8]]+[('mteb_wide','random',8),('mteb_mixed','random',8),('open_llm','provider',2),('open_llm','temporal',2),('open_llm','fixed_targets',1),('open_llm','fixed_targets',2),('open_llm','fixed_targets',4)]:
 a=s[(s.dataset==ds)&(s.condition==cond)&(s.method=='a_opt_covariance')&(s.k==k)].iloc[0]
 r=s[(s.dataset==ds)&(s.condition==cond)&(s.method=='random_covariance')&(s.k==k)].iloc[0]
 d=e[(e.dataset==ds)&(e.condition==cond)&(e.k==k)&(e.comparator=='random_covariance')].iloc[0]
 lines.append(f"| {ds} | {cond} | {k} | {100*a.mae:.3f} | {100*r.mae:.3f} | {100*d.positive_means_a_opt_better:.3f} [{100*d.ci_lo:.3f}, {100*d.ci_hi:.3f}] |")
lines+=['','## How much k is enough?','','The following are operational tolerances, not universal recommendations. Smallest **tested** k with mean MAE at or below each tolerance; untested intermediate k are unresolved. Requiring the descriptive upper interval bound is a separate, more conservative criterion.','', '| Dataset | MAE tolerance (points) | First tested k, mean | First tested k, upper interval |','|---|---:|---:|---:|']
for ds in ['mteb','open_llm']:
 a=s[(s.dataset==ds)&(s.condition=='random')&(s.method=='a_opt_covariance')].sort_values('k')
 for tol in [.03,.05,.1]:
  b=a[a.mae<=tol];d=a[a.mae_hi<=tol]
  lines.append(f"| {ds} | {100*tol:.0f} | {int(b.iloc[0].k) if len(b) else 'not reached'} | {int(d.iloc[0].k) if len(d) else 'not reached'} |")
lines+=['','## Claims and limits for the owners','','- Evaluate the proposed transparent regularized covariance design against all listed controls. Selection and prediction are different comparisons. Do not claim universally optimal selection, a new covariance identity, or consistent superiority over D-optimal or direct ridge/factor predictors.','- The complete-history control can outperform natural sparse-history covariance. Additional incomplete rows do not automatically help this estimator; missingness and population composition are intertwined.','- Fixed-target comparisons control changing target composition. The full unqueried-target metric is the deployment estimand, while fixed targets are a diagnostic on a restricted candidate set. On Open LLM, A-optimal is worse than random at k=1; at k=4 all four eligible query tasks are observed and both policies coincide exactly. Do not summarize this diagnostic as a uniform selection gain.','- MTEB evidence is for English-labelled/involving embedding evaluations under selected task definitions. Dataset revision consistency does not ensure identical evaluator-code versions or training-data independence. Complete-row filtering, related task suites, and unverified model lineages limit generalization.','- Open LLM has six benchmarks only. Submission chronology is one dated partition, not ten independent temporal experiments or verified release chronology. Provider namespaces do not certify family holdout.','- All conclusions are exploratory and conditional on the measured cohorts. Bootstrap intervals resample model names after repeated split/query averaging and do not remove lineage dependence. No inference about benchmark runtime savings beyond a query count is supported.','- Superseded pilots, the negative-prediction clipping correction and commit-SHA alias audit are recorded in RUN_LOG.md; only final corrected outputs feed these tables.','']
(ROOT/'notes/RESULTS.md').write_text('\n'.join(lines))
print('Analysis handoff written from measured summaries.')
