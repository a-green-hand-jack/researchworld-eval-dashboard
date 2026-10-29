
### 2026-10-27 | step=reference_query_plan
- decision: 9 queries (AKLLR 2m(n-1), Feige upper/lower, Lovasz survey, Matthews, resistance/commute-cover, extremal hitting time lollipop, random regular/ER cover time, ridge regression).
- why: each ties to a comparator or family in the run (bound 1.754 vs ridge 0.181 macro log MAE); generic ML/benchmarking/chronology queries rejected as unsupported.
- caveat: resistance-feature idea unscored; per-family results absent, so family-failure queries are hypothesis-driven.

### 2026-10-27 | step=paper_strategy
- decision: standalone measurement paper on the frozen baseline (five-stat ridge) vs 2m(n-1) bound and controls: macro log MAE 0.181 vs 1.754 / 0.870 / 1.423; MC rel SE 0.029; qualified/completed.
- why chosen over Matthews/resistance story (unscored, no evidence) and over a family-failure story (no per-family metrics). No improvement-over-baseline claim since selection = baseline.
- risks: thin evidence for 8-9 page body; family-dependence unanswered; candidate diagnostics unverified; zero episode spread.

### 2026-10-27 | step=paper_draft
- decision: wrote standalone measurement paper (paper.tex) around frozen five-statistic ridge predictor vs 2m(n-1) bound / constant / shuffled-target control (0.181 / 1.754 / 0.870 / 1.423 macro log MAE; MC median rel SE 0.029; qualified/completed). Added analytic closed-form overshoot figure (path/cycle/star/complete; verified vs exact DP at n=7), noise-floor and worst-case-concentration arithmetic, claim-status table.
- rejected/rewritten: per-family failure claims (no per-family data) -> stated unknown; Matthews variant (unscored) -> future work only; search vs final scores kept separate (SI only); episode identity framed as determinism, not uncertainty.
- evidence: scientific-evidence verify dangling=0; validate_claims OK (17 claims); analytic-math claims are backed by closed_form_gap.json via @evidence refs, not by paper_data sources.
- caveat: pdftotext/poppler and src.orchestrator absent in workspace, so compile_latex.sh and validate_figures.py could not run; compiled with pdflatex+bibtex (body 8 pages, refs p9, SI pp10-11). Overview figure is a placeholder pending orchestrator render.
### 2026-10-27T17:50:32.763399+00:00 | step=citation_enrichment | scope=paper
- summary: Retrieved Aleliunas 1979, Lovasz survey, Doyle-Snell via S2; cited in intro, worst-case bounds, discussion, conclusion. Chandra, Matthews, Hoerl-Kennard not retrievable: removed Matthews-type attribution in discussion, ridge left uncited. 11 pages compile, no undefined citations.
- evidence: references_provenance.json; validate_claims.py 19 claims; verification-report dangling=0
- next_action: none; final validation by orchestrator

### 2026-10-27T17:50:35.757854+00:00 | step=citation_enrichment | scope=paper
- summary: Retrieved Aleliunas 1979, Lovasz survey, Doyle-Snell via S2; cited in intro, worst-case bounds, discussion, conclusion. Chandra, Matthews, Hoerl-Kennard not retrievable: removed Matthews-type attribution in discussion, ridge left uncited. 11 pages compile, no undefined citations.
- evidence: references_provenance.json; validate_claims.py 19 claims; verification-report dangling=0
- next_action: none; final validation by orchestrator


## Repair round 1 (2026-10-27)
- Overview figure: concept renderer failed (auth), placeholder flagged by audit. Replaced with native matplotlib diagram (scripts/build_overview.py -> figures/overview_pipeline.pdf/png); manifest marks generator=matplotlib, attempted_generator=generate-concept-figure, fallback_reason set.
- Manifest converted to the rich-schema shape (min_font_size_pt added); validates against figure_manifest.schema.json.
- SI: dropped ungrounded "with a ridge residual" for the unscored Matthews-style alternative.
- Discussion: removed assertion that label noise is non-negligible on slowest families; stated as unmeasured (per-graph SEs not retained). Intro threat sentence aligned with median-SE evidence.
- Evidence verifier: 50 refs, 0 dangling. Paper compiles (11 pages incl. refs/SI).

## repair_round_2 (2026-10-27)
- Intro: dropped "only ... bottlenecked graphs" claim; now "tight up to a constant factor on some graphs such as paths and cycles" (consistent with closed_form_gap.json cycle overshoot ln 4). Added analytic claim to claims_grounding.json.
- Limitations: replaced "clip would hide very large failures" with statement that clip at 10 cannot have been binding (macro 0.181 bounds any graph error at ~4.35); per-graph/per-family errors still unknown.
- figure_manifest.json: closed_form_gap source_ids set to [final.metric.bound_macro_log_mae].
- Recompiled (11 pages, no errors); tex-ref validation ok; evidence verifier dangling=0.
