# Paper Strategy: Frozen-Score Mean Inference

## Decision

**Status:** ready. **Family:** `paper_standalone`, compatible with `write-paper-standalone`.

**Provisional title:** *Frozen-Score Mean Inference: Width Gains and Coverage Limits*.

**Central question:** With labels, unlabeled scores, and the predictor fixed within each comparison, what interval-width gains and coverage limitations does honest score calibration exhibit for a binary population mean relative to prediction-powered and labeled-only intervals?

**Central thesis:** Across seven evaluated binary-mean conditions, honest score calibration has a small paired width advantage over the evaluated PPI++ comparator in only one condition; rare-outcome interval collapse shows why widths need coverage uncertainty and an exact-binomial reference alongside them.

This is a standalone empirical/methodological limitations paper, not a claim of universal improvement or a demonstration that nonlinear calibration caused the observed gain. The shared object is binary superpopulation-mean inference from immutable inputs. Present neutral conditions C1-C7 as evidence blocks under that question, not as named application studies or chronological experiments.

## Evidence and Qualification

Read `paper_data.json.final_evaluation` independently. It reports a completed, qualified final evaluation. The authoritative qualification anchors are `final.qualification.status`, `final.qualification.outcome`, and `final.qualification.correct`; no failed final qualification is reported here. This status is not a guarantee of nominal statistical coverage. Missing gate-specific diagnostics remain unknown, and neither replay flags nor unverified candidate diagnostics prove statistical validity. If later authoritative evidence changes qualification, preserve the reported outcome and limitations through writing, review, audit, and revision without guessing the cause.

The numerical anchor is `final.evidence.episodes`: 256 seeded repetitions, each containing seven conditions and paired candidate/baseline intervals. The aggregate case summaries occur only at `episodes[0].solution.case_summaries`; individual records are under `episodes[*].solution.cases`. All seven coverage summaries, paired mean width differences, and baseline zero-width counts were checked against those records. The diagnostic-trust annotation is `unverified`; the plan relies on recorded endpoints, truths, and comparisons, not on candidate-supplied validity assertions.

The final aggregate coverage is **0.9425223214285714** and mean width **0.12988779848794016** (`final.metric.coverage`, `final.metric.mean_width`). These are descriptive, not proof of 95% validity. Do not treat all seven within-seed cases as independent when constructing aggregate uncertainty. Per-condition candidate coverage ranges from **0.9296875** to **0.95703125**; every reported candidate coverage interval includes 0.95. Non-rejection is not equivalence or validation of nominal coverage.

`downstream_study` and `study.*` grounding sources are absent. Omit search-score deltas, scored/unscored attempt accounting, and superiority to an original search incumbent. Missing evaluations are not measured losses. The measured PPI++ comparator is not automatically the original search incumbent. Internal selection metadata is private provenance, not a visible paper result.

## Framing Alternatives and Edit Decision

No resolved edit-context files, `previous_paper/`, `aggregated/`, or `extra_tasks/` are staged. This is fresh framing, not an update to a prior manuscript. The JSON enum is **recentered** only to describe recentering the broad task opportunity around the actual final evidence; it does not assert a prior paper existed.

- **Preserve a generic improvement story:** reject. Only one condition is narrower than evaluated PPI++; finite-sample validity of the returned method is not established.
- **Broaden to a shared family of searched methods:** reject. Other branches do not supply the necessary measured comparisons; source-only functions and unsuccessful executions are not performance evidence.
- **Center the evaluated score-control method's width/coverage limits:** select. It has repeated paired measurements, uncertainty, a small isolated gain, widespread modest costs, and an informative low-mean failure comparison.

The selected candidate source is under `results/ideas/02_honest_nonlinear_score_controls_with_a_finite_sample_safety_track/program_1/src/`, linked by `result.top_program_01`. Inspect `program.py`, `METHOD.md`, and `study.py` directly for implementation facts. The final evidence records a frozen program-tree digest, but a separate final source tree is not staged for file-by-file comparison. The candidate's preparation notes predate execution; final episode records supersede their absence-of-results statements, not their warnings about asymptotic versus safety intervals.

## Method Groups

