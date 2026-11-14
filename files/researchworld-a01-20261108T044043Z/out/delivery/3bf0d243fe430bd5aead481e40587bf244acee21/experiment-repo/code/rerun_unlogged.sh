#!/bin/bash
# Re-runs the variant steps whose first runs left no timing log (Dirichlet weights, sigma-unit costs) under code/timed.py and checks
# the outputs against the shipped files.  Writes to $OUT (default /tmp/rerun_unlogged); times go to results/runtime_unlogged_steps.csv.
set -euo pipefail
OUT=${OUT:-/tmp/rerun_unlogged}; mkdir -p $OUT; T="python3 code/timed.py"; TC=results/runtime_unlogged_steps.csv; rm -f $TC
$T weights_ollb_emp99 $TC -- python3 code/run_weights.py ollb emp99 $OUT/weights_ollb_emp99.csv
$T weights_helm_emp99T $TC -- python3 code/run_weights.py helm emp99T $OUT/weights_helm_emp99T.csv --strata 2,3,5,10,20,40
for c in emp99 ceil; do $T zcost_ollb_$c $TC -- python3 code/run_zcost.py ollb $c $OUT/zcost_ollb_$c.csv; done
for c in emp99T ceil; do $T zcost_helm_$c $TC -- python3 code/run_zcost.py helm $c $OUT/zcost_helm_$c.csv; done
python3 - "$OUT" <<'PY'
import sys, numpy as np, pandas as pd, glob, os
bad = 0
for f in sorted(glob.glob(sys.argv[1] + "/*.csv")):
    a = pd.read_csv(f); b = pd.read_csv("results/variants/" + os.path.basename(f))
    num = [c for c in a.columns if a[c].dtype.kind == "f"]
    same = a.shape == b.shape and all(np.allclose(a[c].to_numpy(float), b[c].to_numpy(float), rtol=1e-6, atol=1e-6, equal_nan=True) for c in num)
    print(os.path.basename(f), "identical to shipped" if same else "DIFFERS"); bad += not same
sys.exit(bad)
PY
