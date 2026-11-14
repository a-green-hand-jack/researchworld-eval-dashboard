# Map: paper figure / table -> generating script

Owner: figtab-repo. Every figure and table is generated from files in `results/` (experiment-repo) only; nothing is drawn from hand-entered numbers.
Run from the repository root: `python figures/<script>.py` (writes `figures/<name>.pdf`) or `python tables/<script>.py` (writes `tables/<name>.tex`).
Paths can be changed with `FIGTAB_RESULTS` (default `results`), `FIGTAB_OUT` (default `figures`), `FIGTAB_TOUT` (default `tables`).
Shared code: `figures/style.py` (NeurIPS text width 5.5 in, Okabe-Ito colours), `figures/common.py` (loading, Wilson and mean intervals, cell filters).
Requires pandas, pyarrow, numpy, matplotlib (versions in `REPRODUCE.md`). Each script runs in seconds on one CPU.

T0 outputs were generated from `results/*_t0.*` as committed in experiment-repo (code revision 3e7c1bc, results of 92fd717) and inspected.
T1 (real MMLU-Pro outcomes, Qwen2.5-1.5B, cached 24x2000 matrix) outputs were generated from `results/*_t1*.*` of experiment-repo; T1 uncertainties are delete-a-block SEs (replicates share items), not replicate SEs or Wilson intervals.

| item | claim | script | reads | output | status |
|---|---|---|---|---|---|
| Fig A: optimism vs n by K, by tau; theory curve | Q1a, Q1b | `figures/fig_a_optimism.py` | `results/runs_t0.parquet`, `results/theory_curve_t0.csv` | `figures/fig_a_optimism.pdf` | generated (T0); T1 in `fig_a_t1.py` |
| Fig B: optimism by procedure, correlation, baseline accuracy, leakage | Q1b | `figures/fig_b_factors.py` | `results/runs_t0.parquet` | `figures/fig_b_factors.pdf` | generated (T0) |
| Fig C: coverage of the nominal-95% interval per method | Q2a, Q2b | `figures/fig_c_coverage.py` | `results/methods_t0.parquet` | `figures/fig_c_coverage.pdf` | generated (T0); T1 in Table G / H |
| Table C: bias, RMSE, coverage, width, item cost | Q2a, Q2b | `tables/table_c_calibration.py` | `results/methods_t0.parquet` | `tables/table_c_calibration.tex`, `table_c_main.tex` (compact: K=200, n=100), `table_c_m3.tex` (M3 bootstrap cells), `table_c_all_cells.csv` | generated (T0); T1 in Table G / H |
| Table D: tuned-vs-baseline false-claim rate and power | Q1c, Q2a | `tables/table_d_decisions.py` | `results/decisions_t0.csv` | `tables/table_d_decisions.tex`, `table_d_all_cells.csv` | generated (T0); T1 in Table G / H |
| Table E: A-vs-B false-winner and detection rates | Q1c, Q2a | `tables/table_e_ab.py` | `results/decisions_ab_t0.csv` | `tables/table_e_ab.tex` | generated (T0) |
| Table F: compute actually used | all | `tables/table_f_compute.py` | `results/compute.csv` | `tables/table_f_compute.tex` | generated (T0 and T1 jobs) |
| Fig A-T1: optimism vs n by K, real matrix | Q1a, Q1b | `figures/fig_a_t1.py` | `results/runs_t1.parquet`, `results/summary_gap_t1.csv` | `figures/fig_a_t1.pdf` | generated (T1) |
| Fig B-T1: exhaustive vs halving vs greedy | Q1b | `figures/fig_b_t1.py` | `results/runs_t1.parquet` | `figures/fig_b_t1.pdf` | generated (T1) |
| Table G: bias, RMSE, coverage, width, cost per method, real matrix | Q2a, Q2b | `tables/table_g_t1_calibration.py` | `results/methods_t1.parquet`, `results/runs_t1.parquet` (block ids) | `tables/table_g_t1_calibration.tex`, `table_g_main.tex` (compact), `table_g_all_cells.csv` | generated (T1) |
| Table H: ranking flips, false-winner and detection rates of tuned pairs, real matrix | Q1c, Q2a | `tables/table_h_t1_pairs.py` | `results/methods_t1_pairs.parquet`, `results/runs_t1_pairs.parquet` (cross-checked against `decisions_ab_t1.csv`) | `tables/table_h_t1_pairs.tex`, `table_h_t1_decisions.tex`, `table_h_t1_decisions_n500.tex`, `table_h_all_cells.csv` | generated (T1) |
| Fig T1-subjects: gap per MMLU-Pro subject (appendix) | Q1a | `figures/fig_t1_subjects.py` | `results/subject_breakdown.csv` | `figures/fig_t1_subjects.pdf` | generated (T1) |
| Fig T1-check: observed gap vs closed form and vs T0 (appendix) | Q1a, Q1b | `figures/fig_t1_check.py` | `results/summary_gap_t1.csv`, `results/t0_vs_t1_gap.csv` | `figures/fig_t1_check.pdf` | generated (T1) |
| Fig for live tool vs cached replay | Q2b | -- | -- | -- | **not completed**: experiment-repo ran no live tool (replays only); not drawn |

Conventions: T0 intervals over replicates are mean ± 1.96·SE of the replicate mean; coverage and decision rates use Wilson 95% intervals; T0 is synthetic (known truth), T1 real MMLU-Pro outcomes.
Reference world for the headline figures/tables: rho=0.6, baseline accuracy 0.3, exhaustive search, no leakage, main grid (1000 replicates per cell). The extra `|m3` cells (300 replicates) are the only ones with the M3 bootstrap methods and are reported separately (Table C, M3 block).
