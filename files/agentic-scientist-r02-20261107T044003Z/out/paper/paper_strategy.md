# Paper Framing Strategy

**Status:** ready · **Family:** paper_standalone · **Venue:** ICLR 2026

This is a planning memo, not a manuscript draft. No new experimental evidence is claimed.

## Title and Thesis

**Provisional title:** Adaptive ILR Ellipsoids: Coverage–Volume Trade-offs on the Simplex

**Central research question:** When does training-adaptive residual geometry improve the joint-coverage versus common-simplex-volume trade-off of split-conformal prediction regions for strictly positive compositional regression, and where does it fail?

**Central thesis:** In the tested synthetic regimes, externally calibrated adaptive ILR ellipsoids markedly reduce simplex-volume fractions under heteroskedastic logistic-normal responses, but nearly fill the simplex for near-boundary Dirichlet responses and remain below nominal coverage under covariate shift, so their empirical value is condition-dependent rather than uniformly superior.

## Why This Story

The strongest evidence is the frozen four-fold residual model evaluated against two evaluator-owned baselines on five final seeds, not the order in which three training configurations were explored. The common-volume measurement exposes a meaningful reversal: the adaptive model is much smaller in the heteroskedastic regime but substantially larger than the Euclidean comparator in the boundary and shifted regimes. Separate marginal coverage, descriptive subgroup coverage, and volume rather than letting an aggregate selection utility conceal these trade-offs. This supports a standalone empirical methodology study with explicit negative results, not a new conformal validity theorem or a comprehensive geometry benchmark.

## Prior Story and Staged Inputs

**Decision:** recentered. Fresh framing, not manuscript edit mode: no previous_paper directory, resolved edit-context file, aggregated directory, or extra_tasks directory is present. Here recentered means narrowing the source-task agenda and unevaluated proposal language to the actually implemented ILR family; it does not imply that a prior manuscript was revised. No old title, question, or figure plan is inherited.

- The inspected selected implementation uses deterministic four-fold held-out ILR location residuals, a full-training location refit, scale regression, and training-frozen boundary-tertile covariance shrinkage; it does not implement Hellinger scores or group-specific conformal calibration.
- The inspected evaluator supplies valid Euclidean-simplex and isotropic-ILR comparators and six condition blocks; these are four synthetic regimes plus two matched interventions derived from the heteroskedastic regime, not six independent datasets.
- The independent final evaluation is completed and qualified, grounded in final.qualification.status and final.qualification.outcome. Its qualification is not a nominal-coverage or superiority guarantee; the final evidence must still disclose undercoverage, volume failures, and missing diagnostics.
- No downstream_study is present, so no study.* selection facts or scored/unscored classifications can be invented. Use the available result.* sources and all_programs evidence for search context only. The named original starter has source code but no separately grounded baseline measurement in this bundle; do not fabricate its performance.
- The local ICLR template and paper.sty establish a single 5.5-inch text column and 9-inch text height; this replaces any generic two-column figure assumption.
- The bibliography and provenance are present, but many retrieved entries concern unrelated compositional applications and the key permitted foundational sources are not yet represented; literature completeness and source reading require targeted follow-up, not padding or unchecked citations.

## Methods Worth Including

- **Euclidean-simplex split-conformal balls (baseline):** Evaluator-owned ridge predictions in composition coordinates, clipped and renormalized, with Euclidean residual calibration and simplex-intersected membership; essential because adaptive ILR does not dominate this comparator in volume.
- **Isotropic ILR split-conformal balls (baseline):** Evaluator-owned ridge locations in ILR coordinates with an unscaled residual norm; isolates a meaningful coordinate-space reference using the same external calibration and simplex-volume measure, without claiming a matched-training-size mechanism ablation.
- **Four-fold residual adaptive ILR ellipsoids (proposed):** Frozen selected model and sole adaptive method with released final evidence; describe as the studied configuration rather than an established novel algorithm or universal winner.
- **Single-split residual adaptive ILR ellipsoids (ablation):** Three search-seed measurements support a limited direct comparison with the four-fold configuration; the change bundles residual fitting, full-data location refitting, and training-data allocation, so it cannot identify a pure cross-fitting effect.
- **Continuously interpolated covariance ellipsoids (ablation):** Three search-seed measurements test continuous covariance interpolation against hard routing while retaining four-fold residual fitting; show no established advantage and keep this auxiliary branch out of the central thesis.

