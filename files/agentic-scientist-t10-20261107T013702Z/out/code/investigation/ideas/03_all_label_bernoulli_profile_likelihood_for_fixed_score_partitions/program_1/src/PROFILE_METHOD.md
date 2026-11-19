# All-label Bernoulli profile likelihood: implementation, not measured evidence

## Scope and public contract

Target: the binary iid superpopulation mean mu = E[Y], not a finite-pool mean.
Assume iid labeled pairs (Y,S), iid unlabeled scores S from the same population,
independence between samples, and a predictor frozen independently of the
evaluation labels. Repeated sampling, not conditioning on all realized score
and label arrays, defines coverage. The realized arrays, sample sizes and
predictor are identical across the internal paired comparators.

The starter `program.py:handle` reset/input/infer contract, chunk assembly,
validation and state transitions are unchanged. Responses contain exactly the
documented keys. No population truth, unlabeled outcomes, strata metadata,
case identifiers, external files, feedback or extra controls are assumed.
Seeds initialize randomness only. Diagnostics never enter the RPC response.

For n < 16, the original labeled-only Clopper-Pearson branch is unchanged. For
n >= 16 the RPC returns the profile interval below, with no width-based method
selection. This combined procedure is NOT finite-sample exact for all n. The
separate exact interval is callable internally, but is not computed, intersected
or substituted by the RPC. It does not protect the returned profile endpoints.

## Partition and observed-data likelihood

Set K_budget = min(8, max(2, floor(n/32))) using sample size only. Use the reset
seed to permute unlabeled indices, reserve min(floor(N/5),256) scores as a pilot,
and exclude every pilot record from all likelihood counts. Pilot quantiles
at j/K_budget determine cuts; merge ties and remove cuts at 0 or 1. Assign ties
to the right cell. With no pilot, use deterministic j/K_budget cuts. The
resulting number of cells can be less than the budget. All labels are used.
Neither outcomes nor fitted interval widths choose the partition or a fallback.

Conditional on the pilot, B(S) is a fixed measurable partition. Let a_j and
b_j be labeled successes and failures and u_j the remaining unlabeled counts.
Write r_j1=P(B=j,Y=1), r_j0=P(B=j,Y=0), p_j=r_j1+r_j0. The log likelihood is

    ell(r) = sum_j [a_j log r_j1 + b_j log r_j0 + u_j log p_j],
    r >= 0, sum_j (r_j1+r_j0)=1.

The counts are actual observed counts. There are no pseudo-observations,
pseudocounts or fitted predictions treated as labels. `xlogy` implements
0 log 0 = 0. The multinomial combinatorial factors do not depend on r.
This finite-dimensional likelihood is exactly specified for any fixed score
partition: it models the joint law of (B,Y), not the conditional law of Y given
the entire continuous score. E[Y|S] need NOT be constant inside a cell.

Let M=N-pilot_size and n_j=a_j+b_j. The unrestricted MLE has
p_hat_j=(n_j+u_j)/(n+M) and q_hat_j=a_j/n_j when n_j>0. For n_j=0 choose
q_hat_j=1/2 as a representative of a flat likelihood, not as a pseudocount.
For entirely empty cells p_hat_j=0. Such cells are still retained in null fits;
the fit must not silently assume their population probability is zero.
The point estimate is sum p_hat_j q_hat_j, necessarily in [0,1]. A flat MLE
may give nonunique point estimates; the profile rather than an arbitrary
normal approximation handles that nonidentification numerically.

## Null fit, endpoints and numerical safeguards

For each mu in [0,1], maximize the same concave likelihood with the extra linear
constraint sum r_j1=mu. Invert

    2 [ell(r_hat)-ell(r_hat_mu)] <= chi2_(1,1-alpha).

`partition.py:profile_interval` uses an analytic gradient, SLSQP on the two
fixed-mass simplexes, nearby cached feasible solutions as warm starts and
bracketed Brent roots. The objective is scaled by n+M for optimization only;
LR differences and convergence certification use the original likelihood.
At mu=0 any observed success makes ell=-infinity; otherwise the null MLE is
the all-negative multinomial MLE. The symmetric rule applies at mu=1.

