# Endpoint support versus predictive fit: implementation scope

## Status

This candidate has **not been executed or evaluated during preparation**. No
simulation numbers, measured runtimes, paper, template compliance, public-graph
confirmation, or improvement over the incumbent are claimed. The preparation
stage prohibits execution, network access, and writes outside candidate source
(apart from required append-only memory). This document is a protocol and
mathematical analysis, not a completed empirical paper.

The RPC prediction remains the starter's eight-feature regression with ridge
1e-4. Responses, endpoint conventions, and operation transitions are unchanged.
Internal diagnostics are never added to an RPC response. `study.py` is optional
offline research code; it is not imported by the RPC and adds no RPC dependency.
No held-out simulation-cell ranking study, public-graph experiment, official
conference paper, PDF, or checklist has been completed. These remain omissions,
not results. No outside literature has been accessed in this stage.

## Estimability and the two uncertainty ensembles

Write the observed design as X (n by p), and c as the average treated endpoint
feature row minus the average control endpoint feature row. All features stay in
their original, unstandardized coordinates. SVD retains singular values strictly
greater than eps64 * max(n,p) * largest singular value. The numerical estimability
test is ||c-X^+Xc|| <= 1e-8 max(1,||c||). Column scaling can change numerical rank;
near-boundary classifications should not be read as exact identifiability proofs.

If c is in row(X), y=X beta+epsilon with iid N(0,sigma^2) noise, and endpoint
means have the same coefficient beta, then c^T X^+y is conditionally unbiased
for c^T beta, with variance sigma^2 ||c^T X^+||^2. This follows by c^T X^+X=c^T
and the covariance sigma^2 I. Normality gives exact conditional Gaussian
intervals if sigma is known. With mean-zero iid non-Gaussian noise the variance
identity still holds but the Gaussian interval need not have exact coverage.

If c is not estimable, there is a null-space direction v with Xv=0 but c^T v
nonzero. The observed linear means do not identify the contrast. A finite
pseudoinverse coefficient is not a resolution. Code returns explicit status and
JSON null variance, not Infinity. Zero or finite ridge variance does not resolve
this identification failure either. The reset check covers full rank, deficient
but estimable, and deficient/nonestimable matrices. Fits call the diagnostic on
the actual feature matrix; the optional study also fits OLS explicitly.

For omitted response r(z), let r_obs be its observed vector and r_delta its
average all-treated minus all-control value. Under estimability the extra bias
is c^T X^+ r_obs - r_delta. A small held-out prediction error for r_obs imposes
no bound on unsupported r_delta. If nonestimable, even the linear component
also contributes -c^T(I-X^+X)beta. The noise calculation alone bounds none of
these terms. The RPC unit-noise diagnostic sets sigma=1 as a reference scale;
it does not estimate the true uploaded noise or compute ridge-fit uncertainty.

In the study, node covariates and iid unit shocks are drawn once per graph cell,
then held fixed across assignments and paired response worlds. Repeated
assignment errors are therefore finite-population randomization errors. Their
Monte Carlo coverage is reported empirically; the conditional outcome-noise
formula does NOT prove that coverage. Ridge intervals additionally omit
shrinkage bias; misspecified-model intervals omit model bias.

## Paired stress mechanism and isolates

The base synthetic response is

    1 + 0.5*x_i + z_i + 0.75*e_i + 0.25*z_i*e_i + shock_i.

Here e is the fixed RPC feature: mean neighbor treatment, zero for isolates.
The paired response adds z_i * [max((q_i-0.8)/0.2,0)]^2, with q=e except
q=z for isolates. This separate *response* convention makes the truth gap one
even for isolates without changing the regression feature contract. In the
base response the e coefficient remains based on the zero-isolate encoding, so
the base response is in the declared fitted span. All endpoint truths are
computed by calling the response functions with fixed x and shocks.

The positive-part-square bump is C1, not C-infinity or C2 at its threshold.
It is a declared synthetic endpoint stress test, not an assertion about real
social effects. At reset/fit the checks exercise no generated experiments:
fit checks this pair on the supplied topology and assignment, with zero
synthetic shocks and tanh(x) as a bounded synthetic covariate to avoid
cancellation in its truth check. This uses neither hidden endpoint outcomes nor evaluator
information. The optional study uses fixed iid shocks instead.

