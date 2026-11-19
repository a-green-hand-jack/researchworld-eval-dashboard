# Paper Strategy: Conditional Gains and Limits of Frozen-Score Controls

## Decision

**Status:** ready. **Family:** `paper_standalone`, using `write-paper-standalone`.

**Provisional title:** Risk-Adaptive Frozen-Score Controls: Conditional Gains and Limits for Mean Inference.

**Central question:** With labels, unlabeled observations, and a scalar predictor fixed within each repeated-sampling comparison, when does training-only cross-fitted score calibration shorten mean confidence intervals relative to label-only inference, PPI, and PPI++, and what does the evidence establish about coverage?

**Central thesis:** The frozen risk-adaptive control method yields narrower mean intervals than PPI and PPI++ on the evaluated empirical gene-expression source, but is wider than PPI++ in all six synthetic or perturbed-score conditions. Observed coverage and offset-invariant studentization support a conditional efficiency study, not universal narrowing or a finite-sample validity certificate.

This is one shared thesis with condition-specific evidence, not separate dataset papers. The contribution is an implemented, carefully delimited mean-inference construction, explanatory algebra, and a matched assessment of gains and limitations. It is not a claim of a new generally optimal interval or an identified causal mechanism for the measured gain.

## Evidence and qualification audit

Read `paper_data.json.final_evaluation` independently. `downstream_study` is absent. The authoritative sources are:

- `final.qualification.status`: completed.
- `final.qualification.outcome`: qualified.
- `final.qualification.correct`: true.
- `final.evidence.episodes`: 400 final repeats, seven conditions, paired endpoints for the frozen method and all three references.
- `final.metric.empirical_coverage`: 0.9610714285714286; `final.metric.minimum_case_coverage`: 0.95; nominal coverage 0.95; failure fraction 0.
- `final.metric.mean_width_ratio`: 1.2106794607646876, a capped mean of episode ratios, not a ratio of mean widths.

There is no failed final qualification in the current evidence. Qualification is nevertheless not a coverage theorem. The local resource manifest and final evaluator explicitly fix the conservative scientific-validity field at zero because arbitrary theoretical assumptions cannot be certified. That flag is neither a diagnosed coverage/adaptivity failure nor a positive certificate. Candidate diagnostics are marked unverified; prefer evaluator-observed endpoints and evaluator-produced summaries.

If later authoritative evidence changes qualification to failed, preserve that outcome prominently in writing, review, audit, and revision. Never infer an undisclosed gate cause or turn publication acceptance into scientific qualification.

The selected search record directly identifies `results/ideas/02_offset_invariant_risk_adaptive_control_variates/program_1`; its `src/program.py` and `src/METHOD.md` were inspected. The final record supplies a frozen tree hash, but this stage did not independently recompute it against the local source. Keep that verification distinction. `ablation_studies` is empty and its evidence directory is missing.

## Framing alternatives and staged-input impact

**Prior-story status: rejected by default, not an actual manuscript rejection.** No edit context, `previous_paper/`, `aggregated/`, or `extra_tasks/` is staged. There is no prior manuscript to preserve or broaden.

| Candidate framing | Decision and evidence |
| --- | --- |
| Preserve a prospective nonlinear saturation/certificate success story | Reject: oracle identities are available, but the reported interval is not the internal certificate, and nonlinear synthetic data do not show a width benefit against PPI++. |
| Broaden to a shared family including smooth covariance stacking | Reject as the primary thesis: stacking has exploratory search evidence, not the frozen method's final assessment; no controlled component ablations identify a common improvement mechanism. |
| Recenter on the most recent searched configuration | Reject: recency is weaker evidence than the selected method's completed final repeats. |
| Conditional efficiency and validity boundaries of the frozen risk-adaptive method | Select: supported by matched final endpoints, all three references, uncertainty, information controls, and explicit source-level limitations. |

The final evidence changes the private source-only perspective into a measured conditional-results story. No inherited title or figure plan is retained by inertia. Constant/permuted scores support the shared question without becoming independent natural datasets. This structure transfers to other tasks by selecting the frozen method, retaining valid matched references, and organizing conditions by the boundaries they test rather than by execution order.

## Narrow method set

