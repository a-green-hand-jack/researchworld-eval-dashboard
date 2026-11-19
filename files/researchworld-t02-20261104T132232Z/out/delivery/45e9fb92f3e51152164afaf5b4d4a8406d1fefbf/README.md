# Model size and delayed generalisation (grokking) on modular arithmetic

Anonymous submission-format paper (ICLR 2027 template) and artefacts.

- `paper/main.tex`, `paper/references.bib`: paper source (official ICLR 2027 style files, unmodified, in `paper/`); `paper.pdf`: the built paper. Build: `cd paper && latexmk -pdf main.tex` (figures and tables are read from `../figures` and `../tables`).
- `code/`: training harness, sweeps, collection and statistics; `results/`: per-run results, tables, `results/verdicts.md` (verdict per prediction P1-P7 with sources).
- `figures/`, `tables/`: generators and outputs; `figures/README.md` maps each figure and table to its script and inputs.
- `REPRODUCE.md`: environment, seeds, commands, runtimes, deviations and the log of accidental encounters with the withheld paper (none).
- `venue/`: venue rules, official template and the format checker (`python3 venue/tools/check_venue.py --pdf paper.pdf --src <dir containing paper/ and figures/>`).
