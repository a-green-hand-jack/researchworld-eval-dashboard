# Paper Framing Strategy

**Status:** ready for a grounded standalone-paper plan, not a claim of publication readiness.  
**Family:** `paper_standalone`, using `write-paper-standalone`.  
**Provisional title:** *Exact-Refit Stress Tests for Bradley–Terry Rankings*.  
**Venue:** anonymous ICLR 2026 submission; 8–9 body pages excluding references.

## Central Question and Thesis

**Question.** How much can small, matched-budget binary-outcome changes disrupt fitted Bradley–Terry orderings on the observed Arena and NBA panels, and how consistently do exact-refitted guided interventions exceed simple controls?

**Thesis.** On these fixed panels, influence-guided flip-path exchange produces larger budget-averaged pairwise-order disruption point estimates than three matched-budget baselines. Conditional bootstrap evidence supports a clearer advantage on Arena than across NBA seasons. This is an empirical sensitivity study, not a proof of an optimal attack, population generalization or a causal difference between evaluation designs.

This story uses one shared estimator/intervention with condition-specific evidence blocks: a crowdsourced Arena panel and season-specific sports panels. They are neither matched datasets nor a controlled experiment on evaluation design. NBA's home-effect adaptation belongs in the model description, not a separate method family.

## Evidence and Qualification Audit

Read `paper_data.json.final_evaluation` independently of other study metadata. Its reported status is completed, outcome qualified and correctness flag true, grounded respectively in `final.qualification.status`, `final.qualification.outcome` and `final.qualification.correct`. Do not turn these reported outcomes into publication approval, universal validity or comparative superiority. Candidate diagnostic trust is explicitly unverified; use recorded independent refit/audit evidence only within its documented scope.

There is no `downstream_study` or `study.*` source namespace. Do not fabricate a campaign classification, attempt accounting or search-score differences under that namespace. The available selected source and `results/best_program_manifest.json` corroborate the identity in `result.top_program_01`; the final record separately supplies a program-tree digest. No independent recomputation of that tree digest is claimed. Keep development provenance separate from final results, and omit an original-candidate performance comparison because no matched final evaluation of that comparator is supplied.

The completed final evaluation is usable even without downstream-study metadata. In another run, a completed but unqualified outcome would require explicit failed-qualification disclosure throughout drafting, review, audit and revision; neither retained metrics nor publication eligibility could erase it. Here the actual reported outcome is qualified. Never invent absent gate diagnostics or attribute an unknown failure to performance, validity or adaptivity.

### Decisive Grounded Results

- `final.evidence.episodes` contains three final seeds, 401, 503 and 607, each with Arena and NBA 2011–2015. These are algorithmic seeds, not independent datasets.
- Primary endpoint: participant-pair ordering reversals divided by the number of participant pairs, with the fixed participant-index tie rule. Reconstructing it from stored original and edited scores exactly reproduces every stored candidate endpoint. Larger values mean stronger disruption, not improved ranking accuracy.
- Nominal fractions are 0.1%, 0.5% and 1% of all usable rows, floored to integers. Ties remain in fitting and in the denominator but cannot be flipped. Arena costs are 43, 216 and 432 flips; NBA 2012 costs are 1, 5 and 10; other final NBA seasons use 1, 6 and 13. Report counts alongside nominal fractions.
- Final overall disruption values are 0.055641534391534395 for the proposed bundle, 0.00935242200328407 for uniform random, 0.011150133225384662 for degree-quartile matched, and 0.007573891625615763 for close-margin flips. Source each from the corresponding `final.metric.*` entry, not from search results.
- Explain the weighting: equal budgets and seeds within case, equal NBA seasons within the sports family, and equal weight for the two design families. Do not pool rows or overweight NBA because it has five panels.
- Arena's paired intervals have positive lower endpoints against all three baselines in all recorded seeds. Multiple NBA intervals include zero; NBA 2013–2015 do so for all three baselines across all seeds. This uncertainty is essential main-body evidence, not supplemental fine print.
- These intervals concern budget-averaged disruption under fixed intervention plans, not each individual budget point. They use 30 grouped bootstrap replicates per final case/seed. No reselection, seed pooling, design-family confidence interval, multiplicity adjustment or independent-population replication is established.
- Final graphs have 64 Arena participants and 30 in each NBA season. Graph coverage, finite-change influence discrepancies and fixed regularization constrain interpretation. Do not fit causal explanations to those descriptors.

