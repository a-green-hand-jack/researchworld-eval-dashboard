# Paper validation feedback

- generated_at: 2026-11-07T07:04:40.679033+00:00
- paper_dir: `work/results/r02/codex/20261107_044437/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=92e0b78a2c64581e577d259971eb3eeb3df7a9590097f8d45d0c4589b7f8048f; actual=c9a02ece0f490de3610ffaa1bc661ca2f5e575f958888db42c9e0489abb6eb39 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `18502`
- substantive_element_count: `9`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/r02/codex/20261107_044437/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/r02/codex/20261107_044437/paper/scientific-evidence/verification-report.json`
- total_references: `258`
- resolved_references: `162`
- anchored_references: `95`
- dangling_references: `1`
- manifests_checked: `22`

### Dangling `@evidence[[...]]` links to fix
- `figure_manifest.json.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=92e0b78a2c64581e577d259971eb3eeb3df7a9590097f8d45d0c4589b7f8048f; actual=c9a02ece0f490de3610ffaa1bc661ca2f5e575f958888db42c9e0489abb6eb39

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=92e0b78a2c64581e577d259971eb3eeb3df7a9590097f8d45d0c4589b7f8048f; actual=c9a02ece0f490de3610ffaa1bc661ca2f5e575f958888db42c9e0489abb6eb39 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
