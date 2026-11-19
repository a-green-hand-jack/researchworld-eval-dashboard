# Paper strategy: refit-verified removal budgets for Bradley-Terry leaderboards

Status: ready. Prompt family: `paper_standalone` (skill `write-paper-standalone`). Venue: ICLR 2026, single-column, 5.5 in text width, 8 to 9 body pages, double-blind, LLM-usage section required. Edit mode is not active (no prior manuscript staged), so there is no prior story to preserve or recenter.

## Grounded state of the run
- Search stage: three scored attempts (0 unscored), all at search score 0.4993, equal to the starting baseline (delta 0.0). Investigation outcome `completed_no_winner`; the frozen selection is a non-winner candidate (source attempt c01). Search data: arena-55k (64 models, 57,477 rows) and MT-Bench human judgments (6 models, 3,355 rows). Crowd family 0.9987; expert family 0.0; flip rate 0.5.
- Sealed final stage (separate scope, different data): outcome **qualified**, status completed. Data: arena-140k after content-hash deduplication (52 models, 135,630 rows) and NBA 2006 to 2015 (30 teams, 12,900 rows). Mean score 0.926 (crowd 0.988, sports 0.864); random-removal reference 0.041; influence-only reference 0.926; flip rate 1.0; control gap +0.112.
- Per-case verified budgets (rows; cap = ceil(2% N)): crowd top 62 (cap 2,713), crowd mid 4, sports top 62 (cap 258), sports mid 8. Influence-only B2 gives the identical 62, 4, 62, 8; opponent-targeted B3 gives 650, 6, 88, 12; random B1 flipped 0, 6, 0, 0 of 20 draws. Permutation controls flip with 2 and 10 rows and are non-vacuous; empty set never flips; copy control 0 of 2. Both final episodes were identical.

## Central question
Under an exact Bradley-Terry refit (ridge 0.01, ties as half wins), what is the smallest set of comparisons within a 2% cap whose deletion reverses an adjacent top or mid pair, and does that budget differ between a crowd-vote table and a sports table under one verified protocol?

## Central thesis
Adjacent-pair reversals need very few deleted comparisons (4 to 62 of 135,630 crowd rows, about 0.003% to 0.046%; 8 to 62 of 12,900 NBA rows, about 0.06% to 0.48%, derived as k/N), mid pairs are cheaper than top pairs, and the sports budget is about ten times larger as a share of comparisons. But first-order influence ordering with exact-refit bisection already reaches every measured budget, so the elaborate search stages add nothing measurable, and the design contrast is confounded with table size, participant count and era. The claim is a bounded descriptive one, not a method-superiority or causal claim.

## Why this framing
A method-superiority story is unsupported (selected equals B2 everywhere; search delta zero). A run-diary of three tied variants is not a paper. A measurement study with the search procedure as an instrument, evaluator-owned baselines and controls, and honest scope is supported and acceptable under the task ("small sensitivity", "depends on conditions" are valid outcomes). Qualified is reported as achieved but only certifies that the evaluation completed with controls passing. Expert-judgment evidence exists only from the search stage (no flip within the cap on the 6-model table); its cause (myopic search vs infeasibility) is unknown and must be labelled so.

## Method groups
1. Studied configuration (proposed, as instrument): influence-on-gap with leverage correction, re-linearised greedy, prefix bisection, drop-and-readd polish, exact-refit acceptance. Budget is an upper bound on the minimum.
2. B1 random removal (baseline), B2 influence-only (baseline, decisive comparator), B3 opponent-targeted (baseline).
3. Validity controls (supporting): empty set, label permutation, cross-table copy.
4. Search-stage variants (supporting, compact): cell-aggregated relaxed search and stationarity LP tied at 0.4993; runtimes about 1.3 s, 2.0 s, 114 s per episode. Presented as a negative result, not chronology.
The starting baseline program was not run in the final stage, so no final-stage selected-vs-starting comparison is written; the search-stage tie is reported as such.

## Results views
Final-stage per-case budgets with comparators; design contrast with explicit confounds; top vs mid; controls; the studied-equals-B2 negative result; search-stage tie and expert non-flip kept in a separate section; scope statement (point-estimate order reversal of one adjacent pair, 2% cap, no CI events, no rigging or insertion, no model-judge design, two final designs, two identical episodes, no significance claims).

## Figure specs (all full text width in the single-column template)
1. `protocol_overview` (diagram, `generate-concept-figure`, full width 1.0, early placement page 1 or 2): protocol pipeline, baselines and controls, designs and stages. 1 panel.
2. `main_budget_by_case` (grouped bar, matplotlib, full width 1.0): 2 panels (crowd, sports), 2 categories (top, mid), 3 series (studied, B2, B3); log y, percent of comparisons, cap line; random flips annotated as x/20; studied and B2 visually distinguishable because they coincide.
3. `controls_permutation` (paired bar, matplotlib, width 0.9): real vs permuted budget; spread ratio. Convert to a table if it will not read at size; do not shrink.
Export PDF plus 300 DPI PNG, reference the PDF; raster-only needs at least 2400 px at full width and must be regenerated, not upscaled. Tables carry the dataset summary, per-case results and search-variant results.

## Body-page budget (8 to 9 pages, last page at least 75% full)
Introduction 1.0; related work 0.6; problem and method 2.0 (with Figure 1); protocol and datasets 1.0; results 2.5 (Figures 2 and 3, tables, search tie, expert non-flip); discussion and limitations 1.0. Extra room goes to sharper definitions and limitation analysis, not to extra claims.

## Supplementary plan
Full per-case and per-episode table; controls and qualification details; search-variant table with unknown expert-table cause; algorithm and protocol specification; data provenance, dedup counts and reproduction; LLM-usage disclosure and extended limitations. Nothing essential to the thesis is moved there.

## Forbidden
Headings: Experiment 1/2, Campaign Overview, Search Progression, Milestones, First Valid Result, Iteration History, Attempt Chronology, What We Tried, Lessons Learned from the Run, Pipeline Details. Phrases: correctness rate, correct and eligible, eligible, combined_score, rubric, worker names, "state-of-the-art", "outperforms the baseline", "significantly better", "proves the minimum", "design X causes", chronology wording.

## Writer notes
- Report budgets in rows and percent of comparisons; the evaluator's "budget fraction" (0.074) is a fraction of the cap, not of all comparisons.
- Never merge search and final scores; they are different scopes and datasets.
- Cite only keys in `references.bib` (Bradley-Terry literature, Broderick et al. data-dropping metric). The bib lacks Chatbot Arena, MT-Bench, influence functions, vote rigging and leaderboard-illusion entries; do not invent keys, and do not use or cite the withheld prior work.
- Keep anonymous; include the LLM Usage section.
