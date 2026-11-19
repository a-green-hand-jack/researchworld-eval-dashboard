# Agentic evidence audit

- verdict: `fail`
- finding_count: `1`

## Summary
Retained results and qualification are supported, but the residual-shrinkage equation does not match the evaluated implementation.

## Findings
### 1. method-effective-count-floor — Method: Cross-fitted local residual transfer
- claim: Effective count equals (sum w)^2/sum(w^2).
- issue: The implementation floors the denominator at 1e-12. This changes shrinkage when squared weights sum below that floor, even when total weight exceeds the separately disclosed cutoff.
- evidence: paper.tex:122 omits the floor; source_evidence/selected/src/program.py:177 applies it during prediction, and source_evidence/selected/src/program.py:194 applies it during calibration; the prediction path calls this correction at source_evidence/selected/src/program.py:315.
- requested_fix: Change the manuscript equation to (sum w)^2/max(sum(w^2),1e-12), disclose the denominator floor, and qualify the concentration-only interpretation when that floor is active.
