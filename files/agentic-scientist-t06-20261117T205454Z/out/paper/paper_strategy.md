# Paper strategy

**Status:** ready. **Prompt family:** `paper_standalone`. **Writing skill:** `write-paper-standalone`.

**Provisional title:** Exact-Refit Audits of Pairwise Ranking Sensitivity

## Central question

How do small, influence-ordered deletions affect regularized Bradley–Terry rankings, and how does their disruption compare with random and high-loss deletion across crowd preferences and historical sports outcomes?

## Central thesis

A frozen-prefix audit with bounded exact-refit contender selection yields greater aggregate rank disruption than the measured deletion baselines on the final partitions, but its advantage depends on dataset and deletion budget, with fixed-mask group resampling favoring high-loss deletion in Arena and the studied selector in NBA.

## Why this story

The strongest evidence is the direct final comparison on two real-data settings and its conditional uncertainty analysis, not an optimization success story. Use one common sensitivity question with condition-specific evidence blocks, not a causal test of evaluation design. The inspected implementation supports the mechanism description; evaluator refits support measured effectiveness. Search configurations are descriptive supporting material, not independently replicated final ablations. The paper is viable as a bounded empirical audit without universal superiority or novelty-priority claims.

## Framing decision

This is fresh framing, not an edit pass: no resolved edit-context files, previous_paper, aggregated, extra_tasks, or prior manuscript are staged. The status means recentering the source-task brief, not editing an unseen paper. Compare three alternatives: preserving the proposed dependence-aware, multi-judge frontier story is unsupported; broadening to a universal cross-design robustness method overstates unmatched evidence; centering the shared frozen-prefix row-deletion audit and heterogeneous measured limits is supported. Method detail and figure density are not reasons to preserve an unsupported story.

Prior-story status: **recentered** (source-brief recentering; no prior manuscript was staged).

## Grounded input impact

- Read final_evaluation independently: final.qualification.status=completed, final.qualification.outcome=qualified, final.qualification.correct=true. There is no downstream_study or study.* grounding. Qualification is not statistical superiority or generalization; missing additional gate diagnostics remain unknown.

- results/best_program_manifest.json identifies the six-contender exact-refit configuration. Its inspected source supports the named method family; final provenance records a program-tree digest, but an independent reconstruction of that digest is not claimed.

- Final episodes cover Arena and NBA, not the proposed MT-Bench expert/GPT-4 comparisons. Provenance groups support partitioning and conditional resampling, not whole-group deletion or design labels available to the selector.

- Final dataset/budget contrasts and unique fixed-mask bootstrap records shift the thesis away from a general improvement claim. Reversed-row cases are controls, not extra datasets; repeated bootstrap exports are not new resamples.

- Clean-Hessian selection and retained-curvature expansion have descriptive search evidence only. No valid grounded metric for the original starter comparator supports retaining its quantitative comparison.

- References and provenance include irrelevant retrieval matches and do not resolve all exact planned identities. The bibliography is not evidence of a completed literature review or established novelty.

## Results focus

- Lead with final dataset-by-budget normalized inversion fractions for the studied selector, high-loss deletion, and random deletion. Use unpermuted cases for performance summaries and reversed-row cases only for invariance checks.

- Secondary final aggregate table: studied selector 0.011722185737596697, high-loss deletion 0.009340217174121283, random deletion 0.003902759168170127; paired gains over high-loss and random deletion 0.002381968563475412 and 0.00781942656942657. Sources: final.metric.combined_score, final.metric.disagreement_baseline_score, final.metric.random_baseline_score, final.metric.paired_gain_vs_disagreement, final.metric.paired_gain_vs_random.

- Display every unique stored conditional group-bootstrap gain. Each dataset has 32 records, repeated identically across five episode exports, not 160 independent records. All stored high-loss-relative gains are negative in Arena and positive in NBA; Arena random-relative gains include negative observations. Source: final.evidence.episodes.

- Separate seed-resampling intervals from group-weight resampling. The high-loss-relative seed interval has equal endpoints because that contrast is deterministic across recorded seeds; it is not certainty about data variation or general superiority.

