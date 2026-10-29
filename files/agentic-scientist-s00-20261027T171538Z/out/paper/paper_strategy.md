# Paper Strategy — `paper_standalone` / `write-paper-standalone`

**Status:** ready
**Provisional title:** *Six Cheap Statistics versus Worst-Case Bounds: Predicting Random-Walk Cover Times on Small Graphs*
**Venue:** ICLR 2026. The template is single column with a 5.5 in text width. The body must be 8–9 pages, double-blind, with an LLM Usage section.

## 1. Grounded situation
- **Final evaluation** (`final.qualification.*`): status `completed`, outcome `qualified`. The validity diagnostics are clean: isomorphism overlap 0, order-invariance difference 0, capped walks 0, failed episodes 0.
- **Studied method** (`study.*`): the frozen selection is the original configuration (`selection_kind=baseline`, `investigation_outcome=completed_no_winner`). There was 1 attempt: 0 scored, 1 unscored. The unscored variant is missing evidence, not a loss, so it gets no performance claims.
- **Predictor:** log-linear ridge regression of ln C on ln n, ln m, ln(mean deg), ln(max deg), ln(min deg), ln diam, and ln n·ln diam. Features are standardized, ridge is 1e-3 and the intercept is unpenalized.
- **Key numbers** (sealed final, family-weighted mean absolute log error):

| Predictor | Error | Paired delta vs. studied predictor |
|---|---|---|
| Studied predictor | **0.183** [0.167, 0.207] | — |
| OLS (ln n, ln m) | 0.526 | CI [−0.391, −0.288] |
| Matthews reference (needs full graph) | 0.605 | point only |
| Constant | 0.942 | — |
| Permuted-feature control | 1.261 | CI [0.955, 1.196] |
| Best of 2m(n−1), (4/27)n³ | 1.397 | CI [−1.303, −1.130] |
| (4/27)n³ | 1.604 | — |
| 2m(n−1) | 1.836 | — |

- **Per-family errors:** star 0.056, random 3-regular 0.059, random tree 0.062, path 0.092, cycle 0.129, binary tree 0.163, lollipop 0.164, complete 0.357, grid 0.364, Erdős–Rényi 0.381.
- **Paired gain over the best bound:** significant in 9 of 10 families. It is largest for random 3-regular, complete and Erdős–Rényi (about −2.1). Lollipop is −0.111 with CI [−0.225, 0.013], which includes zero.

## 2. Central question
For connected graphs with n ≤ 30, can a regression on six cheap statistics predict expected cover time more accurately than the generic bounds 2m(n−1) and (4/27)n³? How does the error depend on graph family?

## 3. Central thesis
Six cheap statistics in a log-linear ridge model predict held-out small-graph cover times with a geometric-mean error factor of about 1.2 (0.183 log units). The better generic bound has a factor of about 4 (1.397). The advantage is significant in 9 of 10 families and largest where the bounds are loosest (n log n-type dense/expander families). It is not statistically clear on lollipops, where the cubic bound is nearly tight. The predictor's own error is highest on complete, grid and Erdős–Rényi graphs.

## 4. Why this framing
**Candidate framings compared:**
1. **Method-novelty paper.** Rejected. The predictor is the original simple configuration, and no new variant was scored.
2. **Negative-results paper about search.** Rejected. It would misrepresent a qualified, strongly positive sealed measurement. The no-winner selection is a scope fact to disclose, not the story.
3. **Empirical characterization study (chosen).** It answers both task questions with paired CIs and controls. The bound-slack pattern also supports a mechanistic reading: the bounds are tight only near their extremal families (lollipop, path), so fitted prediction gains most where true cover times sit far from the worst case. This suits an ICLR audience that values controlled comparisons and calibrated claims.

No prior paper or staged inputs exist (edit mode is inactive), so no prior story is carried over.

## 5. Method groups
| Group | Role | Reason |
|---|---|---|
| Statistics-only log-linear ridge | proposed (studied) | The sealed-evaluated predictor. Present it as simple and reproducible. |
| 2m(n−1), (4/27)n³, best-of-two | baseline | The task's named comparators, with paired plane and per-family CIs. |
| Matthews reference (max hitting time × H_{n−1}) | supporting | A graph-aware, tighter bound. Only point estimates are available. |
| OLS(ln n, ln m), constant | ablation-like references | Show the value of degree and diameter beyond size. These are evaluator-defined, not training-matched ablations. |
| Permuted-feature control | supporting | Shows predictions depend on each graph's own statistics. |

