# Reference query plan

**Status: ready.** Eight queries; planning only. No reference retrieval was performed.

## Scientific focus

The paper concerns conditional gains and limitations of cross-fitted nonlinear frozen-score control variates for population-mean confidence intervals, holding labeled data, unlabeled data, and the predictor fixed. The defensible story is dataset-specific narrowing and informative limits, not universal improvement.

The method families are prediction-powered mean estimation; training-only affine and spline/ridge score calibration with finite-unlabeled-sample weighting; nested selection among zero, affine, and nonlinear controls; within-fold offset-invariant studentization with shared-pool covariance; and regularized signed covariance stacking. These are post-processing changes to a frozen scalar score. There is no supported predictor-backbone transition or architecture-transfer result.

## Grounding and interpretation

- Primary quantitative evidence: `paper_data.json`, `/final_evaluation/evaluation_evidence/episodes` and `/final_evaluation/metrics`. There are 400 final seeds and seven cases. Final aggregate empirical coverage is 0.9610714 at nominal 0.95; minimum case coverage is 0.95. These estimates do not prove nominal coverage, and the resource manifest explicitly disclaims theoretical certification.
- The final mean per-seed candidate/PPI++ width ratio is approximately 0.9423 on `gene_expression`. Corresponding ratios are approximately 1.0267 on `linear`, 1.0256 on `nonlinear`, 1.0184 on `uninformative`, 1.0369 on `constant_nonlinear`, and 1.0189 on `permuted_nonlinear`. These are computed from final episode evidence, not recent memory. They support a conditional, not uniform, gain claim against the implemented comparator.
- Rare-outcome empirical coverage is 0.98. Some implemented PPI++ intervals have zero width. A direct endpoint-ratio audit encountered division by zero; consequently the reported aggregate ratio of 1.2107 and rare-outcome ratio of 2.4059 must not be interpreted as ordinary uncapped ratios of mean widths. The stored paired raw-width summaries are preferable for paper reporting.
- `task/resources/final/manifest.json` identifies the real source as Vaishnav et al., *Nature* 603, 455–463 (2022), via the permitted upstream `gene_expression` example. Labeled and unlabeled records are independently resampled with replacement from the local normalized source; the target is its empirical-source mean, not an independently known biological population mean. Original promoter strings are unavailable, and data redistribution rights remain unresolved.
- Other evaluated cases are synthetic Bernoulli means with frozen `f(X)=X`: linear, nonlinear, uninformative, rare outcome, and constant/permuted-score controls. Their internal case names do not warrant separate dataset citations.
- Method grounding: `global_memory/ideas/02_offset_invariant_risk_adaptive_control_variates/program_1/src/METHOD.md` and `global_memory/ideas/03_smooth_covariance_stacking_of_frozen_score_controls/program_1/src/METHOD.md`. The selected configuration uses nested risk selection and corrected studentization. The stacking variant is contextual, not evidence of dominance. `paper_data.json` contains no paired learner-ablation study; causal attribution to individual changes is unsupported.
- Oracle affine/nonlinear headroom identities motivate classical control-variate context. They are not a proved universal confidence-interval lower bound. Learned overlapping folds require additional asymptotic stability assumptions. The internal bounded-fold certificate does not determine returned intervals and is not a headline retrieval priority.

## Comparator scope

Executed comparators are label-only Student-t/Clopper-Pearson intervals, PPI, and PPI++. Classical control variates provide the estimator lineage. Cross-PPI and double/debiased machine learning provide conceptual cross-fitting comparisons only: fitting a score post-processor is not the same as training the predictor on the inference labels, and the target here is not causal. Published methods must be distinguished from the specific baseline implementations in the run.

## Query set

1. **Baseline comparator:** `"Prediction-Powered Inference" 2301.09633`  
   Exact permitted starter reference for the executed PPI baseline and labeled/unlabeled mean-inference setting. Resolve this work only; do not expand citations.
2. **Baseline comparator:** `"PPI++: Efficient Prediction-Powered Inference" 2311.01453`  
   Exact permitted starter reference for power tuning. Necessary to position the observed gene-expression benefit and absence of uniform improvement against an efficient comparator rather than label-only intervals.
3. **Baseline comparator:** `"Cross-Prediction-Powered Inference" 2309.16598`  
   Exact permitted starter reference to distinguish cross-fitting a learned predictor from cross-fitting score calibration around an externally frozen predictor. Not an executed baseline.
4. **Core method:** `"Double/Debiased Machine Learning for Treatment and Causal Parameters" 1608.00060`  
   Exact permitted starter reference for sample splitting and learned-nuisance assumptions. It does not establish this estimator's coverage automatically or change its mean estimand into a causal one.
5. **Core method:** `"control variates" "conditional expectation" "estimated coefficients"`  
   Foundational works published before 2023 only. Connect nonlinear/affine variance reduction and estimation costs to the implemented controls. Verify whether auxiliary expectations are known or estimated; finite unlabeled-sample noise matters here.
6. **Architectural shift:** `"stacked regression" "cross-validation"`  
   Foundational works published before 2023 only. Contextualize hard selection versus regularized signed score aggregation without claiming predictor retraining, architecture transfer, or superior stacking.
7. **Result-driven theme:** `"binomial confidence intervals" "Clopper-Pearson" "Wald"`  
   Foundational works published before 2023 only. Interpret rare-outcome conservatism, zero-width baseline intervals, and coverage/width tradeoffs. A standalone exact interval does not certify an adaptive mixture of procedures.
8. **Benchmark context:** `Vaishnav Nature 603 455 463 2022 gene expression`  
   Resolve only the original source explicitly identified in the local manifest. Do not invent its title, infer unobserved sequence inputs, or present frozen scalar-table results as a Transformer comparison.

## Retrieval boundaries and rejected alternatives

The JSON `forbidden_query_patterns` is binding for downstream retrieval. Exact permitted starter references should be resolved by their identifiers, without cited-by lists, related-paper feeds, surveys, or citation-graph expansion. The three foundational topical queries require a publication-before-2023 filter and independent prohibited-content screening; a date filter is not proof that a source is permitted. The benchmark query is restricted to the manifest-identified original source. These queries are not permission for an unrestricted literature sweep.

Do not attempt to identify or reconstruct the unnamed prohibited paper, its title, authors, results, mirrors, code, or discussions. If prohibited material is encountered incidentally, stop reading immediately and record where it appeared and how much was exposed, as the task requires. Do not continue through abstracts, full text, or linked discussion. If a candidate's permissibility cannot be established without risking that restriction, skip it rather than broaden the search.

Reject broad searches for recent work on shorter fixed-predictor intervals: the exact permitted PPI-family references and historical foundations give a useful, narrower neighborhood. Reject generic optimization, benchmarking, scientific-method, and paper-writing terms because they do not explain these estimators or results. Reject campaign chronology and internal score searches because they are not scientific related work.

Do not query Galaxy Zoo, forest, AlphaFold, census/ACS, plankton, ballots, Wine Quality, or California Housing as evaluated benchmarks: none appears among the final cases. Do not search for predictor-backbone comparisons, Transformer retraining, active label acquisition, or extra unlabeled sampling as experimental contributions. Do not phrase queries as established universal narrowing, exact learned-control coverage, proved saturation optimality, or stacking superiority.

No existing `references.bib` or `references_provenance.json` was present, so there are no prior off-topic retrieval queries to carry forward. `figures/` is empty. Recent global memory was used only as qualitative orientation; the final evidence and local resource manifest govern this plan. No references, provenance, paper source, or claims-grounding file is written at this stage.
