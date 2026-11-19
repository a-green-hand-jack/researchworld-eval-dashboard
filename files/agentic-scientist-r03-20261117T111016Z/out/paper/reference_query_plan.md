# Reference Query Plan

**Status:** ready. Planning only; no references have been retrieved or verified in this stage.

## Central topic

Predict unmeasured MTEB text-embedding benchmark scores for held-out models from a small queried benchmark budget using low-rank score-matrix prediction and historically calibrated local residual corrections.

## Grounding and boundaries

- `paper_data.json` identifies the strongest successful configuration and contains the final evaluation: three seeds, budgets 1/2/4/8, aggregate MAE **0.040807843083862115**, and reported best-baseline MAE **0.045249969215420516**. These are combined-system results, not component effects.
- `results/best_program_manifest.json` selects `results/ideas/02_cross_fitted_local_residual_medians/program_1`. Its `src/program.py` and `src/RESIDUAL_METHOD.md` ground the ALS estimator, fixed covariance-based query policy, cross-fitted donor residuals, overlap-aware weighting, weighted medians, shrinkage, and zero-blend fallback. The method note describes implementation and training diagnostics, not an independent outer ablation.
- `results/ideas/01_overlap_aware_transfer_design/program_1/src/METHOD.md` and its evaluation evidence ground an evaluated overlap-shrunk covariance alternative. Its search MAE was **0.05298799410472327**, versus **0.04592733209327031** for the selected configuration in search. This comparison is not a matched final ablation and does not isolate selection from estimation.
- `task/resources/search/manifest.json` and `task/resources/final/manifest.json` verify MTEB results revision `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`, supported English main-metric scores normalized to [0,1], 127 search-plane model rows and 126 final-plane model rows. The final matrix has 135 task/subset columns; these are not necessarily 135 independent benchmark datasets.
- `task/resources/final/plan.json` specifies duplicate-group and heuristic family-plus-duplicate holdouts, sealed common targets, and constant-history/permuted-column controls. Family heuristics do not certify training ancestry.
- `figures/` is empty. Neither `references.bib` nor `references_provenance.json` exists, so there is no prior retrieval history to endorse or repeat. Recent global memory served only as an inspection guide, not quantitative evidence.

## Method and comparator coverage

The core neighborhoods are masked ridge ALS matrix completion with conditional cold-start inference; cross-fitted, overlap-aware local residual medians with effective-count shrinkage; and greedy integrated predictive-variance reduction. The separately evaluated covariance alternative motivates missing-data covariance shrinkage and positive-semidefinite repair literature.

Expected conceptual comparators are cold-start collaborative filtering, local conditional-median/neighborhood prediction, V-optimal experimental design, active rating elicitation, example-level compression in tinyBenchmarks, observational capability scaling, and Sloth skill-based multi-benchmark prediction. The named starter works and alternative design rules are literature comparators, not claims that those methods were implemented as experimental baselines.

**Architectural shifts: none supported.** Model-family grouping is an evaluation safeguard, not an encoder/decoder, mixture-of-experts, or representation-transition experiment. MTEB uses text-embedding models; results cannot be presented as demonstrated generalization to generative LLMs or optional leaderboards.

## Result-driven search priorities

- Final aggregate MAE decreases from **0.04523334197776794** at one query to **0.03615046021288207** at eight queries. Search budgeted cold-start elicitation rather than claiming a universal sufficient budget.
- The combined estimator outperforms the reported best baseline in the final aggregate. No independent outer ablations attribute this to residual calibration, cross-fitting, shrinkage, or selection individually.
- Constant-history and independently permuted-column controls have aggregate MAEs **0.06436711309859705** and **0.06856952089296987**, respectively, above intact-history MAE. This motivates cross-column dependence, but not a new causal or statistical-significance claim.
- Relatedness-aware holdouts bound interpretation; pooled results do not establish superiority in every family, task, or missingness regime. The support-distance gating variant has no successful evaluation and is not a positive literature-search lead.

## Nine planned queries

