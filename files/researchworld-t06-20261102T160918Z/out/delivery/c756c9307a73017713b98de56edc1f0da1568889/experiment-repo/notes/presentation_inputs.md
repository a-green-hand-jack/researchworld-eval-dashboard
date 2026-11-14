# Presentation evidence interface

The figure/table owner supplies final rendering scripts and their manuscript mapping. These source paths are relative to the analysis directory in the delivered project:

| Claim or visual | Numerical source | Generating script |
|---|---|---|
| Dataset support, baseline leading pair and found upper-bound counts | `results/summary/primary/datasets.csv` | `scripts/run_study.py`, `scripts/summarize.py` |
| Fixed leading-pair margin and bootstrap uncertainty | `results/summary/primary/uncertainty.csv`; raw `results/primary/*/bootstrap.csv` | same |
| Random, endpoint-only and influence perturbation curves, actual budgets, Monte Carlo intervals | `results/summary/primary/curves.csv`; raw `results/primary/*/curves.csv` | same |
| Ridge, support, tie and human-annotator controls | `results/summary/robustness/` | same, `--mode robustness` |
| Matched human/GPT-4 cell selection and reselected pair bootstrap | `results/summary/matched/`, `results/summary/matched_bootstrap/` | same, matched modes |
| Fixed original GPT-4–Claude reference contrast in joint bootstrap | `results/summary/matched_fixedpair/` | `scripts/matched_fixedpair.py` |
| Adjacent original-pair existence results and standardized-gap diagnostics | `results/diagnostics/adjacent_pairs.csv` | `scripts/diagnostics.py` |
| Home-adjusted NBA panel sensitivity | `results/nba_home/audits.csv` | `scripts/nba_home.py` |
| Actual primary edited rows and verified refits | `results/witnesses/` | `scripts/verify_witnesses.py` |

Fractions must be multiplied by100 for percent and percentage-point labels. All count searches are successful-attack upper bounds; no method certifies a minimum or robustness below it. Sampling intervals and random-edit Monte Carlo intervals describe different uncertainty sources. Leading-pair reversals and any-winner changes are separate columns. See `notes/results_handoff.md` for the full scope, exact findings and limitations.
