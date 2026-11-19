# Choosing k benchmarks to run and inferring the rest of a new model's scores

Delivery root of the study. Layout (owner in `.forgejo/CODEOWNERS`):

- `paper/` : the paper (`main.tex`, `main.bib`, `main.pdf`, ICLR 2027 style files unmodified), `checklist.md`, `ai_use.md`.
- `code/`, `data/`, `results/`, `REPRODUCE.md` : analysis code, score matrices, results and reproduction notes (environment, data versions, seeds, commands, run times, and which script produces each table and figure).
- `figures/`, `tables/` : the figures and tables of the paper, each with its generator script.

Build the paper: `cd paper && latexmk -pdf main.tex`. The PDF on `main` is built from the sources next to it.
