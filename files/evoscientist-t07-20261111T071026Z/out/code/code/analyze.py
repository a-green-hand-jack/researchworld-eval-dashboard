"""Aggregate results/main.csv -> tables (results/tables/*.csv, *.tex) and figures (figures/*.pdf).

Aggregation protocol (see paper Sec. 4):
  * per (dataset, split, n, method): average each metric over seeds;
  * MAE/RMSE are reported as ratio to the 'random' baseline of the same dataset/split/n and
    summarised by the geometric mean across datasets (so large-error datasets do not dominate);
  * Spearman/Kendall are averaged arithmetically across datasets;
  * 95% CIs: hierarchical percentile bootstrap (1000 reps) resampling seeds within each
    dataset (the same seeds for all methods => paired) and then datasets.
"""
import os, sys, itertools
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); TAB = os.path.join(RES, "tables"); FIG = os.path.join(ROOT, "figures")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
df = pd.read_csv(os.path.join(RES, "main.csv"))
_s2 = pd.read_csv(os.path.join(RES, "stage2.csv"))          # post-hoc stage-2 methods (code/run_stage2.py)
df = pd.concat([df, _s2[~_s2.method.str.startswith("chk_")]], ignore_index=True)
B = 1000
rng = np.random.default_rng(0)

NICE = {
    "random": "Random sampling", "strat_mean": "Stratified sampling (difficulty)", "pps_resid_mean": "Neyman-PPS, weighted mean",
    "rs_learn": "Random + ridge (RS-Learn)", "aipw_ref": "AIPW (reference impl.)", "anchor_w": "Anchor points (k-medoids)",
    "pirt_k2": "pIRT (k=2)", "pirt_k8": "pIRT (k=8)", "irt_plugin": "IRT plug-in (random items)",
    "strat+ridge_cf": "Strat.\\ + ridge-DR (cross-fit)", "strat+ridge_is": "Strat.\\ + ridge-DR (in-sample)",
    "uniform+lat_cf": "Uniform + latent-DR (cf)", "uniform+knn_cf": "Uniform + kNN-DR (cf)",
    "pps_resid+lat_cf": "Neyman-DR (proposed)", "pps_resid+ridge_cf": "Neyman-PPS + ridge-DR (cf)",
    "rsres_strat": "Shrink-to-mean regression$^\\dagger$", "guard_strat": "Guarded shrink-to-mean$^\\dagger$",
    "rslearn_strat": "RS-Learn on strat.\\ coreset$^\\dagger$", "cal1d_strat": "1-D calibration$^\\dagger$",
}
NICE_P = {k: v.replace("\\ ", " ").replace("$^\\dagger$", "†") for k, v in NICE.items()}   # plain-text labels for figures
def nice(m):
    if m in NICE: return NICE[m]
    return m.replace("_", r"\_")


def tensor(sub, metric, methods):
    """-> dict dataset -> array (seeds x methods) (paired by seed)."""
    out = {}
    for d, g in sub.groupby("dataset"):
        p = g.pivot_table(index="seed", columns="method", values=metric)
        p = p.reindex(columns=methods)
        p = p.dropna(axis=0, how="any") if metric in ("mae", "rmse") else p
        out[d] = p.values
    return out


def summarise(T, ref_idx, ratio):
    """point estimate and bootstrap CI for each method; T: dataset->(seeds x methods)."""
    ds = list(T)
    def stat(means):  # means: (..., D, M)
        if ratio:
            return np.exp(np.mean(np.log(means / means[..., [ref_idx]]), axis=-2))
        return np.nanmean(means, axis=-2)
    pt = stat(np.stack([np.nanmean(T[d], 0) for d in ds]))
    per_ds = []
    for d in ds:
        a = T[d]; s = rng.integers(0, a.shape[0], (B, a.shape[0]))
        with np.errstate(all="ignore"):
            per_ds.append(np.nanmean(a[s], axis=1))        # B x M
    per_ds = np.stack(per_ds)                               # D x B x M
    dsel = rng.integers(0, len(ds), (B, len(ds)))           # B x D
    means = per_ds[dsel, np.arange(B)[:, None]]             # B x D x M
    with np.errstate(all="ignore"):
        boots = stat(means)
    return pt, np.nanpercentile(boots, 2.5, 0), np.nanpercentile(boots, 97.5, 0)