## Results That Carry the Thesis

- Primary final comparison: show nominal 90% joint coverage and normalized common-simplex volume separately for the frozen adaptive model and both baselines in all six conditions, with four regimes visually separated from the two matched controls.
- Heteroskedastic logistic-normal evidence: final five-seed means are coverage 0.904375 and volume 0.147566 for adaptive ILR, versus 0.903021/0.333621 for Euclidean and 0.903438/0.335896 for isotropic ILR; smaller measured sets at similar observed marginal coverage, not proven population dominance.
- Boundary and shift limitations belong in the main results: near-boundary volume is 0.975856 versus 0.715514 for Euclidean; shifted coverage is 0.863281 versus 0.859219 for Euclidean and 0.708177 for isotropic ILR. The adaptive model has larger shifted volume than Euclidean (0.622107 versus 0.192813), so coverage and efficiency must be interpreted jointly.
- Final equal-weight summary is coverage 0.894158 and volume 0.544618. Adaptive-minus-baseline coverage differences are -0.001441 for Euclidean and +0.025052 for isotropic ILR; baseline-minus-adaptive volume differences are -0.034631 and +0.049603 respectively. This average includes the two C2-derived controls and is not a broad population estimate.
- Use the released paired seed-bootstrap intervals only for the equal-weight six-condition contrast they estimate: coverage versus Euclidean [-0.006536, 0.003854], volume reduction versus Euclidean [-0.054606, -0.011514], coverage versus isotropic ILR [0.018516, 0.031884], and volume reduction versus isotropic ILR [0.030559, 0.061766]. They are exploratory five-seed intervals, not multiplicity-corrected generalization guarantees or per-condition intervals.
- Subgroup reliability: plot the evaluator’s four overlapping covariate-sign strata for heteroskedastic and shifted conditions. Training boundary tertiles and evaluation sign strata are different objects. Preserve the reported worst-stratum summary of 0.0 and explain that empty negative-sign strata in the constant-input control were encoded as zero; never call that an observed zero-coverage subgroup.
- Auxiliary search comparison: compare three configurations directly on common search seeds 101, 211, and 307, separate from final seeds 1009, 2027, 3049, 4051, and 5059. Show coverage and volume, not a best-so-far trace. No final evaluation exists for the two auxiliary configurations in the released bundle.
- Controls validate specific observed operations, not scientific superiority: constant covariates and training-pair derangement test information dependence; point-copy singleton and full-simplex checks anchor membership semantics; query-order invariance and replay check fixed predictions. Do not interpret their completion as conditional validity or real-data reliability.

### Final-Evidence Sanity Table

Five-seed arithmetic means from `final.evidence.episodes`; values rounded to six decimals. Each entry is joint coverage / normalized simplex volume. These are not population estimates or new runs.

| Condition | Adaptive ILR | Euclidean | Isotropic ILR |
| --- | --- | --- | --- |
| C1: Homoskedastic logistic-normal | 0.898333 / 0.128591 | 0.900052 / 0.178176 | 0.899115 / 0.128429 |
| C2: Heteroskedastic logistic-normal | 0.904375 / 0.147566 | 0.903021 / 0.333621 | 0.903438 / 0.335896 |
| C3: Near-boundary Dirichlet | 0.894740 / 0.975856 | 0.899167 / 0.715514 | 0.901615 / 0.999998 |
| C4: Covariate-shifted Dirichlet | 0.863281 / 0.622107 | 0.859219 / 0.192813 | 0.708177 / 0.614458 |
| C5: Constant-covariate control | 0.901927 / 0.693161 | 0.905417 / 0.816604 | 0.901771 / 0.740298 |
| C6: Training-pair derangement control | 0.902292 / 0.700424 | 0.906719 / 0.823189 | 0.900521 / 0.746242 |

