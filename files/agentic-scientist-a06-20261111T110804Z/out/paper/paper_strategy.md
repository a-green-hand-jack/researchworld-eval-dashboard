# Paper strategy (standalone prompt family, ICLR 2026 single-column, 8–9 body pages)

**Status:** ready. **Edit mode:** off (no prior manuscript) → `prior_paper_story_status: rejected` is a formal "fresh framing" value only.

## Provisional title
Reporting Scores After Prompt Search: A Selection-Aware Posterior Interval from a Hierarchical Latent-Difficulty Model

## Central question
When a configuration is chosen on a finite benchmark sample and its search-time score is reported, how large is the optimism, what controls it, and can a selection-aware interval built only from the search-time evaluation log report fresh-question accuracy more reliably?

## Central thesis
The naive best-of-search score with a Wilson interval is biased upward and too narrow when many configurations are compared on few questions. An empirical-Bayes hierarchical logistic latent-difficulty posterior interval, fitted to all logged (question, config, outcome) triples and agnostic to the searcher, lowers the mean 90%-level interval score relative to naive, Bonferroni-Wilson and question-resampling reporters in the sealed final evaluation (outcome **qualified**, status completed). It retains residual bias and sub-nominal coverage in specific real-data regimes, so the claim is conditional.

## Why this framing
- Final evaluation: mean interval score 0.1449 (proposed) vs 0.2202 naive, 0.1974 Bonferroni, 0.2461 resample; coverage 0.929; null-control coverage 0.929; constant-world error 0.0 (`final.metric.*`, `final.qualification.*`).
- No `downstream_study` block → no downstream claims. Search: 3 of 3 attempts scored, 0 unscored; the frozen selection is the EB-IRT variant (-0.1480 search score; alternatives -0.1519 and -0.1562 from one evaluation each, not a significance ranking). Only the frozen winner has a final evaluation.
- The interesting content is heterogeneity across cases: large gains on synthetic and small-N real worlds; parity with naive on real halving (P4) and large N (P6); sub-nominal coverage there; the resample reporter is slightly better on several real exhaustive cases but very poor under halving. Honest reporting of this beats a "wins everywhere" story and beats a chronological campaign story.
- Rejected framings: (a) search-campaign chronology of three variants (variants are close in score; no final evidence for the two losers); (b) a broad "gap in LLM prompt tuning" claim (only one 0.5B model, two searchers, evaluator-owned worlds were tested); (c) a pure-theory framing (no theory results in artifacts).

## Method groups
1. Baselines: naive Wilson; Bonferroni-widened Wilson; question-resampling optimism reporter.
2. Proposed (frozen selection): EB hierarchical logistic latent-difficulty posterior interval (logit P = a_config − b_question, EB variances, Laplace draws, Gauss-Hermite over fresh difficulties, 5/95% quantiles, kappa calibration, degenerate-world and time guards).
3. Variants (search-plane only): parametric-bootstrap pivot calibration (narrow, coverage 0.77); config-by-subject interaction (coverage 0.8925, no gain).
4. Controls: synthetic null N1, real permuted-config null N2, constant-zero Z1.

## Results views
1. Aggregate final table with spread over 8 final seeds.
2. Optimism gap (naive signed bias, 0.0366 aggregate) vs N, K, searcher, world; proposed reporter's residual bias.
3. Per-case interval score and coverage vs the 0.90 nominal level.
4. Control behaviour.
5. Search-stage width-vs-coverage comparison (kept separate).
6. Open items: whether the gap changes comparative conclusions is not directly tested; say so.

## Figures (all full text width; template textwidth 5.5 in; PDF + 300-DPI PNG; PDF referenced in LaTeX)
- `overview_schematic` (required, `generate-concept-figure`, page 1–2): problem and reporter pipeline.
- `per_case_interval_score` (required, matplotlib, 2 panels ≤5 cases, 4 series; handle resample P2 outlier by annotation/broken axis).
- `bias_and_coverage` (required, matplotlib, 2 panels, 2 series).
- `width_vs_n` (optional, ~0.7 width; move to supplement if unneeded).
- Tables: final aggregate; search-stage variants.

## Body-page use
Problem formalization and interval score; estimator with reimplementable detail and ignorability motivation; controlled comparison with baselines; bias/coverage diagnostics; controls; sizeable limitations section. No padding.

## Supplement
Estimator details/hyperparameters; per-case × per-seed tables; search-stage variants; evaluation protocol and provenance (pinned MMLU-Pro and Qwen2.5-0.5B-Instruct revisions, seeds 9101–9108, measured compute); LLM-usage disclosure.

## Limits to preserve
One 0.5B model, MMLU-Pro, 24 prompt configs, exhaustive and successive-halving searchers, evaluator-owned synthetic worlds; no DSPy/MIPRO, no adaptive Ladder-style reporting; outcome tensor shipped with the task (not regenerated here); kappa calibrated on a local development harness; per-case diagnostics are `unverified` in trust; qualification gate diagnostics beyond outcome are unknown. Reference list: most bib entries are irrelevant (medical etc.) — cite only the adaptive-data-analysis entries; starter-literature works need verified addition before citing.

## Avoid
Chronology headings (campaign, milestones, iterations), pipeline-native terms (`combined_score`, "eligible", "correctness rate", "rubric"), SOTA / "guarantees coverage" / generality claims.
