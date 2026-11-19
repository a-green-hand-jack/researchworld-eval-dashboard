# Fixed-budget audit with exact forests and bounded logistic quadrature

This candidate preserves the starter RPC operations and exact response keys.
Only the supplied frozen model, original scalar-encoded feature groups, query,
background and budget are used. No reference target or additional request field
is assumed. The unchanged starter `kernel_shap` function remains available as
the original baseline; the response path uses `explain_fixed_game`.

## Budget and estimation

All forest explanation requests now use `forest.exact_forest_shapley`, before
the existing nonforest budget dispatch. This computes the same empirical
interventional, probability-scale game from uploaded arrays, not from reference
targets. The affine and logistic estimators, upload validation, RPC response
keys, reset behavior, and sampled-branch RNG handling are unchanged. Forest
calls are deterministic and do not consume RNG draws or sampled coalitions.
No across-call attribution, coalition, or compiled-tree cache is introduced.

Each tree path is compiled into lower-exclusive / upper-inclusive intervals on
distinct original feature groups. Repeated splits are intersected and impossible
paths discarded. Query and background values are converted to float32 before
comparison to float64 bounds, matching the predictor. Unbounded lower intervals
also admit negative infinity produced by conversion of finite extreme inputs.
For each leaf and each full-background row, features are required included,
required excluded, unconstrained (both pass), or make the leaf unreachable
(neither passes). An unreachable row contributes zero; a constant leaf has no
attribution. With `a` required inclusions and `c` required exclusions, each
inclusion gets `p/(a*comb(a+c,a))`, and each exclusion gets
`-p/(c*comb(a+c,a))`, when the respective count is nonzero. These coefficients
integrate permutation marginals of the conjunction, with other features dummy.
Linearity permits summing leaves and averaging every supplied row and tree.
There is no coalition enumeration or sampling in this forest branch. Per-leaf
temporary arrays have at most `B*depth` entries; paths are compiled one tree at
a time, and beta tables have `(d+1)^2` entries. Runtime and memory limits remain
unchanged; no measured runtime or score improvement is claimed.

For logistic models, nonexhaustive calls first attempt the deterministic
probability-game integration described below. If any background row rejects,
the unchanged estimator below receives its original budget and RNG state.

For a fallback nonexhaustive budget `b` and `d` features, preallocate
`floor(b / (4*(d-1)))` independent uniform complete permutation paths, provided
this is at least two. A path costs `d-1` nontrivial coalition observations.
Allocate the remainder to kernel-distributed subsets with complement pairing.
Pairing is used only for regression, never for the independent path bound.
The total sampled nontrivial coalitions is at most `b`; query-local deterministic
caching can reduce the actual prediction count. Empty/full endpoints are not
nontrivial coalitions. Every coalition averages the entire supplied background.
No new background is sampled. A fixed quarter allocation is an untested design
choice, not a measured optimum; it can reduce fidelity relative to the starter.

Path prefixes are uniform over subsets conditional on size, with uniform size
frequency. Kernel samples have size probability proportional to `1/(s*(d-s))`.
Importance weights correct this mixture for the kernel objective. An orthonormal
sum-zero basis imposes efficiency without privileging the final coordinate in
underdetermined least squares. Regression coefficients carry no certificate.

For the unchanged nonforest path, if the budget covers every nontrivial subset,
compute exhaustive original-column
Shapley values with an efficiency assertion. This exact estimate is not an
independent reference experiment. Affine fixtures use their analytic solution.
All forest predictions retain the starter's float32 input comparison semantics.

## Bounded logistic Fourier/Owen branch

`logistic_fourier.py` uses only uploaded coefficients, intercept, query and every
actual background row. For a row `b`, let `a = b @ coef + intercept` and
`delta = coef * (query-b)`. It integrates the imaginary part of
`exp(i*w*a) * expm1(i*w*delta_j)` times the Owen inclusion-probability integral
`integral_0^1 product_{l != j}(1-t+t*exp(i*w*delta_l)) dt`, divided by
`sinh(pi*w)`. This follows from the sigmoid Fourier identity and the multilinear
extension of this fixed probability game, not from logit attributions or
integrated gradients. The degree is at most `d-1`, so `ceil(d/2)` Gauss-Legendre
inclusion nodes integrate that polynomial exactly apart from floating-point
rounding. Prefix/suffix products avoid division at zero mixture factors.

Frequency integration uses composite eight-node Gauss-Legendre panels on
`[0,8]`. Interior nodes and `expm1` handle the zero-frequency limiting integrand
`delta_j/pi`. The per-coordinate omitted-tail bound is
`-(2/pi)*log(tanh(pi*8/2))`, required to be at most `1e-10`. It bounds only the
analytic tail, not total numerical error. The predictor's clipping at logit
magnitude 700 changes mathematical sigmoid below ordinary float64 absolute
precision; finite arithmetic and cancellation still require numerical checks.

