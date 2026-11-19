# Support-calibrated residual transport

## Scope

This candidate extends the supplied cross-fitted residual-median predictor,
documented in `RESIDUAL_METHOD.md`. Its full-history ALS fit, auxiliary fits,
history sampling, donor folds, RNG consumption, query policy, and original
bandwidth/shrinkage/blend selection are preserved. The public `handle` contract
and response fields are unchanged. No extra inputs or evaluator metadata are
used. The geometric gate is a hypothesis, not an established improvement.

## Target-specific geometric support

The existing profile computation now also returns mean squared standardized
distance over shared queried anchors. It divides the squared-distance sum by
overlap exactly once. Each donor uses scales from its own auxiliary fitting
rows. Kernel weights and overlap fractions are unchanged, and donors without
anchor overlap retain zero weight.

For each target, only positive-weight donors with finite observed target
residuals enter the weighted median of profile distances. This uses the same
target-specific weights as residual transfer. Unsupported targets retain the
incumbent output. Supported, unqueried targets receive

    base + exp(-penalty * support_distance) * (incumbent - base)

Both endpoints are clipped before interpolation; the result is clipped to
`[0, 1]`. Queried columns are not modified. Zero penalty returns the incumbent
array immediately and unchanged. The executable mechanism is implemented in
`_profile_weights`, `_target_support_distances`, `_apply_support_gate`, and
`_apply_residual_correction`, not in uncalled demonstration snippets.

## Historical tuning

Penalties are fixed at `(0, 0.25, 1, 4)`. The existing row-disjoint replay
accumulates losses for every original residual configuration and every penalty
on identical observed, unqueried targets at the original query prefixes.
Distance medians are computed once per bandwidth and replay prefix, not once
per residual configuration. The cache contains only error sums with axes
bandwidth, shrinkage, blend, penalty, and historical validation row. It never
allocates a donor-by-target-by-configuration tensor.

The original residual configuration is selected with the unchanged incumbent
losses and tie handling. Only afterward is the penalty selected for that frozen
configuration. Errors across prefixes and targets are aggregated within each
historical row. A nonzero penalty must reduce pooled cell MAE by more than the
existing numerical tie tolerance and have negative mean paired row-MAE change
plus one paired standard error. The best eligible pooled MAE wins; ties within
the numerical tolerance fall back to zero, including ties between nonzero
penalties. With fewer than four eligible rows or no qualifying improvement,
zero wins. Equal-to-incumbent losses always retain zero. This is conservative
historical tuning, not a confidence guarantee,
an unbiased evaluation, or a correction for multiple comparisons.

Calibration arrays and the chosen penalty remain private. Prediction does not
write the donor cache: conditional residuals are recomputed from immutable
historical scores for each queried set. Historical replay retains the existing
eight-entry cache. New-model observations remain trajectory-local and are
cleared by `begin`; `reset` clears all state. No additional ALS fits, RNG draws,
dependencies, response fields, or external files are introduced by prediction.

## Validation status and limitations

This stage permits filesystem edits and static inspection only. No candidate,
tests, verification snippets, experiments, or evaluation were executed; no
network or literature search was performed. Source inspection is not runtime
validation. The harness owns the subsequent official evaluation.

No performance improvement is claimed. Calibration can select zero. A distance
gate can suppress useful corrections, cannot fix biased donor availability,
and does not guarantee robustness to model-family shifts. Sparse overlap and
the approximate auxiliary fits remain limitations of the inherited predictor.
Matched outer comparisons against the exact incumbent, ALS-only predictions,
and fixed gates; budget-specific errors and paired uncertainty; and analyses
by support distance and effective donor count remain unperformed. A completed
conference paper, compiled PDF, and full empirical reproduction deliverables
also remain outstanding and are not represented by this candidate note.
