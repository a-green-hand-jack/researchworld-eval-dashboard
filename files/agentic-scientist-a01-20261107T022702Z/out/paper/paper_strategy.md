# Paper strategy: cap-dependent task budgets

**Status:** ready for the `paper_standalone` family. This is a framing plan, not a manuscript or a statement that final submission requirements have already been met.

**Provisional title:** Cap-Dependent Task Budgets for Leaderboard Promotion.

## Central question and thesis

**Question.** On fixed public multitask score tables, how does the smallest task subset needed to make a target co-first change with the aggregation rule and the allowed fraction of score headroom?

**Thesis.** In the evaluated score tables, changing the response cap reverses mean-versus-median investment orderings for some targets and makes other promotions unattainable. Aggregation-rule resistance must therefore be reported conditional on the cap and target score vector, rather than as a universal ranking.

Present HELM MMLU and the six-task Open LLM table as two settings of one static intervention model. Do not organize them as chronological experiments. The contribution is a conditional, reproducible score-space analysis with explicit allocation certificates and failure cases, not a training method, an architecture, or a demonstrated optimizer improvement.

## Framing decision and alternatives

This is not an edit pass. No seeded prior manuscript, resolved edit-context files, `aggregated/`, or `extra_tasks/` were found. The JSON enum `prior_paper_story_status: rejected` means no inherited manuscript story is adopted; it does not mean an unseen manuscript was assessed.

The selected source and original comparator were inspected directly. The selected staged `program.py` matches the downstream source file by SHA-256. Selection metadata identifies the first candidate, not either later refinement. Recorded directory-tree hashes differ across artifact scopes; do not equate them based on a matching source file.

Three candidate stories were considered:

- **Prospective cap frontiers:** preserve the earlier conceptual direction, but narrow its language. Only two positive caps were evaluated; continuous frontiers, empirical response envelopes, strict-margin sensitivity, and composition resampling are not completed evidence.
- **Broad cross-setting solver improvements:** reject as the center. There are no grounded ablations attributing gains to the later gain-window or mixture-cut variants, and search scores tie the original comparator.
- **Measured cap-dependent promotion budgets:** select. The same-target rule comparisons directly demonstrate reversals in both score tables, while reachability and independent bounds make the limitations inspectable.

This choice beats a campaign diary because it answers the original scientific question with controlled, interpretable comparisons. Neither a positive search winner nor model training is needed for this bounded study.

## Independent final assessment and evidence hierarchy

Read final assessment independently of selection. The following are **private audit facts**, not names for visible scientific metrics:

- `study.selection_kind = non_winner_candidate`; `study.investigation_outcome = completed_no_winner`.
- `study.search_score = study.baseline_score = 0.7239766081871346`; `study.search_score_delta = 0`.
- `study.attempts.total/scored/unscored = 3/3/0`. Unscored attempts would be missing performance evidence, not measured losses.
- `final.qualification.status/outcome/correct = completed/qualified/true`.
- `final.metric.final_score = 0.6633040935672518` belongs to a separate weighted evaluation scope. It is not a matched change from the search score.

No failed final qualification is reported in this run. Do not invent one, reinterpret non-selection as a validity failure, or treat passing assessment as proof of generalization or scientific novelty. Missing criterion diagnostics remain unknown. Candidate diagnostics are marked unverified; use recorded independent validation and reference bounds instead of self-report.

Main quantitative grounding is `final.evidence.episodes`, whose payload is `paper_data.json.final_evaluation.evaluation_evidence.episodes`. Filter `solution.cases` to `case = original`, then pair by family, target, rule, fraction, and seed. Retain exact episode/case/observation pointers for downstream claim mapping. The method files and `task/resources/final/` files support implementation and provenance explanations; their paths are not invented grounding IDs.

## Scientific definitions and scope

For normalized target scores `x` and a selected task subset `S`, selecting coordinate `j` changes it to `round(x_j + rho(1-x_j), 10)`. Other target coordinates and every rival score coordinate remain fixed. Investment is the uniform task count `|S|`, optionally divided by task count `d` for cross-setting display. The empirical positive caps are `rho = 1` and `rho = 0.5`; zero belongs to the no-update control.

Promotion means **co-first** within aggregate tolerance `1e-10`, not strict first place. The ordinary even median averages its two central values. Borda uses average pairwise win credit with half credit for ties: changing the target can change rivals' Borda totals despite fixed rival task scores. Recompute those totals.

