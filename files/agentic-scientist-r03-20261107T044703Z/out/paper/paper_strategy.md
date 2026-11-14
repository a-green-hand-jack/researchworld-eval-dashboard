# Paper Framing Strategy

## Decision

**Status: ready.** Use `paper_standalone` and the `write-paper-standalone` family. Provisional title: **Variance-Guided Benchmark Selection with Masked Low-Rank Score Models**.

**Central question:** Under limited benchmark-query budgets, how well does variance-guided selection with masked low-rank reconstruction predict held-out models' remaining observed scores across model-disjoint and name-family-disjoint leaderboard splits?

**Central thesis:** On the two pinned leaderboard matrices, the retained variance-guided low-rank method has a higher pooled remaining-target prediction score than the tested baselines and loses score under historical-column derangement, supporting a conditional empirical result rather than universal benchmark sufficiency, response-adaptive selection, or fixed-target superiority.

This is an empirical assessment of one retained method, not a story about inventing a winning architecture. MTEB embedding models and Open LLM generative models form **separate evidence blocks under one score-matrix question**. Fit and discuss them independently; do not claim cross-source transfer, merge their model identities, or treat embedding tasks as generative-model benchmarks.

## Framing Alternatives and Staged Inputs

No resolved edit-context files, prior manuscript, `aggregated/`, or `extra_tasks/` are staged. `prior_paper_story_status` is `rejected`: no inherited story is adopted, not a rejection of an old scientific result.

- **Preserve with local updates:** inapplicable because there is no prior manuscript to preserve.
- **Broaden to a shared alternative-method family:** rejected because overlap-shrunk covariance, latent mixtures, and monotone-skill alternatives have no measured performance evidence.
- **Recenter on the retained evaluated method:** selected because it alone has final evidence with meaningful baseline, split, seed, and corruption comparisons.
- **Center a negative search-results paper:** weaker than the selected framing. Unscored alternatives do not establish measured negative performance findings, whereas the retained method has an actual comparative evaluation.

Direct inspection of `source_evidence/downstream/program/src/program.py` establishes masked alternating ridge factors, historical-cell rank selection, conditional ridge prediction, and a trace-reduction query proxy. The selected and original-baseline staged source files are byte-identical. The method is sequential and set-conditioned: purchased score values affect reconstruction **but not query choice**. It is not the response-adaptive mixture or the off-diagonal overlap-aware proposal.

The frozen audit and plan under `task/resources/final/`, the task contract, and the evaluator's score/baseline definitions provide protocol provenance. They do not substitute for registered numerical result sources. Do not assert equality between differently recorded whole-tree hashes merely from equality of the staged source files.

## Private-Only Evidence Ledger

This section is planning/audit context, not reader-facing vocabulary.

- Read `paper_data.json.final_evaluation` independently. `final.qualification.status` is `completed`, `final.qualification.outcome` is `qualified`, and `final.qualification.correct` is true. There is **no failed final qualification** to disclose in this run. Detailed gate diagnostics remain unavailable; successful completion does not establish scientific novelty or stronger validity claims. Candidate diagnostics are explicitly unverified.
- Selection uses `study.selection_kind=baseline` and `study.investigation_outcome=completed_no_winner`. Both search score and original-baseline score are 0.9527030000575736; `study.search_score_delta=0.0`.
- `study.attempts.total=3`, `study.attempts.scored=0`, and `study.attempts.unscored=3`. Unscored attempts are missing performance evidence, not measured losses. Their recorded execution-failure causes are unknown; neither inferiority nor a particular validity/adaptivity defect is diagnosed.
- Keep search and final scopes separate. Never subtract the search score from the final score and call it improvement. Do not display the frozen source as an improved replacement for its identical original baseline.
- Final case data come from `final.evidence.episodes`. The three final seeds are 1009, 1013, and 1019. Exclude control cases from primary comparisons and exclude the replay from every primary aggregate; replay is not a fourth seed.
- Qualification statements must map to `final.qualification.*`, not downstream mirrors or search flags. If later evidence changes the outcome, preserve the changed qualification and its limitations in drafting, review, audit, and revision.

## Method Groups

Keep exactly the six evaluated plot labels; group them scientifically rather than by discovery order.

| Group | Role | Scientific purpose |
| --- | --- | --- |
| Variance-guided masked low-rank reconstruction | Studied method; `proposed` in the JSON contract only | Connect incomplete historical scores, conditional reconstruction, and variance-guided queries; do not imply new architecture or a search gain. |
| Random-query masked low-rank reconstruction | Selector ablation | Same factor-fitting/prediction construction, different query rule; closest comparison and only comparator with supplied pooled paired uncertainty. |
| Information-selected covariance ridge | Strong baseline | Closest pooled nonfactor comparator; representation, tuning, and queries can all differ, so not a matched-query prediction ablation. |
| Correlation-medoid covariance ridge | Simpler baseline | Historical correlation-centrality ordering with covariance reconstruction. |
| Historical benchmark means | Observation-invariant baseline | Expose predictable task marginals; its evaluated remainder still depends on its operational query policy. |
| Random-query mean-offset prediction | Simple observation-using baseline | Test whether a single model-level score offset explains the result. |

