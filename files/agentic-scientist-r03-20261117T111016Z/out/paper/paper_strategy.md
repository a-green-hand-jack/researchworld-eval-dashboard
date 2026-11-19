# Paper Framing Strategy

## Decision

**Ready — `paper_standalone`, ICLR 2026.** Provisional title: **Local Residual Transfer for Budgeted Embedding Benchmark Prediction**.

**Central question:** How accurately can a sparse historical embedding-score matrix and one to eight queried scores predict a held-out model's sealed benchmark scores under model and heuristic-family holdouts, and how does disrupting historical score structure change that accuracy?

**Central thesis:** On the pinned MTEB observed-score evaluation, the frozen low-rank predictor with cross-fitted local residual transfer has lower aggregate MAE than the five evaluated baselines and decreasing aggregate error across the tested budgets; historical-data disruptions expose limits to this advantage without isolating residual transfer's contribution.

This is one scoped empirical method study, not a search diary, a proof of optimal selection, or evidence about executing benchmarks on generative LLMs. The two holdouts are evidence blocks under one research question. A negative control result is part of the scientific conclusion, not discarded evidence.

## Framing Alternatives and Input Impact

There is no resolved edit context, `previous_paper/`, prior manuscript, `aggregated/`, or `extra_tasks/` here. The JSON's `prior_paper_story_status: rejected` means rejecting an assumed inherited story, not claiming a manuscript was replaced. The original task is provenance, not permission to retain its broad generative-model scope.

- **Search-success narrative: reject.** Selection order is not the scientific object, and development comparisons are not independent final comparisons.
- **Shared cross-setting method-family narrative: reject.** Only one pinned embedding dataset is supported; its holdout/control conditions are not separate datasets or domains.
- **Scoped prediction-and-limits narrative: select.** It links the available implementation, final comparisons, budget dependence, uncertainty and disruption controls without requiring new experiments.

`paper_data.json.downstream_study` is absent. The independent `final_evaluation` is completed and qualified, grounded in `final.qualification.status` and `final.qualification.outcome`. Successful protocol completion is not proof of novelty, universal validity or superiority. No failed final qualification is present in this run. If a later audit retains metrics but reports `not_qualified`, that failure and unknown diagnostics must survive the abstract, main results, limitations, review and revisions; do not explain it as a performance or adaptivity failure without evaluator evidence.

Private selection provenance directly identifies `results/ideas/02_cross_fitted_local_residual_medians/program_1/src/program.py` and its `RESIDUAL_METHOD.md` through `result.best_correct_score` and `results/best_program_manifest.json`. There is no new staged setting to privilege. The final MTEB manifest fixes revision `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`, 126 final-plane rows and 135 task/subset columns. These are text-embedding model results, not 135 independent benchmark suites or the full public leaderboard.

References and provenance files exist, but metadata retrieval is not equivalent to reading the papers. No existing figure asset is assumed. This stage generates neither a manuscript nor figures.

## Method Groups and Claim Boundaries

1. **Studied method:** observed-entry ridge ALS; greedy all-column posterior-variance-reduction queries; new-row ridge inference; overlap-aware kernel-weighted cross-fitted residual medians; history-only tuning with an exact zero-blend fallback. Explain the evaluated package.
2. **Low-rank baselines:** random-query and historical-variance-query low-rank prediction. Their different query policies prevent interpreting them as residual-only ablations.
3. **Linear transfer baseline:** ridge regression from variance-ranked queried scores, with missing centered historical values filled by zero as implemented.
4. **Simple references:** historical column means and a constant prediction equal to the new model's observed-score mean. Include both in the main table, including the weak reference.
5. **Supporting conditions:** constant historical observed values and independent cyclic shifts of each column's value/mask pairs. These alter historical data, not a single estimator component.

Describe rank four, ridge 0.1, the source-defined fit/calibration caps and tuning grid from inspected code; do not present resource caps as measured time. Explain shared-anchor distances, donor overlap weights, finite observed donor residuals, weighted medians, effective-count shrinkage, and clipped outputs. Separate historical folds from the held-out new model. The selector sums gains over all columns; it is not the discarded self-excluding transfer-only selector and does not use revealed score values to choose subsequent indices.

