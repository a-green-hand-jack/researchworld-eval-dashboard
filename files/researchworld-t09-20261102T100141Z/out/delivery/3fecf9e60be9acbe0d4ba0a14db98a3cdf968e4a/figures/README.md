# figures/ and tables/: generators for the paper's figures and tables

Run from `figures/` (`python3 figN_*.py`) and `tables/` (`python3 tableN_*.py`). Inputs come only from `results/`
(experiment-repo); `GATE_RESULTS`, `GATE_FIGOUT`, `GATE_TABOUT` override input/output directories. All metrics and the bootstrap
(B=1000, seed 20261102, percentile 95% CI resampling replicates; relative metrics divide by the cell's exact |tau|: 2 in the main grid, 1+gamma in E3) are defined once in `common.py`.
Dependencies: numpy, pandas, pyarrow, scipy, matplotlib (versions in `code/README.md`). Runtime: seconds each, 1 CPU.
Rendered PDFs are committed next to their scripts; regenerate with `bash figures/make_all.sh` (set `GATE_RESULTS` to the experiment-repo `results/` directory).

Built from experiment-repo `results/` at revision fe30525e7721a0acf6224c962d793feaae6ae426 (replicates.parquet sha256 prefix eb3fc94d4df661e6). MAINML (ridge/GBM on the 72 main cells) is not in it yet.
Only `fit_data == observed` rows are used by the figures, except where a script reads `diagnostics.csv` (population fits).

## Paper figure/table -> output file -> script -> input
Keyed by the paper's own numbers (paper-repo `main` at b12ca49, built; the numbers follow the order of the figures in the PDF).
`python3 figures/paper_numbers.py <paper-repo>/paper` prints the current numbers from `main.aux` and the include width of every file, to re-check this table
if the paper is renumbered (the file names below are stable; only the numbers change). The earlier internal names (`fig8_...`, `figM_...`) are just file names.

| Paper item | Output file | natural size w x h (in) | Script (run from `figures/`) | Input (`results/`) | What it shows |
|---|---|---|---|---|---|
| Fig. 1 | `fig1_headline.pdf` | 5.46 x 3.47 | `fig1_headline.py` | MAIN | RQ1: relative RMSE of every estimator, mechanism (panel) x graph (x axis), Bernoulli(0.5). A cross on the bottom axis = Hajek-strict undefined in >5% of replicates |
| Fig. 2 | `figM_rmse_sweeps.pdf` | 5.27 x 1.98 | `fig_more.py main` | E1_size, E3_gamma, E2_degree, `theory_check_var.csv` | rel. RMSE of DM and OLS variants vs n, rho and mean degree; crosses = P2 predicted SD of OLS(z,f) |
| Fig. 3 | `fig8_curvature_population_bias.pdf` | 5.35 x 3.39 | `fig_sweeps.py curv_pop` | E4_curv (`fit_data=population`), `theory_check_bias.csv` | approximation bias of OLS(z,f) and quadratic OLS vs design p; crosses = P1 prediction |
| Fig. 4 | `fig15_model_class.pdf` | 5.36 x 3.07 | `fig_more.py model` | E7_model | OLS / quadratic / cubic OLS vs ridge on rich features vs gradient boosting (rel. RMSE, bias) |
| Fig. 5 | `fig13_coverage_n.pdf` | 3.16 x 2.12 | `fig_sweeps.py cover` | E10_coverage | coverage of cluster-robust vs HC 95% CI, n = 1000 vs 4000 |
| Fig. 6 | `figA1_headline_bern0.1.pdf` | 5.44 x 3.47 | `fig1_headline.py bern0.1` | MAIN | as Fig. 1, Bernoulli(0.1) |
| Fig. 7 | `figA1_headline_cluster0.5.pdf` | 5.46 x 3.47 | `fig1_headline.py cluster0.5` | MAIN | as Fig. 1, graph-cluster randomisation |
| Fig. 8 | `figA2_seed_replication.pdf` | 3.02 x 2.79 | `fig_sweeps.py seed` | MAIN, MAIN_s2 | rel. RMSE under the second seed set vs the first, 332 cell x estimator pairs |
| Fig. 9 | `fig2_bias_sd.pdf` | 4.80 x 2.57 | `fig2_bias_sd.py` | MAIN | abs(bias)/abs(tau) vs SD/|tau|, bias- vs variance-dominated error, by design |
| Fig. 10 | `fig4_coverage.pdf` | 5.17 x 2.48 | `fig4_coverage.py` | MAIN (ci_lo/ci_hi) | coverage vs abs(bias)/SD with the normal-theory curve |
| Fig. 11 | `fig3_h7_diagnostic.pdf` | 5.12 x 2.66 | `fig3_h7_diagnostic.py` | `diagnostics.csv`, MAIN | H7: exposure-support statistic vs population bias of OLS(z,f) |
| Fig. 12 | `fig12_design.pdf` | 5.28 x 2.17 | `fig_sweeps.py design` | E8_design | Bernoulli vs graph-cluster randomisation at three Louvain resolutions |
| Fig. 13 | `fig5_graph_error.pdf` | 5.48 x 3.37 | `fig5_graph_error.py` | E11_grapherr | error vs share of edges dropped and re-added in the feature graph |
| Fig. 14 | `fig10_degree.pdf` | 5.28 x 1.99 | `fig_sweeps.py degree` | E2_degree | error vs mean degree (SBM, ER) |
| Fig. 15 | `fig16_noise.pdf` | 5.29 x 1.98 | `fig_more.py noise` | E9_noise | rel. RMSE vs idiosyncratic noise, three cluster-noise levels |
| Fig. 16 | `fig6_size.pdf` | 5.28 x 2.09 | `fig_sweeps.py size` | E1_size, `theory_check_var.csv` | bias, SD and rel. RMSE vs n (correct linear exposure) |
| Fig. 17 | `fig7_gamma.pdf` | 5.28 x 2.19 | `fig_sweeps.py gamma` | E3_gamma | error vs interference ratio rho |
| Fig. 18 | `fig11_specification.pdf` | 4.72 x 6.01 | `fig_sweeps.py spec` | E6_spec | feature set x form of interference, rel. RMSE |
| Fig. 19 | `fig11b_specification_bias.pdf` | 5.26 x 2.69 | `fig_more.py spec_bias` | E6_spec | signed relative bias heat map, same grid |
| Fig. 20 | `fig14_graph_families.pdf` | 5.29 x 2.37 | `fig_more.py graphs` | E5_graphs | ten graph families: rel. RMSE and CI coverage |
| Fig. 21 | `fig9_curvature_rmse.pdf` | 5.29 x 3.39 | `fig_sweeps.py curv_obs` | E4_curv (observed) | observed rel. RMSE vs design p |
| Fig. 22 | `fig9b_curvature_bias_observed.pdf` | 5.26 x 3.39 | `fig_more.py curv_bias` | E4_curv (observed and population) | observed vs population-fit bias (symlog) |
| Fig. 23 | `fig17_theory_check.pdf` | 5.37 x 2.27 | `fig_more.py theory` | `theory_check_{var,bias}.csv` | P2 predicted vs empirical SD; P1/P3 predicted vs empirical population bias |
| Table 1 | `tables/table2_failure_modes.tex` | - | `tables/table2_failure_modes.py` | `contrasts.csv`, `replicates.parquet`, MAIN | OLS(z,f) vs DM per mechanism x design |
| Table 2 | `tables/table1_setup.tex` | - | `tables/table1_setup.py` | `config.json`, `replicates.parquet` | setup of the main grid; GATE = 2 computed exactly, not rescaled |
| Table 3 | (typeset in `paper-repo`) | - | `sections/appendix.tex` | - | hypotheses and verdicts (analysis owner's text, not a generated table) |
| Table 4 | `tables/table3_contrasts.tex` | - | `tables/table3_contrasts.py` | `contrasts.csv` | paired MSE contrasts over every experiment |

## Sizes: include every figure at its natural size
Every figure is drawn at the size it has in the paper (text 6-7 pt: tick labels 7 pt, legends and annotations 6-6.5 pt; mathtext sub/superscripts are 70% of that).
Scaling a PDF down shrinks the text by the same factor, so **include each figure at its natural width** (`width=<w>in`, or `\includegraphics{...}` without a width option; \linewidth = 5.5 in):
widths in the table are the natural widths; Fig. 1, 3, 4, 6, 7, 13, 21, 22 are 5.3-5.5 in wide (use `width=\linewidth`), Fig. 5 and Fig. 8 are single-column-size (3.16 in = 0.57 \linewidth and 3.02 in = 0.55 \linewidth),
Fig. 9 is 4.8 in (0.87 \linewidth), Fig. 18 is 4.72 x 6.01 in. Log axes carry plain-number tick labels (0.1, 1, 10) rather than 10^k.
Graph names in Fig. 1/6/7 are abbreviated "Stanf.3" (= Stanford3) to fit the half-width panels; a cross on the bottom axis is explained in the legend.

## Not yet drawn
MAINML (ridge/GBM on the 72 main cells; experiment-repo is still running it) is the only planned result not drawn; Fig. 4 (E7) carries the flexible-learner
comparison until it lands. Nothing is drawn from placeholders. `fig_sweeps.py` takes ~2 min (one parquet read, bootstrap per cell); the whole of `make_all.sh` ~6 min on 1 CPU.