Do not add unevaluated methods to the performance comparison. A short supplementary disclosure of alternatives is sufficient.

## Results and Claim Boundaries

### Primary comparison

Show the six methods in each source-by-split condition, displaying every retained seed score. The reader-facing metric is **Normalized prediction score (1 − MAE; higher is better)**. Predictions are clipped to natural score bounds; errors are averaged over available, unpurchased entries within a model and then through the frozen checkpoint/seed/split/source hierarchy. This is not classification accuracy, explained variance, or the fraction of benchmarks successfully recovered.

The pooled scores below already exist in `paper_data.json`; use their `final.metric.*` sources in the eventual claim map.

| Method | Pooled score | Grounding ID |
| --- | ---: | --- |
| Variance-guided masked low-rank | 0.9527636891226994 | `final.metric.combined_score` |
| Random-query masked low-rank | 0.9364101694132948 | `final.metric.random_lowrank_score` |
| Information-selected ridge | 0.9482262260487015 | `final.metric.selected_ridge_score` |
| Correlation-medoid ridge | 0.9327472829724573 | `final.metric.medoid_ridge_score` |
| Mean-offset | 0.920605668187274 | `final.metric.copy_score` |
| Historical means | 0.90687688776656 | `final.metric.constant_score` |

The supplied paired family-clustered interval **against random-query low-rank only** is [0.014807167765235746, 0.01847801943997085], grounded in `final.metric.paired_gain_ci_low` and `final.metric.paired_gain_ci_high`. Explain its fixed resampling definition from the final plan. Do not recalculate it from seed means or attach it to another comparator or subgroup. Other baseline differences are observed-score comparisons, not established statistical superiority.

Retain the local reversal: for Open LLM, family split, seed 1019, the studied score is 0.9531041725072664 versus 0.9533160599665489 for information-selected ridge (`final.evidence.episodes`). The method is not best in every retained cell.

The source-level pooled scores are 0.9468974985138557 for MTEB and 0.9586298797315429 for Open LLM (`final.metric.mteb_score`, `final.metric.open_llm_score`). They have different task and budget regimes; do not interpret their difference as a controlled source-difficulty result.

### Historical-dependence control

Compare actual and independently column-deranged historical training with paired seeds within each source/split. The pooled deranged score is 0.9233917542059907, with an actual-minus-deranged gap of 0.029371934916708625 (`final.metric.permuted_score`, `final.metric.corruption_gap`). This supports use of historical cross-benchmark alignment. It does not uniquely identify the acquisition rule as the cause, certify leakage absence, or establish arbitrary out-of-distribution generalization.

### Essential limitations

Put these in the body, not only after the references:

- Query policies leave different target sets. Results compare the observed remaining-target objective, not prediction error on an identical untouched panel; there is no fixed-target control.
- The selector ignores purchased values. Do not claim response-adaptive query design.
- Historical-cell rank validation is not nested held-out-family validation. Name-family grouping is heuristic and may miss cross-namespace lineages.
- Leaderboard missingness is observational and potentially selective. Missing entries are not measured targets or measured failures.
- The two independent source fits do not demonstrate transfer across domains. MTEB studies embedding tasks; Open LLM covers its own small benchmark suite.
- No universal sufficient budget, tolerance-defined sufficient budget, actual benchmark-inference savings, new-model inference run, rank sweep, missingness sweep, calibration experiment, or nonlinear-method victory is established.
- Execution/replay checks and reported qualification do not remove these scientific limitations.

Budget evidence belongs in a substantive supplementary table: retained studied-method checkpoint arrays only, mapped to MTEB budgets 1/2/4/8 and Open LLM budgets 1/2/3 using the frozen plan. Do not invent baseline checkpoint curves or a threshold answering how large a budget is universally enough.

## Required Figures and Layout

Inspected `.codex/skills/write-paper-standalone/templates/iclr/paper.tex` and local `paper.sty`: the document is an `article` with **one column, 5.5in text width, and 9in text height**. Full text width is also the column width; this is not a two-column conference layout. All three figures target `1.0\textwidth`. A nominal 0.48-width figure would be an inset, not an ordinary conference column, and is too narrow for the planned labels.

### Figure 1: Score-matrix mechanism overview

