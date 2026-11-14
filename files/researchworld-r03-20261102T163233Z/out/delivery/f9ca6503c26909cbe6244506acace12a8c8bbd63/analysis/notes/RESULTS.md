# Numerical handoff

This is analysis evidence for the report and presentation owners, not a manuscript section. Authoritative numeric files are results/summary.csv and results/paired_effects.csv; methods and caveats are in notes/PROTOCOL.md. Errors below are multiplied by 100 (score percentage points, including correlation scales); intervals are descriptive unique-model bootstrap intervals, not independent-lineage population confidence claims.

## Cohorts

- mteb: 233 historical rows × 32 tasks; 95 complete rows; density 0.706; exact per-task modal dataset revision = True.
- mteb_wide: 216 historical rows × 93 tasks; 53 complete rows; density 0.722; exact per-task modal dataset revision = True.
- mteb_mixed: 237 historical rows × 60 tasks; 85 complete rows; density 0.730; exact per-task modal dataset revision = False.
- Open LLM: 4465 rows × 6 raw-score benchmarks after flagged/name/precision/commit-SHA filtering.

## Primary prediction and selection comparisons

| Dataset | k | Predictor and policy | MAE [interval] | RMSE | Models |
|---|---:|---|---:|---:|---:|
| mteb | 0 | a_opt_mean | 11.642 [10.413, 12.913] | 16.383 | 84 |
| mteb | 1 | a_opt_covariance | 8.219 [7.533, 8.938] | 11.087 | 84 |
| mteb | 1 | d_opt_covariance | 9.034 [8.030, 10.045] | 12.562 | 84 |
| mteb | 1 | random_covariance | 8.365 [7.913, 8.831] | 12.735 | 84 |
| mteb | 1 | a_opt_ridge | 8.155 [7.501, 8.838] | 10.911 | 84 |
| mteb | 1 | a_opt_factor4 | 8.176 [7.505, 8.877] | 11.025 | 84 |
| mteb | 2 | a_opt_covariance | 4.941 [4.582, 5.320] | 7.202 | 84 |
| mteb | 2 | d_opt_covariance | 4.593 [4.226, 4.982] | 6.518 | 84 |
| mteb | 2 | random_covariance | 7.007 [6.678, 7.367] | 11.178 | 84 |
| mteb | 2 | a_opt_ridge | 4.977 [4.615, 5.376] | 7.310 | 84 |
| mteb | 2 | a_opt_factor4 | 4.931 [4.565, 5.326] | 7.183 | 84 |
| mteb | 4 | a_opt_covariance | 4.104 [3.802, 4.433] | 6.011 | 84 |
| mteb | 4 | d_opt_covariance | 4.114 [3.773, 4.487] | 5.764 | 84 |
| mteb | 4 | random_covariance | 5.715 [5.401, 6.042] | 9.600 | 84 |
| mteb | 4 | a_opt_ridge | 4.026 [3.716, 4.358] | 5.982 | 84 |
| mteb | 4 | a_opt_factor4 | 4.142 [3.838, 4.453] | 6.066 | 84 |
| mteb | 8 | a_opt_covariance | 3.394 [3.117, 3.715] | 5.038 | 84 |
| mteb | 8 | d_opt_covariance | 3.566 [3.285, 3.877] | 4.923 | 84 |
| mteb | 8 | random_covariance | 4.573 [4.334, 4.815] | 7.697 | 84 |
| mteb | 8 | a_opt_ridge | 3.265 [2.987, 3.619] | 4.896 | 84 |
| mteb | 8 | a_opt_factor4 | 3.421 [3.144, 3.742] | 5.084 | 84 |
| mteb | 16 | a_opt_covariance | 2.462 [2.238, 2.694] | 3.428 | 84 |
| mteb | 16 | d_opt_covariance | 2.744 [2.465, 3.062] | 3.834 | 84 |
| mteb | 16 | random_covariance | 3.896 [3.661, 4.139] | 6.212 | 84 |
| mteb | 16 | a_opt_ridge | 2.003 [1.842, 2.173] | 2.800 | 84 |
| mteb | 16 | a_opt_factor4 | 2.179 [2.002, 2.383] | 3.075 | 84 |
| open_llm | 0 | a_opt_mean | 9.232 [9.086, 9.377] | 12.671 | 3984 |
| open_llm | 1 | a_opt_covariance | 6.035 [5.924, 6.146] | 8.324 | 3984 |
| open_llm | 1 | d_opt_covariance | 6.035 [5.925, 6.148] | 8.324 | 3984 |
| open_llm | 1 | random_covariance | 6.645 [6.564, 6.725] | 9.749 | 3984 |
| open_llm | 1 | a_opt_ridge | 6.015 [5.906, 6.127] | 8.317 | 3984 |
| open_llm | 1 | a_opt_factor4 | 6.013 [5.902, 6.127] | 8.319 | 3984 |
| open_llm | 2 | a_opt_covariance | 3.422 [3.367, 3.479] | 5.328 | 3984 |
| open_llm | 2 | d_opt_covariance | 4.399 [4.317, 4.478] | 5.852 | 3984 |
| open_llm | 2 | random_covariance | 5.238 [5.165, 5.309] | 8.238 | 3984 |
| open_llm | 2 | a_opt_ridge | 3.410 [3.353, 3.467] | 5.309 | 3984 |
| open_llm | 2 | a_opt_factor4 | 3.423 [3.367, 3.481] | 5.318 | 3984 |
| open_llm | 4 | a_opt_covariance | 1.982 [1.944, 2.021] | 2.632 | 3984 |
| open_llm | 4 | d_opt_covariance | 1.982 [1.944, 2.022] | 2.632 | 3984 |
| open_llm | 4 | random_covariance | 4.680 [4.605, 4.760] | 7.731 | 3984 |
| open_llm | 4 | a_opt_ridge | 1.976 [1.937, 2.014] | 2.627 | 3984 |
| open_llm | 4 | a_opt_factor4 | 2.014 [1.976, 2.054] | 2.665 | 3984 |

