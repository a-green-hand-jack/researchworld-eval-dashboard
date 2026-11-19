# Reference Query Plan

**Central topic.** Whether confidence intervals for a population mean can be shortened, at valid nominal coverage, beyond PPI/PPI++ when labels, unlabeled data and the pretrained predictor are all fixed. The run's method is cross-fitted recalibration of the predictor output, used as a control variate.

**Core methods.** Cross-fitted isotonic/binned recalibrated PPI. Repeated cross-fit with an NNLS-stacked calibrator library. The label-free spline-basis control variate with PRESS selection, which scored worse. PPI++ fallback and shrinkage. Efficiency-bound theory.

**Comparators.** Classical labeled-only interval, PPI, PPI++ (tuned and lambda=1), cross-PPI, stratified PPI, DML/semiparametric efficiency.

**Benchmarks.** ppi-python datasets (galaxies, forest, alphafold, gene_expression) and known-truth synthetic data.

**Result-driven themes.**
- Gains over PPI++ are small on real data (log width ratio about 0.003–0.03) and larger on synthetic nonlinear miscalibration (about 0.07).
- The gain over the classical interval is large (about 0.47–0.49 in log ratio).
- Coverage stays near nominal (pooled about 0.94–0.95).
- The label-free basis variant did not beat label-based calibration.

## Queries (10)
1. prediction-powered inference confidence intervals machine learning predictions (baseline)
2. PPI++ efficient prediction-powered inference tuned power (baseline)
3. cross-prediction-powered inference cross-fitting (core)
4. stratified prediction-powered inference (baseline)
5. semiparametric efficient estimation of the mean with missing outcomes and auxiliary predictions (core)
6. double/debiased machine learning cross-fitting target parameter (architectural)
7. isotonic regression calibration of predictions (core)
8. stacking nonnegative least squares combining regression estimators (architectural)
9. control variates variance reduction Monte Carlo regression adjustment survey sampling (theme)
10. Galaxy Zoo 2 morphological classifications; Retiring Adult folktables census datasets (benchmark)

## Rejected
- Generic queries on benchmarking, optimization or automated research.
- Chronology- or cycle-shaped queries.
- Active labeling as a main theme, because it violates the fixed-label constraint (kept only as background).
- Anything aimed at the withheld published paper.
