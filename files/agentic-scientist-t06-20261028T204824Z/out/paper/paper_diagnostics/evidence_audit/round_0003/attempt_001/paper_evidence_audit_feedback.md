# Agentic evidence audit feedback

- generated_at: `2026-10-28T21:55:12.621730+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `2`
- audit_json_path: `work/results/t06/claude/20261028_204856/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t06/claude/20261028_204856/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t06/claude/20261028_204856/paper/paper_evidence_audit_raw.txt`

## Summary
All reported numbers, qualification facts, selection context and the 3/0/3 attempt counts match the grounding artifacts, but two visible statements go beyond the evidence trail.

## Findings
- `winrate-no-refit-1` (Results (Reference policies set the scale)): Nothing in the evidence trail supports the claim that the win-rate heuristic needs no model fit. The evaluator's win-rate baseline selects rows using the incumbent top and the runner-up (case top and rival), and both come from the evaluator's Bradley-Terry fit of the unedited data. The claim_grounding entry for this passage only supports the 0.574 and 0.606 values and the 0.032 difference.
  - claim: The win-rate heuristic, which needs no model refit, scores 0.574 against 0.606 for the influence search
  - evidence: source_evidence/task/evaluate_final.py baseline_winrate reads case["top"] and case["rival"]. Those fields come from the Bradley-Terry fit, and baseline_scores gives the baseline no fit-free path. claims_grounding.json claim on constant/random/win-rate scores lists only final.metric.score_* ids.
  - requested_fix: Delete the clause "which needs no model refit", or replace it with a neutral description such as "which selects rows by the incumbent's wins, preferring those against the runner-up".
- `mtbench-same-comparisons-1` (Introduction, Evaluation designs (Table 1) and Analysis (Expert human versus GPT-4 judge)): The artifacts show only that the expert-human and GPT-4 tables come from the same dataset repository, through separate files (human-*.parquet and gpt4_pair-*.parquet) loaded as separate CSVs. They do not show that the two final row sets cover the same comparisons, questions or models, or that they are matched. The "cleanest contrast" framing and the same-questions-and-models statement therefore overstate what is grounded. The paper also reports no row counts or competitor counts that could confirm a match.
  - claim: GPT-4 pairwise judgments on the same MT-Bench comparisons; Expert human and GPT-4 judgments are on the same MT-Bench questions and models, which makes this the cleanest contrast in the study
  - evidence: source_evidence/task/task_contract.json lists the two MT-Bench tables as separately derived files with separate hashing. evaluate_final.py raw_source loads mtbench_human.csv and mtbench_gpt4.csv independently. paper.tex Table 1 caption says dataset sizes and competitor counts are not used. claims_grounding.json has no claim establishing row-level alignment.
  - requested_fix: Replace "the same MT-Bench comparisons/questions and models" with "both derived from the MT-Bench human-judgment dataset release". State that the overlap of rows, questions and models between the two designs was not verified. Drop or soften "cleanest contrast" so it reads as a contrast between two single measurements from related data sources.