## Explicit Framing Decision

There is no edit-mode context or prior manuscript: `previous_paper/`, `aggregated/` and `extra_tasks/` are absent. The JSON status `prior_paper_story_status: rejected` rejects the earlier prospective story, not an unseen manuscript.

| Candidate framing | Decision and grounded reason |
| --- | --- |
| Preserve exposure-matched MT-Bench block deletion with local updates | Reject: evaluated outcomes are binary flips on Arena/NBA, not question-block deletions or matched human/judge contrasts. |
| Broaden to a general deletion/flip robustness family | Reject as the thesis: the shared family would contain unmeasured interventions and unavailable matching. |
| Recenter on attainable finite-flip sensitivity with exact refits | Select: directly supported by final case/budget/baseline evidence and uncertainty, with two real evaluation designs. |
| Tell a search-winner or component-improvement story | Reject: search order is not the scientific question, and no controlled component-ablation bundle exists. |

Direct inspection of the selected `program.py` and `IMPLEMENTATION.md` supports sufficient-statistic aggregation, a width-two exact-refitted path generator, complete-path swaps/replacements and fallback. Do not import the different width-four branch as the selected mechanism. The intervention interface supplies no provenance-aware deletion or cross-design matching. No old title or figure plan is retained by inertia.

## Narrow Method Set

1. **Proposed:** influence-guided exact-refit flip-path exchange, treated as one evaluated bundle. Explain its original-Hessian screening, nested paths, exact-refitted comparisons, affected-prefix caching and complete incumbent fallback. Do not attribute the aggregate advantage specifically to exchange without an ablation.
2. **Baseline:** uniform random binary-outcome flips, using the recorded stream averages.
3. **Baseline:** degree-sum-quartile-matched random flips, conditional on the actual selected prefixes. This is approximate exposure control, not exact endpoint/content matching.
4. **Baseline:** smallest absolute fitted matchup-margin flips.
5. **Supporting diagnostics only:** independent refits and no-op, rotated-priority, reset and explicitly synthetic constant-zero checks. These are not additional competitive algorithms or architectural ablations.

Define the fixed model: summed logistic losses plus one-half the squared parameter norm, centered participant scores and an optional regularized NBA home coefficient. Preserve ridge 1 and the fixed tie rule. Distinguish the method's displacement-first lexicographic internal objective from the inversion-fraction endpoint. A mathematically correct local derivative does not imply accurate finite-change ranking predictions; exact refits determine measured endpoints.

## Required Figures and Readability Budgets

The inspected ICLR template uses `article`; `paper.sty` sets a **single 5.5-inch text column and 9-inch text height**. Thus ordinary column width equals full text width. There is no two-column `figure*` geometry to borrow, and half-width figures would unnecessarily constrain labels. All required figures use the full 5.5-inch text width. Heights below exclude captions.

### 1. `sensitivity_overview`: Early Conceptual Overview

- **Generator:** `generate-concept-figure`, exactly once in the plan; rendering belongs to the orchestrator, not this strategy stage.
- **Placement:** page 1 or 2; full text width; approximately 1.6–1.9 inches high; final labels at least 9 pt.
- **Content:** two sparse side-by-side panels. The first defines fixed observed comparisons, uneditable ties and legal nested flips. The second relates influence screening, complete-path selection/exchange, independent exact refits, three matched-budget baselines and fixed-plan grouped uncertainty. Arena and NBA are unequal evidence blocks, not causally linked designs.
- **Budget:** at most two panels, two per row, six conceptual categories and four semantic series per panel. No invented empirical graph or rank-change example, decorative architecture or measured values.
- **Grounding:** `final.evidence.episodes`, with mechanism labels corroborated by the selected implementation and public task contract.

### 2. `final_disruption_comparison`: All Cases and Budgets

- **Generator:** matplotlib; grouped dots, not connected trajectories.
- **Placement:** full text width; three vertically stacked panels; approximately 3.7–4.2 inches high, 8–9 pt labels.
- **Content:** one panel per nominal fraction; six case categories; four method series. Use a common metric scale and one shared legend. Mark descriptive means of the three recorded seeds; put individual values in the supplement and actual integer costs in a main-text table.
- **Budget:** at most three panels, one per row, six categories and four series per panel. No invented error bars or interpretation of seeds as datasets; the next figure supplies paired uncertainty.
- **Grounding:** stored `candidate_curves`, `baseline_curves` and `counts` under `final.evidence.episodes`. Seed means are transparent arithmetic summaries of recorded values, not new observations.

