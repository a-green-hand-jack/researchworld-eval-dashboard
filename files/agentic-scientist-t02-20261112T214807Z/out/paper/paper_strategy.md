# Paper framing strategy

## Decision and provisional title

**Status: ready for a bounded standalone paper plan, not scientifically qualified.**
**Title:** Width and Delayed Generalization in Finite-Horizon Modular Addition.
**Format:** `paper_standalone`, using `write-paper-standalone`; ICLR 2026, anonymous, 8–9 body pages excluding references.

**Central question.** How does hidden width relate to the separation between training-set fitting and held-out generalization in a fixed modular-addition network under finite training horizons and matched regularization controls?

**Central thesis.** The retained comparisons show earlier fitting at larger widths without monotone short-horizon generalization, while two longer-horizon width-128 delayed events remain conditional observations rather than qualified evidence of a size law or a decay-clock mechanism.

Final evaluation **completed but did not qualify**. Ground this in `final.qualification.status`, `final.qualification.outcome`, and `final.qualification.correct`, independently of selection results. The precise failing diagnostics remain unknown. Missing records and limited coverage are observable limitations, not proof of the particular cause of non-qualification. Do not relabel the outcome as either inferiority or a protocol/adaptivity defect. Preserve this disclosure in writing, review, audit, and revision. Publication-format readiness does not upgrade scientific qualification.

## Why this story wins

The strongest object is one empirical width study with condition-specific evidence blocks, not a new optimization algorithm. The fixed architecture and actual controls permit a concrete separation of fitting behavior, held-out performance, and observability. This supports a substantive negative/conditional paper without requiring a positive search result.

There is no prior manuscript or enabled edit context, and no `previous_paper/`, `aggregated/`, or `extra_tasks/` input. The contract value `prior_paper_story_status: rejected` rejects the inherited untested mechanism framing; it does not imply that a prior manuscript exists. Inspection of the selected controller and local evaluator confirms a fixed architecture, not an architectural innovation. Current final records, not older memory, determine the thesis.

Candidate framings considered:

| Candidate | Decision | Evidence-based reason |
|---|---|---|
| Preserve a post-fit decay-clock story | Reject | The proposed positive-decay grid and clock-collapse test were not executed; no mechanism is identified. |
| Broaden to a universal size or shared mechanism claim | Reject | Only modulo-97 addition and one architecture are measured; final width-256 records are absent. |
| Recenter on the latest faster-optimizer setting | Reject | It is incomplete and cannot isolate effective regularization or support final superiority. Recency is not evidence strength. |
| Conditional width, fitting, and finite-horizon generalization study | Select | Direct width/arm/seed records, two retained delayed events, and explicit censored/missing outcomes support one coherent question. |

The absence of `downstream_study` and `study.*` sources prevents importing campaign selection margins, scored/unscored counts, or a campaign baseline comparison. Use the configuration explicitly present in final records. Retain the measured fixed-reference arm; do not use an unavailable baseline score as a scientific comparison.

## Scientific object and method groups

The measured task is ordered-pair addition modulo 97. The architecture has two learned input embeddings, their sum plus hidden bias, GELU, and a linear 97-class output. Hidden widths are 32, 128, and 256; parameter count is `292w+97`. Training is full-batch float32 cross-entropy with AdamW, including decay on biases.

Only four groups belong in the main comparison:

1. **Studied common configuration:** learning rate 0.003, weight decay 1.0, initialization multiplier 0.5 across widths. This is a configuration, not a claimed new method.
2. **Fixed reference:** learning rate 0.001, weight decay 1.0, initialization multiplier 1.0. It is paired by width/seed/split/horizon but changes two hyperparameters, so it cannot isolate initialization.
3. **Zero-decay control:** same studied configuration except zero weight decay. Interpret only within the measured horizon and retained pairs.
4. **Matched-initial-global-norm control:** globally rescale parameters to the same-seed width-128 initial norm. This does not match capacity, functions, or effective regularization. At width 128 it duplicates the studied arm, including retained initial/final hashes and scientific metric trajectories; do not count it as independent replication.

