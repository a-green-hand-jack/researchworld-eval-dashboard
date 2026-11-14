# Post-draft reference query plan

**Status:** ready. The gap memo found three narrow gaps in an otherwise well-cited draft. The plan has five queries, all tied to a specific gap and anchor text. Retrieval has not been run.

**Central topic:** reliability of a single run of budget-limited stochastic Kernel SHAP for tabular top-k attributions, predicted per instance by a delete-one-group jackknife with budget-prior shrinkage.

## Queries

1. **Repeated-run stability of LIME explanations** (`baseline_comparator`, high priority)
   - Query: `stability of LIME explanations repeated runs random perturbation sampling instability index`
   - Gap: `related-work-instability-comparators`. Related Work cites only generic robustness and disagreement papers (Alvarez-Melis, Krishna, Yuan).
   - Purpose: find the closest comparators that measure rerun repeatability of sampled explainers, so the "narrower source of variation" claim has something to be compared with.

2. **Per-instance uncertainty for Kernel SHAP** (`baseline_comparator`, high priority)
   - Query: `confidence intervals standard errors for Kernel SHAP sampled Shapley estimates per instance uncertainty`
   - Gap: same as above. The claim "a statement about the run rather than the estimator's average error" is positioned only against population-level inference (Williamson2020Efficient) and worst-case guarantees (Musco2024Provably, Covert2020Improving).
   - Purpose: cite per-instance sampling-uncertainty work for SHAP-style estimators.

3. **Delete-a-group jackknife** (`core_method`, medium priority)
   - Query: `delete-a-group jackknife variance estimation`
   - Gap: `method-jackknife-shrinkage-rationale`. The "delete-one-group jackknife covariance" has no statistical source.
   - Purpose: one or two foundational references to ground the terminology.

4. **Empirical Bayes shrinkage** (`core_method`, medium priority)
   - Query: `empirical Bayes shrinkage estimation toward a prior`
   - Gap: same as above. The draft calls shrinkage toward a budget-specific prior "empirical-Bayes-style" without a source.
   - Purpose: one foundational empirical Bayes or James-Stein reference.

5. **Deployment use of attributions** (`benchmark_context`, low priority)
   - Query: `explainable machine learning in deployment how practitioners use feature attributions`
   - Gap: `intro-deployment-claim`. The credit and medical deployment claim, and the "run once" practice, rest only on Lundberg2017Unified.
   - Purpose: one empirical deployment or practitioner study. Drop it if results are noisy.

## Deliberately excluded
- Dataset citations (German Credit, Give Me Some Credit, Pima). The appendix already gives sources, and the gap memo says not to add them.
- Shapley estimator variants, value-function semantics, rank-similarity measures and deep tabular models. These are already covered or out of scope.
- Any query on directions already in the bibliography: Covert2020Improving, Musco2024Provably, Mitchell2021Sampling, Nogueira2017Stability, Webber2010similarity, Yuan2022empirical, Chen2020True.
