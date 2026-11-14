# Grounded Reference Query Plan

**Status:** ready. Planning only: no reference retrieval, source-reading claims, or bibliography generation.

## Central topic

Select a small number of MTEB embedding tasks and use their measured scores to predict a held-out model's remaining task scores from a naturally incomplete historical model-by-task matrix. Absolute prediction error is the measured objective. This is an embedding-evaluation study, not evidence about generative-model benchmarks in general.

## Grounding and boundaries

The decisions below use `paper_data.json`, the retained configuration's source and method notes, and local task manifests. Private planning memory is not used as empirical evidence.

- `paper_data.json` → `final_evaluation.metrics` records candidate MAE **0.031296949105441715**, greedy-ridge MAE **0.036070484115358764**, random-low-rank MAE **0.04563401706946738**, and historical-mean MAE **0.08782454238980078**. These are aggregate results, not mechanism-specific effects or significance tests.
- Final permuted MAE is **0.08976440453371944**. The columnwise control preserves marginal score information while disrupting cross-task alignment; the degradation supports dependence on joint score structure, not a causal interpretation of transfer.
- `results/best_program_manifest.json` selects the latent-mixture-capable configuration in `results/ideas/02_value_adaptive_latent_mixtures_for_absolute_error_benchmark_prediction/program_1/`. Its source implements missing-data factor analysis, conditional Gaussian inference, latent mixtures, bounded marginal medians, and value-dependent acquisition.
- The quadrature extension in `results/ideas/03_quadrature_bayes_risk_selection_for_latent_benchmark_mixtures/program_1/` ties the retained configuration's aggregate search MAE, **0.032779113034713904**. Implementation alone does not establish use or benefit of quadrature, multiple components, or posterior medians in any particular outer evaluation. Candidate diagnostics are marked unverified; `ablation_studies` is empty.
- `task/resources/search/manifest.json` and `task/resources/final/manifest.json` identify genuine MTEB results at revision `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`, naturally missing scores, model-group and family-disjoint cases, fixed nonqueryable audit targets, and budgets **1, 2, 4, 8**. Family annotations are name-derived lineage proxies, not verified ancestry.
- `figures/` is empty. Neither `references.bib` nor `references_provenance.json` exists, so there is no previous retrieval query set to inherit or correct.

## Method and comparator neighborhoods

**Core methods:** observed-data factor-analysis EM with low-rank-plus-diagonal covariance; exact Gaussian conditioning; regularized latent Gaussian mixtures on fixed factor loadings; bounded posterior-median prediction; off-diagonal covariance-transfer selection; and a moment-matched standard-deviation-reduction surrogate. Historical model-heldout validation uses fixed target tasks excluded from acquisition. The implemented quadrature-integrated absolute-risk extension is secondary context, not an independently established improvement.

**Measured comparators:** random task panels with low-rank prediction, correlation-coverage greedy selection with ridge prediction, historical per-task means, and observed-score-copy controls. Matrix completion is relevant to the incomplete score matrix, but held-out-row prediction under a query budget is not identical to transductive historical-cell completion. Standard ridge and constant controls need no separate broad literature hunt.

**Related-work comparators, not executed baselines:** tinyBenchmarks and metabench for evaluation compression; Observational Scaling Laws and Sloth for latent performance structure and cross-family prediction; Bayesian active feature acquisition and prediction-oriented experimental design for acquisition principles. Item-level compression, whole-task acquisition, and compute/skill scaling must remain distinct. D-optimal control experiments are not established by the supplied results.

**Benchmark context:** MTEB classification, semantic textual similarity, clustering, and retrieval/reranking. Visible examples include Banking77Classification, STSBenchmark, ArguAna, and AskUbuntuDupQuestions. One MTEB source query provides more useful context than separate citations for every panel column. Other supplied optional leaderboards are not evaluated datasets here.

**Architectural shifts:** none established; the JSON field is deliberately empty. A Gaussian-to-mixture change is a statistical representation change, not a neural architecture experiment. Family-disjoint results do not establish encoder/decoder, dense/MoE, size, language, or chronological transfer.

## Query set

These ten queries are retrieval inputs, not retrieved or verified citations. The five exact-title seeds are explicitly permitted in the task's starter list. Classical statistical queries should target original methodological sources rather than unrestricted modern benchmark-prediction discovery.

