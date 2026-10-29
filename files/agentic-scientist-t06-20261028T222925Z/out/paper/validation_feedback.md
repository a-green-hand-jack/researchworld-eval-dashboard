# Paper validation feedback

- generated_at: 2026-10-29T00:48:57.971369+00:00
- paper_dir: `work/results/t06/claude/20261028_222957/paper`
- ok: `True`

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `8962`
- substantive_element_count: `7`
- rendered_checked: `True`
- rendered_heading_present: `True`
- rendered_visible_character_count: `8724`

## Page budget
- paper_format: `iclr`
- body_pages: `9`
- min_body_pages: `8`
- min_last_body_page_fill_ratio: `0.75`
- max_body_pages: `9`
- exclude_references: `True`
- total_pages: `14`
- reference_start_page: `10`
- supplement_start_page: `12`
- supplement_pages: `3`
- last_body_page_number: `9`
- last_body_page_fill_ratio: `None`
- last_body_page_counted: `None`

## Evidence validation
- bundle_path: `work/results/t06/claude/20261028_222957/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t06/claude/20261028_222957/paper/scientific-evidence/verification-report.json`
- total_references: `68`
- resolved_references: `16`
- anchored_references: `52`
- dangling_references: `0`
- manifests_checked: `6`

## Agentic evidence audit
- checked: `True`
- verdict: `pass`
- finding_count: `0`
- summary: The visible claims in the main text, tables, figures and Supplementary Information match claims_grounding.json, paper_data.json final_evaluation (qualified/completed/correct, the 17 verified_k values per seed, metrics and CIs) and downstream_study (baseline selection, 0 of 3 scored, unscored runs described as unknown rather than losses). The derived n values and percentages reproduce exactly, and the implementation details match source_evidence/downstream/program/src/program.py at the cited lines. The paper consistently presents the harness protocol as stated rather than inspectable, discloses that no per-gate diagnostics were recorded, and reports the superiority test as not supported.

## Soft warnings
- figures[0] labels too long without abbreviation
