# figures/

Generators for every figure and table of the paper. They read only `results/` of `experiment-repo` (per-prediction table) except `make_data_table.py`, which reads the pinned `.jbl` score matrices (benchmark-prediction commit 55faff496947789f94e6b5908c77cbc3e84f81ad).

| output | script | command |
|---|---|---|
| `generated/tab_data.tex`, `data_summary.csv` | `make_data_table.py` | `python3 -I make_data_table.py <dir with *.jbl> generated` (seconds) |
| `fig_macro_curves.pdf` (main text: macro-average MAE and Spearman vs. n, both split types, 95% CI over seeds) | `make_figures.py` | `python3 make_figures.py <results table> <outdir> --baseline <name>` |
| `fig_mae_vs_n_<split>.pdf`, `fig_spearman_vs_n_<split>.pdf` (appendix: per-benchmark grid, 3 columns, 95% CI over seeds) | `make_figures.py` | same |
| `fig_paired_diff.pdf` (method minus baseline, same benchmark/split/seed) | `make_figures.py` | same |
| `fig_scatter_<split>.pdf` | `make_figures.py` | same (`--scatter-n`) |
| `tab_{mae,rmse,kendall}_<split>_n<N>.tex` (mean; arrows = paired-difference CI vs. baseline excludes 0) | `make_figures.py` | same (`--table-n`) |
| `fig_pairwise_vs_gap.pdf` | `make_figures.py` | same |

Each figure is written with a CSV of the plotted values. Input columns: `benchmark, method, n, split_type, seed, target_model, true, pred` (accuracies in [0,1]). Errors are in accuracy points. Uncertainty: percentile bootstrap (2000 resamples) over seeds, resampled independently within each benchmark for the macro-average (benchmarks are the units, equal weight). Needs numpy, pandas, scipy, matplotlib, joblib.

Method labels in figures (`common.LABELS`): B0 = `const`, B1 = `random+mean`, B2 = `strat+mean`, B3 = `random+cal`, P1 = `omp+ridge`, P3 DR/EB = `strat+lowrank_dr/_eb`. Rank metrics are undefined for B0 (constant prediction) and omitted. Spearman of B3 equals B1 by construction (monotone recalibration).
The macro-average panels use only budgets n at which all 13 benchmarks have data (n<=100); `generated/PROVENANCE.txt` records the results commit and the exact command.
