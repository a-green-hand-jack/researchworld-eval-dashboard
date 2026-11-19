# Grounded Reference Query Plan

**Status:** ready. Planning only: no reference retrieval or bibliographic verification was performed.

## Scientific focus and grounding

The paper concerns reliability and efficiency of heteroscedastic split-conformal regions for **observed positive continuous compositions**, using fixed isometric-logratio (ILR) coordinates and training-only local-scale selection under IID and covariate-shift synthetic regimes. It is not a label-set classification study or an evaluation of latent categorical probabilities.

Grounding comes from `paper_data.json`, especially `/all_programs`, `/best_correct`, and `/final_evaluation/evaluation_evidence/episodes`; the selected source `results/ideas/03_training_only_conformal_rank_scale_selection/program_1/src/program.py`; and the public workload description in `task/task_contract.json`. `global_memory_summary.md` supplied qualitative leads only. No existing `references.bib` or `references_provenance.json` was present, so there are no prior retrieval queries to reuse or correct. `figures/` is empty.

### Implemented methods and comparators

- Independent split calibration uses the finite-sample residual order statistic for the maximum standardized ILR residual.
- Centers use polynomial-ridge regression in a fixed Helmert ILR basis. Base scales use log residuals. Training-only cross-fitted standardized residual moments supply Gaussian-kernel local scale corrections, bounded and shrunk toward the neutral correction.
- The selected scale variant uses nested training folds and swapped pseudo-calibration/evaluation halves to select corrections by conformal-rank ILR-box volume. Gaussian-loss selection is the fallback. Actual evaluation calibration remains separate.
- Evaluated comparators are unscaled maximum-ILR residuals, simplex-coordinate L-infinity regions, Bonferroni per-coordinate intervals, a training-only constant center, and the whole simplex. Constant/permuted feature inputs and copy-point/reset checks are controls, not additional literature families.
- Weighted conformal under covariate shift is relevant background only; it was not evaluated. Likewise, subgroup audits do not constitute Mondrian or conditional calibration.

### Benchmark and scope

The synthetic `composition-v1` workload has six continuous covariates and six cases: `LN_IID_K3`, `LN_IID_K8`, `DIR_IID_K3`, `DIR_IID_K8`, `DIR_SHIFT_K3`, and `DIR_SHIFT_K8`. These cover logistic-normal IID responses, heteroscedastic Dirichlet IID responses, and a Dirichlet covariate-shift stress test preserving the conditional response law. Compositions are positive; exact structural zeros and face-specific measures are out of scope.

The completed final evaluation has eight statistical seeds, 1024/512/2048 training/calibration/test observations per case, and miscoverage levels 0.05, 0.10, and 0.20. Feature-defined subgroups use the sign of the first covariate. Normalized simplex volume uses 128 contexts and 1024 shared uniform-simplex probes. These internal case names need not become literature search terms; the underlying distribution families provide precision. No real dataset, image backbone, text corpus, or GPU architecture comparison is evidenced.

### Supported transition and result-driven themes

There is **no neural architecture or representation transition**. The strongest scale-only variants hold centers, ILR coordinates, and region family fixed; the procedural transition is from Gaussian-loss scale selection to training-only conformal-rank ILR-box-volume selection.

The rank-selected variant has the highest recorded search utility. Its final evaluation is completed, unlike the unfinished status in older qualitative memory. However, final evaluation of that variant alone is not an independent paired replication of the selector-only comparison.

Final mean absolute coverage error is 0.013562011718750005 for IID cases and 0.13034261067708333 for shifted cases. This motivates marginal-versus-conditional validity and shift-aware conformal background, not a shift-robustness claim. The final aggregate utility gap over the strongest aggregate comparator is 0.011594669497844157. Nevertheless, mean simplex volume is 0.3034934467739529 for the selected method and 0.29170094596015084 for simplex L-infinity: higher aggregate utility does not mean uniformly smaller regions.

ILR-box volume used in training selection and normalized simplex volume used in evaluation are different measures under a nonlinear inverse transform. Their distinction motivates geometric background, but does not establish a causal explanation for the results. Subgroup Wilson intervals, paired statistical-seed bootstrap intervals, simultaneous baseline intervals, and Monte Carlo resolution bound the interpretation; contexts and shared probes are not independent replicates. These uncertainty features inform interpretation without adding a generic statistics query.