- **Purpose:** immediate glance value for the object and mechanism, including the boundary between query choice and observed-score conditioning.
- **Type/generator:** qualitative `diagram`, `generate-concept-figure`; the only figure assigned that generator.
- **Content:** incomplete historical matrix → masked factor estimation → budgeted query set and purchased values → remaining-score reconstruction. Use separate arrows to show that purchased values update prediction, not selection. A short footer distinguishes source-specific fits and the two split regimes. Symbolic matrix cells are allowed; invented numeric pseudo-results are not.
- **Placement/footprint:** page 1 or 2, approximately 5.5 × 1.7in before caption; roughly one quarter page including caption.
- **Readability budget:** one panel, one panel per row, at most six labeled elements, at most three arrow/semantic styles, minimum 9pt rendered text. Full width is needed for the four-part information flow.
- **Grounding:** `final.evidence.episodes`, `study.selection_kind`; implementation provenance is the staged selected source and frozen final plan. No metric is plotted.

### Figure 2: Source- and split-stratified method comparison

- **Type/generator:** horizontal dot plot, matplotlib.
- **Content:** source-by-split 2 × 2 grid. Each panel has six abbreviated method rows, three seed dots, and a distinct mean marker. Use a shared expansion key and consistent score-axis meaning. This uses actual, nonreplay case scores from `final.evidence.episodes` only.
- **Placement/footprint:** results section; 5.5 × approximately 3.7in before caption, roughly half a page including caption. Each panel needs both readable method names and a meaningful score scale; do not shrink the whole figure to an inset.
- **Readability budget:** four total panels, two per row, six categories per panel, four series maximum counting the mean; minimum 8.5pt rendered text. Explicitly label any nonzero axis limits; dots avoid truncated-bar exaggeration.
- **Uncertainty:** seed dots show observed variation, not confidence intervals. The supplied pooled interval belongs in the pooled table/text, not on these subgroup points.

### Figure 3: Dependence on historical alignment

- **Type/generator:** paired-condition dot plot, matplotlib.
- **Content:** two source panels; each shows model-disjoint and name-family-disjoint splits under actual versus column-deranged training. Pair the same seeds, omit replay, and use exactly two condition legend entries. Paired links mark a controlled comparison, not elapsed time.
- **Placement/footprint:** next to the dependence-control discussion; 5.5 × approximately 2.1in before caption, about 0.3 page including caption.
- **Readability budget:** two total panels, two per row, two categories per panel, two series per panel; minimum 8.5pt text. No additional baseline series.
- **Grounding:** `final.evidence.episodes`, `final.metric.permuted_score`, `final.metric.corruption_gap`.

None of the figures is a search trajectory or milestone plot. Do not add a required budget curve when comparator checkpoint values are absent. A compact pooled table and a small protocol table complement the figures without duplicating their visual comparisons.

**Vector-first export:** quantitative source must emit PDF and 300-DPI PNG; LaTeX must use PDF whenever available. Keep the concept diagram editable in draw.io and export PDF. Raster-only full-width assets require at least 2400px width; any genuine column-width alternative requires at least 1200px. Regenerate from source rather than upscale. Simplify labels/panels if final-size text fails the stated budgets.

## Body-Page Plan

Follow `VENUE.md`: ICLR 2026, anonymized review submission, **8–9 body pages excluding references**, with the last page at least 75% full if the body occupies eight pages. Target 8.5 pages. The allocations already include figures and tables:

| Material | Target pages | Scientific use of space |
| --- | ---: | --- |
| Title and abstract | 0.45 | Question, conditional evidence, key scope boundary. |
| Introduction and early overview | 1.05 | Budgeted evaluation problem, precise empirical contribution, domain distinction. |
| Related Work | 0.65 | Verified permitted low-rank/design context and benchmark-evaluation distinctions, not retrieval-list filler. |
| Problem and Scope | 0.65 | Historical masks, availability, purchased versus remaining targets, exact objective. |
| Masked Low-Rank Selection and Reconstruction | 1.65 | Objective, alternating updates, rank validation, conditional reconstruction, acquisition proxy and its limits. |
| Evaluation Design | 1.00 | Source-specific splits, five operational baselines, controls, weighting, supplied uncertainty. |
| Prediction and Historical-Dependence Results | 1.80 | Two direct comparison figures, compact pooled table, heterogeneity and local reversal. |
| Discussion and Limitations | 0.95 | Method-dependent targets, selective missingness, family heuristics, restricted inference about budgets. |
| Conclusion | 0.30 | One conditional conclusion; no new claim. |

Use any layout slack for clearer equations, baseline definitions, and target-policy/uncertainty explanation. Do not pad with unmeasured proposals, repeated pooled scores, broad surveys, operational logs, or speculative experiments. If evidence cannot fill the requirement substantively after typesetting, report that limitation rather than invent content.

