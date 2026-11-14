# Paper Strategy: A Bounded Evaluation of Few-Item Benchmark Prediction

## Decision

**Status: ready.** Use the `paper_standalone` family and the `write-paper-standalone` skill downstream. This stage supplies a strategy only, not a paper draft or final-paper validation.

**Provisional title:** *Score-Targeted Item Selection for LLM Benchmark Prediction: Accuracy and Evaluation Limits*.

**Central question:** What do grouped model holdouts reveal about fixed-prefix, source-only LLM benchmark prediction from 8, 16, or 32 responses, once measured prediction errors are distinguished from incomplete evaluations and failed controls?

**Central thesis:** The score-covariance design with a group-tuned residual-profile/ridge predictor supports a conditional, heterogeneous description of few-item prediction on fixed benchmarks, but missing primary and baseline predictions and failed structural controls prevent a qualified overall accuracy or selection-advantage claim.

This is a method-and-limitations study, not a search diary, an overall superiority claim, or a claim that learned item selection necessarily worsens prediction. A completed unsuccessful qualification can support this bounded scientific story. Publication suitability does not change the method's qualification.

## Evidence That Chooses the Story

Read `paper_data.json.final_evaluation` independently of the absent `downstream_study`:

- `final.qualification.status`: `completed`.
- `final.qualification.outcome`: `not_qualified`.
- `final.qualification.correct`: `false`.
- `final.evidence.episodes`: three seeds, ten fixed benchmark universes, and budgets 8, 16, and 32, with target scores, predictions, completion indicators, structural checks, and comparison predictions.

The final evidence contains missing primary predictions for `commonsense` at seeds **5003** and **9001**, with the reference-baseline predictions absent in the same records. Several matched structural checks fail there as well. The evaluator assigns worst-case error defaults to missing outputs and missing baselines. Consequently, its reported MAE is not purely the average error of observed predictions. The same caveat applies to the reported aggregate RMSE and rank correlations.

`task/evaluate_final.py` requires complete evaluations and passing structural checks; it does not require a novel-method accuracy improvement or target-adaptive acquisition. The observed omissions and structural-check failures identify concrete evidence-integrity limitations. They do **not** identify the underlying exception, implementation defect, or any unreported gate diagnosis. Preserve unknown causes as unknown.

The stored paired interval endpoints `[-1, 1]` are initialized fallback values when complete pairing is unavailable, not an informative measured confidence interval. The paired contrast also has its own missing-record convention: do not reconstruct it by subtracting the two reported aggregate MAEs.

### Why This Beats the Alternatives

| Candidate framing | Decision and grounded reason |
| --- | --- |
| Accuracy improvement supported by development success | Reject. Final qualification failed; development performance does not establish final validity or superiority. |
| Uniform selection is better than learned selection | Reject as a causal thesis. The aggregate ordering mixes observed errors and missing-output penalties; the fitted uniform mode also refits/tunes its predictor. |
| Broad method superiority across benchmarks or architectures | Reject. No evaluated architecture intervention, certified ancestry independence, or informative overall paired interval supports this. |
| A protocol-only account with no estimator | Reject. The delivered source supports a concrete score-targeted design and prediction mechanism, and retained matched predictions support substantive descriptive comparisons. |
| A bounded evaluation of the delivered estimator, its comparisons, and its evidence limits | Select. It uses both the scientific method and the final evidence without converting missing outputs into measured prediction failures. |

No `study.*` sources are available. Do not include search score differences, search-selection performance claims, or scored/unscored attempt counts using other source families instead. The frozen delivered method is the object of study; its discovery order is irrelevant.

## Prior Story and Staged Inputs

This is not edit mode: there is no supplied edit-context file, seeded `previous_paper/`, `aggregated/`, or `extra_tasks/` bundle. The JSON field `prior_paper_story_status: rejected` rejects an inherited improvement narrative, **not** a nonexistent reviewed manuscript. Preserving or broadening an actual prior paper is inapplicable; recentering on the final evidence is the fresh framing decision.

