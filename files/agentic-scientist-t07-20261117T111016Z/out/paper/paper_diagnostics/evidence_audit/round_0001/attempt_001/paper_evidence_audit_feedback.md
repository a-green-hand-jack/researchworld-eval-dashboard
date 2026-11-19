# Agentic evidence audit feedback

- generated_at: `2026-11-17T14:41:01.296163+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `1`
- audit_json_path: `work/results/t07/codex/20261117_111440/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t07/codex/20261117_111440/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t07/codex/20261117_111440/paper/paper_evidence_audit_raw.txt`

## Summary
One reported MAE is rounded inconsistently with the grounding artifacts and supplementary table.

## Findings
- `helm-math-mae-rounding` (Results: Where the Comparison Reverses): The grounded value rounds to 6.19, not 6.18.
  - claim: At 25 items, HELM MATH package MAE is 6.18 percentage points.
  - evidence: paper.tex:214 reports 6.18; claims_grounding.json claims[26] and analysis/paper_statistics.json#/by_case_budget/math/25/selected/mae give 0.06185113173033655, equivalent to 6.185113173 percentage points; Supplementary Table at paper.tex:322 correctly reports 6.19.
  - requested_fix: Replace 6.18 with 6.19 in the Results paragraph.
