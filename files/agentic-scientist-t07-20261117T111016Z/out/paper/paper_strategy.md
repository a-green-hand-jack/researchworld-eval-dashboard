# Paper Framing Strategy

**Status:** ready for a bounded standalone study; relevant-literature repair is required before final related-work writing.  
**Prompt family:** `paper_standalone` / `write-paper-standalone`.  
**Provisional title:** *Score-Targeted Subsets for Predicting LLM Benchmark Accuracy*.

## Central Question and Thesis

**Question.** How accurately can a source-trained, score-targeted shared item subset and decoder predict retained full-benchmark accuracy and model rankings at 5-, 10-, and 25-item budgets, relative to local benchmark-estimation baselines, and where does the comparison reverse?

**Thesis.** On nine frozen benchmark matrices, the evaluated acquisition-and-decoding package has lower average accuracy-prediction error than the recorded baselines under equal benchmark, seed, and budget weighting. Its advantage over local IRT is not uniform across benchmarks. The measurements neither isolate an individual decoder component's benefit nor establish transfer beyond this snapshot.

This is one estimation question with condition-specific evidence from leaderboard and HELM matrices, not two chronological experiments. Lead with the estimand, information constraints, and paired comparison, then explain where the average is misleading. A lower average error is the measured result; universal superiority and nonlinear-mechanism attribution are not.

## Independent Evidence and Qualification Audit

Read the final record independently of any campaign narrative. `downstream_study` is absent. The authoritative qualification sources are:

- `final.qualification.status`: `completed`.
- `final.qualification.outcome`: `qualified`.
- `final.qualification.correct`: `true`.

These facts do not establish complete ancestry separation, contamination absence, out-of-snapshot validity, or any unreported gate diagnosis. Publication readiness is not scientific qualification. If a later authoritative record reports failed qualification, preserve that failure and its reported limitations throughout writing, review, audit, and revision; never infer its cause from retained scores. Missing diagnostics remain unknown.

The final evidence contains three seeds, nine distinct cases, and budgets 5/10/25. A BBH normal replay is a determinism check, **not** an extra case or an independent measurement. The aggregate paired uncertainty object is repeated in each seed wrapper; use it once, not as three independent bootstrap results. Candidate-owned diagnostics are explicitly unverified.

### Primary Numerical Anchors

| Quantity | Recorded value | Grounding source |
| --- | ---: | --- |
| Selected package MAE | 0.038991605535293065 | `final.metric.mae` |
| Selected package RMSE | 0.04837892636321264 | `final.metric.rmse` |
| Local IRT MAE | 0.05911223215296765 | `final.metric.irt_mae` |
| Uniform sampling MAE | 0.10520541810011626 | `final.metric.uniform_mae` |
| Source prior MAE | 0.08335016635136305 | `final.metric.prior_mae` |
| Response-vector anchor MAE | 0.15674229873896958 | `final.metric.anchor_mae` |
| Selected package Spearman | 0.8158480130897703 | `final.metric.spearman` |
| Selected package Kendall | 0.6715966634525837 | `final.metric.kendall` |

All errors use score units in `[0,1]`; these are not 25-item-only results. The evaluator averages the declared budgets, seeds, and cases, with target-lineage-equal errors within cells. Ranking is computed from lineage-mean predictions and truths within each cell, not by pooling every model from different benchmarks. An average of cell RMSEs must not silently become a pooled RMSE.

The recorded candidate-minus-IRT MAE is **-0.02012062661767458**, with recorded 95% interval **[-0.02570984836073398, -0.014632649205711504]**, grounded in `final.evidence.episodes`. Its 200-draw paired lineage-block bootstrap retains checkpoints and seeds within groups, averages cases equally, and conditions on the fixed cases. It is not uncertainty over new benchmarks, a component-ablation effect, or a generalization guarantee.

The raw predictions also support direct case/budget views. Diagnostic postprocessing excluding replay and applying the evaluator's lineage weights finds candidate losses to local IRT on **math at all three budgets**, **legalbench at 5 and 25**, and **med_qa at 10 and 25**. Keep those cells visible in the main paper. Regenerate exact plot values from the raw records rather than quoting rounded framing diagnostics. Do not invent causes for the reversals or reuse the aggregate interval as a per-case interval.

## Framing Decision and Alternatives

**Decision: recentered.** This workspace has no resolved edit-context file, previous manuscript, `aggregated/`, or `extra_tasks/` input. This is fresh framing; the label records a narrowing of the broad source-task brief, not an edit to an unseen paper. No inherited title or figure plan is authoritative.

Compare the candidate framings explicitly:

