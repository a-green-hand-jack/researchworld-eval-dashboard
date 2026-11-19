
### 2026-11-11 | step=reference_plan
- Wrote reference_query_plan.{md,json}: 10 queries on regression GATE, exposure-mapping misspecification, HT/Hajek, cluster randomization, DiM, AIPW-style correction, staggered rollout, extrapolation/positivity, Facebook100. Rejected generic process queries and GCN/spectral queries (no GNN in run). Avoids excluded paper.

### 2026-11-11 | step=paper_strategy
- Wrote paper_strategy.{md,json} (status ready, paper_standalone, ICLR). Framing: thesis-first characterization of regression-GATE accuracy governed by exposure-mapping fidelity; final eval qualified (0.126 rel RMSE vs linear 0.180, DiM 0.622, HT 0.994, oracle 0.045; coverage 0.839 vs 0.95). Beat "new estimator wins" (3 variants, shared case specs between search/final, no ablation, no per-case baselines) and chronology framings. Disclosed: two-hop case unresolved, cause unknown; no downstream_study.

### 2026-11-11 | step=paper
- Wrote paper.tex (ICLR, anonymous), claims_grounding.json (18 claims), figure_manifest.json (4 figures; overview_schematic placeholder awaiting orchestrator render), build_figures.py (Figs 2-4 + derived_stats.json), search_plane_metrics/ (copies of three metrics.json files, needed because evidence verifier does not follow the results symlink).
- Framing: thesis-first characterization (exposure-mapping fidelity governs error); rejected estimator-wins and chronology framings. Final outcome qualified; disclosed shared case specs, no gate ablation, two-hop cause unknown, undercoverage 0.839 cause unestablished.
- References: replaced noisy bib with 28 topical entries (11 retained from original retrieval, 17 added via OpenAlex, provenance merged); irrelevant medical/climate entries dropped. Cited only by title/topic where papers were not read.
- Claim fixes: per-seed score is mean relative error (0.102), distinct from RMSE aggregate (0.126); case 8 search value 0.445 attributed only to linear+correction and library (ensemble 0.428).
- Verification: validate_claims OK; scientific-evidence 0 dangling; compile via pdflatex OK (body 9 pages, last page ~75% with placeholder overview); pdftotext absent so full compile script/validators could not run locally.

## Citation enrichment pass (2026-11-11)
- Added Savje2023Misspecified, Savje2021Unknown, Eckles2016Design, Li2022RandomGraph (OpenAlex-verified records); dropped peripheral Kipf2016GCN and Tiwari2024Quasi to stay at 30 refs.
- Rewrote only: intro paragraph 1 (DiM bias cite), thesis paragraph (misspecified/unknown interference), new related-work paragraph, reliability coverage sentence, limitations cite removal. Cited works described by title/topic only; no new quantitative claims.
- Trimmed several sentences to keep body at 9 pages. claims_grounding.json citation keys/sources updated.

## Repair pass (audit + manifest)
- Copied estimator/evaluator source into ./source_evidence/ and verified implementation details against it; fixed winsorising scope (count mapping only) and two-hop feature wording (walks end at treated node, include returns).
- Found library contains exact case-6 sigmoid -> removed "mapping fidelity governs accuracy" from title/abstract/conclusion; now a hypothesis (selected mappings unverified).
- Dropped per-case search-plane numbers, plane-consistency figure and bias/coverage for search plane (no registered source ids); Table 2 now plane means only (result.improvement_00x).
- Permuted-graph control: report numbers only, no mechanism.
- figure_manifest.json rewritten to schema (list-valued fields, composite type); plane_consistency removed.
- Body ends on page 9 (~95% full); evidence verifier 0 dangling; claims validated.

## Repair round 2 (audit fixes)
- Rewrote HT discussion: HT 0.994 reported without variance attribution; cause undiagnosed (audit: ht-variance-model-risk-overclaim). Removed "included to show variability".
- Reduced Chin/Han/Aronow related-work descriptions to title-level; removed linear-model, covariate-selection, block-bootstrap, cluster-robust attributions (audit: related-work-beyond-title-grounding).
- Removed attribution of seed-mean vs RMSE gap to case 8; constant-outcome control described as ~9e-15 (numerically zero), no "rules out" claim; fallback says exactly-zero variance returns 0 (audit: seed-gap-and-control-overinterpretation).
- Manifest figure_type aligned with strategy (bar_two_panel, strip_plus_bar); figures regenerated at 500 dpi (>=2400 px); reliability legend moved; titles 10pt.
- Trimmed prose to keep body at 9 pages; dropped Wager/Ting sentence. Verifier: 0 dangling.
- Repair round 3: schema validation rejected figure_type 'bar_two_panel'/'strip_plus_bar' and extra field 'category_budget_note'. Set both matplotlib figures to figure_type 'composite' (schema enum), removed the extra field. paper.tex, claims_grounding.json, figures unchanged; final outcome 'qualified' wording in paper matches final.qualification.outcome.

## Repair round 4 (figure_type conflict)
- Root cause: validator requires manifest figure_type == strategy figure_type, but strategy values 'bar_two_panel'/'strip_plus_bar' are not in the manifest schema enum, so rounds 2 and 3 each failed one check. Resolution: set figure_specs[main_accuracy|reliability].figure_type to schema-legal 'composite' in paper_strategy.json (backup: revisions/paper_strategy_before_figtype_fix.json); manifest already 'composite'. Concept-figure spec untouched.
- validate_figures: pass (3 figures). validate_tex_refs: pass (28 keys). scientific-evidence verify: 71 refs, 0 dangling. paper.tex/claims_grounding.json unchanged; pdflatex recompile not possible here (pdftotext missing), existing paper.pdf from last good build.
- Final outcome remains 'qualified' per final.qualification.*; audit verdict pass (0 findings).

## 2026-11-11T09:02:54Z repair_round_5
Repair round 5: addressed 2 audit findings. (1) Reworded gain-attribution in Threats to validity to a hedged untested possibility, retaining no-ablation/no-per-case-gate-logging statement. (2) Replaced 'inspecting model-selection results'/'seeing per-case errors' with 'developed after the two earlier estimator classes had been scored on the model-selection seeds' in Method and Limitations (1). Numbers, claims_grounding and citations unchanged; evidence verifier dangling=0; body 9 pages; refs 28 keys valid.

## 2026-11-11 repair_round_6
Fixed hard error (body 10 pages > 9): trimmed four sentences in Discussion/Conclusion (no numbers or claims changed; removed an unneeded researcher-degree-of-freedom sentence, a relative-error remark, and next-step items). Recompiled: body 9 pages, references start page 10; 28 citation keys valid. Citation-enrichment gaps (exposure-mapping misspecification, DiM bias, interval variance) were already woven in with Savje2023/2021, Eckles2016, Li2022, Han2023. Figure/claims validators unavailable in this workspace (missing src module); parent should revalidate.