## Robustness and fixed targets

| Dataset | Condition | k | A-opt MAE | Random MAE | Paired improvement [interval] |
|---|---|---:|---:|---:|---:|
| mteb | random | 4 | 4.104 | 5.715 | 1.611 [1.367, 1.855] |
| mteb | random | 8 | 3.394 | 4.573 | 1.179 [1.004, 1.341] |
| mteb | provider | 4 | 4.307 | 6.134 | 1.827 [1.602, 2.053] |
| mteb | provider | 8 | 3.523 | 4.857 | 1.334 [1.182, 1.485] |
| mteb | missing30 | 4 | 4.673 | 6.401 | 1.728 [1.491, 1.971] |
| mteb | missing30 | 8 | 4.155 | 5.466 | 1.311 [1.167, 1.454] |
| mteb | missing60 | 4 | 5.597 | 7.492 | 1.895 [1.613, 2.167] |
| mteb | missing60 | 8 | 4.825 | 6.613 | 1.788 [1.625, 1.945] |
| mteb | dense_history | 4 | 3.801 | 5.511 | 1.710 [1.493, 1.958] |
| mteb | dense_history | 8 | 3.012 | 4.235 | 1.223 [1.088, 1.363] |
| mteb | fixed_targets | 4 | 4.494 | 5.476 | 0.981 [0.665, 1.326] |
| mteb | fixed_targets | 8 | 4.208 | 4.651 | 0.443 [0.166, 0.780] |
| mteb_wide | random | 8 | 3.948 | 4.923 | 0.975 [0.755, 1.195] |
| mteb_mixed | random | 8 | 3.615 | 5.093 | 1.478 [1.321, 1.628] |
| open_llm | provider | 2 | 3.429 | 5.265 | 1.836 [1.782, 1.893] |
| open_llm | temporal | 2 | 4.029 | 5.901 | 1.872 [1.747, 1.999] |
| open_llm | fixed_targets | 1 | 6.689 | 6.129 | -0.560 [-0.651, -0.472] |
| open_llm | fixed_targets | 2 | 4.541 | 4.939 | 0.398 [0.363, 0.433] |
| open_llm | fixed_targets | 4 | 4.160 | 4.160 | 0.000 [0.000, 0.000] |

## How much k is enough?

The following are operational tolerances, not universal recommendations. Smallest **tested** k with mean MAE at or below each tolerance; untested intermediate k are unresolved. Requiring the descriptive upper interval bound is a separate, more conservative criterion.

| Dataset | MAE tolerance (points) | First tested k, mean | First tested k, upper interval |
|---|---:|---:|---:|
| mteb | 3 | 16 | 16 |
| mteb | 5 | 2 | 4 |
| mteb | 10 | 1 | 1 |
| open_llm | 3 | 4 | 4 |
| open_llm | 5 | 2 | 2 |
| open_llm | 10 | 1 | 1 |

## Claims and limits for the owners

- Evaluate the proposed transparent regularized covariance design against all listed controls. Selection and prediction are different comparisons. Do not claim universally optimal selection, a new covariance identity, or consistent superiority over D-optimal or direct ridge/factor predictors.
- The complete-history control can outperform natural sparse-history covariance. Additional incomplete rows do not automatically help this estimator; missingness and population composition are intertwined.
- Fixed-target comparisons control changing target composition. The full unqueried-target metric is the deployment estimand, while fixed targets are a diagnostic on a restricted candidate set. On Open LLM, A-optimal is worse than random at k=1; at k=4 all four eligible query tasks are observed and both policies coincide exactly. Do not summarize this diagnostic as a uniform selection gain.
- MTEB evidence is for English-labelled/involving embedding evaluations under selected task definitions. Dataset revision consistency does not ensure identical evaluator-code versions or training-data independence. Complete-row filtering, related task suites, and unverified model lineages limit generalization.
- Open LLM has six benchmarks only. Submission chronology is one dated partition, not ten independent temporal experiments or verified release chronology. Provider namespaces do not certify family holdout.
- All conclusions are exploratory and conditional on the measured cohorts. Bootstrap intervals resample model names after repeated split/query averaging and do not remove lineage dependence. No inference about benchmark runtime savings beyond a query count is supported.
- Superseded pilots, the negative-prediction clipping correction and commit-SHA alias audit are recorded in RUN_LOG.md; only final corrected outputs feed these tables.
