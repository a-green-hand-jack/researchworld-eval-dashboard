"""A6: mean-model misspecification. The true logit mean has a quadratic part of strength nl; the fitted CLR-OLS mean is linear in x.
Compares each A6 configuration with the matching correctly specified A1 configuration (K=3, h=0.5, same seeds 1000.., 200 replications; draws differ
because the DGP differs): difference of the replication means with a standard error, and Kendall tau between the score rankings under
the two DGPs. Outputs results/tables/A6_vs_A1.csv, A6_rank_agreement.csv (A6_summary.csv / A6_paired_vs_euc.csv come from analyze_a1.py A6)."""
import glob
import numpy as np, pandas as pd
from scipy.stats import kendalltau

M = ["log_vol_ratio", "true_x0_10_min", "true_bd_10_min", "true_x0_10_dev", "x_dev", "true_marg_cov"]
rows, rk = [], []
for f in sorted(glob.glob("results/raw/A6_*.csv*")):
    a = pd.read_csv(f); cfg = a.config.iloc[0]; kind = a.kind.iloc[0]; nl = a.nl.iloc[0]
    base = glob.glob(f"results/raw/A1_{kind}_K3_h0.5_linear.csv*")[0]
    b = pd.read_csv(base)
    res = {}
    for m in M:
        pa = a.pivot(index="seed", columns="method", values=m); pb = b.pivot(index="seed", columns="method", values=m)
        da = pa.mean(); db = pb.mean()
        se = np.sqrt(pa.var(ddof=1) / len(pa) + pb.var(ddof=1) / len(pb))
        res[m] = (da, db)
        for meth in pa.columns:
            rows.append(dict(config=cfg, kind=kind, nl=nl, method=meth, metric=m, a6=da[meth], a1=db[meth], diff=da[meth] - db[meth], se=se[meth],
                             reps_a6=len(pa), reps_a1=len(pb)))
    for m in M:
        da, db = res[m]
        if da.notna().all():
            rk.append(dict(config=cfg, nl=nl, metric=m, tau_vs_correct=kendalltau(da.values, db.values)[0],
                           best_a6=da.idxmax() if m == "true_x0_10_min" or m == "true_bd_10_min" else da.idxmin(),
                           best_a1=db.idxmax() if m == "true_x0_10_min" or m == "true_bd_10_min" else db.idxmin()))
R = pd.DataFrame(rows); R.to_csv("results/tables/A6_vs_A1.csv", index=False)
K = pd.DataFrame(rk); K.to_csv("results/tables/A6_rank_agreement.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R[R.method.isin(["euc", "euc/n", "aitch", "aitch/nq", "dirnll"])].pivot_table(index=["config", "metric"], columns="method", values="diff").round(3).to_string())
print(K.round(3).to_string())
