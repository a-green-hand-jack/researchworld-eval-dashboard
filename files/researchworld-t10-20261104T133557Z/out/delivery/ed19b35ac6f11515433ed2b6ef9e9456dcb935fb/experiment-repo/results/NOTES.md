# Analysis notes (experiment-repo)

Numbers below are read from the delivered summaries (`results/summary_*.csv`, compact versions `results/headline_*.csv`,
made by `code/headline.py`); `results/cells_done.csv` lists the cells each summary holds. "ratio" is always the
**like-for-like** width ratio: a method's mean paired width over the width of PPI++ with the same interval calibration
(Wald, t or bootstrap-t); < 1 means narrower. Coverage is of nominal 95% intervals, Wilson CIs in `cov_lo/cov_hi`.

## Findings

1. **Real pools, estimating a mean (headroom is ~0): no usable shortening.** At the population level the best control variate
   from (Yhat, X) is within about 1% of PPI++ on every pool (`headroom_population.csv`). In finite samples every cross-fitted
   adjuster is wider than PPI++ at small n and converges to ratio 1 from above (`headline_mean_real.csv`): the affine
   cross-fitted ablation `cf_lin_f` costs 0.1-8% (largest at n=50 on census_income, 1.076), isotonic up to 12%, GBM up to
   +20-100% at n=50 (gene_expression 2.06). The only cells below 1 are forest at n=1000 (`cf_gbm_f` 0.995, `cf_iso_f` 0.997), the largest n, within noise of 1 (see ratio_lfl_lo/hi).
   Coverage of the adjusted intervals tracks PPI++ (they undercover wherever PPI++ does: census_income n<=200 is 0.82-0.91).
   This is a measured null/negative result for the mean on real data, not missing work.
2. **Where headroom exists, it is realised only above a threshold n and only by a well-matched adjuster** (synthetic knob family
   E[Y|f] = cos(phi) z + sin(phi)(z^2-1)/sqrt2, `headline_synth.csv`, `breakeven_synth.csv`, `theory_vs_measured.csv`):
   phi=0 (no headroom) always loses (1.001-1.17); phi=30/60/90 degrees gain asymptotically (oracle 0.91/0.79/0.74 at rho=0.1) but the
   cubic `cf_poly_f` crosses below 1 first, while `cf_gbm_f`/`cf_iso_f` need n=200-1000 and isotonic never reaches the oracle
   (it cannot represent a non-monotone map). At n=50 only the cubic adjuster gains, and only for strong headroom (knob60/90 at rho=0.1: 0.93/0.89; nonmonotone 0.73), or a linear adjuster where X carries the signal.
3. **X-informative scenarios are the real opportunity**: `cf_lin_fX` is narrower than PPI++ already at n=50 in X_informative
   (0.886 at rho=0.1; oracle 0.828), subgroup_bias and f_noise_X_informative, at nominal coverage; GBM on (f,X) needs n>=200.
   The OLS real-data case (census_income, income on covariates) shows the same pattern: `cv_cf_lin_fX_full` is 2.4-2.8% narrower
   than PPI++ at n=500-1000, 0.6-0.7% narrower at n=200, but 2% wider at n=100 and 6-7% wider at n=50 (`headline_ols_real.csv`, ratio relative to ppi_py PPI++); GBM needs n~1000 to break even.
4. **Coverage**: all intervals, classical included, undercover on skewed/rare-event outcomes at n<=200 (census_income n=50: 0.82-0.86; OLS
   coordinate 0: n=50 0.79-0.85, n=100 0.84-0.88). Narrower is only a saving when coverage is no worse than the like-for-like baseline; check `cov_*`.
5. **Diagnostics**: plankton under a label shift (2013 labels, 2014 unlabeled) breaks PPI++ and every adjuster alike (coverage 0.35 at n=1000;
   `summary_plankton_shift.csv`), so shortening cannot be traded against bias there; no adjuster fixes it. Ballots (no unlabeled truth):
   width-only, adjusters 0.6-2.5% wider than PPI++.
