#!/bin/bash
# usage: analysis/run_all.sh RAW_DIR OUT_DIR
# Runs the whole analysis on the cells of RAW_DIR that are complete (ref, kernel, perm, retrain, and bg when d<=12).
# Incomplete cells and log-odds sensitivity cells (*_logit) are left out of the main tables.
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RAW=$1; OUT=$2
cd "$(dirname "$0")/.."
STAGE=$(mktemp -d)
python3 - "$RAW" "$STAGE" <<'PY'
import sys, os, glob, json, shutil, numpy as np
raw, stage = sys.argv[1:3]
for f in sorted(glob.glob(f"{raw}/*__ref.npz")):
    tag = os.path.basename(f)[:-len("__ref.npz")]
    if "_logit__" in tag: continue
    d = len(json.loads(str(np.load(f, allow_pickle=True)["meta"]))["names"])
    need = ["ref", "kernel", "perm", "retrain"] + (["bg"] if d <= 12 else [])
    if all(os.path.exists(f"{raw}/{tag}__{s}.npz") for s in need):
        for s in need + ["kernell1", "refcheck", "bgd"]:
            p = f"{raw}/{tag}__{s}.npz"
            if os.path.exists(p): os.symlink(os.path.abspath(p), f"{stage}/{tag}__{s}.npz")
        print("complete:", tag, flush=True)
    else:
        print("incomplete, skipped:", tag, flush=True)
PY
mkdir -p "$OUT"
python3 analysis/build_tables.py "$STAGE" "$OUT"
python3 analysis/summarize.py "$OUT"
python3 analysis/compute_matched.py "$STAGE" "$OUT"
python3 analysis/diagnostic.py "$STAGE" "$OUT"
python3 analysis/export_long.py "$STAGE" "${OUT%/tables}/long"
python3 analysis/ties.py "$STAGE" "$OUT"
python3 analysis/retrain_notes.py "$RAW" "$OUT"
python3 analysis/retrain_sensitivity.py "$RAW" "$OUT"
python3 analysis/seed_correlation.py "$STAGE" "$OUT"
[ -d results/logs ] && python3 analysis/runtime_from_logs.py results/logs "$OUT"
python3 analysis/german_checks.py "$RAW" "$OUT"
python3 analysis/logit_sensitivity.py "$RAW" "$OUT"
echo "HUTIAN_WAKE: analysis finished: $OUT"
