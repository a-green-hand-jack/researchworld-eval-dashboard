# Paper validation feedback

- generated_at: 2026-11-11T10:58:55.387074+00:00
- paper_dir: `work/results/t07/claude/20261111_091120/paper`
- ok: `True`

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `6836`
- substantive_element_count: `7`
- rendered_checked: `True`
- rendered_heading_present: `True`
- rendered_visible_character_count: `6961`

## Page budget
- paper_format: `iclr`
- body_pages: `9`
- min_body_pages: `8`
- min_last_body_page_fill_ratio: `0.75`
- max_body_pages: `9`
- exclude_references: `True`
- total_pages: `13`
- reference_start_page: `10`
- supplement_start_page: `12`
- supplement_pages: `2`
- last_body_page_number: `9`
- last_body_page_fill_ratio: `None`
- last_body_page_counted: `None`

## Evidence validation
- bundle_path: `work/results/t07/claude/20261111_091120/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t07/claude/20261111_091120/paper/scientific-evidence/verification-report.json`
- total_references: `39`
- resolved_references: `22`
- anchored_references: `17`
- dangling_references: `0`
- manifests_checked: `6`

## Agentic evidence audit
- checked: `True`
- verdict: `pass`
- finding_count: `0`
- summary: The paper's visible claims, including the Supplementary tables and details, match claims_grounding.json, paper_data.json, derived/metrics_summary.json, the readable source_evidence files and the evidence trail. It states the qualified outcome, the zero-spanning intervals and the limitations without overclaiming.

## Soft warnings
- figures[0] labels too long without abbreviation
- figures[0].font_sizes.title below minimum: 9.0 < 10.0
- figures[0].font_sizes.axis below minimum: 8.0 < 9.0
- figures[1].font_sizes.title below minimum: 9.5 < 10.0
- figures[1] PNG width too small: 1688 < 2400
- figures[2] labels too long without abbreviation
- figures[2].font_sizes.title below minimum: 9.5 < 10.0
- figures[2] PNG width too small: 1618 < 2400
- figures[2] PNG height too small: 692 < 700
