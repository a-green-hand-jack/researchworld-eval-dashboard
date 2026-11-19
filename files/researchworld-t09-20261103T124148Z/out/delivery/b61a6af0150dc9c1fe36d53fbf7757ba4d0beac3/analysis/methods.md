# Analysis methods and scoring definitions

## Target and repeated-sampling population
For fixed graph A, covariate vector x and interference mechanism f, define
Y_i(z)=0.5 x_i + z_i + gamma h_i(z) + epsilon_i. The same additive epsilon_i
appears at every assignment, hence tau = n^-1 sum_i[Y_i(1)-Y_i(0)] is 1+gamma
for linear/quadratic/cubic/sigmoid/threshold/twohop h and 1+2gamma for hidden_tail.
The frozen study uses gamma=1 in every cell; the code parameterizes gamma, but no treatment-strength sensitivity grid was run.
We average experimental error over assignments and Gaussian outcome noise,
conditional on each graph and x. Graph-replicated analyses will retain graph
identity and treat graph uncertainty separately. This is a semi-synthetic
outcome experiment, not evidence about actual social outcomes.

S_i is the fraction of treated immediate neighbors; isolates use own treatment,
so global endpoint exposures are exactly zero and one. T=P S is the two-hop
random-walk exposure, allowing backtracking. Each graph's known x is iid standard
normal independent of topology and assignment. Regressions include x except naive.

## Fixed linear-smoother identity
For a feature matrix X(z), endpoint contrast c = n^-1 sum_i[X_i(1)-X_i(0)],
minimum-norm OLS gives tauhat = c' X^+ Y = a'Y. Let m(z)=E[Y|z], and
Sigma = B B' be noise covariance. Conditional bias is b(z)=a'm(z)-tau;
conditional variance is v(z)=||B'a||²; conditional MSE is b(z)²+v(z).
Across assignments MSE=E[b²]+E[v]. Bias=E[b], variance=Var(b)+E[v].
These identities require fixed features conditional on assignment, finite second
moments and mean-zero noise; no asymptotic approximation or iid node assumption.
They are diagnostics here, not asserted as novel theorems. If c is outside X's
row space, minimum-norm extrapolation is not identified by the fitted features;
flag this using ||c-proj_row(X)c|| rather than silently treating it as valid.

Gaussian noise is epsilon=B u, u~N(0,I), B row-normalizes I+rho P to unit marginal
variance. The iid case is rho=0. A Gaussian 95% interval using exact v is an
oracle diagnostic; it is not a feasible interval. HC3 is a deliberately simple
working-independence interval and must not be called generally valid under
network-correlated noise or model misspecification.

## Full-neighborhood weighting baseline
A node is fully exposed when own and every immediate neighbor treatment agree.
Under independent Bernoulli assignment its event probabilities are p^(d_i+1)
and (1-p)^(d_i+1). Under cluster assignment replace d_i+1 by the number of distinct
clusters touched by that closed neighborhood. HT averages probability-weighted
observed outcomes; Hajek divides each arm by its realized weight total, undefined
if either total is zero. These estimate the GATE under one-hop exposure sufficiency.
For two-hop outcomes the same one-hop baseline is intentionally misspecified.
On dense graphs tiny probabilities make sample RMSE an unreliable description
of rare-event risk; probability diagnostics and exact risk where feasible are
needed before comparing it to regression.

## Mechanisms
linear h=s; quadratic h=s²; cubic h=s³; sigmoid h=(logit^-1(12(s-.5))-
logit^-1(-6))/(logit^-1(6)-logit^-1(-6)); threshold h=1{s>=.75};
twohop h=.5(s+Ps); hidden_tail h=s+max((s-.85)/.15,0)².
The hidden_tail mechanism equals linear on [0,.85] but its endpoint effect differs.
It tests poor policy support, not a claim that arbitrary functions are identifiable.

## Initial validation and failure log
2026-11-03: first four scientific tests failed before any simulation because current
SciPy rejects boolean input to sparse.diags. Cast the isolated-node mask to float;
all four initial tests then passed. An additional exact HT risk test also passed. Tests cover endpoint targets, exact matched-linear
GATE and covariance algebra, a nonzero realized misspecification bias, and exhaustive
HT unbiasedness on eight nodes for individual and cluster randomization.

## Source handling
Only frozen supplied materials and the explicit SNAP data URL have been accessed.
No prohibited-paper search or access has occurred. Source data download is identical
to the supplied SHA-256 (see data/manifest.json). Literature interpretation is supplied
by idea-repo; experiments do not search for the withheld paper.