1. **Honest frozen-score controls — proposed.** Two-fold complementary-label calibration; ridge affine and small piecewise-linear spline candidates selected by training-only GCV; clipped controls; finite-unlabeled-sample factor `rho=N/(n+N)`; residual correction. The evaluated output is a Wilson-style stabilized asymptotic Wald interval, with a size-only Clopper-Pearson branch for fewer than 16 labels. Do not call the general procedure exact or an exact Wilson interval.
2. **Evaluated PPI++ mean interval — primary baseline.** The paired efficiency comparison is central. Restrict claims to this evaluated comparator rather than all implementations of the published method.
3. **Evaluated PPI mean interval — baseline.** Retain in the main table, rare-outcome plot, and complete supplement. Its behavior differs materially from PPI++.
4. **Labeled-only asymptotic mean interval — baseline.** Separates gains over label-only normal inference from gains over prediction-powered inference.
5. **Labeled-only exact binomial interval — baseline.** Finite-sample reference under iid Bernoulli sampling, not permission to transfer its guarantee to another estimator.
6. **Bounded componentwise safety construction — supporting theory only.** The source implements empirical-Bernstein component intervals and union-bound/fixed-weight aggregation separately. It was not the measured primary output; do not assign it empirical coverage or width.

Exclude partition portfolios and likelihood branches from the main comparison. An affine-only matched calibration function exists but has no measured ablation in the supplied evidence. Likewise, the oracle frontier and safety helper are not executed evidence of superiority.

Keep the target **E[Y]**, not the realized finite-pool mean. Inputs are fixed across methods within each repetition; frequentist uncertainty is over repeated draws. Common-population iid sampling and a predictor frozen independently of inference labels are assumptions, not established facts about unidentified generators. Explain the fixed-control variance decomposition, conditional-mean oracle, affine projection gap, and fold-variance approximation with their separate assumptions. A fixed clipped spline dictionary need not attain the oracle; cross-fitting does not make folds unconditionally independent.

## Results That Carry the Story

Use `final.evidence.episodes` for this entire section. Retain C1-C7 identifiers: the records do not identify datasets, generators, or case-specific sample sizes. Do not infer a nonlinear, shifted, or adversarial regime from a result pattern.

- **One small PPI++ width gain:** in C2, candidate-minus-PPI++ mean width difference is **-0.00030173260155952255**, with reported 95% interval **[-0.0004003584986521721, -0.000203106704466873]**. The other six differences are positive. These are pointwise, condition-specific findings, not multiplicity-adjusted general improvement or evidence attributing the effect to splines.
- **Label-only context:** C1-C3 are narrower than labeled-only asymptotic inference; C4, C6, and C7 have small width increases against that baseline. Report the exact-binomial and PPI comparisons too, rather than selecting only favorable baselines.
- **Rare-outcome diagnostic:** C5 records truth **0.006800000000000005**. PPI++ and labeled-only asymptotic coverage are each **0.55078125**, with **115** zero-width intervals each. Candidate coverage is **0.9296875**, with no zero-width intervals; exact-binomial coverage is **0.99609375**. PPI has two zero-width intervals. Collapse and undercoverage are observable; the evaluator's internal cause for every miss is not identified.
- **Exact reference remains important:** in C5, candidate-minus-exact mean width difference is **-0.000046988429386779555**, with interval **[-0.00032065914173324357, 0.0002266822829596845]**. This width comparison is inconclusive. The candidate's absence of collapsed intervals does not establish nominal validity or superiority to exact inference.
- **Avoid unstable ratio headlines:** the retained aggregate width ratio is **64175.10539621905**. Zero and near-zero comparator widths make ratio summaries scientifically misleading; foreground paired differences and raw width distributions. Do not infer the evaluator's denominator regularization.

The main table must include all five evaluated inferential methods. Split coverage and width blocks if necessary. Keep the C2 gain, six PPI++ widenings, C5 collapse counts, and candidate coverage caveat in the main body. The `[0,1]` sanity interval is not a headline efficiency baseline. Do not translate evaluator flags into scientific validity claims.

## Figures and Practical Geometry

Inspected `paper.sty` and `.codex/skills/write-paper-standalone/templates/iclr/paper.tex`. The style has **one 5.5-inch text column and 9-inch text height**. There is no two-column body: all required figures use full text width, not `figure*` to span nonexistent columns. The scaffold's author and final-copy mode must be replaced for anonymous review during later drafting. Practical geometry does not certify the official 2026 template version; verify that provenance before submission.

### Figure 1 — `frozen_score_overview`

