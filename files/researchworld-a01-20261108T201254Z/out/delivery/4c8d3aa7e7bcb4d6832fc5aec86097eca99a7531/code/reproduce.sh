#!/bin/bash
# Offline, CPU-only reproduction from the delivered tree (no `make` needed; same steps as `make reproduce`).
#   unpack the per-instance results -> regenerate the one large file (ollb_powmeans_weighted.csv) -> analysis -> theory checks -> compare with MANIFEST
# Prints the elapsed wall time of each step. Usage: bash reproduce.sh      (python3 with the packages of requirements.txt)
set -e; cd "$(dirname "$0")"; PY=${PY:-python3}
mkdir -p logs   # logs/ is not tracked (the root .gitignore ignores *.log); jobs/_run.sh also creates it
step() { local t=$SECONDS; echo "== $1"; shift; "$@"; echo "   $(( SECONDS - t )) s"; }
step "unpack per-instance results" $PY src/pack_instances.py unpack
step "regenerate ollb_powmeans_weighted.csv (OLLB, 4496 targets, 8 caps, p-means and 20 weighted means)" bash jobs/ollb_powmeans_weighted.sh
step "analysis (bootstrap B=1000, seed 0)" $PY src/analyze.py --B 1000 --seed 0
step "robustness summaries" $PY src/analyze_robust.py --B 1000 --seed 0
step "rank-dependence fits (#6.2)" $PY src/analyze_fits.py
step "cap composition (#6.1)" $PY src/analyze_capcomp.py
step "duplicate-name rule (#6.3a)" $PY src/analyze_dup_rule.py
step "score-cap defence (#6.4b)" $PY src/score_cap_defence.py
step "closed-form theory checks" $PY src/theory_checks.py
step "compare every file with results/MANIFEST.json" $PY src/verify_manifest.py
echo "total $SECONDS s wall"
