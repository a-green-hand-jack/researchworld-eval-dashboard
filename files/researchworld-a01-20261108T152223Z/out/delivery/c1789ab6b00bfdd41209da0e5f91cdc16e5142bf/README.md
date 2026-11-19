# How much targeted investment does it take to top a multi-task leaderboard?

Delivery of the study: the paper (`paper/main.pdf`, LaTeX source `paper/main.tex`), the analysis code and result files (`code/`), the figures and tables (`figures/`, `tables/`) and the venue material (`venue/`).

## Layout
| Path | Content |
|---|---|
| `paper/` | LaTeX source of the paper in the ICLR 2027 template (`main.tex`, `sections/`, `refs.bib`), the built `main.pdf`, `check_numbers.py` |
| `code/` | solvers, data, result grids and tables; **`code/REPRODUCE.md`** has the environment, data checksums, seeds, one command per result and runtimes |
| `figures/`, `tables/` | every figure and table of the paper, with the script that built it (`figures/scripts`) and `*.inputs.json` (script, revision, SHA-256 of each input) |
| `venue/` | format requirements, checklist and `check_format.py` |

## Build the paper
The ICLR 2027 style files are used unmodified from `venue/iclr2027/`.
```
cd paper
export TEXINPUTS=../venue/iclr2027//: BSTINPUTS=../venue/iclr2027//:
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex     # or: make
python3 -I ../venue/check_format.py main.pdf .                    # page limit and anonymity check
python3 -I check_numbers.py                                       # quoted numbers against code/results/tables
```

## Reproduce the results
See `code/REPRODUCE.md`: `sh run.sh data tests theory helm_main helm_pow ...` produces the result CSVs in `code/results/`, `python3 src/analyze.py` the tables in `code/results/tables/`. Figures and tables are rebuilt by the scripts in `figures/scripts` (`figures/CAPTIONS.md` states the claim each output supports). The whole analysis is about 15 hours of job time on two CPUs each (more than the 4 CPU-hours planned; the OLLB rank-rule grids are sampled for that reason, see the paper's limitations and `code/REPRODUCE.md`); the HELM results and the theory checks need about 75 minutes.

## Where each result in the paper comes from
| Paper | Result files / tables | Figure or table |
|---|---|---|
| Sec. 4.2 cost by rule | `helm_main.csv`; `main_by_rank.csv`, `vs_mean.csv`, `rule_order_stability.csv` | Fig. 1, Table 1 (`fig_cost_by_rule_helm`, `tab_headline_helm`) |
| Sec. 4.3 cost against rank | `main_by_rank.csv`, `rank_scaling.csv`, `cost_vs_gap.csv` | Fig. 2 (`fig_cost_vs_rank_helm`) |
| Sec. 4.4 feasibility | `main_by_rank.csv` (`infeasible`, `n_feasible`) | Fig. 3 (`fig_feasibility_helm`) |
| Sec. 4.5 K against n | `helm_tasksub_*.csv`; `tasksub_summary.csv` | Fig. 4 (`fig_k_vs_n_helm`) |
| Sec. 4.6 robustness | `helm_noise_gain10.csv`, `helm_taskboot_gain10.csv`; `noise_summary_helm.csv`, `taskboot_summary_helm.csv` | Appendix figures (`fig_robustness_helm*`) |
| Appendix: solver validation | `theory_checks.csv`, `code/tests` | `tab_validation_*` |

`paper/check_numbers.py` recomputes the numbers quoted in the text of the HELM sections from the tables and reports any disagreement.

## Reproduction notes on the rules of the task
Only the references listed in `paper/refs.bib` were read. No contact with the barred paper (or anything citing it) is known to the paper-repo role; any accidental contact would be logged in `code/REPRODUCE.md`.
