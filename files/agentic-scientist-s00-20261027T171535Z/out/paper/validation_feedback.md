# Paper validation feedback

- generated_at: 2026-10-27T17:58:38.012868+00:00
- paper_dir: `/home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper`
- ok: `False`

## Hard errors
- LaTeX command failed: /usr/local/bin/docker run --rm --network rwe-b1-agentic-scientist-s00-20261027T171535Z-net --user 1000:1000 -v /home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper:/workspace -w /workspace sha256:04a05e4d2625476fb47f10f99e46b758971b2c96554e124e0ccf47e169f9ab22 sh -c exec env -i PATH="$PATH" HOME=/nonexistent LANG="${LANG:-C.UTF-8}" TEXMFHOME=/nonexistent "$@" paper-compile pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `4695`
- substantive_element_count: `9`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `/home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `/home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper/scientific-evidence/verification-report.json`
- total_references: `50`
- resolved_references: `16`
- anchored_references: `34`
- dangling_references: `0`
- manifests_checked: `4`

## Agentic evidence audit
- checked: `True`
- verdict: `pass`
- finding_count: `0`
- summary: Visible claims, including the Supplementary Information, match claims_grounding.json, paper_data.json, closed_form_gap.json, protocol_facts.json, the evaluator and program source, and the evidence trail, with the qualified outcome and the selection and search-versus-final limits stated correctly.

## Soft warnings
- figures[1].min_font_size_pt below minimum: 7.7 < 8.0
- figures[1] PNG width too small: 1500 < 2400
- figures[2].min_font_size_pt below minimum: 7.7 < 8.0
- figures[2] PNG width too small: 1500 < 2400