## Exact HT rare-event risk
Let N_i be the set of independent assignment units in node i's closed neighborhood
(individual nodes or partition clusters), and k_ij=|N_i intersect N_j|. For endpoint
means m1,m0 and additive noise covariance Sigma, define Qab_ij=ma_i mb_j+Sigma_ij.
Full-neighborhood HT is unbiased for one-hop mechanisms. Its exact variance is
n^-2 sum_ij [Q11_ij(p^-k_ij-1)+Q00_ij((1-p)^-k_ij-1)+2 Q10_ij 1{k_ij>0}].
The joint opposite-arm event is impossible when N_i and N_j overlap; otherwise
the events are independent. This formula is implemented blockwise in long-double
precision, reporting log10 risk when double precision overflows. Exhaustive
weighted enumeration at p=.3 on an eight-node graph checks the formula for both
individual and cluster designs with correlated noise. It is not applied to the
two-hop mechanism, for which one-hop full exposure need not reveal endpoints.

## Quadratic complement cancellation
With adjusted baseline 0.5*x and fitted features (1,z,x,s), let a(z) be the
endpoint-contrast weights when the contrast is estimable. Complement assignment
maps the feature span to itself and a(1-z)=-a(z). For m(z)=0.5*x+z+gamma*s²,
m(1-z)=m(z)+(1+gamma)*1-2z-2gamma*s. Consequently
[a(z)'m(z)+a(1-z)'m(1-z)]/2=1+gamma=tau. Under Bernoulli(.5) assignment by nodes
or fixed clusters, complement pairs have equal probability, so the average
conditional bias cancels (provided contrast estimability holds; degenerate
assignments need a declared convention). The realized conditional bias need
not be zero, and assignment variance need not vanish. This is not generic
protection against response misspecification: other shapes need not obey this
algebra, and p!=.5 no longer gives equal weights to complement assignments.
An executable complement-pair test checks the identity; it is an elementary
property of this study's DGP, not a claimed new general theorem.

## Prediction and performance uncertainty
Prediction MSE is evaluated on an independent experimental assignment with a
fresh independent noise vector under the same fixed graph/design/p. The trained
regression sees only its original experiment. `prediction_mean_mse` instead
compares to the known simulation conditional mean to distinguish noise floor.
Prediction target is assignment-distribution performance, not policy endpoints.

Graph-conditional summaries retain all algorithm outputs, including minimum-norm
returns with nonestimable contrasts; `valid_fraction` flags the unsupported
extrapolations. Undefined Hajek returns are excluded from its finite-value
performance ONLY with `defined_fraction` reported; this is conditional defined-run
risk, not unconditional estimator risk. No arbitrary imputation is used. Empirical
HT risk is not trusted when exact tail risk or endpoint counts show rare-event
failure. Use exact one-hop risk where available; one-hop HT on twohop is a
mapping-misspecified comparator, not an unbiased baseline.

Bias MCSE is sample SD(error)/sqrt(R); MSE MCSE is SD(error²)/sqrt(R); RMSE MCSE
uses the delta method MSE_MCSE/(2*RMSE). Normal 95% Monte Carlo intervals are
approximate and may be poor for extreme-tail distributions; exact HT risk and
raw replicates make this visible. Coverage has Wilson95% binomial intervals.
Paired differences use error² differences or the RMSE influence difference,
shared assignment/noise across compared models. Across five independently
simulated graphs, family summaries weight each graph equally and use t4
intervals from graph summaries, with graph-conditional MCSE shown separately.
The family pooled RMSE is sqrt(mean graph MSE); mean graph RMSE is a distinct
reported descriptive statistic. A single public graph has no graph-population CI.

## A policy-support coupling check
Compare linear h=s with hidden_tail h=s+max((s-.85)/.15,0)², same graph/x/assignment/
noise. Their endpoint targets differ by gamma, but their observed data coincide
on E={max_i s_i<=.85}. Any estimator that uses only that experiment and the same
predeclared features gives the same T on E. Pointwise on E,
(T-tau_linear)²+(T-tau_tail)² >= gamma²/2. Averaging under the coupled experiment
implies max(MSE_linear,MSE_tail)>=gamma² P(E)/4. This bound applies to a shared
estimation rule not given the true mechanism label, not to an oracle told which
DGP generated the observations. The actual code fits shared features before
looping over mechanisms; those fits receive no label. This is an elementary
support limitation for the constructed pair, not a theorem that all network
interference is unidentifiable.

For d-regular graphs under node Bernoulli(p), neighbor-treated counts marginally
follow Binomial(d,p), so P(E)>=max(0,1-n P[Bin(d,p)>.85d]) by the union bound.
No independent-node approximation is used. `gatebench.support_bounds` computes
these exact marginal probabilities and the lower bound for the study's regular
regimes. It does not apply the binomial law unchanged to cluster assignment.
Raw `tail_active` counts and paired linear/hidden_tail rows provide an executable
coupling check. The independent-assignment prediction data are not used by T.

