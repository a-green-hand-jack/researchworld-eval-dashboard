#!/bin/sh
# Regenerate every figure and table from the analysis results. Usage (repository root): sh figures/src/run_all.sh RESULTS_DIR
set -e
R=$1
python3 -I figures/src/fig_rank_rules.py $R ollb figures/F_ollb_primary --caps primary
python3 -I figures/src/fig_rank_rules.py $R helm figures/F_helm_primary --caps primary
python3 -I figures/src/fig_rank_rules.py $R ollb figures/F_ollb_oracle --caps ceil
python3 -I figures/src/fig_rank_rules.py $R helm figures/F_helm_oracle --caps ceil
python3 -I figures/src/fig_cap_grid.py $R ollb figures/F_ollb_capgrid
python3 -I figures/src/fig_cap_grid.py $R helm figures/F_helm_capgrid
python3 -I figures/src/fig_scaling.py $R figures/F_helm_scaling
python3 -I figures/src/fig_robust.py $R figures/F_robust noise
python3 -I figures/src/fig_robust.py $R figures/F_robust_boot taskboot
python3 -I figures/src/tables.py $R tables
