# Score-adaptive latent mixture candidate

This implementation uses only the documented normalized historical matrix and
mask, the training allowance, query budget, per-row availability, and purchased
scores. Names are not used. Seeds control ordinary numerical initialization and
row/panel randomization; they never identify a workload. No filesystem or network
access occurs in the candidate.

## Fitting and prospective validation

Masked alternating ridge least squares estimates task intercepts and loadings.
Missing transport zeros never enter observed-entry objectives. Residual variance
is shrunk toward the observed-entry pooled residual variance. Completely unseen
columns use the training-only global mean, zero loadings and pooled noise; an
entirely empty history uses mean 0.5. The latent prior is a regularized Gaussian
mixture with at most four components. Empty historical rows do not fit its prior.
These are approximate empirical-Bayes row factors, not known latent variables.

A seeded holdout of at most twelve historical rows is excluded from intercepts,
loadings, noise and mixture fitting. Eligible holdout rows have at least two
observed cells. The predeclared configuration order is task means, then
(rank, components) = (1,1), (3,1), (3,2), (6,1), (6,2), (6,4).
The training allowance caps the number of non-baseline proposals; ranks are
bounded by inner matrix dimensions, and mixture counts by supported row count.
Each rank shares its fitted factors across its component-count alternatives.
Inner ALS uses at most five sweeps; the selected full-history refit uses at most
eight. EM uses at most twelve iterations. Small histories without a viable row
holdout use task means rather than claim evidence for adaptation.

Replay queries only genuinely observed held-out cells, with at least one cell
left unqueried. Checkpoints are unique feasible values of {0,1,2,4,budget}.
Loss averages checkpoint MSE within rows and then rows, excluding purchased cells.
Configuration selection precedes the final full-history fit. Splits are row-
disjoint, not family-disjoint. Missingness and small holdouts can bias selection.
Plug-in row factors ignore their estimation uncertainty; apparent mixture
structure can reflect uneven coverage rather than distinct performance profiles.

Internal diagnostics compare adaptive, score-free frozen-plan and random queries
under the selected predictor. A same-factor single-Gaussian control predicts on
identical purchased queries and target cells; it also has its own adaptive replay.
Frozen plans advance an independent planning posterior with its predicted mean,
never with actual purchased scores. Additional fixed-panel diagnostics split
observed cells into disjoint query and target panels. The latter are never
purchased. These diagnostics use at most four held-out rows, are not independent
test estimates and must not be reported as outer evaluation or pinned-public-data
experiments. They remain in RAM and never extend RPC responses.

## Posterior and acquisition derivation

For component h, z ~ N(m_h,C_h), and y_j = a_j + b_j^T z + e_j with
independent e_j ~ N(0,s_j). Define v_hj = s_j + b_j^T C_h b_j,
u_hj = y_j - a_j - b_j^T m_h. Bayes' rule multiplies component weights
by exp(-u_hj^2/(2 v_hj))/sqrt(v_hj). Conditional Gaussian updates give
m'_h = m_h + C_h b_j u_hj/v_hj and
C'_h = C_h - C_h b_j b_j^T C_h/v_hj.
All likelihoods and gains use pre-update moments. Every context owns copies of
all posterior arrays; hypothetical observations also use copies.

Let T be a fixed target panel excluding candidate j. Under squared error the
Bayes risk is R_T = sum_t Var(y_t | D). The law of total variance gives
R_T - E_yj R_T(D,y_j) = sum_t Var_yj(E[y_t | D,y_j]).
This exact identity is conditional on the fitted probabilistic model, without
clipping. Writing G_T = sum_t b_t b_t^T evaluates R_T as
tr(G_T Cov(z | D)) + sum_t s_t without materializing target covariance matrices.

The shortlist uses the moment-matched off-diagonal covariance approximation
sum_{t in T} Cov(y_t,y_j)^2 / Var(y_j). At most eight candidates are integrated
using three-point Gauss-Hermite quadrature per predictive mixture component;
both mixture and quadrature weights enter the expectation. Candidate-excluded
targets are identical before and after every simulated outcome. With K=1,
conditional covariance does not depend on the purchased score, and the formula
is exact, so acquisition directly uses its score-independent analytic value.
Internal replay also computes three- versus nine-point gains for one query,
compares the single-Gaussian analytic gain with quadrature, and records the
covariance difference after two distinct hypothetical scores under K=1.
Clipping, approximate ALS, empirical priors, shortlisting, quadrature and MNAR
missingness break any interpretation as a general frequentist optimality result.

Per live mixture query, shortlisting costs O(N r^2 + K N r^2), followed by at
most 8*3*K small posterior updates and latent-risk evaluations. No dense N by N
covariance is needed. Contexts are independent and purchased values are copied
back exactly after clipping predictions to [0,1].

## Stage status

No candidate code, tests, public-data experiments, quadrature checks or official
evaluation have been executed during this implementation-only stage. The checks
and replay comparisons above are implemented runtime paths, not measured results.
The unchanged program specification exposes `program.py:handle`. The harness
owns execution and acceptance. No paper, performance number, confidence interval,
or completed public-data study is claimed by this candidate submission.
