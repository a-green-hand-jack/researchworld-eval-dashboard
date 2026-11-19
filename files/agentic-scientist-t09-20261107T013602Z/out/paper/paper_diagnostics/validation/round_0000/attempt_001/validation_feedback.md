# Paper validation feedback

- generated_at: 2026-11-07T04:15:56.627515+00:00
- paper_dir: `work/results/t09/codex/20261107_014043/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=b7560a4a7250d2a940eb656eeb9612f6a7c0789b17bd581e868341be2659e096; actual=a094e86d7ecdbf5dfca73d46aadc078e266850b7c3b7318a4b6ac36c54e218ea Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `10223`
- substantive_element_count: `8`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/t09/codex/20261107_014043/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t09/codex/20261107_014043/paper/scientific-evidence/verification-report.json`
- total_references: `177`
- resolved_references: `102`
- anchored_references: `74`
- dangling_references: `1`
- manifests_checked: `20`

### Dangling `@evidence[[...]]` links to fix
- `figure_manifest.json.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=b7560a4a7250d2a940eb656eeb9612f6a7c0789b17bd581e868341be2659e096; actual=a094e86d7ecdbf5dfca73d46aadc078e266850b7c3b7318a4b6ac36c54e218ea

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=b7560a4a7250d2a940eb656eeb9612f6a7c0789b17bd581e868341be2659e096; actual=a094e86d7ecdbf5dfca73d46aadc078e266850b7c3b7318a4b6ac36c54e218ea Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
