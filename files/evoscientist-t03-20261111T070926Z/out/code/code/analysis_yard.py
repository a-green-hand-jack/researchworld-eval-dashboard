"""Compare coalition-sampling noise (E1) with other sources of explanation variability (E2/E6) using
instance-aligned exact attributions. Writes results/tables/tabH_yard.csv, tabH2_yard_tests.csv, figs/fig_yard.pdf"""
import os, sys, glob
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import RESULTS
from shapsim import pair_metrics

suffix = "_quick" if "--quick" in sys.argv else ""
TAB = os.path.join(RESULTS, "tables"); FIG = os.path.join(RESULTS, "figs")
rng = np.random.default_rng(3)
core = pd.read_csv(os.path.join(RESULTS, f"core_metrics{suffix}.csv"))
core = core[core.scale == "prob"]
METR = ["top1", "jac3", "rbo", "rel_l2"]
rows, inst_rows = [], []


def add(ds, mo, src, vals):
    """vals: dict metric -> per-instance array"""
    for n in range(len(next(iter(vals.values())))):
        inst_rows.append(dict(dataset=ds, model=mo, source=src, inst=n, **{k: float(v[n]) for k, v in vals.items()}))


for f in sorted(glob.glob(os.path.join(RESULTS, "yard", "*_*.npz"))):
    base = os.path.basename(f)[:-4]
    if base.endswith("_quick") != (suffix == "_quick") or base.startswith("cpu"):
        continue
    ds, mo = base.replace("_quick", "").split("_")
    Z = np.load(f)
    N = Z["phi_ref"].shape[0]
    # (a) retraining
    PR = Z["phi_retrain"]
    K = PR.shape[0]
    iu = np.triu_indices(K, 1)
    per = [pair_metrics(PR[iu[0], n], PR[iu[1], n]) for n in range(N)]
    add(ds, mo, "retrain", {m: np.array([np.mean(p[m]) for p in per]) for m in METR})
    # (b) background sampling
    for key in [k for k in Z.files if k.startswith("phi_bg_")]:
        Bsz = int(key.split("_")[-1])
        A = Z[key]
        r = A.shape[0]
        iu = np.triu_indices(r, 1)
        per = [pair_metrics(A[iu[0], n], A[iu[1], n]) for n in range(A.shape[1])]
        add(ds, mo, f"bg{Bsz}", {m: np.array([np.mean(p[m]) for p in per]) for m in METR})
    # (c) value function: path-dependent vs interventional
    if "phi_pathdep" in Z.files:
        pm = pair_metrics(Z["phi_pathdep"][:N], Z["phi_interv_matched"][:N])
        add(ds, mo, "pathdep", {m: pm[m] for m in METR})
    # between-instance baseline: exact attributions of two different random instances
    ref = Z["phi_ref"]
    I = rng.integers(0, N, 400); J = rng.integers(0, N, 400)
    keep = I != J
    pm = pair_metrics(ref[I[keep]], ref[J[keep]])
    ms = {m: np.full(N, np.mean(pm[m])) for m in METR}
    add(ds, mo, "between_instance", ms)
    # sampling noise from E1 at selected budgets
    for est in ("kernel", "perm"):
        for mult in (4, 16):
            g = core[(core.dataset == ds) & (core.model == mo) & (core.est == est) & (core.mult == mult)].sort_values("inst")
            g = g[g.inst < N]
            if len(g) == 0:
                continue
            add(ds, mo, f"{est}{mult}d", {m: g[m].values for m in METR})
    # NSR relative to population spread (squared distance between different-instance exact attributions)
    spread = np.mean(np.sum((ref[I[keep]] - ref[J[keep]]) ** 2, axis=1))
    for est in ("kernel", "perm"):
        for mult in (4, 16):
            g = core[(core.dataset == ds) & (core.model == mo) & (core.est == est) & (core.mult == mult)]
            if len(g):
                # E||run - ref||^2 = (rel_err*||ref||)^2 approx via ref_rel_err (mean of norms); report ratio of squares
                nsr = np.mean((g.ref_rel_err * g.ref_norm) ** 2) / spread
                inst_rows.append(dict(dataset=ds, model=mo, source=f"nsr_{est}{mult}d", inst=-1, top1=nsr, jac3=nsr, rbo=nsr, rel_l2=nsr))
I_ = pd.DataFrame(inst_rows)
I_.to_csv(os.path.join(TAB, f"tabH_yard_instances{suffix}.csv"), index=False)


