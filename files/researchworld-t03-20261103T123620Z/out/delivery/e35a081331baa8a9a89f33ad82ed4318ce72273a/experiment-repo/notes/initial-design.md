# Analysis commitment and pre-pilot design

Read on 2026-11-03: all five frozen files in `/initial-state/inputs/0/` and objective issue #1. The objective asks about repeated stochastic SHAP estimates of fixed tabular predictions under practical CPU budgets. German Credit and ACS Income are primary data. Main experiment details require story's settled plan and independent feasibility assessment.

## Estimand and controls

Fix a trained prediction function, output probability for a prespecified class, raw input features, explained input, and empirical background. Define the value of a coalition as the empirical mean prediction after replacing features outside the coalition by the same background rows. This is empirical interventional/marginal SHAP. Group each categorical raw feature across its encoding; do not sample incoherent one-hot columns. This target is not a causal attribution and does not resolve dependence-induced off-manifold combinations.

Compare at least permutation-path sampling and sampled Kernel SHAP. Record actual unique coalitions, model rows evaluated, and elapsed/CPU time rather than equating nominal library budgets. Exact enumeration for low-dimensional games tests correctness; larger games need independent references and a measured convergence bound/diagnostic. Main seeds must be disjoint from reference and pilot seeds.

Repeatability and reference accuracy are separate outcomes. Top-feature and top-k selection, sign stability on non-negligible features, normalized vector error, and tie-aware rank diagnostics need reference-gap/near-zero diagnostics. Reference top-k ambiguity is reported rather than interpreted as numerical failure. Adequacy thresholds are operational sensitivity choices, not externally established decision guarantees. Uncertainty resamples explained instances, not individual dependent feature/replicate pairs. Data splits, background draws and trained model stay fixed in the primary estimand; sensitivity strata should change backgrounds/models explicitly.

## Provenance and restrictions

Use only supplied starter literature and unrelated sources; do not search for or infer the withheld paper. No literature search has been made in this repository at this stage. Keep data URL, retrieval date, checksums and preprocessing record. Install versions and scripts accompany outputs. Model performance is diagnostic; attribution reliability is not proof of outcome fairness, clinical utility, causal correctness or model accuracy.

## Pending choices

Story-repo request #2 asks for the settled question/design and paper CODEOWNERS paths. Immediate work: acquire data, implement estimator and reference tests, time a pilot, then submit measured feasibility information before committing the main run scale. Approximately 24 CPU hours is the supplied planning estimate, not a measured allowance or result.
