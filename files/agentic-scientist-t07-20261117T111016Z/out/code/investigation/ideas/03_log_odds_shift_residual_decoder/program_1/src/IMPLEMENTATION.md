# Log-odds shift residual decoder

The unchanged score-targeted all-query ridge described below remains the
acquisition method and exact zero-nonlinear-weight fallback. The added decoder,
its nested validation, resource bounds and untested status are documented in
`DECODER.md`. `program.py` delegates fitting and prediction to
`nonlinear_decoder.py`; `surrogate.py` and `invariant_checks.py` are unchanged.

The starter's `handle(request)` operations, transport, upload bounds, response
keys and cumulative-observation protocol are preserved. Only source rows and
their supplied anonymous groups/weights train the method. No project code,
tests, evaluation, network requests or experiments were run in this editing
stage. There are no measured performance or improvement claims.

## Source model and nested acquisition

`surrogate.fit_score_model` normalizes weights in every fit, computes weighted
item means and source full-row means, then forms weighted centered responses
and their covariance with the full-row score. Full-row means retain all
original item columns and multiplicities. Canonical source-row ordering makes
arithmetic insensitive to permutations of the uploaded source rows/weights.

`select_score_path` greedily maximizes squared conditional score covariance
divided by regularized conditional item variance. A positive ridge enters both
selected covariance and candidate variance. Empty conditioning is explicit.
Each selected item masks its entire content group; exact ties use lowest item
index. The design is completed at fit time and never sees target answers.
Every select returns a cumulative prefix, including an empty prefix at zero.
Constant sources have zero gains and deterministic legal selections, without
switching algorithms based on control observations.

Only source-by-item responses, item-by-selected cross-covariances, and at most
25-by-25 selected covariance matrices are formed. Cross-covariance columns
are cached across ridge paths within each fold. There is no item-by-item
covariance or reconstruction of unobserved target answers. Fold models are
processed sequentially, and the final cross-column cache is released.

## Incumbent decoder and inner validation

`predict_score` uses all cumulative answers in direct regularized prediction of
the full score. The optional offset prediction is source score mean plus mean
difficulty-centered observed response. A source-selected convex blend is
clipped to [0,1]. Zero observations return the source prior before computing
an empty mean. An actual census returns its observed exact score. This is a
model-based estimator, not a design-unbiased audit estimator.

Source validation uses two disjoint held-out partitions of shuffled supplied
lineage IDs (alternating positions), together covering all supplied groups.
Each fold refits item means, score covariances, and the entire greedy path;
no validation row participates in its own design. For each setting, absolute
errors are averaged equally over declared prefixes, then within each lineage
using renormalized supplied weights, then equally over held-out lineages.
Prefixes are unique clipped values of {5,10,25} plus maximum budget; for maximum
budgets up to five they are clipped {2,5}. Neither actual target observations
nor target scores select prefixes, hyperparameters or items.

The deterministic setting list orders blend weights {1,0.5,0}, and within
each blend ridge strengths {0.05,0.01,0.2}. `cv_settings` caps the number of
settings from this list. `training_steps` caps complete selector designs,
reserving one for deployment and allowing two fold paths per distinct ridge;
fold statistics and paths are reused across blend weights. These allowances
are advisory in the RPC; this closed-form method has no optimizer iterations.
If allowances cannot support two fold paths, fewer than three source groups
exist, weights vanish in a required partition, or maximum budget is zero, the
fixed fallback is ridge 0.05 and blend 1 (pure score regression). Winning
settings and the final path are frozen at fit, including across later budgets.

## Executable safeguards and limitations

`invariant_checks.py` is imported by production code: selection checks enforce
content uniqueness and prefix extension; prediction checks enforce bounded,
finite outputs and identical-history equality. Predictions decode sorted unique
histories once and scatter back, so duplicate histories are exactly equal and
target-row permutations cannot change reduction order. Fits use
one BLAS thread and reset/close discard all episode state.

Anonymous supplied lineage groups are not complete ancestry metadata. The
protocol cannot implement per-target adaptive acquisition, request extra
labels, evaluate IRT/anchor baselines, or produce empirical paper tables in
this stage. Comparing those methods, uncertainty analysis, ablations and the
official-template research paper remain unperformed, not claimed completed.
No forbidden literature or external research materials were accessed.
