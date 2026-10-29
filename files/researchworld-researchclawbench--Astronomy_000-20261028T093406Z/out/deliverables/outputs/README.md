# outputs/ — provenance and column definitions

All files are written by code in `code/` from the two frozen posterior files
(`data/M33_X-7_samples.dat`, sha256 `d2e2f88a…1334`; `data/IRAS_09149-6206_samples.dat`, sha256 `e08a545b…08ac`; full hashes in `summary*.json: inputs_sha256`).
Reproduce: `python3 code/make_rate_table.py` (≈25 min, 2 CPUs) → `python3 code/run_analysis.py` and `python3 code/run_analysis.py --rate leaver` (≈10 min each) → `python3 code/validate_rates.py`. Seeds are fixed.

## Model conventions
Scalar boson of mass mu [eV], alpha = G M mu/(hbar c). Dominant levels l = m = 1..5, n = 0.
A posterior sample (M, a*) is *excluded* if the superradiant cloud would have extracted the spin excess within the BH age t_BH (baseline 4.5e7 yr):
`t_ex = [ln N* + max(N_tot/N_max − 1, 0)]/Gamma`, `N* = min(N_tot, N_max)`, `N_tot = (a* − a_f)(M/M_Pl)^2/m`, `a_f = 4x/(1+4x²)`, `x = alpha/m` (no superradiance for x ≥ 1/2); `N_max = kappa·16π alpha f_a² r_c²`, `r_c = l² r_g/alpha²` (bosenova; `N_max = ∞` when no self-interaction). Source of Gamma: `detweiler` = eq. (18) of paper_000; `leaver` = Detweiler × tabulated (Leaver continued-fraction)/(Detweiler) ratio for l=m=1,2,3 (`rate_table.npz`).
P_ex(mu) = fraction of posterior samples excluded. Combined: `1 − Π(1 − P_ex,i)` (independent BHs). "X% exclusion": P_ex ≥ X.

## Files
| file | content |
|---|---|
| `pex_vs_mu.csv`, `pex_vs_mu_leaver.csv` | columns: `mu_eV`; `Pex_<BH>` exclusion probability per BH; `Pex_err_<BH>` binomial 1σ MC error (sqrt(p(1−p)/N_samples)); `Pex_combined`; `Pal_combined`=1−Pex_combined; `posterior_density_per_dex` = posterior of mu (log-uniform prior on 1e-21…1e-10 eV, likelihood Π(1−P_ex,i), normalised to unit integral in log10 mu). Detweiler / Leaver-calibrated rate, respectively. |
| `summary.json`, `summary_leaver.json` | `windows_baseline_eV` (excluded mu intervals at 50/68/95/99.7 %: per BH and combined; empty list = level never reached), `bootstrap_95_edges` (200 bootstrap resamples of the posterior: 16/50/84 % of window edges at 50, 68, 95 %), `point_estimate` (windows using only the median (M,a*), and median M with a* at the 16/84 % marginal values), `sensitivity_95` (95 % windows vs t_BH = 1e6, 1e7, 1.38e10 yr, levels l=1 / l≤2, ≥100 e-folds), `fa_min_95_summary`, `inputs_sha256`. |
| `point_estimate_indicator_<BH>[_leaver].csv` | `mu_eV`, `excluded_at_median_M_a` (0/1 step function of the point-estimate analysis). |
| `pex_grid_mu_fa[_leaver].npz` | `mu_eV` (221 pts), `fa_GeV` (77 pts, 1e10…10^19.5); arrays `<kappa>_<BH>` and `<kappa>_combined` of shape (n_fa, n_mu): P_ex(mu, f_a) for kappa = 1, 0.1, 10 (`kappa1`, `kappa0.1`, `kappa10`). 3000-sample random subsets of each posterior. |
| `fa_min_95_vs_mu[_leaver].csv` | `mu_eV` and, per kappa and BH, `fa_min95_GeV_*`: smallest f_a at which P_ex ≥ 0.95 (NaN: not excluded at 95 % for any f_a). The excluded region is f_a ≥ fa_min (weak self-interaction); equivalently lambda = mu²/f_a² ≤ lambda_max(mu) = mu²/fa_min². |
| `rate_table.npz` | `a_grid`, `x_grid` (x = alpha/alpha_crit, alpha_crit = m Omega_H r_g), `ratio_l1..3` = Gamma_Leaver/Gamma_Detweiler (rows a*, columns x; NaN = root not found). |
| `rate_validation.csv` | Leaver vs Detweiler at selected points; includes the benchmark alpha=0.42, a*=0.99 (paper_003, Table II: 1.504e-7). |
| `literature_windows.json` | literature numbers used for comparison (Stott 2018; Witek 2012). |
| `figure_manifest.md` | per-figure claims and source files. |
