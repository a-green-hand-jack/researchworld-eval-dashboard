# Minimum targeted investment on public multi-task leaderboards

Delivery root of `paper-repo`.

- `paper.pdf` — the manuscript (ICLR 2027 template, double-blind), built from `paper/` by `bash build.sh` (TeX Live, `latexmk`). `paper/` holds the LaTeX sources; the style files are the unmodified official ones (checked against `venue/iclr2027.SHA256`).
- `analysis/` — code, results and reproduction notes (start at `analysis/README.md`, `analysis/docs/REPRODUCTION.md`, `analysis/docs/RUN_STATE.md`).
- `figures/`, `tables/`, `figtab/` — rendered figures and tables, each with a provenance JSON; `figtab/README.md` maps script, inputs and claim.
- `venue/` — template files and the format checker: `python3 venue/tools/check_venue.py paper.pdf paper/ --style-dir venue/iclr2027`.

Every number in the paper comes from `analysis/results/` (checked against the CSVs named in the captions). Unfinished work is stated in the paper and in `analysis/docs/RUN_STATE.md`.

Layout of `paper.pdf`: main text pages 1–9 (abstract to reproducibility statement), references from page 9, then the AI-use statement and appendices A (AI use), B (further results: figures and tables including the top-500 ordinal frame, task-count, noise, margin, rival-frame and Borda-audit results, with the text of the sensitivity checks), C (proofs of the exact results), D (data provenance, licences, full SHA-256 values, reserved-material log) and E (reproduction commands and measured times of the completed clean recomputations). `paper.pdf` is rebuilt from `paper/`, `figures/` and `tables/` as merged on `main`; the venue checker passes at that state.
