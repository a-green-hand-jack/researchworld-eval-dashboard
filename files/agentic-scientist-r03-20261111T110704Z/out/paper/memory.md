
## Reference query plan (2026-11-11)
- Wrote reference_query_plan.{md,json}: 10 method- and result-grounded queries (Gaussian/EM imputation, greedy cond-variance selection, NNLS stacking, matrix completion, IRT, observational scaling laws, A-optimal design, benchmark agreement, MTEB). Rejected generic benchmarking/optimization queries and chronology queries. No retrieval run.
### 2026-11-11 | step=paper_strategy | scope=paper
- framing: thesis-first calibrated empirical paper on cold-start benchmark selection+imputation; final outcome qualified; key numbers skill 0.434, nRMSE 0.562, vs random-k 0.016, vs greedy ridge 0.099, MTEB k-curve 0.787->0.638.
- why chosen: strongest grounded story; rejected search-chronology narrative and "beats baselines" headline (selector/imputer scored jointly, 0.016 margin, no ablation/theory numbers, no downstream_study).
- status ready; no failure.
### 2026-11-11 | step=paper_draft | scope=paper
- references: bib rebuilt to 27 real OpenAlex-retrieved entries (starter literature + methodology classics); dropped 4 earlier retrieved entries (SubLIME, SimBA, From Benchmarks to Skills, Mapping Overlaps) because their content was never read and two sit very close to the task (risk of citing the excluded paper); dropped irrelevant retrieval noise.
- narrative: thesis-first calibrated paper; rejected search-chronology and "beats baselines" headline. Claims narrowed: 0.016 skill over random-k not attributed to selector; greedy-ridge vs random-k inference marked as indicative (mean of ratios); no CI, no ablation, no theory check.
- evidence: copied evaluator source, manifests, config sources into ./source_evidence; derived analysis/protocol_facts.json and analysis/search_metrics.json (scripts/). Search nRMSE/skill/gap values not in paper_data.json -> evidenced via analysis file only, kept out of claim ids.
- figures: main_results (matplotlib, 6.2in wide, fonts>=7.5pt); protocol_overview placeholder for orchestrator (script guarded by .concept_figure_complete).
- validation: validate_claims OK (17 claims), tex refs OK, evidence verifier 0 dangling; pdflatex body 8 pages (last page ~full). validate_figures/pdftotext unavailable in this workspace -> parent orchestrator to run.

## Citation enrichment pass (2026-11-11)
- Targets: related-work comparators, intro redundancy premise, Open LLM Leaderboard component benchmarks. Retrieval via OpenAlex (scripts/add_refs3.py); Semantic Scholar run had aborted.
- Added: Hofmann2025Fluid (adaptive IRT item selection), IFEval, BBH, MATH, GPQA, MuSR, MMLU-Pro. Dropped peripheral BigCodeBench, MT-Bench, Vania2021, Krause2007 to stay at the 30-ref cap.
- Redundancy premise now cited to already-held BenchBench, observational scaling, Sloth (no new refs). Candidate papers on the same task (e.g. low-rank benchmark factor work from 2026) deliberately not cited: unread, and possible overlap with the excluded published paper.
- Related work now states that latent-factor/matrix-completion predictors were not run as baselines (consistent with limitations). No numeric claims changed. Validation: tex refs OK (30 keys), claims OK (18), evidence dangling=0, pdflatex compiles, body 9 pages.

## Repair pass (2026-11-11T13:05Z)
- Fixed figure_manifest.json to the rich schema shape (both figures; protocol_overview kept as generate-concept-figure with prompt log).
- Audit fixes: sealed configuration identity qualified (proposed pair OR latent-skill extension, indistinguishable; tree hash unmatched); removed "frozen"/"evaluated once"; abstract/conclusion refer to the selector-imputer family; SI hyperparameter table labelled as proposed-pair source copy, not verified as sealed tree; H3 reported as not tested by sealed evaluation (0.016 small/unresolved).
- claims_grounding.json claims 4 and 7 updated; evidence verifier: 0 dangling. Compiled (13 pages, body ends p.9).
- Citation gaps for benchmark-level comparators and redundancy were not filled: retrieval hit HTTP 429 and no grounded references were retrieved; Related Work already states latent-factor predictors were not run as baselines. No references invented.