## 6. Results to emphasize
1. Plane-level accuracy against all comparators (Table 1 and Fig. 3).
2. The per-family reliability map with paired gains and CIs (Fig. 2), including the lollipop interval that includes zero.
3. Bound slack by family (derived as predictor error minus delta): smallest on lollipop (~0.28) and path (~0.48), largest on complete and Erdős–Rényi (~2.4). Gains track slack.
4. Controls and uncertainty: the permuted-feature control, isomorphism-disjoint splits, closed-form simulator checks, median Monte Carlo relative SE of 0.033, and the two-level bootstrap. The seed range of 0 reflects a deterministic predictor on fixed labels and is not robustness evidence.
5. Limits on statistics-only prediction: 12 held-out graphs share their exact statistic vector with another graph.

## 7. Figures (all at full text width, 5.5 in; PDF plus 300-DPI PNG; include the PDF)
- **Fig. 1 `overview_concept`** (generate-concept-figure, about 0.95 width, page 1–2). Pipeline: graph families → six statistics → log-linear ridge → predicted C, set beside the bounds. The evaluation side shows Monte Carlo labels, held-out isomorphism-disjoint graphs and paired bootstrap. Full width keeps the stage labels at 8 pt or larger.
- **Fig. 2 `per_family_reliability`** (matplotlib, 2 panels, 10 family rows). (a) Predictor vs. best-bound error on a log x-axis, families sorted by bound slack. (b) Paired delta with 95% CI and a zero line. The category budget is relaxed to 10 because the research question is explicitly per family. Horizontal rows at full width (about 5.5 × 3 in) stay readable.
- **Fig. 3 `plane_level_comparison`** (matplotlib, 2 panels of 4 horizontal bars, about 0.85 width). (a) Fitted and control predictors. (b) Bound-based predictors. Use a shared x-range.
- **Tables:** Table 1 has plane errors and paired CIs. Table 2 is the family roster with held-out counts from the evaluator catalogue (9 each for path, cycle, star, complete and binary tree; 5 grid; 18 lollipop; 16 each for the three random families; 116 total).

## 8. Page budget (8–9 body pages, last page ≥ 75% full)
| Section | Length |
|---|---|
| Introduction and contributions | ~1.2 pp |
| Background: cover time and generic bounds | ~0.7 pp |
| Predictor and feature rationale | ~0.9 pp |
| Evaluation protocol and Table 2 | ~1.2 pp |
| Results: Table 1, Fig. 3, Fig. 2, controls | ~2.3 pp |
| Discussion: where cheap statistics suffice, why bounds are loose | ~0.8 pp |
| Limitations | ~0.6 pp |
| Conclusion | ~0.3 pp |

Fill the space with explanation and analysis, not repetition.

## 9. Supplementary Information
- **Full per-family table:** predictor error, derived best-bound error, delta and CI for all ten families.
- **Protocol and validity diagnostics:** splits, Monte Carlo labelling, simulator checks, bootstrap, overlap, order invariance, capped walks, failed episodes, and feature collisions.
- **Reproducibility:** predictor source summary, episode seeds 211–213, evaluator seeds, and runtime.
- **Selection scope:** 1 attempt, 0 scored, 1 unscored. The search-pool error (0.193) is a different scope from the final 0.183 and is not pooled with it.
- **LLM Usage:** required by the venue.

## 10. Writer guardrails
- **Bounds vs. predictor:** bounds are guarantees; the predictor is fitted on in-distribution labels. Never call the predictor a bound.
- **Hypotheses:** explanations for the high-error families must be labelled hypotheses, since no ablations exist.
- **Lollipop:** write "no statistically clear advantage", not "worse".
- **Scope:** ten synthetic families, 5 ≤ n ≤ 30, uniform-start expected cover time. Make no transfer claims.
- **Citations:** only Lovász (`Lovász2001RandomWO`; skip the garbled `Asz1993RandomWO`) and Aleliunas et al. 1979 exist. Name Feige and Matthews in prose without inventing BibTeX unless verified entries are added. Do not use the forbidden original-paper sources.
- **Forbidden headings:** Experiment Timeline, Search Progress, Campaign Overview, First Valid Result, Milestones, Iteration History, What We Tried, Baseline Seed, Smoke Test, Cycle 1.
- **Forbidden phrases:** combined_score, correctness rate, correct and eligible, eligible, rubric, worker_01, program_0, ridge_log_linear_v0, physmix_cv_v1, baseline seed, campaign, first success, "we then tried", "after several iterations", state of the art, "outperforms all methods", "generalizes to arbitrary graphs", "tight bound" (for the predictor), provably, connectivity smoke test.
