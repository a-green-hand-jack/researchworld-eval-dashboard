# Paper validation feedback

- generated_at: 2026-11-17T23:43:52.989359+00:00
- paper_dir: `work/results/t06/codex/20261117_205956/paper`
- ok: `False`

## Hard errors
- LaTeX command failed: /usr/local/bin/docker run --rm --network rwe-b1-agentic-scientist-t06-20261117T205454Z-net --user 1000:1000 -v work/results/t06/codex/20261117_205956/paper:/workspace -w /workspace sha256:c957359c87fc067a97a5b85deb1f3d0ce1578a8b7d531f75f306726b4a969e08 sh -c exec env -i PATH="$PATH" HOME=/nonexistent LANG="${LANG:-C.UTF-8}" TEXMFHOME=/nonexistent "$@" paper-compile pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `9271`
- substantive_element_count: `8`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/t06/codex/20261117_205956/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t06/codex/20261117_205956/paper/scientific-evidence/verification-report.json`
- total_references: `104`
- resolved_references: `38`
- anchored_references: `66`
- dangling_references: `0`
- manifests_checked: `8`
