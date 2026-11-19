# Finite-N nonlinear score controls: candidate implementation

This is an implementation note, not an evaluated paper. This stage prohibits
execution, simulation, data download, package installation, literature retrieval,
and evaluator inspection. No measured coverage, width, runtime, benchmark score,
oracle checks, real-data comparisons, or publication deliverables are claimed.
Only the supplied task description and starter candidate were consulted.

## Interface and target

The target is the population mean theta = E[Y]. The request contains labeled
pairs (Y_i, S_i), unlabeled scores T_j, sample sizes n and N, alpha, and the
declared outcome kind. The predictor that produced S and T remains unchanged.
A fitted score-to-control map is an auxiliary nuisance, not a retrained predictor.
There are no inputs for oracle probabilities, evaluator truth, sampling indices,
or reference intervals. The implementation does not invent these inputs.

The statistical model is independent iid labeled and unlabeled samples from the
same population, with an externally frozen predictor. Within a replicate, every
method would have to use the same realized inputs. Coverage is over repeated
samples, not a probability conditional on an unchanged realized data set. These
assumptions cannot be checked from the interface. Shifted unlabeled populations,
informatively selected labels, and predictor training on the supplied labels
are outside the justification.

The complete reset/start/chunk/commit/infer protocol, validation, transfer token,
and response fields are preserved. In particular, commit returns only `ok` and
infer returns only finite ordered `lower` and `upper` endpoints. Internal
`certificate` state is neither returned nor used to select the reported interval.
Reset clears all fits, diagnostics and random state. No cross-episode learning
or seed-dependent workload recognition is performed.

## Fixed-control algebra and saturation

For a deterministic score control h, consider

    theta_hat(h) = mean_i[Y_i - h(S_i)] + mean_j[h(T_j)].
    V(h) = Var(Y-h(S))/n + Var(h(S))/N.

Write m(S) = E[Y | S], a = N/(n+N), and e = E[Var(Y | S)]. Up to additive
constants in h, completing the square gives

    V(h) = e/n + Var(m)/(n+N)
           + (1/n + 1/N) Var(h - a*m).

Thus the fixed-control oracle is h* = a*m, with

    V* = e/n + Var(m)/(n+N).

For nonconstant scores with finite positive variance, the unrestricted affine
oracle coefficient is a*Cov(Y,S)/Var(S). Its variance and nonlinear headroom are

    V_linear = Var(Y)/n - N*Cov(Y,S)^2 / [n*(n+N)*Var(S)],
    V_linear - V* = N/[n*(n+N)]
                    * {Var(m) - Cov(Y,S)^2/Var(S)} >= 0.

For constant scores the projection variance is defined as zero; m is then
constant too. The gap is zero for affine m, for uninformative conditional means,
and for any score with at most two support values. On a two-point support every
function is affine, even when its two values are poorly calibrated. This is an
oracle variance identity, not a statement that an estimated interval always
shrinks. It also separates genuine nonlinear gains from scalar coefficient
constraints: comparison to a scalar coefficient constrained to [0,1] would not
isolate nonlinear headroom if its unconstrained optimum lies outside that range.

A score-only semiparametric efficiency interpretation additionally requires
regular asymptotically linear inference in this iid two-sample model. No
finite-sample lower bound over arbitrary confidence intervals is asserted.
The implementation does not estimate or claim knowledge of true oracle
components from fitted calibrators. Analytical oracle checks and synthetic
experiments were not run in this restricted stage.

## Actual inference path

`program.py::_fit` calls `_crossfit_controls`. It partitions a reset-seeded,
outcome-independent random permutation into five held-out folds (four at the
minimum supported n=8, ensuring two observations per held-out mean).
For every fold, training and held-out indices are explicitly checked disjoint.
Only the other folds' scores and outcomes enter `ScoreCalibrator.fit`.

The small basis consists of a linear term, a quadratic term, and positive-part
linear spline terms at normalized score knots -0.5, 0 and 0.5. Score scale,
10th/90th percentile normalization, feature centering and standardization are
estimated from that training fold only. A degenerate quantile span falls back
to the training score range. Features are clipped to the training amplitude
and normalized coordinate range [-3,3] for numerical stability. The intercept
is unpenalized; the prespecified standardized ridge penalties are
(0.1, 2, 4, 4, 4). There is no tuning against evaluator outputs or held-out
labels. Binary calibration predictions are clipped to [0,1]. Real-outcome
predictions use the same basis without outcome clipping.

