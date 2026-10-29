# Output data dictionary and interpretation

Primary dataset: GlaMBIE 1.0.0, DOI 10.5904/wgms-glambie-2024-07.
Derived products are created by `code/analyze.py`. They preserve the published
consensus and do not constitute a new independently observed global estimate.

## Annual benchmark

`annual_mass_change_2000_2023.csv` has 480 rows: 19 regions and the globe, with
24 calendar years each. The `regional_annual_2000_2023.csv` and
`global_annual_2000_2023.csv` files are disjoint subsets.

- `region_id`: 0 = global; 1–19 are the standard glacier regions. IDs and readable
  names are in `region_name`; original dataset labels are in `region`.
- `year`, `start_dates`, `end_dates`: calendar intervals `[year, year+1)`.
  A row is an integrated annual change, numerically equal to its annual mean rate.
- `glacier_area_km2`: released time-varying regional glacier area.
- `mass_change_gt`: integrated mass change in Gt; negative means loss.
- `mass_change_gt_ci95`: released 95% uncertainty half-width in Gt.
- `mass_change_gt_sigma`: Gaussian one-sigma equivalent, `ci95 / 1.96`.
- `specific_change_mwe`: source-specific mass change in m w.e., preserving the
  release's effective water density 997 kg/m³.
- `specific_change_mwe_ci95`, `specific_change_mwe_sigma`: associated released
  95% half-width and one-sigma equivalent. These are observation errors, not the
  standard deviation of interannual climate variability.
- `specific_change_mwe_density1000`: standard-density equivalent, `1000*M/A`,
  which equals `0.997*specific_change_mwe`; `_ci95` scales the source specific
  uncertainty by the same factor. It does not add glacier-area error a second time.
- `source`: provenance label distinguishing the release from secondary analyses.

The source conversion is `mass_change_gt = 0.000997 * area_km2 * specific_change_mwe`.
Global mass changes add; global specific changes are annual area-weighted means.
Do not sum specific regional changes to create a global specific balance.

## Summaries and provenance

`regional_period_summary.csv` gives full-period means and totals, global loss
shares, early (2000–2011) and late (2012–2023) means, and later-minus-earlier
changes. `*_ci95_independent` assumes independence across years.
`cumulative_mass_change.csv` gives the cumulative sum beginning at 2000, labeled
by each interval's end year (2001–2024). Cumulative specific values are a sum of
annual balances over changing areas, not a fixed-footprint ice-thickness change.

`input_inventory.csv` has one row per raw CSV with file-level author/unit labels,
interval lengths, missing-data and error-sign flags, and seasonal-template names.
Counts are archive file counts, not independent scientific estimates.
`raw_interval_coverage.csv` records valid-date/finite-row overlap with calendar
years; a multi-year interval overlapping a year is not an annual observation.
It is an inventory, not an acceptance or correction of zero/negative raw errors.
`input_method_counts.csv` is the region-by-method inventory.
`input_checksums.csv` hashes all source files within `data/glambie/`.

## Method-level diagnostics

`method_series_hydrological.csv` concatenates the released 453 hydrological
region-years with their exact fractional-year bounds. Original error columns are
95% half-widths. `method_availability.csv` distinguishes nonmissing method values
from explicit `annual_variability == 1`. Its `display_year` is only a plotting
index: `floor(start_date + 0.5)`.

`method_pair_comparisons.csv` defines bias as comparison minus reference on
matched intervals. It includes interval counts, date bounds, RMS differences,
and correlations with and without the own-variability restriction. Pairwise
mean error widths assume independent methods and years; they do not validate
that assumption. Different regions have different comparison periods. Removing
a mean for the anomaly RMSE does not remove a linear temporal trend.

`simplified_reconciliation_hydrological.csv` uses equal group means anchored to
a common intersection and own-variability anomalies. It is a diagnostic point
reconstruction with shared inputs; there is no independently validated
uncertainty for it. `simplified_reconciliation_metrics.csv` gives regional RMSE,
bias, and maximum absolute residuals.

`leave_one_method_out.csv` removes a group from equal-weight means while holding
the common dates fixed. Gt-equivalent shifts use mean 2000–2023 calendar area.
Summed shifts are not a coherent global time series because regional common
periods differ. Regions with a single group cannot undergo method deletion.

## Covariance and validation

`covariance_sensitivity.csv` gives uncertainty scenarios documented in the report.
Mean mass loss and period differences are fixed; intervals change with assumed
measurement-error correlations. `ols_slope_ci95_measurement_only` excludes
structural uncertainty and stochastic climate-process uncertainty. Percentage
ratios have both delta-method half-widths and asymmetric Fieller endpoints.

`global_covariance_scenarios.npz` contains one 24×24 covariance matrix per
scenario in **Gt² at the one-sigma scale**; row/column order is 2000–2023. Keys
replace spaces in scenario labels with underscores. These are prescribed
scenarios, not empirical covariance estimates. The independent matrix recovers
the released global annual variances. To construct full regional covariance,
use `sigma_rt*sigma_su*Rspace_rs*Rtime_tu` as documented in the report.

`aggregation_checks.csv` contains numerical global-minus-regional closure checks
(the stored sign is reconstructed minus released).
`literature_comparisons.csv` compares matched calendar periods with published
values; dependencies between sources rule out independent accuracy validation.
`endpoint_sensitivity.csv` contains descriptive OLS slopes over selected windows.
`findings.json` stores headline results and numerical environment versions.
`validation_results.json` records the final scientific and artifact checks.
`run_log.txt` records a numerical run. `literature/` contains cached reference
materials, extracted text, and download provenance.
