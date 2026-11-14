# paper-repo

Delivery root for the study *minimum targeted investment to rank first on a multi-task leaderboard, by aggregation rule*.
`paper/main.tex` (NeurIPS 2026 template, unmodified `neurips_2026.sty`, checklist in `paper/checklist.tex`), `paper/refs.bib`, built `paper/main.pdf`.
Figures and tables come from `figures/` and `tables/`; code, data and results from `code/`, `data/`, `results/`; the environment, data versions and
checksums, seeds, commands and run times are in `REPRODUCE.md`.

Build the paper: `cd paper && latexmk -pdf main.tex` (TeX Live, BibTeX; figures are read from `../figures/`, tables from `../tables/`).

## Paper element → generating script
Full commands and input hashes: `figures/MANIFEST.md` (figures, tables), `REPRODUCE.md` (all result files).

| paper element | file | script |
|---|---|---|
| Fig. 1 (OLLB and HELM primary caps) | `figures/F_ollb_primary.pdf`, `F_helm_primary.pdf` | `figures/src/fig_rank_rules.py` |
| Table 1 (rules by rank stratum, same-target ratios) | `tables/T3c_rules_*.tex` | `figures/src/tables_v2.py` |
| Appendix Tables (closed forms vs solvers; feasibility frontier; exceptions at the top) | `tables/T2_theory_check.tex`, `T4_frontier_*.tex`, `T5_exceptions_*.tex` | `figures/src/tables.py`, `tables_v2.py` |
| Appendix Fig. (noise and task-bootstrap ranges) | `figures/F_robust.pdf` | `figures/src/fig_robust.py` |
| Appendix Figs. (oracle cap; cap-scenario grids) | `figures/F_*_oracle.pdf`, `F_*_capgrid.pdf` | `figures/src/fig_rank_rules.py`, `figures/src/fig_cap_grid.py` |
| Appendix Fig. (HELM scaling in n) | `figures/F_helm_scaling.pdf` | `figures/src/fig_scaling.py` |
| Variant numbers (margin, slices, top-500 Copeland, weights) | `results/summary/summary_variants.csv` | `code/summarize_variants.py` |
| Cap bootstrap, fixed-policy survival, common-target scaling, uniform baseline (numbers quoted in the text) | `results/summary/summary_capboot_*.csv`, `results/robust/survival_*.csv`, `results/summary/summary_rob_helm_tasksubcommon_emp99T.csv`, `results/summary/summary_uniform_baseline_*.csv` | `code/capboot.py`, `code/run_survival.py`, `code/run_robust.py`, `code/uniform_baseline.py` |
| Numbers quoted in the text (ratios, frontier, noise ranges) | `results/summary/*.csv`, `results/core_*.csv` | `code/summarize.py`, `code/run_*.py` (see `REPRODUCE.md`) |

## Licence judgement
Neither the Open LLM Leaderboard `contents` dataset nor HELM's MMLU summary declares a licence for its score data (HELM's code is Apache-2.0).
The paper makes no licence claim; the repository redistributes only derived score tables.

## Record of forbidden material (all positions)
The task forbids searching for or reading the published paper on this question and anything citing or discussing it.
- Report position (`paper-repo`): no such search was made and nothing of that kind was encountered. Full texts read: two items of the supplied starter
  literature (Chen et al., arXiv 2603.08371; Colombo et al., arXiv 2202.03799), both permitted, and their text was read to position our work against them.
- Analysis position: see `REPRODUCE.md`, section "Forbidden-material record" (none encountered).
- Context position (`idea-repo`): wiki page `Encounters`: none known; the searches it ran are listed there.

## Status
Draft under review; not a released version. Open items are listed in the commitment issue (`paper-repo`#2) and in the limitations of the paper.
