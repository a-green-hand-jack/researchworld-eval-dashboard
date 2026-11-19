"""Stratified instance subset for the R=200 reruns: from the R=20 tidy file of a cell (shipped default KernelSHAP, k=3, x1), take n instances
spread over the distribution of r (lowest, middle, highest third by r, ties broken by z_true), deterministic. Prints a comma-separated list.
usage: python3 scripts/select_r200.py CELL [n=30]"""
import sys, numpy as np, pandas as pd
cell = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
T = pd.read_csv(f"results/tidy_{cell}_R20.csv")
D = T[(T.arm == "kshap_default") & (T.k == 3) & (T.budget == "x1")].sort_values(["r", "z_true", "inst"]).reset_index(drop=True)
pos = np.round(np.linspace(0, len(D) - 1, n)).astype(int)     # equally spaced quantiles of r
print(",".join(str(int(i)) for i in sorted(D.inst.iloc[pos])))
