# Saturation-aware scalar skill candidate

## Implementation status

This directory contains one prospective candidate, not a completed public-data
study or paper. No candidate code, numerical assertions, historical replay,
benchmark, or scientific control was executed during preparation. No measured
accuracy, confidence interval, runtime, acceptance, or hypothesis support is
claimed. No external literature or data was accessed. The harness owns the
subsequent official execution. `program_spec.toml` remains identical to the
starter, and `program.py:handle` remains the sole RPC entrypoint. Only NumPy and
the Python standard library are used; no dependency installation is required.

## Fit and replay

Observed-entry alternating ridge fits task intercepts and nonnegative scalar
skill loadings, with positive initialization and at most ten sweeps (six for
the inner fit, also bounded by the supplied allowance). Missing upload zeros
are never scores. Unsupported tasks default to 0.5; supported task means use
observed cells only. Skill coordinates are centered and scaled on nonempty
training rows. Their empirical distribution is interpolated onto at most 65
quantile grid points, with two padded endpoints and 0.5% prior smoothing.

Task-wise isotonic regression first pools exactly tied skills, then applies
weighted pool-adjacent-violators. A convex blend with the nonnegative-slope
linear curve has isotonic weight min(0.9, support/(support+50)), or zero with
fewer than three distinct skills. Isotonic interpolation uses constant
endpoint extension; the blended linear component is bounded to [0,1].
Residual variances are pooled-shrunk, floored, and for isotonic fits bounded
below by half of the corresponding linear residual variance. They are working
likelihood scales, NOT calibrated uncertainty. In-sample residual optimism is
not eliminated by these heuristics.

A seeded row-disjoint split holds out at most twelve eligible rows (six above
256 tasks), at most one fifth of eligible rows, while retaining at least three
training rows. Every inner intercept, skill, curve, variance and prior excludes
every held-out row. Replay chooses task means, linear skill, or monotone skill;
the latter two consider noise variance multipliers 0.75, 1.5, 3.0 and 9 or 17
bins. Checkpoints are feasible versions of budgets 1, 2, 4 and the supplied
maximum (zero when the maximum is zero). Cell MSE is averaged within a row,
then over checkpoints, then over rows. Only genuinely observed unpurchased
held-out cells are scored. Identical losses prefer the earlier, simpler
configuration. The winner is refit on all historical rows. Histories too small
to split use a declared linear fallback, or task means below three rows.
No seed identifies a workload and no unavailable family labels are invented.

This small validation split can select poorly and does not provide an external
performance estimate. Different adaptive trajectories can leave different
targets, so configuration replay alone cannot attribute gains to information
transfer. `research.py:fixed_panel_controls` supplies an optional *internal*
historical query/target-disjoint control. It compares adaptive, frozen-prior,
and random query choices with the same monotone predictor, and replays linear,
mean and nonlinear predictors on identical queries for each selector. Control
models exclude all replay rows. Target values never enter fitting or selection.
The control is not called by the RPC and has not been run. Its row bootstrap is
conditional on one training split, not a family-cluster or refitting interval.

## Posterior and selection

Each context owns an independent discrete skill posterior and observation
arrays. Gaussian continuous-score likelihood updates use shifted log weights;
predictions average the curve grid and preserve purchased values exactly.
Selection never updates a live posterior or consumes an unpurchased score.
New batches replace contexts; reset erases all learned and transient state.

For candidate a, score bins have infinite first/last endpoints. Their
conditional probabilities are Gaussian CDF differences. Let p_g be current
skill mass, L_gb the candidate's bin probability given skill g, and F_gt the
target response. Then

    P_b = sum_g p_g L_gb
    m_bt = sum_g p_g L_gb F_gt / P_b
    G(a; T) = mean_{t in T} sum_b P_b (m_bt - sum_g p_g F_gt)^2.

The actual selector evaluates this nonnegative finite-bin transfer gain on
all available unqueried targets except the candidate. Empty targets produce
zero gain and ties break by column index. Up to 24 candidates are all scored;
otherwise a scalar covariance-transfer approximation shortlists eight, then
the same exact finite-bin objective ranks those eight against all targets.
Shortlisting is an approximation to the maximization, not to the per-candidate
bin integral. The shortlist uses only the current posterior and fitted curves.
Working storage is O(MN + NG B); a selection costs O(NG + C B G N), where G<=65,
B<=17 and C<=24 (or eight above 24 candidates). This is a bound, not a measured
runtime. Training retains one inner fit and one final fit, not a model ensemble.

## Algebraic interpretation, not calibration

Under the conditional-independent scalar working model, for any *fixed*
target set T excluding a, the law of total variance gives

    mean_t Var(F_t(Z)|D)
      - E_b[mean_t Var(F_t(Z)|D, bin(Y_a)=b)] = G(a; T).

Independent target observation noise adds equal terms on both sides and
cancels from this reduction. A bin is a deterministic function of the
continuous Gaussian observation, so conditional expectation as an L2
projection implies G_bin <= G_continuous on the same model and target set.
Nested partition refinement cannot decrease this gain. Nine and seventeen
equally spaced bins are NOT nested, so no monotonicity claim is made about
that validation comparison. For affine responses F_t(Z)=alpha_t+beta_t Z,
the gain reduces exactly to mean_t beta_t^2 times
Var_b(E[Z|D,b]); a discrete empirical prior is not a Gaussian ridge posterior.

`research.py:verify_working_identities` contains unexecuted normalization,
nonnegative gain, total-variance, nested 9-to-18-bin refinement, affine
reduction, context isolation, queried-value, empty-target and PAVA assertions.
`verify_mask_and_degenerate_histories` contains unexecuted missing-value,
monotonicity, unsupported-task and constant-history assertions. These functions
have no import-time execution or RPC output. No assertion is reported passed.

Candidate-excluded target sets generally differ across candidates. The identity
holds for each such set individually; it does not prove optimal overall
selection or rule out changing-target-composition effects. Continuous
posterior updates do not make the finite-bin acquisition an exact continuous
integral. Finite support limits extrapolation; positive scalar skill cannot
represent multidimensional abilities, negative transfer, or arbitrary task
profiles. Missing-not-at-random coverage and related model rows can invalidate
generalization assumptions. Public-data experiments, actual MSE-versus-budget
curves, multi-seed and family-held-out studies, confidence intervals, source
verification, and the official-template paper remain uncompleted requirements
of a later authorized research stage, not outputs fabricated here.
