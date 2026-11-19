# Anchor-only prediction with a probability audit

This candidate implements a mechanism, not an evaluated research conclusion.
No candidate code, tests, numerical experiments, or official evaluation were
executed during this editing stage. No performance improvement is claimed.

## Interface and query allocation

`program.py:handle` retains the starter's operations, response fields, dtypes,
and state lifetime. Source data arrive only through the existing byte transfer.
There are no file reads, network requests, model IDs, or target-score inputs.

The supplied interface requires nested prefixes of lengths 8, 16, and 32. A
single source-selected anchor set of size 2, 4, or 6 is placed first, followed
by 32 minus that count uniformly sampled, distinct complement items. Every
checkpoint therefore has at least two uniform complement audit items. This
deliberately forgoes increasing the informative-anchor count at later budgets:
excluding unqueried future anchors from early audits would invalidate uniform
complement sampling. The proposed 32/64/128 experiment grid is unavailable.

`no_diversity` replaces D-optimal anchors by uniform anchors, keeping the same
validation procedure. `no_calibration` retains the primary query selection but
returns the queried empirical average, as in the starter. These are operational
controls, not claims to reproduce any published method.

## Source training and validation

Training centers each item over source rows and estimates at most 16 loading
directions. For at most 64 rows it uses an exact row-Gram eigendecomposition;
otherwise it uses an oversampled randomized rank-16 decomposition with two
power iterations. Loadings include singular values scaled by sqrt(S-1).
D-optimal greedy selection uses the same ridge precision as target inference,
with lowest-index deterministic ties.

Opaque supplied `source_groups` define one source-only held-out partition:
one quarter of shuffled unique groups (at least one group) is held out, and
training excludes every row in these groups. Validation is capped at 64 rows
by source-seeded subsampling; unsampled rows in held-out groups are NOT put
back into training. These groups are accepted as opaque: no assertion that
they encode proven ancestry is made. If fewer than two groups exist, or the
split leaves fewer than three training rows, the disclosed fallback is rank 4,
ridge 1, four anchors, correction weight 0.5 at all checkpoints.

Each rank in {4,8,16}, ridge in {0.1,1,10}, and anchor count in {2,4,6} is
evaluated using training-only item means, loadings, and anchor selection.
Available rank is capped by the source dimensions. For each configuration,
three separate simulated audit draws evaluate correction weights {0,0.5,1}
at each checkpoint. Weights minimize MAE + 0.25 RMSE; the shared rank, ridge,
and anchor count minimize its checkpoint average. Full validation scores
enter only these validation losses, never the validation-target latent solve
or its item predictions. The selected model is refitted on all source rows.
The final query draw uses a separate seed offset from validation query draws.
No target observations participate in selection, tuning, or source fitting.

Source validation retains a paired, group-resampled percentile interval for
the selected estimator versus matched-anchor weight zero. Query seeds and
budgets are averaged per model BEFORE resampling groups. This internal
interval is post-selection and may be degenerate with a single validation
group; it is not target-test evidence or a valid post-selection significance
claim. It is never added to RPC responses. Weights zero and one are explicitly
evaluated during validation, not reported as completed external comparisons.

## Inference and unbiasedness boundary

For each queried row, `frozen_predictions` receives only the fixed anchor
answers. Its ridge solve produces clipped item predictions. The audit answers
are used only in `residual_estimate`, after these predictions are frozen.
There is no target cache, cross-row fitting, or target identity state. This
call separation implements query isolation; no executed isolation test is
claimed. Full-budget observation returns the exact full mean by forcing
weight one when N equals the query budget.

Let A be the fixed anchors, a=|A|, C their complement of size M=N-a, and p_j
the frozen item predictions. For a uniform size-r subset U of C, the raw
estimate is

    B + w M/N mean_{j in U}(y_j - p_j),
    B = (sum_{j in A} y_j + sum_{j in C} p_j)/N.

Conditional on the trained model, A, anchor answers, and fixed finite target
response vector, a fresh uniform audit has expected residual mean equal to
the complement's population residual mean. Thus ONLY w=1 yields a raw
conditionally design-unbiased estimate of the full score. Its estimated
sampling variance is

    (M/N)^2 (1-r/M) s_residual^2/r,

with sample variance using ddof=1. Census auditing has exactly zero sampling
variance. The implementation computes this quantity internally; it is not
returned or treated as a calibrated interval. Shrinkage, source validation
selection of w, and final clipping generally introduce bias. Item-prediction
clipping before drawing the audit does not invalidate the raw w=1 argument.
No empirical interval coverage has been measured.

## Explicitly unfinished research obligations

- The interface supplies no identities, Base Model links, or details repos.
  Deterministic identity/ancestry connected components cannot be constructed.
  No lineage-disjoint target split is claimed; only supplied source-group
  validation disjointness is checked.
- No target full scores or target groups are available. Target MAE/RMSE,
  ranking correlations, paired target bootstrap intervals, bias, and coverage
  cannot be computed by this candidate.
- The 13 upstream matrices were not downloaded or inspected; their binary
  values and metadata alignment were not independently validated. The RPC
  source is checked for complete transfer and binary values.
- No literature was retrieved or read, including no prohibited material.
  Published-method baselines, broad multi-seed comparisons, measured runtimes,
  a verified conference template, and a paper/PDF are not produced here.
- Parameter choices and runtime costs are unmeasured. A single held-out
  source-group partition and a fixed small anchor count may be weak under
  lineage shift or heterogeneous item structure. The variance cost of an
  audit, and selection bias, can outweigh residual bias correction.

The harness owns the only official evaluation after this editing stage.
