#!/bin/bash
# Figures, tables and the PDF, from the result tables. Run from the delivery root (paper-repo), where figures/src, tables/ and
# paper/ sit next to code/ and results/; the commands are those of figures/MANIFEST.md (figtab position). Seconds to a few minutes.
set -euo pipefail
R=results
[ -d figures/src ] || { echo "figures/src not found: run from the delivery root (paper-repo)"; exit 1; }
python3 figures/src/fig_rank_rules.py $R ollb figures/F_ollb_primary --caps primary
python3 figures/src/fig_rank_rules.py $R helm figures/F_helm_primary --caps primary
python3 figures/src/fig_rank_rules.py $R ollb figures/F_ollb_oracle --caps ceil
python3 figures/src/fig_rank_rules.py $R helm figures/F_helm_oracle --caps ceil
python3 figures/src/fig_cap_grid.py $R ollb figures/F_ollb_capgrid
python3 figures/src/fig_cap_grid.py $R helm figures/F_helm_capgrid
python3 figures/src/fig_scaling.py $R figures/F_helm_scaling
python3 figures/src/fig_robust.py $R figures/F_robust
python3 figures/src/tables.py $R tables
python3 figures/src/tables_ext.py $R tables
(cd paper && latexmk -pdf -interaction=nonstopmode main.tex)