1. **Baseline: label-only mean intervals.** Clopper-Pearson for binary outcomes; Student-t for real outcomes. The latter is not distribution-free exact for the empirical real source.
2. **Baselines: PPI and PPI++.** Both are matched implementations from `ppi-python==0.2.3`; distinguish coefficient one from the optimized coefficient. Keep the original comparator and the optimized reference, with their asymptotic and rare-event caveats.
3. **Proposed: risk-adaptive cross-fitted frozen-score controls.** Nested training-only zero/affine/spline selection, finite-unlabeled-sample multiplier, held-out correction, and offset-invariant within-fold/shared-pool studentization. Explain the actual t-based return path, clipping, and label-only fallbacks.
4. **Supporting conditions: constant and permuted scores.** These perturb the nonlinear records, complementing the uninformative condition. They are information controls, not isolated ablations of nonlinear calibration or studentization.

Exclude smooth stacking and pooled-residual variants from the main method set. Their existing search evidence may appear in an explicitly exploratory supplementary comparison, not as final or causal ablations. Do not invent a performance comparison to an unavailable original incumbent. No `study.*` sources exist; do not fabricate downstream-study selection facts, differences, or scored/unscored counts.

## Results that carry the story

Use every final condition: gene expression, linear, nonlinear, rare outcomes, uninformative, constant-score nonlinear, and permuted-score nonlinear. Group the first four as predictive conditions and the last three as information controls. All required comparison figures use this same partition.

**Empirical-source gain.** In the stored gene-expression summary, mean widths are 0.4488074070562893 for the frozen method, 0.4759006085515874 for PPI++, 0.4727476605089987 for PPI, and 1.5263806745747615 for label-only inference. The paired width-difference interval versus PPI++ is [-0.02969064263718976, -0.02435572792761422]. Candidate coverage is 0.9575 with stored simultaneous interval [0.9163118126035984, 0.9824159148164467]. Source: `final.evidence.episodes`, especially the first episode's `solution.summary.gene_expression` and the paired endpoints throughout the episodes.

**Boundary of benefit.** All six other conditions have positive paired width-difference intervals versus PPI++. Preserve these results in the main paper, including the explicitly nonlinear condition. Gains against label-only inference or PPI do not imply gains against PPI++.

**Coverage uncertainty.** Candidate condition coverage spans 0.95 to 0.98, but its lower uncertainty bounds do not establish coverage at or above nominal. Plot all four methods' stored Clopper-Pearson intervals and the 0.95 reference. These intervals use a joint 95% Bonferroni family over seven conditions and four methods.

**Rare-outcome caveat.** PPI++ observed coverage is 0.92; its interval [0.868958106205729, 0.9562534828761202] includes nominal coverage. Five of its 400 intervals have zero width, counted directly from paired endpoints. Retain its measurements, but do not equate its narrower intervals with a valid practical improvement or claim a statistically established coverage failure. This caveat belongs in the body, not only in the supplement.

**Width estimand audit.** The final evaluator caps each candidate/PPI++ width ratio at 100 and assigns 100 when only the baseline width is zero. The recorded aggregate is secondary. Main comparisons use absolute paired mean differences and ratios of mean widths with their matching stored bootstrap intervals. Do not drop zero-width episodes or silently interchange these quantities. The width intervals use 512 paired bootstrap resamples, recorded seed 79231, and multiplicity-adjusted percentile tails. Explain finite-bootstrap tail resolution; do not claim exact simultaneous bootstrap coverage.

**Mechanism without causal overreach.** Explain deterministic-control finite-N headroom and offset cancellation, but do not attribute the measured gain to nonlinear fitting, selection, or studentization individually. No final component ablations exist. Critical values, clipping, and fallbacks also differ between methods.

## Scope and method explanation

The estimand is a mean. Resource fixing holds within each matched replicate; coverage concerns repeated sampling, not conditioning on every realized input. The real benchmark resamples normalized scalar outcome/prediction records with replacement and targets that empirical source's mean. It does not validate external biological-population inference, a new backbone, or promoter-sequence disjointness.

Describe the weighted held-out residual mean plus the shared-unlabeled control mean. Compute unlabeled variance after combining fold controls to retain covariance. Show why fold-specific additive constants cancel from both the point estimate and the proposed studentizer. This does not show that pooled residual studentization empirically failed.

Separate deterministic-control identities from learned-fold asymptotics: overlapping training sets do not permit an exact conditional independence argument. State the source note's stability and moment conditions; the heuristic inner-fold risk comparison does not establish them or constitute a calibrated significance test. The internal bounded certificate is computed but not returned. A label-only exact binomial fallback does not certify a data-dependent combined rule.

## Figure specifications and layout

Inspected `.codex/skills/write-paper-standalone/templates/iclr/paper.tex` and `paper.sty`: the supplied format is **single-column**, with **5.5-inch text width and 9-inch text height**. Here column width equals full text width; a hypothetical half-width two-column figure would be wrong. Historical style-header text does not certify official ICLR 2026 provenance. All three figures use full text width, with no progression axis.