Contribution claims should be limited to a fully specified estimator, an observed-support comparison with common sealed targets, and explicit disruption-based empirical boundaries. No matched final residual-off, unconditional-residual, donor-score-only or support-gating ablation is available. Training diagnostic code is not unbiased outer evidence. Do not claim residual correction causes the gain, optimal selection, new theory, or firstness. An algebraic explanation of the implemented estimator is useful; a new statistical guarantee is unsupported.

## Results That Carry the Story

### Primary Comparison

Use a fixed-order main table with all five baselines and the studied method, showing aggregate and condition-specific sealed-target MAE. The selected method's retained overall values are:

| Quantity | Retained value | Grounding source |
| --- | ---: | --- |
| MAE | 0.040807843083862115 | `final.metric.mae` |
| Minimum aggregate baseline MAE | 0.045249969215420516 | `final.metric.baseline_mae` |
| Baseline-minus-method MAE | 0.004442126131558401 | `final.metric.delta_best_baseline` |
| RMSE | 0.06432104648676243 | `final.metric.rmse` |
| Reported lower gain bound | 0.0021032442082077377 | `final.metric.gain_ci_low` |
| Reported upper gain bound | 0.009199712663056218 | `final.metric.gain_ci_high` |

The baseline minimum is taken after overall aggregation, not selected independently for each row or budget. No baseline RMSE is retained in the comparison arrays, so do not invent it. Do not combine search scores with this table or replace the frozen selection post hoc.

### Budget and Holdout Views

The pooled MAEs for budgets 1, 2, 4 and 8 are respectively 0.04523334197776794, 0.0422085090615931, 0.03963906108320536 and 0.03615046021288207 (`final.metric.mae_k1`, `final.metric.mae_k2`, `final.metric.mae_k4`, `final.metric.mae_k8`). Generate separate model-holdout and heuristic-family-holdout views from `final.evidence.episodes`; report each comparator rather than assuming superiority at every budget.

The three final seeds are 6841, 8089 and 9011. Seed variation is descriptive: rows and components recur, so these are not three independent datasets. Explain common sealed targets, uniform target averaging within row, equal row weights within episode, equal checkpoint weights, equal seed weights and equal primary-condition weights. The all-unqueried diagnostic has a query-dependent target set and is not the primary fair-comparison metric. A budget-response plot is a direct design comparison, not an optimization trajectory. No specified accuracy tolerance establishes that eight queries are sufficient.

### Uncertainty and Controls

The evaluator uses 400 paired component multinomial resamples with RNG 424242 and shared multiplicities across methods, conditions and seeds. It forms five baseline-specific intervals using quantiles 0.005/0.995 under its Bonferroni construction, then reports minima of the lower bounds and minima of the upper bounds. State this exact construction rather than labeling the supplied pair as a conventional single-comparator 95% interval. Explain finite bootstrap resolution and dependence. Candidate self-diagnostics remain unverified; the row/checkpoint losses here are evaluator-computed, as checked in `task/evaluate_final.py`.

Constant-history MAE is 0.06436711309859705 (`final.metric.constant_control_mae`); column-shifted-history MAE is 0.06856952089296987 (`final.metric.permuted_control_mae`). Compare controls against their matched model-holdout condition, not the pooled two-condition primary result. Retained arrays show no advantage over the column-mean reference under column-shifted history. Keep this boundary in the main results and conclusion. Constant observed values preserve missingness; shifts preserve each column's value/mask marginals while breaking row alignment. Neither manipulation isolates residual transport nor proves a causal or hidden-adaptivity explanation.

## Figures, Readability and Placement

The inspected `paper.sty` sets a **single 5.5-inch text column** (about 397.5 TeX points) and a 9-inch text height. Full-width and column-width have the same maximum physical span; do not assume a two-column `figure*` layout. Legacy comments in the style do not establish official ICLR 2026 provenance; verify that separately before claiming format compliance.

