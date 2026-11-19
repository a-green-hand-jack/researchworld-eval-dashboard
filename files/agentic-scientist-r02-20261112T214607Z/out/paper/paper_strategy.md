# Paper Framing Strategy

## Decision

**Status:** ready. **Prompt family:** `paper_standalone`; writing skill: `write-paper-standalone`.

**Provisional title:** Local Residual Scaling for Compositional Conformal Prediction: Benefits and Limits.

**Central question:** When does training-only local residual scaling improve the coverage–reference-mass tradeoff of split-conformal regions for continuous compositions, and what do homoscedastic and covariate-shift controls reveal about its limits?

**Central thesis:** In the evaluated logistic-normal settings, the frozen training-only scale-selection procedure improves measured coverage–reference-mass tradeoffs over global ILR calibration under boundary-concentrated heteroscedasticity, provides no consistent homoscedastic advantage, and performs favorably under the tested shift without establishing shifted-distribution validity or a contribution attributable specifically to quantile stumps.

This is one condition-structured empirical study, not a general evaluation of all conformal methods, a new compositional geometry, or a discovery diary. Dimensions 3 and 10 instantiate the same question. Homoscedastic, boundary-concentrated heteroscedastic, and shifted conditions are complementary evidence under that question, not separate chronological experiments.

## Evidence and Qualification

Read `paper_data.json.final_evaluation` independently. `downstream_study` is absent. The authoritative qualification entries are:

- `final.qualification.status`: `completed`.
- `final.qualification.outcome`: `qualified`.
- `final.qualification.correct`: `true`.

There is **no failed final qualification in the current artifacts**. This does not establish external validity, superiority of individual components, or reliability outside the tested regimes. Unspecified gate diagnostics remain unknown. Candidate self-diagnostics have trust status `unverified`; do not elevate them into evaluator-certified scientific measurements. Writing, review, audit, and revision must independently preserve the authoritative qualification outcome if artifacts change; an unqualified outcome must never be silently reframed as qualification or assumed to be a performance-only failure.

Primary quantitative grounding is `final.evidence.episodes`, plus the declared `final.metric.*` sources. The episode grounding object is a pointer: follow its `json_pointer` to the actual records. Six final seeds are recorded: 1009, 2003, 3001, 4001, 5003, 6007. Each contains H3, H10, B3, B10, S3 and S10, two nominal levels, matched methods, fixed subgroups, reference mass, and uncertainty summaries.

Implementation and design were inspected directly in:

- `results/ideas/02_cross_fitted_tail_adaptive_residual_scaling/program_1/src/program.py` and `METHOD.md`.
- `task/evaluate_final.py` and `task/resources/final/manifest.json`.
- `task/program_0/src/program.py` for the original ridge-scale comparator.

The final manifest and program-tree hash identify the frozen evaluated selection. The inspected implementation is documentarily linked to that selection; this strategy did not independently recompute a source-tree hash match. Do not call that linkage newly cryptographically verified.

The original quadratic-feature ridge scale has source and search evidence, but no matched repeated-final comparator. Global ILR is a different baseline, not a substitute for that original implementation. Do not compare search scores with final scores or attribute a final improvement to replacing the original ridge learner. There are no `study.*` sources, so omit study-style selection deltas and scored/unscored attempt counts. An unscored interaction attempt is missing performance evidence, not a measured loss; its cause is unknown.

## Framing Alternatives and Edit Decision

No resolved edit-context input, `previous_paper/`, `aggregated/`, or `extra_tasks/` is present. Thus there is no prior manuscript to preserve or replace. The required enum is **recentered**, meaning recentered from the broad source-task/proposal context, not a claim that an unseen manuscript was edited.

| Candidate framing | Decision and grounded reason |
| --- | --- |
| Preserve the broad compositional reliability or latent-target story | Reject as the central story: the measured target is a continuous logistic-normal response, not latent multinomial probabilities or classifier label sets. The proposed count-noise bridge was not implemented. |
| Broaden to a shared bridge/scale/interaction method family | Reject: the branches do not share usable measured scientific evidence. A failed interaction evaluation cannot be a quantitative ablation. |
| Recenter on controlled local residual scaling | Select: final records support direct comparisons, subgroup diagnostics, uncertainty, negative homoscedastic controls, and a bounded shift stress test. |
| Claim quantile-stump superiority or universal validity | Reject: selected-component diagnostics and matched final ridge-only comparisons are missing; shift validity is not guaranteed. |

