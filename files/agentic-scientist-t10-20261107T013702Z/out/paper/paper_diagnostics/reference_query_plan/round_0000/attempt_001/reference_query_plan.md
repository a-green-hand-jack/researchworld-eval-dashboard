# Grounded Reference Query Plan

Status: **ready**. This is a retrieval plan only; no references were retrieved or verified in this stage.

## Central topic

Coverage and interval-width tradeoffs for binary superpopulation mean inference from fixed labeled and unlabeled samples and a frozen scalar predictor, using honest nonlinear score controls against prediction-powered and labeled-only intervals. The target is **E[Y]**, not an unannounced finite-pool mean.

## Grounding and evidence limits

- Primary evidence: `paper_data.json`, especially `/best_correct`, `/final_evaluation/metrics`, and `/final_evaluation/evaluation_evidence/episodes`. Current final evidence takes precedence over historical memory.
- Successful configuration sources: `results/ideas/02_honest_nonlinear_score_controls_with_a_finite_sample_safety_track/program_1/src/program.py:52`, `results/ideas/02_honest_nonlinear_score_controls_with_a_finite_sample_safety_track/program_1/src/METHOD.md:3`, and `results/ideas/02_honest_nonlinear_score_controls_with_a_finite_sample_safety_track/program_1/src/study.py:14`.
- The completed final evaluation contains **256 distinct seeds and seven cases per seed**. Aggregate candidate coverage is **0.9425223214285714** and mean width is **0.12988779848794016**. Historical source notes describe the earlier preparation-only stage; they do not negate the later recorded evaluation.
- Case summaries are attached to the first final episode; the remaining episodes supply individual records. Aggregating those records reproduces the case coverage and paired mean-width differences. Candidate-provided diagnostics are marked unverified; the plan does not use them to assert new mechanisms.
- Candidate-minus-PPI++ mean width is negative only in case 2: **-0.00030173260155952255**, with recorded paired 95% interval **[-0.0004003584986521721, -0.000203106704466873]**. It is positive in the other six cases. The evidence does not support universal improvement.
- Case 5 has truth approximately **0.0068**. The implemented PPI++ comparator has coverage **0.55078125** and **115/256** zero-width intervals; candidate coverage is **0.9296875**. The candidate-versus-exact-binomial width-difference interval includes zero. Narrowness must not be separated from validity, and this failure must not be generalized to every implementation of PPI++.
- Casewise coverage uncertainty includes the nominal level, but non-rejection is not proof of nominal validity. The enormous aggregate width ratio against PPI++ is not evidence of a useful scientific gain; use paired differences and inspect zero denominators instead.
- No existing `references.bib` or `references_provenance.json` is present, and `figures/` is empty. There is no prior retrieval query history here to reuse or correct.

## Method and comparator scope

Core methods are two-fold cross-fitted residual correction with frozen-score controls and finite-unlabeled-sample weight N/(n+N); train-fold-only clipped ridge affine and piecewise-linear spline calibration selected by generalized cross-validation; and Wilson-style stabilized asymptotic Wald intervals with a sample-size-only Clopper-Pearson fallback for n<16.

The source also implements a **separate internal empirical-Bernstein safety track**, using bounded component means and union-bound aggregation. It is not the primary returned interval and has no measured efficiency result here. The conditional-mean oracle and nonlinear-versus-affine variance frontier are theoretical context; oracle attainment is not demonstrated.

Evaluated scientific comparators are original PPI, PPI++, labeled-only asymptotic normal intervals, and labeled-only Clopper-Pearson intervals. The full-range interval is a sanity check, not a separate citation neighborhood. Double/debiased machine learning provides contextual cross-fitting principles, not an evaluated causal-inference comparator. Cross-fitting the calibrator is not evidence that the frozen predictor was trained on the evaluation labels.

**Benchmarks:** no named dataset is identified in the available executed evidence, so the JSON benchmark list is empty and no dataset query is warranted. The seven anonymous binary-mean cases are the observed experiment context; do not relabel them as any dataset listed in the task menu or invent their generating mechanisms.

