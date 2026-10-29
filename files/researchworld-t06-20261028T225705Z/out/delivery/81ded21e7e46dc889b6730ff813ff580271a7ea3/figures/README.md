# Figures and tables: manifest

Every item is made by the named script from tidy CSVs of `experiment-repo` (`results/`, schema in `results/SCHEMA.md`); run from the repo root:
`python3 figures/scripts/<script>.py results figures` and `python3 tables/scripts/<script>.py results tables`.
`figures/scripts/style.py` (NeurIPS text width 5.5 in, text >= 7 pt, colour-blind-safe palette, series also differ by marker) and `common.py` are shared.
**Version of this delivery: final tier-1 build, from `results/` as merged in paper-repo at aaf296b (experiment-repo final delivery, `results/ENV.txt` records library versions).** Regenerate if `results/` changes.
Notes for captions: Arena budgets sit at the floor of one comparison for many pairs (k >= 1); Table 1 shows a bootstrap interval only where >= 20 attack resamples exist (Kendall rows for Arena and NBA: point value only); `commonN.csv` is used for the random-6 row of Fig. 2(b) only (control N+p; control N has disconnected graphs, not used); Fig. 2(b) top-6 rows use the plan's top-by-rank control (near-tied GPT-4 variants), so their budgets are not comparable with the random-6 row (state this).

All budgets are *smallest attacks found* (each verified by exact refit): upper bounds on the true minimum, never proofs of robustness.

| item | claim | source files | script | place |
|---|---|---|---|---|
| Fig. 1 `figures/fig1_fragility_vs_gap.pdf` | C1: the smallest swap of adjacent pairs scales with the standardised gap z; when z < 1 (most Arena/NBA pairs) a handful of comparisons suffices | `adjacent_pairs_*.csv`, `nba_seasons.csv` | `figures/scripts/fig1_fragility_vs_gap.py` | main |
| Fig. 2 `figures/fig2_design_control.pdf` | C3: (a) same 1,814 questions: expert vs GPT-4 judge; (b) size/structure controls (Arena subsampled to MT-Bench N, top-6, NBA seasons); no causal "design" claim | `mtbench_contrast.csv`, `arena_controls.csv`, `commonN.csv`, `decisions_*.csv`, `nba_seasons.csv` | `figures/scripts/fig2_design_control.py` | main |
| Fig. 3 `figures/fig3_top1_adv_vs_benign.pdf` | C2: adversarial top-1 budget (a) vs. random removal/flip at the same size (b) | `decisions_*.csv`, `benign_*.csv` | `figures/scripts/fig3_top1_adv_vs_benign.py` | main (or appendix if space is short) |
| Table 1 `tables/tab_summary.tex` | C1: per-dataset budgets for top-1 and tau<0.95, % of N, bootstrap interval | `decisions_*.csv` | `tables/scripts/tab_summary.py` | main |
| Table 2 `tables/tab_adv_vs_benign.tex` | C2: attack size k vs. P(top-1 changes) under random removal/flip of m = k and m = 10k comparisons | `decisions_*.csv`, `benign_at_k_*.csv` | `tables/scripts/tab_adv_vs_benign.py` | main |
| Fig. A1 `figures/figA1_synthetic.pdf` | C4: SYNTHETIC BT worlds, budget vs. leader gap, N, p | `synthetic.csv` | `figures/scripts/figA1_synthetic.py` | appendix |
| Table A1 `tables/tab_sensitivity.tex` | C5: ties dropped, ridge, NBA home term | `sensitivity.csv` | `tables/scripts/tab_sensitivity.py` | appendix |
| Table A3 `tables/tab_topk.tex` | top-3/5/10 set budgets (comparisons, bootstrap interval); top-10 undefined for the 6-model MT-Bench | `decisions_*.csv` | `tables/scripts/tab_topk.py` | appendix |
| Table A4 `tables/tab_gapfit.tex` | C1/C4: n adjacent pairs, Spearman(k,z) and log-log slope per dataset and attack (n=5 for MT-Bench: nearly uninformative) | `summary_fragility_vs_gap.csv` | `tables/scripts/tab_gapfit.py` | appendix |
| Table A2 `tables/tab_pubrank.tex` | Arena-convention published rank under the cheapest top-1 attack | `pubrank_summary.csv` | `tables/scripts/tab_pubrank.py` | appendix |

## Suggested captions (numbers must be read from the items, not from here)
- **Fig. 1.** Smallest verified attack that swaps an adjacent pair of the ranking, as a fraction of the N comparisons, against the pair's gap in standard errors (z = BT score gap / se). (a) removals, (b) label flips. Markers: adjacent pairs of the full-data ranking of each dataset; crosses: NBA single seasons (leader vs. ranks 2-4). Log-log axes. Values are upper bounds on the minimum; pairs with k = 0 (one season) are omitted.
- **Fig. 2.** (a) Cheapest top-1 attack for the MT-Bench expert and GPT-4-judge verdicts on the 1,814 questions both cover (bootstrap bars: 100 resamples; expert 1-vote-per-item: 100 random draws). (b) Same quantity for size/structure controls fixed before running. Dot: median over n subsamples (bar: 2.5-97.5%) for subsampled rows, original data for full datasets. Cross-dataset differences are confounded with N, number of participants, ties and structure.
- **Fig. 3.** (a) Smallest verified attack changing the top-1 (dot: original data; bar: 2.5-97.5 percentile of bootstrap resamples, when >= 20). (b) Probability that random removal (solid) or flipping (dashed) of m comparisons changes the top-1, Wilson 95% band for removal; vertical lines: adversarial budgets.
- **Table 1 / 2.** As in the scripts' docstrings; Table 2's random columns are simulated at exactly m = k and m = 10k (Wilson 95% intervals).
- **Fig. A1.** SYNTHETIC data: simulated Bradley-Terry worlds, not real leaderboards.