### 3. `paired_effect_uncertainty`: Conditional Effects and Null-Compatible Cases

- **Generator:** matplotlib; forest plot with a clear zero reference.
- **Placement:** full text width; three vertical baseline panels; approximately 4.6–5.2 inches high, 8–9 pt labels. Do not squeeze three forest panels horizontally or shrink this to half width.
- **Content:** six cases per panel; three modestly offset seed-specific intervals per case. Use recorded budget-averaged `paired_intervals` exactly. Keep Arena's clearer advantage beside NBA's inconclusive comparisons.
- **Budget:** at most three panels, one per row, six categories and three seed series per panel.
- **Statistical labeling:** show interval segments without fabricated centers. If a point marker is necessary, compute and label the mean of the corresponding recorded bootstrap paired effects, rather than silently inserting the original-sample effect or interval midpoint. Do not pool seeds or claim simultaneous coverage.
- **Grounding:** `final.evidence.episodes`. Budget-specific point comparisons and budget-averaged intervals are distinct estimands and must be labeled accordingly.

### Export Contract

Save plotting scripts and input mappings. Export quantitative figures as vector PDF and PNG at 300 DPI; include the PDF in LaTeX whenever available. Keep method colors and markers consistent and colorblind-safe. For the concept figure, preserve editable source and use a vector PDF if available; otherwise regenerate the full-width raster at at least 2400 pixels wide. Other column-only rasters require at least 1200 pixels. Never upscale an existing raster. The writer wires concept-figure manifest/prompt-log entries according to the skill; it does not run the orchestrator-owned pipeline.

## Body Layout and Page Use

Target approximately **8.5 body pages**, including captions and figures, within the explicit 8–9-page venue budget. An exactly eight-page body must leave its last page at least 75% full. Use scientific depth, not padding:

| Scientific section | Approximate page allocation | Value supplied |
| --- | ---: | --- |
| Abstract and introduction | 1.2 | Problem, scoped contributions and early overview |
| Related work | 0.6 | Relevant actually read methods and positioning, not retrieval filler |
| Ranking sensitivity and perturbation model | 1.0 | Estimand, fixed objective, ties, costs and order conventions |
| Influence-guided exact-refit stress testing | 1.4 | Bundle, derivative/refit distinction, nested path construction and limits |
| Evaluation design | 1.1 | Panel provenance, graph/count table, baselines, weighting and bootstrap |
| Results and conditional uncertainty | 2.1 | All-case comparison, final aggregate table, paired intervals and inconclusive cases |
| Discussion and limitations | 0.9 | Scope, approximation, adaptive selection, unequal graphs and no causal claims |
| Conclusion | 0.2 | Narrow answer to the research question |

These are layout targets rather than empirical values. Rebalance within the cap; do not invent theory, sweeps, baselines or chronology to reach it. The substantive model/protocol explanation and uncertainty analysis justify the space even without component ablations.

The supplied template scaffold includes final-copy mode and an author identity. The writer must remove both for anonymous review, omit affiliations/acknowledgements/funding, avoid identifying links and preserve the orchestrator-owned watermark block unchanged. The current ICLR brief governs venue choice despite older task-contract venue language. Inspect and document official template provenance later rather than claiming the supplied style proves latest-edition compliance now.

## Supplementary Information After References

Purpose: provide complete existing evidence and reproducibility depth without hiding evidence essential to the thesis. Use `clearpage`, bibliography, `clearpage`, appendix and a substantive `Supplementary Information` section in the final paper. Route later authoritative appendix-ranked analyses here without retroactively revising this strategy.

