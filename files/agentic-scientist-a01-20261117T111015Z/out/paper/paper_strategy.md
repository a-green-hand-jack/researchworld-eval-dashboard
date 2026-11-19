# Paper strategy: response ceilings and targeted investment

**Status:** ready. **Prompt family:** `paper_standalone` / `write-paper-standalone`.
**Provisional title:** Response Ceilings and Targeted Investment in Multitask Leaderboards.

## Scientific center

**Question.** Under a bounded, target-only score-response model with fixed rivals, how many task coordinates must be improved to attain strict first place, and how does that investment depend on the aggregation rule and response ceiling?

**Thesis.** In the evaluated public score panels, aggregation robustness is conditional on the response ceiling: exact six-task results reverse the mean–median minimum-support ordering between half and full headroom on matched attainable targets, while larger subject-level panels establish feasible investment bounds rather than exact rule rankings.

This is a standalone conditional empirical study, not an optimizer breakthrough, a training experiment, or a search report. Organize the six-task and subject-level panels as complementary evidence blocks under one question. Their certificate strength differs; neither is evidence of architecture change or domain transfer. The contribution is the precisely defined investment comparison and its measured limits, not a claim that familiar enumeration or greedy selection is new.

## Framing decision and rejected alternatives

No edit-context file, previous manuscript, `previous_paper/`, `aggregated/`, or `extra_tasks/` is staged. The JSON status `prior_paper_story_status: rejected` rejects an assumed inherited improvement narrative; there is no actual prior manuscript to reject.

| Candidate framing | Decision and grounded reason |
| --- | --- |
| Preserve an optimizer-improvement story | Reject: the frozen selection is the reference baseline, not a successful new optimizer. |
| Broaden to a shared novel certificate family | Reject: no component ablations substantiate the abandoned proposal mechanisms, and large-panel median/trimmed costs are not exact. |
| Recenter on response-dependent investment | Choose: final ordinary decision records support direct rule-by-ceiling comparisons, including exact paired contrasts and explicit unattainability. |

Direct inspection confirms that the staged selected and baseline source files are identical. Their small-panel enumeration, exact mean sorting, and larger-panel greedy witnesses determine what can be claimed. The auxiliary projections and BBH records provide additional scope checks, not a reason to broaden the thesis to a new method family. The venue changes presentation, not the scientific conclusion.

## Private grounding and qualification audit

This section is a provenance memo, not manuscript prose. Use these registered source identifiers in downstream claim mapping:

- `final.qualification.status = completed`, `final.qualification.outcome = qualified`, and `final.qualification.correct = true`. These come from `paper_data.json.final_evaluation`, read independently of selection metadata. Qualification does not establish novelty, population generalization, or every support minimum.
- `study.selection_kind = baseline`; `study.investigation_outcome = completed_no_winner`; `study.search_score_delta = 0`; `study.attempts.scored = 3`; `study.attempts.unscored = 0`. Search evidence and final measurements have distinct scopes. No search alternative has an established qualifying improvement. Missing performance evidence would not be a measured loss.
- `final.evidence.episodes` contains three sampling seeds, ordinary and matched-control cases, primary and auxiliary decisions, and policy-comparison intervals. Its `candidate_diagnostics_trust` remains `unverified`. The evidence-file SHA-256 agrees with the manifest. Direct evaluator inspection shows witness verification and exhaustive small-panel reference computation; that does not license unrelated candidate diagnostics. The field `exact_audit_pass` alone is not proof of full-panel exactness.
- Preserve the final qualification assessment through writing, review, audit, and revision. If authoritative later evidence changes it to a failure, disclose that failure explicitly and retain its limitations. Failed search alternatives have no established causal diagnosis: do not infer performance-only, validity, or adaptivity failure from a boolean outcome.

The cross-rule cohort check was a read-only summary of existing records, not a new experiment. Restrict to ordinary primary Open LLM decisions and join on seed and target slot. Intersect targets attainable under both mean and median at both half and full headroom. The resulting fixed cohorts contain 18, 17, and 17 targets for seeds 1009, 1013, and 1019. The following rounded values are audit checks derived from `final.evidence.episodes`, not hard-coded plotting inputs:

| Sampling seed | Median minus mean support fraction, half headroom | Same contrast, full headroom |
| --- | ---: | ---: |
| 1009 | -0.129630 | +0.138889 |
| 1013 | -0.127451 | +0.127451 |
| 1019 | -0.068627 | +0.156863 |

