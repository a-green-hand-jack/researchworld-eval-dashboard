# Agentic evidence audit feedback

- generated_at: `2026-11-06T06:05:55.281119+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `1`
- audit_json_path: `work/results/a06/codex/20261105_100448/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/a06/codex/20261105_100448/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/a06/codex/20261105_100448/paper/paper_evidence_audit_raw.txt`

## Summary
A supplementary figure-provenance claim contradicts the generation artifacts; the measured results and qualification statements are consistent.

## Findings
- `overview-provenance-1` (Supplementary Information: Reproducibility and Resource Accounting): The overview-generation attempt failed; the retained image is a title-only placeholder, not the claimed orchestrator-rendered overview.
  - claim: It leaves an orchestrator-rendered overview untouched.
  - evidence: paper.tex:345; figures/reporting_overview.prompts.json records status failed and exit code 1; concept_figure_run.log confirms renderer failure; build_artifacts.py:147 creates the title-only fallback visible in figures/reporting_overview.png.
  - requested_fix: Remove the unsupported rendering attribution and describe the retained overview as a title-only placeholder.
