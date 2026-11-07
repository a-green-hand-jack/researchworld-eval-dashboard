# Paper Strategy

**Status:** ready for a bounded standalone comparison study, not a declaration of publication readiness.  
**Writer schema repair:** the two quantitative figure types are normalized to the canonical manifest value `composite`; their faceted dot-whisker and scatter/paired-dot compositions, IDs, evidence, and readability budgets are unchanged. This repairs a schema mismatch without changing the scientific strategy or conceptual-figure ownership.
**Prompt family:** `paper_standalone`; downstream skill: `write-paper-standalone`.  
**Provisional title:** Endpoint-Tuned Regression under Network Interference: Accuracy and Limits.

## Central Question and Thesis

**Question.** How accurately does endpoint-risk-tuned one-hop regression estimate the global average treatment effect across the evaluated networks, interference mechanisms, and assignment designs, relative to simple regression baselines?

**Thesis.** In the evaluated synthetic-outcome settings, endpoint-tuned exposure regression reduces error relative to assignment-only comparators in many spillover conditions but performs worse in aggregate than linear one-hop OLS, while near-noise-level in-sample residuals coexist with substantial endpoint errors under threshold and omitted two-hop interference.

This is one shared thesis with condition-specific evidence across SBM, BA, WS, and Stanford3, not four separate experiment narratives. The contribution is an implemented target-aware regression construction and an honest map of its conditional accuracy and limits. It is not a new identification theorem, proof that target-aware tuning improves estimation, or demonstration of general superiority.

## Why This Story Wins

The completed final evaluation provides matched estimates for the frozen method and three substantive baselines. `final.evidence.episodes` contains 24 seed blocks, covering 576 scientific cases across four graph families and six conditions. This evidence supports a direct performance-and-limitations paper even though the stronger exposure-aware baseline is better in aggregate.

Descriptive reaggregation performed during framing gives equal-cell mean uncapped RMSE of approximately 0.6140 for the selected estimator, 0.4598 for one-hop OLS, and 1.3676 for difference in means. The selected estimator's authoritative recorded mean capped normalized RMSE is 0.6140475146408374; its mean absolute capped normalized bias is 0.4597691498768297. The reaggregated baseline values come from existing final observations, not new simulations or uncertainty estimates. The writer must save the derivation and ground the resulting table before publishing rounded values, and verify clipping before equating raw and capped summaries.

The following alternatives are rejected:

- **Positive development-improvement story:** a development score does not establish final superiority, and the final one-hop OLS comparison contradicts a general-benefit claim.
- **Broad method/architecture family:** no usable final comparison supports a neural or two-hop estimator family, and component ablations are absent.
- **Support or tuning as a proven causal explanation:** measured support and fit are descriptive; feature changes and tuning are not isolated.
- **Search chronology:** does not answer the scientific accuracy question and would conceal the strongest comparisons behind development events.

Negative and conditional findings are the reason to write this paper, not a reason to omit the method or manufacture an improvement.

## Framing and Input Audit

**Decision: recentered.** This is not an edit-mode manuscript revision. No resolved edit-context input, prior manuscript, `aggregated/`, `extra_tasks/`, or contributions scaffold was supplied. The label denotes recentering the source task's broad research agenda on the narrower final evidence, not revising an imaginary prior paper. Preservation is therefore inapplicable; broadening lacks evidence; an evidence-led comparison is the defensible choice.

The inspected selected source is `results/ideas/03_endpoint_contrast_sure_for_exposure_regression/program_1/src/program.py`, located through `paper_data.best_correct` and `results/best_program_manifest.json`. It implements one-hop quadratic exposure regression and endpoint-risk ridge tuning, not a two-hop model. The original source at `task/program_0/src/program.py` uses fixed hinges and fixed ridge. The final manifest identifies the frozen program tree, but an independent file-by-file identity check is not claimed here.

`paper_data.json.final_evaluation` was read independently of study metadata. The grounded values are:

