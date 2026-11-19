# Attempt ledger

## Initial implementation, v1 (2026-11-02)
- Baseline/real-data run completed all five MTEB splits and seven stresses; stopped before OpenLLM evaluation due to numpy.bool JSON serialization (runtime TypeError).
- Sparse MCAR20 histories had an entirely unobserved task for seeds23/53; correctly failed rather than imputing an unidentified mean. These are scientific infeasibility results, not resampled.
- Two .1-shrink training fits reached80 iterations before tolerance1e-5. Numerical repair: uniform200-iteration cap (all estimators/splits, not outcome-tuned).
- Static independent audit found baseline mean was EM mean rather than observed per-task mean: changed to group-weighted observed training means. Other selectors/predictors unchanged.
- Audit found adequacy multiplicity omitted shrinkage selection: changed Bonferroni factor to four shrinkage choices times all budgets times two endpoints. Percentile bootstrap still conditional/finite-group, not a certificate. No test RMSE inspected in deciding this correction; only run log/configurations/convergence/audit.
- Eight-comparison Holm procedure with6 test groups structurally cannot reject (minimum exact two-sided p=.03125 >.05/8). Retain protocol, disclose underpower, do not substitute a favorable test post hoc. Effect intervals remain descriptive conditional intervals.
- Preserve original outputs under artifacts/pilot_v1/; no numbers from them used in final paper. Final full rerun generated from corrected code.
- Row-random comparisons change cohort/weight/sample sizes; label as descriptive protocol contrast, not causally estimated leakage effect.

## Instrumented v2 and post-review correction v3
The v2 measured reproduction took93.06wall seconds/92.40user CPU seconds, peak childRSS238544KiB, one BLAS thread. Seven generated numerical tables were byte-identical to their prior corrected run (numeric_reproduction_reference.json). Instrumentation records objectives/support/inner fits without changing predictions. An attempted system-time wrapper was unavailable/blocked; Python resource/subprocess wrapper replaced it. Tests were subsequently expanded from6 to10.

Independent paper self-review found a real secondary preprocessing defect AFTER results had been inspected: 549 retained OpenLLM Base Model fields equal literal 'Removed'. The initial graph treated that placeholder as a real shared base. Normalize known missing sentinels before unioning edges; preserve genuine slash-free model identifiers. All old secondary runs and the old graph are retained under artifacts/flawed_secondary_v2/. This is a post-review corrective reanalysis, not an untouched confirmatory replication. Rerun all five secondary splits, tuning, selection, adequacy and tests with unchanged grids/seeds/protocol; do not select favorable results. Metadata repair changes381components to472. Primary MTEB panel/group CSV and secondary score matrix remain byte-identical (pre_group_repair_hashes.json), so primary numbers are unaffected. Final report must use only corrected secondary numbers and disclose the defect and chronology.

The delivered final reproduction uses the repaired graph. Per-split logs retain two infeasible MCAR20 conditions and18capped executable stressfits; these were not hidden or resampled.

