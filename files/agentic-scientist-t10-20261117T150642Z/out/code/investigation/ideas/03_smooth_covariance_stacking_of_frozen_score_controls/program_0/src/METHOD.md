# Offset-invariant risk-adaptive controls: implementation note

This is a source-only candidate, not an evaluated research paper. No candidate
code, tests, simulations, package managers, network requests, or evaluators were
run during this stage. No measured coverage, width, score, or runtime is claimed.
Only the supplied task and permitted starter files were read; there was no
literature browsing or forbidden-content encounter. The larger paper/PDF,
official template/checklist, real-data experiments, and repeated-run evidence
remain unperformed, not replaced by illustrative numbers.

## Interface, target, and scope

The target is the superpopulation mean theta = E[Y]. Inputs are labeled outcomes
y[n], their frozen scalar predictions p[n], and independent unlabeled predictions
u[N]. Assume iid labeled pairs and iid unlabeled scores from the same population,
independent of each other, with an externally frozen predictor. Conditioning on
one realized input fixes resources across methods; coverage still concerns
repeated sampling, not uncertainty conditional on all those realized values.
Informative label selection, distribution shift, and predictor training on these
labels are outside this justification.

The reset/start/chunk/commit/infer protocol, validation, response keys/types,
transfer format, manifest and entrypoint are unchanged. Only infer returns
`lower` and `upper`; no diagnostics or additional observations enter responses.
Reset clears fits and seeded random state. Training and selection use only outer
training labels/scores and the supplied sample sizes; unlabeled values never
enter training, selection, normalization, or multiplier fitting. No X, oracle
labels, baseline intervals, hidden inputs, or cross-episode memory are assumed.

## Implemented selection and fitting

`program.py::_crossfit_controls` partitions a reset-seeded permutation into
K=min(5,floor(n/2)) held-out folds. Each has at least two observations for the
supported n>=8. Explicit index assertions verify the outer training boundary.
Each outer training sample uses three inner folds (at least two validation
observations per fold at the smallest supported size). All families use exactly
the same inner splits, drawn before fitting any family.

The prespecified families, in increasing complexity, are:

1. Zero control.
2. Affine least-squares calibration of the scalar score. Score normalization,
   intercept, and slope are fitted only on the relevant training sample. For
   binary outcomes the calibration prediction is clipped to [0,1].
3. The starter's small spline/ridge calibration: linear, quadratic and three
   positive-part terms at normalized knots -0.5, 0 and 0.5. Training-only
   10th/90th percentile scaling, range fallback, clipped features, and penalties
   (0.1,2,4,4,4) are retained. Binary predictions are clipped to [0,1].

For each fitted nonzero calibration q, let rho=n/N using the full supplied
sizes, even during inner fitting. Fit

    b = Cov_train(Y,q(P)) / [(1+rho) Var_train(q(P))],
    g(p) = b*q(p).

Nonfinite or machine-resolution-degenerate denominators, or nonfinite weights,
produce a zero control. The relative variance guard is measured against the
squared maximum training calibration magnitude. It is a numerical guard, not
a performance tuning parameter. The signed multiplier is applied exactly once;
there is no additional multiplication by N/(n+N) after fitting g. Binary q is
clipped BEFORE multiplication, not after multiplying a potentially signed b.

On each inner validation fold compute

    J_hat(g) = sample_var(Y-g(P)) + rho*sample_var(g(P)).

Start from zero. Compare affine, then nonlinear to the currently selected
family. Move only if the mean paired excess risk plus its foldwise sample
standard deviation divided by sqrt(number of inner folds) is negative. Refit
both calibration and multiplier on all outer training data after selection.
Validation folds are equally weighted for this prespecified heuristic even
when sizes differ by one. Because fits overlap, this foldwise quantity is NOT
a calibrated standard error, a significance test, or a coverage guarantee.
No completed intervals are compared or selected for their realized widths.

## Offset-invariant shared-pool studentization

For fold k of size n_k and weight w_k=n_k/n, let g_k be its fitted control,
r_ki=Y_i-g_k(P_i), and H(u)=sum_k w_k*g_k(u). The actual return path uses

    theta_hat = sum_k w_k*mean(r_k) + mean(H(u)),
    V_L = sum_k w_k^2*sample_var(r_k)/n_k,
    V_U = sample_var(H(u))/N,
    V_hat = V_L + V_U.

Variance is computed only AFTER combining all controls on the same unlabeled
pool. This retains every covariance term from shared observations; a sum of
fold-specific unlabeled variances would generally be wrong.

Replacing each g_k by g_k+c_k changes r_k by -c_k and H by the constant
sum_k w_k*c_k. Both the point estimate and variance are unchanged, including
unequal fold sizes. The same center/variance implies identical endpoints under
the same interval builder. These shifted controls are abstract signed controls,
not modified predictor outputs; they must not be clipped again after shifting.
Pooled residual sample variance need not have this invariance. This algebra
alone implies neither improved coverage nor a decrease in measured width.
Within-fold variance can be larger or smaller on individual realized samples.

`_interval_from_statistics` retains the starter's Student-t critical value with
max(2,n-6) degrees of freedom. Binary endpoints are clipped to [0,1]. Constant
scores in either pool and binary samples with fewer than ten successes or
failures retain the label-only rule: Clopper-Pearson for binary, Student-t for
real. Real Student-t intervals are exact under iid Gaussian outcomes, not
general real outcomes. The data-dependent binary fallback does not give the
combined Wald/fallback procedure an exact finite-sample coverage guarantee.

