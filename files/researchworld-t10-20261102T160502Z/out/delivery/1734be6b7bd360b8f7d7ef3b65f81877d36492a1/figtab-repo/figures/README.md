# Figures and tables

Every figure and table is produced by one script from the result CSVs of experiment-repo (`code/results/`); nothing is typed in
by hand. `bash make_all.sh` rebuilds all of it (about one minute, CPU only). Environment: Python 3, numpy, pandas, scipy,
matplotlib; `fig_calibration.py` also needs the `ppi-python` 0.2.3 data (`PPI_DATA_DIR`). The experiment-repo revision the
current outputs were built from is in `PROVENANCE.txt`.

## Output → script → input

| output (`figures/`) | claim | script (`figures/src/`) | input (`code/results/`) |
|---|---|---|---|
| `real_main.pdf` coverage and paired width ratio vs n, six primary datasets, N = 20n; M1-M4, floor dotted | C1, C3 | `fig_real.py` | `summary_final_real_primary.csv`, `theory_predicted_ratios.csv` |
| `real_correction.pdf` M3, M5(M3), M4, M5(M4): coverage and width ratio | C3 | `fig_real.py` | same |
| `real_appendix.pdf` census healthcare / education | C1, C3 | `fig_real.py` | `summary_final_real_appendix.csv` |
| `real_nsweep.pdf` N = n, 5n, 20n, 20000 at n = 100, 400 | C1, C2 | `fig_real.py` | `summary_final_real_nsweep.csv` |
| `plugin_cost.pdf` measured / predicted M4:M3 ratio | C1 | `fig_theory_vs_measured.py` | `summary_final_real_primary.csv`, `theory_predicted_ratios.csv` |
| `calibration_curves.pdf`, `calibration_gap.pdf` E[Y given f] against the best affine fit | C1, C2 | `fig_calibration.py` | `theory_population.csv`, ppi-python data |
| `synthetic_kappa.pdf` width ratio and coverage vs kappa | C2 | `fig_synthetic.py` | `summary_final_synth.csv`, `theory_check_synth_final.csv` |
| `synthetic_factors.pdf` same vs n, N, SNR | C2 | `fig_synthetic.py` | same |
| `plankton_shift.pdf` shift vs within-2013 control | C4 | `fig_shift.py` | `summary_final_shift.csv` |
| `tables/tab_methods` methods and information used | - | `tables.py` | (static) |
| `tables/tab_datasets` Var(Y), rho^2, R^2_cal, floor ratio | C1 | `tables.py` | `theory_population.csv`, `theory_predicted_ratios.csv` |
| `tables/tab_real_cov`, `tab_real_width` n = 100, 400; `tab_real_full.csv` has every cell with CIs | C1, C3 | `tables.py` | `summary_final_real_primary.csv` |
| `tables/tab_regimes` cells where M4 is narrower / indistinguishable / wider than M3; undercoverage counts | C1, C2 | `tables.py` | `summary_final_{real_primary,real_appendix,synth}.csv` |
| `tables/tab_synth_tail` Student-t noise | C2, C3 | `tables.py` | `summary_final_synth.csv` |
| `tables/tab_boot` bootstrap PPI++ ablation | C3 | `tables.py` | `sim_boot.csv` |
| `tables/tab_forest_wor` draws with vs without replacement | - | `tables.py` | `summary_final_real_primary.csv`, `summary_final_forest_wor.csv` |
| `tables/tab_native` intervals at native sizes (one realisation) | - | `tables.py` | `full_data_intervals.csv` |

C5 (conformal baseline): the Bonferroni conformal interval is infinite unless n >= N/alpha - 1 (experiment-repo README), which never holds at N = 20n, so
it has no figure; the paper states it in text.

## Conventions
- Method colours, markers and line styles are fixed across all figures (`src/common.py`, Okabe-Ito palette). Hollow marker with dotted line: t(n-1) critical value; hollow square with dash-dot line: jackknife. M4 is read from `frozen_choices.json`.
- Coverage panels: nominal 0.95 line (black), shaded band 0.95 +- 1.96 sqrt(0.95*0.05/R) (range of a nominally covering method's Monte-Carlo estimate), points with Wilson 95% intervals (computed by experiment-repo from the R replicates).
- Width panels: paired geometric-mean ratio to M3 (PPI++, `ppi_py`, clipped lambda-hat) on identical draws, with 95% percentile-bootstrap CI over replicates (experiment-repo); ratio 1 black; values beyond the axis are drawn on the frame and annotated. Dotted: asymptotic floor ratio for M4 from the population quantities (`theory_predicted_ratios.csv`, `theory_check_synth_final.csv`).
- M1 (classical) is 1.2-3.6 times wider than M3 and left out of the width panels; it is in `tab_real_width`.
- Multiplicity: bold in tables and any reading of a single cell is uncorrected (single-cell Wilson upper bound below 0.95, R = 2000); claims should rest on patterns across n or datasets, not on one cell.
- Tables: bold coverage = Wilson upper bound below 0.95. Ratios in the `.tex` show `ratio +- half the CI width`; the `.csv` files hold exact bounds.
- Width <= 5.5 in (NeurIPS 2026 text width), text >= 7 pt at final size, vector PDF with embedded fonts, PNG at 300 dpi.

## C4 (shift) reading note
`plankton_shift` compares the within-2013 control (`tag=control`) with the 2013-labelled / 2014-unlabelled shift (`tag=shift`). In the final runs
M2 (PPI), M3 (PPI++, clipped lambda-hat) and the jackknife variant of M3 hold close to 0.95 under shift; classical, unclipped PPI++ (`ppipp_nc`) and the calibrated
variants collapse, because lambda-hat is about 1.4 > 1 there and the clip at 1 protects M3 (`shift_lambda_check.csv`, `FINDINGS.md` in experiment-repo).
So the figure does not show "all PPI-type intervals fail under shift"; the caption should say which methods fail and why.

## Caption content the paper needs
Each caption should state n, N (= 20 n unless stated), alpha = 0.05, R = 2000 replicates, the truth definition (full-data mean of Y), the colour/marker key
(shared across figures), that the width panels are paired ratios to M3 with bootstrap CIs, and that the dotted line is the asymptotic floor for M4.
