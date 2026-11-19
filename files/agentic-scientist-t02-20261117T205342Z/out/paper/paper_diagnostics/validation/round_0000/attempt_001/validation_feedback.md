# Paper validation feedback

- generated_at: 2026-11-18T01:45:39.157313+00:00
- paper_dir: `work/results/t02/codex/20261117_205843/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=ad5df6dd1b00f493e18b44ab556b5d08da9d30b9d3cfa363beb215d7293244d8; actual=27505d5212d7e5c1e6c9bf68c9397e6105c7b3aa299f60bf714d0972f95ef718 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `10436`
- substantive_element_count: `7`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/t02/codex/20261117_205843/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t02/codex/20261117_205843/paper/scientific-evidence/verification-report.json`
- total_references: `199`
- resolved_references: `102`
- anchored_references: `96`
- dangling_references: `1`
- manifests_checked: `17`

### Dangling `@evidence[[...]]` links to fix
- `figure_manifest.json.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=ad5df6dd1b00f493e18b44ab556b5d08da9d30b9d3cfa363beb215d7293244d8; actual=27505d5212d7e5c1e6c9bf68c9397e6105c7b3aa299f60bf714d0972f95ef718

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=ad5df6dd1b00f493e18b44ab556b5d08da9d30b9d3cfa363beb215d7293244d8; actual=27505d5212d7e5c1e6c9bf68c9397e6105c7b3aa299f60bf714d0972f95ef718 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
