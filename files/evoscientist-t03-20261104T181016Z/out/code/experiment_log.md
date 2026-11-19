# Experiment log

This file did not exist at the Stage 1 reflection; it is initialized here without reconstructing unobserved earlier entries.

## 2026-11-04 UTC — Stage 1 gate and prospective scope freeze

**Decision: GO — full Tier A**, fixed before viewing main reliability metrics. Preserve `/work/plan.md` unchanged, including every main metric, threshold, budget, reference qualification rule and resource fallback. Read only the requested plan, initial test report, pilot task log, model metrics and data manifest, plus the existing TODO list and relevant planning skill/memory. No main reliability files or web were read.

### Evidence
- `/work/artifacts/tests_initial.txt`: six tests pass in 1.72 seconds.
- `/work/results/pilot_task_log.jsonl`: 18/18 completed tasks, seed-11 first two points in all three datasets by three models, eight repeats, both estimators and all three budgets. German timing used two 1024-pair split references and an additional 128-pair timing audit, per the execution handoff; the latter is not the required final audit.
- Slower of the two measured pilot CPU seconds per point in each dataset/model cell (LR/RF/HGB): German 4.040/6.398/17.327; ACS 0.470/0.703/2.113; Pima 0.048/0.080/0.094. These are whole cached study-task costs, not measured uncached deployment latencies.
- `/work/artifacts/model_metrics.csv`: 27 nominal fits, AUROC range 0.7968–0.8975. LR/HGB prediction hashes match across nominal seeds, consistent with deterministic fit behavior but not standalone proof of learned-state identity. No training-uncertainty claim or accuracy-driven retuning.
- `/work/artifacts/data_manifest.json`: ACS retains ten raw attribution players despite 734 encoded columns; 82 duplicate-feature rows among 20000 (0.41%), unknown test categories OCCP 8 and POBP 6. Selected source-ID disjointness is reported by the execution handoff. Retain the frozen selection; audit duplicate-feature overlap without confusing equal covariates with duplicate source people.

### Conservative throughput projection — not a measured full-run result

The sum of the nine slower-point pilot CPU times is 31.273 seconds. Tier A schedules 72 points in each cell. Applying an intentionally conservative 8x multiplier to the entire pilot task (not merely estimator replay) gives `31.273 * 72 * 8 / 3600 = approximately 5.004 CPU-hours`. This allows for 64 rather than eight repeats, additional mask-union generation/cache misses and solver CPU. Initial German split references are already represented by the pilot; low-dimensional exact game work does not require eight times as many unique masks. The 8x extrapolation is a planning scenario, not an empirically established scaling law or upper bound. With 30% overhead, the main/reference task envelope is approximately 6.505 CPU-hours.

For a whole-program budget scenario, separately retain 4 CPU-hours for full German audit/escalation/repair, 2 for full Tier A Stage 4, and 2 for Stage 5. Apply 30% overhead to the entire future-work envelope and budget the original combined Stage 0/1 allowance of 3 hours: `3 + 1.30 * (5.004 + 4 + 2 + 2) = approximately 19.905 CPU-hours`, below the hard 24-hour cap. The allowances are not measured consumption and do not authorize exceeding the cap. Cumulative child-inclusive CPU, peak RSS and current disk headroom are not certified by the supplied evidence; reconcile them before launch and monitor actual costs. Never infer deployment speed from cached pilot throughput.

### Frozen next actions and limitations

1. Execute the complete 648 point-fit tasks, both estimators, all three budgets and 64 fresh repeats: 248832 main vectors. Do not recycle pilot explainer draws. Retain full Tier A Stage 4 sensitivities, German defaults diagnostic and genuine uncached timing.
2. Keep exact Pima8/ACSIncome10 references as the anchors. Complete two independent German 1024-pair streams per point and the independent extra-4096-pair audit on all six prespecified seed-11 points. `german_hgb_11_00` was initially unqualified; do not omit it, relax tolerances or declare final qualification from pilot flags.
3. Apply the unchanged audit-discordance or >10%-unqualified trigger: once add 4096 independent pairs to each unqualified task within the CPU cap, requalify with disjoint balanced halves, and freeze reference artifacts before main scoring. Publish full denominators/unresolved-task sensitivity and narrow German accuracy claims if >10% remain unqualified.
4. Verify LR/HGB function equivalence through learned states or deterministic-fit semantics before any cache deduplication; preserve nominal seed/ID strata and fixed-fit inference. Report ACS encoded dimensions, unknown categories and duplicate-feature diagnostics, with duplicate-cluster sensitivity if relevant. No data/model/threshold changes.
5. Track actual CPU/RSS/disk with bounded batches and compact cache storage, never a full German coalition enumeration. If unexpected resource pressure forces reduction, use the existing single-step lower-tier deviation rule, not an outcome-dependent subset.

Structured reflection: `/work/artifacts/stage1_reflection.json`. Gate recommendation: proceed to Stage 2/full Tier A, subject to the existing resource preflight and reference qualification gates; no main reliability conclusion is made.
