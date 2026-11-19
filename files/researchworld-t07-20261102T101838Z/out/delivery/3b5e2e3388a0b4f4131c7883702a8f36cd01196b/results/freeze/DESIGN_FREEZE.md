# Freezing the proposed method (P3) by source-internal CV

Procedure (code: `code/run_experiment.py --inner`, `code/aggregate.py`): for pilot benchmarks ifeval, gsm, mmlu_pro, an outer
split (same seeds as the final run) is drawn; **only its source models S** form the population of an inner split
(random 25% inner targets, or the strongest 25% of S as inner targets), 8 seeds each, budgets 10/20/50/100/200. No
outer-target model is used. Candidates: selector {random, strat, pps, ppsq} x model-assisted estimator {IRT, low-rank} x
{difference estimator (dr), empirical-Bayes-shrunk correction (eb)}, plus random+mean, strat+mean, random+cal.
Selection rule fixed beforehand: lowest mean rank of MAE (over benchmarks, budgets and the two inner split types).

Result (mean MAE-rank, see `inner_cv_summary.csv`): strat+lowrank_dr 6.68, strat+lowrank_eb 6.86, pps+lowrank_eb 6.89, ...
=> **P3 := `strat+lowrank_dr`** (stratified-by-source-difficulty sample + low-rank model prediction + Hajek-weighted
mean-residual correction). `strat+lowrank_eb` (shrunk correction) is a pre-declared secondary variant (rank within 0.2).
Both are evaluated in the final run; nothing else is tuned afterwards. The pilot trials of 2-4 benchmarks used before this
freeze (gpqa, mmlu_pro with outer targets, 2-4 seeds) informed the *candidate list* (that is disclosed) but not the choice.
