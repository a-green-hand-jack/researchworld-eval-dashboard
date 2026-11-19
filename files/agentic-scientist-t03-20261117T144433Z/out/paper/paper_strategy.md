# Paper Strategy

**Status:** ready. **Prompt family:** `paper_standalone`. **Writing skill:** `write-paper-standalone`. **Venue:** ICLR 2026, anonymized single-column submission; 8–9 body pages excluding references. This is a framing plan, not a manuscript.

## Central Story

**Provisional title:** Repeatability and Reference Fidelity of Finite-Budget SHAP

**Research question:** For fixed trained tabular models and empirical interventional games, how do finite-budget SHAP estimates compare in repeat agreement, reference fidelity, and measured cost, and does averaging four short runs help relative to one longer run at equal coalition count?

**Thesis:** In the retained two-dataset audit, repeat agreement and near-exact additivity do not certify reference fidelity, and averaging four short explanations has lower mean reference fidelity than one longer explanation at equal coalition count; neither observation establishes universal unreliability or sampler superiority.

A standalone empirical audit is supported by retained attributions, references, measured costs, within-fit input-cluster intervals, and a completed final evaluation. The strongest result is a calibrated distinction between repeated top-feature agreement, reference-sensitive attribution error, and budget allocation, not a winning optimization method. German Credit and California ACSIncome share one empirical interventional estimand but require separate reference-quality evidence blocks: approximate references for German Credit and exact coalition references for ACSIncome. The frozen studied sampler was selected without a qualifying search winner. Independent final qualification is completed/qualified/true, not failed. Descriptive final metrics and unverified retained diagnostics do not establish generalization, causal validity, or deployment safety.

## Framing Decision and Alternatives

**Decision: recentered.** Not an edit-mode preservation decision: no resolved edit-context files, previous_paper, aggregated, or extra_tasks inputs are present. Recenter the broad source-task ambition and speculative memory on the actual frozen sampler and retained audit. A prior manuscript is not claimed to exist. Reject a winning-sampler story; reject a universal high-risk deployment verdict; prefer the shared fixed-game audit with reference-specific evidence blocks. An available detailed implementation is not evidence of superiority.

- Preserve a prior story with local updates: no prior manuscript is present; preserving speculative broad deployment claims would exceed the evaluated evidence.
- Broaden to a shared sampler family: reject as the center of the paper; conditioning and interaction-alias variants are search-only branches, not controlled final ablations.
- Recenter on the frozen method and actual audit: select this option. Repeated attributions, references, allocation contrasts, costs, and within-fit intervals answer a coherent fixed-game question.
- A negative-results component is scientifically useful without a search winner; final qualification must still be read independently.

## Evidence and Staged-Input Effects

- Direct inspection of source_evidence/downstream/program/src/program.py identifies stratified kernel-size sampling, complement-pair coverage, rank headroom, and the unchanged efficiency-constrained least-squares solver; this is the studied method, not the later conditioning or interaction-alias proposals.

- Direct inspection of source_evidence/downstream/baseline/src/program.py identifies independent kernel-marginal sampling with the same solver. Its original search comparison is retained as context; no paired final attribution arrays for this original sampler were found.

- study.* identifies a non-winner selection, three scored attempts, zero unscored attempts, and zero search-score difference from the original baseline. These selection facts cannot substitute for final scientific comparisons.

- final.qualification.* independently reports completed, qualified, and true. Do not invent failed qualification from the no-winner search outcome. Missing detailed qualification-gate diagnostics remain unknown.

- final.evidence.episodes supplies two fitted seeds, six dataset/model conditions, two backgrounds, two coalition budgets, repeated candidate estimates, package Kernel SHAP comparators, references, and one deterministic replay. Its diagnostics are explicitly unverified; all substantive results must retain this provenance limitation.

- The downstream source mapping identifies the staged selected family directly, while its tree digest and the final-evaluation program-tree digest differ. Describe the final linkage as manifest-bound evaluation plus family-level source correspondence, not independently verified exact-file identity; do not discard evaluated family evidence solely because hashes differ.


### Authority and qualification

Selection and search-score statements use `study.selection_kind`, `study.investigation_outcome`, `study.baseline_score`, `study.search_score`, `study.search_score_delta`, and `study.attempts.*`. Independently, `final.qualification.status`, `final.qualification.outcome`, and `final.qualification.correct` report completed, qualified, and true. There is no grounded final qualification failure to disclose in this run. Do not reinterpret the no-winner search as failure of the final evaluation. Missing detailed gate diagnostics remain unknown.