Inspecting the delivered selected-method source and its `METHOD.md` establishes the method family directly. It does not establish which fitted instances selected a nonzero particle contribution. Final prediction evidence changes the story more strongly than the private memory's interpretation of the aggregate selection-control reversal.

Use one shared scientific question with source-specific evidence blocks:

- Open LLM Leaderboard-derived: `bbh`, `gpqa`, `musr`, `openllm_math`.
- HELM-derived: `commonsense`, `gsm`, `legalbench`, `math`, `med_qa`, `mmlu`.

These are fixed staged binary-score universes, not interchangeable versions of every upstream benchmark and not a transfer or architecture intervention.

## Method Groups and Explanation

1. **Studied estimator:** source-only score-covariance item design and group-tuned residual-profile/ridge prediction. Explain the scalar target—the source model's full-benchmark mean—and why conditional score covariance is a plausible item-design objective. State its empirical, source-distribution character rather than promising target optimality.
2. **Uniform selection with fitted prediction:** the recorded `no_diversity` condition replaces the order with seeded uniform prefixes and reruns fitting/tuning. This is a design-and-refitting intervention, not a selector swap holding numerical predictor parameters fixed.
3. **Observed-mean controls:** `no_calibration` returns the mean of selected responses; the evaluator's `uniform` baseline returns a uniform-item sample mean. Neither is the fitted uniform-selection estimator. The former removes the learned prediction procedure, not just one calibration coefficient.
4. **Anchor and IRT references:** retain the original anchor comparison wherever matched predictions exist, plus the evaluator's regularized two-parameter IRT reference. Explain their actual implementations; do not call them audited reproductions of published packages.
5. **Supporting references and integrity checks:** source-mean prediction in a compact table; constant, copied, permuted and replayed observations in an integrity audit, not as candidate deployment methods.

Discarded residual-audit and earlier covariance-only branches need not occupy the narrative. Source-tuning options are not independent measured ablations. In particular, no final standalone residual-weight, offset, group-prior, or mixture intervention isolates the particle mechanism.

The method section should explain the actual source-only pipeline with equations and implementable detail:

- Equal total source-group mass for acquisition and particle priors; conditional covariance/variance selection with a nugget and low-rank updates; one nested order, not target-adaptive queries.
- Unweighted ridge fitting with intercept/shrinkage, with source-group-disjoint tuning and training-fold means. Do not describe every fitting operation as group-weighted.
- Rasch-smoothed response profiles, residual interpolation, ability-offset particles, and a Bernoulli prefix likelihood with group-balanced prior mass.
- Full-score reconstruction from the exact observed total plus expected unqueried total, then a convex blend with the linear fallback.
- Rebuilding selection and prediction within source validation folds; tuning is not independent outer validation. Model posterior spread is not demonstrated calibrated uncertainty.

The delivered documentation supports these mechanisms. Retained scores do not prove that every component contributed to successful predictions.

## Results: Separate Scored Aggregates from Measured Predictions

### Main Evidence Order

1. Establish the **availability and structural-check mask**, including missing primary/reference records and failed controls.
2. Show a compact table of **recorded final aggregates**, explicitly labeled as including worst-case defaults where outputs are missing.
3. Compare **available matched predictions** by benchmark, then examine budget and ranking behavior under the same stated support rule.
4. Interpret heterogeneity and the evidence boundary, without turning conditional analyses into a repaired or qualified evaluation.

The aggregate table can include these recorded values:

| Condition | Recorded aggregate MAE | Grounding source |
| --- | ---: | --- |
| Studied estimator | 0.08801465854359276 | `final.metric.mae` |
| Uniform selection with fitted prediction | 0.044910877034389785 | `final.metric.no_diversity_mae` |
| Selected-item observed mean | 0.10836174574059959 | `final.metric.no_calibration_mae` |
| Uniform-item sample mean | 0.1335974367939037 | `final.metric.uniform_mae` |
| IRT reference | 0.1186668212839868 | `final.metric.irt_mae` |
| Anchor reference | 0.22047382735923254 | `final.metric.anchor_mae` |

