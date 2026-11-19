# Locked experimental protocol

Written 2026-11-02 before running prediction experiments. Data inspection and
reading the explicitly supplied literature preceded this document. This is a
local protocol, not a public preregistration.

Question: can source-informed residual strata reduce error without requiring
source-to-target predictive relationships to remain valid?

Data: all 13 binary LLM matrices named in the task, repository commit
55faff496947789f94e6b5908c77cbc3e84f81ad. Drop all-zero rows (as the upstream
reader does); retain the first of exactly identical response rows, to prevent
identical-profile train/test overlap. Preserve every column and its original
weight. No target responses are used in method fitting or hyperparameter
selection. A separate audit records raw/retained dimensions and hashes.

Splits: 70% source, 30% test; floor for source size. (1) random permutation;
(2) source bottom 70%, targets top 30%; (3) source top 70%, targets bottom 30%.
Tail splits use full scores ONLY to construct stress-test cohorts; they are not
a deployable selection rule or evidence about chronological transfer. Ties
broken by a seed-specific permutation. Seeds 0,...,9. Budgets 20,50,100,200;
the 200-item setting is a sensitivity analysis for shorter benchmarks.

Proposed residual stratification: p_i = source item mean; KMeans of vectors
(X_mi - p_i)_m, H=10, n_init=5, random_state=seed. Same strata across budgets.
Allocate at least two items per non-singleton stratum (one for singleton), then
greedily minimize estimated average-source variance, adding one item at a time
with largest N_h^2 * v_h/[n_h(n_h+1)], v_h = max(mean source within-stratum
sample variance of residuals, .05^2). Sample independently without replacement
within strata. Predict p-bar plus population-weighted sampled residual means.
Do not clip this unbiased estimate. Compute finite-population variance estimate
and normal 95% intervals; empirical coverage is a diagnostic, not a guarantee.

Baselines: source grand mean; uniform sample mean; uniform source-mean
difference estimator; source-to-score RidgeCV; published correlation medoids
and weighted averages (Anchor Points); ridge-on-items estimator using the
upstream AIPW implementation's formula; an explicitly unbiased two-fold
cross-fitted regression difference estimator; Rasch on uniform items; regularized
five-dimensional logistic IRT on uniform items and on latent-parameter KMeans
anchors (IRT-inspired implementations, not exact tinyBenchmarks reproduction).
RidgeCV alphas .1,1,10,100 chosen by five-fold source-only CV. Item ridge alpha
10 follows the allowed repository. IRT dimension 5, L2 penalty 1 for abilities
and loadings, .1 for difficulties, L-BFGS maxiter 1000; fixed, not tuned to targets.

Pre-main amendment after two-dataset smoke run: initial maxiter=200 hit its
limit on commonsense; maxiter=1000 converged in 259 iterations. Increase the
iteration ceiling on numerical-convergence grounds, not prediction accuracy.
Additionally include the AIPW paper's Eq. (3) as well as the fixed repository
formula; inspection of the explicitly permitted paper exposed their difference.
Pilot files remain separate and are not pooled with main results.

Ablations: source-difficulty quantile strata; raw-response strata with no
control variate; residual strata with proportional allocation. H=10 fixed.

Metrics: per-split MAE and RMSE (percentage points), signed bias, Spearman rho,
Kendall tau-b. Constant predicted scores give undefined rank correlation, never
substituted with zero. Each benchmark receives equal macro weight, averaging
seeds first. 95% paired percentile bootstrap resamples 13 benchmark blocks,
10,000 replicates, seed 20261102; it describes dataset heterogeneity, not an
independent sample of future benchmarks. Also report across-seed SD and
per-benchmark results. Primary comparison is k=100, residual strata versus
uniform difference, with both other budgets and negative results reported.

Diagnostics planned: (a) exact tiny-population enumeration checking unbiasedness
and the variance formula; (b) 200 additional item draws with seed-0 fixed splits
for design bias, variance, coverage, and interval widths; (c) source sizes 16,
32,64,128 where available, using random and upper-tail splits, five seeds,
k=100, no sources drawn from the held-out target cohort. Diagnostic (c) is
an ablation, not used to select the main method. No adaptively selected methods
or target-tuned hyperparameters will be presented as pre-specified.

Any implementation correction, failed run, omitted experiment, or departure
will be recorded in logs/RESEARCH_LOG.md. Comparisons describe these frozen
response matrices and do not measure fresh LLM inference cost.
