# Verified venue requirements

NeurIPS 2026 main-track format for the fixed-input confidence-interval study.

- `requirements/venue.md`: objective/venue requirements, artifact and figure constraints, known limits.
- `requirements/build-handoff.md`: report-owner preamble, build command and final PDF checks.
- `requirements/checklist-guide.md`: paper-owner guide to all 16 official checklist questions.
- `official/`: byte-identical official style, instructions/example, and unanswered checklist template.
- `sources.json` and `sources/`: evidence and frozen-input/source hashes.
- `verification/`: measured geometry, example-compile/font findings and reproduction instructions.

The official example/checklist are source templates, not the study or completed answers. The settled `venue/.*` ownership is merged in paper-repo/.forgejo/CODEOWNERS; paper-repo PR #5 delivers this pack under `venue/`. `venue-artifacts.json` declares required delivered artifacts, including report/code/generator directories whose file names remain with their owners. Paper owns the completed checklist under `manuscript/` and the rendered `paper.pdf`.
