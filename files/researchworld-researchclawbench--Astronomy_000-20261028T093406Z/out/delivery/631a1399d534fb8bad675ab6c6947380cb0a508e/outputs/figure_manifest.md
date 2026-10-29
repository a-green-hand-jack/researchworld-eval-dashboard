# Figure / table manifest (claims and sources)

Headline model = `leaver` rate (best estimate); `detweiler` = analytic comparison. Files in `outputs/`.

Headline numbers (95 % exclusion, t_BH = 4.5e7 yr, l = m = 1..5, no self-interaction; `summary_leaver.json`):
- M33 X-7: mu in [2.09e-13, 8.23e-12] eV (bootstrap 1σ on edges < 1 %); 68 %: [1.85e-13, 8.96e-12]; 99.7 %: [2.36e-13, 5.88e-12]. Detweiler: [1.94e-13, 8.23e-12].
- IRAS 09149-6206: **P_ex never reaches 95 %**; max P_ex = 0.69 at mu = 3.5e-19 eV; 68 % window [3.2e-19, 4.0e-19] eV; 50 % window [1.8e-19, 7.6e-19] eV (Hubble-time age: 95 % window [2.1e-19, 5.3e-19] eV). The broad mass posterior (5.6e7–1.8e8 Msun, 68 %) smears the window in alpha.
- Combined 95 %: M33 X-7 window only. Combined 68 %: two windows (IRAS and M33 X-7).
- Self-interaction (kappa = 1): M33 X-7 excludes f_a >= ~3e11 GeV (at the most constraining mu; f_a_min 1e11 / 1e12 GeV for kappa = 10 / 0.1) — see `fa_min_95_vs_mu_leaver.csv`; no 95 % f_a limit from IRAS.
- Caveat to state: the upper edge of the M33 X-7 window (8.2e-12 eV, alpha ~ 0.9) is set by l = 4, 5 levels where neither analytic nor table-calibrated rates are reliable (l = m = 1 alone: 2.1e-12; l <= 2: 4.1e-12). The lower edge (2.1e-13) is robust to levels and rate model (Detweiler 1.9e-13) but depends on t_BH (1.1e-13 for Hubble time, 3.3e-13 for 1e6 yr).

| # | figure / table | claim it supports | source |
|---|---|---|---|
| F1 | M–a* posteriors (done by figtab) | data overview; M33 X-7 strongly correlated (r = 0.88), IRAS independent; IRAS mass broad | `data/` |
| F2 | method illustration: samples classified excluded/allowed at fixed mu, with Regge threshold a_f(alpha) | exclusion criterion acts on the full posterior | `code/sr.py: excluded()` |
| F3 | P_ex(mu) per BH + combined, 50/68/95 % lines, MC error band, shaded excluded windows (log mu axis) | main result; IRAS < 95 % | `pex_vs_mu_leaver.csv` (+ `pex_vs_mu.csv` dashed) |
| F4 | posterior-vs-point-estimate: P_ex(mu) vs step function of the median | full posterior replaces a sharp window by smooth probability; edges differ (e.g. M33 X-7 point-estimate 1.73e-13–9.17e-12 vs 95 % 2.09e-13–8.23e-12; IRAS point estimate gives two sharp windows 1.7e-19–4.3e-19, 5.5e-19–8.7e-19 that the posterior does not support at 95 %) | `point_estimate_indicator_*_leaver.csv`, `summary_leaver.json: point_estimate` |
| F5 | (mu, f_a) map of P_ex per BH (kappa = 1) with the 95 % contour and fa_min_95(mu) curve; kappa = 0.1/10 as band; second axis lambda = mu²/f_a² | self-interaction limit: weak coupling excluded, strong coupling escapes via bosenova | `pex_grid_mu_fa_leaver.npz`, `fa_min_95_vs_mu_leaver.csv` |
| F6 | posterior density of mu (log-uniform prior) | Bayesian view: where mu is disfavoured | `pex_vs_mu_leaver.csv: posterior_density_per_dex` |
| F7 | validation: Gamma_Leaver/Gamma_Detweiler vs x = alpha/alpha_crit for a* values + benchmark point of Witek 2012 | Detweiler is ~2x high at small alpha (ratio 0.43–0.5) and underestimates near the boundary; Leaver reproduces 1.504e-7 | `rate_table.npz`, `rate_validation.csv` |
| F8 | sensitivity: 95 % windows vs t_BH, levels, rate model, e-fold floor (bar/range chart) | robustness; lower edge robust, upper edge level-dependent | `summary_leaver.json: sensitivity_95`, `summary.json` |
| T1 | summary table of windows 50/68/95/99.7 % per BH and combined, with bootstrap edges | headline limits | `summary_leaver.json` |
| T2 | comparison with literature: stellar 7e-14–2e-11 eV, SMBH 7e-20–1e-16 eV (Stott 2018: union over many BHs, not single-source) | order-of-magnitude consistency; ours is one BH each so narrower | `literature_windows.json` |
