# Outputs of the GlaMBIE reconstruction

All files are produced by `code/run_all.py` (`code/run_all.sh`) from `data/glambie/input` (257 CSV files; the task text quotes 233 estimates,
the working set is the whole 257, 19 of which are `WGMS-beta` series; a run without them is scenario `wgms_beta_excluded`).
Only the yearly regional glacier area is read from `data/glambie/results`; the published consensus is used solely as a validation benchmark.
Years are labelled by their start date (`start_dates=2000.0` is calendar year 2000; for hydrological years the region's own start, e.g. 1999.75).
Uncertainties are 1 sigma. Negative = mass loss. m w.e. = Gt / area x 1000. Sea level: 362.5 Gt = 1 mm.

## Main products
| file | content |
|---|---|
| `regional_calendar_years.csv` | consensus per region (`region_id` 1-19) and global (`region_id` 0, sum of regions), 2000-2023 calendar years: `area_km2, mwe, mwe_err, gt, gt_err` (= total), `gt_err_mc` (ensemble: submitted errors + bootstrap of solutions), `gt_err_groupdisp` (inter-group dispersion), `n_groups`, `level_gt` and `annual_variability_gt` (the two components that add up to `gt`) |
| `regional_hydrological_years.csv` | same for the 19 regions in region-specific hydrological years (no global) |
| `group_series_calendar.csv`, `group_series_hydrological.csv` | per region and data group (`altimetry`, `gravimetry`, `demdiff_glaciological`): `mwe, mwe_err, gt, gt_err, n_solutions` (ensemble std of the group series, bootstrap + errors) |
| `solution_annual_calendar.csv` | every submitted solution put on the calendar-year grid (`mwe`, `gt`, annual error `mwe_err`, `annual_resolved`) |
| `input_inventory.csv` | the 257 input files with unit, source, coverage, interval length and whether used in the main run |
| `period_rates.csv` | mean annual rate (Gt/yr and m w.e./yr) per region and global for 2000-2011, 2012-2023, 2000-2023, 2000-2019 and 5-yr blocks; `rate_gt_err` = sqrt(mc^2 + groupdisp^2); the ensemble preserves the correlation of the errors across years |
| `acceleration.csv` | rate difference 2012-2023 minus 2000-2011 and linear trend of the annual series (Gt/yr per decade) with uncertainty |
| `reference_values.csv` | numbers quoted from the supplied related papers (Hugonnet 2021, Zemp 2019 Table 1) for comparison; their uncertainties are 95 % confidence intervals (column `approx_1sigma` = CI/2), whereas all uncertainties in this directory are 1 sigma; the Zemp -267 figure is the total excluding Greenland periphery and Antarctic/Subantarctic, not a global total |

## Validation
| file | content |
|---|---|
| `validation_vs_published.csv` | per region (+global for calendar years), reconstruction vs published `combined_*`: bias, RMSE, r (Gt and m w.e.), fraction of years within 1 and 2 sigma (`z = diff / hypot(err_recon, err_pub)`), mean annual errors of both |
| `validation_vs_published_by_year.csv` | the matched annual values and differences behind it |
| `period_rates_vs_published.csv` | period rates of the reconstruction vs those of the published series (`diff_over_recon_err` = difference / our rate uncertainty) |
| `validation_groups_vs_published_hydrological.csv` | reconstructed group series vs published per-group series |

## Robustness
| file | content |
|---|---|
| `robustness_scenarios.csv` | global (and regional `2000-2023_region:*`) rates under: dropping a group, one group only, hybrids excluded, WGMS-beta excluded, no eligibility rules, plain mean, smoothing window 3/7, weight floor 0.05/0.5 m w.e., density 0.80/0.90 for m -> m w.e., MC without bootstrap, errors fully correlated in time per solution (`mc_err` given where the scenario used an ensemble) |
| `robustness_global_uncertainty.csv` | global rate uncertainty if regional group-dispersion errors are independent (main) or fully correlated |

## Analyses added after review (`code/review_analyses.py`)
| file | content |
|---|---|
| `acceleration_significance_variants.csv` | global 2000-2011, 2012-2023, 2000-2023 rates, difference of halves and linear trend (Gt/yr per decade) with sigma under the combinations of {errors independent between submitted intervals (main) / each solution's errors fully correlated in time} x {regional group dispersion independent (main) / fully correlated / none}; `n_sigma` = |value| / sigma_total. Dispersion of the trend is approximated by the dispersion of the half-difference / 12 yr x 10 |
| `zemp2019_matched_hydrological_2006_2016.csv` | reconstruction in region-specific hydrological years (10 years starting at the one closest to 2006.75), per region, `total_excl_GRL_ANT` and `global_total_19_regions`, with sigma, the published GlaMBIE mean over the same window, and Zemp et al. 2019 Table 1 values (95 % CI and CI/2) with the difference in combined sigma |
| `dem_group_vs_hugonnet_2000_2019.csv` | global 2000-2019 rate of: main combination, DEM+glaciological group only, DEM solutions only, the Hugonnet et al. 2021 solution alone (our unit conversion/areas), Hugonnet as published, GlaMBIE published |
| `robustness_drop_demdiff_glaciological.csv` | main vs alternative without the DEM+glaciological group, for regions with altimetry/gravimetry and years where the alternative is defined (no DEM/glaciological group means no data for 2000-2002 and for regions without altimetry or gravimetry) |
| `validation_groups_summary.csv`, `validation_groups_by_region_wide.csv` | per data group (and per region x group) bias, RMSE and r of the reconstructed group series against the published per-group series |

## Caveats to carry into the report
* Sub-annual (monthly) submissions carry errors of the size of annual errors; they are interpreted as annual-equivalent errors (shared by the target year). The data description does not state this.
* Eligibility of altimetry/gravimetry per region is taken from the published results' group coverage, not derived.
* The GlaMBIE algorithm of the original paper is not among the supplied papers; the method here is an independent construction informed by the dataset's description (data groups, annual variability flags), not a replica.
* Where only one data group covers a region/period (e.g. 2000-2002 in most regions), `gt_err_groupdisp` is 0 and uncertainty rests on the submitted errors.