**Architectural shifts:** none are established, so the JSON list is empty. Affine versus spline score transformations are visible in code, but no reported matched affine-versus-spline ablation establishes a representation-driven improvement. This is not a neural architecture or predictor replacement study.

## Eight selected queries

1. **Core method:** `"Prediction-Powered Inference" 2301.09633`  
   Permitted starter reference and evaluated `prediction_powered_mean` comparator; grounds frozen-prediction residual correction.
2. **Baseline comparator:** `"PPI++: Efficient Prediction-Powered Inference" 2311.01453`  
   Permitted starter reference and evaluated `ppi_plus_plus_mean` comparator; necessary for mixed paired width results and implementation-specific validity caveats.
3. **Core method:** `"Double/Debiased Machine Learning for Treatment and Causal Parameters" 1608.00060`  
   Permitted starter reference for cross-fitting and orthogonal-score principles; not a claim of a causal estimand or an evaluated DML baseline.
4. **Core method:** `"semi-supervised" "mean estimation" "control variates"`  
   Grounds labeled-residual plus unlabeled-control estimation, the finite-N variance identity, and the conditional-mean oracle. The frontier is theoretical, not measured optimality.
5. **Core method:** `"regression splines" "generalized cross-validation" ridge`  
   Targets the actual train-fold ridge/spline machinery and knot selection, not unsupported model-architecture or spline-superiority claims.
6. **Baseline comparator:** `"Clopper-Pearson" "binomial confidence interval"`  
   Grounds the exact labeled-only baseline and size-only small-sample fallback, keeping these guarantees separate from general-n Wald inference.
7. **Core method:** `"empirical Bernstein" "bounded" "mean"`  
   Checks the separate safety track's bound constants and boundedness assumptions; does not imply it was experimentally compared.
8. **Result-driven theme:** `"binomial confidence intervals" "normal approximation" "rare events" Wilson`  
   Addresses case-5 undercoverage and degenerate baseline widths. Wilson-style stabilization of a fitted-control estimator is not an exact Wilson binomial interval or a finite-sample guarantee.

These eight queries separate essential evaluated comparators, implemented inference machinery, and the observed rare-event failure. They are more informative than broad optimization or benchmarking queries and avoid padding the plan with unused datasets or unsuccessful alternatives.

## Retrieval exclusions and safety rules

- Do not infer, identify, search for, access, or use the unnamed prohibited paper or any mirror, abstract, discussion, citing page, reproduction, or associated code. Do not reverse-search the full fixed-input research question or traverse citation/cited-by graphs, surveys, or broad recent-work lists.
- The first three queries should resolve only to their explicitly permitted starter records. The remaining queries describe foundational neighborhoods, **not permission for unrestricted topical searches**: future retrieval must use independently screened unrelated-source allowlists and skip ambiguous hits before opening them. The prohibited work's identity is deliberately unspecified, so this plan cannot certify arbitrary search hits as safe. Do not attempt to discover that identity to construct a filter.
- If prohibited material is encountered accidentally, stop reading immediately and record the location and extent encountered. No external literature was accessed during this planning stage.
- Do not frame queries as proving universal narrowing, exact finite-sample validity of the returned Wald interval, guaranteed 95% coverage from non-rejection, or oracle spline efficiency.
- Do not add Galaxy Zoo, ACS/folktables, Wine Quality, or ppi-python dataset citations merely because they appear in the task menu. No executed artifact links them to this run.
- Do not substitute active labeling, additional samples, predictor retraining/replacement, or deep architecture transitions for the fixed-input setting. Exact hypergeometric partition portfolios and Bernoulli profile likelihood lack successful evaluations here and are not core result-backed citation targets.
- Exclude generic optimization, benchmarking, scientific-method, paper-writing, campaign-order, evaluator-score, and search-history queries. No reference retrieval, bibliography/provenance writing, paper drafting, or claims-grounding generation belongs in this stage.

## Handoff

The JSON and this memo describe the same eight queries and exclusions. Retrieve only after the above safety screening in the later stage, verify actual source contents, and keep measured width comparisons distinct from asymptotic arguments and the unmeasured finite-sample safety track. No failure reason applies: the current artifacts support a coherent, bounded literature neighborhood.