The alternate initialization and faster-update configurations are supplementary sensitivity records, not obligatory narrative branches. Do not invent random-label, frozen-feature, circuit, or architecture controls.

**Falsifiable explanation, explicitly still a hypothesis:** width may alter training-fit speed separately from the process governing held-out generalization; decay and initialization may condition that separation. Earlier fitting without prompt generalization is compatible with the explanation, but the current evidence does not identify a norm-mediated mechanism, clock collapse, or a universal size relationship. Do not call these predictions preregistered.

## Evidence and results views

### Keep the evidence blocks separate

The short-horizon studied-configuration records use 6000 updates, seeds 101/211, and a 4704-pair pool. Final records use 24000 updates, seeds 60613/70717/80821, and a disjoint 4705-pair pool. Seeded training fractions are 0.6 within each pool: train/evaluation counts are 2822/1882 and 2823/1882 respectively. Horizon, pool, and seed set change together. Therefore this is not a controlled horizon-extension experiment, and it cannot establish that longer training caused a width-ranking reversal.

**Private-only source map:** the short-horizon raw observations are `paper_data.json` at `/best_correct/evaluation_evidence/episodes`, also `/all_programs/1/evaluation_evidence/episodes`. Final observations are at `/final_evaluation/evaluation_evidence/episodes`, bound by `final.evidence.episodes`. The selection-summary IDs `result.top_program_01` and `result.best_correct_score` are not substitutes for raw curve grounding. Candidate diagnostics are marked unverified; do not transform that metadata into validity certification.

### Main-text evidence coverage is mandatory

Each retained width-seed record contains all four arms. The table below describes the **studied arm**, not four independent repetitions:

| Final seed | Width 32 | Width 128 | Width 256 |
|---|---|---|---|
| 60613 | recorded, held-out onset censored | recorded delayed event | missing |
| 70717 | recorded, held-out onset censored | recorded delayed event | missing |
| 80821 | recorded, held-out onset censored | missing | missing |

There are five recorded cells out of nine planned, with two recorded delayed events. Missing cells are neither observed failures to generalize nor right-censored training curves. All final paired-contrast summaries are null. The intended 256-minus-32 final width contrast and its interactions are unidentified; a descriptive 128-minus-32 comparison must not impersonate it.

### Direct scientific comparisons

- **Fitting versus endpoint performance:** the studied short-horizon width-32 records have higher held-out endpoint accuracy than widths 128 and 256, although larger widths fit earlier. This is a measured finite-horizon pattern, not an inverse-size law.
- **Delayed events:** the two retained final width-128 records have training-fit/held-out-onset steps 300/17600 and 200/19200. The three width-32 records fit at 2600, 2400, and 3000, but have no held-out onset by 24000.
- **Controls:** retained final fixed-reference and zero-decay arms have no sustained held-out onset. The width-128 norm control reproduces the studied arm by construction. Show arm endpoints directly; neither this identity nor a norm trajectory proves mediation.
- **Uncertainty:** show every seed, use genuine within-seed pairs, and keep selection versus final cohorts distinct. Two or three seeds do not support robust population claims. Checkpoints and examples are not experimental replicates. Any downstream interval must be reproducibly derived from actual records and labeled conditional on availability and exploratory; do not promise significance or equivalence.

The evaluator defines fitting at training accuracy at least 0.99 and held-out onset at accuracy at least 0.95, each sustained for three checkpoints spaced 100 updates apart. Onset is the first checkpoint of that triple. A delayed event requires an onset separation of at least 1000 updates. Keep these three meanings distinct. A normalized capped delay of one is a reporting convention when an onset is missing, not a measured delay equal to the horizon.

**Private-only aggregate caution:** `final.metric.grokking_incidence` is 0.2222222222222222 under nine-cell design weighting; `final.metric.mean_final_accuracy` is 0.48813319164009916 with missing/failure weighting; `final.metric.restricted_mean_delay` is 0.9458333333333333 under the capped convention. These are not an unbiased event probability, the mean accuracy of five recorded runs, or a mean observed event time. Keep them out of headline plots. If an audit table retains them, explain the aggregation, rather than plotting absent records as measured zeros.