def boot_mean(v, B=2000):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    idx = rng.integers(0, len(v), (B, len(v)))
    b = v[idx].mean(1)
    return v.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)


H = []
for (ds, mo, src), g in I_[I_.inst >= 0].groupby(["dataset", "model", "source"]):
    r = dict(dataset=ds, model=mo, source=src, n=len(g))
    for m in METR:
        r[m], r[m + "_lo"], r[m + "_hi"] = boot_mean(g[m].values)
    H.append(r)
H = pd.DataFrame(H)
H.to_csv(os.path.join(TAB, f"tabH_yard{suffix}.csv"), index=False)

# paired tests: retraining disagreement vs. sampling noise at 16d (jac3 per instance), Holm across cells
tests = []
for (ds, mo), g in I_[I_.inst >= 0].groupby(["dataset", "model"]):
    piv = g.pivot(index="inst", columns="source", values="jac3")
    for est in ("kernel16d", "perm16d", "kernel4d", "perm4d"):
        for other in ("retrain", "bg100"):
            if est in piv and other in piv:
                x = piv[[est, other]].dropna()
                d = (x[est] - x[other]).values
                try:
                    p = stats.wilcoxon(d).pvalue if np.any(d != 0) else 1.0
                except ValueError:
                    p = 1.0
                tests.append(dict(dataset=ds, model=mo, sampling=est, other=other, mean_diff_jac3=d.mean(), p=p, n=len(d)))
T = pd.DataFrame(tests)
if len(T):
    order = np.argsort(T.p.values)
    m = len(T)
    holm = np.empty(m)
    run = 0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * T.p.values[i]))
        holm[i] = run
    T["p_holm"] = holm
T.to_csv(os.path.join(TAB, f"tabH2_yard_tests{suffix}.csv"), index=False)

# is instability a property of the instance? rank correlation of per-instance top-3 Jaccard across noise sources
cor = []
for (ds, mo), g in I_[I_.inst >= 0].groupby(["dataset", "model"]):
    piv = g.pivot(index="inst", columns="source", values="jac3")
    for a_, b_ in (("kernel16d", "retrain"), ("perm16d", "retrain"), ("kernel16d", "bg100"), ("retrain", "bg100"), ("kernel4d", "perm4d")):
        if a_ in piv and b_ in piv:
            x = piv[[a_, b_]].dropna()
            if len(x) > 5 and x[a_].nunique() > 1 and x[b_].nunique() > 1:
                r = stats.spearmanr(x[a_], x[b_])
                cor.append(dict(dataset=ds, model=mo, a=a_, b=b_, rho=r[0], p=r[1], n=len(x)))
pd.DataFrame(cor).to_csv(os.path.join(TAB, f"tabH3_yard_corr{suffix}.csv"), index=False)
if cor:
    print(pd.DataFrame(cor).groupby(["a", "b"]).rho.agg(["median", "min", "max", "count"]).round(2).to_string())

# figure
srcs = ["perm4d", "kernel4d", "perm16d", "kernel16d", "bg10", "bg50", "bg100", "bg200", "retrain", "pathdep", "between_instance"]
fig, axes = plt.subplots(1, 3, figsize=(15, 3.8), sharey=True)
MCOL = {"lr": "tab:blue", "xgb": "tab:orange", "rf": "tab:green", "mlp": "tab:red"}
for ax, ds in zip(axes, ["pima", "gmsc", "acsincome"]):
    for k, mo in enumerate(["lr", "xgb", "rf", "mlp"]):
        for i, s in enumerate(srcs):
            g = H[(H.dataset == ds) & (H.model == mo) & (H.source == s)]
            if len(g):
                ax.errorbar(i + (k - 1.5) * 0.12, g.jac3.iloc[0], yerr=[[g.jac3.iloc[0] - g.jac3_lo.iloc[0]], [g.jac3_hi.iloc[0] - g.jac3.iloc[0]]],
                            fmt="o", ms=3, color=MCOL[mo], lw=1, label=mo if i == 0 else None)
    ax.set_xticks(range(len(srcs)))
    ax.set_xticklabels(srcs, rotation=60, ha="right", fontsize=7)
    ax.set_title(ds)
axes[0].set_ylabel("mean top-3 Jaccard between\ntwo independent draws")
axes[0].legend(fontsize=7)
plt.tight_layout()
plt.savefig(os.path.join(FIG, f"fig_yard{suffix}.pdf"))
print(H.pivot_table(index=["dataset", "model"], columns="source", values="jac3").round(2).to_string())
print(T.describe().to_string() if len(T) else "")
