# Paper validation feedback

- generated_at: 2026-11-13T00:43:33.516127+00:00
- paper_dir: `work/results/r03/codex/20261112_215151/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=a21c83028c92611c1f67fe5849117964c069463c2440cbcb0fbb3e03e0623c66; actual=9de575676bd52ac8cf9743b4a26bc7aee3da211172646698023ab1ea59ded78e Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `10404`
- substantive_element_count: `6`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/r03/codex/20261112_215151/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/r03/codex/20261112_215151/paper/scientific-evidence/verification-report.json`
- total_references: `194`
- resolved_references: `124`
- anchored_references: `69`
- dangling_references: `1`
- manifests_checked: `14`

### Dangling `@evidence[[...]]` links to fix
- `paper.tex.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=a21c83028c92611c1f67fe5849117964c069463c2440cbcb0fbb3e03e0623c66; actual=9de575676bd52ac8cf9743b4a26bc7aee3da211172646698023ab1ea59ded78e

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=a21c83028c92611c1f67fe5849117964c069463c2440cbcb0fbb3e03e0623c66; actual=9de575676bd52ac8cf9743b4a26bc7aee3da211172646698023ab1ea59ded78e Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
