# Analysis check of the integrated evidence

Checked paper-repo `8aa79e935dae75d9fdcc3be7b9f290d9c16692a1` against the Research objective and the analysis commitment on 2026-11-05. This is the analysis owner's integration check, not independent release approval or a substitute for the review owner's judgement.

## Completed-job reconciliation

All nine managed jobs announced on this activation had already been consumed in the preceding delivery: main audit/aggregation and claim ledger (`job-f333920147`); changed-background cost pilot (`job-066037b7c2`); six full background cells (`job-3a50b68fc1`, `job-e8826d531c`, `job-ee2dce3f7d`, `job-ea302ad119`, `job-81f1c9775a`, `job-4809bae34f`); background saved-vector audit/aggregation (`job-c7ee407fab`). The announced jobs succeeded. No new explanation calls were launched or counted in this integration check.

The full main result remains 97,200 stochastic calls and 540 exact empirical-game references. The separate background arm remains 5,760 calls and 144 exact changed targets. The timed pilot remains separate. These results and their raw checkpoints are merged into paper-repo via PRs 16/17. The additional whole-study cost disclosure is merged via PR19; evidence requests 3/4 are closed. No result is inferred solely from a job's exit status: the corresponding delivered audits verify complete saved vectors, reference/grid/seed/source identities, endpoint checks and recorded metrics.

## File and display provenance

`supporting-checks/integrated_hash_check.json` records an actual byte-level comparison at the paper revision above. There are 861 matching analysis/evidence files that occur in both repositories. The sole differing common file is the historical work-status note `analysis/notes/next-actions.md`; it is not executable source, settings or scientific evidence. This comparison is not a claim that all repository files belong in the manuscript package.

All 346 path/SHA-256 records traversed in the integrated figure/table manifests resolve and match. There are no unresolved paths or mismatched hashes among those records, including analysis inputs, generators/supporting code, captions and declared output assets. The executed helper is preserved in `supporting-checks/check_integrated_snapshot.py` as a record of the check (its local paths assume this world checkout). These checks do not rerun explanation algorithms or replace the existing numerical audits.

## Checked scientific use

Read integrated abstract, assessment/technical definitions, study design, results, background supplement, implementation checks, computation/reproduction accounting, discussion and scope. Independently inspected the delivered PDF pages 6/7 containing the two main result figures, and rendered the separate ACS background and reference-error/repeatability figures. The displayed scientific use agrees with the analysis handoff:

- Main uncertainty uses 60 input clusters and 30 repeats per condition; all-success [0.824670,1] boundary intervals are preserved. No population >=.95 or individual reliability certificate is claimed. The checked plots distinguish the boundary treatment.
- The primary event is normalized L1 <=.20 with floor .01 AND signed-top3 overlap >=2/3. Stricter all-three recovery and the ACS forest Kernel B64 input with 0/30 successes remain visible. The stricter event is not substituted for the primary one.
- Reference accuracy and pairwise repeatability retain a common reference denominator but remain different measured properties. The manuscript does not force a hidden-error claim unsupported by these observations.
- The inactive .001/.01/.05 floor sensitivity and absence of low-signal cases are disclosed. Sparse near-gap strata, fixed trained models and unmodeled survey/household dependence limit inference.
- Background estimator accuracy is measured against each changed exact target; exact-target shift is measured separately against B32. One draw per size confounds size with row resampling. No changed-background outcome is pooled into primary repetition rates.
- ROC-AUC ranges in the main prose agree with model_diagnostics.csv: German .822976–.852262, ACS .885053–.895514, Diabetes .878889–.894074 (rounded in the manuscript).
- Actual rows and CPU accompany nominal settings. Neither nominal-budget contrasts nor plotted curves assert equal-cost estimator superiority. Interrupted wall times do not establish service latency.
- Main 7.49345 CPU hours remains distinct from the 7.835266-hour disjoint recorded subtotal. Unknown setup/failed-control/validation costs are explicit, and the sampled managed counter remains nonadditive. No exact all-inclusive compute total is asserted.
- Fresh-root reproduction regenerates the omitted fitted bundles; the shipped checkpoints support audit/reaggregation. The actual one-input/180-call preflight with exactly matching vectors is labeled a reproduction check, not new statistical evidence.

No analysis correction was identified in this checked revision. No further numerical work is owed under the completed commitment. Subsequent review corrections remain analysis-owned when requested; the manuscript, presentation and release decisions remain with their owners.
