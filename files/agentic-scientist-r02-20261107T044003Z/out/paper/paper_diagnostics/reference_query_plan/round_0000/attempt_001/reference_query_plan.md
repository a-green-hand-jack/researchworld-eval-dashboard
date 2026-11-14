# Grounded Reference Query Plan

**Status:** ready. **Scope:** planning only; nine queries, no retrieval and no verified new citations.

## Central Topic

Coverage and common-simplex-volume efficiency of externally split-calibrated, training-adaptive ILR ellipsoids for strictly positive continuous compositional regression across synthetic noise, boundary, and covariate-shift regimes.

## Grounding and Evidence Limits

- `paper_data.json` supplies three evaluated variants, three search seeds per variant, and a completed five-seed final evaluation. Its `best_correct` variant is the four-fold out-of-fold ILR residual model. The final evidence contains coverage indicators, Wilson intervals, paired seed bootstrap comparisons, and volume integration errors; earlier implementation notes saying results were unavailable describe the editing stage, not the released evidence.
- Method details come from `results/ideas/02_cross_fitted_ilr_residual_geometry/program_1/src/program.py` and its `IMPLEMENTATION.md`, plus the continuous-interpolation variant's implementation notes. `task/evaluate.py` defines the actual baselines, generators, calibration ranks, descriptive strata, and common volume probes. `task/resources/final/manifest.json` documents dimensions, controls, and the five final seeds. These local artifacts, not private planning memory or proposal titles, determine this plan.
- The best search utility is 0.8818756857036072 for four-fold residual fitting, versus 0.8776261506257234 for the single-split adaptive variant and 0.8818118342646846 for continuous interpolation. These are selection summaries, not confidence intervals or isolated mechanism tests. Replacing the residual split also refits location on more training rows; no dedicated ablation isolates these effects.
- Final aggregate coverage is 0.8941579861111111 at target 0.90. The paired coverage-difference interval versus Euclidean is [-0.006536458333333344, 0.0038541666666666806]; the corresponding baseline-minus-candidate volume interval is [-0.05460599263509114, -0.0115142822265625]. Against isotropic ILR, the respective intervals are [0.018515625000000004, 0.03188368055555556] and [0.03055864969889323, 0.06176579793294271]. Thus the released comparisons support a tradeoff, not dominance: adaptive ILR has better recorded coverage and volume than isotropic ILR, but larger average volume than Euclidean and an unresolved coverage difference. Five-seed percentile bootstrap intervals remain unstable.
- Averaging the five released final episodes within each case gives C3 volume 0.9758560180664062 and C4 coverage 0.86328125. These motivate boundary-related efficiency and exchangeability-limit queries, not a universal robustness claim. The reported worst-stratum coverage of zero includes empty negative-sign strata in constant-input C5; it does not establish zero empirical coverage in a populated subgroup.
- No existing `references.bib` or `references_provenance.json` is present, so there are no prior retrieval queries to retain or correct. `figures/` is empty. No external papers, citation services, or prohibited publication pages were accessed in this planning stage.

## Core Methods and Comparators

The implemented family uses quadratic-feature ridge regression in orthonormal isometric log-ratio (ILR) coordinates. Four-fold held-out location residuals feed log-residual variance regression and regularized pooled/group second-moment shapes. Training-frozen tertiles of the minimum predicted component route positive-definite shapes; independent external split calibration selects a single 0.90 joint-coverage threshold. Cholesky factors implement covariate-adaptive ellipsoids.

Actual baseline literatures are Euclidean residual balls intersected with the simplex and isotropic ILR/Aitchison-distance balls. The Euclidean baseline clips and renormalizes its composition-space ridge predictions. Evaluated adaptive variants compare the single 75/25 training split with four-fold residual fitting, and hard tertile routing with continuous convex covariance interpolation. Point-copy singletons, the full simplex, constant inputs, and deranged training pairs are sanity controls, not additional learned methods.

Conditional-coverage theory and weighted conformal inference under shift are relevant positioning literatures only. Separate group calibration, importance weighting, jackknife+, CV+, Hellinger sets, and structural-zero handling were not implemented.

## Benchmark Context

All responses are observed continuous, strictly positive compositions, not categorical labels or unidentified latent class-probability vectors. There is no executed public-image or other real-data benchmark.

| Local case | Scientifically relevant context |
| --- | --- |
| C1 | K=3 homoskedastic logistic-normal regression; five Gaussian covariates |
| C2 | K=3 covariate-dependent heteroskedastic logistic-normal regression |
| C3 | K=8 near-boundary Dirichlet regression |
| C4 | K=8 Dirichlet regression with test-only covariate location and scale shift |
| C5, C6 | Matched C2-derived constant-input and training-pair-derangement controls, not independent datasets |

Search the generator families, not the local C1-C6 identifiers. The final per-case split sizes are 4096 training, 2048 calibration, and 3840 test observations. Exact zeros, arbitrary real compositions, and classifier probability-vector uncertainty are outside the evidence.

## Representation and Configuration Shifts

