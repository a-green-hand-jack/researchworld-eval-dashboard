# Target-risk residual covariance candidate

The RPC and `program_spec.toml` are unchanged. Only NumPy and the Python standard
library are required, as in the starter. All scores arrive in [0,1]; task names
are opaque, and no data downloads, family inference or score extraction occurs.

## Fit and prediction

The historical matrix is split deterministically by rows using the reset seed.
Ranks 2, 4 and 8 (subject to dimensions) and residual prior strengths 2 and 12
are selected using held-out historical models. Training means and scales use
observed training cells only. A fixed random third of tasks supplies validation
targets; these tasks cannot be probed, so hyperparameters are compared on the
same observed targets. Validation averages model-level MAE over budgets
1, 2, 4 and 8 when feasible, including the final feasible budget. Afterwards,
the chosen model is refitted on all historical rows, never on new query rows.
Very small historical matrices use a fixed configuration without validation.

The model is x = mu + L z + epsilon, with z standard Gaussian and independent
Gaussian task residuals of positive diagonal covariance D. Missing-data EM
computes exact latent posterior means and second moments from observed cells,
then updates each task's intercept, loading and expected residual error. A
zero-filled SVD initializes loadings only. Residual variance has a positive
floor and a weak prior in standardized coordinates. Transforming back gives
C = L L^T + D in raw score units. No imputed cells enter the likelihood.
Prediction is mu_T + C_TO solve(C_OO, x_O - mu_O), with a tiny numerical jitter,
then clipped to [0,1]. D enters C_OO once, not as extra measurement noise.

## Selection and Gaussian identity

After conditioning on selected tasks, let C denote remaining conditional
covariance. Querying j decreases the conditional variance of another task t
by C_tj^2 / C_jj. The selector sums this over every remaining task except j.
Available candidates use an explicitly zeroed diagonal; unavailable tasks
remain targets, but can never be probes. Raw-unit covariance makes all target
weights one; equivalently standardized coordinates would need scale-squared
weights. Ties choose the smallest index. The conditional covariance update is
C <- C - C_:j C_j: / C_jj, using a copied column. Every row starts fresh.
This is a nested, covariance-only, value-nonadaptive panel conditional on its
eligibility mask, not a deterministic common panel across different masks.

The identity assumes a correctly specified joint Gaussian and exact revealed
scores. It is a one-step reduction on the same remaining targets, not a global
optimizer of changing-complement error: querying j also removes j's own error
from the scored complement. Neither MAE optimality under misspecification nor
real-data improvement follows from this identity. Heterogeneous residuals
discourage task-specific variation from being treated as transferable signal.

## Scope and unperformed work

The API supplies historical scores/masks, opaque task tokens, per-row query
eligibility and authorized revealed values. It supplies no model identifiers,
family labels, chronology, outer split IDs, test target masks, or truth for
unrevealed entries. Held-out historical row indices above are not external
test identities. No unknown cell is a validation label. External availability
may encode an audit exclusion, but its cause is not inferred here.

Internal fixed-target validation is implemented; the requested external
fixed-target audit, matched random/D-optimal controls, ablations, paired
bootstrap, real-data study, paper and gain-identity experiment are not run or
claimed. The harness owns outer test separation and scoring. No evaluator,
test, benchmark or optimizer code was inspected or executed. No performance
result, universal sufficient budget, missingness-identification result or
family-shift guarantee is asserted. The candidate awaits the official gate.

Runtime scales approximately as sweeps times (M N r^2 + (M+N) r^3) per fit;
the small validation grid has six configurations and at most twelve sweeps
per configuration. Memory is O(M N + M r^2 + N^2), excluding the upload buffer.
Selection uses O(N^2) per revealed task, and checkpoint predictions solve a
system of size equal to the number of revealed tasks. No runtime was measured.
