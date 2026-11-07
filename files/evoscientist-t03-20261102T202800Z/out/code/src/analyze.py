"""Statistics, tables and figures for the paper. Reads results/tables/*.csv, writes paper/figs/*.pdf, paper/tables/*.tex,
results/summary.json. Usage: python src/analyze.py"""
import os, sys, json, itertools
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

TAB = f"{C.RES}/tables"; FIG = f"{C.ROOT}/paper/figs"; TEX = f"{C.ROOT}/paper/tables"
os.makedirs(FIG, exist_ok=True); os.makedirs(TEX, exist_ok=True)
NB = 2000
rng = np.random.RandomState(0)
SUM = {}
DSN = dict(german="German Credit (d=20)", pima="Pima (d=8)", gmsc="GMSC (d=10)", acs="ACS Income (d=10)")
MC = dict(lr="tab:blue", rf="tab:green", xgb="tab:orange", mlp="tab:red")
MN = dict(lr="LR", rf="RF", xgb="XGB", mlp="MLP")
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "legend.fontsize": 7, "figure.dpi": 150})


def boot_mean(x, nb=NB, rs=None):
    """cluster (instance-level) bootstrap CI of the mean; x is 1-D array of per-instance values."""
    rs = rs or rng
    x = np.asarray(x, float); n = len(x)
    idx = rs.randint(0, n, (nb, n))
    m = x[idx].mean(1)
    return x.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def fmt_ci(t, p=3):
    return f"{t[0]:.{p}f} [{t[1]:.{p}f}, {t[2]:.{p}f}]"


# ------------------------------------------------------------------ load
E1 = pd.read_csv(f"{TAB}/E1_instance.csv")
E1["d"] = E1["d"].astype(int)
E1["below_min"] = E1["B"] < 2 * E1["d"]          # budget below 2d: KernelSHAP/permutation estimators degenerate
E1["dis"] = 1 - E1["pair_jac"]
cells = E1[["ds", "model", "est"]].drop_duplicates().values.tolist()


# ------------------------------------------------------------------ 1. main curves (Fig 1) -----------------------------
def fig_main(est, fname, metric="pair_jac", ylabel="Two-run top-3 agreement (Jaccard)"):
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.0), sharey=True)
    for ax, ds in zip(axs, C.DATASETS):
        for k in C.MODELS:
            g = E1[(E1.ds == ds) & (E1.model == k) & (E1.est == est)]
            if g.empty: continue
            Bs = sorted(g.B.unique()); mu, lo, hi = [], [], []
            for B in Bs:
                t = boot_mean(g[g.B == B].sort_values("inst")[metric].values)
                mu.append(t[0]); lo.append(t[1]); hi.append(t[2])
            ax.plot(Bs, mu, "-o", ms=2.5, color=MC[k], label=MN[k], lw=1)
            ax.fill_between(Bs, lo, hi, color=MC[k], alpha=0.15, lw=0)
        d = int(g.d.iloc[0]); ax.axvline(2 * d + 2, color="grey", ls=":", lw=0.8)
        if est == "kernel" and 2 ** d - 2 <= max(C.BUDGETS):
            ax.axvline(2 ** d - 2, color="k", ls="--", lw=0.8)
        ax.set_xscale("log", base=2); ax.set_title(DSN[ds]); ax.set_xlabel("budget B (coalitions)")
    axs[0].set_ylabel(ylabel); axs[0].legend(loc="lower right", ncol=2)
    plt.tight_layout(); plt.savefig(f"{FIG}/{fname}", bbox_inches="tight"); plt.close()


# ------------------------------------------------------------------ 2. adequacy budgets ---------------------------------
def adequate_B(g, tau, q, metric="pair_jac"):
    """smallest B (with all larger B also adequate) such that >= q of instances have two-run agreement >= tau."""
    Bs = sorted(g.B.unique()); ok = []
    for B in Bs:
        v = g[g.B == B][metric].values
        ok.append((v >= tau - 1e-12).mean() >= q)
    for j in range(len(Bs)):
        if all(ok[j:]): return Bs[j]
    return np.inf