- `final.qualification.status`: `completed`.
- `final.qualification.outcome`: `qualified`.
- `final.qualification.correct`: `true`.

These are reported task-specific completion/integrity facts, not evidence of superiority, generalization, model validity in every setting, or publication acceptance. Missing gate diagnostics remain unknown. If later authoritative evidence reports failed qualification, retain that outcome and its stated limitations through drafting, review, and revision; do not infer its cause from performance metrics or reinterpret publication eligibility as scientific qualification.

No `downstream_study` or `study.*` sources exist. Do not invent them or report campaign winner margins, search-score deltas, or scored/unscored attempt counts. **Private-only provenance:** development pointers locate the selected implementation; they are not main-paper performance evidence.

The original fixed-hinge estimator lacks a matched final comparison with the frozen method. Omit that final contrast rather than comparing development and final scores. A failed two-hop GCV branch has no usable performance evidence: its local stderr reports disconnection before candidate responses, while the underlying cause remains unknown. Mention missing evidence nonchronologically if needed; never call it an estimator loss or an invalid scientific method.

## Methods to Include

| Method group | Role | Scientific purpose |
| --- | --- | --- |
| Endpoint-risk-tuned quadratic one-hop regression | Proposed | The frozen evaluated construction and its guarded endpoint objective |
| Difference in means | Baseline | What a direct assignment contrast misses under interference; retain its favorable no-spillover evidence |
| Own-treatment OLS with covariates | Baseline | Ordinary adjustment without explicit exposure representation |
| Linear one-hop OLS with covariates | Baseline | Essential stronger comparison; it is better in aggregate and is not a same-feature tuning ablation |

Do not expand the main comparison with copy-observed or constant-prediction behavioral checks. The original fixed-hinge method and incomplete two-hop branch belong only in implementation provenance/missing-evidence discussion, without an unsupported final comparison.

### Explanation Worth the Body Space

Define finite-population GATE as the average all-treated versus all-control potential-outcome difference. The estimator averages the corresponding fitted node predictions. Neighbor exposure is zero for isolates, so all-treated exposure is not automatically one for every unit.

Explain the actual feature map: intercept, covariates, own treatment, neighbor treatment fraction, treatment-exposure interaction, exposure curvature, and treatment-curvature interaction. Describe saved centering/scaling, SVD, the fixed penalty grid, contrast estimability and residual-degrees-of-freedom guards, fixed-hinge fallback, and constant-outcome bypass. Their implementation does not establish how frequently the guards or penalties were used.

The implemented risk criterion for a fixed penalty is

`(a_lambda^T y_centered - a_0^T y_centered)^2 + 2 sigma_hat^2 a_lambda^T a_0 - sigma_hat^2 ||a_0||^2`,

where `a_0` represents the estimable reference contrast. Explain the correct-reference and iid homoskedastic Gaussian-noise assumptions. A fixed-penalty risk identity is not unbiased risk reporting after selecting its minimum. Algebraic estimability is not endpoint support, identification, or robustness. Do not promote an unverified derivation into a new theorem.

The candidate changes both representation and tuning relative to the original fixed-hinge regression. No same-feature predictive-GCV, fixed-penalty, or unregularized ablation has usable final evidence. The paper cannot assign gains or regressions to any single component.

## Results That Carry the Thesis

