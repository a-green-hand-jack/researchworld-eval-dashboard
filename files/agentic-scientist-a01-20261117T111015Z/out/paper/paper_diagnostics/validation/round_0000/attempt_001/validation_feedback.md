# Paper validation feedback

- generated_at: 2026-11-17T14:42:37.781648+00:00
- paper_dir: `work/results/a01/codex/20261117_111437/paper`
- ok: `False`

## Hard errors
- scientific-evidence validation failed: scientific-evidence verifier found 3 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=9a944f1f41acd039a3f2fb1d5f855a9912fad4da0db2b529636de5d32c47b21b; actual=7b094f9e8c104aa403fe788f0c8195e965ebaa7436db55035cffcf4dd6523e0b paper.pdf.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=82b4e41b75e4d8f956030da89ccf87f1539deaaff55d2f3ed678359d71dd83b1; actual=4e1923e217cfd27364686047b83351f3d9e92e29ecfe73acadca893138c27459 paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=86809def3e3d793ff37bd6cf701f9debe0c8cc2dc6ae88f538672ce8e7c5223a; actual=aaa38f21ebb2ca37d5dd64b3c4e8204aac5a4229b7456ba85a6713d678613598 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.

## Supplementary Information validation
- appendix_present: `True`
- heading_present: `True`
- placed_after_references: `True`
- pre_bibliography_clearpage_present: `True`
- clearpage_present: `True`
- visible_character_count: `17726`
- substantive_element_count: `8`
- rendered_checked: `False`
- rendered_heading_present: `False`
- rendered_visible_character_count: `0`

## Evidence validation
- bundle_path: `work/results/a01/codex/20261117_111437/paper/scientific-evidence`
- bundle_present: `True`
- verification_report: `work/results/a01/codex/20261117_111437/paper/scientific-evidence/verification-report.json`
- total_references: `306`
- resolved_references: `183`
- anchored_references: `120`
- dangling_references: `3`
- manifests_checked: `19`

### Dangling `@evidence[[...]]` links to fix
- `figure_manifest.json.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=9a944f1f41acd039a3f2fb1d5f855a9912fad4da0db2b529636de5d32c47b21b; actual=7b094f9e8c104aa403fe788f0c8195e965ebaa7436db55035cffcf4dd6523e0b
- `paper.pdf.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=82b4e41b75e4d8f956030da89ccf87f1539deaaff55d2f3ed678359d71dd83b1; actual=4e1923e217cfd27364686047b83351f3d9e92e29ecfe73acadca893138c27459
- `paper.tex.prov.json` <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=86809def3e3d793ff37bd6cf701f9debe0c8cc2dc6ae88f538672ce8e7c5223a; actual=aaa38f21ebb2ca37d5dd64b3c4e8204aac5a4229b7456ba85a6713d678613598

### Evidence hard errors
- scientific-evidence verifier found 3 dangling `@evidence[[...]]` link(s). figure_manifest.json.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=9a944f1f41acd039a3f2fb1d5f855a9912fad4da0db2b529636de5d32c47b21b; actual=7b094f9e8c104aa403fe788f0c8195e965ebaa7436db55035cffcf4dd6523e0b paper.pdf.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=82b4e41b75e4d8f956030da89ccf87f1539deaaff55d2f3ed678359d71dd83b1; actual=4e1923e217cfd27364686047b83351f3d9e92e29ecfe73acadca893138c27459 paper.tex.prov.json <artifact.sha256> -> Recorded sha256 does not match file contents.; expected=86809def3e3d793ff37bd6cf701f9debe0c8cc2dc6ae88f538672ce8e7c5223a; actual=aaa38f21ebb2ca37d5dd64b3c4e8204aac5a4229b7456ba85a6713d678613598 Fix or remove every dangling link, rerun `scientific_evidence.sh verify --root-dir <paper_dir>`, and repeat until zero dangling references remain.
