# Paper Framing Strategy

## Decision and Thesis

**Status:** ready. **Prompt family:** `paper_standalone`, compatible with `write-paper-standalone`. This stage plans a paper; it does not draft one.

**Provisional title:** Missingness-Aware Latent Models for Budgeted Embedding Benchmark Prediction.

**Central question:** How accurately can a historical-only, missingness-aware latent-model procedure predict an unseen embedding model’s recorded but unqueried benchmark scores at small query budgets, and how does this change under name-proxy-family-disjoint evaluation and destroyed historical cross-task alignment?

**Central thesis:** On the evaluated English MTEB panels, the frozen latent-model procedure has lower aggregate prediction error than the evaluated random-acquisition low-rank and greedy-coverage ridge pipelines, including on never-queryable audit targets, but the advantage is not uniform across held-out splits and does not isolate the contribution of mixtures or value-adaptive acquisition.

This is one standalone empirical method-integration study, organized around prediction under a query budget. The two holdout conditions are evidence blocks under that question, not independent datasets or a sequence of discoveries. The observed advantage is descriptive; it is neither a priority claim nor an assertion that a new neural architecture was developed.

## Evidence Authority and Qualification

`paper_data.json.final_evaluation` is read independently of any downstream-study narrative. The current input has no `downstream_study` and no `study.*` grounding IDs. Therefore omit campaign winner narratives, search-score deltas, scored/unscored attempt counts, and original-incumbent performance claims. In any future input, unscored attempts remain missing evidence, not measured losses.

The current final evaluation is **completed and qualified**, grounded specifically in `final.qualification.status`, `final.qualification.outcome`, and `final.qualification.correct`. This is separate from search selection. Qualification is not a scientific guarantee of generalization, mechanistic validity, or superiority. If authoritative qualification changes during later review or revision, preserve its reported outcome—including failure—and limitations rather than explaining it away using retained metrics. Missing gate diagnostics remain unknown.

The final episode evidence is available and its local file hash matches the recorded SHA-256. Its three seed records contain original and permuted-history cases for model-group and name-proxy-family-disjoint holdouts, plus a zero-weight reset replay. Exclude replay from performance averages. Candidate-generated internal diagnostics are explicitly unverified. `ablation_studies` is empty.

Source precedence is: final metric and qualification IDs for headline facts; `final.evidence.episodes` for recorded row/checkpoint/control results; frozen task resources and the selected implementation for protocol and method exposition; reference provenance for bibliography identity, not unread scientific findings. Private memory is not quantitative evidence.

## Framing Alternatives and Edit Decision

No `previous_paper/`, staged new/old program pair, `aggregated/`, `extra_tasks/`, contributions scaffold, or instantiated edit-context file is present. Literal placeholders do not activate edit mode. The JSON status `prior_paper_story_status: rejected` means no inherited narrative is adopted, not that a prior manuscript was scientifically rejected.

| Candidate framing | Decision and evidence |
| --- | --- |
| Preserve an existing manuscript with local updates | Inapplicable: no seeded manuscript is supplied. Do not invent its title or thesis. |
| Preserve the broad generative-LLM aspiration from the source brief | Reject: the measured data are English embedding-model results, not generative-LLM benchmarks. |
| Broaden to a shared latent-model family under two holdout conditions | Select, narrowly: explain covariance fitting, optional mixture inference, conditional prediction, and historical model choice as one frozen procedure, evaluated on one benchmark source. |
| Recenter on the newest quadrature acquisition branch | Reject: static availability and search ties do not make it the frozen evaluated method or establish an acquisition benefit. |
| Lead with uniform superiority or a mixture-specific discovery | Reject: a family-disjoint split favors ridge, actual internal choices are unverified, and external component ablations are missing. |

Private provenance: `results/best_program_manifest.json` identifies `results/ideas/02_value_adaptive_latent_mixtures_for_absolute_error_benchmark_prediction/program_1`. Use its implemented procedure and fallback, not a chronology of candidate branches. Do not expose internal directory or selection terminology in the paper.

## Scientific Scope and Included Methods

The data are pinned MTEB embedding results at revision `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`. Each frozen panel has 48 context-specific columns keyed by task, language, split, primary metric, and dataset revision, with natural missingness. Final plans contain 48 held-out rows and 88–99 historical rows. Budgets are `k={1,2,4,8}`; eight panel columns are never queryable, and each eligible held-out row has at least four recorded audit cells. These are task-resource protocol facts, not new performance measurements or full-repository coverage claims.