This is a hypothetical score-response model. It does not measure training examples, tokens, money, compute, contamination efficacy, transfer, forgetting, or rivals' strategic responses. Only under a genuine upper-response envelope could an exact support minimum lower-bound affected tasks for a successful intervention; no evidence here calibrates such an envelope to real training.

The frozen final context contains 57 HELM subjects and six normalized Open LLM columns, with 42 and 2129 rows respectively. These are resource-context facts, not the broader public-catalog totals from the task brief. Do not mix Raw columns into the six-task analysis or reinterpret their aggregate columns as all underlying subtasks. Target row numbers are local identifiers, not model names.

## Narrow method groups

1. **Static capped-response model, supporting:** the shared intervention and the three aggregation rules define the comparison.
2. **Frozen allocation solver, studied/proposed:** sorted gains for mean, threshold counting for odd median, endpoint counting for even median, and bounded rival-aware integer Borda search with verified fallback. The label proposed does not assert novelty or superiority.
3. **Original frozen comparator, baseline:** preserve its tied search comparison using `study.baseline_score` and `study.search_score_delta`. No separate matched final evaluation of that full implementation is grounded.
4. **Evaluator-recorded policies, baselines:** no update, random task order, and immediate-gain greedy. These have matched final allocation records; do not silently relabel the evaluator's greedy policy as the original frozen comparator.
5. **Independent budget reference, supporting:** exact flags and lower/upper bounds certify individual reported costs. Finite selected allocations match exact reference cardinalities in the original records. This is not a proof that the deadline-bounded Borda algorithm is exact on every input.

Exclude later gain-window and mixture-cut branches from the method narrative. They are not ablations, and their names are not evidence of an improved mechanism. Do not introduce unmeasured architecture shifts or training procedures.

## Results that carry the argument

### Cap-conditioned budget ordering

Put this small table in the main body; each entry is a task count from `final.evidence.episodes`, not a training cost:

| Score table | Local target row | Headroom fraction | Mean | Median | Borda |
|---|---:|---:|---:|---:|---:|
| HELM | 10 | 1 | 9 | 12 | 34 |
| HELM | 10 | 0.5 | 23 | 12 | 39 |
| Open LLM | 1609 | 1 | 2 | 3 | 5 |
| Open LLM | 1609 | 0.5 | 4 | 3 | 5 |

The within-target mean/median ordering reverses in each setting. These are counterexamples to an unconditional ordering, not estimates of reversal frequency in future model populations. Explain them using cumulative score gains versus order-statistic thresholds, not an untested causal account of developer behavior.

Show all sampled targets in the main comparison, not only these examples. Targets were selected as nonwinners under the original **mean**, not under every rule. HELM row 40 already needs zero median updates; retain that zero without attributing it to an intervention.

### Reachability, not fictitious finite budgets

At full headroom, all eight sampled targets per family are reachable under each rule. At half headroom, mean/median/Borda reachability counts are **5/5/4 for HELM** and **7/6/3 for Open LLM**, derived from the original final records. Keep the denominator at eight targets per family, not seeds times targets or controls plus originals.

Report unreachable promotion as a status or infinity. Empty task lists accompanying unattainability are not zero-cost successes. Reference sentinels `d+1` are not investment values. Do not average away unattainable cases or compare finite-only averages without stating the changed population.

### Allocation context and controls

All original reference records in each family report exact bounds; feasible selected allocations match them. Explain the difference between an exact measured instance and a universally exact algorithm. A matched comparator example can show why immediate-gain greedy is not a median certificate: HELM row 28 at half headroom has median cost 21 versus the recorded greedy cost 52. Do not use this isolated comparison to claim general solver superiority.

Selected original allocations repeat across the three recorded seeds. These are repeated static instances, not independently trained models or random population samples. Report repeatability and exact integers; do not invent confidence intervals, significance tests, or population uncertainty. Random-order baseline summaries may use only the recorded orders/seeds with their limited coverage disclosed.

Permutation, constant-score, and zero-update cases are implementation controls. Keep them separate from empirical budget and reachability denominators. A synthetic constant table is not another public benchmark. Do not claim a completed replay result when its retained value is null.

## Required figures and physical layout

`paper.sty` sets a **single 5.5-inch text column and 9-inch text height**. Full text width and column width are therefore the same here; 0.48 text width is not a conference column. All three figures target width fraction 1.0. The generic historical style header does not authenticate the official ICLR 2026 template: verify official venue files before final drafting/submission.

