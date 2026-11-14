# Measured source replay and reproduction workload

Measured reproduction-workload proxy: isolated same-configuration source replay + original frozen cached predictions + corrected scoring; stages executed at different times.

| Stage | CPU seconds | Elapsed seconds | Peak process RSS (KiB) |
| --- | ---: | ---: | ---: |
| source_replay_A | 1084.819 | 1155.498 | 432196 |
| source_replay_B | 375.310 | 446.082 | 314552 |
| predict_A | 37.743 | 37.752 | 473992 |
| predict_B | 29.725 | 29.825 | 426408 |
| scoring_canonical | 237.245 | 237.369 | 1250604 |

The two source commands completed all219 fits and45 tuning cases in an observed parallel wall span of1155.498s, using1460.129 CPU seconds. Their fitted parameter arrays, convergence attempts, objectives and chosen parameters agree with the original source artifacts under the explicit checks in `diagnostics/check_source_timing_replay.py`. The complete original scientific evidence manifest remains unchanged.

The source replay plus original prediction and corrected-scoring commands sum to1764.841 CPU seconds (29.41 CPU minutes) as a reproduction-workload proxy. The phases were measured at different times; this is not an original end-to-end timing. All measurement inputs are hash-pinned in `results/study/compute_accounting.json`.

Original source commands did not measure full CPU; replay is a new measurement, not recovery of the suspended run.

Total combines phases measured at different times. No measured original end-to-end wall time is claimed.

Excludes acquisition, pilots, discarded raw-tie scoring, diagnostic audits, formula reporting, rendering and dependency setup.

Process peak RSS is not aggregate concurrent-job memory. CPU/elapsed change with hardware and shared-host contention.

One GSM development anchor-ridge loss grid is thread-sensitive:1-thread checks reproduce replay values,2-thread checks reproduce original values; chosen alpha unchanged. Historical effective library thread count was not measured.


Development-loss discrepancies are retained in the audit and compute JSON. One GSM/main/k30 correctness-anchor ridge loss grid differs (maximum0.004511713 in accuracy units, or0.4511713pp); its selected alpha remains1. All45 selected-parameter packages and219 MIRT fits match. The replay is a same-configuration workload measurement, not an exact replay of every development quantity. A bounded1/2-thread diagnostic reproduces both loss grids exactly:1 thread matches the replay and2 threads match the original, with one of30 development representatives changed and alpha1 retained. This establishes numerical thread sensitivity; the original effective thread-pool count was not recorded, so historical execution settings are not inferred as fact. All original primary code and results are preserved.

Source-only replay commands and exact inputs are documented in `notes/source_timing_replay_ledger.json` and the reproduction README. Scientific original caches and predictions are never replaced by replay outputs. Retain `notes/timing_caveat.md` and the original suspension-affected record when reporting compute.
