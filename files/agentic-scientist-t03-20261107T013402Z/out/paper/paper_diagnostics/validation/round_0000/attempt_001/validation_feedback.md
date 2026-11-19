# Paper validation feedback

- generated_at: 2026-11-07T04:24:54.340490+00:00
- paper_dir: `work/results/t03/codex/20261107_013849/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=57c472a145c18b20f0f037569791dd281dfa8548eb1972ff67b12106c1fc2455; actual=170b239d9497e0248bdcb0583cc734caf91db37c4665b119176e09cd81005bb8 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `14185`
- substantive_element_count: `8`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/t03/codex/20261107_013849/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/t03/codex/20261107_013849/paper/scientific-evidence/verification-report.json`
- total_references: `196`
- resolved_references: `105`
- anchored_references: `90`
- dangling_references: `1`
- manifests_checked: `15`

### Dangling `@evidence[[...]]` links to fix
- `paper.tex.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=57c472a145c18b20f0f037569791dd281dfa8548eb1972ff67b12106c1fc2455; actual=170b239d9497e0248bdcb0583cc734caf91db37c4665b119176e09cd81005bb8

### Evidence hard errors
- scientific-evidence verifier found 1 dangling `@evidence[[...]]` link(s). paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=57c472a145c18b20f0f037569791dd281dfa8548eb1972ff67b12106c1fc2455; actual=170b239d9497e0248bdcb0583cc734caf91db37c4665b119176e09cd81005bb8 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
