# Agentic evidence audit

- verdict: `fail`
- finding_count: `1`

## Summary
One reported MAE is rounded inconsistently with the grounding artifacts and supplementary table.

## Findings
### 1. helm-math-mae-rounding — Results: Where the Comparison Reverses
- claim: At 25 items, HELM MATH package MAE is 6.18 percentage points.
- issue: The grounded value rounds to 6.19, not 6.18.
- evidence: paper.tex:214 reports 6.18; claims_grounding.json claims[26] and analysis/paper_statistics.json#/by_case_budget/math/25/selected/mae give 0.06185113173033655, equivalent to 6.185113173 percentage points; Supplementary Table at paper.tex:322 correctly reports 6.19.
- requested_fix: Replace 6.18 with 6.19 in the Results paragraph.
