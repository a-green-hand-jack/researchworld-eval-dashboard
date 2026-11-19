# Presentation commitment and evidence contract

Status: design specification; no empirical result or figure has been produced.

## Objective and scope

The objective asks how much targeted investment is needed to make a model first on public multitask leaderboards, and how this changes with aggregation. The delivered figures and tables will make that comparison checkable under the analysis owner's explicit intervention and investment definitions. They will not interpret score edits as measured training costs.

Read: frozen TASK.md, data.md, deliverable.md, resources.md and starter_literature.md under /initial-state/inputs/0. No literature searches or external literature pages have been accessed by this position. The idea-repo Brief and venue specification are not available yet and must be incorporated before delivery.

figtab-repo owns presentation design, renderers, figure assets, table fragments, captions and a figure/table provenance manifest. experiment-repo owns numerical results, estimands, optimization correctness and uncertainty computations. paper-repo owns manuscript prose and layout. story-repo settles delivered path ownership. Proposed presentation paths in paper-repo: `figures/`, `tables/`, `presentation/` (including generators, captions and manifest); these are requests, not a claim that CODEOWNERS already assigns them.

## Evidence-led display design

1. **Investment to reach first.** For each benchmark and aggregation rule, show the fraction of a specified model cohort that can become first as the investment budget increases. Use an empirical cumulative distribution of exact minimum costs only when exactness is established; label approximate bounds as bounds. Display unreachable targets explicitly. For number of edited tasks, show integer counts within each benchmark; a task-fraction companion permits cross-benchmark reading without implying that tasks have equal real-world cost. The origin includes already-first targets only if the common cohort definition includes them, and the caption states this choice.
2. **Paired rule comparisons.** Rules must be compared on the same targets and intervention assumptions. Prefer a paired difference display or paired table, with the difference direction, unit and denominator explicit. An apparent contrast from independently selected rule-specific target cohorts cannot support a rule effect. A finite difference is undefined when either side is unreachable; report those cases separately.
3. **Assumption dependence.** If the analysis supplies intervention strengths, caps, weights or other robustness settings, show the main metric across the actual settings, using the same cohort and rule colors. No line should connect points across an unreported change of model population or estimand. Include failure cases rather than selecting only settings that favor a rule.
4. **Benchmark and result tables.** A compact cohort table will identify the frozen source, score scale, number of retained models/tasks and exclusions. A result table will state the investment unit, cohort, reachability denominator and exactness/bound status. Numerical entries must be generated from committed analysis artifacts, including any uncertainty, rather than typed from prose.

Final figure count and selection follow actual claims and available evidence. These are encoding decisions, not assumed empirical conclusions.

## Input needed from analysis

Supply committed files and their schema, the normalized model-by-task score matrix where needed, and a machine-readable record per benchmark/target/rule/intervention setting with minimum cost (or bounds), feasibility and solver status. Supply cohort selection and source snapshot/checksums; tie/first-place definition, tolerances, task weights, score normalization, caps, and treatment of missing values. If reporting uncertainty, supply the estimand, sampling unit, method, seed and numerical intervals/replicates. Avoid encoding infeasibility, timeout, missing data and zero cost by the same sentinel.

A suggested row key is `(benchmark, target_id, rule, intervention_setting, cost_definition)`; the analysis owner may choose another schema. Rendering will adapt to its actual committed outputs. No demand is made for analyses outside the agreed study plan.

## Statistical and visual standards

- A complete fixed leaderboard cohort is a descriptive population. Variation across its targets is not automatically sampling uncertainty. ECDFs of that population need no invented confidence interval.
- Any bootstrap interval must state what is resampled and which generalization it supports. Do not replace uncertainty of task scores with uncertainty across models. Do not infer a training dose-response from hypothetical score changes.
- Use linear axes with visible units for bounded scores, task counts and fractions. Avoid truncation that magnifies small rule differences; choose transformations only if the observed range justifies them and label them.
- Use a stable colorblind-accessible rule palette, augmented with line styles or direct labels. Use shared axes only when units/definitions match. Preserve zeros, ties and infeasible targets.
- Render publication figures as vector PDF, with PNG previews; generate table LaTeX and plain machine-readable values. Font sizes and dimensions follow the selected venue's final column geometry.
- Captions identify the claim, cohort, source snapshot, intervention, cost, first-place/tie convention, denominator, interval meaning (if any) and limits needed to interpret the display.

## Delivery and verification

Every delivered output will retain its generator and a mapping to input paths/checksums and a reproducible command. Open and inspect every delivered PDF/PNG/table; check final-size legibility, clipping, labels, totals and consistency with inputs. Inspect figures again in the paper-repo root PDF after integration. Numerical computations of new estimands will be requested from the analysis owner; presentation-only reshaping/formatting stays here.

Delivery waits only for its specific missing inputs, not unrelated study work. No mock or synthetic result is delivered as evidence. Before delivering, re-read objective issue #1, the available Brief, the agreed plan and venue specification; update this commitment if the scope changes.

## Open input requests

- experiment-repo#3: committed numerical inputs and claim/interpretation boundaries.
- story-repo#3: settled claim coverage and delivered paths/CODEOWNERS.
- venue-repo#2: official venue geometry and presentation conventions.
- Own commitment: figtab-repo#2.

There are no empirical outputs to inspect or deliver at this stage; final renderers depend on the actual supplied schemas. These requests remain open so their usable answers can activate the dependent work.

## Settled scope and first empirical delivery

Analysis supply is complete at experiment-repo `f558276d110ab218150edb4bc8e4d6a145998eb7`; experiment-repo#3 is answered. story-repo#3 accepts the three proposed delivered paths and study coverage; merged paper-repo CODEOWNERS assigns them to figtab-repo. venue-repo#2 supplies NeurIPS 2026, single-column 5.5-inch text width. The idea-repo wiki Brief has now been read and reconciled.

Delivered selection: primary challenger budget curves; bounded-gain reachability for fixed full evaluation cohorts (as paper-repo#3 requested); composition-sensitivity plot; cohort, primary-budget, paired Borda, robustness, random-selection and ceiling tables. Their generators, captions, metadata and numerical provenance accompany them under the agreed paths. See `presentation/README.md` and `presentation/inspection.md`. Remaining work after handoff is visual inspection in paper-repo's integrated root PDF; final claim prose and page layout remain paper-repo's.

## Corrected numerical schema handoff

After independent analysis review, experiment-repo `d58e1529360f4cdf771f6d87f941f9ae9a7fe8ee` corrected restricted-gain random stopping denominators and supplies fixed-primary challenger curve artifacts. Renderer/provenance now use that schema with an explicit full-cohort MC selection; displayed primary values and all rendered assets are byte-identical. Requested correction figtab-repo#4 is answered and closed. Initial presentation PR paper-repo#10 merged; follow-up schema PR #13 supplies these renderer/provenance changes. Integrated root PDF is not yet in paper-repo main, so inspection request paper-repo#12 remains open.

## Completion

The integrated root PDF at paper-repo `0cb7b7f6463c5e137d3ded0cfbd02c172793d114` has been opened and inspected on every display page (5, 6, 11, 12). All three figures, six tables and their captions are legible and consistent with their declared cohorts and uncertainty meanings. All twenty generated output hashes match the integrated delivery. Detailed verification and the exact PDF checksum are in `presentation/inspection.md`. No presentation work remains for this version; substantive changes to a display or its integration require reinspection.
