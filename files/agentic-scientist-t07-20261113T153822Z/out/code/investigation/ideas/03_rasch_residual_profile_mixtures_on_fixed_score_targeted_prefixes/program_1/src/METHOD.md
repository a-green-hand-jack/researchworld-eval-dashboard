# Candidate method and evidence status

This candidate implements `cycle_03_rasch_residual_profile_mixture`. Only the
documented RPC supplies data. No target identities, groups, scores, filesystem
data, or additional observations are assumed. `program_spec.toml` and the
response keys/types are unchanged. All learned state is cleared by reset or
release. Predictions are reconstructed from the original source prior and the
entire current prefix; no target likelihood is accumulated between requests.

## Fixed source-only question design

The permitted starter contains a diversity/PCA selector, not the previous
cycle's score-targeted selector. Consequently this implementation uses the
idea's documented fallback, rather than claiming exact reuse of unavailable
code. It greedily maximizes squared conditional covariance with the source full
score, divided by conditional item variance. Source covariance uses equal total
weight per supplied opaque group. The diagonal observation nugget is
`0.1 * max(item_mean * (1-item_mean), 0.05)`. A low-rank pivoted factorization
avoids an item-by-item covariance matrix. This produces one unique nested order
shared by the linear and particle estimators, not a target-adaptive policy.

The linear control retains the starter's unweighted ridge regression with an
intercept and shrinkage toward the fit rows' mean score. Strengths are
`(0.1, 1, 10)` and shrinkages `(0, 0.5, 1)`. Unlike the starter's validation,
question selection is rebuilt in each training fold and shrinkage uses that
fold's training mean, never a full-source mean including validation rows.
Per-budget hyperparameters minimize equal-group held-out squared error, with
bounded predictions. These necessary validation changes mean this is a matched
control within this candidate, not an exact previous-cycle reconstruction.

## Particles and source-only tuning

Smoothed source row means give logit abilities. Eight damped Newton iterations
fit item difficulties with group-weighted Bernoulli likelihood and difficulty
ridge `0.01`. Abilities stay fixed. With the documented maximum item count,
smoothed abilities and damped difficulties remain far inside float64 exponential
overflow limits. Profiles interpolate source correctness with fitted Rasch
probabilities and are clipped to `[1e-6, 1-1e-6]`. Each source contributes five
particles with offsets `offset_scale * (-2,-1,0,1,2)` and prior proportional to
`(1,4,6,4,1)`. Total prior mass is identical across source groups and divided
equally among rows in each group. Flattening is source-major, offset-minor.

The prespecified small grid is residual weight `(0,0.5,0.75)`, offset scale
`(0,0.5)`, and mixture weight `(0,0.5,1)`. The zero residual and zero offset
candidates give matched-prefix Rasch and no-offset controls during tuning.
The zero mixture candidate is the explicit linear fallback. The convex blend
has no extra affine calibration. Ties within `1e-12` prefer lower mixture
weight, then lower offset scale, then lower residual weight.

At most three seeded group-disjoint folds rebuild selection, Rasch fitting,
profiles, and priors. The same folds select the linear hyperparameters and
the single blend configuration across all requested budgets. Blend loss is
mean absolute error averaged over budgets, then over rows in each group, then
equally over groups. This is tuning, not an independent performance estimate.
With only one source group, tuning is unavailable: use fixed ridge strength 1,
shrinkage 1, and the zero-mixture fallback without constructing pseudo-holdouts.

For tuning, chunked particle totals and selected-item probabilities suffice;
the final selected mixture stores particle-by-item probabilities. Posterior
normalization uses logsumexp. Full-score estimates add the exact observed
correct-answer total to expected unqueried totals. The batch path uses
precomputed full totals minus queried totals, algebraically equivalent to the
explicit remaining-item sum in the single-row path. Observed responses never
update source fitting, selection, hyperparameters, or a persistent posterior.

## RPC controls and limitations

`no_diversity` substitutes a seeded uniform nested order in every fitting fold
and in the final fit. `no_calibration` retains the primary question order but
returns the raw observed mean, as documented by the starter. No additional
RPC modes or diagnostic response fields were invented. A separately evaluated
row-uniform-prior ablation, a standalone strong IRT baseline, independent outer
group validation, ranking statistics, and paired group uncertainty are not
reported or claimed completed. The tuning alternatives are not independent
ablation evidence. No target validation data are available to this candidate.

No code was executed, imported, compiled, benchmarked, or tested during this
stage. Replay, boundedness, normalization, uniqueness, and group-isolation
assertions are in the implementation but have not been experimentally verified.
Runtime under the harness RPC limits is unmeasured. The harness owns the only
official evaluation. There are no new empirical results, literature claims,
paper PDF, or completed scientific conclusions. Posterior spread is not a
calibrated uncertainty interval; conditional independence, limited global
ability offsets, and source-group representativeness remain substantive risks.