These are **not** a pure measured-accuracy leaderboard. In particular, the lower fitted-uniform aggregate does not demonstrate a causal selection advantage. Missing reference outputs are not measured baseline MAE of one.

For conditional figures, first determine support from availability and the relevant structural flags, not from favorable metric values. Use the common case-seed intersection across each figure's displayed methods and state retained and missing support. Recompute budget-specific errors and rank correlations from stored predictions and `target_full_means`, with deterministic scripts. Keep missing predictions null and preserve every failed record in the audit.

When conditionally aggregating, retain equal source-domain weight, equal cases within domain, equal retained seeds within case, and equal checkpoints when averaging budgets. Explain the changed within-case support normalization. Do not silently drop an entire failed case, silently replace the official aggregate, or represent this conditioning as confirmatory validation.

Show all three seeds where available; use clearly labeled descriptive ranges, not invented error bars. Seeds and models overlap, and fixed benchmarks are not independent benchmark/item-population samples. An informative paired interval is unavailable. Any later dependence-aware uncertainty calculation must be separately labeled exploratory, derived from actual records, and never guessed here.

The main-text audit must preserve the failed qualification and describe incomplete records and failed checks. A successful checked replay (`final.metric.reset_max_abs_error = 0.0`) does not validate every other requirement. Unverified candidate diagnostics are not independent evidence.

## Required Figures and Readability Budgets

### Template Geometry

The inspected `paper.sty` specifies **one text column, 5.5 inches wide and 9 inches high**. Thus ordinary column width and full text width coincide. Use regular single-column figures at `\linewidth`; a `full_width` strategy label does not call for a two-column float. Treat the supplied style as the selected format artifact, not proof that official-template freshness has been independently checked.

### Figure 1 — Method and Evidence Overview

- **Purpose:** immediate glance value for the source-only design, target prefix, estimator, and distinction between prediction error and unavailable evidence.
- **Generator:** `generate-concept-figure`; this is the only planned figure using that workflow.
- **Placement/footprint:** page 1 or 2; full text width, approximately **5.5 × 1.9 inches**, plus caption.
- **Content budget:** one diagram, at most six concise blocks arranged in two rows with no more than three blocks per row; at most three visual streams; final-size text at least **9 pt**.
- **Layout justification:** the mechanism is not legible from scores alone. Two short rows at the actual single-column width explain information access without dense architecture artwork. Separate the optional particle and ridge branches; do not draw arrows implying demonstrated improvement.

### Figure 2 — Available-Pair Method Comparison

- **Purpose:** measured MAE across benchmarks for primary, fitted uniform selection, anchor and IRT, without plotting missing-record defaults as observations.
- **Generator/type:** `matplotlib`, grouped horizontal dot plots.
- **Placement/footprint:** full text width, approximately **5.5 × 3.8 inches**, plus caption; two vertically stacked source-domain panels.
- **Readability budget:** two panels, one per row; four and six benchmark categories respectively; four method series maximum; final-size text at least **8.5 pt**.
- **Implementation:** equal-budget average within each available matched seed; seed points plus an explicitly descriptive available-seed mean; common-support annotations; unavailable markers outside the numerical axis. Use one legend and a shared labeled linear scale.
- **Layout justification:** full width leaves room for case labels and four methods; vertical stacking avoids squeezing six cases into a narrow panel. If scale separation hides useful comparisons, simplify/rework the plot and use its accompanying absolute-value table—do not shrink labels or suppress the original anchor reference.

### Figure 3 — Item Budget, Error, and Ranking