6. **Ablations (C6)**: `cf_lin_f` vs `ppi++` isolates the price of cross-fitting; `_t` vs Wald and `_boot` vs Wald show that calibration
   changes coverage at small n, and every comparison is read like-for-like, so the ratios above are not artefacts of calibration.

7. **pure_noise scenario** (neither f nor X carries signal; formerly named `null`, renamed because pandas reads the string `null` as NaN):
   classical is within 1% of PPI++ (the optimal lambda is 0). With rho=1 the cross-fitted adjusters are 0.1-2.3% narrower than PPI++
   (n=50: `cf_lin_f` 0.977, `cf_gbm_f` 0.977; classical 1.006), with coverage 0.929-0.938
   against 0.940 (PPI++) and 0.942 (classical): 0.2-1.3 points lower, within about 1.5 Monte-Carlo se (se ~0.008 at 1000 reps), so
   this is not shown to be a valid saving and is nothing like the gains of scenarios with signal; the gap is gone by n=200.
   With rho=0.1 they are 0-27% wider at n=50 (`cf_lin_f` 1.27, `cf_gbm_f` 1.26) and ~equal at n>=200 except `cf_lin_f` (1.06-1.10).
   Coverage is 0.92-0.96 overall (`headline_synth.csv`).

Answer to the objective: with labeled set, unlabeled set and predictor fixed, shorter valid intervals than PPI++ are possible
only when E[Y|f,X] differs materially from the best affine function of f (non-monotone miscalibration, or informative X), at n
beyond a scenario-specific threshold (linear (f,X) adjuster: smallest n; flexible adjusters: hundreds), with gains up to the oracle
bound of the scenario (2-43% narrower across the synthetic scenarios that have headroom, `ratio_lfl:oracle`; none for calibrated and heavy_tail). For the mean on the supplied real pools the headroom is ~1% and the practical effect is a loss.

## Caveat on sampling
Real-pool grids draw iid with replacement from the empirical pool (truth = pool mean/fit); ratios are paired (same draw for all methods).

## Method naming (for figures/tables)
Reference/baselines: `classical` (labeled only), `ppi` (lambda=1), `ppi++` (power-tuned, Wald; = ppi_py default for the mean),
`ppi++_t` (t quantile), `ppi++_boot` and `classical_boot` (studentised bootstrap-t), `classical_t`.
Proposed route (headline): cross-fitted control-variate adjusters learned from the labeled data only, lambda-tuned:
`cf_iso_f` (monotone recalibration of Yhat), `cf_gbm_f`, `cf_lin_fX`, `cf_gbm_fX` (use features X where present); suffix `_t` = t quantile.
Ablations: `cf_lin_f` (= affine recalibration, PPI++ equivalent up to cross-fitting: isolates the cost of cross-fitting), `_t` variants (Wald vs t),
`*_boot` (Wald vs bootstrap), f-only vs (f,X) adjusters. `oracle` (synthetic only) = true E[Y|f,X], not implementable.
OLS: `classical`, `ppi_lib`/`ppi++_lib` (ppi_py), `cv_f_coord` (= PPI++ coord-wise), `cv_f_full`, `cv_cf_lin_fX_full`, `cv_cf_gbm_fX_full`.

## Sampling protocol (all real-pool grids)
Population = empirical distribution of the pool; each replicate draws n labeled and N unlabeled points iid WITH replacement from the pool
(N = min(pool size, 10000) unless rho is stated); truth = pool mean (or pool OLS). Seeds: seed*1_000_003 + replicate index. Paired: all methods use the same draw.
Dataset descriptors: `results/datasets.csv`. Theory for synthetic scenarios: `results/theory_synth.csv` (asymptotic width ratio vs ppi++, rho in {1,0.1,0.02}).
`ballots` (no unlabeled truth) and `plankton` (2013 labeled / 2014 unlabeled shift) are diagnostic only (planned, not yet run).