1. **Absolute accuracy first.** A compact main-text table reports all four methods' equal-cell mean RMSE and mean absolute cell bias, with uncertainty derived from existing records. Do not substitute pooled RMSE, mean absolute error, or a composite utility for these definitions. Make the unfavorable aggregate one-hop OLS comparison explicit.
2. **Complete conditional comparison.** Show every final family-by-condition cell, including no spillover, weak and strong linear spillover, threshold interaction, omitted two-hop spillover, and strong linear spillover under cluster assignment. Preserve regressions and large failures in the main figures.
3. **Fit is not endpoint accuracy.** Plot the selected estimator's observed-fit residual RMSE against absolute GATE error. Call it in-sample residual error, not held-out prediction performance; no baseline residual measurements or predictive-GCV comparison are available.
4. **Bounded assignment-design contrast.** Compare strong linear spillover under individual assignment with its graph-BFS cluster counterpart within families and seed blocks. Do not infer optimal clustering or causally attribute the change to support alone.
5. **Supporting diagnostics.** Summarize recorded exposure ranges, endpoint fractions, and the evaluator's simple-linear-design condition measurement. The condition measurement is not that of the selected quadratic reference. Candidate internal diagnostics are unverified; penalty frequencies, fallback frequencies, risk calibration, and inference coverage are absent.

The threshold condition combines a neighbor-exposure threshold with a treatment interaction. The two-hop condition uses length-two walks **including backtracking**, not a unique-distance-two average. The cluster condition changes assignment relative to strong linear spillover, not the outcome formula. Use the actual manifest definitions rather than a generic interference taxonomy. All outcomes, including Stanford3 outcomes, are synthetic.

### Uncertainty and Aggregation

Preserve the complete seed block across graph families, conditions, and methods when resampling the 24 final seed records. A planned 95% paired seed-block percentile bootstrap can summarize Monte Carlo uncertainty; document the random seed and resample count when implemented. For each resample, recompute per-cell RMSEs before forming ratios and recompute equal-cell averages before forming table intervals. No confidence intervals have yet been generated.

The 576 cases are not 576 independent inferential replicates. The resampling quantifies Monte Carlo variation in this benchmark, not unit-level causal interval coverage. Stanford3 is one fixed public topology with repeated generated experiments, not a sample of 24 public networks. Synthetic graph variation and repeated observations on a fixed public graph have different interpretations. Avoid significance stars and posthoc win counts; per-condition comparisons are exploratory and bootstrap intervals do not resolve multiplicity.

## Figure and Table Contract

### Template Geometry

`VENUE.md` fixes ICLR 2026 and an 8-9-page body excluding references. The inspected `paper.sty` specifies a **single text column, 5.5 inches wide and 9 inches high**. Here column width equals full text width; there is no double-column half-width slot. Use full-width figures rather than shrinking dense panels into imagined narrow columns. The style's historical header is not independent proof of official 2026 release provenance; verify that during final preparation and regenerate assets if geometry changes.

All figure labels must remain at least 8.5 pt at final placement. Maximum budgets are figure-specific and never exceed four panels total, three panels per row, six categories per panel, or four series per panel. Page-footprint estimates include captions and are planning allocations, not compiled measurements.

| Figure | Content and generator | Geometry and readability | Placement / footprint |
| --- | --- | --- | --- |
| `endpoint_overview` | Required conceptual diagram via `generate-concept-figure`; observed experiment → exposure regression and endpoint-risk tuning → mean all-treated minus all-control prediction | One cohesive panel, at most three horizontal zones, six short conceptual labels; 0.98 text width, about 5.39 × 1.7-1.9 in; no fabricated curves or numeric results | Page 1 or 2; about one quarter page |
| `conditional_accuracy` | Required matplotlib 2×2 dot-whisker comparison; each family has six condition rows and three ratios, selected RMSE divided by baseline RMSE | Full 5.5 in width, about 3.8-4.2 in high; two panels per row; six categories, three series per panel; shared log ratio axis and line at one; shared three-entry legend | Main results; roughly half page |
| `diagnostic_limits` | Required matplotlib composite: residual-fit/error scatter plus selected-estimator individual-versus-cluster RMSE | Full width, about 2.4-2.7 in high; two panels in one row. Scatter groups threshold, two-hop, and remaining conditions into three visual series; design panel has four families and two series | Main results; about one third page |

For Figure 2, values below one favor the selected method; use ratios of cell RMSEs, never averages of per-run ratios. Intervals are planned reanalyses of recorded data. Keep a main-text table of absolute errors beside the relative comparison so ratios cannot hide poor absolute accuracy. Define the six short condition labels in a compact protocol table.

