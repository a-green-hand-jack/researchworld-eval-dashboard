# Review record: paper-repo PR #12, head 9a2c3b1a0f3f (fourth round)

Verdict: **request changes** — one finding left.

Inspected: `numbers.tex` regenerates identically; check_format PASS; code/README.md at head; appendix "Compute" paragraph and checklist item 8 against the README table (consistent: 21 min, 18 min, 95 min, 53 min, 21 h, stopped run disclosed).
Re-ran `run_experiments.py MAIN --from-config results/config.json --only "er|M1|bern0.5"`: tau_hat of ols_f, dm, hajek identical to `results/replicates.parquet` (max abs diff 0.0). E and F resolved.
Open: A — `figures/README.md` is still keyed to file numbers (Fig. 6 = size sweep, Table 1 = setup, 17 figures); the paper's numbering differs (Fig. 6 = Bernoulli(0.1) headline, Table 1 = main grid, 19+ figures, Fig. M, Table 3). deliverable.md requires every table/figure of the paper mapped to its script. Owner figtab-repo (figtab-repo#6). H: Fig. 1 widened; Fig. 4 tick labels still small (minor, not blocking).
D experiment-side reruns: no longer a condition.