## Required figures and layout

The inspected `paper.sty` defines **one column, 5.5 inches of text width and 9 inches of text height**. There is no two-column conference layout: full-width means the full single column; do not use a two-column `figure*` assumption. Each required figure should use the full text width because reducing any of the composites to half width would reduce label readability. The supplied style's age comments do not independently establish current official-template provenance; verify that separately before final submission without shrinking the layout to fit.

| Figure | Content and intended placement | Size and readability budget |
|---|---|---|
| `study_overview` | Page 1 or 2: fixed network, width/arm design, and observed-event/censored/missing states. Use `generate-concept-figure` downstream; no speculative mechanism arrows. | Full width, about 5.5 × 1.5 in; about 0.22 body page including caption. At most 2 panels, 2 per row, 4 categories, 4 series; minimum final text 8.5 pt. |
| `width_endpoint_comparison` | Direct seed-dot comparison of endpoint held-out accuracy across widths and the four arms. Separate short-horizon and final panels; shared accuracy scale and explicit missing cells. | Full width, about 5.5 × 2.4 in; about 0.34 body page including caption. At most 2 panels, 2 per row, 3 width categories, 4 arm series; minimum text 8.5 pt. |
| `fit_and_generalization_onsets` | Direct event-time comparison for the studied configuration: fit and held-out onset by width/seed, with censor arrows only for observed trajectories. Separate 6000- and 24000-update panels. | Full width, about 5.5 × 2.3 in; about 0.32 body page including caption. At most 2 panels, 2 per row, 3 width categories, 2 marker series; minimum text 8.5 pt. |

The third figure addresses dynamics through event times rather than a chronology plot. No training-curve figure is required because the direct onset view supplies the core separation with less visual density. Keep the coverage table in the main text. Keep a single four-arm palette; identify seeds through small fixed offsets or annotations, not additional colors that exceed the series budget. Mark the norm-control identity rather than treating coincident points as independent confirmations.

Use matplotlib for quantitative figures and retain their generation scripts. Export **PDF plus 300-DPI PNG**, and reference the PDF from LaTeX whenever available. The concept figure must retain editable draw.io source; use a genuine vector PDF if available, otherwise regenerate its raster output at least 2400 pixels wide. Any other raster-only full-width/column-width figure must be at least 2400/1200 pixels wide. Never upscale. Exactly one overview uses `generate-concept-figure`; its downstream orchestration and marker must not be bypassed. No figures are generated at this stage.

## Body-page budget and thesis-first structure

Target approximately **8.8 body pages**, with figure/caption footprints included:

| Material | Pages | Scientific value |
|---|---:|---|
| Title, abstract, introduction, early overview | 1.50 | Define width versus fitting/generalization; state conditional contribution and failed final qualification. |
| Related work | 0.75 | Distinguish permitted norm, circuit, and lazy-to-rich explanations from actual measurements and different architectures. |
| Model, interventions, event estimands, design | 2.00 | Explain paired initialization, arm confounds, data partitions, thresholds, censoring, and the intended width contrast. |
| Results and evidence coverage | 2.80 | Two quantitative figures, coverage table, seed-resolved comparisons, controls, and absence of the planned final contrast. |
| Discussion, uncertainty, identification limits, limitations | 1.45 | Separate descriptive support from mechanistic non-identification; analyze finite follow-up, missingness, and cohort confounding. |
| Conclusion | 0.30 | State the narrow empirical takeaway and unresolved width/decay questions without upgrading qualification. |

If the body ends at 8 pages, the final page must be at least 75% full. Do not pad or repeat caveats merely to meet length. Use additional space for exact definitions, controlled-comparison logic, seed-level evidence, and sharpened limits, not extra weak claims. Recommended headings: Introduction; Related Work; Width Comparisons and Event Definitions; Experimental Design and Evidence Coverage; Width-Dependent Fitting and Held-Out Accuracy; Delayed Events and Matched Controls; Discussion and Limitations; Conclusion. These are scientific organization units, not experiment chronology.

## Supplementary Information after references