C5 and C6 are matched C2-derived interventions, not new datasets. Baseline training allocation differs from the proposed model. This table does not establish isolated geometry effects.

## Figure and Layout Plan

The actual `paper.sty:48` and `paper.sty:49` give a 9-inch text height and 5.5-inch text width. This is a single-column format: full-width means the entire one-column text block, never a two-column `figure*` assumption. Plan all required figures at 5.5 inches, with approximately 9-point final-size labels.

### geometry_calibration_overview — Required

**Purpose:** Provide early glance value: strictly positive composition responses, three region geometries, training-only adaptive factors, independent calibration, and separate coverage/common-volume evaluation.

**Type / generator:** diagram / generate-concept-figure.

**Grouping / metric / split:** training_calibration_evaluation / none_conceptual / information_partition.

**Placement and footprint:** Approximately 0.22 body page including caption; three stages within one cohesive panel, not three separate subfigures.

**Geometry:** full_width, width fraction 1.0. The inspected ICLR style has one 5.5-inch text column. A shallow 5.5 by about 1.55-inch overview on page 1 or 2 gives three stages enough room for 9-point labels without turning the figure into a dense algorithm listing.

**Readability budget:** at most 1 panels, 1 per row, 6 categories per panel, and 3 series per panel. No progression view.

At most six labeled nodes, three method-color keys, short stage titles, and no measured-looking toy scatter or invented region sizes. A simplex icon is conceptual, explicitly not experimental data.

Editable draw.io source and deterministic export; use a PDF if produced from source. The designated workflow may be raster-only, in which case regenerate at at least 2400 px wide, never upscale.

**Grounding:** `final.evidence.episodes`.

### coverage_volume_by_regime — Required

**Purpose:** Expose regime-specific benefits and failures without collapsing reliability and efficiency into one score.

**Type / generator:** paired_dot_plot / matplotlib.

**Grouping / metric / split:** region_geometry / joint_coverage_and_normalized_simplex_volume / synthetic_condition.

**Placement and footprint:** Approximately 5.5 by 3.4 inches plus caption, about 0.45 body page, near the start of main results.

**Geometry:** full_width, width fraction 1.0. Use the full single-column 5.5-inch width, two stacked panels, and a common six-condition x-axis. Six short labels and three consistently colored series fit at 9-point final-size text; a half-width rendering would make method offsets, seed dots, and uncertainty unreadable.

**Readability budget:** at most 2 panels, 1 per row, 6 categories per panel, and 3 series per panel. No progression view.

Three methods, five faint seed points and one mean marker per condition; no fourth decorative series. Use a dashed 0.90 line only in the coverage panel. Volume uses the unit-simplex fraction scale. Separate the two matched controls with a vertical rule, not a chronology arrow.

Show seed dispersion directly. Do not repurpose the released aggregate bootstrap intervals as condition-specific error bars; keep Wilson intervals and Monte Carlo errors in the detailed table or supplement.

Reproducible plotting source must export PDF and PNG at 300 DPI; LaTeX must include the PDF whenever available.

**Grounding:** `final.evidence.episodes`, `final.metric.marginal_coverage`, `final.metric.normalized_volume`.

### descriptive_sign_strata — Required

**Purpose:** Show why near-nominal marginal coverage need not imply local reliability, while preserving the distinction between descriptive diagnostics and coverage guarantees.

**Type / generator:** stratum_dot_plot / matplotlib.

**Grouping / metric / split:** region_geometry / empirical_joint_coverage_in_covariate_sign_stratum / heteroskedastic_and_shifted_regimes.

**Placement and footprint:** Approximately 5.5 by 2.25 inches plus caption, about 0.32 body page, in reliability and failure analysis.

