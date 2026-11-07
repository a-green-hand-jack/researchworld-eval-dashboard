# Stability of pairwise-comparison leaderboards

Delivery root of the study (plan: `world/story-repo` PLAN.md).

| path | content | owner |
|---|---|---|
| `paper/` | LaTeX source (`main.tex`, `refs.bib`, NeurIPS 2026 style) and built `main.pdf` | paper-repo |
| `venue/` | template and checklist material | venue-repo |
| `code/` | analysis code, reproduction README | experiment-repo |
| `results/` | numeric outputs the paper uses | experiment-repo |
| `figures/` | figure/table sources, scripts, outputs | figtab-repo |

Build the paper: `cd paper && latexmk -pdf main.tex`. Raw data are never committed (`data/` is ignored); see the reproduction notes under `code/`.

Reproduce: follow `code/README.md` (about one hour on two CPU cores; pinned public data) to regenerate `results/`; `python3 figures/make_figures.py` writes the figures and tables to `figures/rendered/`; `cd paper && python3 -I make_numbers.py && latexmk -pdf main.tex` regenerates every number in the text (`numbers.tex`) and `paper/main.pdf`. The appendix of the paper maps each figure and table to its result files. Check the format with `python3 -I venue/tools/check_pdf.py paper/main.pdf`.

Status: complete draft (9 content pages, NeurIPS 2026 checklist, LLM-assistance disclosure); pending independent review.
