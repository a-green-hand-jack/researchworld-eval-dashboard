
## Reference planning (2026-10-28)
- Wrote reference_query_plan.{md,json}: 9 queries. Grounding: task contract, starter program, paper_data.json (completed_no_winner, baseline 0.914 kept). Chose BT / influence / drop-k robustness / poisoning / Arena / MT-Bench / NBA / ranking-uncertainty queries over generic optimization or benchmarking ones. Avoided queries about the excluded paper.
- 2026-10-28T21:33:03Z | step=paper_strategy | Framing: cross-design measurement/limitations paper on verified first-order influence rank-1 displacement (crowd 1.000, sports 0.833, expert 0.374, LLM-judge 0.216; mean 0.606; qualified). Rejected method-improvement (0/3 variants scored) and noise-vs-intent (no experiments). Status ready; figures: overview concept + 2-panel bar; supplement planned.

## Paper writing (2026-10-28)
- Framing: measurement/limitations paper on verified first-order influence rank-1 displacement across crowd, expert-human, LLM-judge and sports designs (final.metric.*: 0.606 family-averaged; crowd 1.000, sports 0.833, expert 0.374, LLM judge 0.216). Final outcome qualified/completed (final.qualification.*). Rejected: method-improvement (0/3 variants scored) and noise-vs-intent framing (no experiments).
- Grounding decisions: protocol facts (budget ladder, case set, reference policies, control) cited to copies of evaluator code/contract in source_evidence/task/; implementation facts to source_evidence/downstream/program/src/program.py. No per-case, row-count or per-design baseline numbers used. Search score 0.914 kept in appendix as separate scope.
- Rewrote claim: random/constant aggregate-only inference hedged; dropped speculation about tie rates; derived flip-vs-drop identity (math, labelled not empirical).
- References: removed 4 off-topic entries, added 7 starter-literature entries (Bradley1952, Chiang2024, Zheng2023, Koh2017, Broderick2020, Min2025, Singh2025) with provenance ids ref.starter.*; deliberately did not cite or seek the excluded paper. 28 refs, all cited.
- Figures: design_scores (matplotlib, PDF+PNG, scripts/build_figures.py); overview_protocol is an orchestrator-owned placeholder (guarded by .concept_figure_complete).
- Validation: validate_claims passed (0 dangling evidence refs); validate_tex_refs passed; local pdflatex build: 8 body pages (last page ~full), refs p9-10, appendix p11-12. pdftotext missing locally so compile_latex.sh could not run; orchestrator must run the official compile.

## Citation enrichment pass (2026-10-28)
- Post-draft retrieval (Semantic Scholar rate-limited, OpenAlex fallback) added no refs to references.bib; I merged 5 OpenAlex hits whose abstracts I read: Yang2026Preference (label-flip preference poisoning), Seetharaman2021Influence (data poisoning definition), Giordano2018Swiss (infinitesimal jackknife finite-sample error bounds), Szczecinski2020GElo and Holy2026ScoreDriven (Elo-style sports rating). Dropped 3 over-supported BT refs (Davidson1969, Causeur2005, Yan2011) to stay at the 30-ref cap.
- Rewrote only Related Work (new poisoning paragraph, Elo sentence, IJ sentence), additivity caveat (i), and one sentence in Evaluation designs. No numbers changed. Rejected claim: any home-advantage citation (no retrieved source supports it); stated BT fit has no home term.
- Validation: validate_claims (14 claims, 30 refs), validate_tex_refs, evidence verifier pass; pdflatex: 9 body pages, conclusion on p9.

## Repair pass (audit + figure manifest)
- Removed ungrounded design size / "six models" claims (Table 1, competitors bullet); reworded permuted-control claim to the single control run per case; limited Yang2026Preference/Seetharaman2021Influence descriptions to title-supported content; softened Giordano/Holy/Szczecinski descriptions.
- Concept-figure render failed (rc=1): shipped documented matplotlib fallback (scripts/build_overview.py, PDF+PNG), manifest uses list-valued categories/series_per_panel and generator=matplotlib, attempted_generator=generate-concept-figure.
- validate_claims passes (14 claims, 30 refs); manifest validates against schema; paper compiles (13 pages incl. refs/SI).

## Repair pass (audit round 3)
- Fixed 2 audit findings: (1) L-BFGS cross-check now described as a single check on <=600 rows of the smallest case, not per edited refit/unedited case (Method, SI A); (2) evaluator influence baseline described as using the same first-order formulas with equal family-averaged score (0.606, margin 0.0), dropping "numerically identical/same computation" claims and disclosing the non-negative-effect filter and fitter difference; row-level edit-set identity not shown.
- validate_claims passes; evidence verifier rerun; paper recompiles (13 pages). Soft figure-font warnings left as-is.

## Repair pass (audit round 4)
- Fixed 2 audit findings: (1) win-rate heuristic described as selecting rows by incumbent's wins vs runner-up (dropped "needs no model refit"); (2) MT-Bench expert-human/GPT-4 now "both derived from the same dataset release", overlap of rows/questions/models stated as not verified; removed "cleanest contrast" and "same questions" in intro, Table 1, subsection heading, analysis, limitations.
- validate_claims (14 claims, 30 refs), validate_tex_refs, evidence verifier (0 dangling) pass; paper recompiles (13 pages). No numbers changed. Soft figure-font warnings left as-is.

## Repair pass (audit round 5)
- Restricted related-work descriptions of Min2025, Singh2025, Broderick2020, Giordano2018 and 18 BT background refs to title-only attributions; disclosed title-only knowledge.
- Disclosed declared-synthetic planted near-tie family (weight 0.2) in search-scope score (protocol + appendix).
- LLM usage: variants "proposed", not "wrote their code".
- claims_grounding.json updated (claim 11 grounded on ref.s2.* ids). validators pass; 0 dangling evidence refs.
