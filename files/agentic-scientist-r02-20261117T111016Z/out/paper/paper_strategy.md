# Paper Strategy

## Decision

**Status:** ready for `paper_standalone`, using `write-paper-standalone` for the later manuscript stage. This is a plan, not a paper draft.

**Provisional title:** Scale-Adaptive Compositional Conformal Regions: Reliability and Limits

**Central question:** Across the tested synthetic response distributions, dimensions, and covariate regimes, how do training-only scale-adaptive ILR conformal regions trade observed-composition coverage against uniform-simplex region mass relative to matched-center alternatives?

**Central thesis:** In the six tested synthetic settings, scale-adaptive ILR regions exhibit condition-dependent reliability–efficiency trade-offs rather than uniform dominance: near-target IID coverage coexists with shifted Dirichlet undercoverage, and higher aggregate utility does not imply smaller simplex regions or conditional validity.

The paper is one controlled empirical study of a fixed region family. Logistic-normal IID, Dirichlet IID, and shifted Dirichlet conditions, each at K=3 and K=8, are evidence blocks under the same question—not sequential experiments or a claim of transfer to arbitrary domains. The scientific value is a reproducible method specification and a reliability–efficiency assessment with concrete failures, not a claim that a small aggregate gain establishes a new universally superior method.

## Framing Decision and Alternatives

No edit context, seeded prior manuscript, `aggregated/`, or `extra_tasks/` bundle is present. The JSON decision `recentered` means narrowing the original broad task and proposed geometry audit to actual evaluated evidence; it does not assert that a prior paper was rewritten.

| Candidate framing | Decision and grounded reason |
| --- | --- |
| Preserve an earlier broad geometry/boundary audit with local updates | Reject. No prior manuscript is available, and Hellinger/Euclidean geometry comparisons, structural-zero face audits, and Mondrian calibration were proposed rather than demonstrated. |
| Broaden into a cross-setting conformal method family | Retain only within the six synthetic conditions sharing the fixed ILR construction. No real-data, architecture, classification-label, or alternative-geometry transfer evidence supports a larger family claim. |
| Recenter on rank-selector superiority | Reject as the central thesis. Source code supports the mechanism, but the final evidence lacks a matched Gaussian-versus-rank selector ablation. Search-plane configurations do not establish a causal final-plane gain. |
| Recenter on reliability–efficiency trade-offs of the frozen scale-adaptive regions | Select. Final paired comparisons, independent calibration, multiple nominal levels, and uncertainty records support both favorable IID behavior and adverse shifted results. |

Inspecting the selected source materially narrows the story: fixed Helmert ILR ridge centers, positive diagonal base scales, a bounded covariate-dependent scalar local-moment correction, and nested training-only rank/ILR-box-volume selection. The scalar correction is common to the ILR coordinates for a given covariate vector; it is not a separately learned full covariance geometry.

## Final Evidence and Qualification

Read `paper_data.json.final_evaluation` independently of any campaign summary. `downstream_study` and `study.*` grounding entries are absent. The final qualification sources explicitly report:

- `final.qualification.status`: `completed`.
- `final.qualification.outcome`: `qualified`.
- `final.qualification.correct`: `true`.

There is no failed qualification to disclose in this run. Qualification nevertheless does not establish superiority, conditional coverage, or generalization. If authoritative later artifacts report failed qualification, preserve that outcome and its limitations in writing, review, audit, and revision. Attribute a failure to statistical performance, validity, or adaptivity only when evaluator diagnostics identify the cause; missing gate diagnostics remain unknown.

`final.evidence.episodes` contains eight final seed blocks, with six completed cases per seed and three alpha values per case. Final seeds are 1009, 1013, 1019, 1021, 1031, 1033, 1039, and 1049. Nominal coverage levels are 0.95, 0.90, and 0.80. This is not a set of independent case-by-alpha replications: seeds are the outer repeated unit. The identical uncertainty summary repeated under each seed wrapper must be read once.

Important grounded anchors:

| Quantity | Value and grounding |
| --- | --- |
| Studied method's mean IID absolute coverage error | 0.013562011718750005; `final.metric.iid_coverage_error` |
| Studied method's mean shifted absolute coverage error | 0.13034261067708333; `final.metric.shift_coverage_error` |
| Studied method's mean uniform-simplex mass | 0.3034934467739529; `final.metric.mean_volume` |
| Studied method's mean utility | 0.661819668104677; `final.metric.final_score` |
| Gap to the largest aggregate utility among standard evaluator comparators | 0.011594669497844157; `final.metric.baseline_utility_gap` |
| Simplex-coordinate L-infinity mean mass | Approximately 0.291701, derived from evaluator method records under `final.evidence.episodes` |

These are retained measurements, not certification of a significant aggregate advantage. In particular, larger mean mass than the simplex-coordinate comparator contradicts a blanket size-improvement claim. Absolute coverage error is not signed undercoverage; signed coverage must be shown separately. The existing overall score interval cannot establish a confidence interval for the difference between methods.

The wrapper labels candidate diagnostics as unverified. Use evaluator-owned membership and method statistics, not candidate assertions. Preserve evaluator/program/result hashes in the audit trail. The available selected source is linked by configuration records; do not assert that a locally recovered final source tree has been independently rehashed when it has not.

## Method Groups and Comparison Roles

1. **Training-only scale-adaptive ILR regions — studied/proposed configuration.** Explain the center, base scale, correction family, training-only selector, and independent pooled calibration. “Proposed” is an organizational role, not a claim of unique novelty.
2. **Unscaled ILR — matched-center ablation.** Set scales to one, retaining the same center and ILR basis. This compares the whole scaling package against no scaling; it does not isolate the correction or selector.
3. **Simplex-coordinate L-infinity — primary direct baseline.** Use the inverse-ILR center and a joint maximum-coordinate residual. Include all comparisons, not only conditions favoring the studied method. Its largest aggregate utility among standard comparators is an observed result, not a preregistered comparator-selection rule.
4. **Coordinatewise Bonferroni — simultaneous-coordinate baseline.** Use per-coordinate ranks at alpha/K. Include in the main summary table and complete supplemental comparisons.
5. **Feature-information and degenerate-region controls — supporting diagnostics.** Constant-center, constant-input, permuted-input, whole-simplex, and zero-radius records assess feature information and metric endpoints. They are not additional deployable method families or conditional-validity evidence.

The original initializer source exists, but matched final performance records for it do not. Omit that performance comparison; do not relabel the unscaled ablation as the original initializer. Describe the archived joint-center/scale and Gaussian-selector configurations only in supplementary provenance as search-only alternatives, not final ablations. Without `study.*`, omit campaign winner claims, search-score margins, and scored/unscored accounting. Missing measurements must never become measured losses.

## Scientific Organization and Results Views

Use these body sections:

1. Introduction.
2. Related Work.
3. Prediction Regions and Evaluation Targets.
4. Training-only Scale Adaptation.
5. Experimental Design and Uncertainty.
6. Reliability–Efficiency Results.
7. Discussion and Limitations.
8. Conclusion.

The contribution list should be limited to a reimplementable training-only configuration, a matched-center evaluation separating reliability from region mass, and empirical condition-dependent findings with failure diagnostics. No new conformal theorem, comprehensive benchmark, or causal selector improvement is established.

The main results should answer three scientific questions:

- **Does measured coverage track the target?** Show all nominal levels, with IID and shifted conditions separate. Shift failure belongs in the body, not only the supplement.
- **When does scaling change the trade-off?** The IID Dirichlet K=8 comparison is informative, but retain the logistic-normal K=3 counterexample and shifted Dirichlet utility reversals. No uniform dominance claim survives those comparisons.
- **Does a higher utility mean smaller or more reliable regions?** No. Show separate coverage and mass alongside utility. Explain that the training selector minimizes an ILR-box surrogate, whereas evaluation uses uniform-simplex mass. Different measures are factual; their causal contribution to the observed results is unresolved.

Include one compact main table with four method rows and columns for IID absolute coverage error, shifted absolute coverage error, mean reference mass, and utility. Recompute baseline aggregates from the final records using saved code. Equal weighting is across seeds, cases, and nominal levels, not a pooled mixture weighted by subgroup sample counts. Define utility rather than using an internal score label:

`U = (1 - V) max(0, 1 - |coverage - (1-alpha)| / (1-alpha))`.

Its error penalty includes overcoverage; it is a benchmark-specific summary, not a validity test or a standardized universal objective. Do not use a thresholded success-rate figure.

## Required Figures and Layout

