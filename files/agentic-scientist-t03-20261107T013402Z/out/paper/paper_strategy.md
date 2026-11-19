# Paper Strategy: Fixed-Game SHAP Reliability

## Decision

**Status: ready.** Use the `paper_standalone` family and `write-paper-standalone` skill for a thesis-first ICLR 2026 study. Provisional title: **Fixed-Game SHAP Reliability: Structure, Budgets, and Reference Limits**.

**Central question.** For frozen tabular classifiers and a fixed empirical probability-scale Shapley game, how do sampled and structure-aware computations compare in single-call reference agreement and repeated-call consistency under finite coalition caps, and what reliability claims remain unsupported?

**Central thesis.** On the evaluated German Credit and ACS income conditions, structure-aware forest attribution and probability-scale logistic integration yield perfectly consistent observed repeated-call top-three sets and signs and high reference agreement, but reference uncertainty, restricted game semantics, and unequal computational access prevent interpreting these results as general deployment reliability or equal-time superiority.

This is one shared scientific question with dataset/model-specific adaptations, not separate chronological experiments. The contribution is a bounded computational-reliability comparison and its interpretive limits, not a first-ever exact-tree algorithm, universal reliability theorem, or deployment certification.

## Evidence and Qualification

Read final evaluation independently of search and of any proposed downstream-study narrative. Here `paper_data.json.downstream_study` and `study.*` sources are absent. The final qualification sources report:

| Grounding source | Reported value |
| --- | --- |
| `final.qualification.status` | `completed` |
| `final.qualification.outcome` | `qualified` |
| `final.qualification.correct` | `true` |

No failed final qualification is reported in this run. This outcome concerns the documented evaluation checks, not proof that explanations are valid reasons for high-risk decisions. Preserve the distinction in writing, review, audit, and revision. If later authoritative evidence reports failure, disclose it and retain its limitations; do not classify its cause as performance, validity, or adaptivity without evaluator diagnostics.

Main numerical evidence comes from `final.evidence.episodes`. Final aggregates include reference agreement **0.9975639445869278**, reference top-three overlap **1.0**, and all-coordinate sign agreement **0.9997395833333332**, grounded in their corresponding `final.metric.*` sources. Candidate repeat-pair top-three and sign agreement are **1.0** throughout the retained final empirical observations. These are separate findings, not one undifferentiated reliability score. Controls, efficiency, failed-call fraction and replay are narrow checks.

The final wall total, **700.3707705293782 seconds**, covers the evaluation workload, including references and comparators; it is not per-explanation latency or a candidate-only runtime. The source brief's CPU-hour estimate is not measured usage.

### What is actually evaluated

- German Credit and **ACSIncome-2024-RELSHIPP**, each with logistic regression and random forests: four conditions under one thesis.
- Final episode seeds: **104729, 130363, 155921**; coalition caps **64, 256, 1024**; **six** candidate calls per cap; **16** fixed query instances and **16** fixed training-background rows per condition.
- German has **20** scalar feature groups and retained final splits **300/100/100** for training/validation/explanation. ACS has **10** groups and **20000/6667/6667**. Split counts are inspected resource provenance, not generalization measurements.
- Preprocessing is training-fitted ordinal categorical encoding, numeric median imputation, and standardization of supplied original groups. This is not arbitrary raw-data masking or a one-hot-grouping experiment.
- Logistic regression uses `lbfgs`, `max_iter=500`, `tol=1e-7`; forests have **64** trees, maximum depth **6**, and `n_jobs=1`.
- ACS references enumerate the finite **10**-feature game. German references average two **4096**-coalition library estimates; their half-difference is a recorded disagreement proxy, not a confidence interval or exact ground truth.

These settings are traceable to the final episode arrays, `task/evaluate_final.py`, and `task/resources/final/`. The ACS relationship-field adapter and search/final predictor-content separation must remain explicit. Do not call the adapted task bit-identical historical ACSIncome.

## Framing Choice and Alternatives

**Story status: recentered.** There is no prior manuscript, edit-context file, `previous_paper/`, `aggregated/`, or `extra_tasks/` directory. This decision narrows the broad source-task motivation rather than modifying an unseen prior paper.

| Candidate story | Decision and grounded reason |
| --- | --- |
| Preserve the broad claim about reliable reasons in high-risk deployment | Reject: no human decision evidence, causal validation, conditional-game study, or background-shift evaluation. |
| Shared fixed-game computation across model families | Select: both forest and logistic conditions have measured comparators and reference evidence, with inspectable component changes. |
| Recenter solely on logistic quadrature | Reject as primary: discards useful forest evidence; no recorded branch coverage or total quadrature-error certificate supports making quadrature alone the whole claim. |
| Center single-call confidence certificates | Reject: certificate decisions and acceptance coverage were not persisted; implementation presence is not measured utility. |
| Narrate the selected search result | Reject: discovery order and selection scores do not answer the scientific question or establish final performance. |

