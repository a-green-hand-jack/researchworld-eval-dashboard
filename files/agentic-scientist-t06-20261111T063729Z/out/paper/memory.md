
- Reference query plan (2026-11-11): wrote 10 queries on Bradley-Terry, AMIP/influence-based data-dropping robustness, Arena/MT-Bench/NBA-Elo data context, vote rigging, leaderboard illusion, rank-aggregation robustness, ranking uncertainty. Chosen over generic benchmarking/optimization queries because they match methods and datasets actually run; no query targets the withheld paper.

- Paper strategy (2026-11-11): chose a thesis-first measurement paper on refit-verified removal budgets for BT leaderboards (crowd vs sports final, expert search-only). Rejected method-superiority (selected == influence-only B2 on all 4 final cases; search delta 0.0, 3/3 scored) and run-diary framings. Final outcome qualified is reported as achieved, not as superiority. Gap noted: references.bib lacks Arena/MT-Bench/influence/rigging entries.

- Paper draft (2026-11-11): wrote paper.tex (ICLR, anonymous, 9 body pages, SI incl. LLM Usage), claims_grounding.json (25 claims), figure_manifest.json (protocol_overview placeholder owned by orchestrator; main_budget_by_case and controls_permutation via scripts/build_figures.py). Rejected framings: method superiority (selected == B2 everywhere), run diary. Added derived normaliser (2N/M) showing crowd-vs-sports direction reverses; top-pair share ratio equals table-size ratio (both 62 rows). Rewrote/removed: any claim on c02/c03 implementation (no source evidence), NBA 'regular season' (unknown), starting-baseline held-out comparison (not run). Citation gap: bib lacks Arena/MT-Bench/influence/rigging works; stated openly in related work and SI. Evidence verifier: 0 dangling; validate_claims passes. Concept-figure placeholder guarded by .concept_figure_complete.
### 2026-11-11T08:09:23.528498+00:00 | step=paper | scope=paper
- summary: Final paper written: bounded descriptive measurement of refit-verified removal budgets (crowd 62/4 rows, NBA 62/8 rows); studied config equals influence-only B2; qualified reported as completed-with-controls only. paper.tex and claims_grounding.json consistent with paper_data.json; 0 dangling evidence refs.
- evidence: derived/final_stats.json; claims_grounding.json 25 claims validated; scientific-evidence/verification-report.json dangling=0
- next_action: orchestrator renders protocol_overview concept figure then final compile/validation

### 2026-11-11T08:09:32.348952+00:00 | step=paper | scope=paper
- summary: Final paper written: bounded descriptive measurement of refit-verified removal budgets; qualified outcome reported as completed-with-controls only; claims validated, 0 dangling evidence refs.
- evidence: derived/final_stats.json; claims_grounding.json validated
- next_action: orchestrator renders concept figure and final compile


### 2026-11-11 | step=paper | scope=paper (citation enrichment)
- summary: Wove 3 retrieved references into targeted paragraphs only: Chiang et al. (Arena platform; Intro, Data), Koh & Liang (influence-function motivation; Method, Related Work), Min et al. (vote rigging; Related Work, replaces 'Scope of bibliography' disclaimer). MT-Bench paper and Cook's-distance literature were not retrieved, so they stay uncited and are disclosed as gaps in Related Work and Extended limitations. Rejected citing unconsulted retrieved items (Copilot Arena, leaderboard-portfolio paper, thesis on Bayesian diagnostics) to keep bibliography at 28 <= 30.
- evidence: claims_grounding.json 28 claims validated; bib 28 cited keys; body ends page 9; 0 undefined citations

### 2026-11-11T08:31:56Z | step=paper | scope=paper (audit repair)
- summary: Fixed figure_manifest (figure_type paired_panel_bar -> bar; controls width 0.75). Audit repairs: normaliser sentence now says sports larger under both (about 6x/12x vs 10.5x/21.0x); qualified no longer read as certifying controls (gate criteria not recorded; controls reported as separate observations); evaluator-internal specifics (B1-B3 construction, thresholds, margin, abort/checksum, copy rescaling) removed or marked unverified; dev table limited to grounded totals/runtimes, sub-metrics flagged as quoted from search-stage log, configs 2/3 title-level only. Bib title glyph fixed for compile. Trimmed text to keep body at 9 pages.
- evidence: verifier dangling=0; 29 claims, all source ids resolve; citation keys validated