- Use normalized original-leader rank drop 0.03305066318764949 only as a secondary aggregate for the studied selector, grounded in final.metric.mean_leader_rank_drop. Per-budget curves are normalized inversions, not leader drops or minimal reversal budgets.

- A small descriptive search table may show raw scores only: clean-Hessian-only selection 0.013240276724865765 (result.top_program_03), bounded exact refits 0.01595532053579999 (result.top_program_01), retained-curvature expansion 0.01595532053579999 (result.top_program_02). Keep this separate from final results; no campaign winner, derived search-delta, or scored/unscored count claims without study.* grounding.

## Method groups

- **Frozen-prefix bounded exact-refit selector** (proposed): The studied six-contender configuration computes clean influence orders, selects using retained-data refits, and returns frozen nested prefixes for independent evaluation.

- **Uniform random row deletion** (baseline): Measured at identical floored row budgets; five seeds reflect deletion randomness, not independent dataset draws.

- **High-loss row deletion** (baseline): Strong measured comparator ordered by clean per-row Bradley–Terry negative log-likelihood; it is not disagreement between judges. Its Arena advantage is essential.

- **Unmodified-data and reversed-row controls** (supporting): Numerical zero-change and row-order invariance checks, not reader-facing performance rates or additional replications.

- **Clean-Hessian-only contender selection** (ablation): Descriptive search-configuration comparison for lookahead, explicitly not a replicated final ablation or causal mechanism attribution.

- **Retained-curvature shortlist expansion** (ablation): Supporting negative configuration comparison: expanded proxy/exact pools tie the recorded search aggregate. Do not infer identical behavior, equivalence, or efficiency.

## Figure plan and final-size geometry

Inspected `paper.sty`, the ICLR skill template, and `VENUE.md`: a single 5.5-inch-wide text column and 9-inch text height. Column width equals full text width; do not apply a two-column assumption. Figures are ordinary text-width figures.

### audit_overview — required

Give immediate glance value for the common sensitivity object, method, and conditioning boundary.

- Generator/type: `generate-concept-figure` / `diagram`.

- Encoding: group by audit_component; split by two dataset badges feeding one common audit; metric: none; conceptual mechanism only.

- Content: Six blocks: observed comparisons (Arena crowd preferences / NBA outcomes); regularized Bradley–Terry fit; frozen influence prefixes; bounded exact-refit contender selection; deletion and independent refits; dataset/budget contrasts. Attach a short fixed-mask resampling/no-reselection note to the last block. Do not depict grouped deletion, architecture changes, adaptive row reordering, or causal design effects.

- Readability budget: 1 panels; at most 1 panels per row; 6 categories and 3 series per panel; labels at least 9 pt. No progression view.

- Placement: Page 1 or 2, before the detailed method, using an ordinary single-column figure. Width: 0.98 of text width (full_width).

- Footprint: About 0.65 page including caption; artwork about 2.6 inches tall.

- Layout justification: Inspected paper.sty specifies one 5.5-inch text column and 9-inch text height. At 0.98 text width, about 5.39 inches, a two-row/three-block arrangement avoids tiny text. Half-width placement would obscure frozen-prefix versus refit distinctions.

- Grounding IDs: `final.evidence.episodes`. Supporting protocol/implementation: `results/ideas/02_exact_refit_contender_screening/program_1/src/program.py`, `task/evaluate_final.py`.

### dataset_budget_comparison — required

Expose dataset and budget contrasts hidden by aggregation.

- Generator/type: `matplotlib` / `scatter`, with grouped-dot layout.

- Encoding: group by deletion_rule; split by dataset; metric: normalized pairwise inversion fraction relative to clean fitted ranking.

- Content: Three nominal removed-row fractions: 0.1%, 0.5%, 1%, with floored counts stated in the caption. Plot deterministic studied/high-loss markers without manufactured uncertainty bars; show five random-deletion seed values as faint same-color points and their mean. Do not count reversed-row controls as replicates. Shared y scale; larger means greater disruption, not better ranking accuracy. Budget is an experimental condition, not search progression.

- Readability budget: 2 panels; at most 2 panels per row; 3 categories and 3 series per panel; labels at least 9 pt. No progression view.