## Repair pass 3 (2026-11-11)
- Audit finding si-licence-unsupported-1: removed licence assertions (CC0-1.0 etc.) from SI; now states data come from pinned public upstream sources in Table tab:data and licence terms were not verified.
- Figure manifest: added min_font_size_pt to protocol_overview (rich schema requires font_sizes or min_font_size_pt); strategy main_results figure_type changed from non-schema "multi_panel_line_and_bar" to "composite" (backup outside workspace) because the manifest enum cannot express the former.
- Citation gaps (benchmark-level comparators): still unfilled; retrieval hit 429 and bibliography is at the 30-ref cap. No refs invented.
- Validators: figures, tex refs, claims pass; evidence verifier re-run; paper.pdf recompiled (13 pages).

## Repair pass (2026-11-11, final)
- Hard error in validation_feedback was a docker compile-launch failure (environment), not a LaTeX error; local pdflatex+bibtex compile cleanly (0 undefined citations, 13 pages incl. refs+SI).
- Soft figure warnings addressed: main_results regenerated at 7.2x3.1in, fonts 10/9/8/8, PNG 2880x1240 (scripts/build_figures.py); manifest font_sizes updated. No numbers or claims changed.

## Repair pass 5 (2026-11-11)
- validation_feedback hard error is the docker launch failure (environmental). Local pdflatex+bibtex+2x pdflatex: 13 pages, 0 undefined citations/refs. Evidence verifier: total=52 dangling=0. Only "program" in visible text is the literal path src/program.py. No content changes.

## Repair pass 6 (2026-11-11)
- Fixed 4 audit wording overclaims: permuted-control sentence now states only the 0.678 nRMSE gap; "unavoidable residual" -> residual for the evaluated pair, no lower bound claim; greedy-vs-random statements reworded as indicative only (Results, Conclusion); Related Work/Intro quantitative details on metabench/BenchBench removed; redundancy premise softened. claims_grounding.json wording aligned. Local compile: 13 pages, 0 undefined; evidence verifier re-run.

## Repair pass 7 (2026-11-11)
- Fixed 4 audit findings: BenchBench/redundancy statements hedged (abstract, related work); missingness reworded as untested concern, metric-type list corrected, "well-covered" removed; sealed-tree identity stated as not established (abstract, method, SI, conclusion, claim 7); wall-clock guards and cost sentence qualified as properties of the proposed-pair source copy with accurate guard behaviour. Compile: 13 pages, 0 undefined. Comparator citation gap still unfilled (refs at cap 30, retrieval 429).

## Repair pass 8 (2026-11-11)
- Real LaTeX hard error found: unescaped `&` in GPQA title in references.bib (line 208) -> "Misplaced alignment tab" in .bbl (earlier "clean compile" claims predated the 30-ref bib). Fixed to `Q\&A`; fresh pdflatex+bibtex+2x pdflatex: 13 pages, 0 undefined, 0 errors. tex-refs validator passes (30 keys, none unused/missing); evidence verifier re-run.
- Comparator-literature gap still unfilled (bib at 30-ref cap; earlier retrieval 429); not forced, to avoid ungrounded refs and unvetted search on the task topic. No paper text or numbers changed.

## Repair pass 9 (2026-11-11T13:21:36Z)
- Hard error cause: stale/zeroed paper.bbl (old unescaped & entry); references.bib already fixed. Deleted bbl, rebuilt pdflatex+bibtex+2x pdflatex: 13 pages, 0 errors, 0 undefined. Citation keys/claims sources re-checked; evidence dangling=0. No text or number changes. Comparator-literature gap (cap 30 refs, retrieval 429) remains unfilled; not forced with unvetted refs.
