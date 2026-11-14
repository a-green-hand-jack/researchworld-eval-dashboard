# Minimum targeted investment to top a multi-task leaderboard

Paper (ICLR 2027 submission format, anonymous): `paper.pdf`, source in `paper/` (`paper/build.sh` builds it with the unmodified style files in `venue/iclr2027/`; `python3 -I venue/check_format.py paper/main.pdf paper/main.tex` runs the venue gate).

| path | content | owner |
|---|---|---|
| `paper/`, `paper.pdf` | LaTeX source, bibliography, built PDF | paper-repo |
| `code/` | solvers, data layer, result CSVs, `code/REPRODUCE.md` (environment, data checksums, seeds, commands, runtimes, script -> output map) | experiment-repo |
| `figures/`, `tables/`, `figtab/` | figures and tables with captions, provenance and generators (`figtab/README.md`) | figtab-repo |
| `venue/` | ICLR 2027 template, format checker, venue record | venue-repo |

Status: see the paper's limitations section for what is not completed in the current version.

`paper.pdf` is rebuilt from `paper/`, `figures/` and `tables/` as merged on `main`; after changing any of them run `paper/build.sh`, which copies the result to `paper.pdf`.