For Figure 3, use transparent scatter points and no fitted causal trend. Correlated case records are visual observations, not extra independent replications. The assignment-design panel uses paired-seed uncertainty. Keep support-fraction tables in the supplement. If two panels cannot remain legible, stack them and adjust the body allocation rather than reduce type size.

The overview is a semantic schematic, not an empirical network sample. Endpoint assignments are prediction inputs; endpoint outcomes are withheld from fitting. Use `generate-concept-figure` for exactly this one diagram and preserve its editable draw.io source. This stage only plans figures and does not invoke generation.

### Export Requirements

- Quantitative source scripts export both PDF and PNG, with the PNG at 300 DPI. LaTeX references the PDF whenever available.
- For the concept figure, request a vector PDF export from editable source if supported. If raster-only, regenerate at least 2400 px wide for full-width placement.
- Any raster assigned to a genuinely narrow column in a later changed layout needs at least 1200 px width. Never upscale existing raster output.
- If the concept workflow is impossible or fails, record the concrete failure before a documented vector fallback. Do not silently replace the required workflow with an improvised drawing.
- Plot scripts and figure assets do not yet exist; do not describe them as completed deliverables.

## Body-Page Budget

Target approximately **8.75 substantive pages**, including figures and tables:

| Material | Page allocation |
| --- | ---: |
| Title and abstract | 0.40 |
| Introduction and early overview | 1.10 |
| Related work | 0.65 |
| Target and interference setup | 0.90 |
| Endpoint-tuned estimator | 1.50 |
| Empirical protocol and condition table | 0.95 |
| Conditional comparisons and diagnostic figures | 2.15 |
| Discussion and limitations | 0.85 |
| Conclusion | 0.25 |

Use spare space for the endpoint objective, baseline definitions, conditional-risk assumptions, uncertainty/aggregation, and concrete failures. Do not add methods or studies to fill pages. Keep the main body within nine pages; an eight-page version must have its last page at least 75% full. Figures' footprints are included in the relevant section allocations, not extra pages.

Suggested thesis-first headings are **Global Intervention Target**, **Endpoint-Tuned Exposure Regression**, **Empirical Protocol**, **Conditional Accuracy and Failure**, and **Scope and Limitations**. The abstract and conclusion must retain the negative aggregate comparison and the lack of isolated tuning evidence.

## Supplementary Information After References

The supplement adds grounded depth without hiding evidence essential to the thesis. It is a minimum plan, not an authoritative ranking of later posthoc analyses.

1. **Complete Conditional Error Tables.** All methods and family-by-condition cells: signed bias, absolute bias, uncapped RMSE, replicate counts, and paired-seed uncertainty. Explain equal-cell versus pooled summaries. Sources: `final.evidence.episodes`, `final.metric.mean_capped_normalized_rmse`, `final.metric.mean_absolute_capped_normalized_bias`.
2. **Exposure Support and Residual Diagnostics.** Existing minima/maxima, endpoint fractions, simple-linear-design condition measurements, and in-sample residuals. Interpret descriptively; no identifiability, calibration, or coverage claim. Source: `final.evidence.episodes`.
3. **Estimator Specification and Conditional Risk Criterion.** Document the inspected selected implementation, tolerances, centered/scaled SVD, penalty grid `n × {0, 1e-6, 1e-4, 1e-2, 1}`, tie handling, fallback, and constant bypass. Contrast fixed-penalty reasoning with selected-minimum optimism. `result.best_correct_score` links to the selected source directory; `final.evidence.episodes` supplies evaluated results, not independent source-hash verification. Do not invent tuning or fallback distributions.
4. **Benchmark Construction and Reproduction.** Use `task/resources/final/manifest.json`, `task/task_contract.json`, `task/requirements.txt`, and `task/evaluate_final.py` alongside `final.evidence.episodes` and `final.qualification.status/outcome`. Specify graph and outcome generation, the actual BFS cluster rule, backtracking two-hop exposure, noise/covariates, isolates, seeds, checksums, declared dependencies, and commands verified against existing entrypoints. Separate runtime limits from measured elapsed time. Map eventual tables and figures to scripts only after those scripts exist. Preserve Stanford3 attribution and share-alike obligations.
5. **Evaluation Integrity and Missing Evidence.** Use `final.qualification.*`, the recorded control/failure metrics, and final episode evidence. Explain constant-outcome, relabeling, and replay checks only to their documented scope; internal diagnostics remain unverified. A nonchronological missing-evidence note may cite the two-hop branch's local failure JSON and stderr without converting an unscored attempt into a scientific loss. No unsupported search counts, margins, or matched original-method final results.