**Geometry:** full_width, width fraction 1.0. Two approximately 2.6-inch panels share one full-width 5.5-inch figure and one legend. Four short sign labels per panel and 9-point text fit without shrinking. The two regimes are scientific contrasts, not a temporal sequence.

**Readability budget:** at most 2 panels, 2 per row, 4 categories per panel, and 3 series per panel. No progression view.

Only the four masks x1<0, x1>=0, x2<0, x2>=0, three methods, common y-axis limits, and one nominal line. Masks overlap across covariates and are not a four-way partition. Training-defined boundary groups are not depicted as evaluated coverage groups.

Show all five final-seed stratum rates and their means without unsupported simultaneous intervals. Empty strata are missing observations, never zero-rate plotted points; preserve the original zero-valued aggregate separately in the main text.

Export PDF and PNG at 300 DPI from plotting source; reference PDF from LaTeX.

**Grounding:** `final.evidence.episodes`, `final.metric.worst_stratum_coverage`.

### search_configuration_comparison — Optional Supplement

**Purpose:** Document the limited measured comparison of residual fitting and shape routing without asserting an isolated mechanism or a final generalization result.

**Type / generator:** paired_dot_plot / matplotlib.

**Grouping / metric / split:** training_configuration / joint_coverage_and_normalized_simplex_volume / search_condition.

**Placement and footprint:** About half a supplementary page; include only if a compact direct-comparison table does not already communicate the same evidence.

**Geometry:** full_width, width fraction 1.0. Supplementary single-column figure uses the same 5.5-inch two-stacked-panel design as the main comparison, preserving method labels and raw three-seed dispersion.

**Readability budget:** at most 2 panels, 1 per row, 6 categories per panel, and 3 series per panel. No progression view.

Use search episodes under all_programs, not the final episodes; export PDF and 300-DPI PNG from source and include PDF.

**Grounding:** `result.top_program_01`, `result.top_program_02`, `result.top_program_03`.

## Page Budget and Scientific Depth

Body plan targets 8.5 single-column pages, within the 8–9 page requirement: abstract/introduction 1.10; focused related work 0.65; prediction target and measurement rationale 0.90; method and assumptions 1.45; experimental protocol 0.90; primary comparisons 1.35; reliability, failure analysis, and compact configuration comparison 1.20; discussion/limitations/conclusion 0.95. These are planning allocations, not measured page counts; figures and captions are included, references and supplement are excluded. If ending at eight pages, page eight must be at least 75% full.

Use substantive depth to fill the format: distinguish random continuous composition responses from class labels and unidentified latent probabilities; explain why ILR and Euclidean volumes are measured in the same simplex measure; give the training/calibration information boundary; show per-condition reversals and all key failure caveats. Do not pad with a search diary, broad unrelated related work, large whitespace, redundant plots, or invented ablations.

Section order: Introduction; Related Work; Prediction Target and Evaluation; Training-Adaptive ILR Regions; Experimental Protocol; Coverage–Volume Trade-offs; Reliability and Failure Modes; Discussion and Limitations; Conclusion. After references, include Supplementary Information and the required separate LLM Usage section. Keep essential limitations, final status, and uncertainty in the main body.

## Supplementary Information After References

Provide implementable method detail, full retained diagnostics, and reproducibility without hiding the core boundary-volume, shift-undercoverage, uncertainty, or empty-stratum limitations from the main paper.

### Training-Fitted ILR Geometry and Numerical Details

Transcribe the inspected selected fit_model: quadratic features for five covariates, four deterministic index-modulo folds, location ridge penalty 0.01, full-data refit, log residual-square offset 0.02 and ridge penalty 5, scale clipping [-6,5], standardized-residual clipping at 1000, pooled identity weight 8, group shrinkage weight 32, right-sided tertile routing, and the fewer-than-four-row fallback. Give equations for scores and Cholesky factors; do not turn training shape estimation into groupwise calibration.

