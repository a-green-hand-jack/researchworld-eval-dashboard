# Paper validation feedback

- generated_at: 2026-11-06T05:48:56.702057+00:00
- paper_dir: `work/results/a06/codex/20261105_100448/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=147e04a2eaa91801e552d8cd09950f3f024fc862793c33665294936cf57adaf1; actual=7aefe3c44ac95524d625aeeaa5c4e59a6bdb1d43e6e07ff4ce135e328ab2adf6 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `11062`
- substantive_element_count: `5`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/a06/codex/20261105_100448/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/a06/codex/20261105_100448/paper/scientific-evidence/verification-report.json`
- total_references: `176`
- resolved_references: `72`
- anchored_references: `103`
- dangling_references: `1`
- manifests_checked: `14`

### Dangling `@evidence[[...]]` links to fix
- `figure_manifest.json.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=147e04a2eaa91801e552d8cd09950f3f024fc862793c33665294936cf57adaf1; actual=7aefe3c44ac95524d625aeeaa5c4e59a6bdb1d43e6e07ff4ce135e328ab2adf6

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=147e04a2eaa91801e552d8cd09950f3f024fc862793c33665294936cf57adaf1; actual=7aefe3c44ac95524d625aeeaa5c4e59a6bdb1d43e6e07ff4ce135e328ab2adf6 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
