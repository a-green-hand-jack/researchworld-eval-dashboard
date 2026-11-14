# Quadrature Bayes-risk selection

## Status, scope, and interface

This candidate isolates a selector hypothesis: under an already selected
Gaussian mixture, can outcome-integrated bounded absolute-risk transfer beat
the predecessor's variance or square-root-variance selector? It does not change
the factor/mixture candidate grid, observed-data likelihood, conditioning rule,
or returned posterior predictions. `METHOD.md` documents those inherited parts.
The single-Gaussian prediction path still calls the original Gaussian routine,
including its tiny solve jitter; the acquisition working covariance uses the
inherited sequential conditioning rule without that solve jitter.

`program_spec.toml`, `covariance.py`, RPC operations, response keys, types,
encodings, checkpoint semantics, and authorized observation handling are
unchanged. Only historical matrix/mask values, legal availability, and revealed
scores inform decisions. Opaque identifiers have no semantic use. No target
mask, model family, evaluator loss, external control, or new RPC field is assumed.
Dependencies remain NumPy and the Python standard library.

No project code, tests, benchmarks, evaluation, or numerical checks were run in
this editing stage. No external material was accessed. The harness performs
the official evaluation after exit. There are no measured gains, selected-K
results, timings, completed data experiments, or completed paper in this change.
The runtime validation described below is implemented, not already executed.

## Bounded median and analytic absolute risk

For current component weights pi_g, conditional means m_g,t, and shared
conditional standard deviations s_t, the optimal action under absolute loss
restricted to [0,1] is the mixture median projected into that interval.
`bounded_mixture_median` uses the predecessor's 25 CDF bisections on [0,1].
For one component it directly clips the component mean. The same routine now
serves multi-component RPC prediction and acquisition risk, with optional
leading outcome batches. Standard deviations are floored at 1e-7.

Writing a_t for this action and z_g,t=(a_t-m_g,t)/s_t, the exact working-model
absolute risk (up to the median solve and numerical floors) is

    R_t = sum_g pi_g [2 s_t phi(z_g,t)
                      + (m_g,t-a_t)(1-2 Phi(z_g,t))].

This follows by integrating the normal density on either side of a_t. It is
not the absolute deviation of the mixture mean, nor a moment-matched Gaussian
approximation. Clipping constrains the action, not the Gaussian outcome model.

## Outcome integration and legal shortlisting

For candidate j with within-component variance v_j, cached order-q Hermite
nodes h_l and weights w_l produce outcomes and masses

    y_g,l = m_g,j + sqrt(2 v_j) h_l,
    p_g,l = pi_g w_l / sqrt(pi).

The default is q=3. Query variance is floored at 1e-12, matching the inherited
conditioning denominator. Every node clones the row's weights, means, within
and panel covariance arrays, observed/value lists, and diagnostics dictionary.
The fitted model is shared read-only. `clone_conditioned_row` then calls the
same `reveal` used for real observations, including the component likelihood
reweighting and shared Gaussian rank-one update. Hypothetical scores are not
authorized observations, never persist in the live row, and never cause RPCs.
Multi-component posterior risks batch all outcomes and targets; the K=1 path
uses the direct clipped-median formula at each node.

The utility is

    U(j) = sum_{t not in observed union {j}}
           [R_t - sum_g,l p_g,l R_t(after observing y_g,l at j)].

Every unobserved column except j contributes, including unavailable columns.
Neither the direct benefit of measuring j nor any assumed audit mask is
credited. All calculations use the current row's fitted predictive law.
Negative finite quadrature utilities are retained rather than silently clipped.

Legal unqueried candidates are sorted by the inherited square-root-variance
transfer heuristic, which also excludes observed columns and the candidate
itself. Keep its top four and always include the predecessor's selected column
(variance or square-root, as historically chosen). The union has at most five
columns. Integrated utility reranks only that union; exact ties use the lowest
column index. With one legal candidate the predecessor is returned directly.
Nonfinite integrals or caught numerical exceptions return the predecessor.
There is no unconstrained-Gaussian shortcut in the bounded-action policy.

