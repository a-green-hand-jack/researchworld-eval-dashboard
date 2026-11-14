#!/bin/sh
# Regenerate every figure and table from the aggregated results (about 1 minute on 1 CPU).
# fig8, fig10, fig11 and tab6-11 also read <FIGTAB_RESULTS>/../tables/*.csv.
# Env: FIGTAB_RESULTS (default <root>/results/summary), FIGTAB_OUT (default <root>/figures/out), NETGATE_SRC (for tab1; default <root>/code/src).
set -e
cd "$(dirname "$0")"
python3 fig1_strength.py main
python3 fig1_strength.py app
python3 fig2_bias_theory.py
python3 fig3_bias_vs_n.py
python3 fig4_variance_scaling.py
python3 fig5_cluster_design.py
python3 fig5_cluster_design.py linear
python3 fig6_coverage.py
for g in SBM BA Stanford3 ego-Facebook WS ER; do
  python3 fig7_failure_map.py $g relrmse
done
python3 fig7_failure_map.py SBM biasshare
python3 fig8_factor_ranking.py
python3 fig9_gamma_dependence.py
python3 fig10_hajek.py
python3 fig11_crossover_anova.py
python3 make_tables.py