Required early conceptual diagram; generator **`generate-concept-figure`**. Place on page 1 or 2, preferably page 2 beside the problem definition. Target **5.5 × 1.8 inches**, full text width, approximately one quarter page including caption. Five grouped objects show immutable inputs, complementary-fold fitting/evaluation, residual correction targeting E[Y], the evaluated stabilized primary interval, and a separate unmeasured safety construction. Use solid versus dashed connectors for evaluated versus theoretical paths, not chronological discovery arrows. No predictor retraining or empirical-gain badge.

Readability budget: **one panel, one panel per row, at most five object groups, three semantic series, labels at least 9 points**. Half-width would crowd fold isolation and track distinctions. Grounding: `result.top_program_01` for the source path, `final.evidence.episodes` for which primary output was measured. Retain editable draw.io output and prompt log; no figure generation occurs in this stage.

### Figure 2 — `coverage_width_comparison`

Required matplotlib composite; target **5.5 × 4.3 inches**, full text width, approximately three fifths page including caption. Use a **2 × 2 grid**: coverage left, paired width differences right; C1-C4 in the upper row, C5-C7 below. Keep fixed case order, not performance ranking. Each panel has at most four conditions, so seven cases do not crowd one axis.

Coverage series: candidate, evaluated PPI++, labeled-only asymptotic, exact binomial. Show the reported coverage uncertainty and 0.95 reference. Difference series: candidate minus PPI++, labeled-only asymptotic, and exact; show reported uncertainty and zero reference. Negative means narrower, not automatically valid. PPI remains in the main table and rare-case figure. Clearly labeled different linear scales are permissible across width panels because C5 is much larger.

Readability budget: **four panels, two per row, four categories per panel, four series maximum; final labels at least 8.5 points**. Approximately 2.4-inch subpanels, concise case labels, and shared legends make this possible without shrinking. Grounding: `final.evidence.episodes`, particularly the single attached set of case summaries. Explain that the uncertainty is pointwise, not simultaneous.

### Figure 3 — `rare_outcome_diagnostic`

Required matplotlib diagnostic; target **5.5 × 2.2 inches**, full text width, approximately one third page including caption. Two side-by-side panels show C5 empirical interval-width CDFs and zero-width counts for candidate, evaluated PPI++, evaluated PPI, and exact binomial. Retain the mass at zero on a linear width axis. Mention the labeled-only asymptotic baseline's matching 115 collapses in the caption and main table. Put coverage and its uncertainty in adjacent main text, not only the supplement.

Readability budget: **two panels, two per row, four method categories, four series; final labels at least 8.5 points**. Full width gives each panel enough room for axes and method labels. Grounding: all 256 C5 endpoint records in `final.evidence.episodes`. Do not imply the collapse diagnostic establishes the internal cause of every coverage miss.

### Export Contract

Quantitative plotting source emits **PDF and 300-DPI PNG**, and LaTeX references the PDF whenever available. Preserve editable concept output and export PDF when possible. For truly raster-only figures, regenerate at **at least 2400 pixels wide full-width or 1200 pixels wide column-width**; never upscale an existing raster. Use consistent method colors and validity labels. Exactly one overview uses `generate-concept-figure`; follow its later orchestration handoff rather than rendering it during strategy generation.

## Body Budget and Organization

Target **8.5 pages excluding references**, with figure footprints included:

| Scientific content | Planned pages |
| --- | ---: |
| Abstract, introduction, concrete contributions | 1.25 |
| Problem and related work, including early overview | 1.25 |
| Honest controls and limited theoretical analysis | 2.00 |
| Evaluation design and provenance limitations | 1.00 |
| Direct coverage/width comparison and compact table | 1.75 |
| Rare-outcome analysis | 0.75 |
| Limitations and conclusion | 0.50 |

Suggested thesis-first headings: **Introduction; Problem and Related Work; Honest Frozen-Score Controls; Evaluation Design; Coverage and Width Across Conditions; Rare-Outcome Limits; Discussion and Limitations; Conclusion**. Additional space buys precise estimands, fold isolation, calibration/stabilization detail, comparator uncertainty, and a checked variance argument—not new experiments or a history of discarded approaches.

The venue requires 8-9 body pages; if exactly eight pages, the final page must be at least 75% occupied. These are planned allocations, not a claim that pagination has been validated. Do not pad to meet them. Explicitly retain missing nonlinear ablation, unmeasured safety intervals, unidentified generators/sample sizes, narrow binary scope, no distribution-shift validation, and incomplete end-to-end reproduction.