def table(split, n, methods, metrics=("mae", "rmse", "spearman", "kendall"), datasets=None):
    sub = df[(df.split == split) & (df.n == n)]
    if datasets: sub = sub[sub.dataset.isin(datasets)]
    ref = methods.index("random")
    cols = {}
    for met in metrics:
        T = tensor(sub, met, methods)
        pt, lo, hi = summarise(T, ref, ratio=met in ("mae", "rmse"))
        cols[met] = pt; cols[met + "_lo"] = lo; cols[met + "_hi"] = hi
    t = pd.DataFrame(cols, index=methods)
    return t


KEY = ["random", "strat_mean", "rs_learn", "aipw_ref", "anchor_w", "pirt_k2", "pirt_k8", "irt_plugin",
       "uniform+lat_cf", "uniform+knn_cf", "pps_resid+lat_cf", "pps_resid+ridge_cf", "strat+ridge_cf",
       "rsres_strat", "guard_strat", "rslearn_strat", "cal1d_strat"]
# Table 1 rows (main text)
T1 = ["random", "strat_mean", "rs_learn", "aipw_ref", "anchor_w", "pirt_k2", "irt_plugin", "strat+ridge_cf",
      "pps_resid+lat_cf", "rsres_strat", "guard_strat"]
GRID = [f"{d}+{p}_{m}" for d in ("uniform", "strat", "pps_resid") for p in ("ridge", "lat", "knn") for m in ("is", "cf")]
ABL = ["pps_resid_g0.0+lat_cf", "pps_resid_g0.6+lat_cf", "pps_resid_g1.0+lat_cf"]

def fmt(r, m, d=3):
    return f"{r[m]:.{d}f} [{r[m+'_lo']:.{d}f}, {r[m+'_hi']:.{d}f}]"

