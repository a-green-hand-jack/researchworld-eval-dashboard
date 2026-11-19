# Paper Framing Strategy

## Decision

**Status:** ready for a bounded standalone empirical-methodology paper, not a claim of a new optimizer, new post-selection theorem, or universal improvement. Selected family: `paper_standalone`; writing skill: `write-paper-standalone`.

**Provisional title:** Protected Reporting After Prompt Selection: Benefits and Limits

**Central question:** When does reserving benchmark questions for reporting reduce error after prompt selection, and what can known-truth simulations versus finite real-model audits establish about reliability?

**Central thesis:** Across the five final seeds, half-split reporting lowers mean error relative to reusing the same winner's selection score in the sixteen-prompt conditions, but does not uniformly beat full-budget or non-search comparators, and the real-model results establish audit agreement rather than population validity.

The contribution is a controlled, explicitly limited comparison of reporting targets, selection multiplicity, and reporting-sample cost. Sample splitting itself is conventional. Do not claim that the search invented it or that reliable reporting necessarily increases selected-prompt accuracy. Simulation and real inference serve different evidential roles under one question, not separate chronological experiments.

## Evidence and Framing Alternatives

Read the independent final record before interpreting the search. `final.qualification.status`, `final.qualification.outcome`, and `final.qualification.correct` report **completed / qualified / true**. This run does not have a failed final qualification. That status establishes neither statistical superiority nor general scientific validity. Candidate diagnostics in `final.evidence.episodes` remain **unverified**; missing detailed gate diagnostics remain unknown.

Separately, `study.selection_kind` retains the original baseline; `study.investigation_outcome` reports no qualifying replacement. `study.attempts.scored` is zero, `study.attempts.unscored` is three, and `study.search_score_delta` is zero. Unscored attempts are missing performance evidence, not measured losses. Search scores are not benchmark accuracies and cannot be compared with final-scope metrics as improvements.

No resolved edit-context files, prior manuscript, `aggregated/`, or `extra_tasks/` are present. The JSON decision is **recentered**: from the broad task ambition and private proposals to the retained policy's measured reporting trade-off, not a replacement of an existing manuscript.

| Candidate framing | Decision and evidence |
| --- | --- |
| Preserve a broad automatic-tuning success story | Reject: no scored replacement or measured search improvement. There is no prior manuscript to preserve. |
| Broaden to paired certificates, allocation variants, or an adaptive method family | Reject: no final measurements of those interventions; unscored candidates do not support efficacy claims. |
| Recenter on the frozen-bank reporting trade-off | Select: directly implemented policy, matched reporting comparison, known-truth conditions, real inference, and explicit counterexamples. |
| Lead with universal superiority of protected reporting | Reject: full-budget and fixed-prompt aggregate MSE are lower; comparison targets and observation budgets differ. |
| Reject solely because the campaign found no winner | Reject: the independent completed final evaluation supports a bounded empirical study of the retained method. |

The selected and original-baseline program sources are byte-identical. Treat the baseline as the studied policy, not as a separate identical comparator. `task/evaluate_final.py` has the exact SHA256 recorded in the final evaluator metadata, providing direct linkage for inspected estimator and control definitions. The program-tree hashes reported in different scopes differ; do not silently equate those scopes or claim a stronger source-tree identity than the evidence establishes.

## Methods Worth Including

1. **Protected half-split reporting — studied policy.** Frozen sixteen-prompt bank, seeded random half selection/half reporting, uniform report weights, fixed tie order, 95% Wilson interval. Select the maximum-accuracy prompt on selection rows. Do not call this a novel estimator.
2. **Same-winner selection-score reuse — primary baseline.** Report the selected prompt's selection-row mean. The winner is identical, so this comparison isolates which rows produce the reported score; it is not full-benchmark reuse.
3. **Full-budget selection and reuse — budget-aware baseline.** Select and report using all available questions. Its winner can differ. This is a practical trade-off, not a pure reporting ablation.
4. **Fixed and random prompts — non-search baselines.** Use all questions and evaluate each method against its own prompt target. Lower reporting MSE does not imply higher prompt accuracy.
5. **Alternative half split and controls — supporting only.** The evaluator's first-half/second-half split is another implementation of the same statistical idea. Constant, copied-arm, contaminated-report, permutation, and replay checks are diagnostics, not new performance methods.