1. **Preserve a prior story with local updates:** no prior manuscript is supplied, and private memory is insufficient justification. Do not inherit a random-audit or discovery-order narrative.
2. **Broaden to a cross-setting method family:** the two data ecosystems support a common estimation question, but not an adaptive-per-target acquisition claim or a general transfer mechanism. Use condition-specific evidence under one thesis, not an enlarged capability claim.
3. **Recenter on the frozen final comparison:** strongest choice because it has paired baseline predictions, a defined scoring protocol, aggregate uncertainty, and scientifically informative reversals.

Reject a random-audit unbiasedness paper: that earlier design is not the final evaluated package. Reject a nonlinear-decoder superiority paper: the selected source tree includes an incumbent fallback, its per-case branch selection is not attested, and no controlled ablation bundle exists. Reject a search-progress paper: the central question concerns prediction quality, not optimization dynamics.

## Implementation and Staged-Input Impact

Directly inspected local sources are under `results/ideas/03_log_odds_shift_residual_decoder/program_1/src/`: `program.py`, `surrogate.py`, and `nonlinear_decoder.py`, together with their implementation notes. The local selection manifest identifies this counterpart of the frozen selected package; no candidate was executed during framing.

The core mechanism is source-weighted covariance between each item response and the full source score. Greedy acquisition maximizes squared conditional score covariance divided by regularized conditional item variance, using a nested common path and excluding already represented content groups. All-query ridge/offset decoding uses every legal queried answer. The implementation also offers a source-selected penalized log-odds shift, original-population score curve, and prefix-matched residual ridge, retaining the linear fallback. Explain these as the implemented decoder menu, not as independently validated contributions.

`task/evaluate_final.py`, frozen manifests, and `task/resources/rebuild.py` establish the evaluator definitions and processed data scope. They support metadata-defined source/target lineage separation and conservative item reconciliation, not proof against undocumented derivatives, semantic duplicates, or pretraining contamination. The truth to be predicted is the full mean over **retained matrix columns**, not necessarily every original benchmark item.

No existing figures or controlled ablations are available. Earlier implementations need not become main-paper narrative baggage. Their code may clarify design alternatives, but no final matched measurements support an original-program comparison. In particular, `task/program_0` is readable, but its old score from memory must not be imported. Keep the actual recorded comparators instead.

## Narrow Method Set

| Group | Role | Inclusion and boundary |
| --- | --- | --- |
| Score-targeted acquisition and source-selected score decoding | Proposed | Frozen final package; describe ridge/offset and optional nonlinear menu without asserting branch activation or component causality. |
| Uniform content-group sampling | Baseline | Group-representative sampling with group-mass correction and clipping; not silently ordinary unweighted averaging. |
| Source-score prior | Baseline | No target responses required; display observation cost as zero. |
| Response-vector anchors | Baseline | Local normalized-response/farthest-first representative selection and cluster-weighted score estimate; not an exact published-method reproduction. |
| Local Rasch-style IRT | Baseline | Strongest aggregate comparator; source-fitted item difficulty and queried target ability on the same uniform path as the sampling baseline. Not the full tinyBenchmarks system. |

The measured comparison changes both acquisition and decoding at matching query budgets. It does not isolate either component, guarantee equal training compute, or establish that every comparator received globally optimal tuning.

## Results Organization

1. **Aggregate accuracy and paired uncertainty.** A compact five-method table gives absolute MAE, observation cost, and separately labeled RMSE/ranking where supported. The forest plot shows the four supplied paired MAE differences and intervals. No performance-success threshold or internal pipeline metric is needed.
2. **Benchmark-specific reversals.** Show all nine cases against IRT at each budget using signed differences with a common zero reference. Put the math, legalbench, and med_qa reversals in the main results and limitations, not only the supplement. Ecosystem panels are organizational, not evidence of a causal ecosystem effect.
3. **Ranking as a distinct objective.** Report the selected package's recorded Spearman and Kendall. Baseline rankings may be derived reproducibly from existing predictions using the evaluator's lineage-mean definition; if not derived, mark them “not reported,” never zero or inferred. Do not claim ranking superiority from selected-package values alone.
4. **Controls and evidence limits.** Permuted-source MAE is 0.06257521756337783 (`final.metric.permuted_mae`); zero-response-control MAE is 0.21577661527598374 (`final.metric.constant_mae`). The constant intervention zeroes target observations; it is not necessarily a constant predictor. The source intervention independently circular-shifts each source row's columns. Describe sensitivity, not isolated ablation or validity proof. Duplicate histories and deterministic replay are protocol checks, not accuracy improvements.