def adequacy_table():
    crit = [(0.8, 0.9), (0.9, 0.95), (1.0, 0.9)]
    rows = []
    for ds, k, est in cells:
        g = E1[(E1.ds == ds) & (E1.model == k) & (E1.est == est)]
        insts = np.sort(g.inst.unique()); d = int(g.d.iloc[0])
        row = dict(ds=ds, model=k, est=est, d=d)
        for tau, q in crit:
            pt = adequate_B(g, tau, q)
            bs = []
            for _ in range(500):
                s = rng.choice(insts, len(insts))
                gb = pd.concat([g[g.inst == i] for i in s[:len(s)]])  # resampled with repetition
                bs.append(adequate_B(gb, tau, q))
            bs = np.array(bs, float)
            row[f"B_{tau}_{q}"] = pt
            row[f"B_{tau}_{q}_hi"] = np.percentile(bs, 95)   # 95th percentile over bootstrap resamples (upper bound)
        rows.append(row)
    A = pd.DataFrame(rows); A.to_csv(f"{TAB}/adequacy.csv", index=False)
    return A


# ------------------------------------------------------------------ 3. standards of comparison ---------------------------
def standards(E2, E3):
    rows = []
    for ds in C.DATASETS:
        for k in C.MODELS:
            r3 = E3[(E3.ds == ds) & (E3.model == k) & (E3.inst >= 0)].sort_values("inst")
            cr = E3[(E3.ds == ds) & (E3.model == k) & (E3.inst == -1)]
            retr = boot_mean((1 - r3.pair_jac).values)
            cross = float(1 - cr.cross_jac.iloc[0])
            row = dict(ds=ds, model=k, retrain=retr, cross=cross)
            for m in C.E2_M:
                g = E2[(E2.ds == ds) & (E2.model == k) & (E2.m == m)].sort_values("inst")
                row[f"bg{m}"] = boot_mean((1 - g.pair_jac).values)
            g1 = E1[(E1.ds == ds) & (E1.model == k) & (E1.est == "kernel")]
            for B in C.BUDGETS:
                row[f"run{B}"] = boot_mean(g1[g1.B == B].sort_values("inst").dis.values)
            rows.append(row)
    return rows


def fig_standards(rows):
    fig, axs = plt.subplots(4, 4, figsize=(7.2, 6.2), sharex=True, sharey=True)
    for i, ds in enumerate(C.DATASETS):
        for j, k in enumerate(C.MODELS):
            ax = axs[i, j]; r = [x for x in rows if x["ds"] == ds and x["model"] == k][0]
            Bs = C.BUDGETS
            ax.plot(Bs, [r[f"run{B}"][0] for B in Bs], "-o", ms=2, color="k", lw=1, label="repeat run (KernelSHAP)")
            ax.fill_between(Bs, [r[f"run{B}"][1] for B in Bs], [r[f"run{B}"][2] for B in Bs], color="k", alpha=0.15, lw=0)
            ax.axhline(r["retrain"][0], color="tab:purple", lw=1.2, label="model retraining")
            ax.axhspan(r["retrain"][1], r["retrain"][2], color="tab:purple", alpha=0.15, lw=0)
            ax.axhline(r["bg50"][0], color="tab:cyan", lw=1.2, ls="--", label="background resample (m=50)")
            ax.axhline(r["cross"], color="tab:red", lw=1.0, ls=":", label="different instance")
            ax.set_xscale("log", base=2); ax.set_yscale("symlog", linthresh=0.01); ax.set_ylim(0, 1.0)
            if i == 0: ax.set_title(MN[k])
            if j == 0: ax.set_ylabel(DSN[ds].split(" (")[0] + "\n1 - top-3 Jaccard")
            if i == 3: ax.set_xlabel("budget B")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.03))
    plt.tight_layout(); plt.savefig(f"{FIG}/standards.pdf", bbox_inches="tight"); plt.close()


