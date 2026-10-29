# Reconciliation code

`python code/run_all.py` (from the workspace root; option `--data`, default `data/glambie`) reads
`data/glambie/input/*/*.csv` (257 submissions) and the area series in `data/glambie/results/`,
and writes `outputs/reconciliation/` and `outputs/validation/` (≈ 1 min, NumPy/pandas only).
`code/analysis/homogenise.py` reads and homogenises the inputs; `code/analysis/reconcile.py`
holds the within-group and between-group combinations and the hydrological→calendar conversion.

## Method (main configuration)
1. **Homogenisation.** Elevation change (unit `m`) → m w.e. with density 850 ± 60 kg m⁻³ (error
   adds the density term in quadrature); Gt ↔ m w.e. with the time-varying regional glacier area
   of the GlaMBIE result files (RGI 6.0 with area-change rates), at the mid-point of each period.
   Monthly series are summed to annual hydrological years (1 Oct–1 Oct north, 1 Apr–1 Apr south
   = regions 17–19, calendar year in region 16); their errors are treated as epoch noise (error of
   an interval change = rms of the monthly increment errors, not accumulated). Annual or longer
   periods: independent errors in quadrature.
2. **Data groups** (as GlaMBIE): altimetry; gravimetry; DEM differencing + glaciological. Hybrid
   ("combined") submissions are not used in the consensus, only compared. Gravimetry is retained
   only in the regions where GlaMBIE retained it (1, 3, 4, 6, 7, 9, 17); elsewhere it is a
   sensitivity variant.
3. **Within a group**: random-effects weighted least squares for one annual series z_y.
   Resolved series whose level counts (altimetry, gravimetry): x = z + b_i; multi-year
   periods (each native period of DEM differencing, ICESat-era altimetry, trend-only gravimetry):
   Σ f_y z_y + L b_i = v; glaciological series give annual variability only (free offset a_i,
   Zemp et al. 2019), their errors inflated by √n because they derive from the same WGMS glaciers.
   b_i ~ N(0, τ²) is a submission-level rate bias with τ estimated by moments, so that no single
   submission fixes the level; covariance inflated by the Birge ratio when residuals exceed errors.
   Altimetry/gravimetry years not resolved by the group's own series (e.g. ICESat 2003–2009
   trends) borrow the annual variability of the DEMdiff+glaciological group (error ×2).
4. **Regional consensus**: per hydrological year, inverse-variance weighted mean of the available
   groups; error σ² = weighted mean of group variances + weighted variance of group values
   (groups share area, density and glaciological variability, so averaging does not reduce error).
5. **Calendar years**: each hydrological year distributed over its months with the seasonal
   anomaly of the glaciological sine-wave series (sums to zero within the year); monthly shares of
   the two overlapping hydrological-year errors summed linearly.
6. **Global**: sum of the 19 regions per calendar year, errors in quadrature (regions independent);
   m w.e. = Gt × 1000 / global area; sea-level equivalent with 362.5 Gt mm⁻¹.
7. Period rates and totals: annual errors in quadrature (as GlaMBIE); `*_correlated` columns give
   the fully correlated (linear-sum) bound.

All errors are **1σ**.

## Outputs
`outputs/reconciliation/`
- `inputs_inventory.csv` — one row per submission: region, source, group, label, file, unit,
  n_rows, native_dt (median period, yr), resolved (annual-or-finer), t0, t1, trend_mwe(_err)
  (m w.e. yr⁻¹ over t0–t1), used_in_consensus, role.
- `group_series_hydrological_years.csv` — region, group, year (label), start_dates, end_dates,
  glacier_area (km²), mwe, mwe_err, gt, gt_err, n_resolved, n_trend, borrowed.
- `group_diagnostics.csv` — Birge ratio, τ, number of level-setting submissions per region/group.
- `regional_hydrological_years.csv` — consensus per region and hydrological year: glacier_area,
  mwe, mwe_err, gt, gt_err, n_groups, groups.
- `regional_calendar_years.csv` — consensus per region and calendar year 2000–2023 (same columns).
- `global_calendar_years.csv` — year, n_regions, glacier_area, gt, gt_err, mwe, mwe_err, sle_mm,
  sle_mm_err (sea-level contribution, positive = rise).
- `summary_regional.csv` — per region: glacier_area_2000, mean rates (Gt yr⁻¹, m w.e. yr⁻¹) and
  errors for 2000–2023, 2000–2011, 2012–2023; cumulative 2000–2023 (Gt, m w.e.); share of global loss.
- `summary_global.json` — global totals/rates for the three periods (gt, mwe, sle_mm), linear trend
  of annual mass change (Gt yr⁻² and per decade), the same for the published GlaMBIE series,
  annual comparison statistics, input counts, conventions.
- `hybrid_submissions_hydrological_years.csv` — hybrid submissions on the annual grid.

`outputs/validation/`
- `vs_glambie_regional.csv` (+ `_pairs.csv`) — ours vs published GlaMBIE per region, hydrological
  and calendar years: bias, rmse, r, fraction within combined 1σ, mean errors, mean rates.
- `vs_glambie_global_pairs.csv` — global annual ours vs published.
- `vs_glambie_groups.csv` — per region and data group, ours vs GlaMBIE's group series.
- `group_agreement.csv` — pairwise agreement of data groups per region (mean-rate difference,
  its error and z, annual correlation, rms difference, fraction within 1σ).
- `hybrid_vs_consensus.csv` — each hybrid submission vs our consensus.
- `sensitivity_global.csv`, `sensitivity_regional.csv` — variants: equal weights, independent
  group errors, UZH glaciological series with trend, gravimetry in all regions, no gravimetry,
  no altimetry, no DEMdiff+glaciological (falls back where nothing else exists), hybrids as a
  fourth group, density 800 / 900 kg m⁻³.
- `headline_uncertainty.json` — combined 1σ of the headline rates/totals (Gt, m w.e., mm SLE) for
  2000–2023, 2000–2011, 2012–2023 and the 2012–2023 minus 2000–2011 difference: `random`
  (quadrature of annual errors), `structural_sd` (sample SD of central values over main + 7
  alternative configurations: equal weights, UZH with trend, gravimetry everywhere, no gravimetry,
  hybrids as 4th group, no altimetry, no DEMdiff+glaciological; density variants and
  independent_group_errors excluded), `combined` = √(random² + structural²); `*_choices_only`
  drops the two leave-one-group-out variants; `half_range` for reference. Also the trend of
  annual global mass change: OLS with AR(1) effective sample size, WLS on the annual 1σ with
  Birge and AR(1) inflation, Monte Carlo perturbation, structural SD, and a `recommended` value.
- `prior_estimates.csv` — Hugonnet et al. (2021, Table 1 and abstract) and Zemp et al. (2019,
  abstract) global rates vs ours and GlaMBIE over the same calendar years.
