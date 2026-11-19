#!/usr/bin/env bash
# Small regenerating check (about a minute, plain python): helm_mmlu, protocol B, 1 rep, K=5, selectors random/gv_fa, methods mean/fa/ridge, k=2,4,8.
# Recomputes per-(selector,method,k) mean target nMSE and compares it with results/check/expected.csv (stored from the delivered code, tolerance 1e-6).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
TMP=$(mktemp -d)
python3 code/run_cv.py --data helm_mmlu --out $TMP/check.parquet --reps 1 --K 5 --seed 0 --ks 2 4 8 --selectors random gv_fa --methods mean fa ridge --n_rand 3 --target_frac 0.25 > /dev/null
python3 - $TMP/check.parquet "$@" <<'PY'
import sys, pandas as pd, numpy as np
d = pd.read_parquet(sys.argv[1])
g = d.groupby(['selector', 'method', 'k']).apply(lambda x: x.sse_z.sum() / x.n_t.sum(), include_groups=False).rename('nmse').reset_index()
exp = 'results/check/expected.csv'
import os
if len(sys.argv) > 2 and sys.argv[2] == '--write':
    g.round(8).to_csv(exp, index=False); print('written', exp); sys.exit()
e = pd.read_csv(exp)
m = g.merge(e, on=['selector', 'method', 'k'], suffixes=('', '_exp'))
bad = (m.nmse - m.nmse_exp).abs() > 1e-6
print(m.round(4).to_string()); print('OK' if len(m) == len(e) and not bad.any() else 'MISMATCH')
sys.exit(0 if len(m) == len(e) and not bad.any() else 1)
PY
