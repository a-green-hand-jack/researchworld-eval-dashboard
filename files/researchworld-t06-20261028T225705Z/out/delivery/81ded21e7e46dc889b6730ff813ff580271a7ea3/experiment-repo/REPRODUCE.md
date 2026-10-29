# Reproduction guide: analysis code and results

All numbers in `results/` are produced by the scripts in `code/` from the pinned public data below; nothing is hand-entered. Figures/tables are built by `figures/scripts/` and `tables/scripts/` (owned by the figure position) from `results/` only.

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6 (+ pyarrow for parquet); no GPU; recorded in `results/ENV.txt`. Wall-clock below is for a 2-CPU container that was shared by up to ~20 simultaneous jobs; the single-job numbers are lower.

## Data (not committed; `code/00_fetch_data.sh` downloads and verifies sha256; set `RSENS_DATA` to the directory)
| data | source @ version | licence | sha256 |
|---|---|---|---|
| Arena 55k human preferences (57,477 battles, 64 models) | HF `lmarena-ai/arena-human-preference-55k` @18c298340948c0e7f7727399fd459cca6ce0ca6f, `train.csv` | apache-2.0 | 0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2 |
| MT-Bench human judgements (3,355; 6 models) | HF `lmsys/mt_bench_human_judgments` @f7d2896d2cc5d80f8b55c2bbc722613555233c25 | cc-by-4.0 | 4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769 |
| MT-Bench GPT-4 pair judgements (2,400; 6 models) | same repo, `gpt4_pair-…parquet` | cc-by-4.0 | 57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71 |
| NBA Elo game file (63,157 games; used: `_iscopy==0`) | github `fivethirtyeight/data` @4c1ff5e3aef1816ae04af63218015066e186c147, `nba-elo/nbaallelo.csv` | CC-BY-4.0 | d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc |
Not used (deferred by the plan): Arena 140k, potsawee judge verdicts, WebDev Arena. No synthetic data is used except in `09_synthetic.py`, whose outputs (`synthetic.csv`, `summary_synthetic_*.csv`) are labelled SYNTHETIC and are calibration only.

## Model and conventions (fixed before running)
BT logistic MLE, score gap = log-odds, ridge 1e-3 on all parameters (sensitivity 1e-1, 1e-5). Ties (Arena "tie" and "both bad"; MT-Bench "tie" and GPT-4 "tie (inconsistent)") = half win to each side; sensitivity: ties dropped. NBA: lg_id NBA only (ABA 1968-76 is a separate league: its seasons are separate leaderboards `nba:YEAR:ABA`; mixing it into the all-history fit produced an ABA-only team at rank 4 in an early run, which is why it is excluded), one shared home-advantage parameter (sensitivity: none), seasons = regular season only. Perturbations: drop m comparisons, flip m decisive comparisons, inject m new comparisons for the promoted target. Every adversarial budget is a **verified upper bound on the smallest budget**: influence ranking of candidates, exact refits, bisection on the alteration order; a drop attack may not increase the number of connected components of the comparison graph. Decisions, targets and controls: `story-repo` PLAN.md (v4); output columns: `results/SCHEMA.md`.

## Scripts, outputs, run time, seeds
| script (run from `code/`) | writes to `results/` | time | seeds / draws |
|---|---|---|---|
| `00_fetch_data.sh` | (data dir) | 1 min | - |
| `01_adjacent_pairs.py DS` for arena55k, mtbench_human, mtbench_gpt4, nba | `adjacent_pairs_DS.csv` | 1 s MT-Bench; 80-110 s Arena/NBA | deterministic |
| `02_decisions.py DS B B_TAU` (arena55k 20 6; nba 20 6; mtbench_* 100 100) | `decisions_DS.csv` | MT-Bench 190 s; NBA 730 s; Arena 1030 s | resample r uses seed 1000+r |
| `03_benign.py DS R` (arena55k 100; nba 100; mtbench_* 200) | `benign_DS.csv`, `benign_pairs_DS.csv`, `scores_DS.csv` | 20-90 s | seed 2024 |
| `04_seasons_commonN.py seasons` | `nba_seasons.csv` (78 leaderboards: 69 NBA + 9 ABA seasons) | 75 s | deterministic |
| `04_seasons_commonN.py commonN 100` | `commonN.csv` (N=2000 all participants; N=2000 & 6 random participants out of the 20 most compared) | 850 s | seed 77 |
| `04_seasons_commonN.py arena_controls 50` | `arena_controls.csv` (Arena subsampled to N=2400/3355 with 64 models; top-6 models by BT rank, full and subsampled) | 190 s | seed 78 |
| `05_subsample_b50.py DS R` (arena55k 100; nba 100; mtbench_* 200; nba_seasons 100) | `subsample_DS.csv` | 20-840 s | seed 5 |
| `07_mtbench_contrast.py 100` | `mtbench_contrast.csv` | 5 min | seeds 3 |
| `08_sensitivity.py` | `sensitivity.csv` | 3 min | deterministic |
| `09_synthetic.py 30` | `synthetic.csv` (SYNTHETIC) | 13 min | seed 9 |
| `10_pubrank.py` | `pubrank.csv`, `pubrank_summary.csv` | 1 min | deterministic |
| `11_benign_at_k.py DS R` (200 draws; 500 for mtbench_human) | `benign_at_k_DS.csv` | 3-130 s | seed 11 |
| `06_summaries.py` (after all of the above) | `summary_*.csv` | seconds | seed 6 (bootstrap CIs of medians) |
Seconds per verified attack: MT-Bench 0.01-0.1 s; NBA/Arena 1-2 s (drop/flip, one pair), 3-10 s (injection, one pair), 20-100 s (full Kendall-tau greedy attack).

## Known limitations of the analysis (details in the paper)
Budgets are upper bounds on the minimum (found attacks), not certified minima. Bootstrap CIs resample comparisons as if independent; Arena rows carry no user or prompt ids, so they are optimistic. Arena/NBA attack-resamples: B=20 (Kendall-tau attacks only on the first 6 resamples because each takes ~100 s); MT-Bench B=100. Arena's published-style rank uses Wald (Hessian) intervals, not bootstrap ones. Davidson/Rao-Kupper tie models were not run. A fit is a snapshot of the data, not a live leaderboard.

## Data-use and disclosure statements
No literature was searched or read by the analysis position; starter-literature item 8 and any material about the barred paper were not accessed. Code was written with an LLM assistant (Claude); all results come from running the committed code.
