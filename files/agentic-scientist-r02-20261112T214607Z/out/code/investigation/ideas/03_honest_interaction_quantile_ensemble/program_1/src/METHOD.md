# Honest interaction quantile ensemble with a complete-incumbent fallback

## Scope and interface

`program.py:handle` retains the starter's fit/predict/reset and bounded-transfer
protocol. Only supplied training covariates and training residual norms enter
learning. Fit still returns only `{"ok": true}`; predict still returns only the
encoded float64 `scales` array. Calibration, composition centers, geometry, and
region construction remain evaluator-owned. No extra observations are assumed.

## Honest interaction extension

The hypothesis is that shallow interactions can explain log-residual tails that
the complete ridge/additive-stump incumbent misses. This is a conditional
hypothesis, not a claim of improvement. All targets are
`log(max(residual_norm, 1e-12))`; the fixed working quantile is 0.9, not a
requested conformal coverage level.

The new outer selection uses the same deterministic three-fold partition rule
as the incumbent. In each fitting fold it refits the **complete** incumbent
described below, including that incumbent's own three-fold selection and all
preprocessing. Outer validation observations never enter these inner fits.
The complete incumbent is candidate zero, not just its ridge component. It
retains its existing alignment and prediction bounds without another offset.
Candidate one is the fitting-fold empirical 0.9 log-norm quantile.

For each depth in (1, 2), an ensemble fits 16 trees. Tree index `j` uses
`np.random.default_rng(4103 + j)` to permute its fitting observations, with the
first floor(n/2) reserved for structure and all remaining observations reserved
for estimation. These partitions are disjoint and exhaustive, with live
assertions in the fitting path. Depth-one and depth-two ensembles use identical
partitions to provide a training-only interaction ablation. No reset seed or
evaluation feedback selects the partitions or learning settings.

Each structure node considers up to 16 empirical feature quantile thresholds
at equally spaced levels from 0.05 to 0.95, using structure covariates only.
Splits maximize the reduction in summed empirical pinball loss evaluated at
the two structure-leaf log-norm quantiles. The split must improve loss beyond
`1e-12 * max(1, parent_loss)`. Every structure leaf requires at least
`max(16, ceil(0.05 * structure_root_size))` observations. Recursive growth stops
at the specified depth, with two levels of splitting for the interaction model.
Constant covariates and constant responses yield unsplit trees. Quantiles are
NumPy's default linearly interpolated empirical quantiles, computed from sorted
response membership counts for split search.

After topology is frozen, node estimates use estimation observations only.
Nodes with at least 16 such observations receive their empirical log-norm
quantile. Smaller nodes, including empty leaves, inherit the nearest supported
ancestor estimate, ultimately the estimation-root quantile. Structure responses
are not used for node estimates. If any outer fitting fold would have fewer
than 16 estimation-root observations, the extension is bypassed and the
complete incumbent is refitted directly. The forest also guards its own root
support. Averaging tree log predictions is regularization, **not** an identity
for a mixture-distribution quantile.

The eight outer candidates, in fixed incumbent-first simplicity order, are:
complete incumbent, constant, then depth-one blends at weights 0.25, 0.5, 1.0,
then depth-two blends at those weights. Each weight multiplies the forest log
prediction; the remainder multiplies the complete-incumbent log prediction.
Each forest blend receives a separate additive offset equal to the fitting-only
0.9 quantile of target minus fitted blend. No validation outcome enters an
offset, tree, threshold, or inner incumbent choice.

Outer selection compares unweighted means of the three held-out mean pinball
losses. It chooses the first candidate within one sample standard error of the
lowest mean loss. The standard error uses the three fold losses with ddof=1
and division by sqrt(3). Both inner and outer one-standard-error conventions
are regularization heuristics, **not** confidence intervals or guarantees:
their fitting folds overlap. The complete incumbent and the selected forest
depth, if needed, are then refitted on all supplied training data, and the
selected blend is aligned using those training data only. Internal fold losses
remain model state and are never added to RPC responses.

Selecting the incumbent returns its original positive scales unchanged. Other
selected log scales are bounded to [-30, 30] and exponentiated. Prediction
asserts finiteness and positivity, is read-only, and uses no query-batch
statistics. No query/training pairwise matrix is constructed. The implementation
uses only the existing NumPy and standard-library dependencies.

## Preserved complete incumbent

- The inner base learner remains quadratic-feature ridge regression of log residual norm,
  with fold-local centering, standardization, the original ridge penalties, and
  original log-prediction bounds. Its original residual floor is retained.
- The tail learner targets the 0.9 quantile of
  `log(max(residual_norm, 1e-12))`. This is a surrogate learning target, not an
  assumed conformal miscoverage level.
