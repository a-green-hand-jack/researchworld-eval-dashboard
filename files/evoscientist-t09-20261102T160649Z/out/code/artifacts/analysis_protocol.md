# Frozen analysis protocol (after pilot, before main)

- Main: R=300, synthetic graph seeds 11/23/37, 18 synthetic graph instances plus ego and Stanford, 2 designs => 12,000 assignment records, 840,000 method/mechanism records. Size R=200, allocation R=200.
- Pilot uses only seed11 despite inherited generic seeds list in config; actual manifest authoritative. Pilot excluded from reported main summaries.
- Metrics per fixed graph seed/design/p/method/mechanism. Every attempt retained. `ok` must have finite estimate/error/bias/variance. Failures separately counted, never replaced by zero, never re-randomized. HT propensity underflow is numerical unavailability, not structural lack of positivity.
- Bias and RMSE conditional on valid estimates; intervals/coverage conditional on valid intervals, accompanied by availability. Report conditional metrics for each seed; pooled synthetic results are a descriptive equal-weight mixture of the three fixed graphs, not confidence over a graph population.
- MC SE for mean error = sample SD/sqrt(N). MSE SE = SD(error²)/sqrt(N). RMSE delta SE = MSE SE/(2 RMSE). Coverage and success use Wilson intervals. For fixed-three-graph pooling, same independent assignment formula estimates MC uncertainty of that fixed mixture, NOT graph sampling uncertainty; also provide graph-seed ranges.
- Validate MSE decomposition using D=error²−conditional_bias²−variance, mean D ±1.96 SD(D)/sqrt(N); compare on precisely the same valid rows. Distinguish E[b²] from E[b]².
- Paired comparisons use same design and common valid records only (keys graph_seed,rep), with assignment-level difference in squared errors; report counts. Designs use independent RNG streams: compare designs unpaired.
- HT full-exposure high-degree rare-event estimates: report observed full-exposure counts and zero-estimate fraction. Finite-MC bias/RMSE may be profoundly misleading; no statistical claim of true bias from all-zero finite samples where the exact estimator is unbiased for a one-hop mechanism.
- Normal noise intervals use q=.975 standard-normal quantile 1.959963984540054. Model-based coverage integrates fresh noise schedules. No design-based CI validity claim for fixed realized outcome schedules.
- Rank acceptance is feature-only. Bernoulli visibility bound is unconditional; do not transfer it to rank-selected assignments.
- Independent audit corrected one wording issue in theory.md: mean correctness is sufficient, not necessary; zero conditional contrast bias is the exact condition for centered Gaussian interval coverage. Ridge penalty nonnegative; lambda=1, intercept unpenalized. The residual identity is OLS-only; direct b²+v applies to ridge.
- No hypothesis testing or significance search. Prespecified comparisons descriptive, no familywise superiority claims. Full conditional CSV and graph-seed tables remain available.

## Post-review amendment notice (2026-11-02)
The original bullets above are preserved as the pre-main plan, not rewritten retrospectively. Final uncertainty formulas and valid-count weighting are superseded by `analysis_amendment.md`; the original equal-weight language applies only to all-valid equal-attempt cells. The final analysis uses attempted-record stratified ratio MCSEs, including random valid-count variation. Experiment design, mechanisms, repetitions and outcomes are unchanged.