Final descriptive metrics are repeat overlap 0.9458719135802469; reference fidelity 0.9289530659189914; numerical-efficiency quality 0.9999999999999954; averaging-minus-long-run quality difference −0.03883354541895445; reference-agreement quality 0.992225794670848. Sources: the corresponding `final.metric.*` entries. These are different mathematical quantities, not calibrated reliability probabilities. Arithmetic means over the non-replay cases reproduce the reported repeat overlap, fidelity, and allocation contrast to floating-point precision; this is not an independent execution audit.

## Method Groups

- **Stratified complementary coalition sampling** (proposed): Frozen studied configuration. Explain kernel-size stratification, complement-pair finite-population coverage, rank headroom, and the fixed constrained solver; proposed labels its role, not demonstrated superiority.

- **Library Kernel SHAP at deployment budgets** (baseline): Retained final attribution vectors and prediction-row/CPU counters permit a direct descriptive reference-fidelity comparison at each nominal coalition budget. It is not the original independent sampler and has only one stored call per cell/budget.

- **Four-short-run attribution average** (supporting): Observed allocation comparator: average four additional 64-coalition explanations and compare with the first 256-coalition explanation from the same fixed game. This is not a clean sampler-component ablation.

- **Exact and high-budget attribution references** (supporting): Exact enumeration anchors the ten-player ACSIncome games; two high-budget library references characterize German Credit reference sensitivity. These are accuracy anchors, not competing deployment methods.

- **Original independent kernel-marginal sampler** (baseline): Preserve the original comparator and unchanged-solver relationship. Only search-scope score context is available for its comparison with the frozen method; omit any unmeasured final fidelity or repeatability comparison.


Controls and terminal replay support functional/reproducibility checks only. There is no controlled component ablation establishing the benefit or harm of pairing or stratification.

## Results Focus

- Primary: show repeat top-three-set overlap and reference-fidelity quality separately by dataset, model family, and fitted seed, using existing within-fit input-cluster intervals. Their scales have different meanings; never subtract them or interpret overlap as a probability of a correct explanation.

- Primary: report the observed averaging-minus-one-long-run quality difference, with its signed zero reference and stored within-fit intervals. The final mean is -0.03883354541895445; it is not a candidate-minus-original-baseline improvement.

- Direct descriptive comparison: frozen sampler versus library Kernel SHAP reference fidelity at nominal budgets 64 and 256, separating both fits and datasets. Check actual prediction rows and distinguish wall durations from package CPU counters.

- Condition specificity: distinguish the exact ACSIncome reference setting from approximate German Credit references. Dataset differences are confounded with dimension, data composition, reference construction, and fitted models, not an isolated mechanism.

- Report numerical efficiency residuals and evaluator-reported control/completion outcomes as checks, not attribution accuracy, causal validity, or high-risk deployment certification.

- Keep search selection and final findings separate. Use study.* for attempt counts and score differences; never turn missing attempts into losses. Omit conditioning/alias branches from core results because there are no controlled final component ablations.


## Figure and Layout Contract

`paper.sty` specifies `\textwidth 5.5 true in` and `\textheight 9.0 true in` (lines 48–49). The format is single-column. Full width means the 5.5-inch text area, not the sheet; there is no second column. All four required figures use the full text width. A half-text-width panel would not rescue a dense layout. No trajectory/progression plot is warranted.

### fixed_game_overview

- **Purpose:** Make the fixed empirical game, compared estimators, exact versus approximate anchors, and allocation contrast legible at a glance without implying sampler superiority.

- **Type/generator:** `diagram` / `generate-concept-figure`; required.

- **Mapping:** group by evidence_role; split by reference_kind; metric: none; conceptual structure only.

- **Footprint:** paper.sty sets a single 5.5-inch text column and 9-inch text height. Use the full 5.5-inch text width, approximately 1.8-2.0 inches high plus caption, near page 2. A half-text-width diagram would make six semantic groups and reference annotations unreadable.

- **Readability budget:** 1 panels total; at most 1 per row; 6 categories and 4 series per panel; final font ≥9 pt. No progression.

