#!/usr/bin/env bash
# Rebuild every delivered figure/table from <repo root>/results (or $FIGTAB_EXP) and write figures/PROVENANCE.md.
set -e
cd "$(dirname "$0")"
for f in fig1_main_curves fig2_scree fig3_paired fig4_conditions fig4b_datasets fig5_shift fig6_theory figA1_all_selectors figA2_oracle_leak_cost figA4_cluster figA5_extra_baselines tables; do python3 $f.py; done
python3 provenance.py