## Repair round 2b (2026-11-11)
- Audit fixes: B2 construction no longer asserted (recorded budgets only; construction unverified); dev per-case equality removed (aggregate 0.4993 = 0.4993 only); Broderick/vote-rigging descriptors cut to title level; runtime claim restated as studied-configuration 4.45/4.51 s, no hardware claim.
- Figure manifest: controls_permutation figure_type -> paired_panel_bar, width 0.9 (matches strategy). Soft figure warnings (font/PNG width) left unchanged; no figures regenerated.
- claims_grounding.json updated accordingly; paper recompiled, no undefined refs. Evidence refs untouched (no new tokens).
- 2026-11-11T08:38:48Z Repair round 3: removed unsupported 0.5 non-vacuity line from Figure 3b and caption (only recorded ratios and non-vacuous flag reported); deleted B3 hand-built clause; reworded abstract/intro B2 statement to recorded-budget equality only (no search-machinery attribution); manifest controls_permutation figure_type set to grouped_bar. Body ends p9; evidence verifier dangling=0; paper.tex and claims_grounding.json consistent with grounded inputs.

### 2026-11-11 | step=paper | scope=paper (audit repair round 4)
- summary: Fixed three audit findings: (1) replaced "equally fragile" with same-62-row upper bounds, minima not established, caps differ; (2) dropped certificate/exact-refit-by-evaluator wording (title now "Recorded Removal Budgets", "verified"->"recorded", evaluator verification stated as not inspectable, only candidate's own refit inspectable); Figure 1 caption marks evaluator box/loop as schematic of the metric as understood; figure axis labels "recorded"; (3) crowd mid pair gap closeness reworded as suggested-not-established (6/20 random flips). Added 2 claims. Figures regenerated (labels only).
- unresolved: figure_manifest controls_permutation figure_type: strategy says paired_panel_bar, which the manifest schema enum rejects; manifest keeps schema-valid grouped_bar. Strategy file not modified. Needs orchestrator/strategy fix.

## Repair pass (2026-11-11, post-audit)
- Removed unregistered development sub-scores (0.9987, 0.0, 0.5, 0.0695, 0.5007, 0.3153) and derived inferences (expert non-flip, three crowd rows) from paper.tex and claims_grounding.json; dev table now shows registered totals and runtimes only.
- Copy control reported as 0 flips in 2 trials with no inference. "verified" protocol/budget wording replaced by "evaluator-recorded"/"recorded".
- figure_manifest controls_permutation figure_type -> paired_panel_bar; figures re-exported (PNG 400 dpi, title 10 pt). Evidence verifier: dangling=0. Qualification handling unchanged (qualified, criteria unrecorded).

## Repair pass (2026-11-11, audit round 7)
- figure_manifest controls_permutation figure_type -> grouped_bar (schema-valid; paired_panel_bar had regressed).
- Hedged lambda=0.01 and top/mid pair rule as task-description reading, unverifiable against evaluator source; removed dataset commit/licence table (no artifact support); fixed warm-start description to match src/program.py; narrowed LLM-usage sentence.
- Recompiled (13 pages, no undefined refs); evidence verifier re-run.

## 2026-11-11 figure_type repair
- Hard validation error: manifest figure_type had to equal strategy figure_type for controls_permutation, but strategy used `paired_panel_bar`, which is not in the manifest schema enum (schema rejects it; strategy equality rejects grouped_bar). Unsatisfiable via manifest alone.
- Fix: changed paper_strategy.json figure_specs[controls_permutation].figure_type to `grouped_bar` (backup: paper_strategy.json.bak_pre_figtype_fix). Figure content unchanged (two-panel real-vs-permuted bars). Manifest and strategy types now identical for all 3 figures.
- Recompiled (13 pages, 0 undefined refs); evidence verifier rerun. No paper text or numbers changed. Qualification limitations unchanged.
