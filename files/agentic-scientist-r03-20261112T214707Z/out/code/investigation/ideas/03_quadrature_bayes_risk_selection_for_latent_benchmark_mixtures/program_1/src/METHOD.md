# Inherited latent-mixture design

This document records the predecessor's fitting, prediction, and selection
design. The active candidate keeps its distribution-fitting and prediction
rules, but adds the acquisition and historical gate in `QUADRATURE.md`.
That document supersedes the selector, selector-validation, and selection-cost
claims below. In particular, bounded-action quadrature can be value-adaptive
even for one Gaussian; such adaptation is not mixture-profile inference.

## Status and boundaries

This is one candidate implementation, not a completed empirical study or paper.
No candidate, test, benchmark, evaluation, optimizer, network request, or project
code was executed during this implementation stage. There are no new measured
losses, gains, timing measurements, validation artifacts, or scientific claims
of improvement. The harness will perform the only official evaluation later.
The broader paper/PDF, external data study, and reproducibility experiments are
not completed here; stage-specific instructions require stopping at a ready
candidate. No outside literature was accessed, including prohibited material.

`program_spec.toml` and the entire incumbent `covariance.py` are unchanged.
`program.py` retains the documented JSON operations, keys, shapes, encodings,
checkpoint-only predictions, fused selection/observation transitions, and
reset semantics. `mixture.py` implements the new fitting and row inference.
Dependencies remain NumPy and Python's standard library. No family labels,
task semantics, chronology, evaluator seeds interpreted as identities, outer
targets, external data, or unobserved scores are used. Seeds initialize only
the historical split RNG. The row token is not used as predictive information.

## Hypothesis and model

A covariance-only Gaussian panel depends on query indices and availability,
but not revealed values. Specialization profiles might make score values
informative about which remaining tasks are transferable. We test this within
the supplied interface by retaining the incumbent as a candidate and extending
its latent prior; heterogeneity and improvement are hypotheses, not findings.

First fit the incumbent observed-data factor model

    x = b + W z + epsilon,  epsilon ~ N(0,D),  z ~ N(0,I).

Observed training entries alone determine centering, scaling, W, and diagonal
D. Missing entries are never likelihood terms or labels. Freeze b, W, D and fit

    p(z) = sum_g pi_g N(z; a_g, tau_squared I), K in {2,4}.

The score-space components have means b+W a_g and common covariance
V=tau_squared W W^T+D. K=1 is explicitly the original N(b, W W^T+D),
not a fitted one-component approximation to this extension. Its prediction
calls the original clipped conditional-mean implementation, including its
numerical jitter. Its variance selector and covariance updates also match the
incumbent. All original fitting and validation code remains available unchanged
for invalid or insufficient-validation fallback.

## Observed-data mixture EM

For row i with observed set O, let

    A_i = W_O^T D_O^-1 W_O,
    h_i = W_O^T D_O^-1 (x_O-b_O),
    S_i = (A_i+I/tau_squared)^-1,
    m_ig = S_i (h_i+a_g/tau_squared).

Responsibilities use the observed-score marginal normal density with mean
b_O+W_O a_g and covariance tau_squared W_O W_O^T+D_O, evaluated by the
determinant lemma and Woodbury identity. The likelihood has no imputed-score
terms. EM integrates E[z z^T|x_O,g]=S_i+m_ig m_ig^T, including S_i even for
highly incomplete rows. Rows with no observations are omitted from mixture
fitting rather than inventing evidence. Initial centers come only from the
training latent posterior means under N(0,I), using deterministic farthest
centers and six assignment passes. These means initialize, not replace, the
observed likelihood.

With N informative rows, responsibility masses n_g, first moments s_g and
second moments Q_g, regularization lambda gives

    pi_g = (n_g+1)/(N+K),  a_g = s_g/(n_g+lambda),
    R = sum_g [tr(Q_g)-2 a_g^T s_g+n_g ||a_g||^2],
    tau_squared = [R+lambda (sum_g ||a_g||^2+r)]/[r(N+K+lambda)].

This corresponds to symmetric Dirichlet mass smoothing, a conditional normal
center prior, and a variance shrinkage penalty. Tau squared is constrained to
[0.08,2.5]. Tiny component centers shrink toward zero and masses stay positive.
Lambda is selected from {2,8}. Each profile fit uses at most min(sweeps,12)
passes; it requires at least max(16,4K) informative rows. Observed unpenalized
likelihood history is retained internally, but monotone unpenalized likelihood
is not promised under regularization and constraints. Numerical failures skip
that configuration; a failed final refit restores the original Gaussian.

## Exact row conditioning and L1 prediction

Every row_start independently copies prior component weights, means, and V.
There is no accumulation of evidence across query rows. Revealing x_j=v gives

    pi_g' proportional to pi_g exp(-(v-m_gj)^2/(2 V_jj)),
    m_g' = m_g + (v-m_gj) V_:j/V_jj,
    V' = V - V_:j V_j:/V_jj.

The common normalizing factor cancels in the weights because all components
share V. Log-space weight normalization avoids likelihood underflow. Only the
shared WITHIN covariance receives this exact Gaussian conditioning update.
Observed coordinates are set exactly and their covariance rows/columns zeroed.

