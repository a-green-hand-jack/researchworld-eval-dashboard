# Paper validation feedback

- generated_at: 2026-11-07T04:55:18.815944+00:00
- paper_dir: `work/results/a01/codex/20261107_023211/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=e97607de39440535a91335fc65808af74c7f98e4a2761cbdfef9904420ee33a0; actual=1f71dcdf0656ae638c49630edb9862c428518af2c02346002173a7526ed74af4 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `18120`
- substantive_element_count: `7`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/a01/codex/20261107_023211/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/a01/codex/20261107_023211/paper/scientific-evidence/verification-report.json`
- total_references: `234`
- resolved_references: `101`
- anchored_references: `132`
- dangling_references: `1`
- manifests_checked: `20`

### Dangling `@evidence[[...]]` links to fix
- `paper.tex.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=e97607de39440535a91335fc65808af74c7f98e4a2761cbdfef9904420ee33a0; actual=1f71dcdf0656ae638c49630edb9862c428518af2c02346002173a7526ed74af4

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=e97607de39440535a91335fc65808af74c7f98e4a2761cbdfef9904420ee33a0; actual=1f71dcdf0656ae638c49630edb9862c428518af2c02346002173a7526ed74af4 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