This choice follows evidence strength rather than recency, prior prose density, or the name of a proposed method.

## Contributions and Method Groups

The defensible contribution is an explicitly scoped empirical characterization of a complete scale-selection procedure inside a fixed ILR split-conformal construction. Standard conformal rank validity is explanatory context, not a claimed new theorem. Do not assert literature novelty before checking permitted, actually consulted sources.

1. **Training-only local scale selection — proposed.** Describe the full procedure: quadratic-feature ridge log-scale, constant scale, additive quantile-stump log-scale, four ridge/tail blends, training-only three-fold pinball selection, fitting-only alignment and a one-standard-error heuristic. Do not assume the tail component is selected in any particular case.
2. **Global ILR split conformal — primary baseline.** Same center, ILR norm, splits and rank correction; no covariate-dependent scale. This is the cleanest scale-adaptivity comparison.
3. **Raw-simplex L-infinity split conformal — baseline.** A grounded alternative representation/region shape. Comparing it with ILR does not independently ablate geometry.
4. **Coordinatewise Bonferroni — baseline.** Simultaneous coordinate construction with the evaluator's corrected coordinate quantiles at alpha divided by dimension.
5. **Constant-scale and permuted-residual training controls — supporting.** Constant/global agreement is a numerical invariance check, not an independent method curve. Permutation probes covariate–residual alignment, not the causal contribution of stumps, blending or selection.
6. **Uncalibrated, full-simplex and singleton-center comparators — supporting supplement.** These clarify calibration and coverage–size interpretation, not the main learned-method comparison.

No required new experiment, interaction-depth ablation, latent-count bridge, CQR baseline, weighted-shift method or real-data result is proposed.

## Scientific Design and Results Views

Use three named conditions under one thesis:

- **Homoscedastic controls:** little benefit; small aggregate-utility disadvantages relative to global ILR must remain visible.
- **Boundary-concentrated heteroscedasticity:** strongest joint subgroup-error and reference-mass comparison. H and B change boundary concentration and heteroscedasticity together; neither factor is independently causally isolated.
- **Covariate-shift stress test:** favorable observed local-scale performance, but no exchangeability-based validity conclusion. In S3 the local method uses more reference mass than global ILR; do not promise uniformly smaller regions.

Coverage is coverage of entire continuous composition vectors. It is not class-label prediction-set coverage, probabilistic classifier calibration, or recovery of a latent probability vector. All generated responses are strictly positive. Exact zeros, finite-count noise, real data and neural classifiers are outside this study.

The center-fit/scale-fit/calibration/test sizes are 1024/1024/512/2048. The center is a separately fitted ridge predictor in ILR coordinates. The learned scale has access only to scale-training covariates and residual norms. Calibration uses normalized residuals and the corrected split-conformal rank. State the conditional-on-training rank argument and explicitly exclude group guarantees and unweighted shift guarantees.

**Reference mass is not volume.** The evaluator uses 128 selected test covariates and 1024 probes per query, half from a Gaussian residual reference in ILR coordinates and half from uniform-simplex draws. Its covariance is training-dependent. This is a common, measured reference-distribution probability, not invariant simplex geometry or a universal efficiency quantity. Clustered query/probe hits also limit interpretation of probe-hit Wilson intervals.

### Main quantitative views

- Compare four methods directly across H/B/S and both dimensions; never use search trajectory plots.
- Plot empirical marginal coverage separately at nominal 0.95 and 0.90, retaining all six seed values.
- Plot reference mass separately, with the two nominal levels averaged within seed and clearly labeled; read it alongside coverage, not as an unconstrained size ranking.
- Keep subgroup evidence in the main paper: a six-condition table of mean absolute subgroup coverage error for local scaling, global ILR and permuted residuals, averaged over both fixed groups and nominal levels. Complete signed per-group/per-level values remain in the supplement.
- Use an aggregate table for utility and its error/mass decomposition. Utility weights are a chosen evaluation convention, not a universal scientific objective.

