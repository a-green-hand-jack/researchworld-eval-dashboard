# Honest score-only controls: implementation status

## Contract and primary output

The target remains the binary superpopulation mean E[Y]. The only inputs are
the supplied labeled outcomes and frozen labeled/unlabeled scalar scores.
The predictor is not retrained. `program.py:handle` keeps the starter's
reset/input/infer schemas, byte assembly, state transitions, and output bounds.
No diagnostic fields or track selector are added to RPC responses. There are
no additional runtime dependencies beyond the starter's NumPy and SciPy.

The primary RPC interval is a stabilized asymptotic Wald interval for n >= 16. For
n < 16 it is the labeled-only Clopper-Pearson interval; this rule uses sample
size only, not labels, fitted widths, scores, or hidden truths. The primary
procedure is NOT an exact finite-sample procedure for general n. In particular,
rare outcomes, all-zero/all-one samples, unstable fitted controls, and a fixed
small sample can invalidate Wald coverage. A zero empirical variance is not
evidence of a known population mean. To avoid a mechanically zero-width
interval on constant outcomes, let z be the normal critical value and a=z^2/n.
The interval center is (mu_hat+a/2)/(1+a), and its radius is
z*sqrt(V_hat+z^2/(4*n^2))/(1+a). This deterministic Wilson-style stabilization
is first-order equivalent to Wald at a nondegenerate limit, but is NOT an exact
Wilson interval for a fitted control estimator and has no finite-sample
coverage claim. It does not select between methods or tracks using outcomes.

## Fold isolation and calibration

Two random, label-independent labeled folds and two unlabeled folds are formed
from the reset seed. For each evaluation fold, only the complementary labeled
scores and labels enter `fit_score_calibrator`. Neither held-out labels nor
held-out scores nor any unlabeled scores determine knots, scaling, penalties,
or the fitted intercept. Fit-time knots are training quantiles. Candidate
families are an intercept, a ridge affine function, and small piecewise-linear
splines; training GCV chooses their penalties and complexity. The maximum
number of interior knots is seven. Held-out predictions are clipped to [0,1].
`fit_affine_calibrator` uses the same ridge penalties, GCV, constant candidate,
and clipping but excludes knots; `honest_score_intervals(..., affine=True)` is
an internal matched ablation, not a new RPC input. Clipped affine controls are
not the same class as unrestricted population-optimal affine controls.

Fold estimates are mean(Y-rho*g(S)) + rho*mean(g(S_U)), rho=N/(n+N).
Fold weights are the fixed labeled fold sizes divided by n, and are shared
between the point estimate and finite-sample endpoints. The two variance terms
use the separate labeled residual and unlabeled control arrays. Odd sample
sizes yield slightly unequal fold weights; the pooled Wald variance is a
first-order approximation, not an exact finite-sample variance identity.

## Separate finite-sample safety track

`honest_score_intervals` also computes `finite_sample` internally. The RPC
does not expose it, compare its width to Wald, intersect it with Wald, or
select a track using its width. It is available for a future permitted paired
study through direct internal function calls; no such study was run here.

Assume independent iid labeled pairs and iid unlabeled scores from the same
population, and a predictor frozen independently of evaluation labels. Given
each fold's complementary training sample, its held-out residuals have support
[-rho,1] and its held-out controls have support [0,rho]. Apply the two-sided
empirical-Bernstein radius

    sqrt(2*s^2*log(4/delta)/m) + 7*B*log(4/delta)/(3*(m-1))

with unbiased variance and known range length B. The radius is capped by B,
which remains valid because both sample and population means are in support.
For m=1, a full-range radius gives support fallback. The interface guarantees
n,N>=2, so neither of the two held-out folds is empty. Each of 2K components
receives delta=alpha/(2K). A union bound gives simultaneous coverage regardless
of dependence across fitted folds. Averaging endpoints with the same fixed
nonnegative weights therefore covers E[Y] with probability at least 1-alpha.
Only the known outcome support [0,1] is used to clip the resulting interval.
An empty numerical intersection is conservatively replaced by [0,1]. This
argument does not assume unconditional independence of cross-fitted folds.
The safety interval can be much wider than Wald or Clopper-Pearson.

## Oracle frontier and asymptotic qualifications

For fixed g, write m(S)=E[Y|S], rho=N/(n+N). Then

    Var(mu_hat_g) = Var(Y-rho*g(S))/n + rho^2*Var(g(S))/N
    Var(mu_hat_m) = E[Var(Y|S)]/n + Var(m(S))/(n+N).

The excess variance relative to m is rho/n times Var(g(S)-m(S)); additive
constants in g cancel. The reduction over the best unrestricted affine score
control is N/[n(n+N)] times E[(m-Pi_affine(m))^2]. For constant scores the affine
projection is the intercept. `study.py:oracle_frontier` implements this formula
from supplied analytic moments, not hidden evaluation targets.

For the Wald approximation, require n,N tending to infinity with a positive
finite limiting ratio, a nondegenerate limiting variance, and fold calibrators
converging in L2 to the same deterministic bounded function. Conditional
centering and cross-fitting then make nuisance empirical-mean errors negligible
relative to n^(-1/2). This is not an assertion of finite-fold independence.
The fixed spline dictionary need not consistently estimate arbitrary m, so
attainment of the oracle frontier is not claimed. Nonlinear information,
enough training labels, and stable nuisance estimation are needed for gains.
Affine m, uninformative scores, small N, rare events, and nuisance estimation
costs are important no-gain or failure regimes. Distribution shift is excluded.

## Evidence and unfinished work

Only permitted static candidate/interface inspection and editing occurred.
No candidate code was executed or imported; no tests, benchmarks, searches,
package installs, data downloads, or evaluations were run. No prohibited
literature was encountered. No literature outside the provided task text was
read. No empirically measured coverage, gain, timing, or score is reported.
The fold isolation above is a source-level design audit, not an executed test.

`study.py` supplies unexecuted paired uncertainty and per-repetition record
helpers: exact binomial coverage intervals, paired t intervals for mean width
differences, and explicit validity-track labels. They are not a completed
experiment runner. Paired repetitions, independent synthetic truth checks,
real-data masking studies, established-baseline comparisons, executable audit
tests, and the conference paper/PDF remain uncompleted because this stage
allows candidate preparation only and explicitly forbids their execution or
external source access. The harness alone performs the official evaluation.
