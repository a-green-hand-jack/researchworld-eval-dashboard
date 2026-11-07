"""Aggregate raw results into the tables / figures of the paper.

Metric: per held-out model, RMSE_z = sqrt(mean squared error over its held-out benchmarks) in training-z units.
Headline statistic = median over held-out models (robust to a few gross-outlier models); the mean is also reported.
Uncertainty: 95% percentile interval of a cluster bootstrap over model *families* (B=1000).
Usage: python code/analysis.py   -> results/summary_*.csv, paper/figs/*.pdf, paper/tables/*.tex
"""
import os, glob, json, re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from run_protocol import family_of

os.makedirs("paper/figs", exist_ok=True); os.makedirs("paper/tables", exist_ok=True)
B = 1000
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5, "figure.dpi": 150,
                     "axes.spines.top": False, "axes.spines.right": False})
DATA_LABEL = {"mteb_mid": "MTEB-mid (139x65, complete)", "mteb_dense": "MTEB-dense (117x287, complete)",
              "mteb_wide": "MTEB-wide (234x357, 70% obs.)", "olb": "OpenLLM-LB (4496x6)", "helm": "HELM-Lite (91x10)",
              "livebench": "LiveBench (n x7, sparse)"}
SEL_LABEL = {"random": "random", "greedy_iopt": "greedy I-opt (FA)", "cov_greedy": "greedy cov. (Gauss)", "top_load": "top-communality",
             "piv_qr": "pivoted QR", "kmeans": "k-means cover"}
PRED_LABEL = {"mean": "train mean", "fa1": "1-factor", "fa": "FA(r)", "ppca": "PPCA(r)", "gauss": "Gauss-cov", "knn": "kNN"}


from matplotlib.ticker import ScalarFormatter, NullLocator


def logk(a, kmax=48):
    a.set_xscale("log", base=2)
    ticks = [t for t in [1, 2, 4, 8, 16, 32, 48] if t <= kmax]
    a.set_xticks(ticks); a.xaxis.set_major_formatter(ScalarFormatter()); a.xaxis.set_minor_locator(NullLocator())


def load(name):
    d = pd.read_csv(f"results/raw/{name}.csv.gz")
    d["rmse"] = np.sqrt(d.mse_z)
    return d


def fam_of(d, data):
    return {m: family_of(m, data) for m in d.model.unique()}


class Res:
    """Wide matrix models x (sel,pred,k) of a metric + bootstrap machinery."""

    def __init__(self, name, metric="rmse"):
        self.name = name
        self.d = load(name)
        self.data = self.d.data.iloc[0]
        self.W = self.d.pivot_table(index="model", columns=["sel", "pred", "k"], values=metric)
        fams = fam_of(self.d, self.data)
        self.fam = np.array([fams[m] for m in self.W.index])
        self.ks = sorted(self.d.k.unique())
        rng = np.random.default_rng(123)
        uf = pd.unique(self.fam)
        groups = {f: np.where(self.fam == f)[0] for f in uf}
        self.idx = [np.concatenate([groups[f] for f in rng.choice(uf, len(uf))]) for _ in range(B)]
        self.X = self.W.values
        self.cols = list(self.W.columns)
        self.cix = {c: i for i, c in enumerate(self.cols)}

    def col(self, sel, pred, k):
        return self.cix[(sel, pred, k)]

    def stat(self, X, stat):
        return np.median(X, axis=0) if stat == "median" else X.mean(axis=0)

    def curve(self, sel, pred, stat="median", rel_to=None):
        """point estimate + 95% CI over k. rel_to=(sel,pred) -> paired relative change (curve/ref - 1)."""
        ci = [self.col(sel, pred, k) for k in self.ks]
        pt = self.stat(self.X[:, ci], stat)
        bs = np.array([self.stat(self.X[i][:, ci], stat) for i in self.idx])
        if rel_to is not None:
            cr = [self.col(*rel_to, k) for k in self.ks]
            pt = pt / self.stat(self.X[:, cr], stat) - 1
            br = np.array([self.stat(self.X[i][:, cr], stat) for i in self.idx])
            bs = bs / br - 1
        return pt, np.quantile(bs, .025, axis=0), np.quantile(bs, .975, axis=0), bs


def fmt(pt, lo, hi, nd=3):
    return f"{pt:.{nd}f} [{lo:.{nd}f},{hi:.{nd}f}]"