Grounded aggregate anchors, rounded appropriately in any future paper:

| Quantity | Value | Source |
| --- | --- | --- |
| Local mean utility | 0.8772268474776957 | `final.metric.combined_score` |
| Stored utility interval | [0.8766236679621646, 0.8781275287778212] | `final.metric.combined_score_ci_low`, `final.metric.combined_score_ci_high` |
| Mean marginal absolute coverage error | 0.011729600694444453 | `final.metric.marginal_coverage_error` |
| Mean fixed-group absolute coverage error | 0.015105333854689552 | `final.metric.group_coverage_error` |
| Mean reference mass | 0.4508402082655165 | `final.metric.reference_mass` |
| Local-minus-global mean utility | 0.04762325792650014 | `final.metric.global_ilr_score_gap` |
| Stored paired difference interval | [0.043901240346666696, 0.050616967867983816] | `final.evidence.episodes` |

Visible manuscript text should call the aggregate quantity **utility**, not its internal field name. Define it as one minus 0.375 times marginal absolute coverage error, minus 0.375 times group absolute coverage error, minus 0.25 times reference mass, following the evaluator. Control checks all pass here, so the recorded aggregate agrees with this interpretation.

### Uncertainty discipline

The evaluator uses 2000 paired seed-bootstrap resamples over the fixed six-condition grid. The repeated identical aggregate paired intervals embedded in episodes are one estimate, not six independent estimates. Stored Wilson intervals describe within-seed hit counts, not variability across refitted predictors. Do not average interval endpoints, attach overall bootstrap bounds to individual conditions, pool all test points as one fitted model, or infer independent-query uncertainty from clustered probe intervals. Use seed dots rather than inventing unrecorded condition-specific confidence intervals. Six seeds constrain precision and generalizability.

## Figures and Readability

Inspected the ICLR template at `.codex/skills/write-paper-standalone/templates/iclr/paper.tex` and `paper.sty`. The practical text block is **single-column, 5.5 inches wide and 9 inches high**. Full width is therefore the same as the sole column width, not a two-column conference span. All required figures use the full text width. Never rescue density by shrinking labels.

### Figure 1 — Conceptual overview

- **Required; generator:** `generate-concept-figure`; the only overview assigned to that workflow.
- **Purpose:** interior-simplex response → ILR center and training-only positive scale → held-out normalized-score calibration → separate coverage, subgroup and reference-mass evaluation. A short callout places shift outside the exchangeability guarantee.
- **Footprint:** page 1 or 2, approximately 5.5 × 1.9 inches, about 0.25 page with caption.
- **Budget:** one panel, one panel per row, at most six labeled blocks, no more than four visual series; 9-point labels or larger.
- **Safety:** conceptual only, no invented observed points, numeric results or data-shaped example regions. A workflow schematic explains the method, not discovery order.

### Figure 2 — Coverage Across Conditions

- **Required; generator:** `matplotlib`; faceted seed-dot plot.
- **Panels:** 2 × 2, dimension by nominal level. Each panel has H/B/S and four methods: local scaling, global ILR, raw L-infinity and Bonferroni.
- **Footprint:** 5.5 × approximately 4.2 inches, about 0.55 page including caption.
- **Budget:** four total panels, two per row, three categories per panel, four series. Six small offset seed dots per method and an arithmetic-mean marker; one shared legend.
- **Readability:** common coverage axis, horizontal nominal target, label text at least 9 points and ticks at least 8 points. No lines implying a trajectory through H/B/S. Show existing seed variability without fabricated condition-specific intervals.

### Figure 3 — Reference Mass Across Conditions

