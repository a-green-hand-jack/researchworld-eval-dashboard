"""Cap-saturated screen and settled feasibility of the OLLB top-500 Copeland rows (emp99). Copeland is monotone in the target's scores, so a target that is not
the strict Copeland winner with every task at its cap cannot become first (certain infeasibility), and one that wins there is feasible. The MILP is solved
separately for each cost (L1, K, Linf) under a 120 s limit and a censored solve (NaN) says nothing about feasibility: feasibility is settled when any of the
three costs has a finite value (a feasible solution exists), or infinite (proved infeasible), or when the saturated vector loses. L1 censoring is a statement about
the minimum L1 cost only. Usage: python3 code/copeland_screen.py ->
  results/variants/copeland_top500_screen.csv (per target: l1_status, K_status, Linf_status, wins_at_saturation, feasibility, feasibility_basis)
  results/variants/copeland_top500_feasibility.csv (per rank stratum: settled feasibility and the separate L1 outcomes)"""
import sys, pathlib
import numpy as np, pandas as pd
root = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(root / "code"))
import mti.data as dt, mti.ordinal as od
X, names, _, _ = dt.load("ollb_top500")
d = pd.read_csv(root / "results" / "variants" / "var_ollb_top500.csv"); c = d[d.rule == "copeland"].copy()
st = lambda v: "censored" if np.isnan(v) else ("infeasible" if np.isinf(v) else "solved")
rows = []
for _, r in c.iterrows():
    i = int(r.target_idx); cap = np.maximum(dt.make_cap("emp99", X, i), X[i]); Y = X.copy(); Y[i] = cap
    win = od.copeland_first(Y) == i
    s = {k: st(r[k]) for k in ("L1", "K", "Linf")}
    if "solved" in s.values(): feas, basis = "feasible", "milp_" + "_".join(k for k in s if s[k] == "solved")
    elif "infeasible" in s.values(): feas, basis = "infeasible", "milp"
    else: feas, basis = ("feasible" if win else "infeasible"), "screen"
    if win != (feas == "feasible"): raise AssertionError(f"MILP and cap-saturated screen disagree for target {i}")
    rows.append(dict(target=r.target, target_idx=i, rank_mean=int(r.rank_mean), l1_status=s["L1"], K_status=s["K"], Linf_status=s["Linf"],
                     wins_at_saturation=bool(win), feasibility=feas, feasibility_basis=basis))
o = pd.DataFrame(rows)
o.to_csv(root / "results" / "variants" / "copeland_top500_screen.csv", index=False)
BINS = [(1, 1), (2, 5), (6, 10), (11, 30), (31, 100), (101, 300), (301, 10**6)]
lab = lambda lo, hi: "1 (mean leader)" if hi == 1 else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
out = []
for g, (lo, hi) in [("all", (1, 10**6)), ("all, rank>=2", (2, 10**6))] + [(lab(*b), b) for b in BINS]:
    t = o[(o.rank_mean >= lo) & (o.rank_mean <= hi)]
    if not len(t): continue
    out.append(dict(group=g, n=len(t), n_feasible=int((t.feasibility == "feasible").sum()), n_infeasible=int((t.feasibility == "infeasible").sum()),
                    feasible_share=(t.feasibility == "feasible").mean(), n_L1_solved=int((t.l1_status == "solved").sum()), n_L1_infeasible=int((t.l1_status == "infeasible").sum()),
                    n_L1_censored=int((t.l1_status == "censored").sum()), n_L1_censored_feasible=int(((t.l1_status == "censored") & (t.feasibility == "feasible")).sum()),
                    n_L1_censored_infeasible=int(((t.l1_status == "censored") & (t.feasibility == "infeasible")).sum())))
f = pd.DataFrame(out); f.to_csv(root / "results" / "variants" / "copeland_top500_feasibility.csv", index=False)
print(pd.crosstab(o.l1_status, o.feasibility)); print(o.feasibility_basis.value_counts().to_dict()); print(f.to_string())