def k_threshold(curve, base, frac, ks):
    """smallest k with curve <= base - frac*(base - curve[-1]); curve array over ks."""
    tgt = base - frac * (base - curve[-1])
    ok = np.where(curve <= tgt)[0]
    return ks[ok[0]] if len(ok) else np.nan


def main_tables():
    rows = []
    for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
        for split in ["family", "random"]:
            name = f"{data}_{split}"
            if not os.path.exists(f"results/raw/{name}.csv.gz"):
                continue
            R = Res(name)
            for stat in ["median", "mean"]:
                for (sel, pred) in [("random", "mean"), ("random", "fa1"), ("random", "fa"), ("random", "gauss"), ("random", "knn"),
                                    ("greedy_iopt", "fa"), ("greedy_iopt", "gauss"), ("cov_greedy", "gauss"), ("cov_greedy", "fa"),
                                    ("kmeans", "gauss"), ("piv_qr", "gauss"), ("top_load", "gauss")]:
                    if (sel, pred, R.ks[0]) not in R.cix:
                        continue
                    pt, lo, hi, _ = R.curve(sel, pred, stat)
                    for k, p, l, h in zip(R.ks, pt, lo, hi):
                        rows.append(dict(data=data, split=split, stat=stat, sel=sel, pred=pred, k=k, rmse=p, lo=l, hi=h, n_models=len(R.W)))
    S = pd.DataFrame(rows)
    S.to_csv("results/summary_curves.csv", index=False)
    return S


def paired_gain_table():
    """relative change of the per-model RMSE (median over models) of selection method vs random, same predictor."""
    rows = []
    for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
        for split in ["family", "random"]:
            name = f"{data}_{split}"
            if not os.path.exists(f"results/raw/{name}.csv.gz"):
                continue
            R = Res(name)
            for sel in ["greedy_iopt", "cov_greedy", "kmeans", "piv_qr", "top_load"]:
                for pred in ["fa", "gauss"]:
                    if (sel, pred, R.ks[0]) not in R.cix:
                        continue
                    for stat in ["median", "mean"]:
                        pt, lo, hi, _ = R.curve(sel, pred, stat, rel_to=("random", pred))
                        for k, p, l, h in zip(R.ks, pt, lo, hi):
                            # fraction of models for which sel beats random
                            win = float(np.mean(R.X[:, R.col(sel, pred, k)] < R.X[:, R.col("random", pred, k)]))
                            rows.append(dict(data=data, split=split, stat=stat, sel=sel, pred=pred, k=k, rel=p, lo=l, hi=h, win_frac=win))
    G = pd.DataFrame(rows)
    G.to_csv("results/summary_paired_gain.csv", index=False)
    return G


def k_needed():
    rows = []
    for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
        for split in ["family", "random"]:
            name = f"{data}_{split}"
            if not os.path.exists(f"results/raw/{name}.csv.gz"):
                continue
            R = Res(name)
            for (sel, pred) in [("random", "gauss"), ("cov_greedy", "gauss"), ("greedy_iopt", "fa")]:
                pt, lo, hi, bs = R.curve(sel, pred, "median")
                bm = R.curve("random", "mean", "median")
                base_pt, base_bs = bm[0][0], bm[3][:, 0]
                for frac in [0.5, 0.8]:
                    k_pt = k_threshold(pt, base_pt, frac, R.ks)
                    kb = np.array([k_threshold(bs[b], base_bs[b], frac, R.ks) for b in range(B)])
                    rows.append(dict(data=data, split=split, sel=sel, pred=pred, frac=frac, k_pt=k_pt,
                                     k_lo=np.nanquantile(kb, .025), k_hi=np.nanquantile(kb, .975), rmse_mean_pred=base_pt, rmse_kmax=pt[-1], kmax=R.ks[-1]))
    K = pd.DataFrame(rows)
    K.to_csv("results/summary_k_needed.csv", index=False)
    return K


