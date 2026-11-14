
## Reference query plan (planning stage)
- Wrote reference_query_plan.{md,json}: 9 queries covering grokking origin, mechanistic modular-addition transformer, circuit efficiency, lazy-to-rich, Omnigrok, grokking/double descent, muP, effective LR/AdamW, memorization capacity.
- Rejected generic queries (optimization, benchmarking, scaling laws of LLMs) and direct 'model size grokking delay' queries (risk of excluded prior paper). Final grounded result: width slope CI spans zero, 40% censored.

## Paper strategy stage
- Chose measurement-resolution / inconclusive-result framing: final outcome qualified (valid run), slope -0.020, CI [-0.585, 0.354] straddles 0 -> inconclusive; 40% censored; reference slope -0.368 (1 seed). Rejected capacity-crossover, effective-LR confound and best-search-score framings: no executed evidence (sweep scripts never run; search scores from different plane, 2 seeds).
- Wrote paper_strategy.{md,json}; status ready.
### 2026-11-11T14:25:59.948757+00:00 | step=paper | scope=paper
- summary: Wrote paper.tex (inconclusive width-slope framing), claims_grounding.json (28 claims), figure_manifest.json; corrected strategy bound: exact OLS max |slope| = 0.3*ln40 = 1.107 (not ln40/4 = 0.922, which is the log-linear profile); added 7 starter-literature refs to bib+provenance (task-supplied); only 14 refs cited since remaining retrieved entries are off-topic (min 25 not met, deliberately).
- evidence: derived/resolution.json; scientific-evidence verify: 0 dangling; validate_claims OK; pdflatex compiles; pdftotext unavailable so compile_latex.sh could not run
- next_action: orchestrator renders protocol_overview concept figure, then final validation


### 2026-11-11T14:26:05+00:00 | step=paper
- summary: Wrote paper.tex (inconclusive width-slope framing), claims_grounding.json (28 claims), figure_manifest.json. Corrected strategy bound: exact OLS max |slope| = 0.3*ln40 = 1.107 (ln40/4 = 0.922 is only the log-linear profile). Added 7 task-supplied starter refs to bib+provenance; cited 14 refs, remaining retrieved entries are off-topic so the 25-ref minimum is deliberately unmet. Dev-plane results kept in supplement only. gate=kept; trigger=none; reason=no new cross-cycle conclusion.
- evidence: derived/resolution.json; scientific-evidence verify 0 dangling; validate_claims OK (28 claims); pdflatex compiles (13 pp, body ~8.5 pp); pdftotext absent so compile_latex.sh not runnable; concept figure protocol_overview left as placeholder for orchestrator
- next_action: orchestrator renders protocol_overview; rerun validation

### 2026-11-11 | step=paper | scope=citation_enrichment
- summary: Targeted post-draft citation pass. Added via s2_fetch (one query each, since the batch run exhausted its cap on off-topic hits): Yang2021TensorPI, Yang2022TensorPV (muP / transfer), Doshi2023ToGO, Thilak2022TheSM, Prieto2025GrokkingAT (prior grokking empirics), Cameron2008/Cameron2015 (few-cluster bootstrap), Cox1972 (censored regression). Edited only Related Work (2 paragraphs), Method (bootstrap caveat) and Discussion item (ii). Wording hedged: muP resemblance is "in spirit", no claim that the multipliers implement muP; no claim of nominal bootstrap coverage; novelty claim phrased as non-exhaustive. Tobit/AFT not retrieved; Cox cited only as survival-analysis example. No quantitative content changed.
- evidence: validate_tex_refs OK (22 keys); validate_claims OK (32 claims); pdflatex 14 pp, conclusion on p.9, references from p.10; 25-ref minimum still unmet (22 cited keys in text) - no further relevant retrievable refs.

## Repair pass (audit + figure manifest)
- Fixed false V3 span claim (now: spans V2 mean, just above V1 mean; spreads vs mean differences), qualified V2 censoring statement (cause of censoring unknown from retained records), removed uninspectable claims (sweep script exists; sealed eval run once). Updated claims_grounding.json accordingly.
- figure_manifest.json figure_type aligned to strategy (interval_plot, dot_plot). Recompiled (14 pp), evidence verifier rerun.

## Repair round 2 (2026-11-11)
- Abstract: removed 'calibrated non-answer' and the 'little systematic measurement' gap claim; now 'valid but inconclusive' with interval-coverage caveat.
- Relation paragraph: dropped memorization capacity as an attributed account.
- Dev-plane wording: V3 lower seed 0.801 just above V1 mean, higher 0.899 above V2 mean; mean differences 0.031/0.022; spreads 'no smaller than' mean differences. Claims 17/18 now cite source_evidence/search_variants and derived/resolution.json; added claim on bootstrap coverage caveat.
- figure_manifest.json: figure_type for interval/dot plots set to 'scatter' (schema enum); recompiled (14 pp), evidence verifier dangling=0.

## Repair round 3 (2026-11-11)
- Audit finding decision-rule-provenance: removed "pre-declared"/"sealed evaluation uses"/"task environment supplied the decision rule"; paper now says the three-way rule is our own operationalization applied to the evaluator's interval (scripts/derive_resolution.py); no claim on when it was fixed. Renamed derived key to verdict_from_interval_rule and regenerated derived/resolution.json (values unchanged) and prov sidecars.
- Audit finding grounding-source-mismatch: claims on workload, parameters, compute, slope bounds, seed multisets re-pointed to files via `evidence_files` with empty source_ids (no grounding_sources id holds those values); labelled as derived arithmetic.
- Figure validation: strategy figure_type values interval_plot/dot_plot are not in the manifest schema enum, so the strategy and manifest could not agree; changed both strategy entries and manifest rows to `scatter`.
- Recompiled (14 pp, no undefined refs); scientific-evidence verify: 0 dangling.

## Repair round 4
- Audit fixes: intro now says the three-way rule is our own operationalization applied to the evaluator interval (removed "declares in advance"); log-linear profile slope written as -0.922 in text, table, claim; SI/Method qualify constants (only output-scaling, unembedding, hidden-exponent comments say offline selection was not possible; init scale and reference width are just source constants).
- claims_grounding.json claims 10,13-16 given non-empty source_ids (final.* ids). validate_claims OK (33 claims); compile ok (14 pp); scientific-evidence verify dangling=0.