1. **Complete Case, Budget and Seed Results.** All candidate/baseline endpoints, integer counts, intervals and graph descriptors, including null-compatible cases. Use recorded rank intervals where useful without manufacturing absent budget-specific uncertainty. Source: `final.evidence.episodes`.
2. **Influence Arithmetic and Finite-Change Diagnostics.** Distinguish unit derivatives, signed flip shifts and nonlinear discrepancies; tabulate recorded errors, method audits and control outcomes. The recorded overall discrepancy is 0.14315313656317594, not an invalidity rate. Sources: `final.evidence.episodes`, `final.metric.influence_error`, `final.metric.control_error`; corroborate method equations with code and the public contract.
3. **Nested Flip-Path Construction and Reproducibility.** Document the available selected code's width-two generator, swaps/replacements, cache and fallback. Source-declared optional limits are 128 proposals, 72 added converged fits at dimension at most 64 and 24 otherwise, plus a two-second soft deadline; these are not measured usage or a hard interruption bound. Include recorded seeds/durations/digest and existing dependency/acquisition files, never invented per-method runtimes or claims of a fresh reproduction. Sources: `final.evidence.episodes`, `final.qualification.status`, corroborated by the explicitly named implementation.
4. **Data Provenance and Scope of Comparability.** Explain normalized Arena document groups, unique NBA games, reciprocal-row handling, partition policy, ties, home effects, season-specific fitting and unequal coverage. Use `task/resources/final/manifest.json` and `task/prepare_data.py` as available documentation, distinguishing manifest assertions from independently rerun checks. Anchor empirical graph/count evidence to `final.evidence.episodes`; do not invent missing licenses/checksums or add MT-Bench results.
5. **Evaluation Outcome and Claim Boundaries.** Separate reported completed/qualified status, numerical audits, unverified candidate diagnostics and publication judgment. Preserve all limitations and unknown diagnostics in review/audit/revision. Sources: `final.qualification.status`, `final.qualification.outcome`, `final.qualification.correct`, `final.evidence.episodes`.
6. **LLM Usage.** A separate disclosure section describing documented ideation, code preparation, reference planning, framing and writing assistance. Distinguish static preparation from recorded evaluator execution; omit unsupported literature-reading or empirical-judging claims. Use available assistant logs, `result.top_program_01` and `final.evidence.episodes` for traceability; redact identifying paths.

Source IDs above are existing registered anchors; file paths supply additional documentary support rather than pretending that metric entries independently prove source-code internals or provenance checks.

## Claims, References and Wording Guardrails

Do not infer historical misconduct, attacker access, global optimality, a minimum required corruption budget, population preference change, unseen-model performance or temporal generalization. An attainable disruption is a sensitivity witness, not a robustness certificate. Approximate exposure control does not make the two data designs comparable in a causal sense. No final component ablations, ridge sweeps, deletions or matched human/judge analyses exist.

The existing bibliography is a retrieval output, not an already verified reading list: provenance is metadata-only and many entries are irrelevant. Related work must use admissible relevant originals actually read, with synchronized BibTeX/provenance keys. Do not cite irrelevant records to fill space, claim comprehensive novelty, perform citation expansion, infer the prohibited study's identity or access uncertain related pages. If forbidden material is encountered accidentally, stop and record location and amount read. No such encounter is claimed in this framing stage.

**Forbidden headings:** Search Progression; Campaign Timeline; Milestones; First Valid Result; Experiment A / Experiment B; Phase 1 / Phase 2; Round-by-Round Improvements; From Failure to Winner; Architecture Ablations; Matched MT-Bench Deletion Results.

**Forbidden visible phrases:** first valid result; we then tried; subsequent improvements; next-best; later variants; winning iteration; correctness rate; correct and eligible; eligible; worker_01; worker_02; combined_score; rubric; state-of-the-art leaderboard attack; certified minimum manipulation budget; exactly exposure-matched; all NBA comparisons are significant; sports evaluation is causally more robust; the exchange component explains the gain. Internal identifiers in this strategy are private provenance only, not recommendations for reader-facing labels.

## Handoff and Stage Limits

Implement the required figures first, preserve their readability budgets, and keep both the strong and inconclusive evidence visible. Quantitative final claims use `final.metric.*` or `final.evidence.episodes`; qualification facts use `final.qualification.*`. Search provenance is not final replication and unscored work is not a measured loss.

This stage produces only the strategy memo and JSON plus append-only memory updates. It does not draft `paper.tex`, create `claims_grounding.json`, run candidate/evaluator experiments, generate figures or perform final-paper validation. Check strategy JSON structure, source-ID resolution, figure budgets and memo consistency only. No necessary empirical result is deferred to a hypothetical later experiment.
