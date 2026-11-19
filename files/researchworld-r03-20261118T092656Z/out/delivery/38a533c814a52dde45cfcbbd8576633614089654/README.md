# paper-repo

The delivered paper: *Which Benchmarks, and How Many? Cold-Start Benchmark Selection as Experimental Design on Leaderboard Score Matrices* (NeurIPS 2026 format).

| Path | Content |
|---|---|
| `paper/` | LaTeX sources: `main.tex`, `sections/`, `tables/`, `figures/`, `references.bib`, `checklist.tex`. Built by the command in `.forgejo/document.json` (`cd paper && latexmk -pdf main.tex`). |
| `code/` | The analysis: method code (`src/`), one driver per experiment (`exp/`), closed-form tests (`tests/`), the pinned data of the embedding matrices (`data/`), result tables (`results/`) and the files the figures and tables are drawn from (`figdata/`). `code/README.md` gives the environment, seeds, commands and runtimes. |
| `figtab/` | Scripts that draw the figures and tables of the paper from `code/figdata/`; `figtab/REPRODUCE.md` gives the commands. |

The data of the five generative-LLM matrices are not redistributed (the licences are unstated, see Appendix B of the paper); `code/data/SOURCES.md` pins the public sources and `code/src/build_*.py` rebuilds them.

## Reproduction: script to figure or table

Figures and tables: from `figtab/`, run `FIGDATA=../code/figdata FIGOUT=<dir> python3 <script>`; the PDFs and `.tex` files are those in `paper/figures` and `paper/tables`.
Figure and table numbers are those of the paper.

| Paper item | Script (`figtab/`) | Files read (`code/figdata/`) |
|---|---|---|
| Fig. 1 error against k on MTEB-A1 | `fig_f1.py` | `curves.csv`, `references.csv` |
| Fig. 2 forecast against measurement | `fig_f2.py` | `synthetic_grid.csv`, `curves.csv`, `references.csv` |
| Table 1 primary comparisons on MTEB-A1 and A2 | `tab_t2.py` | `paired.csv` |
| Fig. 3 inference methods and the selection gain | `fig_f6.py` | `h3_imputers_paired.csv`, `h3_selector_x_inference_paired.csv` |
| Fig. 4 benchmarks needed against latent share | `fig_f4.py` | `kstar.csv`, `real_conditions.csv` |
| Table 2 matrices (Appendix B) | `tab_t1.py` | `data_table.csv`, `real_conditions.csv` |
| Table 3 sources and licences (Appendix B) | `tab_t1.py` | `data_table.csv` |
| Table 4 leakage ablation (Appendix C) | typed in `paper/sections/appendix.tex` | `code/results/E2/leak_paired.csv` (`exp/analyze_e2.py`) |
| Table 5 primary family on the MTEB matrices (Appendix D) | `tab_t2.py` | `paired.csv`, `primary_B.csv` |
| Fig. 5 groups of tasks and unequal costs (Appendix E) | `fig_f3.py` | `cost.csv`, `group_paired.csv`, `cost_paired.csv` |
| Fig. 6 simple inference rules (Appendix F) | `fig_f6_rules.py` | `inference_ablation.csv` |
| Table 6 generative-LLM matrices (Appendix D) | `tab_t3.py` | `paired.csv` |
| Table 7, Table 8 unseen organisations and simple alternatives (Appendix H) | typed in `paper/sections/appendix.tex` | `code/results/FAM/paired.csv`, `curves.csv` (`exp/analyze_fam.py`, `exp/fam_tables.py`; full intervals in `code/results/FAM/TABLES.md`) |
| Fig. 7 shift (Appendix I) | `fig_f5.py` | `shift.csv`, `kstar.csv` |

Result files: `code/exp/export_figtab.py` writes `code/figdata/*.csv` from the raw per-fold records in `code/results/`; the commands that produce the records, one per experiment, are tabulated in `code/README.md` (synthetic matrices `e1_synth.py`, cross-validation `run_cv.py`, leakage and groups `e2.sh`, shift `e6.sh`, other matrices `e7.sh`, history size `e8.sh`, inference methods `e_h3.sh`, optimum and stability `e_opt.py`, setting B `loop.sh B`).
The raw records (about 380 MB) are not part of the delivery; `code/results/<matrix>/per_model.parquet` holds the per-model means from which the paired bootstrap is recomputed with `python3 -I exp/analyze_main.py <matrix>` (run from `code/`).
All CPU; the runtimes of each step are in `code/README.md` and Appendix J.

## Release

Versions of the paper are published as releases of `world/result`.