- Placement: Main results, approximately page 5 or 6. Width: 1.0 of text width (full_width).

- Footprint: About 0.70 page including caption; artwork about 3.0 inches tall.

- Layout justification: Use all 5.5 inches for two side-by-side panels, each with three budgets and three methods, common axes and one shared legend. Do not compress the entire figure to half-text width or rescue long labels by shrinking them.

- Grounding IDs: `final.evidence.episodes`. Supporting protocol/implementation: `task/evaluate_final.py:FRACTIONS`, `task/evaluate_final.py:disruption`.

### conditional_resampling_contrasts — required

Keep dependence-sensitive conditional uncertainty and dataset-specific comparator ordering visible in the main paper.

- Generator/type: `matplotlib` / `scatter`, with strip-plot layout.

- Encoding: group by dataset; split by high-loss deletion and random deletion comparators; metric: fixed-mask bootstrap difference in mean normalized inversions: studied selector minus comparator.

- Content: Extract one unique conditional_group_bootstrap block and plot its 32 stored gains per dataset per comparator against zero. Label fixed-mask group-weight resampling. Do not pool duplicated exports, call this full-procedure uncertainty, claim population significance, or infer causal evaluation-design effects.

- Readability budget: 2 panels; at most 2 panels per row; 2 categories and 1 series per panel; labels at least 9 pt. No progression view.

- Placement: Immediately after Figure 2, approximately page 6 or 7; never supplementary-only. Width: 1.0 of text width (full_width).

- Footprint: About 0.65 page including caption; artwork about 2.7 inches tall.

- Layout justification: Two panels across the full 5.5-inch text block leave room for 32 observations per dataset, explicit comparator titles, zero reference, and labels at least 9 pt. Use reproducible display jitter, not more statistical samples.

- Grounding IDs: `final.evidence.episodes`. Supporting protocol/implementation: `task/evaluate_final.py:final_uncertainty`.

## Supplementary plan
Provide implementation, provenance, numerical-control, and uncertainty depth needed to reproduce and audit the narrow claim, without moving the decisive contrasts or limitations out of the main paper.

### Retained-mean objective and frozen-prefix selection
Expand centered ridge Bradley–Terry, half-win ties, clean contrast/influence solves, retained-mean displacement correction, deterministic tie rules, six-contender selection, pair-statistic compression, warm starts/cache, convergence tolerances, incomplete-refit fallback, and selector/evaluation metric mismatch. Inspected program.py, IMPLEMENTATION.md, and evaluator explain the mechanism, not unreported internal shortlist decisions.

Grounding IDs: `final.evidence.episodes`.

### Data partitioning and reproducibility record
Record pinned Arena/NBA sources, content-group split, largest connected components, NBA copy filtering and historical team-code limitations, source/payload hashes, declared seeds, CPU dependencies and staged-resource commands from inspected manifests/code. Distinguish protocol metadata from measured findings. A complete raw-to-partition builder and all original raw archives are not staged; do not claim otherwise.

Grounding IDs: `final.evidence.episodes`, `final.qualification.status`.

### Numerical and row-order checks
Explain residual tolerances, no-deletion zero disruption, invalid constant-certificate rejection, reversed-row invariance, and unverified candidate-authored diagnostics. Preserve the exact final qualification outcome without inferring undocumented gate causes or generalization.

Grounding IDs: `final.evidence.episodes`, `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`.

### Descriptive search configurations
Archive raw scores and inspected implementations for clean-Hessian selection, bounded exact refits and retained-curvature expansion. State missing final controlled ablations and selection-adjusted uncertainty. A tied aggregate is not identical behavior or an overhead measurement. Do not report campaign counts, unscored losses, derived search deltas, or original-starter performance without study.* sources.

Grounding IDs: `result.top_program_01`, `result.top_program_02`, `result.top_program_03`.

### Conditional uncertainty protocol and stored records
Give the complete unique group-weight records and bootstrap algorithm; masks are fixed, weighted removed mass varies, and selection is not rerun. Contrast this with aggregate seed-resampling intervals and their deterministic degeneracy. The main text retains opposite high-loss-relative signs and the conditioning limitations.