**Separate required process disclosure: LLM Usage.** Alongside the five evidence-backed scientific supplement subsections, include a separate venue-required section after references disclosing the precise documented roles of LLMs in ideation, code generation, query planning, framing, and eventual writing/figure work. Use actual process artifacts under `results/ideas/` and local planning records, not performance source IDs or assumptions. Disclose performed activity separately from work still planned, without identifying authors. This requirement is recorded in JSON writer guidance rather than the scientific `planned_subsections` list because scientific metric IDs do not ground process disclosure.

No ablation study, noise stress test, hidden-endpoint twin simulation, risk-calibration study, or inference-coverage experiment is available. Such work may be named as missing or future work, never as supplementary results already obtained. Route later appendix-ranked analyses here without retroactively rewriting this strategy; keep essential negative findings in the main body.

## Citation, Access, and Venue Guardrails

`references.bib` includes relevant starter-title matches `Chin2018RegressionAF` and `Han2023ModelbasedRA`, but the supplied reference provenance records retrieval metadata rather than verified reading. Other retrieved statistical titles are not automatically appropriate foundations for the implemented risk criterion. Use only existing keys after checking and reading permitted sources; check questionable year metadata. Do not invent graph-attribution keys or pad the related work with irrelevant hits. Missing literature acquisition belongs to an authorized reference step.

Do not identify or search for the prohibited paper, expand citation graphs, or read prohibited summaries, reproductions, or discussions. If accidental exposure occurs, stop and record the location and extent. This strategy stage performed no external research and no new scientific runs.

The ICLR 2026 manuscript must be fully anonymous: no names, affiliations, acknowledgements, funding, self-identifying links, or internal URLs. Include the separate `LLM Usage` section after references if appropriate. Current readiness applies to framing only, not verified official-template provenance, citation completeness, completed plot assets, uncertainty computations, or compiled-page compliance.

## Language That Would Break the Story

**Forbidden headings:** Search Progression; Campaign Phases; Milestones; Timeline of Improvements; First Successful Estimator; Experiment A / Experiment B; From Baseline to Winner; Architecture Sweep; and an Ablation Results heading without actual component ablations.

**Forbidden visible phrases:** “we then tried,” “first valid result,” “subsequent improvements,” “next-best,” “later variants,” “search winner proves superiority,” “universally outperforms,” “state of the art,” “robust to arbitrary interference,” “validated endpoint-risk calibration,” “unbiased after tuning,” “predictive GCV is inferior,” and “the two-hop method failed scientifically.”

Keep internal labels such as `eligible`, `correct and eligible`, `correctness rate`, `combined_score`, `worker_01`, `worker_02`, and `rubric` out of visible manuscript prose. Do not use a favorable composite utility as GATE accuracy. No thresholded-rate plot is needed; if added later, define one reader-facing meaning per figure.

## Handoff Boundary

This stage writes only the mirrored strategy outputs and append-only memory updates. It does not draft `paper.tex`, create `claims_grounding.json`, generate figures, execute a new simulation, or run final-paper validation. Later writing must save derived summaries, compute uncertainty, inspect allowed sources, and preserve all stated limitations before claiming a complete paper.