1. **Core method:** `factor analysis expectation maximization missing observations diagonal residual covariance`
   Grounds the observed-entry likelihood, latent posterior moments, diagonal task residuals, and conditional predictor. Avoid substituting generic PCA or zero-filled factorization for the implemented model.
2. **Core method:** `mixtures of factor analyzers missing data latent Gaussian mixture`
   Locates the parent literature for observation-dependent component inference. The implementation shares factor loadings and residual covariance; do not describe it as an unrestricted mixture of independently fitted factor analyzers.
3. **Core method:** `Bayesian active feature acquisition expected prediction loss experimental design`
   Connects purchasing task scores to predictive-risk reduction, covering covariance transfer, the mixture surrogate, and the quadrature alternative without claiming exact information gain or universal optimality.
4. **Baseline comparator:** `low rank matrix completion collaborative filtering matrix factorization`
   Grounds incomplete score-matrix modeling and the random-panel low-rank baseline. Distinguish historical-cell completion from conditional prediction for previously held-out models.
5. **Benchmark context:** `"MTEB: Massive Text Embedding Benchmark"`
   Establishes the actual embedding-task setting and scope, not a generative-model evaluation claim.
6. **Baseline comparator:** `"tinyBenchmarks: evaluating LLMs with fewer examples"`
   Provides the expected item-level compression comparison; it was not executed as a baseline.
7. **Baseline comparator:** `"metabench" "A Sparse Benchmark of Reasoning and Knowledge in Large Language Models"`
   Provides sparse multi-benchmark reconstruction context while preserving the distinction between sampled items and whole embedding tasks.
8. **Baseline comparator:** `"Observational Scaling Laws and the Predictability of Language Model Performance"`
   Positions low-dimensional historical score structure without implying that the present method fits a compute-scaling law.
9. **Baseline comparator:** `"Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families"`
   Provides latent-skill and across-family prediction context, with explicit limits on the local family proxies and architectural interpretation.
10. **Result-driven theme:** `Bayesian decision theory posterior median absolute error loss`
    Grounds the implemented prediction rule under MAE. Optimality under the fitted distribution is not proof of superior real-data accuracy or an isolated median-versus-mean gain.

## Result-driven interpretation

The strongest supported story concerns conditional prediction from cross-task structure under a small measurement budget. The aggregate baseline and permutation contrasts make that neighborhood more relevant than generic optimization or benchmarking literature. MAE motivates decision-theoretic grounding, but the supplied evidence does not isolate mixture inference, median prediction, or adaptive acquisition as the cause of the observed advantage.

Fixed audit targets deserve discussion because querying a task removes its error from the changing complement. Neither monotone gains with budget nor a universally sufficient budget follows from aggregate losses over four checkpoints. The family-disjoint case motivates qualified generalization discussion, not a verified architecture-shift claim. Natural missingness also does not establish robustness to arbitrary selective reporting or missing-not-at-random mechanisms.

## Retrieval safeguards and rejected alternatives

- Do not identify or speculate about the prohibited paper, its authors, title, findings, materials, or code. Avoid unrestricted searches for selecting LLM benchmarks or predicting unmeasured benchmark scores. The specific permitted starter titles and classical foundations are safer, higher-signal entry points.
- No citation chasing, related-paper feeds, or pages citing, discussing, reproducing, reviewing, or mirroring prohibited material. Exact-title queries are entry points, not a guarantee that every result is safe: inspect only permitted original sources. If prohibited content is encountered incidentally, stop reading immediately and record the location, what appeared, and how much was seen.
- Reject campaign-order and search-history queries: they explain workflow, not the scientific contribution. Reject generic optimization, scientific-method, paper-writing, and broad benchmarking queries because they dilute the implemented statistical and decision-theoretic neighborhoods.
- Reject unsupported architecture-transition searches, optional unrun leaderboard contexts, and queries presupposing quadrature superiority, proven specialization, causal transfer, a universal budget, or nonrandom-missingness robustness.
- No sources were retrieved in this stage, and no prohibited material was encountered during this local-artifact planning pass. The downstream retrieval stage must verify sources before any citation or claim that a work was read.

## Handoff

Use the ten JSON queries with these scope and safety restrictions. Leave bibliography, reference provenance, paper text, and claim-grounding artifacts to later stages. No additional experiment or reference retrieval is needed to mark this planning stage ready.
