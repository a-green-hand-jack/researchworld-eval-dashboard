# Paper strategy (paper_standalone, ICLR 2026, single column, 8–9 body pages)

**Status:** ready. **Provisional title:** How Far Do k Benchmarks Go? Cold-Start Benchmark Selection and Score Imputation on Family-Disjoint Held-Out Models.

## Central question
When only k benchmarks can be run on a new model, how accurately can a history-fitted selector-plus-imputer recover its scores on the remaining benchmarks, how does the error fall with k, and how much of the gain comes from cross-benchmark structure versus the choice of which k to run?

## Central thesis
On MTEB, Open LLM Leaderboard and HELM Lite with family-disjoint held-out models, a wrapper-selected, rank-Gauss-transformed, NNLS-stacked Gaussian imputer substantially reduces error versus column-mean imputation (sealed final: outcome **qualified**, skill 0.434, pooled nRMSE 0.562) and beats permuted-observation controls clearly (gap 0.678). Its edge over random-k selection with a ridge imputer is small (0.016), MTEB error falls with diminishing returns in k (0.787 at k=2 → 0.638 at k=20), and difficulty varies by leaderboard.

## Why this framing
- Final evaluation completed and qualified (`final.qualification.*`); a positive-but-modest, calibrated result is supportable. Qualification says nothing beyond the three leaderboards.
- No `downstream_study`; ablations empty; offline experiment/theory scripts have no reported numbers; candidate diagnostics "unverified". So no selector-vs-imputer attribution, no theory claim, no generalization claim.
- Thesis-first organization: question → protocol → method → error vs k → baselines/controls → per-leaderboard difficulty → limitations. Rejected alternatives: a "search campaign" narrative (chronology, three scored variants, one null) and a "method beats baselines" headline (overclaims given 0.016 over random-k).
- Not edit mode; no prior paper.

## Method groups
1. **Proposed** – selected configuration (best search score, c02; c03 ties exactly): rank-Gauss/z representation, EM Gaussian with missing data, selection by covariance-trace greedy or K-fold held-out-error wrapper (history-only CV), per-target NNLS stack (Gaussian conditional means, ridge, kNN, median), clipping, fallback.
2. **Variant (ablation-like, confounded)** – greedy conditional-variance + Gaussian conditional mean (search nRMSE 1.067 vs 1.028; skill vs random 0.100 vs 0.132; permuted gap 0.522 vs 0.568). Many components change at once; label as variant comparison.
3. **Null-result variant** – monotone latent-skill member + A-optimal latent selector: identical search metrics to the selected configuration; cause unknown.
4. **Baselines/controls** – column-mean, random-k ridge, greedy-forward ridge, permuted and constant controls (aggregated values only).

## Results focus
- Error-vs-k on MTEB (4 points) as the answer to "how large a k"; no sufficiency threshold claimed.
- Per-leaderboard nRMSE: MTEB 0.703, HELM 0.501, OLL 0.482; k grids and column counts differ (OLL has 6 columns), so not a pure difficulty ranking.
- Skill: vs column-mean 0.434 (seed episodes 0.433/0.427/0.433), vs greedy ridge 0.099, vs random-k ridge 0.016; selector and imputer are scored jointly.
- Permuted-control gap 0.678.
- Search-split three-variant table (two seeds each), kept separate from sealed results.
- Limitations: joint scoring, three seeds, no CIs on pooled metrics, embedding-model leaderboard, non-adaptive selection, missing ablations/theory.

## Figures (both full-width; ICLR text width ≈5.5 in, no column layout to rescue dense figures)
- **protocol_overview** (`generate-concept-figure`, page 1–2, 1 panel): history matrix → commit k → observe → impute → score; names leaderboards and baselines.
- **main_results** (matplotlib, 3 panels, PDF + 300-DPI PNG, PDF in LaTeX): (a) MTEB nRMSE vs k; (b) nRMSE by leaderboard + pooled; (c) skill vs three baselines. No invented error bars. No progression views.
- Tables: compact final-metric table; search-variant table.

## Body-page use
Problem formulation and protocol (including metric definitions), reimplementable method, results (figure + two tables), substantive limitations and practitioner discussion. Tighten rather than pad if evidence is short.

## Supplement plan
1. Evaluator protocol and data partitions (pinned revisions, sizes, split rule, k grids, seeds, controls, aggregation hierarchy).
2. Full method specification and hyperparameters (incl. latent-skill null-result extension).
3. Full final-metric table, seed episodes, search-variant metrics.
4. Unperformed analyses, data/licence notes, LLM Usage statement.

## Forbidden headings/phrases
Experiment 1/2, iteration history, search campaign, progression, first successful run, milestones, run log, cycle-by-cycle; "correctness rate", "correct and eligible", "combined_score", "rubric", "state of the art", "significantly better" (no tests), "first to".

## Writer cautions
Never invent per-baseline nRMSE, per-family skill, CIs, ablation or theory numbers. Only cite bib entries that are relevant (SubLIME, SimBA, From Benchmarks to Skills, Mapping Overlaps); the bib is otherwise mostly irrelevant retrieval noise and lacks the starter-literature papers. Search nRMSE (>1) and final nRMSE (<1) are different partitions; do not compare them. Double-blind and LLM Usage section required.
