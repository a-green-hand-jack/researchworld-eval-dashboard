#!/bin/sh
# Rebuild every figure and table from the analysis results. Usage: figures/src/make_all.sh RESULTS_DIR   (run from the repository root)
set -e; R=${1:?results dir}; S=figures/src
python3 $S/fig_rank_rules.py $R ollb figures/F_ollb_primary --caps primary
python3 $S/fig_rank_rules.py $R helm figures/F_helm_primary --caps primary
python3 $S/fig_rank_rules.py $R ollb figures/F_ollb_oracle --caps ceil
python3 $S/fig_rank_rules.py $R helm figures/F_helm_oracle --caps ceil
python3 $S/fig_cap_grid.py $R ollb figures/F_ollb_capgrid
python3 $S/fig_cap_grid.py $R helm figures/F_helm_capgrid
python3 $S/fig_scaling.py $R figures/F_helm_scaling
python3 $S/fig_robust.py $R figures/F_robust
python3 $S/fig_robust.py $R figures/F_robust_rank --set rank
python3 $S/tables.py $R tables