The supplied template scaffold contains an identifying author and a final-copy command. The later writer must remove identifying manuscript content, follow review formatting, preserve the orchestrator watermark, and omit acknowledgements/funding. Do not assert that the locally staged style has been independently verified as the latest official release. A separate **LLM Usage** section is required and may be after the references.

## Supplementary Information After References

**Purpose:** provide reproducible method/protocol depth and complete retained evidence without hiding anything essential to the thesis. The JSON gives the following exact planned subsection headings and grounding IDs.

1. **Masked Factor Estimation and Conditional Querying.** Expand the inspected equations, fixed means, zero-filled centered initialization, alternating ridge updates, rank selection, and exact acquisition proxy. The current-target proxy includes the candidate coordinate; do not describe it as pure off-diagonal risk reduction or an MAE-optimal theorem. A rank-one covariance identity can explain the code, not prove empirical optimality. IDs: `study.selection_kind`, `final.evidence.episodes`; staged source provides implementation provenance.
2. **Pinned Data Extraction, Grouping, and Reproduction.** Use existing audit/plan/contract/requirements for revisions, extraction, deduplication, masks, heuristic families, budgets, environment and exact reproduction commands. Do not invent script names, observed storage, or runtime measurements. Register audit/plan linkage before asserting extra quantitative dataset counts. Respect Open LLM's undeclared dataset license and reacquisition rather than asserted redistribution rights. IDs: `study.selection_kind`, `final.evidence.episodes`, `final.qualification.status`.
3. **Complete Seed, Split, and Budget Tables.** All nonreplay actual/control scores, five baseline scores, and studied checkpoint arrays; no invented comparator checkpoint values or new experiment. Retain the local ridge reversal and distinguish seed variation from confidence intervals. ID: `final.evidence.episodes`.
4. **Aggregation, Uncertainty, and Evaluation Boundaries.** Frozen weighting and family-clustered paired uncertainty; no interval reconstructed from seed means. Explain unavailable fixed targets, heuristic families, selective missingness, historical-cell validation and limited validity checks. IDs: `final.metric.paired_gain_ci_low`, `final.metric.paired_gain_ci_high`, `final.metric.reset_replay_ok`, `final.qualification.outcome`, `final.evidence.episodes`.
5. **Unmeasured Alternatives and Evaluation Provenance.** Brief selection/failure disclosure without an alternative-method leaderboard. Record unchanged original-baseline selection, zero measured search change, three missing scores, unknown failure causes, and independent final completion/qualification. IDs: `study.selection_kind`, `study.investigation_outcome`, `study.search_score_delta`, `study.attempts.total`, `study.attempts.scored`, `study.attempts.unscored`, `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`. Translate machine fields into reader-facing language.
6. **LLM Usage.** Describe documented agent-assisted ideation/implementation and framing/writing precisely; distinguish unscored alternatives from evaluated retained code. Do not invent human supervision, literature verification, or experiments. The writer must add its actual subsequent role. IDs: `study.attempts.total`, `study.attempts.unscored`, `study.selection_kind`; the current task also documents the framing-agent role.

Later authoritative appendix rankings can route additional grounded material here; do not modify the strategy retroactively or move essential counterevidence out of the body.

## Literature and Claim Discipline

The current `references.bib` and `references_provenance.json` contain factorization-related metadata but not the allowed starter/dataset records needed for a grounded domain review. Retrieval metadata alone does not establish that the paper was read, that it is relevant, or that any novelty contrast is supported. Do not cite unrelated applications merely to fill the bibliography. Before final writing, resolve genuinely needed allowed records with exact permitted titles/identifiers, verify provenance and content, and cite only keys actually present in the bibliography. Never infer the identity of the forbidden prior paper, search for it, or expand citation graphs; stop and log any accidental exposure. This framing stage performs no network lookup.

Keep reader-facing prose free of private pipeline terms and paths. Distinguish an observed pooled advantage from a statistically supported paired contrast, a useful implementation identity from a new theorem, and publication eligibility from scientific qualification. No newly invented experiment or citation is needed to make this conditional empirical story coherent.

## Wording to Reject

Forbidden headings: **Search Progression; Campaign Phases; Milestones; First Successful Run; Experiment A / Experiment B; Candidate Leaderboard; From Baseline to Winner; Correctness and Eligibility.**

Forbidden visible phrases: **we then tried; first valid result; subsequent improvements; next-best candidate; winning search method; all alternatives performed worse; correctness rate; correct and eligible; eligible; worker_01; worker_02; combined_score; rubric; state of the art; response-adaptive benchmark selection; a universal sufficient number of benchmarks; proved leakage-free; significantly better than every baseline.** Source identifiers appearing in this private memo are not recommendations for manuscript wording.

This stage writes only the strategy artifacts and append-only memory. It does not draft `paper.tex`, write `claims_grounding.json`, generate final figures, run experiments, or run final-paper validation.