- **Purpose:** compare fitted reconstruction and raw response means under selected and uniform items, using both error and ranking quality.
- **Generator/type:** `matplotlib`, grouped dot plots without development trajectories.
- **Placement/footprint:** full text width, approximately **5.5 × 2.5 inches**, plus caption; two side-by-side panels for MAE and Spearman correlation.
- **Readability budget:** two panels in one row, three budget categories each, four method series maximum; final-size text at least **8.5 pt**; one shared legend.
- **Methods:** primary, fitted uniform selection, selected-item observed mean, uniform-item sample mean. Use identical available support across the displayed methods and both panels, and document conditional aggregation weights.
- **Layout justification:** three categories permit readable approximately 2.6-inch panels. Distinct metric labels and directions prevent readers from conflating lower error and higher correlation. Budgets are experimental conditions, not search milestones. Do not assume monotonic behavior.

### Main Tables and Export Rules

Keep the aggregate/default-disclosure table and compact missing-record/structural-check audit next to the results, not solely in the supplement. Quantitative figures must export **vector PDF and PNG at 300 DPI**, with LaTeX referencing the PDF whenever available. Keep source files and the editable overview. Raster-only full-width output must be regenerated at **at least 2400 px** wide; any later column-width raster-only output needs **at least 1200 px**. Never upscale existing rasters.

## Body Layout: Substantive 8.5-Page Target

ICLR 2026 requires an anonymous **8–9-page body**, excluding references; an 8-page body qualifies for the layout requirement only when its final page is at least 75% full. Plan approximately:

| Content | Body pages, including associated visuals |
| --- | ---: |
| Title, abstract, introduction, early overview | 1.4 |
| Focused related work | 0.6 |
| Problem, fixed-universe protocol, evidence mask | 1.3 |
| Source-only design and prediction method | 1.7 |
| Comparisons, budget/ranking results, aggregate and audit tables | 2.2 |
| Discussion and limitations | 1.0 |
| Conclusion | 0.3 |
| **Target** | **8.5** |

These are planning allocations, not measured quantities. Spend available space on the estimator equations, comparator semantics, fixed-universe/grouped protocol, clear comparisons, uncertainty limits, and failure evidence. Do not pad with development branches, generic motivation, speculative experiments, or repeated caveats. Preserve enough main-text detail to understand the method and central limitations without the supplement.

Suggested headings: **Introduction; Related Work; Fixed-Benchmark Score Prediction; Source-Only Item Design and Prediction; Evaluation Protocol and Evidence Availability; Prediction Error and Ranking on Available Pairs; Discussion and Limitations; Conclusion.**

Omit names, affiliations, acknowledgements, funding statements, identifying links and internal host paths. Include the required separate **LLM Usage** section after references if convenient. Do not invent a conference checklist requirement; check applicable submission requirements downstream.

## Supplementary Information After References

The supplement expands actual supplied evidence and reproducibility detail. It never hides qualification failure, substitutes for main comparisons, invents future results, or predicts later analysis rankings.

