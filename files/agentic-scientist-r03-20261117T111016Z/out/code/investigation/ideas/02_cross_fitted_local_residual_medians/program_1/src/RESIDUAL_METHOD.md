# Cross-fitted local residual medians

## Scope and interface

`program.py:handle` remains the only public entrypoint. No operation, response
key, score unit, bound, or budget is added. The full-history ALS fit and its
random-number stream are unchanged. The covariance-gain selection code is
unchanged. Only predictions on unqueried columns may receive corrections;
queried-column predictions retain the incumbent's behavior. A zero blend returns
the incumbent prediction exactly. Reset clears all fitted and trajectory state;
begin clears the current observations. Caches contain historical quantities,
never new-model scores.

## Historical calibration

All calibration is inside `fit`, before any new-model observation. An independent
seeded RNG samples at most 512 historical rows, with a column-dependent cap
targeting roughly 196608 cells (and a 64-row floor). Up to 16 rows having at least
three observed scores are allocated to two validation folds. Each validation
fold is excluded from both its fitted predictor and every donor fit/pool.

Within each outer training pool, up to 128 historical donors are split into two
folds. Each donor fold is predicted by an ALS fit on the pool minus that entire
fold. Non-donor training rows may be used by both fits. Auxiliary fits use the
same ALS/ridge estimator but at most 12 sweeps; this resource approximation does
not change the incumbent fit. Small histories without enough validation support
return the unchanged incumbent.

For a queried column set, each donor's own available anchor scores condition its
cross-fitted predictor. A residual is its actual observed target score minus
that clipped conditional prediction. Missing target cells remain missing;
neither imputed targets nor the new model's predicted scores are donor labels.
Residual matrices are cached for up to eight queried sets per bank.

Distances are mean squared standardized differences on shared observed anchors.
Scales come only from each donor model's fitting rows, with a fixed 0.025 floor
in normalized score units. Gaussian-kernel weights are multiplied by the shared
anchor fraction; zero-overlap donors receive zero weight. Per target, only
finite observed residuals with positive weights enter the weighted median.
Effective count is squared total weight divided by squared-weight sum, using a
1e-12 numerical floor. The correction is median times
`blend * effective_count / (effective_count + shrinkage)`. Negligible total
weight leaves the base prediction unchanged. Final bounds remain [0, 1].

## Predeclared selection and comparisons

The grid is bandwidth `(0.35, 0.75, 1.5)`, shrinkage `(4, 16)`, and blend
`(0, 0.25, 0.5, 1)`. The incumbent selection policy is replayed on each held-out
historical row, with only its revealed scores available to prediction. Only
historically observed cells can be replayed as queries. Loss is pooled absolute
error on finite, unqueried targets at budgets 1, 2, 4, 8 where available; rows
with fewer observed cells cannot contribute every budget. All configurations
share fits, donor pools, query trajectories, and scored cells. Zero blend wins
ties, including differences within 1e-12. The chosen local configuration is then
used with a freshly cross-fitted donor bank from the entire sampled history.

Private diagnostic arrays also compare the unchanged base, unconditional
residual medians across the shrinkage/blend grid, and direct kernel-weighted
historical score medians across bandwidths. They record correction coverage and
effective counts on the same targets. These are training diagnostics, not an
unbiased outer evaluation, and are never included in RPC responses.

## Cost, limitations, and run status

There are at most eight auxiliary ALS fits beyond the unchanged full-history
fit: two outer predictors, four inner donor fits, and two final donor fits.
Final donor fits are skipped when zero blend wins. A bank has at most 128 rows;
conditional donor prediction is batched by anchor-observation pattern. Per-target
weighted medians sort the usable donors. All operations use NumPy on CPU.

Approximate auxiliary fits and history subsampling can mismatch the incumbent.
Sparse overlap, few held-out targets, nonrepresentative donors, extrapolation,
and multiple-configuration selection can all hurt transfer. No improvement or
conditional-median optimality for this residual-transfer estimator is guaranteed.
Only supplied history, opaque column indices, and actually revealed scores are
used; no identities, target masks, families, or evaluator metadata are assumed.

This implementation stage permits filesystem editing and static inspection only.
No candidate execution, tests, experiments, evaluation, literature search, or
paper compilation has been performed. No numerical research findings are
reported. Outer uncertainty estimates, budget/missingness experiments, crossover
ablations, a conference-format paper, and full scientific reproduction artifacts
remain incomplete; they are not fabricated or represented as completed work.
