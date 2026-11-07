# Preliminary full-horizon pilot results

Exploratory, one seed per configuration; not a replicated width effect. Read against the objective's requirement for uncertainty and falsifiable prediction. This is regime-finding and measured costing only; confirmatory evidence remains unfinished.

Three ReLU width pilots completed at p=31, train fraction=0.5, lr=0.001, AdamW decay=1, horizon=20000, evaluation interval=100. Configurations: `configs/pilot-a.json` and first entry of `configs/pilot-b.json`. Raw data: `results/pilot/pilot_relu_w{32,128,512}_wd1/`. Source hashes and exact initial/final models are included. Two independent one-thread jobs were started concurrently; runs within each job are sequential.

| Width | Train-fit onset (99%, 3 evals) | Validation onset (95%, 3 evals) | Final validation accuracy | Wall seconds | CPU seconds | Process peak RSS KiB |
|---|---:|---:|---:|---:|---:|---:|
| 32 | 1600 | censored at 20000 | 0.230769 | 32.6967 | 32.1893 | 345064 |
| 128 | 400 | censored at 20000 | 0.808732 | 64.2696 | 62.7095 | 345064 |
| 512 | 200 | 19100 | 0.958420 | 168.7028 | 168.3040 | 359736 |

The raw summaries are authoritative for full precision. The width-512 validation event was confirmed at step 19300 and remained above threshold for the final three evaluations. This establishes that the candidate architecture/settings can exhibit a long training-fit to generalization separation. It does not establish a replicated size effect. The 32 and 128 noncrossings remain right-censored; they are not 'never generalizes'.

Process peak RSS is read from Linux `getrusage(RUSAGE_SELF).ru_maxrss` (KiB), includes Python/PyTorch and any earlier sequential runs in that interpreter, and is therefore a conservative process bound for each configuration rather than an isolated incremental model allocation. At roughly 337–351 MiB it is far below the 4 GiB job limit. Both exploratory jobs have completed successfully. The final analysis snapshot contains five completed runs and zero incomplete runs.

Measured cost supports tens to hundreds of seed runs under the one-week limit: extrapolating a 60000-update horizon at these unchanged throughputs gives approximately 98/193/506 wall seconds at widths 32/128/512 (planning estimates only). Exact confirmatory grid and horizon still await the plan decision and completed exploratory controls. A candidate 5-width, 8-seed, 2-decay matrix is on the order of hours rather than tens of hours at p31; this is only a costing example, not a selected protocol.

## Completed exploratory controls

`pilot_relu_w128_wd0p1`: train-fit onset 300; validation 95% event censored at 20000; final validation accuracy 0.04158004; full-grid spectral fraction 0.14110440. `pilot_gelu_w128_wd1`: train-fit onset 400; validation 95% event censored at 20000; final validation accuracy 0.86902285; spectral fraction 0.40075589. Raw data and exact summaries are in the corresponding `results/pilot/` directories.

At this one exploratory seed, smaller decay gave lower held-out accuracy at the fixed horizon. GELU did not remove the right-censoring. These observations select neither a replicated effect nor an explanation. They motivate a regularization contrast and longer, common-horizon follow-up. The pilot has succeeded at locating a measurable grokking regime and bounding run cost; it has not fulfilled the study's required uncertainty or scope checks. No failed computation or missing run is hidden: three timing runs and five full pilots completed, with no training failure.