1. **Core method:** `regularized matrix factorization alternating least squares cold-start collaborative filtering`
   - Grounds the actual masked ridge ALS and new-model conditional estimator in matrix completion and cold-start recommendation, without inventing a neural architecture.
2. **Core method:** `kernel weighted conditional median regression absolute loss`
   - Grounds Gaussian-profile-weighted donor residual medians and their MAE motivation. Do not imply Bayes optimality of the full clipped, shrunk correction or a demonstrated independent component gain.
3. **Core method:** `V-optimal experimental design Bayesian linear regression integrated predictive variance`
   - Matches summed predictive covariance reduction in the preserved latent-factor selector. It is more precise than calling the rule D-optimal information gain; design alternatives were not independently ablated.
4. **Baseline comparator:** `covariance estimation missing observations shrinkage positive semidefinite`
   - Explains the evaluated overlap-shrunk covariance alternative and its repair step. Its weaker search result is contextual, not a matched final negative finding.
5. **Baseline comparator:** `"tinyBenchmarks: evaluating LLMs with fewer examples"`
   - Uses an explicitly permitted starter reference to distinguish example-level compression from whole-benchmark selection and cross-task score inference. Not an implemented baseline.
6. **Baseline comparator:** `"Observational Scaling Laws and the Predictability of Language Model Performance"`
   - Uses an explicitly permitted starter reference for latent-capability performance prediction; contrast observational scaling with conditioning on a small measured profile. No experimental comparison is claimed.
7. **Baseline comparator:** `"Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families"`
   - Uses an explicitly permitted starter reference for skill-based prediction across families. Family-group holdouts motivate the comparison but do not establish architectural transfer or an implemented Sloth baseline.
8. **Benchmark context:** `"MTEB: Massive Text Embedding Benchmark"`
   - Establishes actual text-embedding task/metric context. The pinned result manifest, not the original paper alone, supplies snapshot provenance.
9. **Result-driven theme:** `active collaborative filtering cold-start rating elicitation query budget prediction error`
   - Contextualizes measured errors at budgets 1/2/4/8 using established active-elicitation work. This covers the budget/design tradeoff, distinct from query 1 on the factor estimator, without a broad task-specific search.

## Forbidden patterns and retrieval safeguards

- Do not issue broad task paraphrases such as “predict LLM benchmark scores from few benchmarks” or “benchmark selection LLM performance prediction.” Do not attempt to identify the prohibited paper, its authors, or its findings.
- Do not access that paper or mirrors, preprints, abstracts, reviews, slides, posters, videos, blogs, code, reproductions, or pages citing or discussing it. Do not expand cited-by, related-paper, survey, or citation chains from allowed sources.
- For queries 5–8, restrict future retrieval to exact-title original records of the explicitly permitted starter works, not unrestricted web/full-text expansion. For other queries, stay within foundational statistics, experimental design, and recommender-method literature. These constraints reduce risk but cannot certify that an unknown page is safe. Stop reading immediately and log where and how much was seen if prohibited content is encountered; do not use it.
- Do not treat Open LLM Leaderboard, HELM, LiveBench, BigCodeBench, AlpacaEval, MMLU, or generative tasks as evaluated datasets. Do not invent encoder-to-decoder, dense-to-mixture-of-experts, architectural-transfer, or representation-transition stories.
- Avoid generic optimization, benchmarking, scientific-method, paper-writing, campaign chronology, and milestone queries. Avoid presumed successes for support-distance gating, presumed completed residual ablations, missing-not-at-random correction claims, or universal eight-query sufficiency.

## Why this set

The nine queries cover the successful estimator, its preserved selection rule, the evaluated covariance contrast, three precisely identified permitted comparator works, the actual dataset, and the measured budget-error theme. General LLM evaluation searches would be less specific and risk prohibited material. Extra task-origin citations, unrelated optional leaderboards, generic cross-validation searches, causal-inference cross-fitting frameworks, and untested architecture stories would dilute the contribution. No retrieval, paper writing, or experiment execution belongs to this stage.

**Failure reason:** empty; the local source, evaluation, and resource manifests support a coherent literature neighborhood.