All feasible primary six-task costs in this contrast have exact support status and correspond to the frozen exhaustive procedure. The reversal is a descriptive within-snapshot result selected during framing, not a preregistered significance finding. Larger-panel HELM witness-cost reversals are not minimum-cost reversals when certification intervals overlap.

## Scope and method groups

Define scores in `[0,1]`, a target model, a fixed rival pool, a task panel of size `m`, and selected support `S`. Only selected coordinates change, by `x_j -> x_j + alpha(1-x_j)`, with recorded `alpha` values `0.25`, `0.5`, and `1.0`. Unique first means target aggregate exceeds the largest rival aggregate by more than `1e-10`. Investment is `|S|`, with `|S|/m` used for normalized display. Total normalized score lift is secondary, not dollars, training examples, or compute.

Include only these method groups:

1. **Frozen support-minimization procedure — supporting.** Exhaust at most six coordinates, sort headroom for larger means, and construct marginal-score-greedy supports for larger median/trimmed panels. Explain the all-coordinate infeasibility test and exact versus lower–upper outcomes.
2. **Equal-task arithmetic mean — aggregation baseline.** Retain throughout; the headroom solution is exact.
3. **Conventional median — supporting condition.** Average the two middle scores on even panels; do not substitute a different median convention.
4. **Symmetric 20-percent trimmed mean — supporting condition.** Remove `floor(m/5)` scores from each tail.
5. **No-intervention, seeded-random, and marginal-score-greedy policies — selection baselines.** Keep matched recorded comparisons, including ties. They are not component ablations.

Do not require discarded rank-window or clipped-envelope branches in the main narrative. No evaluated Borda condition, equilibrium model, measured training response, architecture intervention, or unrun ablation belongs in this paper. State equal task weights, no spillover, no score regression outside the support, fixed rivals, and uncertain mapping from score uplift to actual training investment.

## Results structure and uncertainty

Lead with the exact fixed-cohort mean–median contrast. Follow it with all-target attainability and support/certificate scope for both primary families. Maintain one definition of **target attainment rate**: the fraction of ordinary primary target decisions with a verified strict-first support and a supported claim. Do not mix controls into that rate.

Use a compact main comparator table at half headroom for both families and all three rules, retaining ties with greedy and comparisons against random and no intervention. The complete rule/ceiling/seed grid and all recorded comparator intervals belong after references. A meaningful exact-selection advantage in one small-panel condition does not make the frozen reference a newly invented optimizer.

The main body must distinguish:

- Exact six-task and mean minimum costs from larger median/trimmed feasible upper bounds and verified lower bounds.
- Unattainable cases from unresolved support intervals. Never draw the `m+1` infeasibility sentinel as an actual intervention cost.
- Successful-target support from a penalized effort summary: `final.metric.mean_effort_fraction` assigns one to nonattainment. Likewise, `final.metric.mean_verified_gap_fraction` measures distance to a verified lower bound, not necessarily true optimizer error.
- Paired comparisons on identical targets from cross-ceiling summaries with different attainable cohorts.
- Three sampling seeds from independent training replicates. Public pools and some targets/ancestry may overlap.

Existing intervals use 200 paired cluster resamples with RNG seed 48271, conditional on fixed snapshots and rival pools. They compare the selected procedure with random or greedy policies, not aggregation rules with each other. Do not reuse those intervals for the central reversal, invent p-values, or call the certification intervals statistical confidence intervals. Show all seed summaries and describe the cross-rule comparison as descriptive.

Keep matched constant-ceiling, zero-response, permutation, and replay checks in a concise scope discussion; replay has statistical weight zero. Passing them establishes only the tested properties. Report auxiliary six-coordinate projections and revision-matched BBH separately, never pooled into primary scores or described as independent transfer replication.

## Required figures and layout

The inspected `paper.sty` declares a **5.5-inch text width and 9-inch text height** in a single-column ICLR layout. Thus `full_width` means the one text column, not a two-column spread. Half-width placement would provide only about 2.75 inches and is unsuitable for the planned multi-panel comparisons. Use ordinary full-text-width figures, not a two-column layout workaround.