# ---------------------------------------------------------------------------------------------- figures
def fig_main(S):
    datas = ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.2))
    styles = [("random", "mean", "0.5", "--"), ("random", "gauss", "tab:blue", "-"), ("random", "fa", "tab:cyan", ":"),
              ("greedy_iopt", "fa", "tab:red", "-"), ("cov_greedy", "gauss", "tab:green", "-")]
    for a, data in zip(ax.ravel(), datas):
        sub = S[(S.data == data) & (S.split == "family") & (S["stat"] == "median")]
        if sub.empty:
            a.set_visible(False); continue
        for sel, pred, c, ls in styles:
            s = sub[(sub.sel == sel) & (sub.pred == pred)].sort_values("k")
            lab = f"{SEL_LABEL[sel]} + {PRED_LABEL[pred]}" if pred != "mean" else "train-mean (no scores used)"
            a.plot(s.k, s.rmse, color=c, ls=ls, lw=1.2, label=lab)
            if pred != "mean":
                a.fill_between(s.k, s.lo, s.hi, color=c, alpha=.12, lw=0)
        logk(a, sub.k.max()); a.set_title(DATA_LABEL[data]); a.set_xlabel("k (benchmarks run)")
        a.set_ylim(bottom=0)
    ax[0, 0].set_ylabel("median RMSE$_z$ (family-held-out)"); ax[1, 0].set_ylabel("median RMSE$_z$")
    h, l = ax[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig("paper/figs/fig_main_curves.pdf"); plt.close(fig)


def fig_selection_gain(G):
    datas = ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.0), sharey=False)
    cols = {"greedy_iopt": "tab:red", "cov_greedy": "tab:green", "kmeans": "tab:purple", "piv_qr": "tab:orange", "top_load": "tab:brown"}
    for a, data in zip(ax.ravel(), datas):
        sub = G[(G.data == data) & (G.split == "family") & (G["stat"] == "median") & (G.pred == "gauss")]
        if sub.empty:
            a.set_visible(False); continue
        for sel, c in cols.items():
            s = sub[sub.sel == sel].sort_values("k")
            if s.empty: continue
            a.plot(s.k, 100 * s.rel, color=c, lw=1.1, label=SEL_LABEL[sel])
            if sel in ("cov_greedy", "greedy_iopt"):
                a.fill_between(s.k, 100 * s.lo, 100 * s.hi, color=c, alpha=.12, lw=0)
        a.axhline(0, color="k", lw=.6); logk(a, sub.k.max()); a.set_title(DATA_LABEL[data]); a.set_xlabel("k")
    ax[0, 0].set_ylabel("% change of median RMSE$_z$\nvs random (Gauss-cov predictor)"); ax[1, 0].set_ylabel("% change vs random")
    h, l = ax[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig("paper/figs/fig_selection_gain.pdf"); plt.close(fig)


def fig_predictors():
    datas = ["mteb_mid", "mteb_wide", "olb", "helm"]
    fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.0))
    cols = {"mean": "0.5", "fa1": "tab:orange", "fa": "tab:cyan", "ppca": "tab:purple", "gauss": "tab:blue", "knn": "tab:brown"}
    S = pd.read_csv("results/summary_curves.csv")
    for a, data in zip(ax, datas):
        sub = S[(S.data == data) & (S.split == "family") & (S["stat"] == "median") & (S.sel == "random")]
        for p, c in cols.items():
            s = sub[sub.pred == p].sort_values("k")
            if s.empty: continue
            a.plot(s.k, s.rmse, color=c, lw=1.1, label=PRED_LABEL[p], ls="--" if p == "mean" else "-")
        logk(a, sub.k.max()); a.set_title(DATA_LABEL[data].split(" (")[0]); a.set_xlabel("k (random S)")
    ax[0].set_ylabel("median RMSE$_z$")
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, frameon=False)
    fig.tight_layout(rect=(0, 0.12, 1, 1)); fig.savefig("paper/figs/fig_predictors.pdf"); plt.close(fig)


def theory_vs_real():
    rows = []
    for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
        for split in ["family", "random"]:
            name = f"{data}_{split}"
            if not os.path.exists(f"results/raw/{name}.csv.gz"):
                continue
            d = load(name)
            fits = json.load(open(f"results/raw/{name}_fits.json"))
            imp = {}
            for f in fits:
                for k, v in f["implied"].items():
                    for key, val in v.items():
                        imp.setdefault((int(k), key), []).append(val)
            for (sel, pred, key) in [("random", "fa", "fa_random"), ("random", "gauss", "gauss_random"),
                                     ("greedy_iopt", "fa", "fa_greedy"), ("cov_greedy", "gauss", "gauss_covgreedy")]:
                x = d[(d.sel == sel) & (d.pred == pred)]
                for k, g in x.groupby("k"):
                    m = g.mse_z.values
                    tm = np.mean(np.sort(m)[: int(np.ceil(0.9 * len(m)))])      # 10%-upper-trimmed mean
                    rows.append(dict(data=data, split=split, sel=sel, pred=pred, k=k, measured_median=np.median(m), measured_trim=tm,
                                     measured_mean=m.mean(), implied=float(np.mean(imp[(k, key)])), noise_floor=float(np.mean(imp[(k, "fa_noise_floor")]))))
    T = pd.DataFrame(rows)
    T["ratio_trim"] = T.measured_trim / T.implied
    T["ratio_median"] = T.measured_median / T.implied
    T.to_csv("results/summary_theory_vs_real.csv", index=False)
    return T


