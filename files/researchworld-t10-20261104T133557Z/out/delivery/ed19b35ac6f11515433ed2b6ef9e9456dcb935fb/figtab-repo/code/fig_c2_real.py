"""[reads] results/summary_mean_real.csv, results/summary_plankton_noshift.csv  [writes] figures/fig_c2_real.{pdf,png}, figures/fig_c2_real_app_a.{pdf,png}  (run via run_all.sh)
C2 (+C0): like-for-like width ratio and coverage vs n on the real pools, t-calibrated intervals.
Ratio = cross-fitted interval / PPI++ with the same t calibration (ratio_lfl), paired draws, band = 95% CI over replicates.
Coverage panels also show the practitioner default PPI++ Wald and studentised-bootstrap PPI++ (dashed); Wilson 95% bars.
Main figure: the four roled pools, compact.  Appendix figures: all seven pools + plankton (no shift) over two figures.
Input: data_in/summary_mean_real.csv, summary_plankton_noshift.csv."""
import pandas as pd
import widthcov as wc, style
df = pd.concat([wc.read("data_in/summary_mean_real.csv"), wc.read("data_in/summary_plankton_noshift.csv")])
T = lambda g: style.DATASET_LABEL.get(g, g.replace("_", " "))
RM = ["cf_lin_f_t", "cf_iso_f_t", "cf_gbm_f_t", "cf_gbm_fX_t"]
CO = ["ppi++_t", "ppi++", "ppi++_boot"]
wc.draw(df, "figures/fig_c2_real", "dataset", ["census_income", "gene_expression", "galaxies", "forest"], RM, CO,
        ylabel="width / PPI++ width", titles=T, width=1.0, height=2.75, cov_ylim=(0.78, 1.0), ncol_leg=4, fs=6.5, ms=3)
wc.draw(df, "figures/fig_c2_real_app_a", "dataset", ["alphafold", "census_healthcare", "census_education", "plankton_noshift"],
        ["cf_lin_f_t", "cf_iso_f_t", "cf_gbm_f_t", "cf_lin_fX_t", "cf_gbm_fX_t"], CO, ylabel="width / PPI++ width", titles=T,
        width=1.0, height=2.9, cov_ylim=(0.78, 1.0), ncol_leg=4, fs=6.5, ms=3)