1. **Proposed procedure:** observed-data low-rank-plus-diagonal covariance fitting; optional small latent-mixture prior; conditional score prediction and transfer selection; historical row-heldout fixed-target model choice; Gaussian fallback. The available single-component path must remain explicit. Code availability does not show the selected component count or selector.
2. **Random acquisition plus masked low-rank prediction:** retain the genuinely executed baseline. It differs in acquisition and fitting, so it does not isolate acquisition quality.
3. **Greedy correlation coverage plus ridge prediction:** retain the stronger whole-pipeline comparator, including cases where it wins.
4. **Historical per-benchmark mean:** retain as a simple historical reference, clarifying the target-set convention.
5. **Supporting controls:** column-permuted history in the main analysis; queried-score-average and reset replay details in the supplement. Neither protocol completion nor a weak score-copying control is a performance contribution.

Do not add measured method groups for Gaussian versus mixture, mean versus median, adaptive versus blind acquisition, or quadrature. The source implements some internal comparisons, but their results are not externally verified. Do not infer an original-starter final comparison where no such evaluated comparison is supplied.

Explain observed-data fitting, not a zero-filled score likelihood. Standardization uses recorded historical entries only; residual variance denotes task-specific variation. The constrained posterior median is optimal for modeled absolute loss, not a proof of real-data optimality. The square-root transfer criterion is a heuristic; it is not exact bounded-mixture integrated absolute risk. Gaussian unconstrained-risk identities cannot be reused unchanged for bounded actions. No new theorem or experimental theory verification is established.

## Results That Carry the Paper

### Aggregate accuracy and unchanged-target accuracy

The following primary final metrics are authoritative:

| Evaluated pipeline | Remaining-recorded-target normalized MAE |
| --- | ---: |
| Frozen proposed procedure | 0.031296949105441715 |
| Greedy coverage plus ridge | 0.036070484115358764 |
| Random acquisition plus low-rank | 0.04563401706946738 |
| Historical mean | 0.08782454238980078 |

Sources: corresponding `final.metric.*` IDs. Reader-facing presentation should round consistently and label lower as better. Do not display an internal search objective.

Remaining-target sets depend on which tasks each method queries. Consequently the common-target audit is essential to the central thesis, not an appendix-only reassurance. Audit columns are never selectable and only their recorded cells are scored. Descriptive audit means derived from the six non-replay original case summaries are 0.02687114697690909 for the proposed procedure, 0.029409541552239845 for ridge, and 0.0354685223509185 for random low-rank. These are deterministic summaries of existing evidence, not additional experiments. Record JSON pointers and aggregation code in downstream figure/claim mapping.

### Budget trade-offs and the adverse split

Use fixed-audit error at each recorded budget, broken out by holdout condition. Show all three split-seed values and their descriptive means; this answers how prediction changes within the tested budget range without inventing a universal sufficient budget or an acceptable-error threshold.

Include a main-text six-row table for the two conditions and three seeds. In particular, retain the family-disjoint seed 4021 reversal: proposed remaining-target MAE is **0.03665795350948428**, compared with ridge **0.03414373962951742**; audit MAE is **0.02971584244781457**, compared with ridge **0.026874009322976657**. These are comparative performance results, not a diagnosed validity or adaptivity failure. Neither a favorable aggregate nor administrative qualification may erase this observation.

### Dependence on historical alignment

The reported proposed MAE changes from 0.031296949105441715 with original history to 0.08976440453371944 under historical-column permutation (`final.metric.permuted_mae`). For the figure, prefer unchanged audit targets and show all three evaluated pipelines in both holdout conditions. The transformation preserves recorded masks and column marginals while disrupting cross-task alignment. Because the entire pipeline is refitted and retuned, this is not a pure component ablation or a proof that a particular representation captures true latent skills.

### Aggregation and uncertainty

Follow `task/evaluate_final.py` exactly: average checkpoints equally; use equal row weights for model-group; use equal proxy-family means for family-disjoint; then average equally over original non-replay cases across conditions and seeds. Case loss order is proposed, historical mean, queried-score average, random low-rank, greedy ridge. Audit baseline order is random low-rank, greedy ridge. Do not accidentally reverse them.

Seeds 4001, 4009, and 4021 specify frozen split realizations that may reuse rows or families; they are not independent population draws or pure optimization-seed repeats. Show raw split values and descriptive variation, not fabricated confidence intervals, significance tests, or pseudo-replication over rows/checkpoints. Historical internal paired-SE selection rules are not inferential evidence about final superiority.

## Figures, Geometry, and Footprints

The inspected `paper.sty` sets **one 5.5-inch text column and a 9.0-inch text height** (lines 48–49). Thus full text width and column width coincide. A two-column 0.48-width assumption would be incorrect. All required figures target the full 5.5-inch text width with labels at least 9 points after placement. Do not rescue dense panels by shrinking them.