## Variance identities and their limits

For deterministic fold controls, independent sampling gives exactly

    E[theta_hat] = theta,
    Var(theta_hat) = sum_k w_k^2*Var(Y-g_k(P))/n_k
                    + Var(sum_k w_k*g_k(P))/N.

The labeled terms are independent because deterministic functions are applied
to disjoint iid observations, and the unlabeled sample is independent of them.
The implemented sample-variance estimate is unbiased for this deterministic
variance, even when controls have different shapes. Normal or t coverage is
still not exact merely because variance is estimated without bias.

For a common deterministic control g, completing the square with
m(P)=E[Y|P], e=E[Var(Y|P)], and a=N/(n+N) gives

    V(g) = e/n + Var(m)/(n+N) + (1/n+1/N)*Var(g-a*m).

For an independently fixed calibration m_hat and J(g)=n*V(g), this yields

    J(a*m_hat) = Var(Y) - a*Var(m) + a*Var(m_hat-m).

Thus calibration estimation error can consume the available prediction
headroom. At the oracle level, the optimal affine variance and nonlinear gap
for positive score variance are

    V_affine = Var(Y)/n - N*Cov(Y,P)^2/[n*(n+N)*Var(P)],
    V_affine - V_oracle = N/[n*(n+N)]
                         *[Var(m)-Cov(Y,P)^2/Var(P)].

The gap is zero for affine conditional means, uninformative scores, and scores
with at most two support points. Estimated nonlinear fits are not guaranteed
to improve on a fitted affine or zero control. These are deterministic oracle
identities, not a learned-nuisance coverage theorem or a universal lower bound
over arbitrary confidence intervals.

For learned cross-fit controls, overlapping training folds create dependence:
the deterministic variance formula is NOT an exact conditional-on-training
formula for the full estimator. A sufficient asymptotic framework is fixed K,
n,N tending to infinity with N/n tending to a positive finite constant,
finite 2+delta moments with suitable uniform integrability for fitted residual
and control squares, nondegenerate limiting variance, and stable selection and
fitting so that g_k-c_k converges in L2 to one common deterministic g for every
fold. The c_k may be training-dependent additive constants. They cancel exactly
before the usual cross-fit argument. Conditional on the training observations
for a given fold, the centered held-out nuisance-error average is negligible
at n^(-1/2) when its L2 norm tends to zero; the independent shared unlabeled
sample is handled by the analogous average for the combined nuisance. Fixed
K then gives the common-control first-order limit. The within-fold residual
variances and shared-pool variance consistently estimate its variance under
the stated moment/stability conditions, giving asymptotic Wald coverage.

These conditions need not hold for arbitrary unstable nuisance fits or
near-tied selections among distinct limiting controls. The one-standard-error
rule does not establish them. A small basis need not converge to m. Heavy
tails, rare binary events, unstable selection, and small samples require actual
coverage checks; there is no universal finite-sample t guarantee here.

## Separate internal bounded certificate

As in the starter, bounded inputs also compute a standalone internal certificate
on every input, before choosing a fallback or Wald interval. If a fitted binary
control has weight b, it lies in [L,U]=[min(0,b),max(0,b)], since its calibration
q lies in [0,1]. Its residual lies in [-U,1-L]. Bounds are training-only and
remain valid for zero and signed controls. The original two-sided empirical
Bernstein radius is retained for each fold's residual and control means, with
error allocation alpha/(2K), weighted addition and a union bound. The sample
variance, range term and truncation are the starter's unchanged implementation.
Conditional independence within each held-out/unlabeled sample and a union
bound suffice; no independence of reused pools or overlapping folds is claimed.
The weighted center is the same as the reported estimator, but this certificate
does NOT determine the reported interval and is not exposed by RPC. The return
must not be described as certified.

## Source-tree tests and deferred experiments

`test_controls.py` contains executable unittest regression checks for the actual
`_control_statistics` and `_interval_from_statistics` used in inference. They
inject five unequal offsets AFTER fitting, into both held-out and shared-pool
controls, for equal and unequal fold sizes, without reclipping. Other tests
check the explicit shared-pool covariance formula, zero/constant controls,
single-use finite-N weighting, identical inner splits and full-training refit,
outer training-only inputs, small samples, finite bounded endpoints,
constant-score fallback, response keys, state transitions, and reset replay.
They were authored but NOT executed. When execution is authorized, from the
candidate directory the focused command is:

    python -m unittest discover -s src -p 'test_controls.py'

No new dependency is introduced: implementation uses existing NumPy and SciPy;
tests additionally use the Python standard library. Dependency versions and
runtime have not been measured or pinned in this non-executing stage.

Required future scientific checks include paired repeated draws for incumbent,
variance-only, affine-only, selection-only and combined methods, plus label-only,
PPI, tuned PPI++ and a permitted fixed-stratum comparator. Cover affine and
nonlinear signals, weak/shuffled scores, rare events, heavy tails, unequal
folds, and varying N/n; use identical n,N and frozen predictions across methods.
Report coverage uncertainty and paired width uncertainty. Real-table studies
must avoid distribution-shift pooling. The interface has no population labels
or oracle means, so such diagnostics cannot be invented from seeds or presumed
evaluator inputs. No empirical improvement, nominal coverage, completed paper,
or publication artifact is asserted by this candidate.