On E = {no treated unit has q>0.8}, paired observed outcomes coincide exactly.
The algorithm sees identical inputs under a coupling using the same algorithm
randomness. Its output T then satisfies

    ((T-tau)^2 + (T-(tau+delta))^2)/2 >= delta^2/4.

Integrating over E, the average two-world squared risk, and hence the maximum
world risk, is at least P(E)*delta^2/4. This is a two-world risk statement, not
a claim that both worlds have that lower bound individually. For independent
Bernoulli(p) assignment on a fixed simple graph, the probability that a
positive-degree node activates the bump is

    p * Pr(Binomial(degree_i,p) > 0.8*degree_i).

For isolates it is p. A union bound gives P(E) >= max(0,1-sum_i P(activation_i)).
No independence of node exposures is assumed. The bound is often vacuous at
low degree. It is NOT applied to cluster assignment. Actual no-bump event
frequencies and active counts are retained even when they contradict the
endpoint-indistinguishability hypothesis. Exact equality is not asserted when
any bump activates. An oracle bump column is itself nonestimable if never
activated: its zero observed column does not identify its nonzero endpoint.

## Optional study and reproducibility

No additional dependency is needed for the RPC. The optional runner uses
NetworkX in addition to NumPy and SciPy. A prospective pinned environment is
Python 3.11, NumPy 1.26.4, SciPy 1.13.1, NetworkX 3.3; these versions have not
been installed or verified here. Actual versions and source SHA256 hashes are
recorded when the runner completes. No package manager was invoked.

From the candidate directory, a future permitted execution is:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/study.py --output src/study_output

The default planned grid is n=2000, degrees 8/32/128, graph seeds 1103/2207/3301,
200 independent assignments per fixed graph. Counts are planned, not completed.
An optional robustness run adds `--families regular sbm ba --cluster` and uses
a distinct output directory. Runtime is unmeasured; a smaller prospective pilot
can set `--repetitions 2 --graph-seeds 1103` before committing to the full grid.
Existing output directories are refused, not overwritten. No script runs
automatically as part of this preparation.

Regular graphs are generated by NetworkX random_regular_graph, not assumed
uniform over regular graphs. BA uses m=degree//2, so mean degree is only matched
approximately. SBM has 20 contiguous blocks with expected 75% within-block
degree and 25% across-block degree (exact nominal mean match for equal block
sizes; the runner requires n divisible by 20 for SBM). Bernoulli assignment is p=0.5. Optional cluster assignment randomizes
these 20 blocks independently at p=0.5 on the same graph and population. Any
effect combines changed endpoint support and fewer independent randomization
units; this is not a support-only intervention. Seeds, realized mean degree,
edge hash, population seed sequence, and assignment-unit count are retained.

Each assignment is reused for linear, paired-bump, and a visible quadratic
control response (base + 0.5*e^2). Methods are difference in means, linear
exposure OLS (with own-neighbor interaction and x*z), quadratic OLS (the RPC
feature map), validation-tuned ridge on the same map, and an explicitly
oracle quadratic-plus-bump OLS. Ridge is selected from a declared grid using
fixed three-fold node validation, which does not represent out-of-network
generalization. Oracle results are diagnostics, not a deployable advantage.

`replicates.jsonl` retains every completed or failed method/world/assignment
record. `summary.json` is grouped by fixed graph, world, method, and design;
it does not pool graph variation with Monte Carlo assignment uncertainty.
Bias measures direction of error, RMSE penalizes large endpoint errors,
coverage and length describe assumption-labeled intervals, and validation MSE
is ordinary observed prediction loss. Bias MCSE uses sample standard deviation;
RMSE MCSE uses the delta method; the associated normal-approximation intervals
can be poor with very few repetitions or heavy tails. Coverage MCSE is the
binomial plug-in and is zero at empirical 0/1; this does not prove no uncertainty.
Undefined intervals count as uncovered and have a separate defined-rate report.
Failed fits are explicitly counted and excluded from error means, not silently
imputed. `diagnostic_checks.json` contains analytical checks, and
`provenance.json` contains arguments, versions, elapsed time, hashes and graphs.
No paper figures or tables are generated, so there is no completed figure/table
mapping. The record stream allows later paired-method or held-out-cell analyses,
but such analyses and their claims are deliberately not reported as completed.