# ------------------------------------------------------------------ 4. margin analysis ---------------------------------
def margin_analysis(est="kernel", Bmax=512):
    g = E1[(E1.est == est) & (~E1.exact) & (~E1.below_min) & (E1.B <= Bmax) & np.isfinite(E1.z)].copy()
    g["flip"] = 1 - g.set_recover
    bins = [0, 0.5, 1, 2, 3, 5, 10, 1e9]
    g["zbin"] = pd.cut(g.z, bins)
    out = g.groupby("zbin", observed=True).agg(n=("flip", "size"), flip=("flip", "mean")).reset_index()
    # cluster bootstrap (by ds/model/inst) for flip rate per bin
    cl = g.groupby(["ds", "model", "inst"]).ngroup().values; ncl = cl.max() + 1
    res = {}
    for b in out.zbin:
        sel = (g.zbin == b).values; num = np.bincount(cl[sel], weights=g.flip.values[sel], minlength=ncl); den = np.bincount(cl[sel], minlength=ncl)
        bs = []
        for _ in range(500):
            s = rng.randint(0, ncl, ncl); dd = den[s].sum(); bs.append(num[s].sum() / dd if dd else np.nan)
        res[b] = (np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5))
    out["lo"] = [res[b][0] for b in out.zbin]; out["hi"] = [res[b][1] for b in out.zbin]
    out["zbin"] = out.zbin.astype(str)
    out.to_csv(f"{TAB}/margin_bins.csv", index=False)
    # share of instances with small normalised margin at B=256 and B=2048 (kernel)
    sh = {}
    for B in [64, 256, 1024]:
        h = E1[(E1.est == est) & (E1.B == B) & (~E1.exact) & np.isfinite(E1.z)]
        sh[B] = float((h.z < 2).mean())
    SUM["share_z_lt2"] = sh
    fig, ax = plt.subplots(figsize=(3.3, 2.3))
    x = np.arange(len(out)); ax.bar(x, out.flip, color="tab:gray", yerr=[out.flip - out.lo, out.hi - out.flip], capsize=2)
    ax.set_xticks(x); ax.set_xticklabels(out.zbin, rotation=40, ha="right")
    ax.set_xlabel("normalised margin z = gap(3rd,4th)/noise SD"); ax.set_ylabel("P(top-3 set differs from ref.)")
    plt.tight_layout(); plt.savefig(f"{FIG}/margin.pdf", bbox_inches="tight"); plt.close()
    return out


# ------------------------------------------------------------------ 5. two-run diagnostic ------------------------------
def diagnostic():
    from sklearn.metrics import roc_auc_score
    D = pd.read_csv(f"{TAB}/E1_diag.csv"); D = D[(~D.exact)]
    D = D.merge(E1[["ds", "model", "est", "B", "below_min"]].drop_duplicates(), on=["ds", "model", "est", "B"])
    D = D[~D.below_min]
    D["bad"] = (D.ref_jac < 1).astype(int); D["score"] = 1 - D.diag_jac
    rows = []
    for B, g in D.groupby("B"):
        if g.bad.nunique() < 2: continue
        cl = g.groupby(["ds", "model", "est", "inst"]).ngroup().values
        au = roc_auc_score(g.bad, g.score)
        bs = []
        for _ in range(200):
            s = rng.choice(cl.max() + 1, cl.max() + 1)
            w = np.bincount(cl, minlength=cl.max() + 1)[s]
            idx = np.concatenate([np.where(cl == c)[0] for c in s])
            yb = g.bad.values[idx]
            if yb.min() == yb.max(): continue
            bs.append(roc_auc_score(yb, g.score.values[idx]))
        # P(bad | diag says stable (diag_jac==1)) vs P(bad | diag says unstable)
        st = g[g.diag_jac == 1]; un = g[g.diag_jac < 1]
        rows.append(dict(B=B, n=len(g), p_bad=g.bad.mean(), auroc=au, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                         p_bad_if_agree=st.bad.mean() if len(st) else np.nan, n_agree=len(st),
                         p_bad_if_disagree=un.bad.mean() if len(un) else np.nan, n_disagree=len(un)))
    R_ = pd.DataFrame(rows); R_.to_csv(f"{TAB}/diagnostic.csv", index=False)
    return R_