- **Required; generator:** `matplotlib`; two dimension panels with the same four methods and three condition categories.
- **Metric:** within-seed mean reference mass over the two nominal levels. Caption names that averaging and the mixed reference measure.
- **Footprint:** 5.5 × approximately 2.5 inches, about 0.35 page with caption.
- **Budget:** two panels in one row, three categories per panel, four series; seed dots and mean markers, shared scale and legend, same typography as Figure 2.
- **Readability:** do not merge Figures 2 and 3 into a dense six-panel figure. Pair this size view with the coverage plot and main subgroup table.

**Export contract:** quantitative plotting source must export both PDF and PNG, with PNG at 300 DPI, and LaTeX must reference the PDF when present. Raster-only full-width assets require regeneration at least 2400 pixels wide; any later narrower column-width-only raster requires at least 1200 pixels. Never upscale an existing image. Preserve editable concept source and generator provenance; document an actual fallback if needed rather than silently replacing the overview. No figure is generated at this stage.

## Main-Paper Structure and Page Budget

Target **8.5 substantive body pages**, satisfying the venue's 8–9-page rule; if the body ends at 8 pages, its last page must be at least 75% occupied. Allocations include associated floats:

| Component | Pages | Scientific value |
| --- | ---: | --- |
| Abstract and Introduction, including early overview | 1.25 | Target and question, bounded contributions, glance-value explanation |
| Related Work | 0.65 | Consulted foundations, ILR context and distinction from neighboring quantile methods |
| Compositional Regions and Training-Only Scale Learning | 1.85 | Complete procedure, center/scale/calibration separation, short conditional rank argument |
| Evaluation Design | 1.15 | Generator, comparators, groups, reference measure and uncertainty |
| Coverage and Efficiency Across Conditions | 2.40 | Two quantitative figures, aggregate table and subgroup table; negative controls remain visible |
| Discussion and Limitations | 0.95 | Confounded condition changes, missing attribution, shift and external-validity limits |
| Conclusion | 0.25 | Direct answer within the tested scope |
| **Total** | **8.50** | No generic filler or chronology |

Subheadings in results should identify **Homoscedastic Controls**, **Boundary-Concentrated Heteroscedasticity**, and **Covariate-Shift Stress Test**. If space remains, improve the exact reference-measure explanation, scale-selection description and subgroup contrasts. If space is tight, move extended pseudocode after references—not the failed/negative controls or central limitations.

Table 1 compares the four main methods' aggregate utility, errors and mass, with stored paired local-minus-comparator intervals explicitly labeled as aggregate. Table 2 compares local/global/permuted subgroup errors across the six conditions. Do not turn the original ridge-scale code into a nonexistent final-results column.

## Supplementary Information After References

Purpose: substantive reconstructability and complete observed diagnostics, not a hiding place for evidence essential to the thesis. No speculative future ablation or posthoc ranking is assigned. Separately supplied authoritative appendix-ranked analyses should also go here without retroactively altering this strategy.

1. **Complete Conditional Scale-Selection Specification.** Source-derived pseudocode and all actual settings: tail quantile 0.9, 15 threshold quantiles, minimum leaf size, learning rate 0.1, maximum 80 updates, three deterministic folds, four blend weights, fitting-only alignment, simplicity order, refit and numerical clipping. The one-standard-error rule is a heuristic, not a test. Do not invent component-selection frequencies. Anchor: `final.evidence.episodes`; documentary sources are the selected implementation and `METHOD.md`, not unverified candidate diagnostics.
2. **Generator, Splits, Geometry and Reference Measure.** Full equations from `task/evaluate_final.py`, six-dimensional covariates, shift 1.25, dimensions, split sizes, ridge center, ILR basis, strict positivity, probe mixture and query-clustering limits. Anchor: `final.evidence.episodes`; documentary source: final resource manifest and evaluator.
3. **Full Seed-Level Coverage and Efficiency Tables.** All cases/seeds/levels/groups for the four main methods, signed coverage deviations, reference mass and recorded Wilson intervals. Describe aggregate bootstrap intervals once. Anchors: `final.evidence.episodes`, `final.metric.marginal_coverage_error`, `final.metric.group_coverage_error`, `final.metric.reference_mass`, `final.metric.global_ilr_score_gap`.
4. **Alignment, Calibration and Degenerate-Region Checks.** Constant/global agreement, permuted residuals, uncalibrated quantiles, full-simplex and singleton-center checks; explain exactly what each tests. Anchors: `final.evidence.episodes`, `final.metric.constant_control_score`, `final.metric.permuted_control_score`, `final.metric.control_pass_fraction`.
5. **Conditional Rank Argument and Its Boundaries.** Standard rank proof conditional on center/scale training, corrected rank with infinity when necessary, ties and common scale clipping. Not a new theorem, subgroup guarantee or shift theorem. Anchor: `final.evidence.episodes`; construction details come from the evaluator and selected method source.
6. **Reproducibility and Evaluation Scope.** Recorded Python 3.12/NumPy 2.1.3 statements, final seeds, synthetic generation, anonymous relative commands, hashes and figure/table-generator mapping when implemented. Stored per-seed elapsed durations are not new method-only runtime measurements. Disclose unimplemented count-noise work, the unscored interaction extension, unknown failure cause, absent matched final ridge-scale evidence, and omitted study-style search counts/deltas. Anchors: `final.evidence.episodes` and `final.qualification.*`; process facts require their actual local records, not inference from an episode pointer.

