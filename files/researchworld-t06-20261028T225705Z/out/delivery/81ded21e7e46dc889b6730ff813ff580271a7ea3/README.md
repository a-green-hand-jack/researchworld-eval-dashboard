# Stability of pairwise-comparison (Bradley-Terry) leaderboards

Paper (NeurIPS 2026 template, anonymised): `paper/main.tex` -> `paper/main.pdf` (`cd paper && latexmk -pdf main.tex`).
Reproduction: `REPRODUCE.md` (environment, data versions and checksums, seeds, commands, run times, scripts -> result files).
Raw data are downloaded by `code/00_fetch_data.sh` into a directory outside this repository (`$RSENS_DATA`).

| paper item | script | reads |
|---|---|---|
| Table 1 | `tables/scripts/tab_summary.py` | `results/decisions_*.csv` |
| Table 2 (published rank) | `tables/scripts/tab_pubrank.py` | `results/pubrank_summary.csv` |
| Table 3 (adversarial vs random) | `tables/scripts/tab_adv_vs_benign.py` | `results/decisions_*.csv`, `results/benign_at_k_*.csv` |
| Appendix Table 4 (modelling variants) | `tables/scripts/tab_sensitivity.py` | `results/sensitivity.csv` |
| Figure 1 | `figures/scripts/fig1_fragility_vs_gap.py` | `results/adjacent_pairs_*.csv`, `results/nba_seasons.csv` |
| Figure 2 | `figures/scripts/fig2_design_control.py` | `results/mtbench_contrast.csv`, `arena_controls.csv`, `commonN.csv`, `decisions_*.csv`, `nba_seasons.csv` |
| Figure 3 | `figures/scripts/fig3_top1_adv_vs_benign.py` | `results/decisions_*.csv`, `results/benign_*.csv` |
| Appendix Figure 4 (SYNTHETIC) | `figures/scripts/figA1_synthetic.py` | `results/synthetic.csv` |

Run figure and table scripts from the repository root, e.g. `python3 figures/scripts/fig1_fragility_vs_gap.py results figures`.
Every number quoted in the text of the paper is read from `results/` (mainly `summary_decisions.csv`, `summary_groups.csv`, `summary_fragility_vs_gap.csv`, `summary_synthetic_regression.csv`, `benign_*.csv`, `commonN.csv`, `sensitivity.csv`, `pubrank_summary.csv`).
