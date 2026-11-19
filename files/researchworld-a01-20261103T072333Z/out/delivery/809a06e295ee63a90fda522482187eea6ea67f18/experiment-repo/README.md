# Task investment under multitask aggregation

Reproducible score-space counterfactual analysis on frozen HELM MMLU v1.13.0 and Open LLM Leaderboard snapshots. The cost is the number of selected tasks; selected target scores improve by a stated fraction of headroom toward a specified ceiling. The analysis does not measure training cost or establish achievable contamination effects.

- `notes/methods.md` and `notes/analytic-results.md`: definitions and exact algorithms.
- `data/manifest.json` and `data/processed/audit.json`: public source provenance, hashes, exclusions and cohorts.
- `results/attacks_*.csv`: per-target optima, witnesses, reachability and solver status.
- `results/summary.csv`, `budget_curves.csv`, `paired_rules.csv`, `rank_strata.csv`: numerical figure/table inputs.
- `notes/primary-findings.md` and `notes/robustness-findings.md`: measured claims and interpretation limits.
- `reproduction/README.md`: dependencies, seeds, commands and runtime evidence.
- `tests/test_solvers.py`: independent exhaustive optimizer validation.

The primary full-improvement median budgets (mean / median / geometric / minimum / Borda) are 16 /21 /16 /11 /46 of57 HELM subjects, and 2 /3 /3 /3 /6 of6 Open LLM tasks. Gain restrictions materially alter reachability. These are conditional finite-cohort results; exceptions rule out universal ordering claims.

Manuscript and official presentation are owned by paper-repo and figtab-repo. This repository supplies their analysis material.
