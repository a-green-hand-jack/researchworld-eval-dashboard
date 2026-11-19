"""Price of calibration (E5 vs deployer alternatives): for each group and certificate rule at (k, delta), the cheapest FIXED budget of each arm
(shipped KernelSHAP, l1-off KernelSHAP, permutation, Covert-Lee) whose pooled P(top-k exact) is at least the certificate's pooled correct rate
(runs stopped at the first certified stage; uncertified runs delivered at x16). Cost = mean coalitions per run. Reads results/ only.
Writes results/cost_at_equal_reliability.csv."""
import argparse, glob, re
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="R20"); ap.add_argument("--out", default="results"); ap.add_argument("--delta", type=float, default=0.1); ap.add_argument("--k", type=int, default=3)
a = ap.parse_args()
C = pd.read_csv(f"{a.out}/certificate_coverage.csv"); C = C[(C.k == a.k) & np.isclose(C.delta, a.delta)]
T = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{a.out}/tidy_*_{a.tag}.csv"))], ignore_index=True)
m = T.cell.str.extract(r"^(?P<ds>.+)_d(?P<sub>\d+|full)_(?P<model>[a-z_]+?)_s(?P<seed>\d+)$"); T["group"] = m.ds + "_d" + m["sub"] + "_" + m.model
T = T[T.k == a.k]
rows = []
for _, c in C.iterrows():
    G = T[T.group == c.group]
    for arm, A in G.groupby("arm"):
        B = A.groupby("budget").agg(r=("r", "mean"), N=("N", "mean"), n_cells=("cell", "nunique")).reset_index().sort_values("N")
        B = B[B.N > 0]
        ok = B[B.r >= c.pooled_correct_delivered]
        shipped = {"perm": "perm500"}.get(arm, "x1")
        sh = B[B.budget == shipped]
        rows.append(dict(group=c.group, rule=c.rule, delta=a.delta, k=a.k, cert_pooled_correct=c.pooled_correct_delivered, cert_mean_cost=c.mean_cost_all,
                         cert_certified_share=c.certified_share, arm=arm, fixed_budget=ok.budget.iloc[0] if len(ok) else None,
                         fixed_cost=ok.N.iloc[0] if len(ok) else np.nan, fixed_pooled_correct=ok.r.iloc[0] if len(ok) else np.nan,
                         shipped_budget=shipped, shipped_cost=sh.N.iloc[0] if len(sh) else np.nan, shipped_pooled_correct=sh.r.iloc[0] if len(sh) else np.nan,
                         max_fixed_pooled_correct=B.r.max()))
R = pd.DataFrame(rows)
R.insert(4, "comparison", np.where(R.arm == "covert_lee", "same_estimator", "across_estimators"))
R = R.sort_values(["group", "rule", "comparison", "arm"], key=lambda c: c.map({"same_estimator": 0, "across_estimators": 1}) if c.name == "comparison" else c).reset_index(drop=True)
R.to_csv(f"{a.out}/cost_at_equal_reliability.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R[R.rule.isin(["naive", "bonf"])].round(3).to_string())