Development and final evaluations are separate. Development uses `arc_challenge`, `ifeval`, `commonsense`, and `gsm`, seeds 101/211. Final uses `bbh`, `gpqa`, `mmlu_pro`, `musr`, `openllm_math`, `legalbench`, `math`, `med_qa`, and `mmlu`, seeds 1009/2003/3001. Do not compare their absolute averages as a paired improvement. There are no `study.*` sources here: no search-score differences, campaign win rates, or scored/unscored performance accounting is proposed. An unscored attempt would be missing evidence, never a measured loss.

## Figure Plan and Physical Layout

The inspected `paper.sty` sets **one 5.5-inch-wide text column and 9-inch text height**. This is not a two-column format: column width equals full text width. Use ordinary full-width figures, not `figure*`, 0.48-width defaults, or dense graphics rescued by shrinking. Render labels at least 9 points. None of the planned figures needs more than one panel per row.

| Figure | Required design and evidence | Footprint and placement | Readability limits |
| --- | --- | --- | --- |
| `score_prediction_overview` | One conceptual information-flow diagram: historical responses/full source scores → source-only shared subset design and decoder selection → legal target query answers → predicted full score; true retained target score remains beyond an external-scoring boundary. Mark nonlinear decoding optional/source-selected. Use `generate-concept-figure`. | Page 2, full 5.5-inch width; about 2.0-inch drawing height plus short caption, roughly 0.30 body page. Full width is necessary for legible matrix roles and information boundaries. | One panel, at most six blocks/categories, three visual information roles/series, at least 9-point labels. |
| `paired_error_comparison` | Horizontal forest plot of selected-minus-baseline MAE for uniform, prior, anchors, and IRT using the single supplied aggregate interval per comparator; common zero line. Generate with matplotlib; canonical manifest type `scatter` (points with intervals). | Around page 6, full 5.5-inch width; about 1.7-inch axes height, roughly 0.26 body page with caption. Comparator labels, signed ticks, and intervals need the complete span. | One panel, four comparator categories, one series. Do not clip interval endpoints or duplicate the interval by seed. |
| `case_budget_reversals` | Two vertically stacked horizontal dot-plot panels: five leaderboard cases and four HELM cases. Each case has three offset budget symbols for candidate-minus-local-IRT MAE. Common signed x-axis; no connected progression lines. Generate with matplotlib; canonical manifest type `composite` (faceted dot plots). | Around page 7, full 5.5-inch width; about 3.2-inch total axes height, roughly 0.43 body page with caption. Stacking avoids illegible adjacent mini-panels and preserves all failure cells. | Two panels, one per row; at most five cases and three budget series per panel; shapes plus color, at least 9-point labels. |

Only the overview uses the concept-figure workflow; the downstream orchestrator, not this framing stage, owns its execution. Preserve editable source and vector exports when available. Quantitative figures must have reproducible source and **both PDF and PNG exports**, with PNG at 300 DPI. LaTeX references the PDF whenever one exists. For raster-only full-width placement, regenerate at **at least 2400 pixels wide**; any justified narrower/column raster-only placement needs at least 1200 pixels. A 300-DPI preview at 5.5 inches is not enough for the raster-only full-width rule. Never upscale an existing image.

## Body Budget and Scientific Structure

Target about **8.5 body pages**, excluding references and substantive Supplementary Information:

| Material | Body allocation including its floats |
| --- | ---: |
| Title, abstract, introduction, early overview | 1.5 pages |
| Problem/estimand and focused related work | 1.0 page |
| Weighted acquisition, decoding, source-only tuning | 1.8 pages |
| Frozen data, fair protocol, baseline definitions | 1.1 pages |
| Aggregate uncertainty, ranking, case/budget reversals | 2.0 pages |
| Interpretation, limitations, conclusion | 1.1 pages |

Suggested headings: **Introduction; Problem and Related Work; Score-Targeted Subset Prediction; Evaluation Protocol; Results** with subsections **Aggregate Accuracy and Conditional Uncertainty** and **Benchmark-Specific Reversals and Ranking; Scope and Limitations; Conclusion**.

Spend available space on precise estimands, the acquisition/decoder equations, group weighting, fold-local refitting, baseline definitions, interpretation of failures, and uncertainty assumptions. Do not add unsupported ablations, inflated related work, repeated plots, or oversized graphics to fill pages. The venue requires 8–9 body pages; an eight-page body must have its final page at least 75% full, and a nine-page body must not overflow the body limit. Check final layout later, not by final-paper validation during framing.

## Supplementary Information After References

**Purpose:** add reproducibility and complete evidence disaggregation without hiding any essential result, reversal, or limitation. Later authoritative appendix rankings can add material here without retroactively changing this strategy.