- **Content:** At most six semantic groups: fixed model/input/background and probability estimand; coalition sampling; repeated attributions and library comparator; agreement and fidelity readouts; exact ACSIncome/two approximate German references; four short versus one long allocation. Mark evidence scope and unverified diagnostics in the caption. Arrows denote data dependencies, not discovery order or a production certification pipeline.

- **Grounding:** `final.evidence.episodes`.

### agreement_and_reference_fidelity

- **Purpose:** Contrast repeatability with reference-sensitive quality without conflating metrics or datasets.

- **Type/generator:** `point_interval` / `matplotlib`; required.

- **Mapping:** group by model_family; split by dataset and metric; metric: top-three-set overlap and normalized L1 reference-fidelity quality in separate panels.

- **Footprint:** At the inspected 5.5-inch single-column width, a 2-by-2 layout gives roughly 2.5 inches per panel, sufficient for three short model labels and two fitted-seed markers. Allocate roughly 2.8 inches plus caption on pages 5-6; use at least 8.5-point final labels and never shrink to half text width.

- **Readability budget:** 4 panels total; at most 2 per row; 3 categories and 2 series per panel; final font ≥8.5 pt. No progression.

- **Content:** Rows: German Credit/ACSIncome; columns: repeat overlap/reference fidelity. Show two fits individually. Use case means and stored input_cluster_intervals, both pooled over the same background/budget levels. Caption labels intervals descriptive within-fit 95% input-cluster bootstrap intervals; do not attach pooled intervals to budget-specific points. Explain that exact and approximate fidelity anchors differ.

- **Grounding:** `final.evidence.episodes`, `final.metric.repeat_agreement`, `final.metric.reference_fidelity`.

### budget_allocation_contrast

- **Purpose:** Show the observed cost-allocation result and uncertainty, retaining negative and uncertain effects.

- **Type/generator:** `point_interval` / `matplotlib`; required.

- **Mapping:** group by model_family; split by dataset; metric: quality(mean of four additional 64-coalition runs, reference) minus quality(first 256-coalition run, reference).

- **Footprint:** Two side-by-side panels across the single 5.5-inch text column support three model labels, two seed markers, intervals, and a visible zero line. Target about 1.9-2.1 inches plus caption on page 6 or 7; reserve caption space for the exact contrast and reference definition.

- **Readability budget:** 2 panels total; at most 2 per row; 3 categories and 2 series per panel; final font ≥8.5 pt. No progression.

- **Content:** Show both fitted seeds separately with stored gain intervals and one common signed interpretation. German gain uses the mean reference vector, whereas its ordinary fidelity metric averages qualities to each reference. Equal coalition count also yields equal candidate oracle masked-row count for a fixed background; it does not imply equal runtime. No significance stars or universal loss claim.

- **Grounding:** `final.evidence.episodes`, `final.metric.matched_budget_gain`.

### deployment_estimator_comparison

- **Purpose:** Retain a meaningful measured deployment comparator and expose budget- and fit-specific fidelity behavior.

- **Type/generator:** `grouped_dot` / `matplotlib`; required.

- **Mapping:** group by model_family; split by dataset and fitted_seed; metric: reference-fidelity quality reconstructed with the evaluator definition.

- **Footprint:** Four panels in a 2-by-2 grid over 5.5 inches keep three model categories and four estimator/budget series readable at a minimum of 8.5 points. Target about 2.8 inches plus caption on pages 7-8. Use short legend labels and a shared external legend rather than reducing font size.

- **Readability budget:** 4 panels total; at most 2 per row; 3 categories and 4 series per panel; final font ≥8.5 pt. No progression.

- **Content:** Four series: studied-64, studied-256, library-64, library-256. Average within retained input/background cells and candidate repeats, preserving the two fitted seeds in separate panels. Package calls have no estimated seed-to-seed variance. Reconstruct only deterministic summaries from stored vectors, verify candidate reductions against existing summaries, and record formulas and sources. Plot no fabricated error bars. Do not identify the library implementation with the original independent sampler; nominal coalition budgets need not imply identical prediction-row costs.

- **Grounding:** `final.evidence.episodes`.


Quantitative plots require plotting source plus PDF and 300-DPI PNG exports. Reference PDF from LaTeX whenever available. Raster-only fallback: regenerate at ≥2400 px for full width or ≥1200 px for column-only placement; never upscale. The overview is the only planned `generate-concept-figure` figure.

