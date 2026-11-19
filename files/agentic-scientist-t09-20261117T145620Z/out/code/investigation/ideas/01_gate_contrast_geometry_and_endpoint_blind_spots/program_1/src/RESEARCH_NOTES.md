# Contrast geometry: implemented scope

This candidate is a protocol-compatible estimator, not a completed simulation
study or paper. It uses only the uploaded edges, covariates, assignment,
outcomes and block labels. No experiments were run while preparing it.

## Endpoint geometry

The endpoint contrast is the difference of the mean all-treated and
all-control feature rows. Endpoint exposures are recomputed from the graph,
so isolates retain zero neighbor exposure. For an observed fixed design
`F = U S V'` and contrast `c`, the code checks whether `c` belongs to the
retained row space. The SVD cutoff is `1e-12 * largest_singular_value`, matching
the interface's least-squares convention; rank sensitivity is recorded at
one tenth and ten times this cutoff. The null-space tolerance is relative to
the contrast norm. These are numerical, not statistical, support checks.

If `c` is estimable and `E[y | F] = F beta`, then
`c' F+ y - c' beta` has conditional variance
`sigma^2 sum_j ((v_j' c) / s_j)^2` under independent homoskedastic noise.
This is a directional quantity, not the condition number of all of `F`.
If `c` is not estimable, the pseudoinverse selects an arbitrary representative
of observationally equivalent coefficients; the diagnostic returns no finite
variance certificate. A finite ridge estimate does not resolve this problem.
The code uses unit-noise geometry, not an assumed known outcome variance.
No confidence intervals are returned or claimed. Exact Gaussian t inference
would additionally need a correct model, positive residual degrees of freedom
and the usual independent homoskedastic Gaussian noise assumptions.

## Observed-data-only recipe selection

All eight permitted `(basis, ridge)` recipes are fitted, with the intercept
unpenalized and no extra standardization. SVD of the stacked penalized design
implements the same minimum-norm solution as the documented least-squares
objective. For each recipe its GATE is `a' y`; augmented OLS supplies reference
weights `b`. The selected recipe is finally refitted with the starter's
`numpy.linalg.lstsq` stacked-design convention and `rcond=1e-12`, and its
reported contrast is recomputed from those coefficients. Conditional on the
design, if `b' E[y]` equals GATE and the true
noise covariance is `Sigma`, then

`E[((a-b)'y)^2 - (a-b)'Sigma(a-b) + a'Sigma a]`
`= (a'E[y] - GATE)^2 + a'Sigma a`.

This identity motivates a focused risk criterion without using endpoint truth.
The implementation substitutes a block sandwich computed from augmented OLS
residuals, with HC2 leverage adjustment and a block-count finite-sample factor.
This plug-in criterion is a heuristic: its unbiasedness and Gaussian risk
comparison formula are not asserted for estimated covariance, arbitrary block
dependence, misspecification or data-selected recipes. Blocks are used only as
observed covariance groups, never assumed to be independent treatment units.

Selection starts from the incumbent augmented ridge 0.1. Switching requires a
lower focused criterion and improvement over this default exceeding a plug-in
one-standard-error margin for the difference of squared reference discrepancies.
For Gaussian discrepancies with covariance `K` and means `mu`, the variance of
`delta_i^2 - delta_d^2` is
`2(K_ii^2 + K_dd^2 - 2 K_id^2)`
`+ 4(mu_i^2 K_ii + mu_d^2 K_dd - 2 mu_i mu_d K_id)`.
The means are heuristically shrunk via
`sign(delta) * sqrt(max(delta^2 - diag(K), 0))`. This conservative rule is
specified without tuning on evaluation outcomes. It is not a significance test
and does not guarantee selection gains. Unsupported or cutoff-sensitive
augmented reference contrasts, saturated designs, fewer than four blocks or
near-unit observation leverage cause fallback to the incumbent. Non-finite
or out-of-contract fits are not eligible. All diagnostics remain episode-local
and are cleared on reset/release; response keys and transitions are unchanged.

## Endpoint blind spots and unavailable experiments

An interior exposure fit cannot exclude a function that vanishes on observed
exposures but changes at zero and one. Neither observed prediction error nor
the SVD variance certifies absence of such misspecification. The candidate
records the observed fraction of nonisolates with exposure outside
`[0.25, 0.75]` internally. This is descriptive support information, not a
probability bound or a claimed test for an endpoint bump, and it does not tune
the estimator.

The proposed paired endpoint-bump mechanisms, known conditional bias/MSE
identities, fixed-assignment noise replication and graph-seed Monte Carlo
uncertainty cannot be validated through this interface: it supplies neither
conditional means nor global potential-outcome truth, and permits no new
feature maps or outcome-generating mechanism. Independent cluster assignment
and its Hoeffding bound additionally require assignment-unit membership and
probabilities, which are not documented inputs. Block labels alone are not a
substitute. These proposed study components are not implemented or claimed.

There are no measured improvements, simulation tables, public-graph runs,
coverage claims, new literature claims or paper artifacts in this candidate.
Model selection can fail under omitted interference, concentrated exposures,
correlated noise not represented by the supplied blocks, few covariance
groups, or a noisy augmented reference. Even with a correct feature map, the
selected estimator is adaptive, so fixed-recipe risk identities do not imply
post-selection interval validity. The harness owns evaluation and inference.