The recoverable full implementation is under `results/ideas/03_probability_scale_logistic_shap_by_bounded_fourier_quadrature/program_1/src/`. The best-program manifest links this configuration to the final-tested method at selection/path level; the final program-tree digest is recorded but has not independently been matched to a recovered byte-identical final snapshot in this stage. Describe source-grounded mechanisms and evidence-grounded behavior separately.

Private-only selection context must not leak into manuscript labels. Without `study.*`, do not manufacture a frozen-study selection contract, publish search score differences or attempt totals, or use the memory-only original-incumbent score as a comparison. The stored library comparators remain valid measured baselines.

## Methods Worth Including

1. **One-shot library Kernel SHAP — baseline.** Same model, empirical background, queries, identity link and nominal cap; `l1_reg=0.0`.
2. **Two-start split-cap Kernel SHAP — baseline.** Average two independent half-cap estimates. Explain that endpoint overhead and actual prediction rows need not match one-shot cost.
3. **Structure-aware fixed-game computation — proposed family.** Exact forest leaf-literal algebra and probability-scale logistic Fourier/Owen integration, with exhaustive nonforest dispatch when all subsets fit and the existing sampled fallback on numerical rejection. Explain the common estimand before model-specific computations.
4. **Sampled path/regression configuration — development ablation.** Compared with the forest-enabled configuration on forest conditions; not the untouched original incumbent.
5. **Forest-enabled, sampled-logistic configuration — development ablation.** Compared with the full family on logistic conditions; unchanged forest behavior checks component locality.
6. **Same-game references and analytic controls — supporting evidence.** Exhaustive ACS, approximate German, zero/affine/permutation controls, and reset/replay. Do not count them as extra public datasets or as full nonlinear validation.

Inspection of `reliability.py` confirms that the forest comparison adds its import/dispatch and the logistic comparison adds its import/dispatch. Stored matched development episodes support direct component contrasts at seeds **1729/2718** and caps **64/256**. Label these comparisons development data throughout; they are neither final holdout ablations nor independent confirmations. Complete tables may go in the supplement, but the main component comparison must remain visible.

Do not expand the paper into unmeasured neural models, background resampling, alternative certificates, leverage-score methods, external TreeSHAP implementations, or additional datasets. Relevant literature methods may be context, not measured baselines.

## Results Organization and Statistical Meaning

### Main final comparison

Compare three methods at each cap in each dataset/model condition. Use normalized L1 **reference agreement**:

`1 / (1 + ||phi - phi_ref||_1 / max(||phi_ref||_1, 0.001))`.

Show individual episode markers rather than invented per-cap confidence bands. Preserve the distinction between approximate German and exhaustive ACS references. High-cap ACS one-shot computation can close the gap; split-cap averaging has particularly poor German agreement at cap 64. Report these negative and boundary results without an unsupported diagnosis such as regression rank failure.

### Distinct reliability assessments

- Reference top-three overlap uses absolute values and original-column tie breaking.
- Reference sign agreement covers **all coordinates**, with absolute zero tolerance **1e-8**; it is not signed-top-three accuracy.
- Repeated-call top-three and sign agreement compare candidate outputs on the same fixed game. Baseline outputs do not include six within-model repetitions, so a matching baseline repeatability comparison is unavailable.
- Normalized efficiency residual uses a **0.001** denominator floor and is capped at one. It is not reference fidelity.

Existing case-level 95% bootstrap intervals first average candidate agreement over repetitions and caps and then resample **16 instances**, using **1000** bootstrap draws and seed **84017**. They condition on a fitted model and its reference; they are not per-cap intervals and omit reference-estimation uncertainty. Do not average interval endpoints into a new interval. The same instances recur across episodes, and fitted forests may differ with seeds; neither repeated calls nor overlapping episode samples create independent people. Near-degenerate intervals from deterministic outputs do not imply negligible deployment uncertainty.

### Limits required beside the main results

Residual German differences cannot be assigned solely to reference noise or solely to candidate error. Deterministic outputs cannot establish the active internal branch. Nonforest exhaustive dispatch occurs at cap `>= 2^d - 2`; ACS logistic cap 1024 is therefore not evidence of the quadrature branch. Internal certificate acceptance/rejection, quadrature rejection frequency, candidate per-call runtime, and total discretization-error guarantees are unavailable.