1. **Representation:** Euclidean simplex-coordinate balls versus isotropic ILR balls versus adaptive ILR ellipsoids. These are small ridge predictors, not a neural architecture transition.
2. **Residual estimation:** a single 75/25 training split versus deterministic four-fold out-of-fold residuals plus an all-row final location refit. Cross-fitting is internal training, not cross-conformal calibration or a source of independent conformal guarantees.
3. **Shape routing:** hard training-fixed boundary tertiles versus continuous convex interpolation of training-estimated covariance shapes. The small search-utility difference does not establish a reliable interpolation benefit.

## Result-Driven Themes

Prioritize residual estimation and positive-definite shape adaptation because they recur in the strongest implemented variants. Frame their relation to efficiency as evidence-limited, given the changed location training size and absence of isolating ablations. Use the final evidence to motivate regime-dependent coverage-volume tradeoffs, near-vacuous boundary-case volumes, covariate-shift limitations, and the distinction between marginal and descriptive subgroup coverage. Compare regions with shared uniform-simplex probes: coordinate-space volume is not a common measure. Wilson test intervals, paired seed bootstrap intervals, and integration errors quantify distinct uncertainty sources; three search and five final seeds do not justify strong replication claims.

## Nine Queries

| # | Category | Query | Run-specific purpose |
| --- | --- | --- | --- |
| 1 | core_method | `"Distribution-Free Predictive Inference For Regression" Lei` | Allowed starter-title lookup for independent split calibration, finite-sample ranks, and marginal guarantees. |
| 2 | baseline_comparator | `isometric log-ratio transformation Aitchison distance compositional data` | ILR representation and isotropic/Aitchison comparator versus Euclidean geometry; starter Aitchison background is relevant. No conformal terminology in this query. |
| 3 | core_method | `multivariate split conformal prediction Mahalanobis ellipsoidal regions` | General vector-valued standardized residual norms and Cholesky-shaped regions, without the composition-specific task intersection. |
| 4 | architectural_shift | `out-of-fold residuals heteroskedastic regression variance estimation` | The strongest search variant's held-out residuals and variance fitting; distinguish training cross-fitting from CV+, jackknife+, and cross-conformal calibration. |
| 5 | architectural_shift | `covariance shrinkage positive definite heteroskedastic multivariate regression` | Shared pooled/group shape regularization and numerical stability; interpolation remains a secondary, unproven refinement. |
| 6 | benchmark_context | `logistic-normal Dirichlet regression compositional responses boundary` | The actual positive-composition generators, heteroskedasticity and boundary regimes; no unused public dataset names or conformal terminology. |
| 7 | result_driven_theme | `distribution-free predictive inference marginal conditional coverage limitations` | Pooled calibration does not imply subgroup guarantees; descriptive strata and empty controls require care. |
| 8 | baseline_comparator | `"Conformal Prediction Under Covariate Shift" Tibshirani` | Allowed starter-title lookup for exchangeability failure and the unevaluated weighted-conformal alternative to shifted C4. |
| 9 | result_driven_theme | `multivariate prediction regions volume efficiency Monte Carlo integration` | Common-measure region efficiency, paired integration errors, and near-full-simplex volumes, distinct from coverage and seed uncertainty. |

## Exclusions and Retrieval Safety

These restrictions mirror `forbidden_query_patterns` in the JSON:

- Never identify or guess the prohibited task-specific paper or inspect its title, authors, results, mirrors, abstract/review/presentation pages, repositories, or pages citing, discussing, or reproducing it. This plan does not identify that paper.
- Avoid broad task-identifying combinations such as “conformal prediction compositional outputs reliability evaluation,” “conformal compositional benchmark,” or “conformal simplex comparison.” Keep general conformal method searches separate from composition-only representation and generator searches. This separation reduces exposure risk; it cannot certify that every future search result is permissible.
- Do not citation-chain, run cited-by searches, expand related-paper graphs, or browse aggregation/review pages that could expose forbidden content. Begin later retrieval with permitted starter-title lookups and narrowly scoped methods. If prohibited material is encountered accidentally, stop reading immediately and record the location and extent of exposure; do not continue through snippets or linked pages. No retrieval occurs now.
- Exclude CIFAR-10, APS/RAPS, image classifiers, softmax networks, transformers, and any other public dataset or neural architecture not executed here. Their appearance in task possibilities does not establish benchmark use.
- Exclude Hellinger or smoothed-log-ratio comparisons, structural-zero robustness, and latent-probability/credal-set coverage inferred from labels. The original Hellinger proposal title is not implementation evidence.
- Do not describe groupwise/Mondrian calibration, multivalid coverage, jackknife+, CV+, or importance weighting as executed methods. If needed later, distinguish them explicitly as unevaluated alternatives rather than add speculative comparator claims.
- Reject queries premised on universal superiority, guaranteed conditional coverage, a demonstrated interpolation gain, or shift robustness.
- Reject generic optimization, benchmarking advice, scientific-method or paper-writing queries, campaign chronology, internal attempt names, and local case IDs as standalone literature searches. The chosen queries instead map directly to implemented residuals, geometry, data families, or observed limitations.

## Handoff

The JSON is the machine-readable query contract. Query strings express literature needs, not verified bibliographic facts. Later retrieval must independently verify permitted sources before citing them. No bibliography, reference provenance, manuscript, or claims-grounding artifact is created or modified in this stage.