## Body-Page Budget

| Content | Page equivalents, including floats/captions |
|---|---:|
| Abstract and introduction | 1.15 |
| Related work | 0.65 |
| Estimand and experimental design | 1.30 |
| Sampling and allocation | 1.15 |
| Metrics, references, uncertainty | 1.05 |
| Empirical comparisons | 2.30 |
| Discussion and limitations | 0.85 |
| Conclusion | 0.25 |
| **Target** | **8.70** |

These are planning allocations, not empirical measurements. Keep the early overview near page 2 and quantitative comparisons near pages 5–8. Main Table 1 gives scope/estimand/design; Main Table 2 reports measured work with honest denominators and separated clocks. Spend available space on mathematical definitions, fixed-game assumptions, references and uncertainty, meaningful comparisons, and limitations. Do not pad to reach the budget; an 8-page alternative requires its final page to be ≥75% full. References and substantive supplement follow the body.

Suggested visible headings: Introduction; Related Work; Fixed-Game Reliability Question; Coalition Sampling and Budget Allocation; Metrics, References, and Uncertainty; Empirical Comparisons; Scope and Limitations; Conclusion. Dataset/reference settings are evidence blocks under one thesis, not chronological experiments.

## Supplementary Information After References

Provide substantive estimand, implementation, uncertainty, provenance, and reproduction detail after references without moving the negative allocation finding, reference limitations, or evidence-trust caveat out of the main paper.

### Fixed empirical games and implementation details

Document original-column players, probability-scale interventional masking, train-fitted preprocessing, kernel-size law, complement-pair coverage and rank-headroom formula, and identical constrained solver. Include source listings/precise pseudocode from staged implementations and the documented interface limits, not an invented package implementation equivalence. Pairing rank headroom is not a full-rank or accuracy guarantee.

**Grounding:** `final.evidence.episodes`.

### Data, fitted models, and reproduction manifest

Expand measured training/validation/selection row counts, validation accuracies, model hashes, final seeds, costs, and exact-reference counters from retained case records. Cross-reference task/evaluate_final.py, task/requirements.txt, and task/resources/final/manifest.json for public source versions, split rules, CPU environment, package versions, and exact model hyperparameters; these files are protocol evidence, not additional measured results. Preserve protected held-out-example restrictions and anonymous submission conventions.

**Grounding:** `final.evidence.episodes`.

### Metric definitions and descriptive uncertainty

Give the exact normalized L1 quality, top-three overlap/tie handling, rank and sign agreement definitions, efficiency residual, German fidelity-versus-gain reference distinction, equal-level aggregation, and existing 200-draw input-cluster intervals. Explain conditioning on each of two fits and the dependence of repeat pairs/backgrounds. Include retained budget/background-resolved tables and rank/sign summaries only as deterministic reconstructions from stored vectors, not new experiments.

**Grounding:** `final.evidence.episodes`, `final.metric.repeat_agreement`, `final.metric.reference_fidelity`, `final.metric.reference_resolution_quality`, `final.metric.local_accuracy_quality`, `final.metric.matched_budget_gain`.

### Reference sensitivity and measured computational work

Report both high-budget reference vectors and their disagreement, exact ACSIncome counters, library actual prediction rows and CPU seconds, and candidate observed wall durations/oracle masked-row totals. Show budget/background splits without conflating distinct empirical games; no reference convergence certificate, universal runtime benefit, or counterfactual CPU-hour measurement.

**Grounding:** `final.evidence.episodes`, `final.metric.reference_resolution_quality`.

### Selection provenance and evaluation scope

State frozen non-winner selection, original comparator search score and zero score difference, three scored and zero unscored attempts, independently completed/qualified final evaluation, unverified retained diagnostics, tree-digest/linkage limitations, and missing gate-level detail. Explain that search score was an evaluator-defined completion/control proxy rather than a reliability objective; keep its internal field names out of reader-facing prose. Retain controls/replay evidence as checks and exclude replay from scientific aggregates.

**Grounding:** `study.selection_kind`, `study.investigation_outcome`, `study.attempts.total`, `study.attempts.scored`, `study.attempts.unscored`, `study.baseline_score`, `study.search_score`, `study.search_score_delta`, `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`, `final.metric.control_pass_fraction`, `final.metric.coverage`, `final.evidence.episodes`.

### LLM Usage

