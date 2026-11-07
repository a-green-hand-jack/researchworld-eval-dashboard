"""[reads] results/summary_synth.csv, results/theory_synth.csv  [writes] figures/fig_c3_synth.{pdf,png}, figures/fig_c3_synth_app_knob_rho1.*, figures/fig_c3_synth_app_named_{a,b}_rho{0.1,1}.*  (run via run_all.sh)
C3: synthetic scenarios with known truth.  Measured paired width ratio of Wald cross-fitted intervals vs Wald PPI++ (solid, 95% CI
band; ratio_lfl = ratio for Wald/Wald) next to the asymptotic prediction (dashed, theory_synth.csv), oracle E[Y|f,X] line, and
Wilson coverage of the same intervals.  Main figure: headroom knob phi at rho=n/N=0.1.  Appendix: knob at rho=1, named scenarios.
Knob: E[Y|f] = cos(phi) z + sin(phi) (z^2-1)/sqrt(2), z = f standardised (phi=0 affine, no headroom).
Input: data_in/summary_synth.csv, data_in/theory_synth.csv."""
import numpy as np
import widthcov as wc
df = wc.read("data_in/summary_synth.csv"); th = wc.read("data_in/theory_synth.csv")
knob_t = lambda g: f"$\\varphi$={g[4:]}$^\\circ$"
named_t = lambda g: g.replace("_", " ")
KM = ["cf_lin_f", "cf_iso_f", "cf_poly_f", "cf_gbm_f", "oracle"]
NM = ["cf_lin_f", "cf_iso_f", "cf_gbm_f", "cf_lin_fX", "cf_gbm_fX", "oracle"]
def fig(groups, methods, rho, name, titles, **kw):
    d = df[np.isclose(df.rho, rho)]
    wc.draw(d, f"figures/{name}", "scenario", groups, methods, ratio_col="ratio_lfl", ylabel="width / PPI++ width", theory=th, rho=rho,
            titles=titles, width=1.0, cov_ylim=kw.pop("cov_ylim", (0.88, 1.0)), fs=6.5, ms=3, **kw)
KN = ["knob0", "knob30", "knob60", "knob90"]
fig(KN, KM, 0.1, "fig_c3_synth", knob_t, height=2.75, ncol_leg=3)
fig(KN, KM, 1.0, "fig_c3_synth_app_knob_rho1", knob_t, height=2.9, ncol_leg=3)
for rho, tag in ((0.1, "rho0.1"), (1.0, "rho1")):
    fig(["nonmonotone", "monotone_miscal", "X_informative", "subgroup_bias"], NM, rho, f"fig_c3_synth_app_named_a_{tag}", named_t, height=2.9, ncol_leg=4, cov_ylim=(0.84, 1.0))
    fig(["f_noise_X_informative", "heavy_tail", "calibrated"], NM, rho, f"fig_c3_synth_app_named_b_{tag}", named_t, height=2.9, ncol_leg=4, cov_ylim=(0.84, 1.0))