| Figure | Specification | Placement and footprint | Readability budget |
| --- | --- | --- | --- |
| `method_overview` | Required diagram via `generate-concept-figure`; distinguish history-only fitting/calibration from held-out querying and sealed targets; combine base prediction and local residual correction without fake numeric cells. | Page 1 or 2; full 5.5-inch width; two vertically stacked panels; artwork 2.0–2.3 inches high plus caption, about one third page. | Two panels, one per row; at most five labeled objects per panel and two information streams; at least 9-point text. |
| `budget_comparison` | Required matplotlib direct budget-response plot, separate model and heuristic-family holdout panels; series are studied method, random-query low-rank, variance-query low-rank, linear ridge. | Pages 5–6; full 5.5-inch width; two panels side by side; artwork 2.4–2.7 inches high plus caption, about 0.4 page. | Two panels, four categories and four series per panel; common axes and external legend; at least 8.5-point text. Stack rather than shrink if labels collide. |
| `history_structure_controls` | Required matplotlib grouped-point comparison; Intact / Constant / Column-shifted conditions; studied method, column means and variance-query low-rank; all under the matched model-holdout protocol. | Pages 6–7; 0.9 text width, about 4.95 inches; artwork 1.7–2.0 inches high plus caption, about 0.3 page. | One panel, three conditions, three series; at least 9-point labels; offset coincident points without changing values. |

All figures have `allow_progression: false`. At most one overview uses the concept-figure workflow; later orchestration owns that rendering. Explain short labels in captions, use consistent method colors and avoid an architecture drawing that invents neural components. The overview's categories are qualitative encodings, not simulated measurements.

Generate quantitative figures from retained arrays using a reproducible plotting script, exporting **PDF and PNG at 300 DPI**. LaTeX includes the PDF whenever one exists. Raster-only full-width figures must be at least 2400 pixels wide; a genuinely reduced column figure must be at least 1200 pixels wide. Regenerate from source; never upscale. Preserve editable overview source and prompt provenance. Any seed error bars must be explicitly descriptive standard deviations or otherwise defined uncertainty, never implied independent-sample intervals.

## Body Plan Without Padding

Target **8.5 substantive body pages**, excluding references and appendix, inside the venue's 8–9-page requirement. An eight-page body requires its last page at least 75% full. Approximate space allocations include all embedded figures, tables and captions:

- Title, abstract and introduction: 1.25 pages.
- Related work: 0.75 page.
- Problem and information boundary: 0.75 page.
- Method and historical calibration: 1.75 pages.
- Evaluation protocol and uncertainty: 1.25 pages.
- Results across budgets, holdouts and controls: 1.75 pages.
- Discussion, limitations and conclusion: 1.0 page.

Suggested headings are Introduction; Related Work; Budgeted Score Prediction and Local Residual Transfer; Evaluation Protocol; Accuracy Across Budgets and Holdouts; Historical-Structure Controls; Discussion and Limitations; Conclusion. The allocations describe content, not rigid page breaks.

Use space for the observed-entry ALS objective, new-row inference and correction equations, a compact algorithm box and parameter table, careful fixed-target reasoning, complete comparator reporting, bootstrap interpretation and sharp failure conditions. Do not fill space with a campaign account, irrelevant literature, unmeasured ablations or stretched formatting. If grounded depth cannot sustain the minimum, report that rather than padding.

## Supplementary Information After References

The supplement adds implementation and evidence depth, not hidden central limitations. Its source IDs are existing entries in `paper_data.json.grounding_sources`; the local method and evaluator paths below are direct provenance, not invented IDs.

