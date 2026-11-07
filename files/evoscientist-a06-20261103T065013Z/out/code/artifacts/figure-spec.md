# Figure specifications

All numerical panels load executed CSV results; no fitted curves or invented data.

- `optimism.png/pdf`: two-panel line chart. Left: iid equal-quality p=.7, K=8 at latent rho=0,.5,.9, n=16,32,64,128; right: real finite-cohort and remainder optimism at the same n. Vertical units percentage points, linear axes, 95% Monte Carlo error bars (1.96 MCSE) for cohort and iid means. Remainder MCSE is scaled by N/(N-n). Curves connect measured settings only. No population label on real panel.
- `coverage_width.png/pdf`: two-panel coverage versus interval-width plot, iid primary and real-cache primary. Six methods in frozen order, common linear axes, horizontal 95% nominal reference, vertical 1.96 MCSE error bars. Width in percentage points, coverage in percent. Exact/conservative methods square, approximate methods circles. The guarded/raw primary may overlap; labels use short method names.
- `failure_precision.png/pdf`: three panels. (a) p=.95,n=16 boundary coverage of six methods for rho=0,.9, paired grouped points; (b) real audit size32,64,128 versus exact-audit width and coverage (two panels in place of twin axes). Linear scales. All plotted rows explicitly filtered, full grids delivered separately as CSV.
- `correlation.png/pdf`: real outcome Pearson correlation heatmap, eight prompt labels, full [-1,1] range and colorbar. Diagnostic, not an independence test.

Shared palette and styles identify the same method everywhere; axes include all shown points and error bars, legends do not duplicate direct labels. Figure scripts also emit precise source subsets and machine-readable plotted values. No confidence band is interpreted as uncertainty over new benchmark datasets.
