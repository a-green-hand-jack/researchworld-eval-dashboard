# Smooth covariance stacking of frozen-score controls

## Status and boundaries

This is one source-only candidate, not an evaluated paper. No candidate code,
tests, simulations, package managers, network requests or evaluator were run.
No measured coverage, width, score improvement or runtime is claimed. Only the
permitted starter implementation, method note, manifest and supplied task were
read; there was no external literature browsing or prohibited-content encounter.
The requested paper/PDF, latest official conference template/checklist, real-data
study and repeated-run evidence remain unfinished under this stage's boundaries.

## Target and interface

The target is mu=E[Y], the superpopulation outcome mean. The documented RPC
provides y[n], labeled frozen scalar predictions p[n], independent unlabeled
frozen predictions u[N], alpha and label kind. There are no X, strata, oracle
means, extra labels, predictor updates or cross-episode learning. Assume iid
labeled pairs and an independent iid unlabeled pool from the same population,
with an externally frozen predictor. Informative label sampling, distribution
shift and training the predictor on these labels are outside the justification.
Coverage concerns repeated sampling; keeping each realized input identical
across methods is not a conditional-on-all-data coverage guarantee.

The manifest, entrypoint and reset/start/chunk/commit/infer protocol are unchanged.
Only infer returns lower/upper floats; update responses have no diagnostics.
Reset clears the complete state and RNG. Only training labels and scores enter
calibrator fitting, moment estimation, scaling and weight estimation. The full
n/N ratio is used as supplied, without consulting unlabeled score values.

## Live learner

The outer split and studentizer are inherited unchanged. There are
K=min(5,floor(n/2)) label-disjoint held-out folds. Inside each outer training
sample of size m, `_fit_stacked_control` makes three inner splits (the supported
minimum outer training size is six). Both bases use identical fitting and
validation indices:

- Unscaled `AffineCalibrator`: training-normalized score least squares.
- Unscaled `ScoreCalibrator`: the inherited small spline/ridge basis, quantile
  normalization, clipped features and fixed basis penalties.

For Bernoulli outcomes each base prediction is clipped to [0,1] exactly as in
the starter. Neither base passes through `_fit_control`, which would apply a
separate scalar finite-N multiplier. That legacy helper and `_select_control`
remain available for source compatibility/comparison but are not called by the
live learner. Only inner validation labels enter the weight moments; no outer
held-out labels enter either the calibrators or those moments.

For inner validation fold j, form a two-column base prediction matrix Q_j,
with v_j rows. `_stack_moments` computes

    G_hat = sum_j (v_j/m) sample_cov(Q_j),
    c_hat = sum_j (v_j/m) sample_cov(Q_j,Y_j).

These are within-fold centered covariances with sample divisor v_j-1, weighted
by validation size (not pooled uncentered out-of-fold predictions). Subtracting
each column's first value before covariance calculation additionally makes
exactly constant columns numerically zero. Distinct additive intercept offsets
in each validation fold and each base leave the mathematical moments unchanged.
This is an algebraic property, not a guarantee against floating-point loss for
arbitrarily large offsets.

With r=n/N, the prespecified rule is

    variance_floor = 1e-12 trace(G_hat),
    D = (2/m) diag(max(diag(G_hat), variance_floor)),
    w = solve((1+r) G_hat + D, c_hat).

Zero covariance scale, nonfinite moments/weights or a failed solve return zero.
The relative floor and ridge coefficient are fixed design choices, not fitted
to evaluation outcomes. Both unscaled bases are then refitted on all outer
training records. The control is g(p)=w[0]q_affine(p)+w[1]q_nonlinear(p), with
no additional finite-N shrinkage and no clipping of the signed combined output.
The single finite-N penalty is the (1+r) factor in the normal equations.

## Unchanged estimator and returned interval

For outer fold k with a_k=n_k/n, held-out residuals R_ki=Y_i-g_k(P_i), and the
shared-pool function H(u)=sum_k a_k g_k(u), inference uses

    mu_hat = sum_k a_k mean(R_k) + mean(H(u)),
    V_hat = sum_k a_k^2 sample_var(R_k)/n_k + sample_var(H(u))/N.

The second term retains covariance between fold controls on the same unlabeled
records. Adding a distinct constant to each g_k on both its held-out and
unlabeled predictions leaves the center, variance and resulting interval
unchanged. No pooling of differently offset residuals is performed.

The inherited critical value is Student t with max(2,n-6) degrees of freedom;
endpoints are clipped to [0,1] for Bernoulli outcomes. Constant labeled OR
unlabeled scores, and Bernoulli samples with fewer than ten outcomes in either
class, retain the exact inherited label-only fallback. That is Clopper-Pearson
for Bernoulli and the ordinary Student t interval for real outcomes. The real
label-only interval is not distribution-free or finite-sample exact outside
normal sampling. Neither critical values nor fallback conditions were relaxed.

