# Frozen surrogate random audit candidate

The existing RPC entrypoint, states and response schemas are unchanged.
`program.py` integrates `surrogate.py`; `invariant_checks.py` contains opt-in unit
checks. No code or tests were executed during this restricted editing stage.
No measured accuracy, timing, ranking, uncertainty or improvement is claimed.

## Source fitting and selection

Source weights define a weighted item mean and a centered source-row Gram
decomposition (at most 12 nonzero components). Greedy regularized log-determinant
selection chooses pilots from singleton content groups, with deterministic ties.
Two source-lineage-held-out partitions refit both decomposition and selector.
Each partition holds out one fifth of the supplied lineage IDs and uses at most
32 validation rows. Validation weights are renormalized supplied source weights;
row subsampling is a compute cap, not a claim of independent row observations.

On the first selection, source validation chooses a pilot count from zero,
approximately half the budget, and up to budget minus one (capped at 12).
Ranks are 1/4/12, ridge strengths 0.05/0.25/1, and correction weights
0/0.25/0.5/0.75/1. Rank zero is used with no pilots. Two independent audit draws
per source partition are scored by weighted validation MAE, including output
clipping. These are finite source-only hyperparameter choices, not guarantees
of transfer, unbiasedness, or improved rankings.

The first selection fixes the pilot count and complete random audit order.
Later budget requests expose longer prefixes and retune rank, ridge and
correction weight using only the same source partitions. Thus larger budgets
add audits, not pilots; this is an intentional capacity limitation imposed to
preserve nested subsets and exact complement sampling. No target observations
enter tuning or selection. Seeds only initialize independent deterministic RNG
streams; they never select a workload-specific algorithm.

Initial budgets of at most two, or fewer than three source lineage IDs, use a
fixed uniform sampling fallback for the entire episode. With unique content
groups this is the sample mean. A census of all items returns its exact mean.
Invalid budgets raise errors rather than querying additional items.
If a zero budget is requested, selection is empty and prediction is the
source-weighted prior; the first positive selection still chooses the design.

## Frozen predictions and audit design

Only the pilot slice is passed into ridge reconstruction. Its clipped per-item
predictions are made read-only before the estimator reads the audit slice.
There is no refitting on audit responses. With N items, pilot set P and
complement R, the raw estimate is

    [sum(y[P]) + sum(frozen[R])] / N
      + correction_weight * (|R| / N) * mean(y[A] - frozen[A]).

For distinct content groups the audit is uniform without replacement from R.
For positive audit size, correction weight one and no final clipping, this is
conditionally design-unbiased given the pilot answers and source-trained
surrogate. It does not imply unbiased MAE, correlations or rankings. Source-tuned
shrinkage and final clipping to the RPC's [0,1] range give up that guarantee.
Zero and full correction remain executable through `combine_prediction`.

For repeated content groups, pilots are restricted to singleton groups. Audits
sample remaining groups uniformly without replacement and then choose one
member uniformly in each selected group. For G remaining groups of sizes d_g,
the residual correction instead is

    (G / N) * mean(d_g * (y[item_g] - frozen[item_g])).

This is the Horvitz--Thompson residual total divided by N; it does not require
identical target answers or identical predictions within a content group. The
uniform fallback uses the analogous weighted response total. Clipping can bias
these estimates too. Sampling uniformly over all raw items while forbidding
duplicate content groups is not generally possible; the unweighted formula is
not used for such groups.

## Interface limitations and unfinished work

The RPC returns a common subset before cumulative pilot and audit answers are
delivered together. Therefore it cannot literally request an audit only after
computing numerical pilot-conditioned predictions. Instead the candidate
precommits to a response-independent random audit order and computes frozen
predictions before accessing audit labels. This preserves the statistical
independence needed above but does not implement a two-round observation RPC.

Only anonymous `source_groups` and weights are supplied. No model names,
`details_repo`, ancestry or research-test metadata are available. The candidate
uses the supplied lineage grouping for disjoint fitting and validation; it does
not construct identity/family components or claim a family-held-out experiment.
Harness target splits are unchanged. No metadata were read from external mounts.
Identity-only sensitivity, external data verification, actual baseline
comparisons, group bootstrap intervals, empirical clipping rates, an evaluated
paper and PDF, and measured improvement remain unperformed. No forbidden
literature or evaluator code was accessed.

The opt-in checks cover audit-label invariance, unqueried-label invariance,
sampling replay and budget uniqueness, constant sources, census recovery,
tiny-budget means, and exhaustive raw unbiasedness on small unit fixtures,
including unequal content groups. They are not scientific experiments and have
not been run. Exact software versions and empirical runtime have not been
measured or invented; runtime dependencies remain NumPy and threadpoolctl.
