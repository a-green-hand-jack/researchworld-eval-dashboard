"""Numerical verification of closed-form propositions against solver output (results/*.csv written by run_core.py).
Usage: python3 src/theory_checks.py > results/theory_checks.txt
 P1 mean/ceil:   L1 = n*gap + n*eps (when feasible); Linf >= gap + eps (mean of the increments), with equality iff the uniform raise
                 hits no cap, i.e. max_t x_t + gap + eps <= 100
 P2 mean/ceil:   K = minimal k with the k largest headrooms summing to n*gap + n*eps
 P3 min/ceil:    L1 = sum_t max(0, b - x_t), K = #{t: x_t < b}, b = tau + eps = max_j min_t X_jt + eps, Linf = b - min_t x_t
 P4 median(n odd)/ceil: K = (n+1)/2 - #{t: x_t >= b}, b = max_j median_t X_j + eps
 P5 monotonicity: under any rule, tightening the cap never lowers the minimum investment
"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt, scorerules as sr
EPS = 1e-3
def check(name, ok, detail=""): print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

for ds, csv in (("helm", "results/helm_main.csv"), ("ollb", "results/ollb_closed.csv")):
    d = pd.read_csv(csv); d = d[d.cap == "ceil"]
    X, names, tasks, _ = dt.load(ds); M, n = X.shape
    mean = d[d.rule == "mean"].set_index("target_idx").sort_index()
    gap = mean.gap.values; idx = mean.index.values
    pos = gap > 0
    e1 = np.abs(mean.L1.values[pos] - (n * gap[pos] + n * EPS)).max()
    check(f"P1 mean L1 = n(gap+eps) [{ds}, {pos.sum()} targets]", e1 < 1e-6, f"max|err|={e1:.2e}")
    lin = mean.Linf.values[pos]; lb = gap[pos] + EPS; unsat = X[idx[pos]].max(axis=1) + lb <= 100
    check(f"P1 mean Linf >= gap+eps [{ds}]", (lin >= lb - 1e-5).all(), f"min slack={np.min(lin - lb):.2e}")
    check(f"P1 mean Linf = gap+eps when uniform raise unsaturated [{ds}]", np.allclose(lin[unsat], lb[unsat], atol=1e-5),
          f"{unsat.sum()}/{pos.sum()} targets unsaturated")
    # P2
    bad = 0
    for i, g in zip(idx[pos], gap[pos]):
        h = np.sort(100 - X[i])[::-1]; k = np.searchsorted(np.cumsum(h), n * (g + EPS) - 1e-9) + 1
        bad += int(k != mean.K.loc[i])
    check(f"P2 mean K = greedy headroom count [{ds}]", bad == 0, f"mismatches={bad}")
    # P3
    mn = d[d.rule == "min"].set_index("target_idx").sort_index()
    v = X.min(axis=1); bs = np.array([np.delete(v, i).max() for i in range(M)]) + EPS
    ok = v < bs - EPS  # not already first
    L1 = np.array([np.maximum(0, bs[i] - X[i]).sum() for i in range(M)]); K = np.array([(X[i] < bs[i]).sum() for i in range(M)])
    Li = bs - X.min(axis=1)
    m = np.isfinite(mn.L1.values) & (bs <= 100)
    check(f"P3 min L1/K/Linf closed form [{ds}]", np.allclose(mn.L1.values[m], L1[m], atol=1e-6) and (mn.K.values[m] == K[m]).all()
          and np.allclose(mn.Linf.values[m & ok], Li[m & ok], atol=1e-5), f"n={m.sum()}")
    # P4 (n odd only)
    if n % 2:
        md = d[d.rule == "median"].set_index("target_idx").sort_index()
        v = np.median(X, axis=1); b = np.array([np.delete(v, i).max() for i in range(M)]) + EPS
        Kc = np.maximum(0, (n + 1) // 2 - (X >= b[:, None]).sum(axis=1))
        check(f"P4 median K (n odd) [{ds}]", (md.K.values == Kc).all(), f"mismatches={(md.K.values != Kc).sum()}")
# P5 monotone in caps (HELM, nested caps ceil >= front2 >= front0 ; gain20 >= gain10 >= gain5)
d = pd.read_csv("results/helm_main.csv")
for chain in (["ceil", "front2", "front0"], ["gain20", "gain10", "gain5"]):
    for rule in d.rule.unique():
        for meas in ("L1", "K"):
            w = d[d.rule == rule].pivot_table(index="target_idx", columns="cap", values=meas)[chain]
            viol = int(((w.iloc[:, 0] > w.iloc[:, 1] + 1e-6) | (w.iloc[:, 1] > w.iloc[:, 2] + 1e-6)).sum())
            check(f"P5 cap monotonicity {chain} {rule}/{meas}", viol == 0, f"violations={viol}")
