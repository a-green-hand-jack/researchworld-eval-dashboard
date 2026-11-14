# Agentic evidence audit

- verdict: `fail`
- finding_count: `4`

## Summary
Headline held-out numbers match the evidence trail, but one normaliser conclusion contradicts the paper's own figures, qualification is over-read as "controls passed", and some evaluator-internal and development-breakdown claims are not supported by the cited sources.

## Findings
### 1. normaliser-direction-contradiction — Results: Crowd votes versus sports
- claim: Dividing by the mean number of comparisons a participant appears in (2N/M) instead of by N reverses the direction of the size effect; both views disagree about which table looks more fragile.
- issue: The paper's own numbers do not show a reversal or disagreement. Under k/N the sports budgets are 10.5x (top) and 21.0x (mid) the crowd value. Under k/(2N/M) they are still larger for sports: 7.2% vs 1.2% for top and 0.93% vs 0.077% for mid, about 6x and 12x. Both normalisers rank sports as the larger share, so the sentence misdescribes the derived values.
- evidence: paper.tex Results section on crowd versus sports; derived/final_stats.json cases.F1.studied_percent_of_mean_participant_comparisons=1.1885 with mean_comparisons_per_participant=5216.5; claims_grounding.json claim on 2N/M (5,217 and 860; 1.2% and 7.2%; mid 0.077% and 0.93%).
- requested_fix: Remove the claims that the direction reverses and that the views disagree about which table looks more fragile. State that sports has the larger budget share under both normalisers, with a smaller ratio under the per-participant view (about 6x top and 12x mid versus 10.5x and 21.0x). Keep the confound caveat.

### 2. qualified-means-controls-passed — Experimental Protocol 4.3, Discussion (iii), Supplement Controls and qualification details
- claim: We read this as: the evaluation ran to completion and its controls passed. The qualified outcome of the held-out evaluation certifies that the evaluation completed with its controls passing.
- issue: final.qualification.* grounds only outcome=qualified, status=completed, correct=true, and candidate diagnostics unverified. No artifact records which gates or criteria the qualification decision covers or that it certifies controls. Reading qualified as certifying controls and validity is an unsupported inference. The recorded control outcomes (empty-set no flip, non-vacuous permutation, copy 0 of 2) are separate observations from final.evidence.episodes.
- evidence: paper_data.json final_evaluation (outcome, status, correct only; no gate diagnostics); claims_grounding.json claim on qualification (outcome qualified, status completed, success indicator true, diagnostics unverified); paper.tex lines for the qualification subsection and Discussion (iii).
- requested_fix: Say only that the sealed evaluation completed and was recorded as qualified with a true success indicator. Report the control results as separate observations from the episode evidence. Delete the statements that qualified certifies controls passing, and add that the qualification gate criteria are not recorded in the evidence.

### 3. evaluator-internals-unsupported — Problem Setup 3.4 and 3.5, Supplement Controls and Algorithmic specification and Data provenance
- claim: B3 deletes rows where the upper participant beat another participant, ordered by opponent rating. The permutation control is non-vacuous only within 90% of expected moved fraction and spread at most half. The evaluator's acceptance test is theta_hi<theta_lo with no margin. Held-out content hashes are tested for overlap and the evaluation aborts on any overlap; tables are checked by checksum. Cross-table copy rescales row indices.
- issue: These describe evaluator internals (comparator construction, control thresholds, acceptance rule, abort-on-overlap and checksum behaviour, copy-control mechanics). The only inspectable source is the candidate and baseline program under source_evidence/downstream, and no evaluator source or spec is staged. claims_grounding.json has no claim for these details. The abort-on-overlap statement also sits awkwardly beside the recorded removal of 2 overlap rows and the 652 kept prompt-only overlaps.
- evidence: source_evidence/downstream contains only baseline and program (program.py, datasets_offline.py, program_spec.toml); claims_grounding.json covers budgets, scores and control outcomes but not comparator or control construction; derived/task_meta/final_meta.json shows 2 rows removed and 652 prompt-only overlaps kept.
- requested_fix: Remove or explicitly mark as not independently verifiable the evaluator-implementation specifics: the B3 construction, the 90% and half-spread thresholds, the no-margin acceptance rule, abort-on-overlap, checksum verification, and the copy-control rescaling. Keep only the observed control outcomes that final.evidence.episodes records.

### 4. dev-breakdown-grounding-mismatch — Results: Development tables, Table dev, Supplement Development tables additional detail
- claim: Crowd 0.9987, expert 0.0, flip rate 0.5, random reference 0.0695, influence reference 0.4993, mean budget fraction 0.5007, control gap 0.3153 for each of the three configurations; configurations 2 and 3 described as cell-aggregated relaxed search with exact swap polishing and a stationarity LP.
- issue: The claims_grounding.json entries cite result.best_correct_score and result.top_program_01 to 03, which each carry only the 0.4993 combined score. paper_data.json does not contain the per-family, flip-rate, random-reference, budget-fraction or control-gap breakdown for the search scope, and the sub-scores appear only in generated prompt text. Descriptions of configurations 2 and 3 rest on idea titles, with no inspectable source.
- evidence: paper_data.json grounding_sources result.top_program_01 to 03 (value 0.4993478 only); all_programs entries (combined_score and durations only); claims_grounding.json development claim and its source_ids; source_evidence/downstream has no source for configurations 2 and 3.
- requested_fix: Either anchor the development sub-metrics to a resolvable evidence source or state that they are quoted from the search-stage evaluator output without a registry entry. Limit the Table dev columns for configurations 2 and 3 to the grounded score and duration. Describe those two configurations only at title level, with no claim about their algorithms.