## Risk algebra and limitations

For a fixed two-component control vector q(P), let G=Cov(q(P)), c=Cov(q(P),Y)
and r=n/N. Independence of labeled and unlabeled observations gives n times the
variance of the fixed-control mean estimator as

    R(w) = Var(Y) - 2 w^T c + (1+r) w^T G w.

Differentiating R(w)+w^T D w gives the ridge normal equations
((1+r)G+D)w=c. Positive definite G gives unregularized solution
w_star=G^{-1}c/(1+r); a singular G may have nonunique coefficients but the
oracle prediction is still defined on its span. Zero and either individual
control belong to the unregularized population span, so its minimum risk cannot
exceed their population oracle risks. Penalization, estimated moments and
refitting do NOT inherit a finite-sample no-harm or interval-width guarantee.
Inner covariance estimates describe different fitted bases across folds, not
independent observations of a single fixed control. Overlapping training sets
also prevent interpreting foldwise quantities as independent risk replicates.

For any fixed scalar score, write m(P)=E[Y|P]. Completing the square shows that
the optimal unrestricted control is m(P)/(1+r), modulo constants. The optimal
affine control attains the same variance when m(P) is affine in P, including
nonconstant two-valued scores. Its gap from the unrestricted optimum is

    [Var(m(P)) - Cov(Y,P)^2/Var(P)] / [n(1+r)].

Thus these no-gain cases have no new nonlinear population oracle headroom;
differences between learned methods there can only reflect finite-sample
estimation behavior. Constant scores provide no information and trigger the
unchanged label-only fallback. Uninformative scores, rare events, heavy tails,
near-collinear bases and noisy inner moments can eliminate or reverse gains.

For learned cross-fit controls, sufficient asymptotic conditions include fixed
K, n,N tending to infinity with N/n tending to a positive finite constant,
finite 2+delta moments and uniform integrability of fitted control/residual
squares, and nondegenerate limiting variance. Crucially, require each fitted
g_k, modulo a training-dependent additive constant, to converge in L2 to one
common deterministic control. Stable base fits, consistent inner moments and
a nonsingular limiting covariance can support that requirement; they are not
established here for all inputs. With singular limiting covariance, prediction
stability must be justified separately; the vanishing ridge alone is not a
proof. Under common-control stability the held-out nuisance averages and the
independent shared-pool nuisance average have negligible first-order error,
yielding consistent studentization and asymptotic Wald coverage. This argument
is not an exact conditional-on-overlapping-training variance formula. The
Student t critical value does not establish finite-sample coverage.

## Separate internal certificate

For bounded bases, the signed stack range is training-measurable:

    L = sum(min(w,0)), U = sum(max(w,0)),
    g in [L,U], Y-g in [-U,1-L].

`StackedControl` passes these bounds to the inherited per-fold empirical
Bernstein calculation. Its error allocation alpha/(2K), weighted sum and union
bound are unchanged. Reuse of pools and overlapping fits does not require
independence for the union bound; each held-out/unlabeled sample has the needed
within-sample independence conditional on its own fold's training data. This
certificate is computed internally, including before binary fallback, and is
NOT the returned Wald interval or a validation of its coverage. No certificate
or fitted bounds are added to the RPC response.

## Authored tests and deferred validation

`test_stacking.py` exercises the actual live stack, moment helper, studentizer,
interval conversion and RPC. It checks normal equations, a single finite-N
factor, single-active and collinear bases, zero scale, signed unclipped outputs
and live certificate range propagation, shared inner splits, full-training
refit, outer held-out exclusion, within-fold moment shift invariance, whole
interval invariance for equal/unequal outer sizes, fallbacks and reset replay.
The inherited `test_controls.py` is preserved; no test source was inspected.
Neither test file was executed, so no pass result or empirical validity is
asserted. If execution is authorized later, a focused command from program_1 is:

    python -m unittest discover -s src -p 'test_stacking.py'

Implementation dependencies remain NumPy and SciPy; tests additionally use
standard-library unittest. No package installation or version probe was allowed,
so exact environment versions and runtime remain unmeasured.

Future authorized experiments should prespecify replication counts and pair
identical data/predictions across label-only, PPI, tuned PPI++, incumbent hard
selection, affine-only, diagonal-covariance and full stacking. Include weak
near-ties, nonlinear means, affine/two-valued and constant scores, rare outcomes,
heavy tails, varying N/n and permitted same-distribution frozen-score tables.
Report per-case binomial coverage uncertainty, paired width-difference
uncertainty and failures; pooled coverage cannot establish per-case validity.
Do not select completed intervals by minimum realized width. No experiments,
paper tables/figures or measured improvement are supplied in this source-only
stage, and no seeds or hidden interface fields are treated as population truth.