## Nine citation-oriented queries

1. **Core method:** `Lei G Sell Rinaldo Tibshirani Wasserman Distribution-Free Predictive Inference For Regression`  
   Exact starter-literature target for independent split calibration, finite-sample residual ranks, and marginal rather than conditional coverage guarantees.
2. **Core method:** `locally adaptive conformal regression normalized residual scores heteroscedasticity`  
   Places feature-dependent residual scaling in its proper literature; the implemented adaptation changes scores, not calibration locality or neural architecture.
3. **Core method:** `conformal prediction model selection training split prediction region volume`  
   Targets precedents for training-only selection using pseudo-calibration ranks and region efficiency while preserving a separate actual calibration split. Does not presume a new theorem or replicated selector advantage.
4. **Core method:** `isometric logratio transformations compositional data analysis`  
   Grounds the implemented fixed orthonormal ILR representation without implying that alternative representations were compared.
5. **Benchmark context:** `logistic normal Dirichlet distributions compositional regression`  
   Covers the actual synthetic response families and heteroscedastic concentration context rather than unused real-data benchmarks.
6. **Baseline comparator:** `multivariate conformal prediction rectangular regions Bonferroni simultaneous coverage`  
   Grounds joint maximum-residual boxes, simplex-coordinate L-infinity regions, and per-coordinate Bonferroni constructions in simultaneous multivariate prediction.
7. **Baseline comparator:** `Tibshirani Barber Candes Ramdas Conformal Prediction Under Covariate Shift`  
   Exact starter-literature target for distinguishing ordinary split calibration from shift-aware weighting; weighted conformal remains an untested comparator.
8. **Result-driven theme:** `conformal prediction marginal coverage conditional coverage limitations`  
   Supports careful interpretation of feature-group diagnostics under pooled calibration without implying conditional or Mondrian validity.
9. **Result-driven theme:** `logratio inverse transformation simplex Jacobian volume measure`  
   Explains the distinction between ILR-box selection volume and uniform-simplex evaluation volume using change-of-variables background, not an unsupported causal account.

## Exclusions and retrieval safeguards

The prohibited study must not be identified or guessed. Do not search for its title, authors, results, mirrors, summaries, code, or pages citing, discussing, or reproducing it. Avoid broad searches combining conformal prediction, compositional-output evaluation, and benchmark terms; the plan deliberately separates classical geometry, calibration, synthetic distribution families, and reliability limitations. No query can guarantee safe results: if later retrieval accidentally exposes prohibited material, stop reading immediately and record what appeared, where, and how much was seen. Do not pursue citation-network expansion, cited-by pages, related-paper recommendations, or unrestricted survey crawling around it. No prohibited encounter occurred in this local-artifact planning stage.

Do not search as though CIFAR-10, image classifiers, softmax labels, topic models, latent probability targets, exact structural zeros, boundary-face mass, Hellinger or Euclidean comparisons, additive-logratio alternatives, Mondrian calibration, or neural architecture transfer were evaluated. Earlier proposals do not establish implemented experiments. Weighted conformal, jackknife+, conformalized quantile regression, credal sets, clustered conformal, and multivalid prediction must not be represented as evaluated baselines.

Reject generic optimization, benchmarking, scientific-method, paper-writing, campaign chronology, and internal acceptance terminology: they dilute the actual fixed-ILR scale-selection and reliability story. Do not frame queries as proving conditional validity, shift robustness, universal volume superiority, or causal selector gains. The nine queries cover the demonstrated method and expected comparator neighborhoods with no near-duplicates; internal case-name searches and standalone generic uncertainty searches would contribute less precision.

## Handoff

Use `reference_query_plan.json` as the machine-readable plan. Any later retrieval must enforce the exclusion policy, verify bibliographic identity and scientific relevance, and retain provenance; a planned query is not a retrieved or read reference. This stage does not create bibliography, provenance, manuscript, or claims-grounding artifacts.
