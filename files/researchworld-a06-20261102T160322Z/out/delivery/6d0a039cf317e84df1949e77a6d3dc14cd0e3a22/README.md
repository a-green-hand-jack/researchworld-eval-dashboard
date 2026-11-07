# What does a tuned system's benchmark score mean?

Optimism of the score reported on the items used to tune a prompt/program, on a synthetic world with exact truth (T0) and on a real model and benchmark (T1: Qwen2.5-1.5B-Instruct on MMLU-Pro, replayed search), and reporting methods M0--M5 to correct it.

## Deliverables
- **Paper**: `paper/main.pdf` (NeurIPS 2026 format, 9 content pages, appendix and checklist after the references); LaTeX sources in `paper/` (`main.tex`, `sections/`, `references.bib`, `checklist.tex`, `neurips_2026.sty`).
- **Code and results**: `code/` (simulation, replay, methods), `results/` (per-replicate outputs, summaries, `SCHEMA.md`, `MANIFEST.md`, `compute.csv`).
- **Figures and tables**: `figures/` and `tables/` (generator scripts next to the outputs; script map in `figures/SCRIPTS.md`, draft captions with the quotable numbers in `figures/CAPTIONS.md`).
- **Reproduction**: `REPRODUCE.md` (environment, commands, data and model versions, known limits).

## Rebuild the paper
```
cd paper && latexmk -pdf main.tex
```
The figures are read from `figures/` and the tables from `tables/`; regenerate them with the commands in `REPRODUCE.md` and `figures/SCRIPTS.md`.

## Not done
No live run of an auto-tuning tool (DSPy/MIPRO) and no 0.5B-model arm; real-LLM results come from one 1.5B model on a fixed 2000-item MMLU-Pro pool (see the paper's Limitations).