The supplied ICLR template uses `article` and `paper.sty`. The inspected style sets one **5.5-inch text column** and **9-inch text height**. Here full-width and column-width refer to the same physical text width; there is no two-column `figure*` assumption. A 0.48-width inset would be approximately 2.64 inches and is unsuitable for these dense comparisons. The required figures use about 5.39 inches at fraction 0.98. Keep final-size labels at least 9 pt and shorten labels instead of shrinking a crowded figure.

### Figure 1 — `composition_reliability_overview`

- **Purpose:** immediate understanding of observed-composition prediction, training/calibration separation, and coverage versus reference mass.
- **Generator:** `generate-concept-figure`; exactly one overview uses this workflow. Do not render it in this stage.
- **Footprint:** full text width, approximately 5.39 by 1.6 inches; about 0.30–0.35 page including caption. Place on page 1 if natural, otherwise page 2.
- **Readability budget:** at most three panels in one row, six short nodes/categories per panel, and two information streams per panel; labels 9–10 pt.
- **Content:** training-only center/scale fitting and local-moment/rank-volume selection; separate finite-rank calibration; observed-composition membership and uniform-simplex probe evaluation across IID/shift. Pseudo-calibration stays inside the training partition. Label the ILR surrogate and simplex evaluation measure distinctly.
- **Grounding:** `final.evidence.episodes`; selected source at `results/ideas/03_training_only_conformal_rank_scale_selection/program_1/src/program.py`; evaluator definitions in `task/evaluate_final.py`.
- **Cautions:** no invented region measurements, alternative geometries, architectural blocks, or arrows implying a proven causal gain. This is a scientific data-partition schematic, not a research-run timeline.

### Figure 2 — `coverage_by_regime`

- **Purpose:** show near-target IID coverage and shifted Dirichlet deficits across every target level.
- **Generator:** matplotlib calibration curves, not a search progression plot.
- **Footprint:** full text width, approximately 5.39 by 2.45 inches; about 0.40–0.45 page with caption. Two panels side by side for K=3 and K=8.
- **Readability budget:** two panels; three target positions; three regime curves plus the identity reference, at most four series total per panel. Share axes and legend.
- **Content:** studied method only, target coverage 0.80/0.90/0.95 versus empirical coverage; logistic-normal IID, Dirichlet IID, and Dirichlet shift. Baseline evidence remains in Figure 3 and the main table. Use the observed coverage range and explicitly mark a truncated axis rather than flattening IID differences with an unhelpful zero origin.
- **Uncertainty:** the writer may derive deterministic 95% seed-block percentile intervals from the eight existing coverage records, resampling seeds jointly across cases and targets. These intervals are a later analysis of retained measurements, not an already available stored mean-coverage interval. Do not average per-episode Wilson endpoints.
- **Grounding:** `final.evidence.episodes`, `final.metric.iid_coverage_error`, and `final.metric.shift_coverage_error`.

### Figure 3 — `paired_region_tradeoffs`

- **Purpose:** directly show condition-dependent utility and region-mass differences against simplex-coordinate L-infinity, including adverse shifted comparisons.
- **Generator:** matplotlib paired dot-and-whisker comparisons.
- **Footprint:** full text width, approximately 5.39 by 4.2 inches; about 0.60–0.70 page including caption. Four panels in a 2-by-2 grid; rows are K and columns are utility difference versus mass difference.
- **Readability budget:** four panels, two per row; three regime categories and three alpha markers per panel. Shared scales within each metric column; a common legend and zero-reference lines.
- **Content:** scaled ILR minus comparator, for every regime at alpha 0.05/0.10/0.20. Utility above zero favors scaled ILR; mass below zero indicates smaller regions. State both sign meanings explicitly rather than inventing one common success threshold.
- **Uncertainty:** use `utility_difference`/`paired_seed_bootstrap95` and `volume_difference`/`paired_volume_bootstrap95` under each case's `paired_baselines.simplex_linf`. Descriptive 95% intervals are not simultaneous certificates. The stored adjusted utility endpoints are supplemental context and must not be applied to mass differences.
- **Grounding:** `final.evidence.episodes` and `final.metric.baseline_utility_gap`.