Disclose the documented use of LLM assistance for research ideation, code preparation, reference planning, and framing/writing assistance. Distinguish candidate implementation from evaluator-owned observations, and do not invent human supervision, independent audits, or tools not documented. This section may follow the technical supplement under VENUE.md.

**Grounding:** `study.selection_kind`, `final.evidence.episodes`.


The local evaluator/manifest and staged implementations supplement the quantitative source registry as protocol evidence; they do not create new measured results. LLM-use disclosure is grounded in the documented task interaction, not inferred from scientific metrics. Keep the negative contrast, approximate-reference caveat, and unverified-diagnostics status in the main text. Later appendix-ranked analyses can supplement this plan without retroactive changes.

## Writer Instructions and Scientific Guardrails

1. This is strategy only. Do not create paper.tex or claims_grounding.json or run final-paper validation in this stage. The downstream writer must follow write-paper-standalone, grounding claims to exact registered sources and preserving qualification facts through review, audit, and revision.

2. Evidence ledger: final.metric.repeat_agreement=0.9458719135802469; final.metric.reference_fidelity=0.9289530659189914; final.metric.local_accuracy_quality=0.9999999999999954; final.metric.matched_budget_gain=-0.03883354541895445; final.metric.reference_resolution_quality=0.992225794670848. These are evaluator-defined descriptive qualities, not calibrated probabilities, statistical significance, or evidence of superiority.

3. The final.qualification.status/outcome/correct sources currently read completed/qualified/true. The study sources report no search winner, not failed final qualification. Gate-level diagnostics not supplied remain unknown. If later authoritative qualification changes to not_qualified, explicitly disclose it in main limitations and preserve all reported restrictions; attribute failure to performance, validity, or adaptivity only if evaluator diagnostics identify that cause.

4. Keep final.evidence.episodes candidate_diagnostics_trust=unverified explicit in the main experimental-evidence subsection and main limitations. Arithmetic reconciliation of retained vectors/aggregates is not an independent execution audit, gate explanation, or source-identity verification. The final scalar aggregates reconcile with six non-replay dataset/model cases per fit.

5. Study scope is German Credit with 20 original players and California 2024 ACSIncome with 10, logistic regression/random forest/gradient boosting, background sizes 8/32, nominal coalition budgets 64/256, six candidate repeats per cell, twelve explained inputs per fit/model, and fitted seeds 7301/9109. Protocol details are grounded in retained episodes plus local evaluator/manifest; do not substitute optional task-brief datasets, neural architectures, or unperformed background-resampling/training-uncertainty studies.

6. Define v_x,B(S) as mean positive-class probability under replacing absent original columns with fixed background rows. Keep the fitted model, explained input, and background fixed within a repeat comparison. Background sizes define different empirical games, not pure Monte Carlo replicas of one estimand. Neither exact enumeration of this game nor agreement with it establishes causal or conditional-expectation faithfulness.

7. Quality is 1/(1+L1(phi-reference)/max(1e-8,L1(reference))). Ordinary German fidelity averages quality against each of two high-budget references; German allocation gain uses their mean vector. ACSIncome uses exact coalition references. Reference agreement alone cannot certify convergence or expose shared reference bias. Near-zero reference norms and magnitude ties constrain interpretation.

8. The paired allocation contrast uses four additional low-budget runs and the first retained high-budget run, not whichever long run looks best and not the first four repeat vectors. It matches coalition counts and, for this candidate oracle at fixed background size, masked prediction rows; repeated endpoints and multi-call overhead still matter. Candidate durations are wall-clock observations; package counters are CPU seconds. Do not compare these clocks as identical.

9. Use existing case-level input-cluster intervals for pooled comparisons. Never treat repeat pairs or multiple backgrounds of one input as independent samples; never combine two fits into a population-level confidence claim. Any new budget-specific interval or statistical test would be a new analysis, not a stored result, and is not required by this strategy. Do not invent acceptability thresholds for single-run explanations.

10. Exclude the terminal deterministic replay from scientific sample sizes and means; retain it only for reproducibility/control reporting. The initial-seed episode includes that replay, while the other fitted-seed episode does not. Synthetic constant/copy/permutation and reset/replay checks are coarse functional checks, not a comprehensive validity or safety audit.