### Figure 1: `fixed_resource_overview` — required

- **Type/generator:** conceptual diagram; `generate-concept-figure`, the only figure using that workflow.
- **Content:** fixed inputs and outer-training-only zero/affine/spline selection in one panel; held-out correction, shared-pool aggregation, and the returned interval in the other. Mark the separation between returned inference and empirical assessment, not a certified-success arrow.
- **Budgets:** at most two panels, six functional groups per panel, two visual series; 9–10pt text.
- **Footprint:** 1.0 text-width fraction, approximately 5.5 by 2.0 inches; near one quarter page with caption, on page 1 or 2.
- **Justification:** the training boundary and shared-pool combination are not immediately legible from result plots alone. Two compact conceptual panels provide glance value without reproducing a software execution diary.
- **Execution constraint:** the downstream orchestrator owns rendering. Honor no paid APIs: deterministic draw.io rendering without optional paid image restyling; if orchestration cannot honor that constraint, report the blocker rather than silently paying or changing ownership.

### Figure 2: `paired_width_comparison` — required

- **Type/generator:** paired-bootstrap forest plot; matplotlib.
- **Metric:** candidate mean width divided by comparator mean width; three series for label-only, PPI, and PPI++ with matching stored ratio intervals. Record deterministic derivations from the stored means and endpoint sources.
- **Grouping:** two vertically stacked panels: four predictive conditions, then three information controls. Common log-ratio axis; reference one. Do not imply that a width advantage establishes coverage.
- **Budgets:** two panels, at most four conditions per panel, three series; minimum 8pt text, preferably 9pt.
- **Footprint:** 1.0 text-width fraction, 5.5 inches wide by approximately 3.3–3.7 inches total height; about half a page with caption.
- **Justification:** stacked full-width panels keep condition labels and three uncertainty series legible; shrinking two panels side by side would not.

### Figure 3: `coverage_with_uncertainty` — required

- **Type/generator:** binomial-interval forest plot; matplotlib.
- **Metric:** empirical coverage with the stored simultaneous intervals; frozen method plus three references. One nominal line at 0.95.
- **Grouping:** same two-panel vertical partition as Figure 2 and common axis covering every stored endpoint. No thresholded success colors, cropped lower bounds, or pass/fail interpretation when an interval spans nominal.
- **Budgets:** two panels, four conditions per panel, four series; 8–9pt text.
- **Footprint:** 1.0 text-width fraction, 5.5 inches wide by approximately 3.3–3.7 inches total height; about half a page with caption.
- **Justification:** directly pairs coverage with the efficiency comparison and keeps rare-outcome uncertainty visible.

Retain quantitative plotting source and export PDF plus 300-DPI PNG. LaTeX references PDF whenever available. Keep editable draw.io source and its vector export when available. Raster-only full-width output requires at least 2400 pixels across; column-width output requires at least 1200. A 5.5-inch raster at 300 DPI alone does not reach the full-width minimum: regenerate larger from source rather than upscale.

## Body-page use

Target nine substantive ICLR body pages, excluding references and supplement. Planning allocations include floats, not just prose:

| Material | Page budget |
| --- | ---: |
| Title and abstract | 0.5 |
| Introduction and early overview | 1.2 |
| Related work | 0.6 |
| Method | 1.6 |
| Identities and validity boundaries | 1.1 |
| Evaluation design | 0.7 |
| Results and two quantitative figures | 2.1 |
| Discussion and limitations | 0.9 |
| Conclusion | 0.3 |

If the body instead finishes at eight pages, its last page must be at least 75% full. Use space for assumptions, comparator distinctions, uncertainty definitions, and substantive failure analysis, not filler. Add a compact full-width design table describing conditions, targets, pairing, and transformations. No new experiments are needed to fill the plan.

Suggested sections: Introduction; Related Work; Mean Inference with Frozen Scores; Control Construction and Validity Boundaries; Evaluation Design; Conditional Width Gains and Coverage; Discussion and Limitations; Conclusion. Preserve the standalone template's required core sections, using these as appropriate section/subsection names.

## Supplementary Information after references

**Purpose:** add reproducible technical and audit depth, not hide central non-benefits or coverage limitations. Use `clearpage`, bibliography, `clearpage`, appendix, and a Supplementary Information section in the same manuscript. Route authoritative later appendix-ranked analyses there without retroactively editing this strategy.