## Supplementary Information

After references use a page break, appendix mode, and **Supplementary Information**. Its purpose is audit depth and substantive methods, not hiding central limitations. The following mirrored JSON entries are grounded in existing artifacts:

1. **Complete paired interval comparisons** (`final.evidence.episodes`). All seven conditions and all recorded comparators, coverage limits, paired width differences and limits, ratio diagnostics distinguished from ratio-of-means, and zero-width counts. Document formulas for derived tables. Never duplicate the first episode's aggregate summaries across repetitions.
2. **Calibration and interval implementation** (`result.top_program_01`, a path anchor). Use the linked `program.py` and `METHOD.md` for fold generation, train-only knots, ridge/GCV, clipping, rho weighting, approximate variance, stabilization, and the size-only exact fallback. Affine-only and safety functions are available but unmeasured; the scalar selection score does not substantiate implementation properties.
3. **Fixed-control variance and separate safety argument** (`result.top_program_01`, linked method sources). Check the decomposition, conditional-mean oracle, and affine projection gap under explicit assumptions. Explain componentwise bounded concentration, union bounds, fold dependence, and nonnegative endpoint weights. This is not observed oracle attainment or validity of the returned asymptotic interval.
4. **Evidence extraction and reproducibility boundaries** (`final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`, `result.top_program_01`). Record hashes, seeds, truths, endpoint extraction, and table/figure scripts. Retain qualification and diagnostic-trust annotations. Recreating figures from records is possible; case generators, case-specific n/N values, and a separately staged final source tree are not recoverable here. Study helpers are not an executed complete experiment runner.
5. **LLM Usage** (`result.top_program_01`, `final.evidence.episodes`, with role descriptions from visible task/source-preparation records). Disclose agent-assisted ideation, implementation preparation, reference planning, and framing/writing accurately; distinguish those roles from automated evaluation. Do not invent model identifiers, human checks, or claims of LLM-verified coverage.

Later authoritative appendix-ranked analyses go here without retroactively altering this plan. Never move the isolated gain, widening, rare-outcome failures, or nominal-coverage caveat out of the main paper.

The machine-readable figure type for both quantitative groups is the canonical schema value `composite`; the forest comparison and ECDF/collapse designs above remain unchanged.

## Literature, Anonymity, and Handoff

`references.bib` and `references_provenance.json` exist, but central permitted PPI/PPI++ starter sources and exact-binomial/empirical-Bernstein foundations are missing. DML and GCV metadata are relevant leads, not proof of source consultation; GCV's venue field needs checking. Before final writing, consult exact allowlisted starter/foundational works and verify citation metadata. Do not invent keys or pad related work with off-topic retrieval hits. Do not guess or search for the prohibited paper, traverse citation networks, or inspect ambiguous follow-up material. This framing stage performs no retrieval and does not claim that metadata is reading.

The venue is **ICLR 2026, anonymous conference review**. Remove names, affiliations, acknowledgements, funding, identifying links, and final-copy mode from the seeded scaffold later; preserve the orchestrator-owned watermark block. Include the separate LLM Usage disclosure. Do not falsely certify the old-looking staged style as the official current venue release.

This stage writes no `paper.tex`, no `claims_grounding.json`, and no figures, and runs no final-paper validation. Check only strategy structure, source references, consistency, and stage boundaries. Missing experiments remain missing, not promises converted into completed work.

## Diary and Overclaim Guardrails

Forbid headings centered on **Search Progression, Campaign Phases, Milestones, First Valid Result, Iteration History, Experiment A / Experiment B, Winning Program, Universal Improvements**.

Forbid visible phrases **we then tried; subsequent improvements; next-best; later variants; first valid result; correctness rate; correct and eligible; eligible; combined_score; rubric; worker_01; worker_02; uniformly narrower valid intervals; 95% coverage is established because it was not rejected; cross-fitting guarantees finite-sample validity; the spline component caused the gain; unscored attempts were measured losses; state of the art**. Internal selection identifiers in this memo are private provenance only, never recommended reader-facing language.

The framing wins because it uses the strongest paired final evidence, preserves unfavorable comparisons, and identifies a useful limitation without inventing a mechanism, a dataset, a universal winner, or an exact guarantee. No failure reason applies to this bounded strategy; bibliography and reproduction gaps remain explicit final-manuscript limitations or remediation requirements.