For each unqueried task t, prediction is the mixture marginal median, obtained
from sum_g pi_g Phi((q-m_gt)/sqrt(V_tt))=1/2 by 25 vectorized bisection steps
on [0,1]. Phi uses standard-library erfc; conditional standard deviations have
a 1e-7 floor. A median minimizes expected absolute loss: a subgradient of
E|X-q| is 2F(q)-1 at continuity points. Constraining q to [0,1] clips the
unconstrained median, including cases where all bisection values lie on one
side of 1/2. Gaussian support outside [0,1] is not discarded or renormalized;
this is a constrained action, not a truncated-distribution model. Bisection
has interval width 2^-25 in score units. This optimality is under the fitted
distribution only, not a guarantee about real score MAE. Revealed entries are
copied exactly before the usual finite little-endian float32 response encoding.

## Selection: an approximation, not exact information gain

After real observations recompute the posterior total covariance

    C = V + sum_g pi_g (m_g-mbar)(m_g-mbar)^T.

For legal candidate j use the moment-matched Gaussian heuristic

    gain(j) = sum_{t not observed, t != j}
              [sqrt(C_tt)-sqrt(max(C_tt-C_tj^2/C_jj,0))].

For a Gaussian, expected centered absolute error is proportional to standard
deviation, motivating this objective. For a mixture it is neither exact MAE
reduction nor exact expected information gain, and it is not globally optimal
planning. Candidate self-gain and already queried targets are explicitly zero.
All other columns, including unavailable columns, remain prediction targets;
only supplied available, unqueried columns may be selected. Ties use sorted
column indices. The original summed variance-transfer selector is also tuned.

Value dependence follows directly from the exact weight update: with distinct
component means at j, the log posterior odds are an affine function of v,
with slope (m_gj-m_hj)/V_jj. Posterior between-component uncertainty, and hence
the next heuristic score, can therefore change with the revealed value. This
does not guarantee different choices for every row or dataset. K=1 still has
the original covariance-only, value-nonadaptive panel. No empirical replay
result is asserted before execution.

The value-blind ablation uses the same fitted mixture and exact posterior
predictor, but selects using an initial total-covariance panel that receives
value-independent Gaussian rank-one updates. That covariance is ONLY a panel
approximation, never the exact mixture posterior used for predictions.

## Historical validation and recorded ablations

The same seeded row split and fixed random third of audit tasks as the
incumbent are used. Train and validation row indices are asserted disjoint.
Each usable validation row has at least one observed audit target and one
observed non-audit query candidate. Audit targets remain fixed at all compared
budgets and are excluded from every query pool. Preprocessing and every model
parameter are fitted on training rows only. Audit truth is read only for loss.
Scores at unknown cells are never labels. Insufficient validation (fewer than
six usable held-out rows), invalid selection, or tiny historical matrices
invoke the unmodified incumbent fitting procedure.

First select the original ranks {2,4,8} and residual strengths {2,12}, using
at most twelve factor passes per configuration, exactly the incumbent grid.
Freeze the winning training fit for the profile experiment. Then compare
K={1,2,4}, lambda={2,8} for K>1, and variance/square-root transfer. Each row's
loss averages feasible budgets {1,2,4,8} plus its final feasible budget; the
objective averages rows, not cells. A non-incumbent choice must improve MAE
over the original Gaussian by more than max(0.0001,0.5 paired standard error).
This is a conservative selection heuristic, NOT a corrected significance test
or independent evidence of generalization. The lowest eligible validation MAE
wins. The selected configuration is then refitted on all uploaded rows using
the supplied factor sweep budget and at most twelve additional mixture passes.

Fitted objects retain genuine runtime-only `validation_records_`,
`validation_choice_`, and `validation_split_`. These contain row IDs, fixed
target counts, budgets, query sequences, per-checkpoint/per-row errors,
configuration choices, skipped-fit reasons, paired differences and standard
errors. They are internal state, never additional RPC fields, stdout messages,
or prefilled evidence files. They do not exist as measured artifacts yet.
The mean/median ablation uses the same mixture posterior and identical queries.
K=1 versus mixture is paired under each identical selector. For the best
validation mixture, a value-blind panel replay uses the same fit, availability,
audit targets, budgets, and posterior predictor as the adaptive replay.
Paired row-level uncertainty is descriptive: related historical models and
selection on these same rows can make it optimistic. No independent family,
temporal, missingness, or external dataset split is implied by this interface.

## Cost and limitations

The incumbent factor fitting cost is unchanged: approximately
O(sweeps (M N r^2+(M+N)r^3)) per factor fit, six validation configurations plus
one final fit. Gram matrices are cached for mixture fits; each mixture pass
costs O(M(r^3+K r^2)), after O(M N r^2) observed-statistic construction.
There are at most four training profile fits plus one final profile fit.
Runtime validation compares up to ten additional predictor/selector settings
including the blind replay. Each selection costs O(N^2+K N^2), conditioning
O(N^2+K N), and a median checkpoint O(25 K N) CDF calls. Memory is polynomial
in the supplied small matrices, O(M N+M K r+M r^2+N^2). No timings were run.

Shared within covariance and fixed W,D can miss genuinely different local
correlations; few observations can leave profile assignment ambiguous. Tiny
components, sparse or selectively reported scores, near-identical profiles,
out-of-support new models, and nonrandom missingness can erase or reverse
gains. Clipping, priors, and floors are numerical/modeling choices, not
identification results. The staged validation grid does not jointly retune
factor loadings for every mixture and is itself subject to selection noise.
An explicit K=1 choice is a scientifically valid negative outcome. There is no
claimed universal sufficient k, real-data superiority, theoretical planning
optimality, or completed paper/reproducibility study.
