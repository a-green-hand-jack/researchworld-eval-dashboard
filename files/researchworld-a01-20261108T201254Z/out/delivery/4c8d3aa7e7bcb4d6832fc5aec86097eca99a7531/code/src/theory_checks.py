"""Numerical verification of the closed-form statements of the paper against solver output.
Usage: python3 src/theory_checks.py       -> results/theory_pairs.csv (one row per instance: closed-form prediction vs solver output),
                                             results/theory_checks.txt (PASS/FAIL summary)
The predictions are coded from the closed forms alone (no call into mti.scorerules), from X, the cap vector and the rival frontier:
  b = tau + eps, tau = best RIVAL value of the rule; target value v_i <= tau (instances that are not already first).
  mean   (P1/P3): feasible iff sum(cap) >= n*b;  L1* = n*b - sum(x);  K* = fewest tasks, taken by decreasing headroom cap-x, whose headroom covers n*b - sum(x)
  min    (P5)   : feasible iff cap_t >= b on every task with x_t < b;  L1* = sum_t (b-x_t)+;  K* = #{t : x_t < b}
  median (P6, odd n only: HELM n=57): need m=(n+1)/2 tasks with y_t >= b: K* = max(0, m - #{x_t >= b}); the cheapest
           deficits (b-x_t) among tasks with cap_t >= b are raised; feasible iff enough such tasks; L1* = sum of the K* smallest deficits
P2: Linf* <= L1* <= n*Linf* and 1 <= K* <= n for every instance with finite values.   P4: task-subset scaling (mean): L1* = n*(gap_own+eps).
"""
import sys, glob, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
R = pathlib.Path(__file__).resolve().parents[1] / "results"; EPS = 1e-3
lines = []
def rep(name, ok, detail):
    lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}"); print(lines[-1])

def predict(rule, x, cap, tau, n):
    b = tau + EPS; dx = np.maximum(b - x, 0)
    if rule == "mean":
        need = n * b - x.sum()
        if (cap - x).sum() < need - 1e-9: return np.inf, np.inf
        h = np.sort(np.maximum(cap - x, 0))[::-1]; return need, int(np.searchsorted(np.cumsum(h), need - 1e-9) + 1)
    if rule == "min":
        low = x < b
        return (np.inf, np.inf) if (cap[low] < b - 1e-12).any() else (dx.sum(), int(low.sum()))
    if rule == "median":
        m = (n + 1) // 2; have = int((x >= b).sum()); k = max(0, m - have)
        cand = np.sort(dx[(x < b) & (cap >= b - 1e-12)])
        return (np.inf, np.inf) if len(cand) < k else (cand[:k].sum(), k)
    raise KeyError(rule)

pairs = []
for ds, files in (("ollb", sorted(glob.glob(str(R / "ollb_score_*.csv")))), ("helm", [str(R / "helm_main.csv")])):
    X, names, tasks, _ = dt.load(ds); M, n = X.shape
    rules = ("mean", "min") + (("median",) if n % 2 else ())
    val = {"mean": X.mean(1), "min": X.min(1), "median": np.median(X, 1)}
    for f in files:
        d = pd.read_csv(f); d = d[d.dataset == ds]
        for rule in rules:
            for cap_name, s in d[d.rule == rule].groupby("cap"):
                v = val[rule]; order = np.argsort(-v, kind="stable"); best, second = v[order[0]], v[order[1]]
                for r in s.itertuples():
                    i = r.target_idx; tau = second if i == order[0] else best
                    if v[i] > tau or r.censored == 1: continue
                    pL, pK = predict(rule, X[i], dt.make_cap(cap_name, X, i), tau, n)
                    pairs.append(dict(dataset=ds, cap=cap_name, rule=rule, target=r.target, n_tasks=n, pred_L1=pL, solver_L1=r.L1, pred_K=pK, solver_K=r.K))
P = pd.DataFrame(pairs)
both_inf = np.isinf(P.pred_L1) & np.isinf(P.solver_L1)
P["abs_err_L1"] = np.where(both_inf, 0.0, (P.pred_L1 - P.solver_L1).abs())
P["feasible_agrees"] = np.isinf(P.pred_L1) == np.isinf(P.solver_L1)
P["K_agrees"] = (np.isinf(P.pred_K) & np.isinf(P.solver_K)) | (P.pred_K == P.solver_K)
P.to_csv(R / "theory_pairs.csv", index=False)
for (ds, rule), g in P.groupby(["dataset", "rule"]):
    fin = g[np.isfinite(g.pred_L1)]
    rep(f"closed form L1 = prediction [{ds}, {rule}, {g.cap.nunique()} caps, {len(g)} instances, {len(fin)} feasible]",
        bool(g.feasible_agrees.all()) and (fin.abs_err_L1.max() < 1e-6 if len(fin) else True),
        f"feasibility agrees on {g.feasible_agrees.mean():.4%}; max |L1 pred - solver| = {fin.abs_err_L1.max():.2e}")
    rep(f"closed form K = prediction [{ds}, {rule}]", bool(g.K_agrees.all()), f"K agrees on {g.K_agrees.mean():.4%} of {len(g)}")

for ds, files in (("ollb", sorted(glob.glob(str(R / "ollb_score_*.csv")) + glob.glob(str(R / "ollb_ordinal_*.csv")) + glob.glob(str(R / "ollb_plurality_*.csv")))), ("helm", [str(R / "helm_main.csv")])):
    n = dt.load(ds)[0].shape[1]; e = pd.concat([pd.read_csv(f) for f in files]); e = e[e.dataset == ds]
    e = e[np.isfinite(e.L1) & np.isfinite(e.K) & np.isfinite(e.Linf) & (e.L1 > 0)]
    ok = (e.Linf <= e.L1 + 1e-6) & (e.L1 <= n * e.Linf + 1e-6) & (e.K >= 1) & (e.K <= n)
    rep(f"P2 Linf <= L1 <= n*Linf, 1<=K<=n [{ds}, all rules/caps]", bool(ok.all()), f"{int(ok.sum())}/{len(ok)} instances; violators by rule: {e[~ok].rule.value_counts().to_dict()}")
p = R / "helm_tasksub_ceil.csv"
if p.exists():
    d = pd.read_csv(p); m = d[(d.rule == "mean") & (d.gap_own > 0) & np.isfinite(d.L1)]
    r = (m.L1 / (m.n * (m.gap_own + EPS))).describe()
    rep("P4 task-subset scaling, mean: L1 = n(gap+eps)", abs(r["max"] - 1) < 1e-6 and abs(r["min"] - 1) < 1e-6, f"ratio min {r['min']:.6f} max {r['max']:.6f} over {int(r['count'])} draws")
(R / "theory_checks.txt").write_text("\n".join(lines) + "\n")
