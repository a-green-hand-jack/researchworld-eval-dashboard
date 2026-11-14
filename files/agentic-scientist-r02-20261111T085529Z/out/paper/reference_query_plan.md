# Reference Query Plan

**Status:** ready

## Central topic
Evaluating the reliability (marginal, conditional, shift-robust coverage versus set size) of split conformal prediction-set methods applied to compositional softmax outputs on synthetic multi-family benchmarks.

## Core Methods
- Split conformal prediction with LAC score
- Mondrian (class-conditional / confidence-bin) conformal calibration
- Gated domain-classifier weighted conformal under covariate/label shift
- Group-indicator quantile-regression conformal thresholds with fallback

## Comparators
- LAC
- APS
- RAPS
- classwise conformal
- uncalibrated top-mass baseline
- trivial baselines
- negative controls (permuted calibration labels, shuffled test labels, constant uniform input)

## Benchmarks
- Evaluator-generated synthetic softmax families (K in {10,50,100}: exchangeable, temperature-miscalibrated, long-tailed prior, heteroscedastic, covariate/label shift)
- No real dataset (e.g. CIFAR-10) was used in the run

## Architectural Shifts
- Plain LAC -> Mondrian grouping -> gated importance-weighted Mondrian -> gated quantile-regression thresholds (no gain over previous variant)

## Result Driven Themes
- Exact marginal validity coexists with residual worst-slice coverage gap
- Importance weighting reduces shift coverage gap but increases set size
- Quantile-regression conditional thresholds gave no measurable gain over weighted Mondrian in search
- Beats best baseline on final evaluation with CI excluding zero

## Queries
1. `least ambiguous set-valued classifiers conformal LAC softmax score` (core_method) — LAC (1 - softmax of true class) is the base nonconformity score in all three variants; need its original set-valued-classifier source.
2. `adaptive prediction sets APS RAPS conformal classification regularization` (baseline_comparator) — Evaluator runs APS and RAPS as baselines on identical synthetic softmax data; final score margin over best baseline (+0.039, CI [0.027,0.050]) is the headline comparison.
3. `Mondrian conformal prediction class-conditional label-conditional validity` (core_method) — Chosen configurations are Mondrian (class-conditional for K<=10, confidence-bin for K>10); classwise baseline also in evaluator.
4. `clustered conformal prediction many classes class-conditional coverage` (baseline_comparator) — K in {10,50,100} with limited per-class calibration data; confidence-bin grouping for K>10 relates to clustering/grouping remedies for class-conditional coverage.
5. `weighted conformal prediction covariate shift label shift importance weights` (core_method) — Best configuration adds gated domain-classifier importance weights (test mass at +inf, effective-sample-size margins); shift gap fell from 0.061 to 0.020 in search runs.
6. `density ratio estimation probabilistic classifier importance weighting covariate shift` (architectural_shift) — Weights come from a cross-fitted ridge-logistic domain classifier with a held-out shift-detection gate, an implied density-ratio-by-classification literature.
7. `conformal prediction conditional coverage impossibility group-conditional guarantees` (result_driven_theme) — Worst-slice coverage gap (class/size/difficulty strata) stays 0.04-0.07 despite exact marginal validity (~0.001-0.0003 gap); must cite limits of distribution-free conditional coverage and group-conditional methods.
8. `conformal prediction conditional coverage via quantile regression of nonconformity scores` (architectural_shift) — Third variant used group-indicator pinball quantile-regression thresholds with out-of-fold offset and exact fallback; it gave identical scores to the second variant (fallback/no gain), a result needing this literature.
9. `size-stratified coverage metric evaluating conformal classifiers adaptiveness` (result_driven_theme) — Reliability protocol is multi-axis (marginal gap, worst-slice gap, set-size ratio, shift gap, negative controls); need prior evaluation metrics for set-valued classifiers.
10. `compositional data analysis simplex log-ratio transformation Aitchison geometry` (benchmark_context) — Outputs are softmax simplex vectors (Aitchison framing); motivates simplex-valued outputs and what is and is not exploited by scalar-score conformal methods.

## Forbidden patterns
- generic 'benchmarking' or 'optimization' phrasing
- campaign/search-history or milestone-shaped queries
- CIFAR-10 / real-image dataset queries as main topic (not used in run)
- regression-only conformal intervals unrelated to set-valued classification
- the withheld prior paper on this task, its title/authors/results or any page citing it

## Notes
Grounding: three model variants evaluated on synthetic softmax families only (final score 0.842 vs best baseline 0.803; shift gap 0.054; worst-slice gap 0.068). Queries target literatures those methods and results imply; generic process queries rejected. No retrieval performed. Search for the withheld prior paper is prohibited.