def fig_theory(T):
    datas = ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]
    fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.0))
    for a, data in zip(ax.ravel(), datas):
        sub = T[(T.data == data) & (T.split == "random")]
        if sub.empty:
            a.set_visible(False); continue
        for (sel, pred), c in [(("random", "fa"), "tab:cyan"), (("random", "gauss"), "tab:blue"), (("greedy_iopt", "fa"), "tab:red"), (("cov_greedy", "gauss"), "tab:green")]:
            s = sub[(sub.sel == sel) & (sub.pred == pred)].sort_values("k")
            a.plot(s.k, s.measured_trim, color=c, lw=1.2, marker="o", ms=2, label=f"measured {SEL_LABEL[sel]}+{PRED_LABEL[pred]}")
            a.plot(s.k, s.implied, color=c, lw=1.0, ls="--", label="model-implied" if c == "tab:cyan" else None)
        logk(a, sub.k.max()); a.set_title(DATA_LABEL[data]); a.set_xlabel("k"); a.set_ylim(bottom=0)
    ax[0, 0].set_ylabel("MSE$_z$ (trimmed mean)"); ax[1, 0].set_ylabel("MSE$_z$ (trimmed mean)")
    h, l = ax[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig("paper/figs/fig_theory_vs_real.pdf"); plt.close(fig)


def fig_synth():
    a = pd.read_csv("results/theory_t1t2.csv"); m = pd.read_csv("results/theory_mp.csv")
    t3 = pd.read_csv("results/theory_t3.csv"); t4 = pd.read_csv("results/theory_t4.csv")
    fig, axx = plt.subplots(2, 2, figsize=(7.0, 5.0)); ax = axx.ravel()
    # (a) OLS vs formula / tail
    s = a[(a.r == 6) & (a.sig2 == 0.25)].sort_values("k")
    ax[0].plot(s.k, s.ols_mean, "o-", ms=3, color="tab:red", label="OLS mean (sim.)")
    ax[0].plot(s.k[s.ols_formula < 1e9], s.ols_formula[s.ols_formula < 1e9], "k--", label=r"$\sigma^2(1+\frac{r}{k-r-1})$")
    ax[0].plot(s.k, s.ols_p99, "s:", ms=3, color="tab:red", alpha=.6, label="OLS 99th pct")
    ax[0].plot(s.k, s.bayes_mean, "o-", ms=3, color="tab:blue", label="Bayes mean (sim.)")
    ax[0].plot(s.k, s.bayes_p99, "s:", ms=3, color="tab:blue", alpha=.6, label="Bayes 99th pct")
    ax[0].set_yscale("log"); ax[0].set_xscale("log"); ax[0].set_xticks([7, 10, 15, 20, 30, 60]); ax[0].xaxis.set_major_formatter(ScalarFormatter()); ax[0].xaxis.set_minor_locator(NullLocator()); ax[0].set_xlabel("k"); ax[0].set_title("(a) known loadings, r=6, $\\sigma^2$=.25 (random S)"); ax[0].legend(frameon=False, fontsize=6)
    # (b) MP
    for r, c in [(5, "tab:blue"), (20, "tab:green")]:
        s = m[(m.r == r) & (m.s2 == 0.3)]
        ax[1].plot(s.k, s.sim, "o", ms=3, color=c, label=f"sim. r={r}")
        ax[1].plot(s.k, s.mp, "-", color=c, lw=1, label=f"MP formula r={r}")
        ax[1].plot(s.k, s.naive, ":", color=c, lw=1)
    ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xticks([1, 3, 10, 30, 100]); ax[1].xaxis.set_major_formatter(ScalarFormatter()); ax[1].xaxis.set_minor_locator(NullLocator()); ax[1].set_xlabel("k"); ax[1].set_title("(b) excess variance of Bayes error, $\\sigma^2$=.3\n(dotted: naive $\\sigma^2 r/k$)")
    ax[1].legend(frameon=False, fontsize=6)
    # (c) heterogeneity
    for het, c in [(0.0, "tab:gray"), (0.5, "tab:orange"), (1.0, "tab:red")]:
        s = t3[t3.het == het].pivot_table(index="k", columns="sel", values="mse")
        ax[2].plot(s.index, s["greedy_iopt"] / s["random"], "o-", ms=3, color=c, label=f"heterogeneity {het}")
    ax[2].axvline(6, color="k", lw=.5, ls=":"); ax[2].set_xscale("log"); ax[2].set_xticks([2, 3, 4, 6, 8, 12, 18, 24, 36]); ax[2].xaxis.set_major_formatter(ScalarFormatter()); ax[2].xaxis.set_minor_locator(NullLocator()); ax[2].set_xlabel("k (r=6)"); ax[2].set_ylabel("MSE greedy / MSE random"); ax[2].set_title("(c) value of design"); ax[2].legend(frameon=False, fontsize=6)
    # (d) estimation of loadings
    d = t4.groupby(["miss", "M", "k"])[["mse_est", "mse_oracle"]].mean().reset_index()
    d["excess"] = d.mse_est - d.mse_oracle
    d["Meff"] = d.M * (1 - d.miss)
    for k, c in [(5, "tab:red"), (10, "tab:blue"), (20, "tab:green")]:
        for miss, mk in [(0.0, "o"), (0.5, "^")]:
            s = d[(d.k == k) & (d.miss == miss)]
            ax[3].plot(s.Meff, s.excess, mk + "-", ms=3, color=c, lw=.8, label=f"k={k}, miss={miss}" if True else None)
    ax[3].set_xscale("log"); ax[3].set_yscale("log"); ax[3].set_xlabel("effective training models $M(1-p)$"); ax[3].set_ylabel("excess MSE vs known loadings"); ax[3].set_title("(d) cost of estimating $V$")
    ax[3].legend(frameon=False, fontsize=6)
    fig.tight_layout(); fig.savefig("paper/figs/fig_synthetic.pdf"); plt.close(fig)
    # slopes of excess vs Meff
    out = []
    for k in [5, 10, 20]:
        s = d[(d.k == k) & (d.Meff >= 40)]
        sl = np.polyfit(np.log(s.Meff), np.log(s.excess.clip(lower=1e-4)), 1)[0]
        out.append(dict(k=k, loglog_slope=sl, excess_times_Meff=float((s.excess * s.Meff).median())))
    pd.DataFrame(out).to_csv("results/summary_estimation_slope.csv", index=False)


def fig_conditions():
    rows = []
    for tag, label, val in [("", "full", 1.0), ("_trainfrac0.5", "frac", 0.5), ("_trainfrac0.25", "frac", 0.25), ("_trainfrac0.12", "frac", 0.12),
                            ("_trainmiss0.3", "miss", 0.3), ("_trainmiss0.6", "miss", 0.6), ("_trainmiss0.8", "miss", 0.8)]:
        name = f"mteb_mid_random{tag}"
        if not os.path.exists(f"results/raw/{name}.csv.gz"):
            continue
        R = Res(name)
        for sel, pred in [("random", "gauss"), ("random", "fa"), ("greedy_iopt", "fa"), ("cov_greedy", "gauss"), ("random", "mean")]:
            pt, lo, hi, _ = R.curve(sel, pred, "median")
            for k, p, l, h in zip(R.ks, pt, lo, hi):
                rows.append(dict(tag=tag, kind=label, val=val, sel=sel, pred=pred, k=k, rmse=p, lo=l, hi=h))
    C = pd.DataFrame(rows)
    C.to_csv("results/summary_conditions_mid.csv", index=False)
    if C.empty:
        return C
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.2))
    for a, (sel, pred, ttl) in zip(ax, [("random", "gauss", "random + Gauss-cov"), ("cov_greedy", "gauss", "greedy cov. + Gauss-cov"), ("greedy_iopt", "fa", "greedy I-opt + FA")]):
        for kk, c in [(2, "tab:blue"), (6, "tab:orange"), (12, "tab:green"), (24, "tab:red")]:
            xs, ys = [], []
            for kind, ordr in [("frac", None)]:
                pass
            sub = C[(C.sel == sel) & (C.pred == pred) & (C.k == kk)]
            f = sub[sub.kind.isin(["full", "frac"])].sort_values("val")
            a.plot(f.val * 100 * 0.9, f.rmse, "o-", ms=3, color=c, label=f"k={kk}")
        a.set_xscale("log"); a.set_xlabel("% of other models used for training (≈ M)"); a.set_title(ttl)
    ax[0].set_ylabel("median RMSE$_z$ (MTEB-mid, random split)"); ax[0].legend(frameon=False)
    fig.tight_layout(); fig.savefig("paper/figs/fig_conditions.pdf"); plt.close(fig)
    return C