All coalition logits for a row lie between `a+sum(min(delta,0))` and
`a+sum(max(delta,0))`. Initial panel count is at least the ceiling of the maximum
absolute phase bound times cutoff divided by eight. Preflight reserves room for
two doublings within 2048 frequency nodes per level. Each level processes at
most 32 frequency nodes at a time, and backgrounds are processed one row at a
time. There are at most nine levels (8 through 2048 nodes) per row; this is a
work cap, not a measured runtime guarantee. Refinement requires two successive
coordinate-wise max differences at most `1e-8` AND endpoint efficiency errors
at most `1e-8`. Nonfinite arithmetic, excessive phase, insufficient work or
failed diagnostics return `None`; the whole call then uses the incumbent
sampled estimator. There is no partial-background approximation, efficiency
projection, coefficient sign replacement or timing-dependent dispatch.

The final vector averages every resolved background row. Integration uses no
coalition predictions, random draws, cross-call answer cache or new response
fields. Mesh agreement and efficiency are diagnostics, NOT a discretization
error proof. Oscillation/aliasing, finite-precision phase cancellation and
near-zero attribution gaps remain limitations. Deterministic outputs alone
do not establish fidelity, causal meaning or acceptable high-risk reasons.

`validate_logistic_fourier.py` is independent executable validation source for
a later authorized stage: `python src/validate_logistic_fourier.py` from the
candidate directory. It enumerates small games with a separate scalar
probability predictor and factorial Shapley weights; checks coordinates,
efficiency, all-row averaging, dummies, exact repeats, zero mixture factors and
the near-origin limit; and exercises dispatch, RNG preservation, work caps,
nonfinite/efficiency/refinement rejection, unchanged sampled fallback and RPC
upload/reset/replay. Its fixtures include mixed signs, positive/negative
saturation, odd/even dimensions, repeated backgrounds, near ties and identical
query/background rows. These checks were written but NOT executed. No new
accuracy, score, measured runtime or public-data findings are asserted.

## Certificate and scope

For a fixed game each coordinate of an independent path marginal vector lies
in `[-1,1]` and has expectation equal to its Shapley value. Apply the two-sided
empirical Bernstein bound for range width two, with conservative logarithm
`log(4*d/alpha)`, and union-bound the coordinate failure events. The radius is
`sqrt(2*s_j^2*log(4*d/alpha)/m) + 14*log(4*d/alpha)/(3*(m-1))`.
On simultaneous coverage, strict separation between selected lower absolute
bounds and excluded upper absolute bounds identifies the exact absolute top-k;
selected intervals excluding zero establish signs. Stable original-column order
breaks estimated ties; a true boundary tie cannot pass the strict criterion on
the coverage event. Here `k=min(3,d-1)` and `alpha=0.05` are fixed in advance.

The wrong-certificate probability is at most alpha per prespecified fixed-game
call. It is not a bound on conditional accepted-call error, simultaneous error
across RPC calls, background sensitivity, causal validity or fairness. Nothing
is certified about fallback regression outputs. When accepted, the returned
vector is the certified path mean, not the regression vector. A conservative
bound may never accept under these budgets; no coverage is claimed.

## Unavailable research mechanisms and validation

The transport contains already encoded columns, not raw pandas data or a frozen
preprocessing pipeline. Consequently this implements masking of the supplied
groups, not the proposed raw-data masking API. The harness supplies neither
dataset identities and splits nor per-instance reference failures. No German,
ACS or Pima experiments, independent reference study, bootstrap confidence
interval, paper, figures or performance improvement are claimed. The RPC has no
certificate/artifact response field, so decisions and measured prediction-row
counts remain internal to the query-local computation and are not persisted.

No candidate code, tests, benchmark, network access, literature search or
evaluation was executed during preparation, per the stage restrictions. Runtime
checks cover bounded path increments, complete-path efficiency and exhaustive
efficiency when those branches are exercised later; these are not a substitute
for additive-game tests or independent statistical validation. No external
literature was accessed and no prohibited paper was encountered.

`validate_forest.py` contains executable, independent small-game checks for a
later authorized stage (`python src/validate_forest.py` from the candidate
directory). It uses separate scalar traversal and exhaustive permutation means,
compares exact vectors and endpoint efficiency, checks deterministic repeats,
budget invariance and absence of forest RNG consumption, and compares the
starter predictor to scalar traversal. Fixtures cover repeated splits,
impossible leaves, mixed positive/negative literals, dummy features, root-only
constant trees, multiple trees, multiple and repeated background rows, identical
queries/backgrounds, equality and float32 rounding near thresholds, and finite
inputs that overflow float32. These routines were written but not executed.
This candidate step does not complete the public-data study or paper, establish
background robustness or causal validity, or resolve near-zero sign ambiguity.
