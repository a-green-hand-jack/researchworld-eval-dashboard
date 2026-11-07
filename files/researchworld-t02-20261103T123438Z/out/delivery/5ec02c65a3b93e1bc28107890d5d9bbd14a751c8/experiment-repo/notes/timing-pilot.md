# Timing pilot (exploratory)

Exact command: `python3 scripts/run_grid.py configs/timing.json results/timing`.
Resource reference: `job-ec82c12fb1`, succeeded. One job, sequential configurations, one PyTorch intra-op thread, full-batch updates on 480 train pairs and 481 validation pairs modulo 31. Each configuration has 2000 updates and 21 full-grid evaluations (including initialization), and initial/final checkpoints. Total executable runtime excludes Python import and resource provisioning.

| Width | Parameters | Wall seconds | CPU seconds | Training seconds | Evaluation seconds |
|---|---:|---:|---:|---:|---:|
| 32 | 3039 | 3.2234 | 3.2212 | 3.1216 | 0.0925 |
| 128 | 12063 | 6.2756 | 6.0593 | 5.9491 | 0.1108 |
| 512 | 48159 | 16.3977 | 16.3902 | 16.1538 | 0.2355 |

These values were transcribed from the run `summary.json` files; machine-readable records are authoritative. All three memorized by the final checkpoint (99% or higher train accuracy) and no run generalized within this short horizon (validation accuracy 0 to 0.42%). These are censored exploratory observations, not evidence of eventual absence of generalization or a replicated width trend. See `results/timing-analysis/` for event definitions and event flags.

Peak RSS was not recorded in this first timing pilot; it cannot be inferred as a measurement. Subsequent runs will record process-peak RSS (a process-level upper bound when a grid executes sequentially in one interpreter). Source code Git revision/hash will also be recorded in subsequent metadata; the exact initial timing implementation is in commit history immediately before this note.

Planning extrapolation, not measurement: at unchanged throughput 20000 updates would take approximately 32/63/164 wall seconds for widths 32/128/512, plus import/provisioning and changed host sharing. Five exploratory full pilots (three widths with decay 1; width 128 decay 0.1; width 128 GELU) are therefore affordable in minutes. They will retain the same exploratory seeds and not enter confirmatory inference.