| Figure | Concrete design and source | Readability budget and footprint |
| --- | --- | --- |
| 1. Investment overview | `generate-concept-figure`; fixed scores/rivals, target-only headroom equation, three aggregation branches, exact/infeasible/bounded support outcomes. Source: `final.evidence.episodes`, interpreted with inspected source/contract. No numerical toy result. | One shallow diagram, at most six visual groups and three aggregator branches; approximately 5.5 by 1.8 inches; full width on page 1 or 2; at least 9-point labels. |
| 2. Exact rule contrast | `matplotlib`; two side-by-side signed dot plots at half and full headroom, each showing the per-seed median-minus-mean exact support fraction on the same fixed cohort. Source: ordinary primary Open LLM slices of `final.evidence.episodes`. | Two panels, two per row, three seed categories, one contrast series; approximately 5.5 by 2.1 inches; full width; same signed y scale and zero line; caption gives cohort counts. No invented error bars. |
| 3. Attainability and support scope | `matplotlib`; 2-by-2 composite, rows HELM/Open LLM; left all-target attainment at three ceilings; right paired support bounds at half/full headroom. Source: ordinary primary `final.evidence.episodes`. | Four panels, two per row, at most three categories and three rule series per panel; approximately 5.5 by 3.4 inches; full width, common legend and readable scales; at least 9-point labels. |

For Figure 3 right panels, intersect attainable targets across all three rules within each seed and ceiling, state cohort sizes, and average the within-seed lower and feasible upper fractions with declared equal seed weights. Unlike Figure 2, these cohorts may differ across ceilings. Exact costs collapse to points; other intervals are certification ranges. Show an empty cohort as not estimable, not as a cost or an imputed value. Do not use these changing-cohort panels alone to establish the central reversal.

All figures are direct condition comparisons; no optimization trajectories, milestone views, or campaign timelines. Use tables for scope, status counts, and policy differences rather than another dense dashboard. Quantitative figures must export vector PDF and PNG at 300 DPI from source; LaTeX uses PDF whenever available. Preserve editable overview source and prompt provenance. If only raster is available, regenerate at least 2400 pixels wide for full-width placement, or 1200 pixels for a later justified narrow placement; never upscale. Only the overview uses the concept-figure workflow. This stage does not generate figures or invoke that workflow.

## Main-body budget and venue contract

Target ICLR 2026, anonymized, with about **8.5 substantive body pages excluding references**. Figure area is included in the following allocation:

| Scientific use of space | Approximate pages |
| --- | ---: |
| Abstract, introduction, precise contribution and scope | 1.25 |
| Safely grounded related work and modeling context | 0.75 |
| Bounded-response objective and assumptions | 1.00 |
| Support computation and certificate scope | 1.00 |
| Public-panel protocol, pairing and uncertainty | 0.75 |
| Exact contrast, attainment, support bounds and comparators, including figures | 2.75 |
| Limitations and conclusion | 1.00 |

An eight-page body counts only if its last page is at least 75 percent full. Expand useful model explanation, certificate reasoning, comparison clarity, and limitation analysis before adding visual or textual filler. Do not import the NeurIPS template or checklist obligation from a source-data manifest in place of the selected ICLR venue requirements. Use the provided ICLR style, with no author names, affiliations, identifying links, acknowledgements, or funding statement. Include a separate `LLM Usage` section, optionally after references, describing actual assistance only.

Suggested headings: **Introduction; Related Work and Scope; Bounded-Response Investment; Computing Support and Certifying Limits; Public Score Panels and Comparison Protocol; Response-Dependent Aggregation Costs; Attainability and Certificate Scope; Limitations and Conclusion.**

## Supplementary Information after references

Purpose: add grounded mathematical, uncertainty, sensitivity, and reproduction depth without concealing evidence essential to the thesis. No new experiment or guessed later ranking is required. Route separately supplied authoritative appendix-ranked analyses here without retroactively modifying the strategy.