| Figure | Contents and generator | Readability budget | Placement and intended footprint |
| --- | --- | --- | --- |
| 1: Problem and evidence overview | `diagram` via `generate-concept-figure`: masked historical matrix; historical-only fitting/model choice with Gaussian fallback; query/condition loop; unqueried predictions; fixed audit boundary. No invented numeric cells. | One panel, at most six major objects, one schematic series; four or five principal units preferred. | Page 1 or 2, full text width, about 2.1 inches high plus caption, roughly a quarter page. At most this one concept-generator figure. |
| 2: Common-target budget comparison | Source-generated matplotlib point/line plot: two holdout-condition panels, fixed-audit MAE at four budgets, three pipelines, unconnected seed points plus descriptive means. | Two panels total and per row; four x categories; three method series. Seed observations use the method color, not extra legend series. | Main results, full text width, about 2.5 inches high plus caption, roughly a third page. Shared legend and y scale; each panel about 2.5 inches wide. |
| 3: Historical-alignment control | Matplotlib paired-dot comparison: one panel per condition, three pipelines, original and permuted history, fixed-audit MAE averaged over budgets. | Two panels total and per row; three method categories; two arm series. Show recorded seed points and means. | Main results, full text width, about 2.2 inches high plus caption, roughly a quarter to a third page. Short method labels, common y scale, no cramped inset. |

All diagrams describe information flow, not research chronology. Budget on Figure 2’s x-axis is the scientific resource variable, not campaign progression. No thresholded success-rate figure is needed.

Create two compact main tables: the aggregate four-method primary/common-target comparison, and the six-row split-seed proposed-versus-ridge comparison. Do not duplicate them with redundant bar charts. Generate detailed numerical tables from evidence, not from copied plot coordinates.

Every quantitative figure must export **vector PDF and a 300-DPI PNG from source**; LaTeX uses PDF whenever available. Preserve the editable draw.io source for the overview. Raster-only full-width output must be regenerated at least 2400 pixels wide; a genuinely column-width raster in a different format requires at least 1200 pixels. Never upscale existing raster images. In the downstream figure manifest, record placement, intended width fraction, and minimum rendered font. No figures are generated in this stage.

## Body Budget and Thesis-First Layout

Target approximately **8.75 body pages**, within the ICLR 2026 brief’s 8–9 pages excluding references. An eight-page body must have its last page at least 75% full. These allocations include associated floats and captions; do not add figure space a second time.

| Scientific content | Approximate pages |
| --- | ---: |
| Title, abstract, introduction, early overview | 1.55 |
| Related work and precise problem formulation | 1.00 |
| Missingness-aware inference, selection, validation, fallback | 1.65 |
| Data and evaluation protocol, baselines, target-set definitions | 1.20 |
| Accuracy/budget comparisons, adverse split, alignment controls | 2.15 |
| Discussion, limitations, reproducibility | 0.95 |
| Conclusion | 0.25 |

Suggested headings: Introduction; Related Work and Problem Formulation; Missingness-Aware Latent Prediction and Transfer Selection; Evaluation Protocol; Prediction Accuracy and Budget Trade-offs; Dependence on Historical Alignment; Discussion and Limitations; Conclusion. Use extra space for a faithful conditional-inference explanation, protocol clarity, and adverse-case interpretation—not branch history or filler. Do not overfill beyond nine pages, and do not leave an obviously underfilled eight-page body.

Double-blind requirements remain hard constraints: omit author identities, affiliations, acknowledgements, funding statements, identifying links, and internal absolute paths. Keep a separate `LLM Usage` section after references in the supplement.

## Supplementary Information After References

The supplement adds auditable depth, not a hiding place for central negative evidence:

1. **Complete Budget-Resolved Prediction Errors.** All recorded checkpoints, split seeds, conditions, original/permuted arms, evaluated pipelines, historical means, and queried-score averages, for both error definitions. Exclude replay from averages. Grounding: `final.evidence.episodes` and the corresponding final metric IDs.
2. **Aggregation and Common-Target Comparisons.** Exact weights, seed-level paired deltas, and policy-specific versus unchanged-target views. Grounding: `final.evidence.episodes`; implementation: `task/evaluate_final.py`.
3. **Observed-Data Inference and Historical Model Choice.** Faithful EM/conditioning equations, implemented candidate grids, regularization, bounded median, transfer heuristics, historical-only fixed-target validation, and fallback. The source’s `max(0.0001, 0.5 paired SE)` margin is a selection heuristic, not a significance test. Grounding is the selected `src/covariance.py`, `src/mixture.py`, and `src/METHOD.md`, not unverified internal performance. Private-only provenance anchors: `result.top_program_01` identifies the implementation and `final.evidence.episodes` links the frozen evaluated artifact by program hash. These anchors do not establish component-specific gains or which optional branch ran; no search score is used as final evidence.
4. **Frozen Data, Score Contexts, and Reproduction.** Pinned source revision, normalization, task-context keys, resource checksums, natural missingness, name-proxy families, mask-defined availability, seeds, dependency versions, and existing commands/interface. Sources: frozen resources, task contract, final manifest, `final.evidence.episodes`, and qualification provenance. Separate recorded evaluator timing from unmeasured method-only runtime or actual evaluation-cost savings. Anonymize public paths.
5. **Permutation and Reset Controls.** Complete recorded control tables and deterministic replay; distinguish protocol checks from predictive evidence. Sources: `final.evidence.episodes`, permutation metric IDs, and `final.qualification.*`.
6. **LLM Usage.** Disclose agent roles supported by implementation/status documents and append-only logs; add later drafting/figure assistance only if it occurs. Do not claim human validation, unread literature review, unrun experiments, or an undocumented model identity. Private-only provenance anchor: `result.top_program_01` identifies the implementation whose assistance is disclosed; it does not establish LLM involvement. Ground those roles directly in the selected `src/METHOD.md`, `global_memory/memory.jsonl`, `memory.md`, and planning files, never in the source metric. All supplementary entries retain non-empty lists of existing paper-data source IDs without fabricating scientific evidence.

The writer may receive a later authoritative analysis ranking; route appendix-ranked material here without retroactively altering this strategy. No absent robustness study or posthoc ranking is presumed complete.

## Limitations That Must Stay Visible

- Only pinned English embedding panels are evaluated, not generative LLMs, multilingual tasks, every upstream model, or every MTEB benchmark.
- Naturally missing target scores have no ground truth here. Retrospective query availability is supplied from each target row’s recorded mask with audit columns removed. This does not establish prospective availability or arbitrary missing-not-at-random recovery.
- Name-derived family proxies and frozen-data content checks do not guarantee complete architectural/lineage independence, population-level generalization, or absence of all contamination.
- Cross-pipeline comparisons do not identify which component helps. Actual mixture choices, acquisition adaptation, fallback frequency, uncertainty calibration, cost-weighted selection, missingness sensitivity, and additional-dataset replication are not externally established.
- Query count is not measured compute or monetary savings; real benchmarks have unequal costs. No universal sufficient budget or accepted-error threshold is demonstrated.
- The adverse split, small and dependent split-seed set, target-set dependence, and incomplete mechanism attribution belong in the main discussion even though aggregate errors favor the procedure.

## Literature and Writing Guardrails

`references.bib` and `references_provenance.json` exist. At inspection they contain a retrieved method-oriented pool, including `Ghahramani1996TheEA`; essential MTEB and several explicitly allowed starter titles are not in that pool. Retrieval metadata is not evidence of reading a source’s scientific conclusions. Before final drafting, verify a small relevant subset of permitted original sources and safely retrieve missing explicitly allowed starter works. Avoid broad discovery, citation chasing, and all prohibited work or discussion of it. Do not infer or search for the prohibited paper’s identity. No network retrieval was performed for this strategy.

Do not pad related work with irrelevant retrieval hits, assert novelty priority from an incomplete bibliography, or claim comparisons to unrun published methods. Position the contribution as a concrete, reproducible integration and bounded empirical finding unless stronger grounding is supplied.

Forbidden headings include Search Progression, Campaign Timeline, Milestones, First Valid Result, Phase One / Phase Two, Iteration History, Experiment A / Experiment B, From Gaussian to Mixture to Quadrature, Architecture Improvements, and State-of-the-Art Benchmark Compression.

Forbidden phrases include “we then tried,” “subsequent improvements,” “first valid result,” “next-best,” “later variants,” “the winning idea,” “the latest variant proves,” “all families improve,” “eight benchmarks are sufficient,” “statistically significant improvement,” “the mixture caused the gain,” “quadrature improves prediction,” “calibrated uncertainty,” and “state of the art.” Internal field/agent names listed in the JSON are prohibited in visible manuscript text; the path and source-ID discussion here is private writer guidance, not recommended paper language.

## Handoff and Stage Boundaries

The accompanying JSON mirrors this memo and provides per-figure aggregation, source paths/IDs, and export requirements. The writer must use final metric sources for measured headline claims and record exact episode pointers for derived plots and tables. Static implementation details do not become measured claims through a citation to external episode records.

Only strategy consistency checks are appropriate now. Do not create `paper.tex` or `claims_grounding.json`, run new experiments, generate final figures, or invoke final-paper validation at this stage.
