# Agentic evidence audit

- verdict: `fail`
- finding_count: `1`

## Summary
A supplementary figure-provenance claim contradicts the generation artifacts; the measured results and qualification statements are consistent.

## Findings
### 1. overview-provenance-1 — Supplementary Information: Reproducibility and Resource Accounting
- claim: It leaves an orchestrator-rendered overview untouched.
- issue: The overview-generation attempt failed; the retained image is a title-only placeholder, not the claimed orchestrator-rendered overview.
- evidence: paper.tex:345; figures/reporting_overview.prompts.json records status failed and exit code 1; concept_figure_run.log confirms renderer failure; build_artifacts.py:147 creates the title-only fallback visible in figures/reporting_overview.png.
- requested_fix: Remove the unsupported rendering attribution and describe the retained overview as a title-only placeholder.