After rescaling the two fitted groups to their required masses, concavity gives
the global optimality bound

    ell_mu_star <= ell(r) + G,
    G = mu max_j grad_j1 + (1-mu) max_j grad_j0 - grad dot r.

Require successful solver termination, finite gradients and a nonnegative G
up to roundoff, with G <= 0.005 raw log-likelihood units. If necessary retry
at stricter objective tolerance. Use ell(r)+max(G,0) in the LR, which can only
enlarge its acceptance set relative to the exact constrained optimum in exact
arithmetic. Starting-point smoothing is initialization only: all bounds remain
closed at zero and the objective always uses the actual unsmoothed counts.

Roots use absolute tolerance 1e-7 and relative tolerance 1e-8, then move outward
by 2e-7. Unresolved fitting, root bracketing or nonfinite/invalid endpoints
produce [0,1], not short artifacts. Certification and padding are numerical
safeguards, not a formal interval-arithmetic proof. Solver behavior, failure
rates, speed and empirical coverage are UNTESTED in this stage.

## Coverage: two different claims

### Profile: asymptotic only

Conditional-pilot Wilks calibration requires a regular identifiable model:
fixed bounded cell count, positive population cell masses, strictly interior
q_j, growing labeled counts in each cell, and suitable two-sample asymptotics,
for example n,M tending to infinity with a positive finite ratio. Random pilot
cuts can be treated conditionally when these regularity conditions hold for
the resulting partition. Structurally empty cells, tiny cell probabilities,
zero successes/failures, nearly deterministic labels, or rare-event sequences
are NOT covered by a boundary-uniform Wilks assertion. The n<16 exact branch
does not repair these issues for n>=16. Undercoverage must be reported if
later experiments find it; no score improvement or nominal coverage is claimed.

### Exact partition safety: finite-sample, separate

`exact_partition_interval` allocates alpha/(2K) to each of K two-sided CP
intervals for q_j from a_j of n_j labels and K two-sided CP intervals for p_j
from u_j of M unlabeled scores. Use [0,1] for q_j when n_j=0. Conditional on
the pilot and the labeled bin counts, each a_j is binomial(n_j,q_j), so the CP
bound holds conditionally and hence marginally. Each u_j is marginally
binomial(M,p_j). A union bound, requiring no independence across intervals,
makes all 2K inclusions simultaneous with probability at least 1-alpha.

On that event the true p lies in the intersection of the simplex and all
p-bounds. Since p_j>=0,

    min_p p dot q_lower <= mu <= max_p p dot q_upper.

Two simplex-box LPs give these extrema. The implementation uses the LP equality
dual multipliers to calculate conservative bounds: for any lambda,

    min_p c dot p >= lambda + sum_j min((c_j-lambda) l_j,
                                                        (c_j-lambda) h_j).

Use c=q_lower for the lower bound and c=-q_upper for the upper bound, with
outward roundoff padding. If M=0, the region is infeasible, the solver fails or
results are invalid, return [0,1]. The statistical coverage argument is exact
for the mathematical region and CP inversion, subject to ordinary numerical
precision in its implementation. It needs no calibration assumption and
allows empty/boundary cells, but can be much wider than profile or labeled-only
intervals. There is no unadjusted intersection/minimum with another track.

## First-order variance and possible/no-gain regimes

