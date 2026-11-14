# Grounded Reference Query Plan

**Status: ready.** Nine citation-oriented queries; no references retrieved or inspected externally in this stage.

## Scientific Focus

Study budget-constrained repeatability and reference consistency of fixed-game, probability-scale SHAP explanations for frozen German Credit and ACS income classifiers. The actual comparison is randomized Kernel SHAP versus structure-aware forest and logistic computations, not a general study of neural explanations or deployment safety.

The implemented families are empirical interventional Shapley games; Kernel SHAP regression with complement-paired coalitions and an importance-corrected permutation-prefix mixture; independent complete permutation paths with simultaneous empirical Bernstein bounds; exact forest leaf-game algebra; and logistic Fourier/Owen quadrature with capped refinement and sampled fallback. Exhaustive small-game and analytic affine controls and instance-clustered bootstrap intervals supply evaluation context.

## Grounding and Boundaries

- `paper_data.json`, especially `all_programs[*].evaluation_evidence.episodes`, records three evaluated configurations. Their non-replay cases are `german_logistic`, `german_forest`, `acs_logistic`, `acs_forest`, and controls. Case-level evidence supports improved agreement for the structure-aware branches; it does not establish better predictive accuracy.
- `paper_data.json` at `final_evaluation.evaluation_evidence` contains three final episodes, with seeds 104729, 130363, and 155921. Final aggregate metrics are reference fidelity 0.9975639445869278, top-3 overlap 1.0, signed agreement 0.9997395833333332, and replay error 0.0. These are distinct measured summaries, not a universal reliability guarantee. Reference uncertainty is persisted, including nonzero values in German cases.
- `results/ideas/03_probability_scale_logistic_shap_by_bounded_fourier_quadrature/program_1/src/IMPLEMENTATION.md` and its estimator sources ground the leaf decomposition, probability-scale Fourier/Owen computation, and independent-path certificate. Preparation-time statements that checks were unexecuted must not be confused with later evaluation evidence. Attribution-only outputs do not establish certificate acceptance or coverage.
- The persisted `standard`, `multistart`, and `baseline_metrics` observations ground the actual library Kernel SHAP comparators. The local evaluation implementation defines multistart as the average of two independently seeded half-budget runs. TreeSHAP and leverage-score sampling are expected literature comparators, not separately executed methods.
- `task/resources/final/provenance.json` identifies German Credit (UCI DOI 10.24432/C5NC77) and **ACSIncome-2024-RELSHIPP**. For the 2024 ACS data, native RELSHIPP replaces unavailable RELP; do not call this bit-identical historical ACSIncome. Frozen retained subsets, not assumed full original datasets, were evaluated. Zero/affine and feature-permutation fixtures are controls rather than extra datasets.
- The architectural comparison is logistic regression versus random forests, with a shift from black-box sampling to model-structure-aware computation. There is no measured deep architecture, representation-learning, retraining, or dataset-transfer experiment.
- A coalition sampling limit does not equate the wall-time cost of quadrature, leaf algebra, and model prediction. Deterministic replay, endpoint efficiency, and mesh convergence diagnostics do not individually prove fidelity. Fixed-background results do not establish background robustness, causal interpretation, fairness, or sufficiency for high-risk deployment.

`global_memory_summary.md` was used only as qualitative orientation; quantitative statements above come from the run artifacts. The figure directory is empty. Neither existing reference BibTeX nor provenance is present, so there are no prior retrieval queries to reuse or correct.

## Queries

