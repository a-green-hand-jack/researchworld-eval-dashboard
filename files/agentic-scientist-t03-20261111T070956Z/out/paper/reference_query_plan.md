# Reference Query Plan

**Central topic.** Whether a single run of a budget-limited stochastic Kernel SHAP explainer gives a reliable top-k feature attribution for a trained tabular model, and whether per-instance reliability can be predicted from that one run (within-run variance diagnostics) rather than from repeated runs.

## Grounding
Search-stage evidence: Kernel SHAP evaluator on Pima and German Credit, budgets of 4d and 16d coalitions, repeat-run label = mean top-k Jaccard. Three variants were evaluated: diagonal jackknife (0.976), covariance-aware antithetic simulation with calibration (0.984), and partition-ensembled jackknife with budget-prior empirical-Bayes shrinkage (0.985; sealed final about 0.984). Mean label is 0.84 at low budget vs 0.96 at high budget in search (0.81 vs 0.93 sealed). Spearman of r_hat vs label is about 0.54. Gains over a gap heuristic and always-reliable baseline are small (about 0.01), and a permuted control scores close behind. No ablation directory exists, and no deep tabular models appear in the run.

## Queries
1. `Improving KernelSHAP: practical Shapley value estimation using linear regression` (core_method) — Kernel SHAP sampling, paired sampling and variance reduction are the stochastic estimator whose rerun noise is studied.
2. `Shapley value estimation sampling error bounds approximation guarantees` (baseline_comparator) — Theory of estimator error under limited coalition budget (leverage-score sampling and related) frames why reruns differ.
3. `uncertainty quantification confidence intervals for Shapley value estimates feature attribution` (core_method) — The self-diagnostic quantifies within-run uncertainty of attributions; closest prior work on SHAP error bars.
4. `stability of post-hoc explanations LIME SHAP repeated runs random sampling instability` (baseline_comparator) — Direct comparator literature on rerun and perturbation instability of sampled explainers.
5. `top-k feature attribution agreement metrics rank-biased overlap Jaccard rank correlation explanations` (core_method) — Reliability label is top-k Jaccard; need justification and comparison with rank-aware similarity measures.
6. `delete-a-group jackknife variance estimation` (architectural_shift) — Delete-one-group jackknife of the Kernel SHAP regression is the mechanism behind the single-run diagnostic.
7. `empirical Bayes shrinkage noisy variance estimates` (architectural_shift) — Best variant shrinks the simulated stability estimate toward a budget-level prior.
8. `interventional versus observational conditional expectation Shapley values background data choice` (result_driven_theme) — Clarifies that the study targets the reliability of the estimator, not the choice of value function; background resampling is a noise source.
9. `Statlog German Credit Pima Indians Diabetes tabular classification benchmark datasets` (benchmark_context) — Dataset provenance for the two evaluation datasets; keep only to find dataset citations.

## Rejected alternatives
Generic queries (explainable AI surveys, benchmarking, optimization) and deep tabular architecture queries were dropped, as the run grounds neither. Queries about campaign chronology were excluded. Nothing may target the prohibited prior paper. Starter literature (Lundberg and Lee, Krishna et al., Yuan et al., Musco and Witter, Chen et al., Nogueira et al., Webber et al., Ding et al., Gorishniy et al.) is assumed already known, so queries seek complementary work.