Exclude unmeasured certificates, outcome corrections, quarter allocations, stratum-balanced performance claims, new architectures, and generic optimizer comparisons. There are no scored ablation studies to turn into an ablation narrative.

## Results That Carry the Argument

The final evidence contains five seeds, each with eight conditions: synthetic/real, total questions 64/256, and prompts 1/16. Synthetic conditions include four regimes with 1024 replicates each; real conditions have one realized benchmark/audit comparison per seed, not 1024 model runs. Use `final.evidence.episodes` for condition-level comparisons and uncertainty.

**Primary comparison.** Show protected reporting versus same-winner selection reuse and full-budget reuse, stratified by evidence family, question budget, and prompt count. The sixteen-prompt condition means support lower protected-report error than same-winner reuse. The one-prompt condition removes selection multiplicity and reveals that withholding observations still costs precision. Synthetic full-budget reporting has lower MSE than protected reporting in the condition means; keep that counterexample visible.

**Secondary aggregate context.** Supplied aggregate MSE is 0.0033498776393466522 for protected reporting and 0.005354862639043066 for selection reuse. Full-budget reuse is 0.002705803510381116 and fixed-prompt reporting is 0.0021956944465637207. These come from `final.metric.report_mse`, `final.metric.reuse_mse`, `final.metric.full_budget_naive_mse`, and `final.metric.fixed_prompt_mse`. They support a trade-off, not a universal ranking. Equal weighting across conditions and synthetic regimes is not pooling all simulation replicates and real questions into one population estimate.

**Known-truth evidence.** Explain the four synthetic regimes: equal/graded prompt means crossed with shared-outcome mixing parameters 0.1/0.9. Do not mislabel that mixing parameter as an exact Pearson correlation. Retained regime metrics support bias, optimism, MSE, Wilson coverage, width, and report-MSE standard-error summaries. A compact main table should expose these mechanisms; complete regime tables belong in the supplement. Simulation coverage is not a new inferential theorem.

