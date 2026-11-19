# Completed synthetic evidence handoff

Status: full planned synthetic grid completed and validated, real LLM experiment not yet run. Do not describe the overall study as complete.

## Evidence and provenance

- `scripts/run_synthetic.py`: exact joint-count sampler, selection rules, intervals, budget comparisons, seeds.
- `docs/synthetic-spec.md`: generative model and planned grid; `docs/statistical-guarantees.md`: proofs/conditions.
- `results/synthetic-main.jsonl`: all 288 cells × 25 metrics, 20000 independent repetitions per cell, per-metric mean and Monte Carlo standard error.
- `results/synthetic-summary.csv`: same results, directly usable by presentation scripts; every row identifies n,K,rho,spread,seed.
- `results/synthetic-main.summary.json`: measured 89.8811 computational wall seconds, 89.7073 process CPU seconds, peak RSS 285564 KB. These timers exclude interpreter/import startup.
- `scripts/exact_null_reference.py` and `results/synthetic-exact-null.csv`: exact, nonsimulation references for all 48 independent equal-quality cells. `results/synthetic-exact-check-*.csv` / `synthetic-validation.json` preserve simulation-reference discrepancies. All standardized discrepancies are below 5 Monte Carlo SE; maximum is 3.651 across 144 comparisons.
- `tests/check_synthetic.py` validates the generating distribution against analytic means/covariances and dependence endpoints independently of reported empirical patterns.

## Claim-level findings (proportions, not percentage points)

1. Reusing a winner's selection score can be markedly optimistic, and this depends on n,K and shared question errors. At n=64,K=16,rho=.5,spread=0, optimism is .077055 (MCSE .000354), naive 95% CP coverage .822950 (.002699), simultaneous coverage .982900 (.000917), independent-audit coverage .958350 (.001413). Equal-quality candidates have no real improvement, so this isolates selection.
2. Decision errors occur even with a conservative comparison. The largest observed false-superiority frequency for the prespecified nonoverlapping marginal-interval rule was .098900 (MCSE .002111), at n=512,K=128,rho=0,spread=0. The nominal frozen-pair rule has family error at most .05 before winner selection. Do not generalize this number to all decision rules, or call it conditional FDR.
3. Across the entire grid, selected-candidate naive coverage ranges from .051650 to .975250. Simultaneous coverage ranges from .951450 to .999550; independent same-size-audit coverage from .950650 to .976050. These are point estimates over a prespecified grid, not simultaneous confidence guarantees for their measured minima. Exact CP discreteness and Bonferroni conservatism matter.
4. Strongly correlated errors and a clear quality advantage can make optimism much smaller. At n=512,K=128,rho=.9,spread=.08, optimism is .010308 (MCSE .000152), selected true quality .476406 (MCSE .000028), versus .474746 (MCSE .000040) for a half-search/half-audit split at equal total question budget. This demonstrates a quality cost of reserving questions; the independent same-size audit uses additional resources and must not be compared as cost-free.
5. Holdout and simultaneous methods solve different problems. Holdout gives an unbiased score of the frozen selected system with exact fixed-system uncertainty, whereas simultaneous intervals protect selection within a frozen bank but do not debias the reused point score. Neither dominates on interval width, MSE, calls and selected quality in every setting. Zero empirical error or MCSE is not proof of zero population risk (zero events among 20000 gives one-sided 95% upper bound about .000150).

## Presentation requirements supplied to figtab

Show bias/coverage versus n and K with separate rho/spread panels or selected clearly labeled slices; a nominal .95 line is essential for coverage. Compare uncertainty/selected quality under equal question and equal model-call budgets, labeling the extra-cost independent audit. Do not use the smallest coverage or largest decision error without identifying its setting. Keep synthetic truth distinct from real fresh-question estimates.

## Interpretation limits and unfinished evidence

The mixture is deliberately controlled and the bank is frozen; it does not model all real prompt dependence or an optimizer creating new prompts from labels. K changes the true-quality grid in heterogeneous cells, so clean budget effects are isolated in equal-quality cells. The CP and proof statements assume iid question sampling. The real LLM experiment must still establish how these mechanisms appear on actual generated responses. No real-model performance number has been measured yet.