| # | Query | Category | Run-specific purpose |
|---|---|---|---|
| 1 | `"A Unified Approach to Interpreting Model Predictions" Lundberg Lee` | core_method | Permitted starter anchor for SHAP semantics, kernel regression, and the actual one-shot/two-start baselines. |
| 2 | `"Provably Accurate Shapley Value Estimation via Leverage Score Sampling"` | baseline_comparator | Permitted starter anchor for budget-aware estimator guarantees; theoretical comparator only. |
| 3 | `TreeSHAP exact interventional tree ensemble Shapley values` | architectural_shift | Position exact leaf inclusion/exclusion algebra against established exact tree attribution, matching game semantics. |
| 4 | `Owen multilinear extension cooperative games Shapley value` | core_method | Ground the inclusion-probability polynomial integral explicitly used by the logistic branch. |
| 5 | `Shapley values logistic regression probability scale numerical integration` | architectural_shift | Find same-output-scale comparators; distinguish nonlinear probability attributions from logit coefficients without presuming a prior identical Fourier method. |
| 6 | `empirical Bernstein bounds sample variance bounded independent observations` | core_method | Check assumptions and constants for simultaneous independent-path bounds; distinguish marginal coverage from accepted-call conditional error. |
| 7 | `"On the Stability of Feature Selection Algorithms" Nogueira Sechidis Brown` | result_driven_theme | Permitted starter anchor for feature-set stability context; top-3 overlap is measured, but the adjusted selection-stability estimator is not claimed. |
| 8 | `"True to the Model or True to the Data?" Chen Janizek Lundberg Lee` | core_method | Permitted starter anchor for empirical interventional versus conditional explanation semantics and limits on causal interpretation. |
| 9 | `"Retiring Adult: New Datasets for Fair Machine Learning"` | benchmark_context | Permitted starter anchor for folktables/ACS context; document the local RELSHIPP adaptation independently. German Credit already has a precise dataset DOI. |

Queries 4 and 5 address different needs: foundational cooperative-game integration versus logistic output-scale attribution. The general SHAP query supplies the implemented Kernel SHAP baseline; there is no need for a duplicate broad sampling query. The numerical integration search is exploratory, not a claim of novelty or of an existing identically named method.

## Rejected Alternatives and Retrieval Safety

The JSON `forbidden_query_patterns` is the authoritative exclusion list. In particular:

- Do not identify or speculate about the prohibited paper. Do not access its primary or derivative material, abstracts, mirrors, reviews, slides, code, citing discussions, or reproductions.
- Avoid broad SHAP rerun-reliability, instability, and single-explanation-trust searches. Prefer the exact permitted starter titles and narrow foundational method queries above. Do not expand citation networks or browse related-paper recommendations, aggregators, surveys, blogs, or social discussions. Exact-title anchors reduce exposure but do not make derivative pages safe.
- For non-title queries, limit downstream retrieval to primary method/theory records and sources whose permitted relevance can be established. If that cannot be done without prohibited exposure, skip the query and record the gap rather than broadening it. Never infer the forbidden study's identity to create an exclusion filter.
- If prohibited material is encountered accidentally, stop reading immediately and record what appeared, its location, and how much was seen in the reproduction log. No such encounter occurred in this local-only planning stage.
- Reject FT-Transformer/tabular ResNet and deep-background stability searches: those architectures were only possible task context, not measured configurations. Likewise omit Pima, Give Me Some Credit, and Arrhythmia because they are not observed evaluation datasets.
- Reject predictive multiplicity and retraining variability: the fitted model is held fixed. Reject fairness, causal validation, background-size ablations, and learned abstention as claimed experimental themes because the artifacts do not establish them.
- Do not search rank-biased overlap as though it were implemented. The measured selection statistic is top-3 overlap. Feature-selection stability literature is contextual, not evidence that its estimator was run.
- Omit broad explainability-disagreement discovery and the otherwise permitted practitioner-disagreement starter from the small query set: the measured comparison is estimator variation within a fixed Shapley game, not a cross-explainer practitioner study.
- Reject generic optimization, benchmarking, scientific-method, and paper-writing queries, as well as campaign chronology. They add citation volume without explaining these estimators, games, metrics, or data.

No paper text, bibliography, reference provenance, or claims-grounding file is generated here. Downstream retrieval must verify each candidate reference before citation; a query is not evidence that a paper was read.