def to_tex(t, caption_cols, path, bold_min=("mae", "rmse"), bold_max=("spearman", "kendall"), d=3):
    lines = []
    best = {m: (t[m].min() if m in bold_min else t[m].max()) for m in caption_cols}
    for name, r in t.iterrows():
        cells = []
        for m in caption_cols:
            s = f"{r[m]:.{d}f}"
            if abs(r[m] - best[m]) < 1e-12: s = r"\textbf{" + s + "}"
            s += f" {{\\scriptsize[{r[m+'_lo']:.{d}f},{r[m+'_hi']:.{d}f}]}}"
            cells.append(s)
        lines.append(nice(name) + " & " + " & ".join(cells) + r" \\")
    open(path, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    splits = [s for s in ["interp", "org", "extrap"] if s in set(df.split)]
    budgets = sorted(df.n.unique())
    print(df.groupby(["split"]).agg(n_ds=("dataset", "nunique"), seeds=("seed", "nunique")))
    allm = [m for m in df.method.unique()]
    # complete methods only (some k-ablation methods only exist for first seeds)
    # ---------------- main tables ------------------------------------------------
    summary_rows = []
    for split in splits:
        for n in budgets:
            t = table(split, n, KEY)
            t.to_csv(os.path.join(TAB, f"key_{split}_n{n}.csv"))
            to_tex(t, ["mae", "rmse", "spearman", "kendall"], os.path.join(TAB, f"key_{split}_n{n}.tex"))
            tg = table(split, n, ["random"] + [m for m in GRID if m != "random"] + ABL)
            tg.to_csv(os.path.join(TAB, f"grid_{split}_n{n}.csv"))
    # ---------------- grid matrices (design x predictor) for n=50 ------------------
    for split in splits:
        tg = pd.read_csv(os.path.join(TAB, f"grid_{split}_n50.csv"), index_col=0)
        rows = []
        for d in ("uniform", "strat", "pps_resid"):
            row = {"design": d}
            for p in ("ridge", "lat", "knn"):
                for m in ("is", "cf"):
                    r = tg.loc[f"{d}+{p}_{m}"]
                    row[f"{p}_{m}"] = f"{r.mae:.3f}"
            rows.append(row)
        pd.DataFrame(rows).to_csv(os.path.join(TAB, f"gridmat_{split}_n50.csv"), index=False)

    # ---------------- significance (paired over datasets) ----------------------------
    pairs = [("pps_resid+lat_cf", "random"), ("pps_resid+lat_cf", "aipw_ref"), ("pps_resid+lat_cf", "uniform+lat_cf"),
             ("pps_resid+ridge_cf", "uniform+ridge_cf"), ("strat+ridge_cf", "uniform+ridge_cf"),
             ("aipw_ref", "random"), ("strat_mean", "random"),
             ("anchor_w", "random"), ("pirt_k2", "random"), ("rs_learn", "random"),
             ("rs_learn", "strat_mean"), ("guard_strat", "strat_mean"), ("guard_strat", "rs_learn"),
             ("rsres_strat", "rs_learn")]   # last three: post hoc (stage 2)
    sig = []
    for split in splits:
        for n in budgets:
            sub = df[(df.split == split) & (df.n == n)]
            ms = sorted(set(itertools.chain(*pairs)))
            piv = sub.groupby(["dataset", "method"]).mae.mean().unstack()
            for a, b in pairs:
                lr = np.log(piv[a] / piv[b]).dropna()
                try: p = wilcoxon(lr).pvalue
                except ValueError: p = np.nan
                sig.append(dict(split=split, n=n, a=a, b=b, geo_ratio=float(np.exp(lr.mean())), wins=int((lr < 0).sum()),
                                n_ds=len(lr), p=p))
    sig = pd.DataFrame(sig)
    sig["p_holm"] = np.nan
    for (s, n), g in sig.groupby(["split", "n"]):
        p = g.p.values; o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
        for r, i in enumerate(o):
            run = max(run, (m - r) * p[i]); adj[i] = min(1, run)
        sig.loc[g.index, "p_holm"] = adj
    sig.to_csv(os.path.join(TAB, "significance.csv"), index=False)

    # ---------------- per-dataset table for n=50 ------------------------------------
    for split in splits:
        sub = df[(df.split == split) & (df.n == 50) & df.method.isin(KEY)]
        piv = sub.groupby(["dataset", "method"]).mae.mean().unstack()
        rat = piv.div(piv["random"], axis=0)[KEY]
        rat.round(3).to_csv(os.path.join(TAB, f"perdataset_ratio_{split}_n50.csv"))
        seeds = sub.groupby(["dataset", "method"]).mae.std().unstack()
        sub2 = df[(df.split == split) & (df.n == 50) & (df.method == "random")].groupby("dataset").agg(
            mae=("mae", "mean"), true_sd=("mae", "size"))
        piv.round(4).to_csv(os.path.join(TAB, f"perdataset_mae_{split}_n50.csv"))

    # ---------------- figures --------------------------------------------------------
    style = {"random": ("k", "-", "o"), "strat_mean": ("tab:gray", "--", "s"), "aipw_ref": ("tab:blue", "-", "^"),
             "anchor_w": ("tab:orange", "-", "v"), "pirt_k2": ("tab:green", "-", "D"), "rs_learn": ("tab:brown", "-", "x"),
             "irt_plugin": ("tab:olive", ":", "x"),
             "strat+ridge_cf": ("tab:purple", "--", "P"), "pps_resid+lat_cf": ("tab:red", "-", "*"),
             "guard_strat": ("tab:pink", "-", "h")}
    fig, axes = plt.subplots(2, len(splits), figsize=(4.3 * len(splits), 6.2), squeeze=False)
    for j, split in enumerate(splits):
        for m, (c, ls, mk) in style.items():
            ys, los, his, sp = [], [], [], []
            for n in budgets:
                t = pd.read_csv(os.path.join(TAB, f"key_{split}_n{n}.csv"), index_col=0)
                if m not in t.index: ys.append(np.nan); los.append(np.nan); his.append(np.nan); sp.append(np.nan); continue
                r = t.loc[m]; ys.append(r.mae); los.append(r.mae_lo); his.append(r.mae_hi); sp.append(r.spearman)
            axes[0, j].plot(budgets, ys, color=c, ls=ls, marker=mk, label=NICE_P.get(m, m), ms=5)
            axes[0, j].fill_between(budgets, los, his, color=c, alpha=0.08)
            axes[1, j].plot(budgets, sp, color=c, ls=ls, marker=mk, ms=5)
        axes[0, j].set_xscale("log"); axes[1, j].set_xscale("log")
        axes[0, j].set_yscale("log")
        axes[0, j].set_title({"interp": "Random model split", "org": "Held-out developers", "extrap": "Top-30% models held out"}[split])
        axes[0, j].set_ylabel("MAE / MAE(random)"); axes[1, j].set_ylabel("Spearman"); axes[1, j].set_xlabel("budget n (items)")
        axes[0, j].axhline(1, color="k", lw=0.5)
        axes[0, j].set_xticks(budgets); axes[0, j].set_xticklabels(budgets)
        axes[1, j].set_xticks(budgets); axes[1, j].set_xticklabels(budgets)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=8, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(os.path.join(FIG, "fig_budget_curves.pdf")); fig.savefig(os.path.join(FIG, "fig_budget_curves.png"), dpi=110); plt.close(fig)

    # signed bias figure (n=50): mean signed error by split for several methods, per dataset-averaged
    bm = ["random", "aipw_ref", "rs_learn", "anchor_w", "pirt_k2", "irt_plugin", "pps_resid+lat_cf", "guard_strat"]
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    w = 0.8 / len(splits)
    for j, split in enumerate(splits):
        sub = df[(df.split == split) & (df.n == 50) & df.method.isin(bm)]
        b = sub.groupby(["dataset", "method"]).bias.mean().unstack()[bm]
        mu = b.mean(0); se = b.std(0) / np.sqrt(len(b))
        ax.bar(np.arange(len(bm)) + j * w, mu, w, yerr=1.96 * se, label=split, capsize=2)
    ax.axhline(0, color="k", lw=0.5); ax.set_xticks(np.arange(len(bm)) + w); ax.set_xticklabels([NICE_P.get(m, m) for m in bm], rotation=30, ha="right", fontsize=7)
    ax.set_ylabel("mean signed error (pred - true)"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_bias.pdf")); fig.savefig(os.path.join(FIG, "fig_bias.png"), dpi=110); plt.close(fig)

    # per-dataset heatmap (extrap & interp) n=50
    hm = ["strat_mean", "rs_learn", "aipw_ref", "anchor_w", "pirt_k2", "strat+ridge_cf", "pps_resid+lat_cf", "guard_strat"]
    fig, axes = plt.subplots(1, len(splits), figsize=(4.4 * len(splits), 4.2), sharey=True)
    for ax, split in zip(np.atleast_1d(axes), splits):
        sub = df[(df.split == split) & (df.n == 50) & df.method.isin(hm + ["random"])]
        piv = sub.groupby(["dataset", "method"]).mae.mean().unstack()
        rat = np.log2(piv.div(piv["random"], axis=0)[hm])
        im = ax.imshow(rat.values, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
        ax.set_xticks(range(len(hm))); ax.set_xticklabels([NICE_P.get(m, m) for m in hm], rotation=60, ha="right", fontsize=6)
        ax.set_yticks(range(len(rat))); ax.set_yticklabels(rat.index, fontsize=7); ax.set_title(split)
        for (i, j), v in np.ndenumerate(rat.values): ax.text(j, i, f"{2**v:.2f}", ha="center", va="center", fontsize=5)
    fig.colorbar(im, ax=axes, shrink=0.8, label="log2 MAE ratio vs random (blue = better)")
    fig.savefig(os.path.join(FIG, "fig_heatmap.pdf"), bbox_inches="tight"); fig.savefig(os.path.join(FIG, "fig_heatmap.png"), dpi=110, bbox_inches="tight"); plt.close(fig)
    # ---------------- Table 1 (main text): MAE ratio [CI] and Spearman per split, one file per budget --------
    for n in budgets:
        lines = []
        tabs = {s: pd.read_csv(os.path.join(TAB, f"key_{s}_n{n}.csv"), index_col=0) for s in splits}
        for m in T1:
            cells = []
            for s in splits:
                r = tabs[s].loc[m]
                best_mae = tabs[s].loc[T1, "mae"].min(); best_rho = tabs[s].loc[T1, "spearman"].max()
                a = f"{r.mae:.2f}"; a = (r"\textbf{" + a + "}") if abs(r.mae - best_mae) < 1e-12 else a
                b = f"{r.spearman:.2f}"; b = (r"\textbf{" + b + "}") if abs(r.spearman - best_rho) < 1e-12 else b
                cells.append(f"{a} {{\\scriptsize[{r.mae_lo:.2f},{r.mae_hi:.2f}]}} & {b}")
            lines.append(nice(m) + " & " + " & ".join(cells) + r" \\")
        open(os.path.join(TAB, f"table1_n{n}.tex"), "w").write("\n".join(lines) + "\n")

    # ---------------- ablations of the proposed design (n=50, seeds 0-9: k=1,4 fits exist only there) -------
    abl_methods = ["random", "uniform+lat_cf", "pps_resid+lat_cf", "pps_resid_g0.0+lat_cf", "pps_resid_g0.6+lat_cf",
                   "pps_resid_g1.0+lat_cf", "uniform+lat_cf_k1", "pps_resid+lat_cf_k1", "uniform+lat_cf_k4",
                   "pps_resid+lat_cf_k4", "uniform+lat_cf_k8", "pps_resid+lat_cf_k8"]
    rows = []
    for split in splits:
        sub = df[(df.split == split) & (df.n == 50) & (df.seed < 10)]
        T = tensor(sub, "mae", abl_methods)
        pt, lo, hi = summarise(T, 0, ratio=True)
        for m, a, b, c in zip(abl_methods, pt, lo, hi):
            rows.append(dict(split=split, method=m, mae_ratio=a, lo=b, hi=c))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, "ablation_seeds0-9_n50.csv"), index=False)
    print("analysis done")