Insert a page break after the body, references, then a new page and **Supplementary Information**. Main-text qualification failure, missingness, and central comparisons stay in the body.

1. **Exact model, data partition, and intervention definitions.** Extend architecture, coupled initialization, parameter counts, train/evaluation splits, norm rescaling, and optimizer semantics from the local task/resource policies. Measured-source anchor: `final.evidence.episodes`; code paths are method provenance, not newly invented source IDs.
2. **Complete per-seed comparison records.** All final arm endpoints, events, censor flags, updates, state hashes, and missing cells; limited global-norm readouts where actually recorded. Highlight the width-128 identity. Source: `final.evidence.episodes`.
3. **Selection sensitivity and incomplete alternate settings.** Organize initialization and faster-update sensitivity by condition, never by iteration. Raw observations are at `/all_programs/0`, `/all_programs/1`, and `/all_programs/2` under `evaluation_evidence/episodes`. Selection-summary anchors `result.top_program_01` and `result.top_program_02` do not stand in for those raw observations. Retain incomplete faster-setting evidence without diagnosing an unreported failure cause or counting its missing record as a measured loss.
4. **Censoring, uncertainty, and evaluation limitations.** Exact onset/capped-delay rules, all seed values, aggregate failure weighting, unavailable final contrasts, failed qualification, and unknown diagnostics. Sources: `final.evidence.episodes`, `final.qualification.*`, and the applicable `final.metric.*` IDs listed in the JSON. Do not present a tiny-sample interval as mechanistic validation.
5. **Reproducibility and LLM Usage.** Actual dependencies, CPU settings, seeds, hashes, supplied code, and downstream figure/table script mappings and commands once implemented. Runtime claims must come from recorded timings, not resource-budget projections. Disclose documented LLM roles precisely; do not claim unrecorded training or literature consultation. Keep the required LLM Usage section separate and preserve anonymity.

Route authoritative later appendix-ranked analyses to the supplement without modifying this strategy retroactively. Do not guess such rankings now.

## Literature, language, and audit guardrails

The bibliography/provenance contain retrieval metadata, not evidence that originals were read. Restrict downstream consultation and citation to exact user-authorized starter originals after identity checks. Prioritize Power for the phenomenon, Loshchilov/Hutter for AdamW, Liu for norm hypotheses; use allowed Kumar, Varma, Nanda, Davies, or Nakkiran originals only when they add a necessary comparator. No browsing is needed for strategy generation. Do not inspect neighboring hits, citation networks, or try to identify the prohibited work. Do not invent an accidental-encounter report.

Avoid headings such as **Search Progression**, **Campaign Phases**, **Milestones**, **First Successful Run**, **Experiment A / Experiment B**, **Cycle 1 / Cycle 2 / Cycle 3**, **From Baseline to Winner**, **A Universal Width Scaling Law**, **Proof of the Decay Clock**, and **Validated Superiority**.

Avoid diary phrases: “we then tried,” “subsequent improvements,” “first valid result,” “next-best,” and “later variants.” Avoid unsupported scientific wording: “search winner proves,” “larger models always grok faster,” “weight decay is necessary for grokking,” “initial norm explains width effects,” “longer training caused the ranking reversal,” “zero incidence means grokking is absent,” “missing runs failed to generalize,” “final failure proves inferiority,” “final failure proves a protocol defect,” “statistically significant,” and “state of the art.”

**Private-only visible-language blacklist:** `eligible`, `correct and eligible`, `correctness rate`, `worker_01`, `worker_02`, `combined_score`, `rubric`. Do not expose these labels in paper prose or plots. Use substantive method names, training-fit onset, held-out generalization onset, and delayed-event counts with explicit denominators. Do not mechanically relabel configuration-level search entries as independent seeded experiments.

The final submission must omit identifying authors, affiliations, acknowledgements, funding, and self-identifying links. This stage writes neither the final manuscript nor claims mapping, runs no new experiments or final-paper validation, and generates no figures. Strategy-only checks should verify JSON structure, grounding-source existence, data/pointer consistency, figure budgets, and agreement between these two strategy outputs.
