# Source timing replay: scope and development-anchor thread sensitivity

The supplemental source jobs completed successfully and measured the same45-case fitting/tuning configuration. Their219 MIRT fits, parameter arrays, convergence attempts and objectives match the preserved original artifacts. All45 complete chosen-parameter packages are unchanged, including selected dimensions, alphas and mixture weights. The original717-file final scientific evidence manifest remains unchanged.

The first equivalence audit correctly rejected one intermediate loss grid: GSM/main/k30 correctness-anchor ridge. Across the five alpha values the largest MAE difference is0.0045117129322 in accuracy units, or0.45117129322 percentage points. The selected alpha is1 in both runs. All other development loss grids agree within1e-12. Both grids are saved in source_replay_discrepancies.json and source_timing_replay_audit.json. The initial failed assertion and downstream absent-audit-file error are recorded in notes/run_failures.json; no source fitting/prediction job failed and no result was dropped.

A targeted source-only check holds data, seeds, software and source/development masks fixed, and controls thread counts with threadpoolctl. It alternates1,2,1,2 threads. Both1-thread checks match all five replay loss values exactly; both2-thread checks match all five original loss values exactly. One of30 chosen development representatives differs. This is direct evidence of numerical thread sensitivity in clustering/representative selection. It explains how the two grids can arise with fixed random seeds; it does not establish the original effective thread count, which was not instrumented. The original source ledger describes intended single-thread settings; intended settings are not a measurement of historical library thread pools. Do not retrospectively claim such a measurement. The diagnostic script and complete item/weight/loss outputs are diagnostics/audit_anchor_threads.py and results/study/source_anchor_thread_diagnostic.json.

The separate diagnostics/audit_anchor_reproduction.py loads preserved final MIRT parameters and compares regenerated correctness-/IRT-anchor items at every13x3 budget case with the original item selections before accessing target responses. All78 final selections match in order. Only those identical original-budget responses are read for prediction checks. All78 mean-prediction vectors reproduce exactly (maximum absolute difference0); the audit adds no target observations or tuning. This is separate from the GSM source/development intermediate check, and it does not estimate anchor-fit uncertainty. Source fits/hyperparameters, final item lists, original predictions and primary error/rank evidence are not replaced or retuned.

The timing supplement therefore reports a measured **same-configuration workload proxy**, not exact equality of every development intermediate and not recovery of the suspended original command's CPU. The measured source total is1460.128825 process CPU seconds; combined with the original cache-reusing prediction commands and canonical scoring, the comparable-phase workload proxy is1764.841251 CPU seconds. Acquisition, pilots, old raw-rank scoring, diagnostic audits, display rendering and setup are excluded. Exact measurements, RSS, scope limits and hashes are in results/study/compute_accounting.json and notes/compute_accounting.md.

Reproduce this bounded diagnostic with the preserved original caches:

```bash
source scripts/env.sh
python3 diagnostics/audit_anchor_threads.py
python3 diagnostics/audit_anchor_reproduction.py
python3 diagnostics/check_source_timing_replay.py
python3 diagnostics/summarize_compute.py
```

Run a fresh measurement in a copy; preserve the delivered measurement timestamps and hashes. A complete refit can differ in numerically sensitive representatives even with fixed random seeds. The delivered raw predictions/selections, original development losses and final artifact hashes remain the record of the actual study.

The supplemental thread-control dependency is pinned in requirements.txt; results/study/source_replay_environment.json records its version and a clearly labeled post-run snapshot of loaded numerical libraries and effective thread pools. This snapshot does not establish the historical source commands' thread settings.

## Independent bounded assessment

Internal review accepted this limitation and workload-proxy interpretation in world/internal-review-repo#4, with its independent record at internal-review-repo commit `fdb524227c5f3ba45ca18c6e8ab2ac0c8264ef5f`, `review/2026-11-05-source-replay.md`. The reviewer independently checked the evidence/supplement hashes, fit-parameter and tuning provenance, timing sums, all78 recorded final-anchor selections, and the GSM1/2/1/2-thread development diagnostic. The reviewer also regenerated GSM final correctness anchors at all3 budgets and, after ordered-item matching, reproduced their mean and ridge predictions using only the identical original-budget responses. It did not rerun all219 fits or inspect the unavailable replay directory. No primary refit, retuning or target re-evaluation was requested. This bounded assessment is separate from final-version approval, anchor-fit uncertainty and invariance across hardware/thread settings.
