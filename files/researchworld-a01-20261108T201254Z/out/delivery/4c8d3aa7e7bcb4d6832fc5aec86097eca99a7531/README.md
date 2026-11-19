# Minimum targeted investment to top a multi-task leaderboard

Research paper (NeurIPS 2026 format) and reproduction material. Question: on public multi-task leaderboards (Open LLM Leaderboard `contents`, HELM MMLU v1.13.0), how much targeted investment (raising a target model's scores on chosen sub-datasets) does it take to rank first, and how does that depend on the aggregation rule?

* `paper.pdf` — the paper (9 pages of main text, appendix, filled NeurIPS checklist), built from `paper/` on `main`.
* `paper/` — LaTeX source: `main.tex`, `sections/`, `refs.bib`, the unmodified `neurips_2026.sty`, `checklist.tex`. Build: `cd paper && latexmk -pdf main.tex` (figures and tables are read from `figtab/`). `paper/scripts/check_numbers.py` recomputes the headline numbers quoted in the text from `code/results/analysis/*.csv` (`python3 -I paper/scripts/check_numbers.py code/results/analysis`).
* `code/` — exact solvers, drivers, tests, job scripts, analysis pipeline, compact result files, manifest with SHA-256 and the full reproduction notes: environment, data versions and checksums, seeds, commands, runtimes, claim-to-script map (`code/README.md`).
* `figtab/` — figure and table scripts, the figures (PDF) and LaTeX tables the paper includes, their input hashes (`figtab/INPUTS.md`) and captions (`figtab/CAPTIONS.md`); `figtab/scripts/make_all.sh` rebuilds them from the result files.
* `venue/` — the venue requirements and the official template files.

Reproduction in short: data are fetched by `code/` scripts from public hosts (versions and SHA-256 in `code/README.md` section 4 and Appendix A of the paper); `bash code/reproduce.sh` (offline, CPU only, about 31 minutes) unpacks the per-instance results shipped in `code/results/instances/`, rebuilds `code/results/analysis/` and compares every file with the manifest; `make experiments` in `code/` re-runs every solver job (3.25 recorded solver CPU-hours, 7.7 CPU-hours of scheduler accounting); `figtab/scripts/make_all.sh` rebuilds figures and tables; Appendix A of the paper maps each figure and table to its script.

Provenance: all code, experiments, analyses and the manuscript were produced by AI agents (Claude models in the ResearchWorld harness), with no human authorship.
