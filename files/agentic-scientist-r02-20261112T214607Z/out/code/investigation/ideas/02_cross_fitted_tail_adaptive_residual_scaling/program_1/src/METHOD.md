# Cross-fitted tail-adaptive residual scaling

## Scope and interface

`program.py:handle` retains the starter's fit/predict/reset and bounded-transfer
protocol. Only supplied training covariates and training residual norms enter
learning. Fit still returns only `{"ok": true}`; predict still returns only the
encoded float64 `scales` array. Calibration, composition centers, geometry, and
region construction remain evaluator-owned. No extra observations are assumed.

## Prespecified learner

- The incumbent remains quadratic-feature ridge regression of log residual norm,
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
selection rule may favor an inferior efficiency tradeoff. Additive stumps miss
interactions; irrelevant features, small samples, finite threshold grids, and
tail sparsity can impair learning. Numerical clipping can limit adaptivity and
break otherwise irrelevant global-scale invariance. No improvement, runtime,
coverage, or uncertainty estimate for the harness metrics has been measured.

## Execution status

This stage permits source edits and static filesystem checks only. No candidate,
tests, benchmark, evaluator, package manager, network request, or exploratory
computation was executed. Positivity, batch-invariance, degeneracy, and protocol
tests remain unperformed; their expected behavior is supported only by source
reasoning, not test evidence. The official evaluation is harness-owned.

This is a candidate implementation, not a completed research paper. Repeated-run
experiments, numerical uncertainty quantification, literature review, an official
conference-template manuscript/PDF and checklist, measured dependency versions,
and measured resource use remain incomplete. No fabricated results, citations,
or paper claims are supplied. No prohibited literature was accessed.