- Each stump uses training-only thresholds at 15 equally spaced quantile levels
  from 0.05 to 0.95 for each supplied feature. Both leaves require at least
  `max(20, ceil(0.03 * fitting_sample_size))` observations. Updates are within-leaf
  empirical residual quantiles. The learning rate is 0.1; at most 80 rounds are
  fitted, stopping when no candidate reduces training pinball loss beyond a
  numerical tolerance. Constant features and undersized folds yield an
  intercept-only tail predictor. Repeated residual values are allowed.
- To avoid repeatedly sorting every leaf, each round sorts working residuals
  once. Cumulative membership counts recover interpolated leaf quantiles; exact
  pinball losses of the shrunken updates choose the split. The selected leaf
  updates are then recomputed with NumPy's empirical quantile operation.
- Three deterministic folds use `np.random.default_rng(0).permutation(n)` and
  `np.array_split`. Each fold fits its own incumbent preprocessing, tail
  thresholds, and quantile alignment offsets using only fitting observations.
- Six candidates, in fixed simplicity order, are incumbent, constant, and
  log-space incumbent/tail blends with tail weights 0.25, 0.5, 0.75, and 1.0.
  Every candidate receives a fitting-only additive log offset equal to the
  empirical 0.9 quantile of target minus fitted log scale. Aligning a blend this
  way is unchanged by first applying constant offsets to its component models.
- Candidate losses are mean validation pinball losses within each fold. Their
  unweighted fold means are compared; the standard error is the sample standard
  deviation across the three fold losses divided by sqrt(3). The first candidate
  within one standard error of the lowest mean loss is selected. This is a
  regularization heuristic, not a significance test or a confidence interval:
  fitting folds overlap. For fewer than three training observations the
  incumbent is used without cross-validation. Empty training arrays are rejected.
- Models and offsets are refitted using all training observations. Prediction is
  read-only and does not depend on query-batch statistics. Selected log scales
  are bounded to [-30, 30] before exponentiation, with a positive numerical floor.
  The documented evaluator additionally clips scales to [0.0001, 10000].

No aggregate evaluation feedback enters any choice. Reset seeds retain their
protocol meaning and do not select workloads or hyperparameters. Selection
statistics are internal and are not added to RPC responses.

## Validity argument and limitations

Condition on the training data and all fitting choices. The learned scale is
then a fixed strictly positive function. If calibration and test observations
are exchangeable conditional on those choices, and use the same evaluator-owned
center, geometry, and numerical scale clipping, their normalized residual scores
are exchangeable. For m calibration scores and k = ceil((m+1)(1-alpha)), the usual
split-conformal threshold at rank k (infinity if k > m) gives marginal coverage
at least 1-alpha, with ties conservative. Training-only selection does not change
this rank argument. It does not imply conditional/group coverage, nor validity
under distribution shift or calibration reuse. The argument presumes the
evaluator actually uses this split-conformal construction; the candidate does
not inspect or alter it.

Pinball loss on log norms is not simplex volume or the harness objective. The
selection rule may favor an inferior efficiency tradeoff. The shallow forest
only addresses interactions exposed by greedy positive-gain splits; pure
interactions with no useful first split can still be missed. Irrelevant features,
small samples, finite threshold grids, tail sparsity, and splitting the training
sample for honesty can impair learning. Depth two is not proof of an interaction
benefit, and an incumbent fallback is not evidence of improvement. Honesty here
means within-training structure/estimation separation, not distribution-free
conditional coverage. Numerical clipping can limit adaptivity and
break otherwise irrelevant global-scale invariance. No improvement, runtime,
coverage, or uncertainty estimate for the harness metrics has been measured.

## Execution status

This stage permits source edits and static filesystem checks only. No candidate,
tests, benchmark, evaluator, package manager, network request, or exploratory
computation was executed. Deterministic-fit, supported-ancestor fallback,
constant/no-signal, positivity, batch-invariance, and protocol tests remain
unperformed; their expected behavior is supported only by source reasoning,
not test evidence. Live fitting paths enforce disjoint halves, root support,
and finite positive predictions, but these checks have not yet been executed.
The official evaluation is harness-owned. Even a favorable single aggregate
evaluation cannot establish interaction causality or general superiority;
independent paired-seed experiments and no-interaction controls remain needed.

This is a candidate implementation, not a completed research paper. Repeated-run
experiments, numerical uncertainty quantification, literature review, an official
conference-template manuscript/PDF and checklist, measured dependency versions,
and measured resource use remain incomplete. No fabricated results, citations,
or paper claims are supplied. No prohibited literature was accessed.