### Figure 1: score-space overview

- **Generator:** `generate-concept-figure`, later orchestrator-owned; do not run it during strategy generation.
- **Content:** public score table and frozen target/rivals, capped target-coordinate updates, the three rules, and minimum task count or unattainability. State that no training is performed. Use an equation and labels, not invented scores.
- **Placement:** page 1 or 2, within the introduction/problem transition.
- **Footprint:** approximately 5.5 by 2.3 inches plus caption, about 0.30 body page.
- **Readability budget:** one panel, at most five major blocks and three rule branches; labels at least 9 pt. The arrows describe the mathematical mechanism, not research chronology.

### Figure 2: paired mean/median budgets

- **Generator:** `matplotlib`; four panels arranged 2 by 2, dataset by response cap.
- **Axes:** exact/bounded minimum mean task fraction on x and median task fraction on y, both on `[0,1]`, with an equality diagonal.
- **Data:** all eight original targets per panel; use no more than four status encodings. Eight points are observations, not eight colored series. Put unreachable cases in separate labeled marginal rails, with a corner category for both unreachable; never place a fabricated finite value on either numeric axis.
- **Annotations:** highlight only the reversal exemplar in each dataset; show multiplicity for overlapping finite points. Do not turn repeated seeds into additional target points.
- **Footprint:** approximately 5.5 by 3.8 inches plus caption, about 0.48 body page. At least 8.5-pt rendered ticks and 9-pt axis labels. Two panels per row, never four across.

### Figure 3: cap-conditioned reachability

- **Generator:** `matplotlib`; two panels, one per dataset.
- **Axes:** three aggregation rules on x; reachable targets out of eight on a common 0-to-8 y axis. Two cap markers per rule and one shared cap legend.
- **Footprint:** approximately 5.5 by 2.0 inches plus caption, about 0.26 body page; labels at least 9 pt.
- **Meaning:** whether co-first is possible under the stated cap. Do not add another definition of success, optimizer scores, controls, or conditional finite-budget averages.

All quantitative figures require source-generated **PDF and 300-DPI PNG**, with LaTeX referencing PDF when available. Keep editable source for the overview and obtain vector export when available. A raster-only full-width figure must be regenerated at **at least 2400 px wide**, never upscaled. Keep at most three panels per row and respect each figure's stricter panel/category/series budgets.

## Body budget and scientific organization

Target approximately **8.75 substantive body pages**, excluding references and supplementary information:

| Component | Inclusive page budget |
|---|---:|
| Title and abstract | 0.50 |
| Introduction, including early overview | 1.00 |
| Related work | 0.50 |
| Problem and intervention assumptions | 0.90 |
| Allocation methods and certificate reasoning | 1.35 |
| Public score tables and comparison protocol | 0.80 |
| Results, including quantitative figures and compact tables | 2.45 |
| Discussion and limitations | 0.90 |
| Conclusion | 0.35 |

The venue requires 8 to 9 body pages; if stopping at eight, page 8 must be at least 75 percent full. These numbers are layout allocations, not empirical findings. Spend space on why task-count support is an investment proxy, endpoint monotonicity, odd/even median mechanics, Borda rival updates, cap-dependent counterexamples, target-sampling asymmetry, and explicit failure conditions. Do not pad with search history, extra decorative plots, spacing tricks, or imagined experiments. If substantive compliance remains impossible, report insufficiency.

Use thesis-first headings: **Problem and Intervention Model**, **Allocation Certificates**, **Public Score Tables and Comparison Protocol**, **Cap-Dependent Promotion Budgets**, and **Scope and Limitations**. Keep the core reversals, reachability failures, and noncausal limitations in the main body.

## Supplementary information after references

The supplement adds auditable depth rather than hiding evidence needed for the thesis. Its authoritative source IDs are listed in the JSON.