# ------------------------------------------------------------------ 6. kernel vs permutation ---------------------------
def kernel_vs_perm():
    rows = []
    g = E1[~E1.exact & ~E1.below_min]
    piv = g.pivot_table(index=["ds", "model", "inst", "B"], columns="est", values=["ref_relL2", "pair_jac"]).dropna()
    for (ds, k, B), h in piv.groupby(level=[0, 1, 3]):
        dk = h["ref_relL2"]["kernel"].values - h["ref_relL2"]["perm"].values
        dj = h["pair_jac"]["kernel"].values - h["pair_jac"]["perm"].values
        if np.allclose(dk, 0): continue
        try:
            p = stats.wilcoxon(dk).pvalue
        except ValueError:
            p = 1.0
        rows.append(dict(ds=ds, model=k, B=B, n=len(dk), d_relL2=dk.mean(), d_jac=dj.mean(),
                         ratio=np.exp(np.mean(np.log(h["ref_relL2"]["kernel"].values / np.maximum(h["ref_relL2"]["perm"].values, 1e-12)))), p=p))
    K = pd.DataFrame(rows)
    # Holm correction across all tests
    o = np.argsort(K.p.values); m = len(K); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * K.p.values[i]); adj[i] = min(1, run)
    K["p_holm"] = adj; K.to_csv(f"{TAB}/kernel_vs_perm.csv", index=False)
    return K


# ------------------------------------------------------------------ 7. scaling slopes -----------------------------------
def slopes():
    rows = []
    for ds, k, est in cells:
        g = E1[(E1.ds == ds) & (E1.model == k) & (E1.est == est) & (~E1.exact) & (~E1.below_min)]
        Bs = sorted(g.B.unique())
        if len(Bs) < 3: continue
        P = np.stack([g[g.B == B].sort_values("inst").ref_relL2.values for B in Bs])  # (nB, n)
        lb = np.log(Bs)
        def sl(P_):
            y = np.log(np.maximum(P_.mean(1), 1e-12)); return np.polyfit(lb, y, 1)[0]
        s0 = sl(P); n = P.shape[1]
        bs = [sl(P[:, rng.randint(0, n, n)]) for _ in range(500)]
        rows.append(dict(ds=ds, model=k, est=est, nB=len(Bs), slope=s0, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                         relL2_at_Bmin=P[0].mean(), relL2_at_Bmax=P[-1].mean()))
    S = pd.DataFrame(rows); S.to_csv(f"{TAB}/slopes.csv", index=False)
    return S


if __name__ == "__main__":
    fig_main("kernel", "main_kernel.pdf"); fig_main("perm", "main_perm.pdf")
    A = adequacy_table(); print(A.to_string())
    have = lambda f: os.path.exists(f"{TAB}/{f}")
    if have("E2_instance.csv") and have("E3_instance.csv"):
        E2 = pd.read_csv(f"{TAB}/E2_instance.csv"); E3 = pd.read_csv(f"{TAB}/E3_instance.csv")
        rows = standards(E2, E3); fig_standards(rows)
        import pickle; pickle.dump(rows, open(f"{TAB}/standards.pkl", "wb"))
    print(margin_analysis().to_string())
    print(diagnostic().to_string())
    K = kernel_vs_perm(); print(K.describe().to_string())
    print(slopes().to_string())
    json.dump(SUM, open(f"{C.RES}/summary.json", "w"), indent=1, default=float)