### Separate Required Disclosure

**LLM Usage.** Retain this separate mandatory section after references, outside the six evidence-backed supplementary subsections listed in JSON. Disclose assistance evidenced by the current framing interaction and available proposal, source-editing and reference-query process artifacts; add the precise writing role when it occurs. Inspect actual logs before attributing further roles or model versions. Do not claim unrecorded manual checks or call unexecuted experiments completed. Process provenance is not grounded in a scientific-result episode: do not invent a result source ID to support this disclosure. Record prohibited-literature encounters only if documented. This strategy made no network requests.

## Literature, Anonymity and Writing Safeguards

`references.bib` and `references_provenance.json` exist. Retrieval metadata is not evidence that a paper was read or even relevant. `Lei2016DistributionFreePI` is a directly relevant metadata match in the allowed starter lineage; actual consulted content still requires verification before citation. Do not pad related work with irrelevant retrieval results. Verify appropriate ILR, quantile-learning and conditional-coverage sources through permitted material before making novelty claims. Do not search for or identify the prohibited related paper, expand citation networks into it, or read citing/discussing pages. Stop and document an actual accidental encounter.

Use ICLR 2026 as required by `VENUE.md`. Do not claim this local style was independently certified as the latest official release. The inspected scaffold contains a named author and final-copy switch: those must not be copied into the anonymous review manuscript. Omit author names, affiliations, acknowledgements, funding and identifying links. Preserve automatically managed watermark blocks. Include `LLM Usage` and any actually required ICLR checklist, not an invented checklist borrowed from another venue.

### Forbidden Headings

Search Progression; Campaign Phases; Milestones; First Valid Result; Iteration History; Experiment A; Experiment B; Winner Selection; From Failure to Success; Latent-Count Bridge Results; Quantile-Stump Ablation.

### Forbidden Phrases

“we then tried”; “subsequent improvements”; “first valid result”; “next-best”; “later variants”; “search winner”; “correctness rate”; “correct and eligible”; “eligible”; “combined_score”; “rubric”; “worker_01”; “worker_02”; “state of the art”; “universally reliable”; “uniformly smaller regions”; “guaranteed coverage under covariate shift”; “distribution-free conditional validity”; “quantile stumps caused the gain”; “the latent bridge restored coverage”; “unscored attempts were measured losses”.

Internal field names and pipeline labels in this memo are **private-only grounding context**, never recommended visible manuscript terminology. Memory is private qualitative context, not numerical grounding. Old implementation-stage statements of incomplete execution must not override completed final evaluation evidence.

## Stage Boundary

This strategy writes only the framing memo and JSON, with append-only memory updates. It does not draft `paper.tex`, write `claims_grounding.json`, generate figures, run experiments, or run final-paper validation. Strategy-schema, grounding-ID and consistency checks are appropriate here. The final writer must preserve the scope, qualification facts, negative controls and limitations throughout drafting and audit.
