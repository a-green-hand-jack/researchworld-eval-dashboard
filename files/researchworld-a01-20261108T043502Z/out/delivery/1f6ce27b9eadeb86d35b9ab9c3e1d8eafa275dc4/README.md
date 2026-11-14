# paper-repo

Delivery root for "Minimum targeted investment to top a multi-task leaderboard under different aggregation rules".

- `paper/main.tex` (NeurIPS 2026 template, unmodified `neurips_2026.sty`), `paper/refs.bib`, `paper/checklist.tex`, built `paper/main.pdf` (9 content pages, references, appendices A–D, checklist).
- `figures/`, `tables/`: figures and tables with generators (`figures/src/`), sidecars and manifests (`figures/MANIFEST.md`, `tables/MANIFEST.json`).
- `code/`, `data/`, `results/`, `REPRODUCE.md`: analysis code, pinned public data, result files, versions, seeds, run times and the map from result files to scripts.
- Build the paper: `cd paper && latexmk -pdf main.tex` (run twice for cross-references).

Status: final version proposed for review (pull request into `final`).

## Paper figure and table to script

`R` is `results/`; run from the repository root. `sh figures/src/run_all.sh results` regenerates everything below (after the analysis in `REPRODUCE.md` has produced `results/`).

| in the paper | file | command | main input (under `R`) |
|---|---|---|---|
| Figure 1 | `figures/F_ollb_primary`, `F_helm_primary` | `python3 -I figures/src/fig_rank_rules.py R ollb figures/F_ollb_primary --caps primary` and the same with `helm`, `F_helm_primary` | `core_ollb.csv`, `core_helm.csv` |
| Figure 2 | `figures/F_helm_scaling` | `python3 -I figures/src/fig_scaling.py R figures/F_helm_scaling` | `summary/summary_rob_helm_tasksub_emp99T.csv` |
| Figure 3 | `figures/F_robust` | `python3 -I figures/src/fig_robust.py R figures/F_robust noise` | `summary/summary_rob_*_noise_*.csv`, `core_*.csv` |
| Figure 4 (appendix) | `figures/F_ollb_oracle`, `F_helm_oracle` | `fig_rank_rules.py R <ollb or helm> figures/F_<ds>_oracle --caps ceil` | `core_*.csv` (cap `ceil`) |
| Figure 5 (appendix) | `figures/F_ollb_capgrid`, `F_helm_capgrid` | `fig_cap_grid.py R <ollb or helm> figures/F_<ds>_capgrid` | `core_*.csv` (all caps) |
| Figure 6 (appendix) | `figures/F_robust_boot` | `fig_robust.py R figures/F_robust_boot taskboot` | `summary/summary_rob_*_taskboot_*.csv`, `core_*.csv` |
| Table 1 | `tables/T4_frontier_{ollb,helm}.tex` | `python3 -I figures/src/tables.py R tables` | `core_*.csv` |
| Table 2 | `tables/T3_rules_ollb_emp99.tex`, `T3_rules_helm_emp99T.tex` | same | `core_*.csv` |
| Table 3 (appendix) | `tables/T2_theory_check.tex` | same | `theory_check.csv` |
| Table 4 (appendix) | `tables/T4b_frontier_ci_{ollb,helm}.tex` | same | `summary/frontier_*.csv`, `core_*.csv` |
| Table 5 (appendix) | `tables/T6_paired_{ollb,helm}.tex` | same | `summary/paired_*.csv` |
| Table 6 (appendix) | `tables/T5_variants_{ollb,helm}.tex` | same | `summary/summary_variants.csv` |

Inputs, hashes and the claim each output supports are in `figures/MANIFEST.md`, the `.json` sidecars and `tables/MANIFEST.json`; the ids T2–T6, F1–F5 there are the plan's ids, not the paper's numbers (the table above is the map).

Material about the published study behind the question: none was searched for, read or encountered (statement in `REPRODUCE.md`).
