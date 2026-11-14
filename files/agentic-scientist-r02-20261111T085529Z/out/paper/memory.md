
## Reference planning (2026-11-11)
- Wrote reference_query_plan.{md,json}: 10 queries over LAC/APS/RAPS, Mondrian, weighted conformal + density-ratio, conditional-coverage limits and QR thresholds, evaluation metrics, Aitchison compositional context. Chosen over generic 'conformal prediction benchmark' queries because they map to the run's variants and results; no CIFAR query since no real data used.

## Paper framing (2026-11-11)
- Chose thesis-first standalone framing: protocol-centred empirical study of gated weighted-Mondrian conformal on synthetic softmax families; final outcome qualified (score 0.8416 vs best baseline 0.8029, margin 0.0387, CI [0.0274,0.0499]); residual shift gap 0.0536 and worst-slice gap 0.0675 reported as limitations.
- Rejected: (a) search-chronology narrative (violates standalone/no-progression rules), (b) claiming a compositional-geometry (Aitchison) method (procedure uses summary features, no evidence), (c) real-data/CIFAR claims (no results exist). Variant 3 == variant 2 in all retained metrics; cause left unknown.
- Unknown/unsupported: per-baseline scores, per-case results, cause of search-to-final drop. Diagnostics trust 'unverified'.

## Paper draft (2026-11-11)
- Wrote paper.tex (ICLR, anonymous), claims_grounding.json (21 claims), figure_manifest.json (4 figures: protocol_overview [orchestrator-owned placeholder], final_comparison, variant_profile, loss_decomposition). Scripts: scripts/build_figures.py (guarded placeholder), scripts/derive_stats.py -> derived/derived_stats.json. Source files copied to ./source_evidence/ (evaluator, V1-V3 sources + metrics) because the results symlink is not traversable by the evidence verifier.
- Added derived analyses (all from retained numbers): loss decomposition (marginal term 0.0893 by subtraction, flagged as implied), full-set score 0.75 (analytic), paired dev differences, margin-theory constants f(0)=0.399, f(0.7)=0.143 (heuristic, flagged unchecked).
- Rejected/qualified claims: exact no-op under exchangeability softened to "intended; not guaranteed; activation not logged"; shrinkage breaks exact Mondrian guarantee (stated); V3==V2 cause left unknown (source falls back verbatim, activation not recorded); no per-baseline / per-case / real-data claims; Aitchison/Vovk/Tibshirani/Angelopoulos refs not in references.bib so not cited (stated in SI).
- Related-work descriptions limited to titles/venues (provenance has no abstracts); all 25 bib keys cited.
- Page budget: body = 9 pages, last page ~85% full with placeholder concept figure; real figure may shift layout.
- Verification: scientific-evidence verify dangling=0; validate_claims passes; validate_tex_refs passes; compile via pdflatex/bibtex (compile_latex.sh needs pdftotext, unavailable).

## 2026-11-11T10:08:56Z citation enrichment
- Added 7 grounded refs (OpenAlex, DOI-verified): Vovk2005, Lei2018, Sadinle2019, Romano2020, Angelopoulos2020 (arXiv), Tibshirani2019, Aitchison1982. Dropped 2 low-value entries (Rueda2007 proceedings front matter, Löfström2022 KNIME tutorial) to stay at 30 refs.
- Edited only Related Work (new Foundations and Distribution-shift paragraphs), Method baselines/background/weighted paragraphs, SI reproducibility note. Baseline implementation details stay attributed to the evaluator source, not to cited papers.
- Moved evidence-inventory table to SI to keep body at 9 pages (ends ~75% of page 9). claims_grounding.json updated (25 claims); evidence verifier dangling=0.
- 2026-11-11T10:21:23Z  repair round 1: fixed 4 evidence-audit findings (control count unretained, selection-bias wording, trade-off citation overreach, vacuous-control description) and figure manifest min_font_size_pt; body 9 pages; dangling=0.

## Repair round 3 (validation feedback)
- Fixed audit finding c3-control-rule-1: C3 now described as one-sided (coverage >= target - tolerance, mean size >= (1-alpha)K-1; over-coverage not penalised), per source_evidence/evaluator/evaluate.py control_verdicts.
- Fixed figure_manifest.json figure_type for final_comparison (dot_plot_with_interval) and variant_profile (small_multiples_dot_plot) to match paper_strategy.json.
- Recompiled paper.pdf (14 pp, no undefined refs); evidence verifier report unchanged (dangling=0). Soft figure-size warnings left as is.

## Repair pass (final)
- Fixed figure_manifest figure_type for final_comparison and variant_profile ("composite"; schema enum).
- Audit fixes: Intro "close to nominal" -> one-sided under-coverage gap 0.0017; Method/Limitations/Conclusion qualify frozen-config identity (V2 vs tied V3, manifest not retained), drop "evaluated once"; loss decomposition marginal term described as implied by subtraction.
- Recompiled (15 pages), citation keys valid, evidence verify run.

- [2026-11-11T10:28:48Z] paper/repair_round_4: repair round 4: only hard error was figure_type mismatch (strategy used unsupported types dot_plot_with_interval / small_multiples_dot_plot, not in manifest schema enum or aliases). Set both strategy figure_type values to 'composite' (multi-panel) to match manifest rows; paper.tex and claims_grounding.json unchanged; validate_figures passes, soft warnings (PNG width/font) left as-is since LaTeX uses vector PDFs.
- repair_round_5: audit findings fixed (slice-axis, H2, impossibility); body trimmed to 9 pages; evidence dangling=0.
