# experiment-repo (analysis)
No new model runs: the task's evidence is the experimental log frozen in the objective (7B-class models, no GPU here).
`analysis/ledger.py` transcribes the log tables verbatim and derives differences, ensemble-vs-best-member gaps and a claim-by-claim check.
Outputs in `results/`: `log_numbers.csv` (tidy ledger), `byte_minus_token.csv`, `ensemble_vs_best.csv`, `fim_byte_vs_token.csv`, `beam_ablation.csv`, `claims_check.md` (how each log claim may be worded).
Rough SEs use benchmark sizes that are NOT in the log (external, flagged).
