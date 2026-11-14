# Score-targeted covariance candidate

## Interface and estimator

`program.py:handle` retains the starter RPC operations and response schema.
Only supplied source bits, opaque integer source groups, query budgets, a random
seed, the control mode, and cumulative queried target bits are consumed. No
target identity, full target score, metadata files, network, or external data is
used. Reset and release clear all episode state. Observe is a stateless mapping
of each supplied response row to a float64 probability; repeated response rows
therefore receive identical predictions. Diagnostics remain in candidate RAM
and are never added to any RPC response.

Every group receives equal total source weight. The supervised response is the
full source-row item mean. Weighted centered item factors yield item-to-score
covariances, and only selected item covariance columns are computed. Greedy
selection maximizes squared conditional score covariance divided by regularized
conditional item variance. Rank-one Schur updates maintain item variances;
small solves maintain score covariances. No item-by-item covariance matrix is
formed. The ordering is deterministic, distinct, and reused for all budget
prefixes. The prediction is the regularized linear regression of the benchmark
mean on the selected responses, with an optional affine calibration and only
final clipping. The ridge is a covariance-scale penalty, not a sum-of-squares
penalty scaled by the number of source rows.

## Source-only tuning and assessment

The fixed ridge grid is `{0.025, 0.1}`. Six source-group partitions define three
inner folds: each fits four partitions, calibrates on one, and validates on the
remaining one. All factors and the complete selection order are refitted on
each fold's fitting rows. Identity and nonnegative-slope affine calibration
are compared independently at each budget by group-balanced validation MAE;
one ridge is chosen across budgets, preserving a single nested ordering.
Ties favor identity and the first ridge. After selection, calibration is
refitted from pooled out-of-fit predictions for both omitted partitions, then
the predictor is fitted on all supplied sources. These final calibration
labels are not new validation evidence. The source-fold fit-size difference
can affect calibration transfer to the full-data predictor.

For primary episodes with at least eight supplied groups, a separate outer
source holdout contains a seeded quarter of groups (at least two). All tuning,
calibration, selection and control fitting exclude these groups. The outer
comparison is not used to choose final settings. Final deployment retunes on
all supplied sources; the outer audit assesses the smaller-training-set
procedure, not an untouched test of that final fit. With fewer than eight
groups the configuration is predetermined ridge 0.025 and identity calibration,
and no nested outer assessment is claimed. Groups are never subdivided.

Internal comparisons use equal query budgets: uniform sample means, the
group-balanced source mean, response-profile farthest-first anchors with
cluster-mass weighting, and a local regularized fixed-discrimination Rasch
control on the candidate's prefixes. The anchor control is an explicit local
approximation, not a reproduction of a published implementation. The starter
does not expose the harness's IRT or anchor baseline code or predictions;
the local Rasch control is not claimed equivalent to that IRT baseline.

D-optimal and unweighted selectors use the same covariance estimator and
primary-selected ridge. They are compared against raw primary predictions
without affine calibration, isolating these choices without transferring
an inappropriate primary calibrator. The no-calibration mode retains the
primary ridge/order and uses identity calibration. The no-diversity mode uses
a seeded uniform ordering and separately source-tuned ridge/calibration; it
is a policy control, not a pure selector-only causal effect. Outer comparisons
also include that separately tuned uniform policy.

Paired absolute-error differences are averaged within each outer held-out
group, then equally across groups. Their stored group standard error is a
descriptive uncertainty summary for this one split, not a distribution-free
interval or evidence that supplied groups are independent genealogies.
Source means and pseudo-target full scores are source-only supervision; every
pseudo-target predictor consumes only its own legal prefix bits. Seeds are
not counted as independent model observations.

## Edge cases and resource intent

Positive ridge and a variance floor handle singular and constant columns.
Empty design prefixes use unconditional covariance quantities. Nonempty
increasing budgets up to the item count are supported. An item pool smaller
than a requested prefix is rejected, because returning repeated items would
violate the interface. Too-small group counts use the conservative fallback.
Factor and selected-column caches are shared across the small tuning grid
within each fitting fold. BLAS thread environment settings are set before
the candidate imports NumPy; a hosting process that pre-imports NumPy may
control threading independently. Fitted factors/covariance caches are dropped
before observation, and release/reset clear the remaining state.

## Reproduction status and limitations

This execution stage permits file edits only, not candidate execution, tests,
benchmarks, data acquisition, or evaluation. No run time, prediction accuracy,
confidence interval, successful smoke test, or baseline improvement has been
measured here. The harness owns the subsequent official evaluation. The only
runtime dependency beyond the Python standard library is NumPy, as in the
starter; the runtime's exact version was not inspected or changed. Inputs and
seeds come from the documented RPC protocol, not new candidate-owned files.

No literature or forbidden content was accessed. No target-label experiments,
paper, figures, tables, PDF, conference template, or checklist are claimed to
have been completed. A complete research deliverable still requires permitted
actual runs, uncertainty analysis, literature review and paper production.
The proposed design is a regularized linear proxy, not exact Bayesian
Bernoulli inference, a design-unbiased estimate, or a guaranteed improvement
over IRT under model shift. Calibration and clipping do not add unbiasedness.