Grounding IDs: `final.evidence.episodes`, `final.metric.paired_gain_disagreement_ci_low`, `final.metric.paired_gain_disagreement_ci_high`, `final.metric.paired_gain_random_ci_low`, `final.metric.paired_gain_random_ci_high`.

## Required process disclosure
The five source-backed supplementary entries above describe scientific evidence. Separately, include the venue-mandated **LLM Usage** subsection in Supplementary Information as process disclosure, not as an additional result-grounded entry.

Disclose the roles documented in supplied agent-run logs and artifacts: research ideation, candidate-code generation, reference-query planning, and manuscript assistance. Distinguish these from the numerical evaluator. Do not invent provider/model identities, human oversight or paid-API experiments; this is process provenance, not a numerical result.

Documented agent-run artifacts support this disclosure; no numerical grounding ID is assigned to agent-process roles.

## Writer contract: body budget, output, and limitations

1. Scope: this strategy writes neither paper.tex nor claims_grounding.json, drafts no final paper, renders no figures, runs no new experiment, and invokes no final-paper validation. Dotted JSON fields, internal selection terms and hashes in this memo are private-only source maps, not visible manuscript labels. Memory is qualitative planning context only.

2. Venue/layout: use VENUE.md and the supplied ICLR 2026 style. The inspected paper.sty has textwidth=5.5 inches and textheight=9 inches, single-column: column width equals full text width. All three figures use this text block, not a two-column figure* layout. Keep margins and typography unchanged.

3. Body budget, approximately 8.5 pages including figures/tables but excluding references: title/abstract 0.5; introduction 1.0; related work 0.6; method 1.6; data/metrics/uncertainty protocol 1.1; results 2.6; discussion/limitations 0.8; conclusion 0.3. These are planned page equivalents, not measured pagination. Venue requires 8–9 body pages; an eight-page body must end at least 75% full. Spend space on scientific explanation, not padding or unsupported experiments.

4. Thesis-first headings: Introduction; Related Work; Frozen-Prefix Ranking Audits; Data, Metrics, and Uncertainty; Dataset- and Budget-Dependent Disruption; Discussion and Limitations; Conclusion. Use three figures plus two compact tables: final aggregate metrics with seed-interval interpretation, and descriptive search configurations. Keep search context brief and distinct from final evidence.

5. Protocol from inspected code: mean negative log-likelihood plus lambda=0.001 ridge, centered scores, ties as half wins, nominal deletion fractions 0.1%, 0.5%, 1%, floored row counts. For removed prefix S of size k among n rows, the screening displacement is H_clean inverse applied to (sum of removed row gradients + k*lambda*theta_clean), divided by n-k. Distinguish that approximation from converged retained-data fits; exact means residual-controlled numerical refitting, not symbolic exactness.

6. Definitions: normalized inversion fraction divides discordant participant pairs by all participant pairs. Normalized original-leader rank drop divides its downward position change by participant count minus one. Per-budget curves are inversions, not leader drops. The selector uses leader-drop objectives, which need not optimize the reported inversion statistic. Larger disruption does not imply ranking inaccuracy or better models.

7. Comparison scope: row fraction normalizes intervention size, not effective sample size, participant exposure, graph geometry, leverage or uncertainty. Two unmatched designs do not identify a causal design effect. NBA historical team codes/eras are heterogeneous. Fit-specific ranking sensitivity is not evidence about present-day platform rankings or participant ability across eras.

8. Uncertainty: the aggregate high-loss-relative seed interval is [0.002381968563475412, 0.002381968563475412]; the random-relative interval is [0.007377907506332164, 0.008168732424939618]. Source each endpoint with its final.metric.paired_gain_*_ci_* ID. Explain seed-resampling construction in the main table caption. Repeated deterministic contrasts do not estimate data uncertainty.

9. Conditional group resampling holds original masks fixed, refits weighted data, and does not rerun contender selection or either baseline order. Removed weighted mass is not fixed by nominal row fraction. There are 32 unique stored records per dataset, repeated across exported episodes; never pool these into 160 independent records. No full-procedure confidence or population-wide significance claim.

