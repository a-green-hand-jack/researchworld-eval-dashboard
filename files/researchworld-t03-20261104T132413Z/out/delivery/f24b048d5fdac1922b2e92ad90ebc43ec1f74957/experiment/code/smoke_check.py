"""Smoke test: a small re-run of one cell must reproduce the delivered raw results bit for bit on the shared instances and runs.

usage (from experiment/):
  python3 code/run_cell.py pima lr --n_inst 5 --R 5 --K_retrain 2 --K_ref 2 --m_ref 2000 --out /tmp/smoke
  python3 code/smoke_check.py /tmp/smoke pima lr
Instances are the first n_inst of the fixed selection and run r of instance i at budget b uses the same seed in every call, so
kernel and permutation attributions of the small run equal the corresponding slice of results/raw.  Prints the largest absolute difference.
"""
import os, sys
import numpy as np

small, ds, m = sys.argv[1:4]
full = os.path.join(os.path.dirname(__file__), "..", "results", "raw")
for ex in ("kernel", "perm"):
    a = np.load(f"{small}/{ds}__{m}__{ex}.npz")["phi"]; b = np.load(f"{full}/{ds}__{m}__{ex}.npz")["phi"]
    n, _, R, _ = a.shape
    print(ex, "max |difference| on", a.shape[:3], "=", float(np.abs(a - b[:n, :, :R]).max()))
