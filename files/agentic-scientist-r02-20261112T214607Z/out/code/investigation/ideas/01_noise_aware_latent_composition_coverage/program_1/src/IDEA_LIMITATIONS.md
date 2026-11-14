# Noise-aware latent composition coverage: interface assessment

Attempt: `c01_noise_aware_latent_composition_bridge_attempt_01`

Idea: `c01_noise_aware_latent_composition_bridge`

Candidate: `program_1`

## Implemented scope

This candidate preserves the starter's numerical scale estimator, RPC responses,
array representation, and transfer/state protocol. The source docstring records
the incompatibility below. The proposed noise enlargement and research audit are
**not implemented**. No unused bridge helpers, fabricated observations, additional
RPC operations, or extra response fields are introduced.

## Why the proposed method cannot be expressed

Fit supplies six-dimensional training covariates, scalar training residual norms,
the composition dimension, and scale bounds. Prediction receives only covariates.
The reset seed does not identify a workload. The candidate controls positive
scalar scales, not centers, geometry, or calibration.

| Proposed component | Missing interface capability |
| --- | --- |
| Corrected conformal order statistic | Calibration scores, sample size, miscoverage level, and control of calibration |
| Multinomial noise radius | Announced integer count depth and a stated multinomial observation model |
| Additive enlargement of an L1 radius | Compatible geometry, calibrated radius, and region-construction control |
| Observed-versus-latent coverage audit | Observed compositions, latent vectors, prediction centers, and test outcomes |
| Exact score-atom experiment | Controlled count generation, centers, and independent calibration repetitions |
| Paired seed-level bootstrap | Actual repeated experimental outcomes for both targets |

The dimension alone cannot identify a multinomial noise radius. No meaning for
individual covariate columns is documented, so none is interpreted as depth, a
latent target, or a noise parameter. Residual norms do not identify the sampling
model or separate observation noise from prediction error.

An output scale cannot generally encode an additive radius enlargement without
the unknown calibrated radius and compatible geometry. Changing training scales
is therefore not claimed to implement the bridge. Generating separate synthetic
data inside the learner would neither supply the missing workload observations
nor validate latent coverage for this interface.

## Conditional mathematical proposal, not an experimental result

If an interface explicitly supplies compositions Y=C/M under conditional
multinomial sampling, known depth M, and L1 regions, the proposed argument is:

    ||Y-p||_1 = 2 max_A sum_{j in A}(Y_j-p_j).

One-sided Hoeffding bounds over the 2^D-2 nonempty proper subsets give

    P(||Y-p||_1 > epsilon) <= (2^D-2) exp(-M epsilon^2/2).

For 0 < delta < alpha < 1, the proposed noise radius is

    epsilon = min(2, sqrt(2 log((2^D-2)/delta)/M)).

Under joint exchangeability conditional on an independently trained center,
observed-target calibration at miscoverage alpha-delta gives L1 radius q. The
corrected calibration rank is ceil((n_cal+1)(1-alpha+delta)); a rank beyond n_cal
requires an infinite radius. Inclusive comparisons retain ties. The triangle
inequality and union bound then yield marginal latent coverage at least 1-alpha
for radius min(2,q+epsilon). Clipping at two uses the simplex's L1 diameter.
Independence of the error events is unnecessary; covariate-conditional coverage
does not follow.

For the proposed two-component boundary-center counterexample, the zero-score
atom has probability (1-epsilon_rare)^M. A zero calibration quantile requires at
least ceil((n_cal+1)(1-alpha)) zero calibration scores. Its probability is a
binomial upper tail when that rank is feasible, and zero otherwise. With interior
center (a,1-a), where 0<a<1/(2M), the unique lowest-score atom instead has score
2a and the same probability. If epsilon_rare>2a, its radius excludes the latent
vector. These are analytical observations, not measured frequencies.

These arguments do not justify use with unknown depths, overdispersed counts,
arbitrary softmax outputs, covariate shift, or latent probabilities reconstructed
from single categorical labels. They have not been implemented or empirically
checked in this candidate.

## Execution and evidence status

Only permitted filesystem inspection, copying, source/documentation editing,
and append-only memory updates were performed. No candidate code, tests,
experiments, evaluation, package installation, or network access was executed.
No literature was accessed and no forbidden material was encountered. There are
no measured coverage results, uncertainty intervals, performance improvements,
paper/PDF, or completed experimental claims from this attempt. The proposed
experimental grid remains unexecuted.

The `apply_patch` command was unavailable; the initial patch attempt did not
modify source files. Plain filesystem editing was used instead.

`program_spec.toml` and the numerical learner remain unchanged. The existing
`program.py` entrypoint continues to implement `python_rpc_v1:handle`. Only the
harness's later official evaluation can establish candidate performance.