## Historical selector gate

The predecessor's historical train/validation row split, fixed audit columns,
rank/shrinkage/component/regularization grid, and initial configuration rule
are retained. All scaling, factors, and mixture parameters use training rows
only. Train/validation indices are asserted disjoint. Audit cells are excluded
from every validation query pool and used only for error computation.

After selecting the predecessor configuration, reuse its cached training fit
and replay only quadrature; its incumbent replay is already cached. No new
distribution is fitted for the comparison. Both policies use identical row
identities, audit targets, legal query pools, feasible budgets, and checkpoints
{1,2,4,8} plus the feasible final budget (at most eight). Row identities,
checkpoint lists, and target counts are asserted aligned. Each row's MAE
averages checkpoints on its same fixed observed audit cells.

For aligned rows i let d_i=MAE_quad,i-MAE_incumbent,i. With at least two rows,

    SE = std(d, ddof=1)/sqrt(number of rows).

Use quadrature only if mean(d)+SE < 0, every difference is finite, and no
quadrature numerical fallback occurred in the replay. Otherwise retain the
predecessor, including small-history and insufficient-validation fallback
paths. This gate is additional to, not a replacement for, the inherited
distribution/configuration gate. Selected distribution parameters are refitted
on all supplied historical rows; only an accepted selector is carried over.
A failed final mixture fit still invokes the original single-Gaussian fallback.

Internal records retain paired row deltas and SE, component count, chosen
selector, query paths, checkpoint errors, number of matching query positions,
numerical fallback counts, and measured replay/selection elapsed times once
run. They also distinguish a gate decision from application after final refit.
They are not response fields, stdout messages, or prefilled result artifacts.
One-SE selection is a conservative heuristic, not a significance test: the
same validation rows also selected the predictor, historical models may be
dependent, and no independent family/temporal generalization is established.

## Reference limit, cost, and untested limitations

For one unconstrained Gaussian, the posterior absolute-loss Bayes risk is
sqrt(2/pi)*s_t. Gaussian conditioning makes posterior variance independent of
the revealed value; hence the exact expected transfer is sqrt(2/pi) times
summed square-root-variance reduction, excluding j and already observed tasks.
This follows from E|N(0,s_t^2)|=sqrt(2/pi)*s_t and the Gaussian Schur complement.
It is a reference identity, not a verified numerical result here. Bounded
actions break that simplification whenever clipping binds. In particular,
value adaptation for K=1 would not demonstrate latent-profile identification.
The copied-state construction structurally isolates hypothetical updates;
its numerical state-invariance and Gaussian-limit checks remain unexecuted.

With shortlist S<=5, K<=4, q=3 and N<=128, each acquisition uses at most S*K*q
hypothetical updates, each O(N^2+K*N), and 25-step vectorized median solves.
Outcome batches use O(q*K^2*N) memory plus row/covariance copies. Rule nodes
are cached; K=1 has no CDF bisection cost. Only one extra validation replay is
added after predictor tuning, with no extra training fits. These are operation
bounds, not measured runtime or a guarantee of fitting the harness deadline.

Order three and a four-item shortlist are computational defaults, not measured
optima. Nonlinear posterior risks can require higher-order integration; the
shortlist can omit the best candidate. Order-five/shortlist sensitivity,
boundary sensitivity, CPU measurements, and paired outer-row uncertainty are
not completed. Gaussian tails deliberately generate nodes outside [0,1];
silently clipping nodes would change the integration measure. Real scores are
bounded, so that working-model support mismatch can bias acquisition,
particularly near boundaries. There is no exact-optimality claim. Sparse or
nonrandom missingness, model shift, weak multimodality, correlated historical
rows, shared within-component covariance, and validation selection noise can
make this policy ineffective or worse. A selected single Gaussian, rejected
gate, identical queries, or numerical fallback is an honest no-op/negative
outcome, not evidence of a mixture or quadrature gain.