1. **Extended control construction and variance identities.** Expand selected `src/METHOD.md` and `src/program.py`: deterministic finite-N variance/headroom, offset cancellation, shared-pool covariance, nested fitting, signed multipliers, spline penalties, critical values, clipping, fallbacks, and assumptions. Source IDs: `result.best_correct_score`, `final.evidence.episodes`. Existing `test_controls.py` is source, not a passed test report.
2. **Complete paired interval and coverage tables.** All conditions and methods, exact coverage counts, means, uncertainty, and missingness; retain principal comparisons in the body. Source IDs: `final.evidence.episodes`, `final.metric.nominal_coverage`, `final.metric.failure_fraction`.
3. **Rare outcomes and width-ratio definitions.** Identify zero-width episodes by seed; audit mean differences, ratios of means, and capped episode ratios from `task/evaluate_final.py`. Avoid undefined infinite averages and preserve baseline coverage uncertainty. Source IDs: `final.evidence.episodes`, `final.metric.mean_width_ratio`, `final.metric.empirical_coverage`.
4. **Frozen-source provenance and reproduction.** Use `task/resources/final/manifest.json`, `task/evaluate_final.py`, `task/requirements.txt`, selected code, and final manifests. Document 128 labels, 8192 unlabeled scores, seeds 1000–1399, pairing, normalized duplicate-group separation, empirical-source sampling, and hashes. Do not invent unrecovered synthetic generative equations from condition names: frozen arrays support replay. Map every final table/figure to its actual script and command when implemented; report only recorded runtimes. Independent NPZ redistribution rights remain unresolved; do not bundle data without permission. Source IDs: `final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome`, `result.best_correct_score`.
5. **Exploratory configuration comparisons and selection boundary — optional.** Existing 100-repeat search records can compare pooled-residual controls, offset-invariant risk-adaptive controls, and smooth stacking, with explicit adaptive-search caveats. No chronological ordering, causal-ablation claims, pooling with final repeats, unknown selection frequencies, or fabricated downstream-study counts. Omit if not scientifically useful. Source IDs: `result.top_program_01`, `result.top_program_02`, `result.top_program_03`, `result.best_correct_score`.
6. **LLM Usage.** Separate required disclosure of documented ideation, editing, and framing roles, adding the actual writer's role later. Do not invent human verification, tests, or reference consultation. Source IDs: `result.best_correct_score`, `final.evidence.episodes`.

## Writing, reference, and anonymity safeguards

- No isolated calibration ablations, parameter sweeps, oracle experiments, selection-frequency studies, extra real datasets, or predictor retraining are supported as completed final experiments.
- Most episodes do not contain repeated summaries. Read the summary at `final_evaluation.evaluation_evidence.episodes[0].solution.summary` and paired endpoints from each episode's `solution.cases`.
- A key-only scan of the newly retrieved bibliography exposed unscreened recent candidates. No associated abstracts, pages, or full texts were read here; no prohibited work was identified. Quarantine those entries rather than trying to infer the forbidden paper's identity. Bibliography and provenance presence do not establish safe or actually consulted references.
- Permitted exact PPI and Cross-PPI records are starting points. Resolve PPI++ only through permitted `arXiv:2311.01453` and use other permitted starter works only as needed. Avoid citation-graph expansion, related-paper feeds, and unscreened modern searches. Stop and log location/extent if prohibited content is encountered. Do not invent citations or novelty claims.
- Confirm official ICLR 2026 template provenance using venue-only sources before final submission. Remove the supplied template's named authors and final-copy author presentation; omit affiliations, acknowledgments, funding, and identifying links. Preserve the orchestrator-owned watermark. Do not invent a venue checklist requirement.
- Internal qualification fields and selection identifiers in this memo/JSON are **private audit context**, not recommended visible paper metrics or labels. Do not expose pipeline terminology in reader-facing tables or plots.

## Forbidden organization and wording

Avoid headings: Search Progression; Campaign Phases; Milestones; First Valid Result; Experiment A / Experiment B; Iteration History; From Baseline to Winner; Universal Interval Shortening; Certified Coverage of the Returned Method.

Avoid phrases: “we then tried,” “first valid result,” “subsequent improvements,” “next-best,” “winning iteration,” “state of the art,” “uniformly narrower,” “guaranteed nominal coverage for the returned intervals,” and “the nonlinear component caused the observed gain.” Also prohibit visible pipeline labels: `correctness rate`, `correct and eligible`, `eligible`, `combined_score`, `rubric`, `worker_01`, and `worker_02`.

## Stage boundary

This is a strategy, not a final paper. Do not create `paper.tex` or `claims_grounding.json`, render final figures, run concept generation, or invoke final-paper validation in this stage. Strategy/schema and evidence-consistency checks are appropriate. Missing citation consultation and template provenance are downstream completion requirements, not permission to fabricate either.
