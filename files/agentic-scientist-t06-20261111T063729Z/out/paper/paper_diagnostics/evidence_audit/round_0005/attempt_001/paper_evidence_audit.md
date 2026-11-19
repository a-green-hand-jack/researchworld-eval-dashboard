# Agentic evidence audit

- verdict: `fail`
- finding_count: `3`

## Summary
The held-out numbers and the qualification handling match the evidence trail, but the development sub-scores have no support in the grounding artifacts, one control is interpreted despite the paper's own no-claim statement, and "verified" wording contradicts the stated evaluator-opacity caveat.

## Findings
### 1. dev-subscores-ungrounded — Results (Development tables), Table tab:dev, Supplement "Development tables: additional detail", Studied-vs-influence-only subsection
- claim: Configuration 1 splits into crowd 0.9987 and expert 0.0 with flip rate 0.5, random reference 0.0695, influence reference 0.4993, mean budget fraction 0.5007 and control gap 0.3153. From these the paper derives that neither MT-Bench pair flipped within the 68-row cap, that the crowd cases needed three rows, and that the development aggregate equals the influence-only reference.
- issue: None of these sub-scores appears in any evidence-trail artifact. The paper itself says they are quoted from a log and have no registry entry. The claims_grounding entries cite result.best_correct_score and result.top_program_0x, which hold only the 0.4993 total. The derived inferences and the main-text B2 comparison on the development tables therefore rest on unregistered numbers.
- evidence: paper_data.json: grep finds no 0.9987, 0.0695, 0.3153 or 0.5007; all_programs and top_programs carry only combined_score 0.4993478 and per-seed durations. claims_grounding.json claims 21-22 cite result.* ids that are scalar totals. The values appear only in strategy and memory prompt text (paper_strategy_prompt.md, global_memory_summary.md), not in the scientific-evidence trail. Verification report entries for these lines are only anchored to paper_data.json#all_programs and give a total score only.
- requested_fix: Remove the unregistered sub-scores from Table tab:dev and the prose. Drop the derived statements about expert non-flip, three crowd rows, 0.5007 and the development influence-reference equality. Keep only the registered totals (0.4993 for all three configurations and the baseline, delta 0.0, 3 of 3 scored, runtimes). State that no per-family development breakdown is recorded.

### 2. copy-control-overinterpreted — Results (Controls) vs Method (Comparators and validity controls)
- claim: The cross-table copy control flipped 0 of 2 trials, "which is consistent with the budgets not being artefacts of an already-reversed pair or of row position."
- issue: Methods and the Supplement say the copy control's construction and thresholds are not documented and that no claim is made about it. Results then interprets it as ruling out a row-position artefact. That interpretation is unsupported and contradicts the paper's own caveat.
- evidence: claims_grounding.json claim "Empty-set control flips no case; cross-table copy control flips 0 of 2 trials" cites only final.evidence.episodes, which records copy_control {flips:0, trials:2} with no construction detail. paper.tex Method states "we make no claim about them". Supplement states "its construction is not documented in the staged evidence".
- requested_fix: Keep the empty-set interpretation only if wanted (empty set flipped no case). For the copy control, report only "0 flips in 2 trials" and delete the "row position" inference.

### 3. verified-protocol-wording — Introduction (Research question), Results Table tab:cases caption, Contributions
- claim: Budgets are measured "by one verified protocol", and $k$ is "the verified number of removed rows".
- issue: The paper repeatedly states that the evaluator source is not staged and that it could not inspect how the evaluator verifies a returned set. Calling the protocol or the budgets "verified" overstates the evidence. The only inspectable refit is the candidate's own.
- evidence: paper.tex Intro ("we could not inspect how it verifies them"), Method comparators section, Supplement "Controls and qualification details" ("we could not inspect how the evaluator verifies it"). claims_grounding.json: "Evaluator source for comparators B1-B3 and the controls is not staged; only recorded outcomes ... are reported".
- requested_fix: Replace "verified" with "evaluator-recorded". For example, "one evaluator-recorded protocol" and "the recorded number of removed rows".
