# Figure specification

- chart_type: two-panel endpoint line comparison
- data_sources: fixed_cohort.csv, triple cohort
- rows: same jointly feasible, initially nonwinning targets selected at rho=.5; keep IDs at rho=1
- x: rho=.5 and 1 (lines guide the eye, not interpolation claims)
- y: mean optimal support fraction K/n, linear [0,1]
- series: mean, median, Borda; bootstrap paired difference intervals in paper table, not pseudo training error bars here.

Numeric axes linear; mean blue, median vermilion, Borda green. All data from saved results; no fitted lines or invented values. PNG at 300 dpi; PDF vector.