def fig_spectrum():
    out = []
    fig, ax = plt.subplots(1, 1, figsize=(3.2, 2.3))
    for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
        D = pd.read_csv(f"data/processed/{data}.csv", index_col=0)
        Z = ((D - D.mean()) / D.std()).values
        import sys
        sys.path.insert(0, "code")
        import bsp
        R = bsp.pairwise_corr(Z, min_overlap=10) if np.isnan(Z).any() else np.corrcoef(Z.T)
        ev = np.sort(np.linalg.eigvalsh(R))[::-1]
        ev = ev / ev.sum()
        cum = np.cumsum(ev)
        out.append(dict(data=data, N=R.shape[0], pc1=ev[0], pc1_3=cum[min(2, len(cum) - 1)], r80=int(np.argmax(cum >= .8) + 1), r90=int(np.argmax(cum >= .9) + 1),
                        part_ratio=float(1 / np.sum(ev ** 2))))
        ax.plot(np.arange(1, min(len(cum), 30) + 1), cum[:30], label=data.replace("_", "-"), lw=1)
    ax.set_xscale("log"); ax.set_xlabel("number of principal components"); ax.set_ylabel("cumulative variance"); ax.legend(frameon=False, fontsize=5.5)
    fig.tight_layout(); fig.savefig("paper/figs/fig_spectrum.pdf"); plt.close(fig)
    pd.DataFrame(out).to_csv("results/summary_spectrum.csv", index=False)
    return pd.DataFrame(out)


