# Completed deliverables

- **`paper.pdf`** — final compiled research paper; **7 main-text pages, 13 total pages**, unmodified official ICML 2026 style, 6 tables, 4 figures, impact statement, references, appendix, AI disclosure, and completed research/reproducibility checklist.
- **`paper/main.tex`** and associated `paper/` files — complete LaTeX source, bibliography, generated tables/numbers, and official style/template provenance.
- **`src/`**, **`requirements.txt`**, **`reproduce.sh`** — all download, preprocessing, fitting, attack, control, uncertainty, plotting, validation, and packaging code.
- **`README.md`** — commands, exact environment, fixed seeds, data versions/hashes, expected runtime, and script-to-figure/table mapping.
- **`results/`**, **`figures/`** — actual experiment outputs, saved bootstrap draws and edit witnesses, independent replay checks, vector and raster plots.
- **`notes/`**, **`data/manifest.json`**, **`data/PROVENANCE.md`** — initial protocol, exploratory changes, failed attempts, restricted literature access log, dataset attribution and provenance.
- **`submission.zip`** — source/results distribution excluding raw data, processed row arrays, environment, and downloaded literature. **`MANIFEST.json`** gives checksums for its contents.

Checks actually run:

- All **535** saved successful perturbation witnesses independently refit and replayed.
- Complete one-command reproduction passed; **66** scientific output files identical by SHA-256 across runs.
- Final PDF has only embedded **Type 1** fonts, no missing citations or overfull LaTeX boxes, and meets the 8-page ICML main-text limit.
- All four downloaded raw files have recorded SHA-256 hashes; the three hashes specified by the task match exactly.
- No known access to prohibited literature; only explicitly allowed starter papers and official formatting sources were consulted. No live-platform actions or new annotation requests were made.

The findings are descriptive and conditional: feasible edit witnesses are upper bounds on minimum required edits, and failed searches do not prove robustness. The main comparisons cover crowd votes, expert judgments, a fixed GPT-4 judge, and three sports seasons; the same-item MT contrast controls schedule and count, without establishing judge accuracy or a causal effect of design.