Write q_B=E[Y|B] and p_j=P(B=j). In the regular model the pooled multinomial
estimate of p has covariance (diag(p)-pp')/(n+M). The conditional binomial
estimate q_j has first-order variance q_j(1-q_j)/(n p_j). Their information
blocks are orthogonal, so delta-method variance of sum p_hat_j q_hat_j is

    V_B = E[Var(Y|B)]/n + Var(q_B)/(n+M).

`partition_variance` implements this expression, and `matched_partition_wald`
uses its plug-in version with the exact same pilot and counts. It is an
asymptotic ablation, not an exact fallback; it may degenerate at boundaries.
For continuous-score m(S)=E[Y|S], the ideal score-only control frontier is

    V_S = E[Var(Y|S)]/n + Var(m(S))/(n+M),
    V_B - V_S = M/[n(n+M)] E[(m(S)-E[m(S)|B])^2] >= 0.

For unrestricted scalar affine controls the corresponding variance reduction
from labeled-only inference is M/[n(n+M)] Cov(Y,S)^2/Var(S), or zero for
constant scores. Binning instead reduces it by M/[n(n+M)] Var(q_B). Neither
quantity universally exceeds the other. Nonlinear conditional means can favor
bins, but coarse bins can discard even useful affine information. If m is
constant within bins, the binning loss vanishes; if m is globally constant,
there is no first-order score gain. Constant-within-bin means do NOT imply
affine-in-score calibration. Small n, tiny cells and boundary probabilities
need separate empirical investigation, not the regular variance formula.

The pilot has a real information cost: all formulas use M, not the original N.
Known cell prevalence removes the between-cell term, but is an explicitly
synthetic oracle ablation, unavailable through the RPC. The incumbent spends
labels fitting complementary-fold splines; here all labels enter the same
observed-data likelihood, but cell discretization can lose information.

## Internal comparator and evidence helpers

- `incumbent.py` is a byte-for-byte copy of starter `program.py`.
- `evidence.py:compare_on_arrays` computes labeled CP/Wilson, original scalar
  PPI, unrestricted scalar plug-in PPI++, unchanged incumbent, matched-bin Wald,
  profile, separate CP safety, K=1 and deterministic-cut profile intervals.
- `known_prevalence_wald` is an internal synthetic oracle, not an RPC option.
- `summarize_repetitions` reports CP coverage intervals, mean widths with MCSE,
  paired profile-minus-incumbent width differences with MCSE and t intervals,
  optimization failures and misses in observed zero-success/failure cells.
  The latter flags observed sparse/boundary cells, not hidden true q_j values.

These helpers require aligned independent repetitions supplied by a future
authorized study. They have NOT been executed. They are not a complete study
runner, verification tests or numerical evidence. No baseline-package parity
or runtime is asserted. The inherited `study.py` remains unmodified and was
not used as an experiment or source of results.

## Reproducibility status and limitations

Runtime dependencies remain NumPy and SciPy; no package installation occurred.
The intended interpreter is the contract's Linux CPython 3.12, float64, CPU.
Installed dependency versions and timings were not inspected or measured.
No external sources were accessed: only the task text and allowed candidate
files were read. The supplied literature list is context, not a claim that
those papers have been independently read. No forbidden material was sought
or encountered. One combined edit-shell invocation failed to locate the
patch utility; its patch was reapplied separately, with no scientific code run.

No candidate imports/execution, tests, benchmarks, optimizers, package managers,
network calls or evaluations were invoked during preparation. Encoding,
numerical stability and failure rates therefore still need official runtime
validation. No measured score, coverage, width, speed or superiority claim is
made. No numerical tables or figures have been fabricated.

Future authorized work should use at least 1000 independent repetitions per
primary setting, the same fixed inputs for each method, and independent seeds
for study generation rather than inferred workload identifiers. Study affine,
nonlinear/U-shaped, uninformative, rare-event, sparse/tied and nearly
deterministic settings across n and N/n, reporting both all-run and numerical
failure counts. Public binary PPI examples, if later downloaded lawfully, may
be sampled with replacement to define an explicit empirical-distribution
superpopulation truth; this is not a finite-pool estimand. Distribution shift
is an assumption violation, not evidence of nominal iid validity.

Execution and external downloads are forbidden in the present stage. Repeated
sampling, real-data evidence, dependency pins, a measured execution budget,
formal executed verification, latest official conference template/checklist,
paper PDF/LaTeX and script-to-figure mappings remain unfinished. This candidate
does not pretend those broader research deliverables have been completed.