The proposed family has model-parameter access; library methods use prediction queries. A nominal sampled-coalition cap does not equate arithmetic work, information access, or wall time. Do not claim equal-time superiority. The quadrature's analytic frequency-tail bound does not bound all discretization error; refinement agreement and efficiency are numerical diagnostics. Independent validation scripts are present but their preparation records say they were not run. Their presence cannot become a validation result.

No acceptable-error or user-decision reliability threshold was prespecified. State that one call meets the **observed same-game criteria in these retained conditions**, not that a universal trustworthy-explanation threshold was established.

## Figure Specifications and Layout

The inspected ICLR template uses `article` and `paper,times`; `paper.sty` sets **5.5 inches text width**, **9 inches text height**, and a **single-column** layout. Full width means that one text column, not a two-column float. Half-width placement is not appropriate for the required composites.

### Figure 1 — `fixed_game_overview`

- **Required; diagram; generator `generate-concept-figure`.** Early placement on page 1 or 2.
- One panel with at most six concise blocks: fixed game, sampled computation, structure-aware computation, repeat consistency, reference agreement, and scope boundary. Explain details in the caption rather than adding microtext.
- Full **5.5-inch** width, approximately **1.6–1.8 inches** high plus caption; intended footprint about **0.23 page**. At least **9-point** final-size text.
- Budget: **1 panel**, **1 per row**, **6 main categories/blocks**, **2 computational branches**. No invented numeric annotations or causal/deployment guarantees.
- Grounding: `final.evidence.episodes` plus the inspected estimator source. This is an evidence map, not a claim that a confidence certificate was observed.
- Use the orchestrator-owned editable draw.io concept-figure workflow later; do not run it during strategy planning. At most this one overview uses that generator.

### Figure 2 — `final_reference_comparison`

- **Required; grouped categorical dot plot; matplotlib.** Four dataset/model panels in a **2x2** arrangement.
- Three cap categories and three method series per panel; per-episode points, one shared legend, explicit exhaustive/approximate reference labels. A common **0–1** agreement scale keeps the low split-cap outcomes visible; communicate near-ceiling differences through concise values or the companion table, not a hidden truncated scale.
- Full **5.5-inch** width, approximately **3.5–4 inches** high plus caption; footprint about **0.48 page**. Roughly **2.6 inches** per panel supports short cap labels and at least **9-point** text.
- Budget: **4 panels**, **2 per row**, **3 categories**, **3 series**. No search-order lines or per-cap error bars borrowed from budget-pooled intervals.
- Grounding: `final.evidence.episodes`, `final.metric.reference_fidelity`.

### Figure 3 — `component_comparison`

- **Required; paired categorical dot comparison; matplotlib.** Two panels: forest component and logistic component.
- Four dataset/cap categories per panel, two compared configurations, and the two matched development episode points. Show the relevant disabled/enabled contrast rather than all configurations in an ordered sequence.
- Full **5.5-inch** width, approximately **2.2–2.5 inches** high plus caption; footprint about **0.32 page**. Short labels and at least **9-point** text are required; simplify instead of shrinking.
- Budget: **2 panels**, **2 per row**, **4 categories**, **2 series**. Explicitly mark development data. No campaign progression, ranking, or final-set ablation claim.
- Private grounding bridge: `result.top_program_03` identifies sampled-only, `result.top_program_02` forest-enabled, and `result.top_program_01` full computation. Use their actual `all_programs[*].evaluation_evidence.episodes` arrays and inspected source changes, not the scalar selection scores, as evidence for the plotted component contrasts.

### Export and consistency contract

Quantitative figures must retain source/data and export **PDF plus PNG**, PNG at **300 DPI**. LaTeX must use the PDF whenever available. For raster-only full-width assets, regenerate at **at least 2400 pixels wide**; column/partial-width raster assets require **at least 1200 pixels**. Never upscale an existing raster. The concept workflow does not itself promise a PDF: prefer one exported from its editable vector source when available, otherwise meet the raster minimum and preserve the prompt/source manifest.

Use gray for one-shot library, orange for split-cap averaging, and blue for structure-aware computation. Component plots may use gray/blue for the explicitly labeled disabled/enabled contrast. Keep reference quality as text labels, not a remapping of method colors. No trajectory figures are warranted.

## Body Budget and Reader Value

Target **8.5 body pages** under the supplied **8–9-page** brief. Figures and tables are already included in these allocations:

| Material | Planned pages |
| --- | ---: |
| Introduction and early overview | 1.25 |
| Related work | 0.65 |
| Fixed-game estimand and metrics | 1.00 |
| Model-specific computation | 1.40 |
| Experimental and statistical protocol | 1.05 |
| Results and component comparison | 2.00 |
| Limitations and interpretation | 0.90 |
| Conclusion | 0.25 |

