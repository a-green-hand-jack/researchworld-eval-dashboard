# Agentic evidence audit

- verdict: `fail`
- finding_count: `1`

## Summary
Numerical results and qualification limitations are grounded, but the manuscript describes a completed overview figure that remains an unrendered placeholder.

## Findings
### 1. overview-rendering-1 — Introduction Figure 1; Supplementary Information—Reproducibility
- claim: The overview depicts the study design and “is rendered separately by the designated concept-figure workflow.”
- issue: The included image contains only a pending-rendering message; the rendering workflow failed, contradicting the manuscript’s completed-rendering claim and figure description.
- evidence: paper.tex:51 and paper.tex:52 include and describe figures/study_overview.png; paper.tex:361 asserts rendering; the PNG reads “Concept overview pending orchestrator rendering”; figure_manifest.json records generator=null, rendering exit code 1, and a placeholder note.
- requested_fix: Remove the placeholder figure and its descriptive caption, and remove or qualify the supplementary claim that rendering completed; retain the supported study-design explanation in prose.
