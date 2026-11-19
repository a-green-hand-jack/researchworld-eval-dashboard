# Endpoint-contrast audit candidate

The RPC operations, response keys, encodings, shapes and baseline ridge
predictions are unchanged. `program.py` calls its internal audit on each
fit. The entrypoint remains self-contained. All diagnostic state is private
and reset clears it. There are no
new inputs, filesystem outputs, model selectors or simulated observations.

## Implemented

The all-treated minus all-control feature contrast is constructed from
the supplied graph, including the starter's isolate convention. Observed
design columns and contrast coordinates are normalized by the same column
norms before the OLS audit. It checks row-space estimability, records rank
and residual, and computes contrast-specific noise and approximation gains.
Nonestimable contrasts retain algebraic pseudoinverse diagnostics but have
no variance or bias certificate. A rank-deficient design can still have an
estimable endpoint contrast; full parameter identification is not required.

The independent-noise OLS identity and the uniform-approximation bias bound
are documented in `program.py`. Neither the noise variance nor the
uniform residual envelope is estimated or assumed verified. For the actual
ridge fit, separate weights give its unit-noise variance multiplier and
its nonzero linear-reference contrast defect. Thus an OLS certificate is
not silently applied to ridge; even an exactly linear reference may incur
ridge bias through that defect. Correlated noise requires w.T Sigma w.

A fixed width-0.2 squared positive-part bump describes support at observed
neighbor exposure. The function is C1, not globally C2, and its interior
second derivative is 2/width**2. For isolate-free graphs its endpoint gap
is one. Isolates have zero neighbor exposure at both endpoints and invalidate
that universal gap claim. The audit records their count. It does not infer
the assignment design or compute a Bernoulli probability for an unknown
design. Exposure support is not evidence of the true outcome mechanism.

## Analytical witness, not an executed experiment

Fix two mechanisms before assignment, f1=f0+delta*b_h(e), on an isolate-free
graph, with common assignment and independent common Gaussian noise. On
H={max(e)<=1-h}, the observed data agree exactly, while GATEs differ by delta.
For the same estimator in both worlds, its two squared errors on H sum to
at least delta**2/2. Integrating and taking the larger world risk yields
max(R0,R1)>=P(H)*delta**2/4. This concerns that specified model class and one
experiment, not an unrestricted smoothness-free impossibility theorem.
Under independent Bernoulli(p) only, a union bound gives
P(H)>=max(0,1-sum_i P[Binomial(d_i,p)>(1-h)*d_i]). This may be vacuous and
does not apply to cluster assignment without a separate derivation.

## Not performed

Stage restrictions prohibit executing candidate code, tests, simulations,
network retrieval, benchmarks and evaluation. The RPC has no experiment
controls, endpoint truth, assignment-design probabilities or artifact
exchange. Consequently no paired-world study, variance calibration, complete
graph test, public-graph study, replicate archive, empirical RMSE/bias table,
Monte Carlo uncertainty, paper PDF or official-template retrieval is claimed.
No metric improvement is claimed. The starter estimator is intentionally
preserved rather than modified on the strength of unperformed experiments.

This candidate is an internal analytical audit, not a completed research
paper or an empirically validated new estimator. The proposed simulation
study requires a separately authorized execution and artifact interface.
