# Paper Strategy (paper_standalone, ICLR 2026, double-blind)

**Status:** ready (narrow, measurement-style paper; no improvement claim).

## Title (provisional)
How Far Can Five Cheap Graph Statistics Go? Log-Linear Cover-Time Prediction on Small Connected Graphs

## Central question
For connected graphs with 6<=n<=30, does a ridge model on cheap statistics (n, m, mean degree, max degree, diameter) predict Monte Carlo start-averaged cover time with lower family-macro log error than the generic 2m(n-1) bound?

## Central thesis
On the sealed held-out graphs, the five-statistic log-linear ridge predictor (family-macro log MAE 0.181) is far closer to Monte Carlo cover times than the 2m(n-1) bound (1.754), a constant control (0.870) and a label-shuffled control (1.423); median Monte Carlo relative SE is about 0.029. Scope is 12 synthetic families, 24 test graphs. Which families the predictor fails on is *not* answered by the retained evidence.

## Why this framing
- The frozen selection is the seed baseline (`study.selection_kind=baseline`, investigation `completed_no_winner`, 1 attempt, 0 scored, 1 unscored, search delta 0.0). The studied method *is* the baseline, so no "improvement over baseline" is claimed. The comparison that exists is against the 2m(n-1) bound and controls, all in the same sealed final run.
- Final outcome is `qualified` / `completed` / correct=true (`final.qualification.*`). Candidate diagnostics trust is `unverified`; disclose. No failed gates exist to discuss.
- The unscored resistance/Matthews variant has no performance evidence. It appears at most as untested future work.
- The second half of the task's question (error vs graph type) cannot be answered quantitatively: no per-family metrics in `paper_data.json`. Treat as an explicit unknown/limitation, not a failure finding.
- Search score (-0.1913) and sealed final (-0.1814) are different scopes; never present them as an improvement.

## Edit mode
Not edit mode (placeholders unfilled, no previous_paper). `prior_paper_story_status` is nominal ("preserved"); nothing staged.

## Method groups
1. Five-statistic ridge predictor (proposed/studied): standardized log n, log m, log mean degree, log max degree, log diameter; ridge lambda=1, unpenalised intercept; bound fallback with no training data.
2. 2m(n-1) bound (baseline).
3. Constant control (baseline).
4. Label-shuffled control (ablation-style negative control).
5. Relabeling-invariance check (perm_max_rel_dev 0.0; supporting validity check).

## Results focus
- One direct comparison of family-macro log MAE (lower better); improvement_vs_bound 1.572 = 1.754-0.181.
- MC uncertainty only via median relative SE 0.0287 (noise-floor context, small vs 0.181).
- Episodes 201-203 all gave 0.18137: deterministic candidate on fixed graphs/labels; zero spread is NOT sampling uncertainty over graphs. State that graph-draw uncertainty was not measured.
- Derived ratios (about 1/5 of constant error, about 1/10 of bound error) allowed if labelled arithmetic.
- Unknowns: per-family, per-size errors.

## Figures
| id | type | generator | span | width | rationale |
|---|---|---|---|---|---|
| overview_pipeline | diagram | generate-concept-figure | full width (single-column template, ~5.5in) | 1.0 | graph -> statistics -> ridge -> compare with MC label and bound; aggregation hierarchy; place on page 1-2 |
| main_comparison | bar, 1 panel, 4 bars | matplotlib | full width | 0.7 | readable labels without shrinking; export PDF + 300 DPI PNG, reference PDF |

No trajectory figures. No error bars unless grounded.

## Using the 8-9 page body without padding
Evidence is thin, so space goes to: precise problem framing and why a worst-case bound is loose on small graphs; reimplementable method spec; metric/aggregation design (clipped log error, family-macro mean); a threats-to-validity section (small test set, family composition, deterministic episodes, MC labels, size range, unverified diagnostics); related work (Aleliunas et al., Feige, Lovász; only cite what is in references.bib). Do not invent experiments. If the evidence cannot honestly fill the budget, prefer substantive discussion; flag risk.

## Supplementary plan
1. Predictor specification and hyperparameters (frozen program source).
2. Evaluation protocol and full final-metric table (`final.metric.*`).
3. Episode records and qualification status (`final.evidence.episodes`, `final.qualification.*`).
4. Search-stage context, clearly separated (`study.*`).
5. LLM usage statement (ICLR requirement).

## Forbidden headings / phrases
Headings: Search Campaign, Iteration History, Milestones, Progression of Attempts, First Valid Result, Experiment A/B, Run Log, What We Tried.
Phrases: correctness rate, correct and eligible, eligible, combined_score, rubric, worker_01, "outperforms the baseline", "improves over the baseline", "state of the art", "generalizes to all graphs", unsupported "fails on"/"reliable on" family claims.
