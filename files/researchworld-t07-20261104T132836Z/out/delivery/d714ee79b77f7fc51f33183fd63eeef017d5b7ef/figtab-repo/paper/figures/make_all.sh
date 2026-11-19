#!/bin/bash
# usage: FIGTAB_RESULTS=/path/to/results bash figures/make_all.sh   (about a minute on 1 CPU)
set -e
cd "$(dirname "$0")/../.."
for s in fig_budget fig_paired fig_ess fig_extrap fig_sens; do python3 paper/figures/src/$s.py; done
for t in tab_headline tab_audit tab_sens tab_ablate; do python3 paper/tables/src/$t.py; done
