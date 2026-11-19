# Candidate: log-odds shift plus residual ridge

## Interface and unchanged acquisition

Only `program.py:handle` is public. The starter's operations, upload limits,
cumulative histories, transitions and response schemas are unchanged. In
particular, update returns only `{"ok": true}`. No additional observations,
metadata, target scores or target-specific acquisitions are assumed.

`nonlinear_decoder.fit_candidate` first fits the original incumbent on the
original supplied source arrays, using the original seed offset and tuning
allowances. It calls the unchanged `surrogate.py` tuning, fitting, selection and
prediction functions. Its full-source selection order is frozen before any
nonlinear decoder tuning and remains the common nested path for all targets.
Each item content group can be selected only once. A zero nonlinear weight
uses the incumbent prediction directly, without evaluating the nonlinear path.

## Prefix-specific nonlinear model

Weighted source item means are clipped to [0.0001, 0.9999] and transformed into
logits. For each response row at a queried prefix, infer a single shift by
minimizing summed Bernoulli negative log likelihood plus half the shift penalty
times squared shift. Safeguarded Newton iterations use a [-20,20] bracket and
at most 64 iterations. Converged rows freeze independently, so adding other
target histories cannot change a row's stopping iteration. Positive penalties
give finite estimates for all-zero and all-one histories.

The score curve is the equal-item mean of shifted item probabilities over
**every original item column**. Probability matrices are evaluated in chunks
of 1024 item columns. Repeated-content columns retain their original full-score
multiplicity; content deduplication affects queries only.

For each queried prefix and shift penalty, source shifts are inferred from
that prefix's binary answers only, never from their full scores. A source row's
full score minus its curve score is the regression label; its queried answers
minus its shifted query probabilities are the features. Weighted centering
and a positive ridge fit all features, with an unpenalized intercept. Target
predictions are the curve plus intercept plus residual features times fitted
coefficients, blended with the incumbent and finally clipped to [0,1].
The curve-only configuration disables both the residual intercept and residual
coefficients. Source prefix statistics are reused across residual ridge and
blend choices. Deployment caches only fitted source coefficients by prefix.

## Source-only selection and allowances

The deterministic shortlist, in tie-breaking order, is:

1. Unchanged incumbent (nonlinear weight zero).
2. Penalty 1, residual ridge 0.05, weights 0.5 then 1.
3. Penalty 0.1, residual ridge 0.05, weights 0.5 then 1.
4. Penalty 1, residual ridge 0.01, weights 0.5 then 1.
5. Penalty 1, curve-only, weights 0.5 then 1.

`cv_settings` caps this list at nine entries, with the incumbent always
available. No target observations, number/order of targets, control patterns
or seed identity choose a decoder. Seeds only shuffle source lineage folds.

At least six source lineage groups are required for nonlinear validation.
Two disjoint outer held-out lineage partitions together cover every group.
Each outer training partition refits the full incumbent preprocessing, inner
lineage validation and greedy paths before fitting its nonlinear decoder.
Outer held-out rows never participate in their own item means, path tuning,
selection, source ability/residual fitting or regression labels. Their shifts
use only their allowed queried responses. Inner folds cannot see outer held-out
groups. No all-source path is reused in an outer validation fold.

All shortlisted decoders are compared on the same fold-local query prefixes.
Absolute errors are averaged equally over the incumbent's declared supported
prefixes, then within each held-out lineage using normalized supplied weights,
then equally over held-out lineages. One setting is selected for all budgets;
ties retain the earlier setting, including the incumbent. These validation
losses are internal tuning statistics, not reported experimental results.

The original full-source incumbent keeps its original allowances. Its design
cost is bounded by one final path plus two paths per distinct tuned ridge
(at most seven). Remaining `training_steps` allow two outer incumbent fits;
each gets at most seven paths and must have at least three to support inner
validation. Consequently, outer fits may use fewer inner ridge candidates
than the full-source incumbent. Fold-local blend tuning is still performed.
The total selector path bound is the deployment cost plus twice the allocated
fold cost, never exceeding the supplied allowance when validation is enabled.
As in the starter, an unconditional fallback deployment still needs one path
even if the advisory allowance is zero. There is no iterative model optimizer.

If source groups, positive partition weights, settings or design allowances
are insufficient, the unchanged incumbent wins without target-dependent
switching. After selection, the nonlinear model is refitted on all sources
for each requested prefix. Nonlinear-only source arrays are canonically sorted
by response bytes, weight and group before fitting. Every target history is
decoded independently; sorted unique histories are decoded once then scattered
back. With zero queried items the exact incumbent weighted source score prior
is returned. An actual census retains the starter's exact observed-score path.
The original imported runtime invariants check nested content uniqueness,
finite bounded predictions and identical-history equality. New production
checks enforce group separation, prefix membership and finite shifts/losses.

## Status, files and limitations

Changed `program.py` and `IMPLEMENTATION.md`; added `nonlinear_decoder.py` and
this document. `program_spec.toml`, `surrogate.py` and `invariant_checks.py`
remain unchanged. No dependencies were added.

This editing stage prohibits candidate execution, tests, benchmarks, evaluator
inspection, network access and external literature search. None were performed.
No runtime, accuracy, ranking, uncertainty estimate or improvement is claimed.
The nonlinear hypothesis remains untested; the harness owns the subsequent
official evaluation. No empirical baseline comparison, ablation experiment or
paper has been produced. No restricted research material was accessed.

Anonymous lineage IDs cannot establish complete ancestry separation. Nested
validation can be noisy with few lineages, and its selected setting can
overfit the shortlist. Source-only validation is not a guarantee under target
distribution shift. The scalar curve assumes a common log-odds shift; residual
ridge can still extrapolate poorly. The method is model-based, not a
design-unbiased audit estimator. The interface cannot request per-target
adaptive items, external benchmark labels, or empirical baseline evaluations.
