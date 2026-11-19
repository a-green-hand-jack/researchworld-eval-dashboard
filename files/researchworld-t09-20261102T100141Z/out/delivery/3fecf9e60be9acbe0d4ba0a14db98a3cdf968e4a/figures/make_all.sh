#!/bin/sh
# Regenerates every figure and table from results/ (run from the repository root or figures/).
set -e
cd "$(dirname "$0")"
for f in fig1_headline fig2_bias_sd fig3_h7_diagnostic fig4_coverage fig5_graph_error; do python3 $f.py; done
python3 fig1_headline.py bern0.1
python3 fig1_headline.py cluster0.5
python3 fig_sweeps.py
python3 fig_more.py
cd ../tables && python3 table1_setup.py && python3 table2_failure_modes.py && python3 table3_contrasts.py
