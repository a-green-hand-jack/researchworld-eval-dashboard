# Minimum targeted investment to top a multi-task leaderboard, by aggregation rule

Delivery root of the study. Question: what targeted investment (raising one target model's scores on chosen sub-datasets) makes it rank first on a public multi-task leaderboard, and how does this depend on the aggregation rule?

| path | content | owner |
|---|---|---|
| `paper/main.tex`, `paper/sections/`, `paper/refs.bib`, `paper/main.pdf` | the paper (ICLR 2027 template, `paper/template/`); build with `paper/build.sh` (pdflatex + bibtex) | paper-repo |
| `analysis/` | data pinning, exact solvers, experiments, result CSVs, summary tables, tests; **start with `analysis/REPRODUCE.md`** (environment, data versions and SHA-256, seeds, commands, expected run time, script -> result map) | experiment-repo |
| `figures/`, `tables/` | the paper's figures and tables, with generator scripts under `figures/scripts/` and a per-output provenance file listing input hashes | figtab-repo |
| `paper/template/` | unmodified official ICLR 2027 style files and `VENUE.md` (requirements, sources, checksums) | venue-repo |

Reproduction in short: `cd analysis && ./reproduce.sh data && ./reproduce.sh test && ./reproduce.sh <target>` (see `REPRODUCE.md` for the target list and timings), then the generators in `figures/scripts/`, then `paper/build.sh`.
The script that produces each figure and table of the paper is listed in the appendix of the paper (Table "Provenance") and in `figtab-repo`'s README.

Data: Open LLM Leaderboard `contents` (commit `9c09a7cae43334062a82cb164f2ef255013dafa2`) and `results` (commit `aa81ecc38fdc5708254b833923368970efdf5ef5`); HELM MMLU release v1.13.0. Both public; licences undeclared, reasoning in `analysis/REPRODUCE.md` section 2.
