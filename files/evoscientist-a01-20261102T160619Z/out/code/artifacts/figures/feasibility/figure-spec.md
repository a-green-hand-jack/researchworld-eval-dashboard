# Figure specification

- chart_type: 2x2 step ECDF / all-target success curve
- data_sources: results_helm.csv, results_open_raw.csv; shared first, rho=.5 and 1
- x: allowed edited-task fraction, linear [0,1]
- y: fraction of ALL targets attaining shared first within budget, linear [0,1.02]
- infeasible cases: remain in denominator and never contribute
- series: mean, median, Borda; one legend; no uncertainty (fixed cohort).

Numeric axes linear; mean blue, median vermilion, Borda green. All data from saved results; no fitted lines or invented values. PNG at 300 dpi; PDF vector.