**Real evidence.** Runtime and split manifests identify CPU float32 `HuggingFaceTB/SmolLM2-135M-Instruct`, revision `12fd25f77366fa6b3b4b768ec3050bf629380bac`, and MMLU-Pro revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`. Generation is deterministic and constrained to one legal answer-letter token; context exclusions and invalid outputs count as errors. Do not substitute an assumed larger model or free-form reasoning pipeline.

Each real target is a **512-question finite audit**, not known fresh-population accuracy. The supplied paired subject-bootstrap interval estimates **selected-minus-fixed audit accuracy**, using 200 bootstrap draws; it is not an interval for reporting optimism or an MSE difference. Plot all five seeds in both sixteen-prompt question-budget conditions, including zero-crossing and negative estimates. Do not select only positive intervals. Shared-pool sampling and overlapping conditions preclude interpreting these as independent datasets or pooling their intervals into a blanket significance claim. Public-data pretraining contamination is possible, not demonstrated.

**Validity boundary.** Deliberately copied reporting rows correctly record failed independence in the contaminated control; that is not the retained policy failing final qualification. Completed controls and replay do not certify representative sampling, adaptation-safe inference, or population coverage. Preserve unverified diagnostics in the body. If an authoritative later record changes qualification to `not_qualified`, disclose it in writing, review, audit, and revision without inventing a statistical, validity, or adaptivity cause.

The recorded decision-reversal quantity compares protected-report-minus-full-sample-fixed and selected-target-minus-fixed-target signs, excluding ties. It is not directly the probability that a naive winner claim gets overturned. Omit it from the central narrative unless this precise definition is necessary.

## Required Figures and Layout

`paper.sty` sets **one text column, 5.5 inches wide and 9 inches high**. Consequently full-width and column-width mean the same full text span here, not a two-column float. Do not rescue dense plots by shrinking them. The JSON specs provide canonical generator, grouping, sources, and readability budgets. Both quantitative multi-panel figures use the schema-supported `composite` type; grouped-point and horizontal-interval describe their panel designs, not additional manifest types.

| Figure | Design and role | Placement and readability budget |
| --- | --- | --- |
| `reporting_overview` | Concept diagram: bank, selection/report split, same-winner reuse, and known-truth versus finite-audit targets; distinguish the different-winner full-budget comparator. Use `generate-concept-figure`, with editable draw.io and prompt provenance. | Page 1 or 2; full 5.5-inch width, about 1.6 inches high plus caption, roughly one fifth page. One panel, at most six semantic blocks, three paths/series, at least 9-point final labels. No numerical decoration or adaptive feedback loop. |
| `reporting_error_comparison` | Matplotlib 2x2 grouped-point comparison: rows synthetic/real, columns question budget; K=1/16 categories, three reporting series, and five seed dots. Label the synthetic row population MSE and real row audit-reference squared error. | Full 5.5-inch width, about 2.8 inches high plus caption, roughly two fifths page. Four panels, two per row, two categories and three series per panel. One legend, at least 8.5-point final labels. Match scales within rows or make differences unmistakable. |
| `real_audit_accuracy_difference` | Matplotlib horizontal paired-bootstrap intervals, selected minus fixed audit accuracy at K=16; two question-budget panels with every final seed and a zero line. | Full 5.5-inch width, about 1.8 inches high plus caption, roughly one quarter page. Two panels in one row, five seed categories, one series; shared x limits and at least 8.5-point labels. |

Seed dots are within method series, not five extra legend series. Use descriptive means/scatter, not invented error bars from unavailable paired replicate data. Include a compact main table with all six reporting comparators and another compact synthetic regime diagnostic table covering bias, reuse optimism, coverage and width. Do not turn the table into a winner leaderboard.

Quantitative plots must have reproducible source, **vector PDF plus 300-DPI PNG**, and LaTeX must use PDF when available. Raster-only full-width assets must be at least 2400 pixels wide; column insets at least 1200 pixels. Regenerate from source rather than upscale. Exactly one planned overview uses `generate-concept-figure`; no figure is generated at this stage.

## Body Budget and Venue Checks

Target **8.5 body pages**, within the venue's 8–9-page requirement, excluding references. An exactly eight-page body must fill at least 75% of its final page. Budget allocations are plans, not experimental measurements:

| Content | Pages |
| --- | ---: |
| Title, abstract, problem, concrete contributions, early overview | 1.25 |
| Related work | 0.75 |
| Estimands and reporting policies | 1.50 |
| Experimental design and provenance | 1.00 |
| Controlled comparisons, Figure 2, all-comparator table and regime diagnosis | 2.00 |
| Real audit uncertainty and Figure 3 | 0.75 |
| Interpretation, limitations, reproducibility pointer and conclusion | 1.25 |

Use the space for target definitions, budget fairness, dependence, uncertainty, and explicit counterexamples; not filler, oversized graphics, or invented additional experiments. Suggested headings are **Introduction; Related Work; Selection and Reporting Targets; Reporting Policies; Experimental Design; Reporting Error and Selection Multiplicity; Finite-Audit Evidence; Discussion and Limitations; Conclusion**.

`VENUE.md` mandates **ICLR 2026**, double-blind anonymity, and a separate **LLM Usage** section. The staged resource template is named `iclr2027_conference` and the working style has historical comments. The matching geometry is inspected, but official 2026 provenance is not established. The downstream writer must verify or obtain the correct official 2026 files through a direct known official source, not silently relabel the 2027 template. Omit author identities, affiliations, acknowledgements, funding statements and identifying links; do not alter geometry to force page fit.

## Supplementary Information

Place it in the same manuscript **after references**: clear page, bibliography, clear page, appendix, `Supplementary Information` section. Keep essential counterexamples, audit limitations, and diagnostic caveats in the body. Separately supplied appendix-ranked analyses belong here; this strategy does not guess their ranking.

1. **Complete Condition and Regime Results.** All eight conditions for each seed; all six comparator metrics; full synthetic regime summaries and supplied report-MSE standard errors. Distinguish population coverage from real audit containment. Sources: `final.evidence.episodes`, `final.metric.report_mse`, `final.metric.reuse_mse`, `final.metric.honest_half_mse`, `final.metric.fixed_prompt_mse`, `final.metric.random_prompt_mse`, `final.metric.full_budget_naive_mse`.
2. **Partition, Estimand, and Uncertainty Details.** Exact prompt bank, tie order, random partition, alternative half split, Wilson formula, each method's target, synthetic construction, averaging, and subject-bootstrap semantics, using the SHA256-matched evaluator and staged source. Sources: `final.evidence.episodes`, `study.selection_kind`, `final.metric.coverage`, `final.metric.interval_width`.
3. **Diagnostic Controls and Evidence Boundaries.** Constant/copy/permutation/replay observations, deliberate contaminated-report independence failure, unverified diagnostics, unknown gate checks, and hash-scope distinctions. Sources: `final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`, `final.metric.control_failure_rate`, `final.metric.replay_discrepancy`.
4. **Reproducibility, Resources, and Incomplete Comparisons.** Local model/data manifests, dependency versions, seeds, commands and eventual figure/table scripts; observed episode durations rather than invented CPU-hours or token counts. Distinguish future reproduction commands from completed execution. Disclose baseline retention and three unscored attempts without guessing timeout causes. Sources: `final.evidence.episodes`, `study.selection_kind`, `study.investigation_outcome`, `study.attempts.scored`, `study.attempts.unscored`, `study.search_score_delta`.
5. **LLM Usage.** Precisely disclose observed assistance in ideation, implementation, reference planning and writing, distinct from evaluated answer generation. Do not invent human oversight or use identifying internal paths. Sources: `study.selection_kind`, `study.attempts.total`, `final.evidence.episodes`; current workflow provenance supports the writing disclosure, not numerical scientific claims.

## Wording and Grounding Guardrails

Avoid headings such as **Experiment A / Experiment B; Search Progression; Campaign Phases; Milestones and First Success; Round-by-Round Improvements; Winning Configuration; From Failed Attempts to a Final Breakthrough**.

Avoid phrases such as “we then tried,” “first valid result,” “subsequent improvements,” “next-best,” “later variants,” “our search discovered a superior method,” “three failed methods performed worse,” “guaranteed unbiased reporting,” “validated population coverage on MMLU-Pro,” and “uniformly outperforms all baselines.” The exact forbidden internal-label list is in JSON; do not expose those labels in reader-facing text or figure legends. No threshold-rate figure is needed.

Use `final.metric.*` and `final.evidence.episodes` for results, `final.qualification.*` for final status, and `study.*` for selection/search accounting. Private memory supplies no quantitative evidence. A bibliography entry and metadata provenance do not establish that an original document was consulted or that a paper is relevant. Verify consultation and cite only relevant actual keys; do not pad related work with incidental retrieval matches or invent missing benchmark, Wilson, or bootstrap references. The permitted starter exact-title scope and `Berk2013ValidPI` are positioning leads, not a claim of completed reading. Do not discover, identify, search for, or follow citation graphs to the prohibited paper or related discussion. Stop and log any known accidental encounter. This framing agent performed no external literature browsing.

The strategy is ready because the evidence supports a coherent, narrow study, **not** because novelty, conference acceptance, full reproducibility, or general validity is established. The template-year and citation-consultation checks remain explicit downstream production requirements. This stage writes no final manuscript, claim ledger, figures, new experiments, or final-paper validation.