Let g_k denote the fitted calibration and w_k = n_k/n. The implementation uses

    R_i = Y_i - a*g_k(S_i), for i in held-out fold k,
    H_j = sum_k w_k*a*g_k(T_j),
    estimate = mean(R) + mean(H),
    variance = sample_var(R)/n + sample_var(H)/N.

The unlabeled control is averaged across folds BEFORE its sample variance is
computed. The same unlabeled pool is reused, not treated as independent pools.
The returned interval uses a Student-t critical value with max(2,n-6) degrees
of freedom, a finite-sample heuristic for the asymptotic Wald construction,
not an exact pivot. Binary endpoints are monotonically clipped to [0,1].

As in the starter, constant scores in either supplied pool trigger a label-only
response. Binary data with fewer than ten observed successes or failures also
use the label-only response. That response is Clopper-Pearson for binary data
and Student-t for real data. The latter is exact under iid Gaussian outcomes,
not arbitrary real distributions. The binary Clopper-Pearson interval alone
has a finite-sample guarantee; selecting it on the observed event count and
otherwise returning a Wald interval does NOT make the overall rule exact.

The cross-fit variance requires, for example, fixed fold count, n,N tending to
infinity with N/n tending to a positive finite constant, a common deterministic
L2 limit for the fitted controls, suitable finite moments, and nondegenerate
limiting variance. Training is independent of its held-out fold and of the
unlabeled observations. Orthogonality of the difference of score means then
makes consistent nuisance error first-order negligible. Cross-fit residuals
are not unconditionally independent: the argument is asymptotic, not an
exact conditional variance calculation. The fixed small basis need not converge
to m, so oracle efficiency is NOT claimed for arbitrary nonlinear m. Quantile
and degenerate-support edge cases also need validation; no blanket convergence
theorem for this particular fitting rule is claimed.

## Separate bounded-fold certificate

For binary outcomes, the code computes an internal certificate on EVERY input,
including rare-outcome and constant-score cases, before choosing the returned
interval. It is therefore a standalone algorithm, not a bound selected only
after observing that a fallback gate passed. This computation consumes no
additional observations and never changes the reported Wald/fallback interval.

For each fold, conditional on its training observations, the held-out residuals
are iid in [-a,1] and the unlabeled controls are iid in [0,a]. Both have at
least two observations. For each of these 2K mean bounds use delta=alpha/(2K)
and the two-sided empirical-Bernstein radius

    b(v,L,U,delta) = sqrt(2*sample_var(v)*log(4/delta)/len(v))
                     + 7*(U-L)*log(4/delta)/(3*(len(v)-1)).

The radius can be truncated at U-L, since no two means in that range differ
by more than U-L. Every fold's population residual mean plus population
control mean equals theta, regardless of how inaccurate its fitted g_k is.
Weighting the two radii and centers by w_k and applying a union bound yields
a 1-alpha certificate. Dependence across folds and repeated use of the
unlabeled pool do not invalidate a union bound. Normalization and calibration
must remain training-only for this conditional argument; no global unlabeled
quantiles or full-label model selection are used here.

This is a mathematical justification under the stated iid bounded model,
not empirical verification. Tail allocation and small held-out folds can make
the certificate much wider, even the full [0,1] interval. It is not substituted
after observing a narrow or suspicious Wald interval. The RPC cannot return
two intervals or separate diagnostic lanes, so certificate comparisons would
require a separately permitted experiment stage, not extra response keys.

## Unperformed work and reproducibility boundary

All changes are source edits; no candidate, project code, tests, simulations,
package managers or evaluators were executed. No additional dependency was
introduced: the existing NumPy and SciPy imports suffice. The manifest and
entrypoint remain unchanged. The harness owns the next execution.

The supplied idea's synthetic grid, oracle diagnostics, affine ablation,
fixed-bin stratified comparisons, pinned-package PPI++ checks, real-table
sampling, saved paired trials, Wilson coverage intervals, paired-bootstrap
width uncertainty, and saturation experiments were NOT performed. The RPC
does not provide empirical-population labels or oracle conditional means;
they must not be reconstructed from seeds or presumed evaluator inputs.
No unused experiment stubs or fabricated artifacts stand in for that work.

There is no full paper, PDF, conference template or checklist in this candidate.
Producing them honestly requires literature access and actual repeated-run
evidence, both prohibited in this stage. This file reports only implemented
mechanisms, theoretical assumptions, and limitations. In particular, no
numerical improvement over the incumbent or nominal empirical coverage is
asserted. Evaluating rare events, score interventions, heavy tails, calibration
error, small samples and no-headroom regimes remains necessary.
