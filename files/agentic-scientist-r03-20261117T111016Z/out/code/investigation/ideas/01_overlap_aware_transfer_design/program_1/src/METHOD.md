# Overlap-aware transfer candidate

This candidate preserves the starter's `handle(request)` protocol and uses only
the uploaded history, its observed mask, the episode query pool, and explicitly
revealed scores. It does not download data or write evaluation artifacts.

## Estimator

For each column, compute the observed training mean. For each pair, compute an
unbiased covariance using the pair's common rows and pair-specific means; pairs
with fewer than two common rows have zero covariance. Clip pair covariances to
the bounds implied by the training marginal variances. Multiply off-diagonal
covariances by `pair_counts / (pair_counts + shrinkage_strength)`, restore the
training marginal variances, symmetrize, and floor the eigenvalues. A positive
diagonal congruence then restores the floored marginal variances while retaining
positive definiteness in exact arithmetic.

Unobserved columns have mean 0.5. Marginal variances with fewer than two samples
use the median supported marginal variance, or a fixed prior variance of 0.01
when no column has support. These are algorithmic defaults, not measured results.
Zero variances and absent pair overlaps are explicitly handled. The numerical
variance floor is `max(1e-10, min(1e-6, ridge * 1e-6))`. The original rank and
sweep settings are accepted and validated; this covariance method does not use
low-rank factors or alternating sweeps.

## History-only tuning

Before any new-model episode, reserve a random fifth of history rows, bounded
between two and 32 rows. With fewer than eight rows or three usable columns,
use `max(8, 0.1 * historical_row_count)` without tuning. Cap tuning at 192
uniformly sampled columns having at least two inner-training observations;
the final estimator always uses every uploaded row and column.

Freeze a random one-third of tuning columns as audit targets, with the rest
as query candidates. Inner-training and validation rows are disjoint. Only
observed validation query cells may be revealed, and only observed audit cells
enter validation loss. Every strength uses the same split and audit labels.
Sparse validation rows use up to eight available queries; rows without both
query and audit observations are skipped. Minimize model-macro MAE, averaging
available checkpoints 1, 2, 4, and 8 within each model. Equal losses favor more
shrinkage. If no validation row is usable, retain the default strength.

For inner-training row count `m`, candidate strengths are 2, `max(8, 0.1*m)`,
`max(32, 0.5*m)`, `max(128, 2*m)`, and `max(1e6, 1e4*m)`. The last is an
approximately diagonal fallback. Scale the selected strength by the ratio of
full to inner-training row counts before refitting. Sampling, sparse-row
restriction, and using one split are limitations of this computationally bounded
validation procedure, not a claim of unbiased prospective performance.

## Querying and inference

Start every trajectory from copies of the immutable fitted mean and covariance.
For each available candidate `c`, sum `V[j,c]**2 / V[c,c]` over all unqueried
columns `j != c`. Select the maximum, breaking ties by ascending opaque index.
The implementation uses an equivalent vectorized calculation for larger query
pools. No new-model target values or target masks enter selection.

After authorized observation `y`, update `mu += V[:,c]*(y-mu[c])/V[c,c]` and
`V -= outer(V[:,c], V[:,c])/V[c,c]`, copying the covariance column before the
in-place update. Guard tiny denominators, symmetrize, and zero the observed
covariance row and column. Output clipped means, retaining exact observed scores.
Check uniqueness and the eight-query budget; reset clears all fitted and episode
state, and begin clears only episode state.

For a correctly specified Gaussian model, absent the numerical guards, this
rank-one identity gives the exact conditional reduction in summed squared-error
Bayes risk on the *other* unqueried columns. It is not an identity for MAE and
does not guarantee error reduction under misspecification or informative
missingness. The query sequence depends on covariance and availability, not
on observed score values, although predictions do depend on those values.

## Scope and resource costs

Fit requires dense pair statistics and an eigendecomposition, with asymptotic
time `O(M*N**2 + N**3)` and working memory `O(M*N + N**2)`. Each query/update
uses at most `O(N**2)` arithmetic; bounded tuning adds up to five decompositions
of matrices no larger than 192 by 192. These are complexity bounds, not timings.

The interface exposes no outer model IDs, family metadata, held-out target masks,
data provenance, or external audit partition. Its row-disjointness and public-data
evaluation are harness responsibilities. The disjoint audit control above is
strictly an internal tuning device, not a separately reported outer experiment.
No paper, scientific comparison, uncertainty interval, measured runtime, or score
improvement is claimed. No tests or evaluation were run during candidate editing.
