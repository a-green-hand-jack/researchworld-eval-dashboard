
## Reference query plan stage (2026-11-11)
- Wrote reference_query_plan.{md,json}: 10 queries tied to winner's-curse, adaptive analysis, post-selection inference, EB-IRT, prompt-search, MMLU-Pro. Rejected generic AutoML/benchmarking/process queries as off-target; no retrieval performed.

## Paper strategy stage (2026-11-11)
- Chose thesis-first estimator paper: EB-IRT selection-aware posterior interval; final outcome qualified; conditional claims; heterogeneity (halving, large N) foregrounded. No downstream_study; no edit mode. Rejected chronology of 3 variants and broad prompt-tuning-gap framing. References bib mostly irrelevant — flagged to writer.
### 2026-11-11T14:45:13.394107+00:00 | step=paper_draft | scope=paper
- summary: paper.tex, claims_grounding.json, figure_manifest.json written and consistent with grounded inputs. Decisions: thesis kept as EB-IRT selection-aware interval with conditional claims; replayed evaluator code to derive naive/Bonferroni/resampling coverage and width (exact reproduction of recorded interval scores and biases, max diff 0) because sealed evidence lacks baseline coverage; corrected strategy memo: kappa is hand-set (untuned prior), no kappa-off ablation; reported resampling ties EB-IRT under exhaustive search (0.1405 vs 0.1406) so aggregate win vs resampling comes from halving; pruned 18 irrelevant bib entries and added 20 identifier-verified references; rejected chronology and generalization framings; no ranking-reversal claim. Evidence verifier: 0 dangling.
- evidence: analysis/final_per_case.json, analysis/reconstructed_baselines.json, analysis/search_variants.json
- next_action: orchestrator renders overview_schematic then final compile and validation


### 2026-11-11 | step=postdraft_citation_weave | scope=paper
- Earlier retrieval added nothing; added 6 identifier/title-verified refs (arXiv API, Crossref, OpenAlex): Cawley2010Overfitting, Feldman2019MultipleClasses, Zhou2022APE, Yang2023OPRO, Bock1981MML, MartinezPlumed2019IRTinAI. Dropped 3 overview/extension refs (Ullman, Dwork2017, Marchant) to stay at the 30-ref cap. Rewrote only intro, related-work and EB-IRT model paragraphs; no numbers changed. Roelofs meta-analysis not added (id unverified). Compile clean, 0 dangling evidence, 30 refs.

## Repair round 1
- Fixed 3 audit findings: compute wording (wall-clock, dropped replay-time sentence), halving undercoverage restricted to real-outcome halving, N=60 optimism comparison weakened to "same order as spread"; claims_grounding updated.
- figure_manifest figure_type aligned to strategy (paired_dot_or_bar, line_or_bar). Evidence verifier rerun; paper recompiled (13 pages).

## Repair round 2
- Audit fixes: baseline coverage/width and resampling bias labelled replay-derived (protocol text, Table 1 caption, P2/P4 resampling bias text, claims 8/17); removed unrecorded package versions/runtime from SI; P4 coverage 0.89 described as slightly below nominal, within seed noise, only P6 0.83 called undercoverage (abstract, results, limitations, conclusion, claim 14).
- figure_manifest figure_type set to schema enum values (grouped_bar, line). Recompiled (13 pages), evidence verifier 0 dangling.

## Repair round 3 (2026-11-11)
- Hard error: manifest figure_type vs strategy mismatch for bias_and_coverage, width_vs_n. Strategy used `paired_dot_or_bar`/`line_or_bar`, which are not in the manifest schema enum, so manifest and strategy could not agree. Relabelled the two strategy specs to `grouped_bar`/`line` (the types actually plotted); manifest unchanged from schema-valid values. Backup: revisions/paper_strategy.before_figtype_fix.json. Paper text and claims untouched.