| Heading | Grounded material and source IDs |
| --- | --- |
| Source-Only Design and Predictor Details | Exact design weights, nugget and low-rank updates, ridge/shrinkage grids, Rasch/residual/offset grids, group priors, likelihood and score decomposition, fold rebuilding and tie handling from the delivered `src/program.py` and `src/METHOD.md`. Existing evaluation anchor: `final.evidence.episodes`; link implementation paths separately, since episode evidence alone does not prove method details. |
| Fixed Item Universes and Grouped Splits | Ten cases, staged matrix/audit checksums, source/target grouping, seeds and budgets, realized target support from `task/resources/final/manifest.json`, case metadata and `final.evidence.episodes`. Explain conservative ancestry heuristics, opaque source groups and supplied alignment attestations; do not claim newly audited raw outputs. |
| Complete Case, Budget, and Seed Tables | All stored or deterministically derived MAE/RMSE/Spearman/Kendall results, reference predictions and support masks. Keep failed rows and recorded aggregates separate from available-pair calculations. Sources: `final.evidence.episodes`, `final.metric.mae`, `final.metric.rmse`, `final.metric.spearman`, `final.metric.kendall_tau_b`, and the reference/control `final.metric.*` entries listed in the JSON. |
| Evaluation Completeness and Structural Checks | Exhaustive missingness and structural-check ledger; worst-case defaults; contrast/interval fallback; checked replay identity; unknown underlying failure cause. Sources: `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`, `final.evidence.episodes`, `final.metric.control_failure_rate`, `final.metric.missing_episode_rate`, `final.metric.reset_max_abs_error`, `final.metric.delta_anchor_mae`, `final.metric.delta_anchor_ci_low`, `final.metric.delta_anchor_ci_high`. |
| Reproducing the Delivered Evaluation and Figures | Delivered code and evaluator/manifest hashes, declared dependencies, staged data provenance, recorded execution configuration and artifact-to-visual transformations. Anchor: `final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome`; add actual local manifests/code links for implementation facts. Distinguish historical experiments from later plotting scripts, and measured timings from unverified runtime details. Do not silently repair the estimator and attribute new results to the frozen evaluation. |
| LLM Usage | Precise evidenced assistance in ideation, implementation, literature planning, and manuscript planning/writing. Anchor the evaluated artifact with `final.evidence.episodes`, and use actual assistance provenance for disclosure—not as scientific metric evidence. Do not invent human verification or unrecorded API/model details. |

The final writer receives any authoritative appendix ranking separately. Route those analyses alongside this plan without retroactively guessing their rankings here.

## Citation and Grounding Discipline

Private grounding map:

- Qualification facts: `final.qualification.*`, independently of any downstream-study status.
- Final numerical summaries: `final.metric.*`.
- Seeds, budgets, cases, targets, predictions, availability, lineage identifiers and structural checks: `final.evidence.episodes`.
- Delivered method: `results/ideas/03_rasch_residual_profile_mixtures_on_fixed_score_targeted_prefixes/program_1/src/program.py` and its `src/METHOD.md`.
- Interpretation of scoring, checks and fallback intervals: `task/evaluate_final.py`.
- Staged provenance: `task/resources/final/manifest.json` and case metadata.

Two permitted exact-title entries were matched to reference provenance: `Vivek2023AnchorPB` and `Polo2024tinyBenchmarksEL`. They contextualize anchors and IRT, not exact baseline reproduction. Metadata retrieval is not proof of full-paper reading; only genuinely inspected permitted literature can ground substantive related-work statements. Do not pad the bibliography with unrelated retrievals. Do not identify/search for the prohibited unnamed paper, traverse citation graphs, or treat private memory as quantitative or citation evidence. Stop and record any accidental prohibited-source exposure without further investigation.

## Language Guardrails and Downstream Handoff

Avoid chronological headings: **Search Progression, Campaign Phases, Milestones, Timeline, First Valid Result, From Failure to Success, Experiment A / Experiment B, Iteration-by-Iteration Results, Winning Configuration**.

Avoid diary phrases: **we then tried, subsequent improvements, next-best, later variants, first valid result, the search winner proves**.

Keep internal labels out of visible scientific prose: **correctness rate, correct and eligible, eligible, combined_score, rubric, worker_01, worker_02**. No thresholded rate is necessary for this story; if one is later needed, define one reader-facing meaning and denominator explicitly.

Also reject unsupported claims: **statistically significant improvement, state-of-the-art accuracy, certified lineage generalization, calibrated posterior uncertainty, uniform sampling is superior, failed qualification means lower accuracy**.

Carry failed qualification and its limitations through **writing, review, audit and revision**. Do not suppress them because other metrics look favorable. Distinguish observed missingness/structural failure from unknown underlying causes, and never equate unsuccessful qualification with demonstrated inferiority. Conditional plots remain conditional descriptions, not proof of valid overall performance.

No manuscript, claim-mapping JSON, new experiment, figure rendering, or final-paper validation belongs to this strategy stage. The downstream writer should implement auditable artifact transformations and the specified figures, preserve the frozen evidence and masks, then draft the standalone paper within these boundaries.