| Planned subsection | Available grounded content | Registered source IDs |
| --- | --- | --- |
| Support objective, aggregation conventions, and certificates | Full objective, strict margin, median/trim definitions, headroom argument, enumeration, infeasibility test, conservative-bound and feasible-witness reasoning, tied to inspected frozen source and `task/evaluate_final.py`. | `final.evidence.episodes` |
| Complete rule-by-response and comparator tables | All ordinary primary counts, support/status/bounds, zero/random/greedy comparisons and recorded conditional cluster intervals, including null effects. | `final.evidence.episodes`; `final.metric.feasible_rate`; `final.metric.mean_effort_fraction`; `final.metric.mean_verified_gap_fraction` |
| Task granularity and auxiliary sensitivity | Separate six-task projections and BBH records using evaluator routing, revision reconciliation, and distinct-run caveat; no unrun causal granularity experiment. | `final.evidence.episodes` |
| Matched controls and evaluation scope | Constant/zero-response/permutation/replay checks and their narrow interpretations; completed final qualification and retained evidence-trust caveat. | `final.evidence.episodes`; `final.metric.control_pass_rate`; `final.qualification.status`; `final.qualification.outcome`; `final.qualification.correct` |
| Frozen selection and unsuccessful alternatives | Brief nonchronological disclosure of baseline selection, zero search-score change, three scored and zero unscored attempts; unknown failure causes and search/final separation. | `study.selection_kind`; `study.investigation_outcome`; `study.search_score_delta`; `study.attempts.total`; `study.attempts.scored`; `study.attempts.unscored` |
| Public data provenance and reproduction map | Existing source manifests, hashes, normalization/alias grouping, filtering, strata/seeds, CPU dependencies and commands; planned script-to-table/figure map; license uncertainty and evaluation-setting differences. | `final.evidence.episodes` |
| LLM Usage | Disclose documented ideation, code preparation, query planning, and framing assistance; add writing/figure use only if it actually occurs. Do not invent identities, human checks, or training. | `study.selection_kind`; `study.attempts.total`; `final.evidence.episodes` |

The listed IDs anchor evaluated outcomes; direct method and provenance details must additionally cite their actual local artifacts in the later evidence map, rather than pretending an episode record itself contains the entire source manifest.

## Reproducibility and reference handoff

Use HELM **v1.13.0**, Open LLM contents revision `9c09a7cae43334062a82cb164f2ef255013dafa2`, and the distinct results revision `aa81ecc38fdc5708254b833923368970efdf5ef5`. The final manifest records acquisition on 2026-11-17 and extracted-record SHA-256 `d80abb1b13c6962e15f04d9794fc18fcf39e91cf7c79c679e233d3031f934398`. Preserve each source checksum from `task/resources/final/manifest.json`, and distinguish public repository sizes from the evaluated extracted pools. Existing manifest and raw records support normalization, filtering, alias grouping, split, and setting caveats; do not claim perfectly homogeneous evaluation conditions.

BBH reconciliation matches model revisions but does not prove identical evaluation settings. In the Open LLM auxiliary routing, odd slots use BBH and even slots use the primary-family projection. Do not match auxiliary slots to primary model identities without reconstructing their actual identifiers. Data-specific redistribution permission remains unresolved: public accessibility, code licenses, and model licenses do not establish a score-data redistribution license.

The writer must create deterministic derived-data/plot/table scripts, record their exact source slices and commands, and provide the dependency versions already available in `task/requirements.txt`. Those manuscript reproduction scripts are not present merely because the evaluated solver exists. Regeneration from existing records is not a new empirical run; any genuinely new analysis must be labeled and grounded separately.

The bibliography currently provides metadata retrieval, not evidence of substantive reading, and many entries are tangential. Several relevant starter records are absent. Before literature-dependent prose, curate safely and actually read the permitted source; use only available, verified citation keys and do not fabricate positioning or pad related work. This is a writer-stage prerequisite, not a reason to invent a novelty claim now. No external page was accessed during strategy generation. Do not identify or search for the prohibited study, expand citation graphs, or use discussion/aggregation pages; stop and log any accidental exposure.

## Language guardrails

**Forbid headings:** Search Progression; Campaign Phases; Milestones; First Valid Result; Timeline; Experiment A; Experiment B; From Baseline to Winner; Optimization Breakthroughs; Successful Certificate Variants.

**Forbid phrases:** “we then tried,” “first valid result,” “subsequent improvements,” “next-best,” “later variants,” “winning implementation,” “state of the art,” “universally most robust aggregation,” “median always requires more investment,” “measured training cost,” “causal contamination effect,” and “all full-panel solutions are optimal.”

Private-only terminology exclusions for manuscript prose: `correctness rate`, `correct and eligible`, `eligible`, `combined_score`, `rubric`, `worker_01`, and `worker_02`. Prefer target attainment rate, support fraction, strict first place, exact minimum support, certified infeasibility, and feasible support interval.

## Completion boundary

This strategy supports a coherent conditional scientific paper, not a claim of conference acceptance or an already-complete reproduction package. Core limitations, unsuccessful search disclosure, all-target attainment, conditioning definitions, and exact-versus-bounded scope remain in the main paper. No manuscript, claim-mapping JSON, figure, or new research experiment is produced here, and final-paper validation is not run. Bibliographic substantive reading, plotting scripts, manuscript drafting, and later validation remain downstream work.
