# figtab-repo — figures and tables

Presentation position. Scripts in `scripts/` read result files of `experiment-repo` (path passed as argument) and write
vector PDF + PNG into `figures/`, LaTeX tables into `tables/`.

| output | script | inputs (experiment-repo `results/`) | status |
|---|---|---|---|
| `figures/fig_cost_by_rule_helm` (+`_allcaps`) | `scripts/fig_cost_by_rule.py` | `helm_main.csv` | delivered (HELM, 9 rules) |
| `figures/fig_cost_weighted_helm`, `fig_cost_power_helm` | `scripts/fig_cost_by_rule.py` (`--rules`, `--extra`) | `helm_main.csv`, `helm_pow.csv` | delivered (HELM) |
| `figures/fig_cost_vs_rank_helm` | `scripts/fig_rank_rules.py` | `helm_main.csv` | delivered (HELM) |
| `figures/fig_feasibility_helm` | `scripts/fig_feasibility.py` | `helm_main.csv` | delivered (HELM) |
| `figures/fig_k_vs_n_helm` | `scripts/fig_k_vs_n.py` | `helm_tasksub_{ceil,gain10}.csv` | delivered |
| `figures/fig_robustness_helm` (+`_K`) | `scripts/fig_robustness.py` | `helm_main.csv`, `helm_noise_gain10.csv`, `helm_taskboot_gain10.csv` | delivered (HELM) |
| `tables/tab_headline_{helm,ollb,ollb_top500}.tex` | `scripts/table_headline.py` | `tables/main_by_rank.csv`, `tables/vs_mean.csv` | HELM delivered; OLLB ready |
| `tables/tab_validation_{checks,data}.tex` | `scripts/table_validation.py` | `theory_checks.csv`, `../data/processed/manifest.json` | delivered |
| `figures/fig_cost_by_rule_ollb_{pop,top500}` | `scripts/fig_cost_by_rule_ollb.py` | `ollb_*.csv(.gz)` | ready |
| `figures/fig_cost_by_rule_ollb_top500_emp95`, `tables/tab_headline_ollb*_compact.tex` | as above, `--caps ceil,gain10,emp95` | as above | ready (compact variants) |
| `figures/fig_cost_vs_rank_ollb` | `scripts/fig_rank_rules_ollb.py` | `ollb_score.csv.gz`, `ollb_ord_*.csv` | ready |
| `figures/fig_feasibility_ollb` | `scripts/fig_feasibility_ollb.py` | `ollb_top500_*.csv`, `ollb_score.csv.gz`, `ollb_ord_*.csv` | ready |
| `figures/fig_raw_vs_norm_ollb` | `scripts/fig_raw_vs_norm.py` | `tables/raw_vs_norm.csv` | ready |
| `figures/fig_robustness_ollb` | `scripts/fig_robustness.py --dataset ollb` | `ollb_top500_*.csv`, `ollb_noise_gain10.csv` | ready (noise only) |
| `figures/fig_example_plan_helm` | `scripts/fig_example_plan.py` | `example_plan.csv`, `example_plan_summary.csv` | ready (optional, C1/C5) |
| `tables/tab_rule_transfer.tex` | `scripts/table_transfer.py` | `tables/{main_by_rank,vs_mean,rule_order_stability}.csv` | ready (compact main-text table, C1/C5) |

All HELM outputs: `sh scripts/make_helm.sh <experiment-repo>/results`; all OLLB outputs and the headline tables: `sh scripts/make_ollb.sh <experiment-repo>/results`. One script: `python3 scripts/<script>.py <experiment-repo>/results <out-stem>` (see each docstring). Provenance: `<stem>.inputs.json` next to each output; captions and claim per output in `figures/CAPTIONS.md`.
Shared style: `scripts/style.py`, `scripts/common.py`. Commitment: issue #2. Draft-status notes: waiting on venue-repo for column width (figures use 5.5 in text width).