10. No matched-support experiment, whole-group deletion frontier, expert/judge comparison, adaptive order refinement, ridge-sensitivity study, runtime ablation or global minimum-deletion certificate was measured. Provenance groups support split/resampling only; the selector receives anonymous rows. Do not turn implementation intent into empirical findings.

11. Qualification: current authoritative final sources report completed and qualified. This does not establish generalization or universal superiority. If later authoritative evidence reports failed qualification, disclose and preserve it through writing, review, audit and revision; distinguish statistical/performance causes from validity/adaptivity causes only when identified by evaluator diagnostics. Missing causes stay unknown.

12. Source map: final.evidence.episodes supports per-case data and conditional resampling; final.metric.* supports aggregate metrics; final.qualification.* alone grounds qualification. No downstream_study or study.* sources exist, so omit campaign selection advantages, derived search-score differences, attempt counts and original-starter quantitative comparison. Use result.top_program_* only for clearly labeled descriptive raw search scores. Unscored performance is missing, not a loss.

13. Positioning: claim an auditable fitted-ranking protocol, measured two-setting budget contrasts and conditional uncertainty with limitations. Do not claim new Bradley–Terry estimation, novelty priority, universally effective attacks, or causal effects of evaluation design. The two exact-refit configurations share a search aggregate, not proven equivalence; no comparative CPU-cost claim is available.

14. References: staged retrieval has irrelevant matches, duplicate Bradley–Terry records, and lacks several exact planned influence-function, finite-sample robustness, Arena, vote-rigging and NBA provenance identities. Later verify exact allowed identities and actually consult their content; use synchronized BibTeX/provenance keys only. Existing matches are not citation permission. No broad leaderboard searches, citation traversal, guessing of the prohibited work, or citations to unconsulted material. This strategy makes no network requests.

15. Figure outputs: quantitative plots require reproducible source, vector PDF and PNG at 300 DPI or higher. LaTeX must reference PDF whenever it exists. Prefer editable draw.io plus PDF/PNG for the concept overview; if raster-only, require at least 2400 px width for these full-width figures, or 1200 px for any later justified column-scale raster. Regenerate rather than upscale. Follow concept-figure orchestration later; do not render during strategy generation.

16. Readability: labels should render at 9–10 pt or larger. Method colors stay consistent within the comparison; dataset colors in the uncertainty figure have an explicitly different labeled role. A zero reference is not another method. No thresholded success-rate plot is warranted. Simplify or regenerate dense figures rather than shrinking.

17. Supplement: substantive material already exists. After references use a clear page, appendix mode, and Supplementary Information in the same paper source; include a separate LLM Usage subsection. Authoritative posthoc rankings arrive separately; route appendix-ranked analyses there without guessing rankings now or moving central evidence out of the main text.

18. Anonymity: omit names, affiliations, acknowledgements, funding, self-identifying links and internal URLs. Remove template final-copy/author scaffolding during drafting while preserving its required watermark. Include the separate LLM Usage disclosure; do not invent a mandatory checklist not supplied for this venue.

19. Reproducibility: inspected sources include the candidate, evaluator, normalized resources/manifests and numpy==2.2.6, scipy==1.15.3 requirements. A complete raw-to-partition builder and all raw originals are not staged. Inventory actual available artifacts/commands and distinguish staged-resource reruns from raw-source reconstruction. Do not claim the broader reproduction package is already complete.

## Forbidden headings
**Search Progression**, **Campaign Phases**, **Milestones**, **First Valid Result**, **Timeline of Improvements**, **Experiment A**, **Experiment B**, **From Failure to Success**, **Winning Configuration**.

## Forbidden phrases
**we then tried**, **first valid result**, **subsequent improvements**, **next-best**, **later variants**, **search winner**, **universally superior**, **universally more robust**, **state of the art**, **globally minimal deletion budget**, **causal effect of evaluation design**, **full-procedure bootstrap**, **five independent datasets**, **160 independent bootstrap replicates**, **correctness rate**, **correct and eligible**, **eligible**, **combined_score**, **rubric**, **worker_01**, **worker_02**.

These lists prohibit chronology framing, unsupported claims, and pipeline-native visible labels; source identifiers elsewhere in this strategy are private-only grounding, not exceptions.
