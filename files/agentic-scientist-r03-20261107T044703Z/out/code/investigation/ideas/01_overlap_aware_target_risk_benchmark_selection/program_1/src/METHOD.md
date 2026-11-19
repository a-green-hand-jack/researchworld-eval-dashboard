# Overlap-aware target-risk candidate

The executable entrypoint remains `program.py:handle`. Dependencies remain Python
and NumPy, as in the starter. No files, network requests, or additional response
fields are used by the candidate. This document describes implementation, not
experimental findings. No candidate execution or evaluation was permitted during
this editing stage.

## Estimation and conditioning

Upload masks identify observations; transport zeros under false masks are never
treated as observed scores. Means and scales use observed historical entries only.
Scales have a 0.01 floor in the interface's normalized score units. Covariance
uses pair-specific observed counts and pair-specific centering, with zero
off-diagonals for fewer than three overlapping observations. Correlations are
bounded using the empirical marginal variances before overlap shrinkage. An
off-diagonal is multiplied by `n_ij / (n_ij + overlap_penalty)`; marginal variances
are restored before eigenvalue flooring. A diagonal congruence rescaling after
the PSD projection preserves empirical variances (with a positive floor), and
also preserves positive definiteness. Empty columns have mean 0.5 and no inferred
cross-covariance. Missing-not-at-random bias is not corrected.

Prediction is the standardized regularized Gaussian conditional mean, inverted
to normalized score units and clipped to [0,1]. Purchased entries are copied back
exactly. Conditioning ridge is tuned regularization, not an estimate of physical
benchmark measurement noise.

## Query objective and algebra

Let C be the current standardized posterior covariance, r the positive ridge,
and w_t the squared training scale for target t. For candidate j, the target set
is the available, unpurchased tasks excluding j itself. The selection objective
is `sum_t w_t C[t,j]^2 / (C[j,j] + r)`. Squared training scales give equal
weighting in the API's common normalized score units, rather than equal weighting
after variance standardization. Ties resolve to the lowest column index.
The posterior rank-one update is `C -= C[:,j] C[j,:] / (C[j,j] + r)`.
This is a static historical-data-selected sequence conditional on availability;
the values of purchased scores do not adapt the sequence. Unavailable tasks are
neither queried nor included in the target-risk objective.

For a Gaussian prior and independent query noise variance r, the conditional
covariance identity gives the update above. Taking the weighted trace on any
fixed target set disjoint from j gives exactly the acquisition expression. Live
code compares the vectorized acquisition with its explicit scalar formula and
checks the weighted-trace difference after each update. These checks are
implemented but have not yet been executed in this stage. Their identity is not
a guarantee under distribution shift, MNAR missingness, or misspecification, and
does not establish submodularity. Excluding the candidate's own term does not
eliminate the moving-target evaluation issue.

## Historical-row tuning

A seeded split holds out up to 32 eligible historical rows, with at least three
observed tasks per row. The remainder alone determines inner-fold means, scales,
covariances, and query sequences. No cell from a held-out row contributes to that
fit. For at least three advisory training steps, overlap penalties are 0, 16,
and 64; otherwise only 16 is tried. Ridges are 0.02, 0.2, and 1.0.
Validation replays available historical queries at feasible checkpoints 1, 2, 4,
8 and the supplied budget. It includes both the application objective and a
seeded disjoint half-task query-pool/target-panel control. Hyperparameters minimize
the mean paired squared-error difference from the training mean on identical
scored cells, plus one quarter of its historical-row standard error. This is
a modest regularization heuristic, not a reported confidence interval.

The zero-gain baseline is a diagonal covariance model. It is retained if no
configuration improves the penalized validation objective. This prevents the
model from being forced to extrapolate historical correlations unsupported by
validation. With insufficient validation rows, defaults are penalty 16 and ridge
0.2. The selected configuration is refit on all uploaded historical entries.
The RPC seed initializes only reproducible historical splits/partitions, never
workload-dependent behavior. A reset clears every learned or uploaded object.

## Scope and limitations

The internal selector accepts separate query and target masks, used by the
historical validation control. Selected and scored indices are recorded in an
internal, ephemeral validation cache, never added to RPC outputs. This is not an
outer-test fixed-target audit: the external interface always scores available
unpurchased targets and supplies no target-panel control. Likewise, it supplies
no historical model identifiers, family labels, dataset provenance, or timestamps.
Family-disjoint validation, family bootstrap intervals, temporal splits, pinned
data acquisition, and claims about specific public datasets cannot be honestly
implemented from this interface. No such experiments or results are claimed.
No paper/PDF, real-data benchmark results, baseline comparisons, or empirical
performance improvement were produced in this restricted candidate-edit stage.

Leading estimation costs are O(rows * columns^2 + columns^3); each unique
availability mask needs O(budget * columns^2) planning. Plans, not posterior
matrices, are cached across contexts. Scores from separate new-model contexts
are never pooled. Storage is O(rows * columns + columns^2), plus upload masks,
small validation caches, and per-context observed values. These are complexity
bounds, not measured resource or runtime results.
