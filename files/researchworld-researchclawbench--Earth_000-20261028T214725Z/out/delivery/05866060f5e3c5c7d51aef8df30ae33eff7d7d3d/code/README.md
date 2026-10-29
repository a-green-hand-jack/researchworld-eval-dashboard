# GlaMBIE reconstruction (code)

Independent reconstruction of regional and global glacier mass change 2000-2023 from the 257 submitted solutions in
`data/glambie/input`, validated against the published GlaMBIE consensus in `data/glambie/results`.

* `glambie_recon.py` : homogenisation and combination library.
* `run_all.py`       : produces everything in `../outputs/` (`run_all.sh` runs it with 1000 ensemble members).
* Dependencies: numpy, scipy, pandas (versions in `../outputs/environment.txt`).

## Method (what the code does)
1. **Units.** Gt -> m w.e. with the regional glacier area of the target year; m (elevation/thickness change) -> m w.e. x 0.85.
   The yearly region area (km2) is the only quantity read from `results/`; no published mass-change value enters the reconstruction.
2. **Annualisation.** Every solution is mapped to calendar years (global product) and to region-specific hydrological years
   by spreading each submitted interval change uniformly in time and summing the overlap with each target year
   (`annualise`). A year is kept if >= 95 % covered.
3. **Error structure.** Intervals >= 1 yr (e.g. 5-yr DEM periods) carry one independent error draw per interval, so annual values
   inside a period are fully correlated; sub-annual (monthly) intervals carry an annual-equivalent error shared by the target year
   (the submitted monthly errors are of the size of annual errors, see `outputs/README.md`); errors are independent between solutions.
4. **Within-group combination.** Sub-groups altimetry, gravimetry, DEM, annual-resolved (glaciological + hybrid/"combined") solutions are
   combined with a weighted fixed-effect model v[s,y] = mu[y] + b[s] (weights 1/(sigma^2 + 0.15^2) m w.e.), which avoids steps when the
   number of contributing solutions changes.
5. **Data-group eligibility.** Altimetry is used in 13 and gravimetry in 7 of the 19 regions. This expert choice (small regions,
   ice-sheet leakage, hydrology) cannot be derived from the inputs; it is taken from the groups present for each region in the published
   results and tested in `robustness_scenarios.csv` (`no_group_eligibility_rules`).
6. **DEM + glaciological group.** DEM period means set the multi-year level; annual solutions supply the anomalies about their mean in
   every DEM period; outside DEM coverage the annual series is shifted by its mean offset to DEM over the 5 nearest covered years.
7. **Cross-group combination.** combined = L + AV: L is the equal-weight fixed-effect combination of the groups' 5-yr running means,
   AV the mean annual anomaly of those groups that resolve annual variability (this avoids damping annual variability by groups that
   only resolve multi-year means).
8. **Uncertainty.** 1000-member ensemble: draws of all submitted errors with the correlation of (3) plus bootstrap resampling of
   solutions inside each group, plus an inter-group dispersion term (standard error of the group values, added in quadrature; the
   period-rate version uses the group period means). Regions are independent when summed to the global series.
9. **Outputs/validation/robustness** are written by `run_all.py`; see `../outputs/README.md`.
