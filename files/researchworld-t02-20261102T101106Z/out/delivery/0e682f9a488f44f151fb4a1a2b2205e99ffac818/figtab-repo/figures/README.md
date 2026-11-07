# figtab-repo — figures and tables

`figures/src/make_all.py` regenerates every figure (`figures/*.pdf|png` + `*.caption.txt`) and table (`figures/tables/*.tex|csv`)
from `experiment-repo`'s `results/*_{runs,cells}.csv`, `_stats.json` and `experiments/runs/<sweep>/*.json`
(paths via env `FIGTAB_RESULTS`, `FIGTAB_RUNS`; default: `results/` and `experiments/runs/` of the paper-repo root, else a sibling checkout `../experiment-repo`). Run: `cd figures/src && python make_all.py`. No number is typed by hand.

| output | script | plan item / claim |
|---|---|---|
| `width_trends_main` | `fig_width_trends.py` | F1: t_gen (primary), t_fit, D vs width, censoring kept, 100k-step re-runs overlaid in (a) (A1) |
| `curves_main`, `grok_survival_main`, `regimes_main` | `fig_curves.py`, `fig_grok_survival.py`, `fig_regimes.py` | F2: shape of the delay, KM survival, outcome regimes |
| `mechanism` | `fig_mechanism.py` | F3: t_fit and D vs norm at fit, init-scale runs (A2) |
| `wd_alpha` | `fig_wd_alpha.py` | F4: D vs weight decay (A2 slope -1 reference), t_gen vs init scale |
| `frac` | `fig_frac.py` | F5: grok fraction and t_gen vs training fraction per width (A3) |
| `scope`, `t2_scope` | `fig_scope.py`, `tables.py` | robustness: MLP, multiplication, lr rescaling, fixed split |
| `budget` | `fig_budget.py` | late-not-never check: paired seeds under 30k vs 100k ceilings; forest of the A1 AFT slope under budget/threshold/width/architecture variants |
| `t1_main`, `t3_trend`, `t4_mechanism`, `t5_wd_alpha` | `tables.py` | T1 per-cell table; T3 A1 trend tests and sensitivity rows with the verdicts written in the stats files; T4 A2(ii) regressions, total-L2 and per-parameter-RMS norm side by side with verdicts; T5 A2(i) wd slope and A2(iii) init-scale effect with verdicts (`t4_mechanism_all.csv`: every coefficient, incl. the outcome-contaminated norm-at-t_gen models) |

Figure width is 5.5 in (NeurIPS text width) and tables are `\resizebox{\linewidth}` wrapped. Requires numpy, pandas, matplotlib (versions: see `ht-role environment` lock of the world). All delivered figures and tables come from the complete real runs. Only Kaplan-Meier curves are computed here; medians, CIs, slopes and tests are read from `experiment-repo`'s stats files.