def paired_tests():
    """Wilcoxon signed-rank on per-model RMSE (selection vs random, Gauss-cov predictor), Holm-corrected over all tests.
    Descriptive only: models of one family are not independent, so p-values are optimistic; cluster-bootstrap CIs are primary."""
    from scipy.stats import wilcoxon
    rows = []
    for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
        for split in ["family", "random"]:
            name = f"{data}_{split}"
            if not os.path.exists(f"results/raw/{name}.csv.gz"):
                continue
            d = load(name)
            for sel in ["greedy_iopt", "cov_greedy"]:
                pred = "gauss"
                for k, g in d[(d.pred == pred) & (d.sel.isin([sel, "random"]))].groupby("k"):
                    p = g.pivot(index="model", columns="sel", values="rmse").dropna()
                    diff = p[sel] - p["random"]
                    try:
                        pv = wilcoxon(diff).pvalue
                    except Exception:
                        pv = np.nan
                    rows.append(dict(data=data, split=split, sel=sel, k=k, n=len(p), mean_diff=diff.mean(), median_diff=diff.median(), p=pv))
    P = pd.DataFrame(rows)
    m = P.p.notna()
    order = np.argsort(P.p[m].values)
    adj = np.empty(m.sum()); pv = P.p[m].values
    run = 0.0; M = len(pv)
    for rank, i in enumerate(order):
        run = max(run, (M - rank) * pv[i]); adj[i] = min(1.0, run)
    P.loc[m, "p_holm"] = adj
    P.to_csv("results/summary_paired_tests.csv", index=False)
    return P


def worst_models():
    rows = []
    for name in ["mteb_mid_family", "mteb_dense_family", "mteb_wide_family"]:
        if not os.path.exists(f"results/raw/{name}.csv.gz"):
            continue
        d = load(name)
        k = 8
        x = d[(d.sel == "random") & (d.pred == "gauss") & (d.k == k)].set_index("model").rmse
        m = d[(d.sel == "random") & (d.pred == "mean") & (d.k == k)].set_index("model").rmse
        t = pd.DataFrame({"rmse_gauss": x, "rmse_mean_pred": m}).sort_values("rmse_gauss", ascending=False).head(8)
        t["data"] = name
        rows.append(t.reset_index())
    W = pd.concat(rows) if rows else pd.DataFrame()
    W.to_csv("results/summary_worst_models.csv", index=False)
    return W


if __name__ == "__main__":
    S = main_tables(); print("curves", S.shape)
    G = paired_gain_table(); print("gain", G.shape)
    K = k_needed(); print(K.round(3).to_string())
    fig_main(S); fig_selection_gain(G); fig_predictors()
    T = theory_vs_real(); fig_theory(T)
    fig_synth()
    C = fig_conditions()
    sp = fig_spectrum(); print(sp.round(3).to_string())
    W = worst_models(); print(W.round(2).to_string())
    P = paired_tests(); print((P.p_holm < 0.05).groupby([P.sel, P.split]).mean())
