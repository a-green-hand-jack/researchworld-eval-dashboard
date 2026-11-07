# Post-primary comparator amendment

After the frozen main results were analyzed, add one stronger learned baseline family to reduce the 1PL-only comparison limitation. This is NOT a change to SCFD, its hyperparameters, primary endpoints, four contrasts, or existing outputs. All positive and negative main findings remain.

Baseline: regularized point-estimate multidimensional 2PL IRT, rank5 fixed in advance of its target evaluation, source parameters trained by L-BFGS on Bernoulli likelihood; standard-normal ability/discrimination priors and beta variance9. Infer target ability only on uniform query labels and aggregate observed plus imputed outcomes. A source-group-disjoint 80/20 inner calibration supplies a convex blend with uniform sample mean: lambda=validation_MAE²/(source_mean_row_variance/b+validation_MAE²). This is a source-calibrated gpIRT-inspired adaptation, not a faithful Bayesian tinyBenchmarks reproduction. Inner model never sees validation full rows during item fitting. No target-based rank/penalty/mixture selection.

Run all13 banks x2 primary regimes x5seeds x4budgets; keep results separately under artifacts/irt_runs. Gap panel optional not required for added baseline. If fitting fails or hits cap, record status; do not hide. Do not claim exact optimizer convergence if only approximate. Existing primary error intervals/p-values unchanged.