## Frozen scoring/failure policy and numerical thresholds
Primary regression `estimate`/error/bias/RMSE summarize the specified minimum-norm
algorithm over every finite returned estimate, including nonestimable endpoint
contrasts. These are operational algorithm risks, not evidence of identified
endpoint prediction. Separate `estimable_*` metrics condition on a finite return
and `valid=True`; each carries `estimable_replicates/fraction`. All-repeat
`undefined_count` and `unsupported_defined_count` preserve failure accounting.
For a nonestimable fit no value is imputed or dropped from the operational risk.
For an undefined Hajek (or empty-arm naive mean difference), no artificial error
is assigned: defined-run risk is conditional, with `defined_replicates/fraction`
and undefined count. Such a partially defined algorithm has no unconditional
finite risk claim from these summaries. No method-ranking plot should hide its
failure fraction or mix conditional-defined risk with unconditional regression
risk without the label. Pair outputs carry total/defined/valid pair counts;
supported-only paired differences condition on joint success.

Gaussian interval operational coverage uses all finite stored interval indicators;
its `_denominator` is explicit. `estimable_cover_*` and its denominator condition
on estimability. The naive/DIM estimator is fitted as own-treatment regression
and has the same stored HC3/oracle interval diagnostics as the other regression
outputs when both arms exist. Empty-arm DIM has no interval indicator. Full-
exposure HT and Hajek have no implemented intervals or coverage claim. Families
average per-graph conditional/operational metrics
with equal graph weight and retain their respective denominators/rates in the
graph table; conditional-support family averages do not redefine unconditional
risk. Oracle intervals keep their label. Approximate MC intervals are not a
remedy for heavy tails; exact HT risk is the risk comparison in rare-event cells.

SVD retains singular values strictly greater than eps_machine * max(n,k) * smax.
Endpoint contrast is estimable when absolute Euclidean projection residual
||c-proj_row(X)c|| <1e-8. Condition number uses all reported singular values,
so a rank-deficient matrix can have infinite condition even for an estimable c.
HC3 clips1-h only at1e-10 to avoid division by floating-point zero; this is a
numerical safeguard and not a validity repair. Empty treatment/control arms make
the declared naive difference undefined; its minimum-norm fit is not substituted.
Floating full-exposure probabilities may underflow for absent extreme-degree
events. Only observed nonzero exposure terms are divided; no probability/weight
truncation is introduced. Exact HT risk uses integer assignment-set intersections
and long-double exponents, with log10 output on float overflow. A truly observed
event whose inverse probability cannot be represented will be nonfinite and
reported as numerical failure, not a silently clipped estimate.

Production stream masters are2202601(core),2202602(noise),2202603(imbalance), as
settled by story. Pairing IDs include the actual master namespace. Models and
mechanisms within each cell share assignment/noise; different panels use
independent streams. Cross-panel contrasts must use independent-panel uncertainty,
while graph identity can still be matched for descriptive graph-level contrasts.
Pilot IDs predate the namespace field and are compared only within their cell.

## Aggregation corrections before production
Independent review found floating-point endpoint truth in family keys split
scientifically identical graph regimes; family/paired-family identity now excludes
derived truth, retaining actual per-graph truth/error and reporting truth_min/max.
The summary rejects duplicate graph/scenario rows rather than treating overlapping
checkpoints as extra graph realizations. All-undefined and single-defined-repeat
RMSE intervals retain NaN endpoints when their uncertainty cannot be computed.
Scientific checks exercise both defects and the actual pilot summaries are rebuilt.
These change aggregation, not any raw simulation estimate or target. Production
uses the corrected implementation. Source hashes are captured on module import
and verified unchanged before writing a checkpoint, guarding against a mutable
working tree during tracked execution. Early pilot hashes were read at completion;
its code-only delivery wrapper edits did not alter numerical primitives/results.

## Corrected rational support boundaries

The corrected production implementation counts treated neighbors before dividing by degree when computing one-hop exposure. This is mathematically Pz, but avoids accumulating normalized floating weights across a rational step boundary (60/80=.75 must activate threshold;17/20=.85 must not activate the hidden tail). Two-hop remains P applied to this one-hop exposure. Isolates retain own-treatment exposure. Every102-cell output and selected replay is regenerated with this source; old v1production is superseded as explained in exposure_boundary_correction.md. No scientific configs/graphs/seeds change. Complete final execution requires the new integer-inequality boundary audit in addition to ordinary arithmetic/checkpoint audits.

## Boundary rates and finite Monte Carlo certainty

An all-success/all-failure event fraction can have zero observed between-graph
variation, so its approximate graph t interval degenerates at0or1. This does
not prove an event impossible/certain under new assignments. Per-graph event
Wilson intervals remain available; the hidden-tail analytic union bound is
reported separately. No binomial pooling across heterogeneous graphs or
independence across methods/mechanisms is assumed. Raw Monte Carlo residuals
for b²+v are descriptive and can be unstable for spline errors; decomposition
checks do not require all pointwise intervals to cover zero.
