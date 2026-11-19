# Measured gates for the complete 204-run protocol

All values below are derived from actual nonconfirmatory benchmarks or explicitly labeled projections. No fresh confirmatory seed was run to choose this design. Exact authoritative source is `results/gate-benchmarks/resource-quote.json`, reproduced by `python3 code/scripts/resource_quote.py`.

Implementation checks are in `results/implementation-checks/checks.json`: counts, correct data and orbit grouping, multiplication zeros, frozen-weight invariants, step60000 onset with step60200 confirmation, exclusion after horizon, bitwise model/AdamW resume and optional continuation, and preservation of the parent's terminal output. Paired binary method was fixed prospectively in `reproduction/analysis_methods.md`.

Two concurrent independent jobs each used one intra-op thread, with sequential configs within each. Both succeeded. Jobs used immutable code checkout `d7b6b207999a6d1ec37e7122c724e0a6cfc9c71b`, pilot seeds100/200, 2000 updates, eval100, checkpoint1000 (stricter checkpoint frequency than production10000). The raw `summary.json` files include source hashes, environment, exact configs and process peak RSS. Process peak RSS carries earlier sequential runs as an upper bound. It is not an isolated incremental model allocation.

| Benchmark | Width | Total/trainable parameters | Train pairs | Wall seconds | CPU seconds |
|---|---:|---:|---:|---:|---:|
| Ordinary addition |64|6047/6047|480|4.499|4.424|
| Ordinary addition |256|24095/24095|480|10.374|10.267|
| Frozen hidden |512|48159/15903|480|9.890|9.696|
| Orbit split |512|48159/48159|482|18.688|18.285|
| Multiplication |512|48159/48159|480|17.960|17.762|
| lr0.0003 |512|48159/48159|480|17.853|17.740|
| lr0.003 |512|48159/48159|480|17.722|17.499|
| decay0.1 |512|48159/48159|480|17.487|17.377|

The end-to-end wrappers measure interpreter startup as well as training/checkpoint/evaluation work. Job1 took57.766 wall seconds and57.064 child-CPU seconds; job2 took72.264 wall seconds and71.520 child-CPU seconds. The maximum observed interpreter/loop CPU overhead above run summaries was7.851 seconds, included conservatively for four production job interpreters. Maximum measured process peak RSS was362040 KiB, about354 MiB, far below4096 MiB. The measured host was shared (40 CPUs with56 assigned CPU placements); this does not reserve future throughput or promise linear speedup.

The weighted registered grid projection is15.004 CPU-hours before contingency; including startup and50% reserve gives22.518 CPU-hours, leaving21.482 hours below the44-hour cap. Family quotes in hours: main4.261, decay1.878, frozen1.283, lr-low1.892, lr-high1.883, orbit1.913, multiplication1.893. Lower unmeasured control widths use measured full-model width baselines with only upward recipe adjustments; width512 full-model pricing uses the largest measured full-model rate. These are prospective, conservative planning choices, not a mathematical runtime bound or completed-study compute.

The crude uniform price of every one of204 runs at the maximum measured cell, including50% reserve, is46.783 CPU-hours and exceeds44. This alternative bound is disclosed. The unchanged complete matrix fits the cap under the more informative measured, width-weighted projection; independent feasibility should assess that evidence rather than silently trim seeds or controls. If actual running costs threaten the cap or deadline, request explicit revision and preserve unfinished requirements. No grid reduction has been made.

The largest measured2000-step run used1773041 logical artifact bytes (counting the hard-linked checkpoint and terminal alias twice, as a Git checkout would). Maximum measured curve row was436 bytes. Adding all603 production rows with25% row-size margin gives an all204-run archive projection of426407124 bytes; including50% failed-attempt reserve is639610686 bytes. This is a planning storage allowance, not actual completed-output size. Initial/final states, rolling optimizer state, all curves and attempt logs are retained; no per-evaluation weight dumps are planned.

`reproduction/deadline_ledger.json` uses the first experiment activation as the conservative overall one-week start,2026-11-03T12:39:10.373Z. The absolute deadline is2026-11-10T12:39:10.373Z; do not restart it at production or revisions. Experiments should complete by2026-11-06T12:39:10.373Z, reserving48h for analysis/figures/writing and48h for review/reproduction. Production launch remains null while relevant context/independent feasibility gates are pending. The actual UTC production launch will be appended before starting fresh seeds. The serial projection plus reserve is below one day, but this is not a guarantee against future contention or failures.

A later recovery-audit refinement adds durable attempt-start/end records and flags abrupt-loss CPU uncertainty; it does not change updates, events, controls or seeds. Bitwise recovery/continuation checks were repeated successfully in results/implementation-checks-v2/. The exact benchmark trainer remains archived under code/archive/gates-v1/ with hashes/provenance.