11. Main Table 1: experimental scope, fitted-model families, fixed-game definition, repeats, references, budget units, and seed handling. Main Table 2: measured work by method/budget/background with exact denominators and separated clocks; use existing counters and mark unavailable cells rather than estimating them. Neither table may claim the estimated 24 CPU-hour allowance was measured consumption.

12. Target an 8.7-page body within the VENUE.md 8-9-page requirement: abstract/introduction 1.15; related work 0.65; estimand/design 1.30; sampling/allocation 1.15; metrics/references/uncertainty 1.05; results 2.30; discussion/limitations 0.85; conclusion 0.25. These allocations include figures, captions, and tables, not additional pages. If an 8-page body is used, its last page must be at least 75% full. Use space for estimand clarity, reference limitations, cost comparisons and source caveats, never narrative padding.

13. Suggested thesis-first headings: Introduction; Related Work; Fixed-Game Reliability Question; Coalition Sampling and Budget Allocation; Metrics, References, and Uncertainty; Empirical Comparisons; Scope and Limitations; Conclusion. Organize results by agreement versus fidelity, allocation, and estimator/cost comparison, not task chronology. One shared thesis has condition-specific exact/approximate-reference evidence blocks.

14. The actual selected ICLR style has a 5.5-inch (about 397.5-point) text width and 9-inch text height. It is single-column: column-width and full-text-width coincide. All required figures use preferred_span=full_width and width fraction 1.0 of text width, not paper width or a fictitious two-column 0.48 span. Preserve anonymity and the supplied style; do not switch to the task scaffold NeurIPS template or assert the historical header alone verifies official-current-template provenance.

15. Use at most one generate-concept-figure diagram, editable and deterministic, without embedding invented measurements. Quantitative figures must have reproducible plotting sources and both PDF and PNG exports at 300 DPI. LaTeX references PDF whenever available. A raster-only full-width fallback must be regenerated at least 2400 pixels wide; column-only fallback at least 1200 pixels wide. Never upscale an existing raster. Keep final labels at least 8.5 points (9 for the overview), and simplify/split rather than shrink dense panels.

16. Only cite existing, actually consulted, safely screened references. Exact starter matches presently include Lundberg2017AUA and Musco2024ProvablyAS. The bibliography also contains broad-query noise; inclusion in it does not authorize access, citation, or novelty claims. Do not inspect unapproved surveys, citation chains, related-paper lists, or the prohibited prior study; no external retrieval was performed in this framing stage. Describe an empirical audit contribution without claiming priority or exhaustive literature coverage.

17. Do not create component-isolation ablations, estimator tournaments, architectural transfers, causal diagnoses of the negative allocation result, new datasets, or reliability certificates. The search-only conditioning and alias variants are unnecessary narrative baggage; substantive available protocol and retained rank/sign/cost details belong after references. A later authoritative analysis ranking may add appendix analyses without retroactively changing this strategy.

18. Reader-facing prose may describe the frozen configuration, original comparator, final measured audit, and evaluator-reported completion requirements. Internal field names in this JSON and source identifiers are private-only provenance, not visible manuscript terminology. Publication readiness is not scientific qualification, and scientific qualification is not high-risk deployment approval.


## Diary and Overclaiming Traps

**Forbidden headings:** Search Progression; Campaign Phases; Milestones; First Valid Result; First Success; Iteration Timeline; Experiment A; Experiment B; Winning Configuration; From Failure to Success.

**Forbidden visible phrases:** “we then tried”; “subsequent improvements”; “first valid result”; “next-best”; “later variants”; “the winning sampler”; “state-of-the-art reliability”; “correctness rate”; “correct and eligible”; “eligible”; “combined_score”; “rubric”; “worker_01”; “worker_02”; “94.6% of explanations are reliable”; “negative matched-budget gain proves the sampler loses to the original baseline”; “exact efficiency proves attribution accuracy”; “the final evaluation failed because search found no winner”.

Internal identifiers and forbidden wording shown in this private memo are not recommendations for visible manuscript prose. No plot uses a thresholded success label: no acceptability threshold was established. If one is later justified, preserve one reader-facing meaning per figure and do not turn a descriptive quality into a qualification rate.

## Completion Boundary

The standalone framing is supportable as a narrow empirical audit with a negative allocation result and explicit evidentiary limits. This does not guarantee conference acceptance, scientific novelty, or deployment reliability. No final paper, claim map, figure, new experiment, external retrieval, or final-paper validation is produced in this stage. Failure reason: none.