**Grounding:** `result.top_program_01`, `final.evidence.episodes`.

### Synthetic Generators and Matched Interventions

Describe evaluate_final.py generate_raw and make_episode_data with the final manifest: logistic-normal versus Dirichlet responses, dimensions 3 and 8, five Gaussian covariates, heteroskedastic scales, positivity handling, test-only coordinate shift and rescaling, and C2-derived constant-input/training-pair interventions. Include only existing generator parameters and manifest hashes; no real dataset, structural-zero experiment, or additional sweep.

**Grounding:** `final.evidence.episodes`.

### Complete Seed-Level Coverage and Common-Volume Tables

All thirty final seed-condition records for three methods, retained test coverage Wilson intervals, per-anchor volume fractions, Monte Carlo integration errors, paired volume integration errors, and all descriptive sign-stratum rates. State that Wilson intervals condition on a fitted/calibrated region and that integration errors condition on the selected anchors and sets; neither replaces between-seed uncertainty. Flag empty sign strata with their operational zero encoding rather than silently dropping or reinterpreting the original aggregate.

**Grounding:** `final.evidence.episodes`, `final.metric.worst_stratum_coverage`.

### Auxiliary Training-Configuration Comparisons

Direct search-seed tables from all_programs[*].evaluation_evidence.episodes for single-split versus four-fold geometry and four-fold hard routing versus continuous covariance interpolation, plus optional Figure S1. These are three-seed selection-data comparisons, not final replications. The single-split comparison bundles several training changes, and the interpolation contrast has no demonstrated benefit. No Hellinger, groupwise calibration, shrinkage sweep, or isolated full-data-refit ablation is available.

**Grounding:** `result.top_program_01`, `result.top_program_02`, `result.top_program_03`, `result.total_attempts`, `result.total_evaluated_programs`.

### Uncertainty Estimands and Audit Controls

Document evaluator quantile rank ceil((n_cal+1)*0.9), shared uniform-Dirichlet probes (64 anchors times 4096 probes per final condition), paired resampling of five seeds with all six cases retained together, and the released few-seed warning. Tabulate observed singleton/full-simplex, query-invariance, matched-intervention, and replay checks. Do not infer any unreported validity/adaptivity diagnostic. Preserve final completed/qualified status independently of all observed performance failures.

**Grounding:** `final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`.

### Reproducibility and Evidence Provenance

List existing final/search resource manifests, dataset hashes, selected source path, evaluator and selected-program tree hashes, released seed lists, Python environment information where actually available, NumPy requirement 2.2.6, and evaluation/figure-generation entrypoints. Private-entropy resources must be distributed or explicitly declared necessary; seeds alone do not recreate the released final arrays. Distinguish observed evaluation elapsed time from unmeasured hardware-specific reproduction estimates. Audit bibliography/provenance scope, permitted source reading, and any prohibited-source encounter log without inventing a clean history.

**Grounding:** `final.evidence.episodes`, `result.top_program_01`, `final.qualification.status`.

### LLM Usage

Disclose the documented use of LLM agents for ideation, implementation assistance, reference planning, and paper framing/writing, while attributing numerical results to the evaluator-owned executable computations. Describe actual roles only; do not invent independent human review or identify authors, private services, paths, or repositories.

**Grounding:** `result.total_ideas`, `result.total_attempts`.

## Rejected Framings

- Broad proposal preservation: alternative score geometries and group calibration are not implemented.
- Comprehensive cross-geometry comparison: the evaluated method family is much narrower.
- Pure cross-fitting improvement: residual fitting, full-data location refit, and data allocation change together.
- Boundary or shift robustness: contradicted by retained volume and coverage limitations.
- Search-winner chronology: weaker than final paired scientific comparisons and irrelevant to the thesis.

## Headings and Language to Avoid

**Forbidden headings:** Search Progression; Campaign Phases; First Valid Result; Milestones; Best-So-Far Results; Cycle 1 / Cycle 2 / Cycle 3; Experiment A / Experiment B; From Failure to Success; Winning Program; Correctness and Eligibility.