1. **Endpoint reduction and scalar budget certificates.** Expand monotonicity and mean, odd-median, and even-median derivations using the selected source and recorded reference checks. No fabricated exhaustive tests or unverified theoretical novelty. Source: `final.evidence.episodes`, with method files as supporting artifacts.
2. **Rival-aware Borda constraints and bounded search.** Give pairwise credit definitions, changed rival totals, integer constraints, witness validation, deadline fallback, and observed reference-bound closure. No later refinements as ablations. Source: `final.evidence.episodes`, with the frozen source implementation.
3. **Complete paired allocation and comparator tables.** Include every original target/rule/cap record, status, task count, normalized cost, bounds, and available greedy/random costs; retain seed-level differences where present. Source: `final.evidence.episodes`.
4. **Matched controls and repeated-execution coverage.** Report control checks and retained failures separately from original data; distinguish repeatability from statistical population uncertainty. Do not fill missing replay evidence. Sources: `final.evidence.episodes` and `final.qualification.*`.
5. **Public snapshots, normalization, and reproduction map.** Document embedded upstream URLs/checksums, HELM v1.13.0 and pinned Open LLM contents revision, score scaling, acquisition dates, clustering/splitting, local hashes, and fixed target selection. Explain uncertain score-data redistribution rights and prefer upstream reacquisition. Map figures/tables to actual scripts, dependencies, commands, and evidence pointers when those scripts exist. Source: `final.evidence.episodes`, plus `task/resources/final/` metadata.
6. **Selection scope and independent final assessment.** A short audit statement of tied search comparison and independent final outcome, not a candidate-by-candidate narrative. Sources: `study.selection_kind`, `study.investigation_outcome`, `study.search_score`, `study.baseline_score`, `study.search_score_delta`, `study.attempts.total/scored/unscored`, and `final.qualification.status/outcome/correct`.
7. **LLM Usage.** Meet the venue requirement with precise documented roles in ideation, candidate-code assistance, query planning, framing, and later writing where actually used. Distinguish evaluator-produced results from assisted interpretation. Do not guess human effort, model identities, or unlogged verification. Sources: `study.selection_kind`, `final.evidence.episodes`, and available execution/source logs for role provenance.

## Limitations and writing safeguards

Essential main-text limitations are the hypothetical independent response cap; no calibrated training-cost interpretation; no transfer, forgetting, or reacting rivals; uniform task costs; co-first rather than strict victory; only two positive caps; normalization-dependent budgets; mean-based target sampling; finite public snapshots; and incomplete model-lineage knowledge. An unattainable result is impossibility **under the stated cap**, not a measured training loss or an invalid solver result.

The final writer should build an extractor from `final.evidence.episodes`, check pairing and bounds, reproduce the displayed examples and counts, and separate originals from controls. Names of future scripts are plans, not existing deliverables. A clean reproduction map, paper figure/table scripts, authenticated venue files, and verified paper-level citations remain to be supplied. Do not claim measured CPU costs from episode duration or the original resource estimate.

The bibliography is not yet a sufficient read-and-verified literature foundation. Many retrieved records are off-topic. `Lanctot2023EvaluatingAU` and `Brandt2016HandbookOC` have exact allowed-seed title matches, but metadata retrieval alone does not demonstrate content reading. Do not cite unrelated hits for padding, invent missing keys, or claim this stage read benchmark papers. Later source consultation must stay within the task's explicit exclusion boundary: exact allowed identifiers only, no citation-graph or related-content expansion, and stop/document accidental prohibited exposure. No external literature retrieval occurred in this framing stage. Do not assert first-ever novelty.

Follow `VENUE.md`: ICLR 2026, anonymous manuscript, no author identities, affiliations, acknowledgements, funding statements, personal links, or internal absolute paths. Verify official template provenance and any actual venue checklist; do not import a checklist from another conference. Include `LLM Usage` after references.

## Forbidden framing

Avoid headings centered on **Search Progression**, **Campaign Phases**, **Milestones**, **Timeline**, **First Success**, **Experiment A / Experiment B**, **Cycle-by-Cycle Improvements**, **Winning Candidate**, and **Architecture Evolution**.

Avoid phrases such as “we then tried,” “first valid result,” “subsequent improvements,” “later variants,” “next-best,” and “search winner.” Do not claim “median is universally more robust,” “Borda is universally safer,” “measured training-data cost,” “proved contamination effectiveness,” “continuous cap frontier,” or state-of-the-art resistance.

Internal labels banned from visible paper prose include `correctness rate`, `correct and eligible`, `eligible`, `combined_score`, `rubric`, `worker_01`, and `worker_02`. Their appearance in this memo is private audit guidance only. If a thresholded metric is used, give it one reader-facing meaning per figure; Figure 3 uses only reachability of co-first under the stated cap.

## Stage completion criteria

Validate the two strategy files for JSON shape, source-ID existence, consistent decisions, example/count grounding, figure budgets, and a nonempty grounded supplement. Do not draft `paper.tex` or `claims_grounding.json`, generate the figures, run new candidate experiments, or invoke final-paper validation in this stage.
