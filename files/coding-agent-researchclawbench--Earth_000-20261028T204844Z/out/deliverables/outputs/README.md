# Output data dictionary and provenance

Source dataset: **GlaMBIE 1.0.0**, final release 2024-07-16,
DOI **10.5904/wgms-glambie-2024-07**. Primary methods paper:
The GlaMBIE Team (2025), DOI **10.1038/s41586-024-08545-z**.

## Annual benchmark

`benchmark_annual_all.csv` contains 480 rows: 19 regions plus the global series,
each with 24 calendar intervals, 2000 through 2023 inclusive. The corresponding
regional and global files partition these rows. They are audited exports of the
released consensus. Negative values indicate loss.

| Column | Meaning |
| --- | --- |
| `region_id` | RGI-style region identifier 1–19; 0 denotes the global aggregation |
| `region`, `region_name` | Source region label and readable name |
| `year` | Calendar-year label; 2023 denotes 2023-01-01 through 2024-01-01 |
| `start_dates`, `end_dates` | Fractional years, half-open interval |
| `glacier_area_km2` | Area used in the upstream product for the interval |
| `mass_change_gt` | Integrated interval mass change, Gt |
| `mass_change_gt_h95` | 95% uncertainty half-width, Gt |
| `mass_change_gt_lower95`, `mass_change_gt_upper95` | Central estimate minus/plus the half-width |
| `specific_mass_change_mwe` | Integrated interval specific change, m w.e. |
| `specific_mass_change_mwe_h95` | 95% uncertainty half-width, m w.e. |
| `specific_mass_change_mwe_lower95`, `specific_mass_change_mwe_upper95` | Corresponding bounds |

Intervals are one year, so annual changes have the same numerical value as
annual mean rates in Gt yr⁻¹ or m w.e. yr⁻¹. The released values satisfy
`mass_change_gt = 0.997 * glacier_area_km2 * specific_mass_change_mwe / 1000`.
This archive-specific 0.997 factor is preserved, documented in the report,
and explored separately in `unit_convention_sensitivity.csv`.

## Aggregation and dependence

- `regional_period_summary.csv`: 24-year means and sums, early/late averages,
  regional contributions, area evolution and derived interval half-widths.
  `_independent` assumes independent annual errors. `_fully_correlated` holds
  all annual errors in the region perfectly positively correlated.
- `global_cumulative.csv`: cumulative mass change anchored to zero at the start
  of 2000, with independent, AR(1) rho=0.7, and common-error half-widths.
  `cumulative_mwe_dynamic_area` is the sum of annual specific changes on changing
  area, not a fixed-area thickness.
- `temporal_covariance_scenarios.csv`: sensitivity using the released global
  annual marginal errors. `increase_pct_h95_delta` uses a first-order delta
  approximation. The WLS `loss_acceleration_gt_per_yr2` is the negative slope
  of the finite-record annual mass series, weighted by reported inverse variance;
  its propagated half-width covers observational uncertainty only and excludes
  a stochastic climate-process or model-discrepancy term. It is supplementary
  and is not used for the report's principal half-period inference.
- `temporal_covariance_curve.csv`: AR(1) correlation sensitivity for plotting.
- `spatial_covariance_sensitivity.csv`: annual global intervals under common
  pairwise regional error correlations. Temporal and spatial sensitivities are
  calculated separately, not as a joint empirically estimated covariance model.
- `global_annual_covariance_ar1_07_gt2.csv` and `.npy`: 24 × 24 illustrative
  covariance matrix for global annual Gt changes, ordered 2000–2023. Diagonal
  entries are `(h95/1.96)**2`, and correlations are `0.7**abs(year_i-year_j)`.
  The CSV's first column is the row-year index. Units are **Gt²**.

## Method diagnostics

- `method_coverage.csv`: numbers of finite trend entries and annual-variability
  flags equal to one for each method group and region. Unflagged values may
  contain borrowed annual variability.
- `method_native_pair_comparison.csv`: pair comparisons only on shared intervals
  with own-variability flags equal to one. Mean differences are `method_a` minus
  `method_b`, over the exact paired subset. `first_start` and `last_end` describe
  the outer extent; the paired set can contain gaps. Mean-difference half-widths
  assume independent years and methods. Correlations describe the observed
  short record and carry no inference of causal mechanism or independence.
- `method_annual_sensitivity.csv`: 453 hydrological region-year rows, method
  support, contemporaneous equal and inverse-variance means, and leave-out shifts.
  Interpret weight/leave-out diagnostics on rows with `n_methods_native >= 2`.
  They do not replace the full upstream anomaly-and-trend reconciliation.
- `literature_comparison.csv`: Hugonnet (2021) uses matching 2000–2019 calendar
  years; Zemp (2019) uses the regional hydrological decade 2006/07–2015/16 and
  that paper's Table 1 value. All comparisons share data or methods and are
  marked `independent_validation=False`.

## Audit and reproducibility

`input_inventory.csv` audits all 257 archived CSV files, with interval coverage,
units, missing/negative/zero error counts and duplicate intervals. Archive
file counts differ from the 233 scientific estimates described in the paper.
No raw errors are silently repaired or used for new precision weights.
`input_units.csv` counts interval rows by method and original unit label.
`aggregation_audit.csv` and `audit_summary.json` record regional/global closure,
error aggregation, annual grid and conversion checks. `data_manifest_sha256.csv`
records every supplied dataset file and its SHA-256 checksum.

`key_metrics.json` supplies report statistics. `run_metadata.json` records package
versions and conventions. `analysis_run.log` captures the analysis run;
`validation_results.json` records final artifact validation. Extracted reference
texts and cached primary-paper HTML are in `literature/`. None of these products
independently validates glacier mass changes against withheld observations.
