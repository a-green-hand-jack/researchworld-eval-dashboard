# Production reflection

Evidence scope: current local artifacts only; no browsing, identity inference, or prior research findings incorporated.

## Reviewer-acceptable conclusions
- Production numerical gate passes: validation.json reports 11,085 audited fits, maximum gradient 9.9994e-9, and 338 cold-replayed witnesses with maximum margin discrepancy 7.3163e-9.
- At the locked nominal 1% budget, uncapped selected flips reverse the original top-pair margin in 4/6 full cohorts; tested strict-cap procedures reverse only Arena. These are fixed-schedule, regularized-BT witnesses, not population prevalence estimates or certificates.
- Budget denominators materially change the feasible perturbation set. NBA strict caps permit at most 1/2/1 edits in 2013/2014/2015: floor(sum of endpoint caps / 2), versus global budgets of 13. At 0.1% and 0.5%, all NBA participant caps are zero.
- Integer-linear optimization reports optimal status and zero gap in all 16 recorded conditions, certifying only the linear surrogate to solver tolerance. At 1%, its exact-refit margins closely match capped greedy results; edit counts can differ.
- On 1,814 common equal-weight MT cells, the reported paired GPT4-minus-human GPT4-v-Claude BT margin difference is 0.479, percentile interval [0.173, 0.795]. This is a conditional descriptive contrast, not evaluator accuracy or a causal effect.

## Conclusions not supported
- No universal fragility/robustness claim, eight-independent-replicate interpretation, nonlinear optimum, minimum-edit threshold, or all-challenger robustness certificate.
- Arena was already near tied: original margin 0.00424, bootstrap interval [-0.103, 0.106]. A point reversal does not overturn a statistically established original ordering.
- Original-bootstrap-SD-standardized reductions are not post-edit tests. Cell reversals, individual-vote reversals, deletion, and whole-question edits have different cost units.
- No causal evaluator-design comparison, broad human-versus-GPT superiority, novelty clearance, or real-world attacker characterization follows.

## Bounded remaining work
1. Preserve the locked primary analysis. Add the end-to-end attack bootstrap explicitly to plan_deviations.md as post-outcome exploratory; do not retroactively promote it. Its capped-Arena edited-margin interval [-0.20934, 0.000868] crosses zero despite 97% reversed bootstrap replicates. Recomputed-attack uncertainty is not uncertainty for one fixed witness.
2. Reconcile exploratory-bootstrap audit coverage: bootstrap_sensitivity_fit_audit.csv contains 7,208 fit records, but validation.json does not explicitly identify their inclusion. Document target-pair freezing, aligned cluster resampling where paired, multiplicities, budget/cap recomputation, failures, and original-versus-bootstrap denominators before relying on these intervals.
3. Complete the claim-evidence, ablation-coverage, and publication/reproducibility audit. Arena tie-dropping already reverses the unedited fixed pair; do not count that as an edit-induced reversal. Cap-plus-one is a changed restriction, not equivalent rounding. Publication gate remains unverified by the inspected artifacts.

Stop rule: no new datasets, models, parameter searches, or bootstrap expansion. Re-run only a specifically failed audit condition. Keep optional Arena matched-exposure subsampling deferred. Existing recorded core/supplementary/exploratory runtimes are about 16.27/16.67/27.09 seconds, respectively, not an end-to-end reproduction timing.
