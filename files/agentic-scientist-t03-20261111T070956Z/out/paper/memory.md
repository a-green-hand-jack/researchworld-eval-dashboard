
## Reference query plan (2026-11-11)
Chose 9 queries tied to Kernel SHAP estimator noise, within-run uncertainty/jackknife, empirical-Bayes shrinkage, top-k stability metrics, explanation instability, value-function choice, and dataset provenance. Rejected generic XAI/benchmarking/optimization queries, deep tabular architecture queries (not in run), chronology queries, and anything aimed at the prohibited prior paper.

## Paper strategy (2026-11-11)
Chose bounded "conditional reliability + single-run diagnostic vs baselines and permuted control" framing (final outcome qualified). Rejected: (a) search-progression story (3 scored attempts, no ablations, overlapping seed ranges); (b) broad empirical study of SHAP reliability across datasets/models (no grounded breakdown); (c) superiority-over-baseline-program story (no grounded baseline score). Key limitation kept front-and-center: permuted control scores 0.9701 vs 0.9838. Flag: references.bib mostly irrelevant, starter refs missing. Not edit mode. Status ready.
### 2026-11-11T08:25:12.240152+00:00 | step=paper | scope=paper
- summary: paper.tex drafted: bounded conditional-reliability framing (final outcome qualified; 8 body pages). Rebuilt references.bib to 26 grounded entries (OpenAlex/S2) incl. starter papers; dropped off-topic entries. Added derived-metric script, 2 matplotlib figures, concept figure wired as placeholder. Rewrote claims: explicit decomposition (61% of gain over always-reliable survives permutation), no per-dataset claims, no ablation attribution, search-plane scores labeled proxies. gate=kept; trigger=none; reason=no new experimental category
- evidence: paper_data.json final_evaluation.metrics; analysis/derived_metrics.json; source_evidence/*
- next_action: validate and finish


### 2026-11-11 | step=paper
- Rejected framings: search chronology (3 configurations, no ablations), broad multi-dataset empirical study (no per-cell evidence retained), superiority over baseline program (no grounded baseline score).
- Kept: conditional budget dependence of single-run top-3 agreement + single-run diagnostic vs 3 baselines and permuted control; qualification outcome "qualified" disclosed; limitations foregrounded (61% of gain survives permutation, no budget-only constant baseline, hand-set constants, 2 seeds, 3 datasets).
- Claim rewrites: "modestly beats control" kept as absolute 0.0137 plus relative 45.9% MSE; search label means not used (not in paper_data.json); prior-vs-final shift derived from source constants and final means.
- References: rebuilt to 26 entries via OpenAlex/Semantic Scholar; Petrosian entry dropped (title-only knowledge). pdftotext unavailable so compile_latex.sh could not run; compiled manually with pdflatex+bibtex (body 8 pages, last page full).
### 2026-11-11T08:25:16.797049+00:00 | step=paper | scope=paper
- summary: x
- evidence: y
- next_action: z


## Post-draft citation enrichment (2026-11-11)
- Retrieval pass had returned no new refs; retrieved 5 via OpenAlex: Visani2021Statistical, Slack2020Reliable (per-run/per-explanation stability and uncertainty comparators), Kott2001Using (delete-a-group jackknife), Efron1973Stein (shrinkage), Bhatt2020Explainable (deployment). Dropped uncited-by-need Grinsztajn2022tree (out-of-scope clause) to stay at 30 refs.
- Rewrote only: intro opening (deployment claim softened to "used to explain", practitioner-study cite), related-work Shapley paragraph (comparators + contrast), method jackknife/shrinkage rationale. No numbers changed.
- Validation: tex refs OK (30 keys), claims validated (28), evidence verifier dangling=0, pdflatex+bibtex compile OK (12 pp; body ends p.8, est. ~80% full). pdftotext absent so compile_latex.sh could not run.

## Repair round 1 (2026-11-11)
- Evidence audit fixes: removed "chiefly the budget" attribution (control does not apportion budget vs dataset/family calibration); qualified "held-out" datasets (German Credit final half is the complementary hash half of a search-plane split); abstract and Table tab:consts caption now state budget prior 0.84/0.96 came from search-plane aggregate label means.
- figure_manifest.json: main_comparison figure_type set to two_panel_bar to match strategy. Soft font/PNG-width warnings left as is (PDF used in LaTeX).
- Evidence verifier: dangling=0. pdflatex compile OK (13 pages total); canonical validator/pdftotext unavailable locally, parent revalidates.
### 2026-11-11T08:48:27.173845+00:00 | step=repair_round_3 | scope=paper
- summary: Audit fixes: prior constants 0.84/0.96 reworded as hand-set, origin per notes only and not retained in evidence (abstract, method, Table 4); protocol/constant claims re-anchored to source_evidence files+lines, not sealed metrics; main_comparison figure_type -> composite so manifest validates. Verifier dangling=0, claims validate, paper compiles (13 pages). paper.tex and claims_grounding.json consistent with grounded inputs.
- evidence: paper_evidence_audit_feedback.json; source_evidence/selected_config_NOTES.md; claims_grounding.json; scientific-evidence/verification-report.json
- next_action: done


## paper repair_round_3 (2026-11-11)
- Audit fixes: prior constants 0.84/0.96 reworded as hand-set, origin per configuration notes only and not retained in evidence (abstract, method, Table 4 caption/row, statistical-limits paragraph).
- Protocol/constant claims in claims_grounding.json re-anchored to source_evidence files and lines (not sealed metrics); source ids now result.improvement_003 / final.evidence.episodes only as provenance pointers.
- figure_manifest main_comparison figure_type two_panel_bar -> composite (schema fix).
- Verifier dangling=0; claims validate (30 claims); pdflatex+bibtex compile OK, 13 pages.
- Not done: global_memory/ is a dangling symlink (../investigation missing), so global memory files were not appended; validate_figures.py and compile_latex.sh could not run here (no src package / pdftotext).
- paper.tex and claims_grounding.json consistent with grounded inputs.

## Repair round 4 (2026-11-11)
- Validation hard error: main_comparison figure_type mismatch. Root cause: strategy used `two_panel_bar`, not in manifest schema enum (figure_manifest_schema.py), so manifest `composite` could never match. Changed paper_strategy.json main_comparison figure_type to `composite` (same figure, no content change); manifest already `composite`.
- tex refs OK (30 keys), evidence verifier dangling=0, pdflatex+bibtex compile OK (13 pp). Canonical validate_figures.py could not run (pydantic missing).
