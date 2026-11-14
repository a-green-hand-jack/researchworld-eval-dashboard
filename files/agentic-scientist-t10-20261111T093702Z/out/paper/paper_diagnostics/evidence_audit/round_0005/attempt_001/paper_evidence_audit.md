# Agentic evidence audit

- verdict: `fail`
- finding_count: `1`

## Summary
Results numbers, qualification facts, coverage statements and SI tables all match the grounding artifacts, but the description of the selection/fallback rule contradicts the frozen estimator source.

## Findings
### 1. selection-rule-margin-misstated — Method (Selection with fallback) and Supplement S1 (fallback margin 0.99)
- claim: Each recalibrated candidate replaces the current best only if its half-width is below 0.99 times the current best; otherwise PPI++ is returned.
- issue: In source_evidence/frozen_winner_estimator.py, _best_interval sets threshold = 0.99 * best_half, which is the PPI++ half-width. After the isotonic candidate is accepted it sets threshold = half, with no 0.99 factor. The binned candidate then replaces the isotonic one if it is merely narrower, with no 1% margin. The 1% margin applies only against PPI++, not against the current best, so the stated rule is not what was evaluated.
- evidence: paper.tex Method paragraph Selection with fallback, plus SI S1 settings list; source_evidence/frozen_winner_estimator.py _best_interval (lines ~262-280: threshold = 0.99 * best_half, then 'if half < threshold: best, threshold = cand, half'); claims_grounding.json has no claim supporting the per-candidate 0.99-of-current-best wording.
- requested_fix: Reword to say that a recalibrated candidate is adopted only if its half-width is below 0.99 times the PPI++ half-width, and that between the isotonic and binned candidates the narrower one is kept without an additional margin. Apply the same wording in the SI and in the 'smaller of three estimated widths' discussion.