Use consistent condition colors across the overview and plots; alpha can use marker shape and methods can use labels/line style. Never reuse a condition hue to mean a different method or threshold. Export quantitative figures from reproducible source as **PDF plus PNG at 300 DPI**, and reference the PDF from LaTeX. Preserve overview draw.io source and prompt logs; use a vector PDF export if available. Raster-only full-width figures require at least **2400 px** width, and any future column-width raster inset requires at least **1200 px**. Regenerate from source; never upscale an existing raster.

## Body Budget and Venue Fit

Target about **8.6 body pages**, excluding references, within `VENUE.md`'s 8–9 page requirement:

| Body material, including its figures/tables | Approximate pages |
| --- | ---: |
| Abstract, introduction, and early overview | 1.20 |
| Related work | 0.55 |
| Prediction regions and estimands | 0.90 |
| Training-only scale-adaptation method | 1.35 |
| Experimental design and uncertainty | 1.05 |
| Results, Figures 2–3, and summary table | 2.35 |
| Discussion and limitations | 0.95 |
| Conclusion | 0.25 |

These allocations include figure space; do not add it again. If the body ends at eight pages, the final page must be at least 75% full. Reflow within nine pages without changing margins or fonts. Spend additional room on the split-independence argument, precise objectives, complete paired comparisons, uncertainty levels, and scope analysis—not filler, redundant plots, or chronological search details.

Follow the anonymous ICLR 2026 brief: omit names, affiliations, acknowledgements, funding, and identifying links. The supplied template has a populated author placeholder and final-copy setting; do not preserve them unchanged in an anonymized submission. Preserve required infrastructure watermark behavior. Include a separate `LLM Usage` section after the references.

## Method and Statistical Guardrails

- Define `z=log(y)B`, the maximum standardized ILR residual, independent split-calibration order `ceil((n_cal+1)(1-alpha))`, and the region membership rule. The evaluator uses an infinite threshold if the rank exceeds calibration size; the training pseudo-calibration selector has a distinct Gaussian fallback. State the usual exchangeability argument as background, not a new theorem or a conditional-on-X guarantee.
- Explain the actual scalar local correction, held-out selection, and fixed base fits. The unscaled ablation is not the unchanged-base-scale control, and no final local-correction-only or selector-only attribution is available.
- Measure `V` under Dirichlet(1,...,1), averaged over sampled contexts. It is normalized simplex volume, not ILR-box volume or an unnormalized Euclidean-volume measurement. Do not rank intrinsic efficiency by comparing raw K=3 and K=8 masses.
- Use eight seed blocks for variability over fitting and evaluation. Resample complete seed blocks jointly for any new aggregate contrast; do not pretend the repeated case/alpha cells are independent seeds. Saved Wilson intervals concern test uncertainty within a fitted episode and are not retraining or simultaneous subgroup intervals.
- Existing paired percentile intervals are descriptive with only eight seeds. The stored adjusted utility intervals use 54 comparisons and adjusted bootstrap tails; they are not an exact finite-sample familywise theorem. No corresponding adjusted mass interval is supplied.
- The reference-mass estimator uses 128 contexts and 1024 shared probes per case. Shared probes induce dependence across contexts. The stored mean per-context Monte Carlo diagnostic is not a complete standard error of the grand mean. Zero hits do not prove zero mass, and per-context probe resolution differs from averaged resolution.
- The shift recipe changes test X from uniform training support [-1.5,1.5] to a clipped normal on [-2.5,3], retaining the conditional generator. This includes support expansion as well as nonexchangeability. Undercoverage is measured; extrapolation, weighting, and model mechanisms are not separately identified. Do not promise that ordinary importance weighting would repair the result, and do not imply weighted conformal was evaluated.
- Keep limitations in the main paper: synthetic data only; fixed basis/region family; K=3 or 8 only; pooled calibration; no structural-zero evaluation; limited seeds/levels; Monte Carlo resolution; different selection/evaluation measures; missing final selector-only and original-initializer comparisons. Do not add CIFAR, label-set, latent-probability, Hellinger, Mondrian, or real-data claims.

## Supplementary Information

After references, use `clearpage`, appendix, and a **Supplementary Information** section. This adds substantive depth, not a dumping ground for adverse thesis-essential findings. Planned grounded subsections mirror the JSON:

1. **Training-only fitting and selection details.** Basis, ridge design/penalties, three-fold residual construction, standardized moments, smoothing bandwidths, shrinkage/clipping, swapped pseudo-calibration halves, finite ranks, log arithmetic mean ILR-box objective, and static fallbacks. Ground in `final.evidence.episodes`, `result.top_program_01`, and the selected source. Do not invent realized fallback frequencies.
2. **Synthetic data and reproduction specification.** Generator equations, positivity floor, substreams, K, split sizes 1024/512/2048, final seeds/alphas, manifests, hashes, probe design, and documented NumPy dependency. Use `task/evaluate_final.py`, `task/resources/final/manifest.json`, and `task/requirements.txt`; grounding anchors `final.evidence.episodes` and `final.qualification.status`. The writer must save actual analysis commands and figure-script mappings, not invent runtime, hardware, or environment versions.
3. **Complete paired comparison and uncertainty tables.** Every case/alpha/standard baseline, full utility and mass contrasts, descriptive and adjusted utility endpoints, and the deduplicated uncertainty record. Ground in `final.evidence.episodes`. Keep essential shifted failures and unfavorable comparisons in the main body as well.
4. **Feature-group reliability and information controls.** Evaluator x0-sign groups, sample counts, Wilson intervals, and feature-control contrasts. Any mean group coverage interval must be computed at seed level. Ground in `final.evidence.episodes` and the evaluator. These are descriptive audits, not Mondrian validity or training-time feature ablations.
5. **Reference-mass resolution and limiting controls.** Shared probes, zero-hit bounds, per-context granularity, Monte Carlo diagnostic limitations, whole-simplex/zero-radius endpoints. Ground in `final.evidence.episodes` and evaluator definitions.
6. **Evidence provenance and configuration scope.** Separate qualification from performance and search from final evidence; retain source/result hashes and describe archived joint-center/scale and Gaussian-selector configurations without an ordered success story. Ground in `final.qualification.*`, `final.evidence.episodes`, `result.top_program_02`, and `result.top_program_03`. Do not report unsupported original-incumbent or campaign-count comparisons.
7. **LLM Usage.** Disclose documented ideation, implementation assistance, reference-query planning, and framing roles from local/global memories and source artifacts. Add later writing/figure-generation roles only when performed. `final.evidence.episodes` anchors the study; process disclosure is independently supported by `memory.md`, `global_memory/memory.md`, and the selected configuration's memory. Do not invent model versions, human oversight, or independent checks, and keep the disclosure anonymous.

Later authoritative appendix-ranked analyses should join this supplement without retroactively inventing rankings in the strategy.

## Citation and Language Discipline

`references.bib` and `references_provenance.json` now exist, but many retrieved entries are off-topic or have ambiguous publication versions. Metadata retrieval does not mean a work was read. `Lei2016DistributionFreePI` and `Yang2021SelectionAA` are potentially relevant existing keys, not automatically approved scientific support. Before citation, verify the relevant source, publication identity/year, and the claimed statement. Do not pad related work with unrelated applications or invent missing references.

Do not identify, infer, search for, access, or follow citation networks to the prohibited study. No external literature browsing is part of this strategy stage. If later work accidentally encounters prohibited material, stop reading and record the location and amount seen.

Forbidden headings include **Search Progression**, **Campaign Phases**, **Milestones**, **First Valid Result**, **Winning Attempt**, **Experiment A / Experiment B**, **From Failure to Success**, **Leaderboard**, and **Generalization Guaranteed**.

Forbidden visible phrases include pipeline labels such as `correctness rate`, `correct and eligible`, `eligible`, `combined_score`, `rubric`, `worker_01`, and `worker_02`; chronology language such as “we finally found,” “first successful attempt,” and “each iteration improved”; and unsupported claims such as “state-of-the-art performance,” “uniformly smaller prediction regions,” “guaranteed conditional coverage,” “distribution-shift robustness is established,” “zero probe hits prove zero volume,” or “rank selection causes the improvement.” Internal source keys belong only in private grounding/audit context, not reader-facing result labels.

## Handoff and Checks

Implement the required figures before optional additions. Derive new summaries only from retained final records with saved analysis code; no new experiment is required for this strategy. This stage writes neither `paper.tex` nor `claims_grounding.json`, generates no figures, and does not run final-paper validation. Its checks are JSON syntax, required fields, source-ID existence, figure readability budgets, and agreement between this memo and the JSON.