**Forbidden visible phrases:** `correctness rate`; `correct and eligible`; `combined_score`; `rubric`; `worker_01`; `worker_02`; `eligible`; `our winning program`; `first successful attempt`; `then we tried`; `the next cycle improved`; `best-so-far trajectory`; `Hellinger reliability audit as the implemented method`; `group-calibrated guarantees`; `cross-fitting guarantees conditional coverage`; `universally superior`; `state of the art`; `robust to covariate shift`; `zero coverage in an observed constant-input subgroup`; `six independent datasets`.

These prohibited strings appear here only as private writing constraints, not recommendations for visible manuscript language.

## Writer, Review, and Revision Guardrails

- Write a standalone empirical study, not a final manuscript at this strategy stage. No paper.tex, claims_grounding.json, new experiment, rendered figure, external retrieval, or final-paper validation is authorized here. A later writer must use the standalone skill with the venue constraints taking precedence over generic template defaults.
- Layout is grounded in paper.sty lines 48–49: one text column, 5.5 inches wide and 9 inches high. Here full_width and column width coincide; full_width means the entire text block, not a two-column float. Use approximately 9-point minimum final figure labels, one consistent method-color palette, and no more than three panels per row. Do not shrink a dense panel to rescue layout.
- Only one overview uses generate-concept-figure; plan its early location, six-node content budget, editable source, and prompt provenance. It is a conceptual schematic, not a data figure or invented measured simplex illustration. The later writer wires this generator according to the standalone workflow; this strategy stage does not invoke rendering.
- Every quantitative plot must be reproducible from the released JSON and export PDF plus 300-DPI PNG; LaTeX uses PDF when available. Raster-only overview output must be regenerated at least 2400 pixels wide for this full-width plan. Any later column-width raster must be at least 1200 pixels wide. Never upscale an existing image.
- Private-only grounding context: final.qualification.status=completed, final.qualification.outcome=qualified, and final.qualification.correct=true. Record the evaluator’s completed qualification honestly, but translate to a modest reader-facing audit statement rather than an accuracy/acceptance badge. No failed final qualification occurred in these artifacts; preserve any failure in future revisions if the authoritative status changes, without guessing its statistical, validity, or adaptivity cause.
- Private-only search provenance: result.total_attempts=3 and result.total_evaluated_programs=3, each with three released scored episodes; do not infer additional attempts or measured losses from missing records. Search ordering selects the four-fold hard-routing configuration (result.top_program_01); its internal selection utility is 0.8818756857036072 versus 0.8776261506257234 for the single-split configuration and 0.8818118342646846 for interpolation. These scores are not final evidence and need not appear visibly; if ever required, describe the explicitly defined coverage-volume utility, not a pipeline field name.
- There is no downstream_study, hence no study.* score-difference or attempt-status source. Do not import the bootstrap incumbent score from memory. The evaluator-owned Euclidean and isotropic ILR comparators remain the valid scientific baselines; the original starter is source-only unless additional authoritative measurements are supplied.
- Exact final evidence path in paper_data: final_evaluation.evaluation_evidence.episodes[*].solution.cases[*].details contains candidate and baselines.{euclidean,ilr}; shared intervals are solution.paired_seed_bootstrap_comparisons95, repeated across episodes but representing one bootstrap analysis, not five independent intervals. The four interval entries are coverage difference versus Euclidean, volume reduction versus Euclidean, coverage difference versus isotropic ILR, and volume reduction versus isotropic ILR.
- The main experiment has 4096 training, 2048 calibration, and 3840 test rows per final condition; the independent calibration quantile rank is 1845 at alpha=0.1. Baseline locations use the first 75% of training rows while the selected model refits on all training rows. Therefore the primary comparison is between end-to-end configurations, not an isolated covariance geometry intervention or a training-size-matched causal test.
- Expected theorem scope only: frozen training-derived scores plus independent exchangeable calibration/test pairs permit the ordinary split-conformal marginal guarantee for future continuous compositions. Explain the standard rank argument without claiming a new theorem. The shifted condition is not exchangeable with calibration; external calibration does not guarantee target-domain or conditional coverage. Do not label this model jackknife+, CV+, or conformalized group calibration.
- Condition-specific numbers in this strategy are deterministic averages of the five released final seeds, rounded to six decimals, not new experiments. Show individual seeds in figures and clarify what each uncertainty quantity conditions on. No per-condition bootstrap interval is released; do not create one by relabeling the aggregate interval.
- The reported worst-stratum summary 0.0 is an empty-mask encoding artifact in the constant-input control, not evidence of zero conditional coverage. The evaluator does not retain per-mask sample counts or test covariates in the episode JSON. A count-based reanalysis requires the available resource arrays and the exact intervention; do not invent denominators or silently replace the registered statistic. Any recomputed nonempty-mask summary must be explicitly new derived analysis and retain the original.
- The held-out evaluation reduces direct selection reuse, but five seeds and a small synthetic design do not establish a broad nonadaptivity audit, robustness certification, or real-data generalization. Candidate self-diagnostics are explicitly unverified; use evaluator-owned measured fields and documented checks, not speculative candidate reports.
- The final resource generator uses private entropy and stored arrays; public seed integers alone are insufficient to reconstruct those draws. Reproduction must preserve the distributed NPZ resources and manifest hashes or state this limitation. Do not claim an exact regenerate-from-seed pipeline that the artifacts do not support.
- Current references_provenance.json has 25 metadata-grounded entries, including ellipsoidal conformal work but many off-topic compositional applications. Do not cite all entries or claim to have read their full texts. Resolve permitted foundational split-conformal and ILR background through conservative allowed-title lookup and actual source reading before drafting; no invented keys, no task-identifying search or citation chaining, and stop/log any prohibited encounter. The present strategy is not a novelty certification.
- Use the anonymous ICLR 2026 venue brief: omit names, affiliations, acknowledgments, funding, and identifying links. The seeded template’s author placeholder and final-copy command are not permission to deanonymize. Keep its required watermark while anonymizing the submission; make the actual LLM roles explicit in the separate disclosure section.
- Interpret other framings explicitly: preserving the broad proposal would claim unimplemented methods; broadening to all conformal geometry families would lack evaluated comparisons; a pure cross-fitting improvement story would overattribute bundled changes; a boundary-robustness story would contradict near-full-simplex volume and shifted undercoverage. The chosen shared thesis across regime-specific evidence is stronger than each alternative.
- Source IDs identify available evidence categories; method formulas and generator details additionally require direct code references to results/ideas/02_cross_fitted_ilr_residual_geometry/program_1/src/program.py, task/evaluate_final.py, and task/resources/final/manifest.json. Auxiliary seed-level comparisons live in all_programs[*].evaluation_evidence, not in scalar ranking entries alone. Do not pretend a metric source proves a code-level mechanism.
- No later posthoc ranking is known at this stage. Route future authoritative appendix-ranked material to the supplement without retroactively changing this plan or promoting unsupported analyses; keep all evidence essential to the thesis in the main paper.

## Decision and Remaining Work

The evidence supports the selected standalone family. No strategy failure is declared. Qualification is completed/qualified in this run; observed scientific failures and missing diagnostics remain explicit. The next stage must implement the figure specifications, complete allowed literature grounding, write the manuscript and reproducibility materials, and perform that stage’s validation. This strategy stage must not draft `paper.tex`, write `claims_grounding.json`, or run final-paper validation.

## Writer Validation Vocabulary Note

The quantitative type labels `paired_dot_plot` and `stratum_dot_plot` were normalized to the canonical manifest enum `scatter` in the matching JSON. Data, grouping, budgets, scientific purpose, and generator ownership are unchanged. The overview remains orchestrator-owned and is not rendered by the writer.
