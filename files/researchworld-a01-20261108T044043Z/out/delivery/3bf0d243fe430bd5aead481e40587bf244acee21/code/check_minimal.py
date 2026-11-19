"""Compare the minimal-path core tables with the shipped ones: every (dataset, cap, rule, target) row of the minimal run must
have the same L1, K, Linf (inf/NaN included) as results/core_*.csv.   Usage: python3 code/check_minimal.py OUT_DIR"""
import sys, numpy as np, pandas as pd
out = sys.argv[1]; bad = 0
for ds in ("ollb", "helm"):
    a = pd.read_csv(f"{out}/core_{ds}.csv"); b = pd.read_csv(f"results/core_{ds}.csv")
    k = ["cap", "rule", "target_idx"]; m = a.merge(b, on=k, suffixes=("", "_ship"), how="left")
    assert m.L1_ship.notna().any(), "no overlapping rows"
    for c in ("L1", "K", "Linf"):
        x, y = m[c].to_numpy(float), m[c + "_ship"].to_numpy(float)
        same = (x == y) | (np.isnan(x) & np.isnan(y)) | (np.abs(x - y) <= 1e-6 * (1 + np.abs(np.where(np.isfinite(y), y, 0))))
        bad += int((~same).sum()); print(f"{ds} {c}: {len(m)} rows, {int((~same).sum())} differ, max|diff| = {np.nanmax(np.where(np.isfinite(x) & np.isfinite(y), np.abs(x - y), 0)):.2e}")
print("MINIMAL PATH MATCHES SHIPPED RESULTS" if bad == 0 else f"MISMATCH: {bad} values differ"); sys.exit(1 if bad else 0)