1. **Weighted Acquisition and Decoder Specification.** Full weighted covariance/conditional-gain and decoder equations, source-only tuning shortlists and group partitions, optional branch, clipping, and zero-budget/insufficient-group fallbacks. Ground in the inspected selected source tree linked to `final.evidence.episodes` and `final.qualification.status`. Clearly distinguish specification from ablation evidence.
2. **Frozen Data and Lineage/Content Provenance.** Pinned snapshot, rebuild script, retained columns, actual evaluated dimensions, grouping rules, hashes, and conservative ancestry/content limitations. Ground the evaluated data link in `final.evidence.episodes` and detail provenance from the local manifests. Do not substitute generic task-brief model counts.
3. **Complete Benchmark, Budget, and Seed Results.** Every non-replay normal cell and its four baseline prediction arrays; reproducible MAE/ranking extraction and reconciliation to the recorded final metrics. Newly derived baseline statistics are postprocessing, not new runs; no invented cell intervals. Sources: `final.evidence.episodes`, `final.metric.mae`, `final.metric.rmse`, `final.metric.spearman`, `final.metric.kendall`, and the four baseline `final.metric.*` entries.
4. **Paired Uncertainty and Observation Controls.** The single fixed-case bootstrap, checkpoint/seed retention, equal-case weights, evaluator missing-cell policy, recorded zero failed normal cells, and intervention/replay/duplicate-history definitions. A no-failure count is not a performance-success rate or universal validity certificate. Sources: `final.evidence.episodes`, `final.metric.constant_mae`, `final.metric.permuted_mae`, `final.qualification.outcome`, `final.qualification.status`.
5. **Reproduction and Evidence Boundaries.** Anonymized reconstruction/evaluation commands based on existing scripts and dependency/specification files, seeds/budgets, hashes, and an eventual script-to-table/figure mapping. Label unrerun commands truthfully, report CPU requirements as requirements, and give no unmeasured speedup or end-to-end time. Include the absence of component ablations/branch-selection diagnostics. Sources: `final.evidence.episodes` and all three `final.qualification.*` entries.
6. **LLM Usage.** The separately required venue section: precise documented roles in ideation, implementation, citation-query planning, framing, and eventual writing/figure assistance; distinguish evaluator measurements from agent-produced interpretation. Disclose actual verification, not fictitious human review. Framing used local inspection and existing-prediction postprocessing, not candidate execution. Link measurements to `final.evidence.episodes`; process roles come from the supplied task/memory provenance, which is not quantitative evidence.

## Literature and Readiness Boundary

The supplied bibliography is mostly off-topic. The retrieval log shows its quota was exhausted before the planned task-specific title queries; relevant source metadata does not imply source reading. Some existing foundational entries may be useful leads, such as `Derezinski2019BayesianED`, `Ravi2016ExperimentalDO`, and `Uto2020AGM`, but their exact relevance must be checked and they do not substitute for the permitted benchmark-prediction literature.

Before final related-work writing, repair this gap using permitted direct-title sources from the task brief and focused unrelated foundational material, maintain citation provenance, and cite only genuinely consulted relevant works with actual BibTeX keys. Do not cite tangential engineering papers to reach a target count. This is a **citation-readiness prerequisite**, not a reason to invent a weaker or broader empirical story. This stage does not modify references or perform retrieval.

Never infer or search for the prohibited paper's identity or expand citation networks toward it. If a later accidental encounter occurs, stop and document location and reading extent. This local-only framing stage identified no such encounter. Omit authors, affiliations, acknowledgements, funding, personal links and internal URLs from the anonymous manuscript. Do not invent a venue checklist requirement absent supporting venue instructions.

## Anti-Diary and Overclaim Guardrails

Avoid headings **Search Progression; Campaign Phases; Milestones; First Valid Result; Iteration History; Experiment A / Experiment B; From Audit to Ridge to Nonlinear; Winning Configuration; Nonlinear Decoder Ablation; Universal Benchmark Prediction**.

Avoid wording **we then tried; subsequent improvements; first valid result; next-best; later variants; state of the art; wins on every benchmark; proves generalization; leakage-free; the nonlinear component caused the gain; unbiased rankings; adaptive per-target acquisition**. Internal field names and pipeline labels listed in the JSON forbidden phrases are private bookkeeping, never visible metrics or prose recommendations.

Do not conflate source-only fitting with complete validity; score error with ranking preservation; aggregate confidence with new-benchmark uncertainty; local baseline families with exact published systems; or an implemented optional module with a measured component gain. Anonymization, qualification facts, mixed results, and scientific limitations must survive later writing, review, audit, and revision.

## Stage Boundary

Deliver only `paper_strategy.json` and this mirrored memo, with append-only memory updates. Do not create `paper.tex`, `claims_grounding.json`, figures, new experiments, or final-paper validation outputs. Validate strategy schema, source-ID existence, figure budgets, qualification preservation, and memo agreement only. No final paper has been drafted in this stage.