Keep two compact main tables: experimental geometry and condition-specific final reliability. The latter can present the existing conditional intervals at their true scope, alongside separate repeat consistency, reference top-three/sign agreement, and a nearby integrity-check paragraph. Do not force all diagnostics into an unreadable table.

Spend available space on the common game definition, the nonlinear probability-scale mechanism, independent meaning of metrics, reference limitations, and fair-compute discussion. Do not pad with method history, oversized graphics, redundant tables, untested possibilities, or search scores. If ending at eight pages, its last page must be at least 75% filled; do not alter margins or shrink type to manipulate this. The supplied template's sample final-copy author block is not suitable for double-blind submission.

## Supplementary Information After References

Flush main floats, place references, then clear the page, enter appendix mode, and add **Supplementary Information**. The following substantive sections use available evidence; they do not require new experiments or guessed posthoc rankings:

1. **Fixed-Game Definition and Preprocessing.** Expand the estimand, original-group representation, training-only preprocessing, exact data/split provenance and ACS adapter. Sources: `final.evidence.episodes` with inspected `task/evaluate_final.py` and final resource records.
2. **Structure-Aware Computation and Numerical Safeguards.** Include leaf inclusion/exclusion coefficients, repeated splits and float semantics, Fourier/Owen integration, inclusion quadrature, frequency-tail versus discretization distinction, dispatch and fallback. Sources: `final.evidence.episodes`, `result.top_program_01`, and the recoverable estimator files; label unrun validation scripts accurately.
3. **Episode-Level Reliability and Reference Uncertainty.** Complete per-case/cap/episode tables, stored bootstrap intervals at their actual scope, reference half-differences, model diagnostics, controls and replay. Sources: `final.evidence.episodes` and `final.metric.efficiency_error`, `final.metric.control_pass_rate`, `final.metric.replay_error`, `final.metric.failed_fraction`.
4. **Component Comparison Details.** Full development comparison tables, source dispatch differences, unchanged-family checks, and recorded regressions/nonmonotone cap behavior. Sources: `result.top_program_01`, `result.top_program_02`, `result.top_program_03` followed to their episode arrays. No selection-score narrative or final-confirmation claim.
5. **Reproducibility and Compute Accounting.** Dependencies, program specifications, seeds, offline data acquisition/provenance, hashes, commands, measured timing scopes, and exact figure/table script mapping once implemented. Sources: `final.evidence.episodes`, `final.metric.wall_seconds`, and the three final qualification sources, with inspected local specifications/resources. No identifying internal paths in the anonymous submission.

Add a separate **LLM Usage** section, preferably after these appendix subsections, describing documented ideation, code-preparation, framing and writing roles precisely. Do not invent model identifiers, human verification, or independent execution. Follow later authoritative appendix rankings without retroactively rewriting this strategy; never move essential final evidence or decisive limitations out of the body.

## Literature, Access, and Disclosure Boundaries

The existing bibliography is a noisy retrieved candidate pool with metadata-level provenance. It is not evidence that every source was read. Start only with relevant permitted primary records such as `Lundberg2017AUA`, `Musco2024ProvablyAS`, and appropriate tree-attribution records after actual source verification. Do not use irrelevant retrievals as citation padding, invent missing Owen/empirical-Bernstein/semantic references, or claim unverified theoretical novelty. Nonessential certificate theory should not carry the central thesis.

No external paper pages were accessed in this strategy stage and no prohibited encounter was identified here. This does not certify earlier retrieval as reviewed or contamination-free. Do not attempt to identify the prohibited study or conduct broad rerun-reliability discovery. Stop and record any actual forbidden encounter, including where it occurred and how much was read.

## Anti-Diary and Overclaim Guardrails

Avoid headings **Search Progression**, **Campaign Phases**, **Milestones**, **First Valid Result**, **Iteration History**, **Experiment A / Experiment B**, **Winning Configuration**, and **Successive Improvements**.

Forbidden visible wording includes “we then tried,” “subsequent improvements,” “first valid result,” “next-best,” “later variants,” and the internal labels listed in the JSON contract. Also avoid “state of the art,” “certified reliable explanations,” “repeatability proves validity,” “exact German ground truth,” “equal-time superiority,” and “safe high-risk deployment.” Private-only source identifiers in this memo are not recommended manuscript terminology.

Never turn unscored or unrun alternatives into measured losses. Never invent significance, certificate coverage, quadrature branch counts, candidate latency, robustness studies, additional datasets or external-baseline experiments. Retain the fixed small query set, fixed background, scalar encoding, approximate German reference, missing branch diagnostics, and absent human/causal/background-shift validation in the main limitations.

This stage produces strategy only: no `paper.tex`, no `claims_grounding.json`, no final-paper validation, and no claim of submission readiness or verified official-template provenance merely from inspecting the supplied local style.