1. **Observed-score extraction and split provenance.** Use the final manifest, plan and evaluator for pinned results/task-definition revisions, metric identity, coverage, normalization, duplicate components, heuristic families and disjoint allocation. Explain that current CC0 attribution does not establish historical licensing of a snapshot without a LICENSE file. Sources: `final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome` plus direct local provenance.
2. **Residual-transfer algorithm and historical calibration.** Give pseudocode, the tuning grid, two-level historical folds, donor filtering and weighting, effective counts, fallbacks and computational caps from selected source. Explain approximate auxiliary fits and why cross-fitting alone guarantees neither unbiased residuals nor superiority. Sources: `result.best_correct_score`, `final.evidence.episodes` plus inspected `src/program.py` and `RESIDUAL_METHOD.md`.
3. **Complete sealed-target comparisons and paired uncertainty.** Derive all-method condition/budget/seed tables from retained arrays, with evaluator method order and aggregation/resampling pseudocode. Keep primary values and uncertainty interpretation in the body. Sources: `final.evidence.episodes`, `final.metric.mae`, `final.metric.baseline_mae`, `final.metric.gain_ci_low`, `final.metric.gain_ci_high`.
4. **Changing-target diagnostic and disruption details.** Compare retained all-unqueried and sealed-target losses, marking changing targets clearly; document mask-preserving constant values and column value/mask shifts. Do not claim an unmeasured missingness ablation. Sources: `final.evidence.episodes`, `final.metric.constant_control_mae`, `final.metric.permuted_control_mae`.
5. **Reproducibility, configuration selection and incomplete evidence.** Map future extraction/plot scripts to every figure and table, document existing evaluator entry point, requirements, final seeds, hashes and reset result. Briefly disclose adaptive search and the failed support-gating attempt with no retained numeric performance from `results/attempts_history.jsonl`. Its missing causal diagnostics remain unknown. Search alternatives are not matched final ablations. Sources: `result.best_correct_score`, `result.top_program_01`, `result.top_program_02`, `result.total_attempts`, `result.total_evaluated_programs`, `final.evidence.episodes`, `final.metric.reset_max_abs_delta` plus direct attempt records. No `study.*` sources exist; do not invent study counts or treat ambiguous aggregate labels as scored/unscored diagnoses.
6. **LLM Usage.** Provide the venue-required separate disclosure of documented ideation, implementation assistance, query planning, framing, and later writing assistance when performed. Numerical evidence comes from the evaluator, not generated measurements. Use the documented interaction record and `final.evidence.episodes`; do not claim later work is already complete.

No later posthoc ranking is guessed. Any authoritative appendix-ranked analyses arriving later belong alongside this plan only when grounded.

## Limitations That Must Stay Visible

Prediction is evaluated on previously observed cells within frozen queryable reservoirs, not genuinely unreported scores. Missingness may be informative. Task/subset columns are heterogeneous and dependent; heuristic family labels cannot certify undisclosed ancestry. Repeated seeds reuse data and components. There are no matched outer residual-component ablations, temporal tests, cross-leaderboard tests, generative-model tests or established deployment-cost savings. The historical-source licensing caveat remains. The discarded selector and support-gating variants do not inherit the selected method's results.

Preserve the independently reported final outcome. Reader-facing scientific descriptions should explain information access, common targets and replay checks, not equate successful evaluation with an exhaustive validity guarantee or a performance threshold. Protocol outcomes and statistical outcomes are distinct only to the extent evaluator evidence identifies them.

## Wording and Citation Guardrails

Avoid headings centered on Search Progression, Campaign Phases, Research Timeline, Milestones, First Successful Result, Experiment A / Experiment B, Round-by-Round Improvements, or Winner Selection as the Main Result.

Avoid phrases such as “first valid result,” “subsequent improvements,” “we then tried,” “later variants,” and “next-best.” The following are private-only internal labels, never visible paper metrics: `correctness rate`, `correct and eligible`, `eligible`, `worker_01`, `worker_02`, `combined_score`, `rubric`. Also forbid unsupported claims of “state of the art,” “provably optimal benchmark selection,” “residual correction explains the gain,” “eight benchmarks are enough,” “generalizes to generative LLM evaluation,” and “unscored attempts were worse.”

Only cite keys already in `references.bib` with synchronized provenance and actually consulted content. Existing matrix-factorization/neighbor-method metadata gives candidate positioning, not permission to invent findings. Do not pad related work with unrelated recommender applications or make an unverified novelty claim. Approved starter works require permissible consultation and grounded retrieval before use. Never search for or infer the prohibited paper or its citation network; stop and record any accidental encounter.

Keep the manuscript double-blind: omit names, affiliations, acknowledgements, funding statements and identifying links. Internal paths remain private grounding metadata, not public prose. Do not claim new experiments, completed plots, final manuscript drafting or final-paper validation at this stage.
