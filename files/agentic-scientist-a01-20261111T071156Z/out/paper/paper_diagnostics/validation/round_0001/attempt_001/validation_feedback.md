# Paper validation feedback

- generated_at: 2026-11-11T09:30:23.986875+00:00
- paper_dir: `work/results/a01/claude/20261111_071545/paper`
- ok: `False`

## Hard errors
- LaTeX command failed: /usr/local/bin/docker run --rm --network rwe-b1-agentic-scientist-a01-20261111T071156Z-net --user 1000:1000 -v work/results/a01/claude/20261111_071545/paper:/workspace -w /workspace sha256:c957359c87fc067a97a5b85deb1f3d0ce1578a8b7d531f75f306726b4a969e08 sh -c exec env -i PATH="$PATH" HOME=/nonexistent LANG="${LANG:-C.UTF-8}" TEXMFHOME=/nonexistent "$@" paper-compile pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `5822`
- substantive_element_count: `7`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/a01/claude/20261111_071545/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/a01/claude/20261111_071545/paper/scientific-evidence/verification-report.json`
- total_references: `46`
- resolved_references: `21`
- anchored_references: `25`
- dangling_references: `0`
- manifests_checked: `5`

## Soft warnings
- figures[0].font_sizes.title below minimum: 8.5 < 10.0
- figures[0].font_sizes.axis below minimum: 8.0 < 9.0
- figures[1].font_sizes.title below minimum: 8.5 < 10.0
- figures[1].font_sizes.axis below minimum: 8.0 < 9.0
- figures[1] PNG width too small: 1650 < 2400
- figures[2].font_sizes.title below minimum: 8.5 < 10.0
- figures[2].font_sizes.axis below minimum: 8.0 < 9.0
- figures[2] PNG width too small: 1650 < 2400
