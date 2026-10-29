"""Analysis of experiment outputs -> tables (LaTeX + CSV) and figures used in the paper.
Usage: python code/analyze.py   (reads artifacts/results/*.csv, writes artifacts/tables, artifacts/figures)
"""
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(ROOT, "artifacts", "results")
TAB = os.path.join(ROOT, "artifacts", "tables")
FIG = os.path.join(ROOT, "artifacts", "figures")
os.makedirs(TAB, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

NICE = {
    "arena140k": "Arena-140k", "arena55k": "Arena-55k", "st_crowd": "Arena-ST crowd",
    "st_Qwen2-72B-Instruct": "Arena-ST Qwen2-72B", "st_Meta-Llama-3-70B-Instruct": "Arena-ST Llama-3-70B",
    "st_Athene-70B": "Arena-ST Athene-70B", "st_Meta-Llama-3-8B-Instruct": "Arena-ST Llama-3-8B",
    "st_Mistral-7B-Instruct-v0.2": "Arena-ST Mistral-7B", "mt_human": "MT-Bench human", "mt_gpt4": "MT-Bench GPT-4",
    "nba": "NBA (39 seasons)",
}
ORDER = ["arena140k", "arena55k", "st_crowd", "st_Qwen2-72B-Instruct", "st_Meta-Llama-3-70B-Instruct",
         "st_Athene-70B", "st_Meta-Llama-3-8B-Instruct", "st_Mistral-7B-Instruct-v0.2", "mt_human", "mt_gpt4", "nba"]
DESIGN_COLOR = {"crowd": "tab:blue", "llm-judge": "tab:orange", "expert": "tab:green", "sports": "tab:red"}
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 200})


def nice(k):
    if k.startswith("nba") and k != "nba":
        return "NBA " + k[3:]
    return NICE.get(k, k)


def load_e1():
    e1 = pd.read_csv(os.path.join(RES, "e1_pairs.csv"))
    e1["group"] = np.where(e1.dataset.str.startswith("nba"), "nba", e1.dataset)
    e1["frac"] = e1.k / e1.N
    e1["local"] = e1.n_i + e1.n_j - e1.n_ij
    e1["frac_local"] = e1.k / e1.local
    e1["kappa"] = e1.z_sand * np.sqrt(e1.N) / e1.k          # global kappa (verified k)
    e1["kappa_pred"] = e1.z_sand * np.sqrt(e1.N) / e1.k_pred
    return e1


def top1(e1, kind):
    s = e1[(e1.kind == kind) & ((e1.pair_type == "leader") | ((e1.pair_type == "adjacent") & (e1.rank_i == 1)))]
    idx = s.groupby("dataset").k.idxmin()
    return s.loc[idx].set_index("dataset")


def fmt_k(k, N):
    return f"{int(k)} ({100 * k / N:.2g}\\%)"


def table_main(e1):
    rows = []
    t_drop, t_flip, t_add = top1(e1, "drop"), top1(e1, "flip"), top1(e1, "add")
    adj = e1[(e1.kind == "drop") & (e1.pair_type == "adjacent")]
    for ds in ORDER:
        if ds == "nba":
            keys = sorted(k for k in t_drop.index if k.startswith("nba"))
            td = t_drop.loc[keys]
            fr = td.k / td.N
            a = adj[adj.dataset.isin(keys)]
            med = a.groupby("dataset").frac.median()
            rows.append(dict(dataset=nice(ds), N=f"{int(td.N.median())}", m="30", pair="(season leader vs. challenger)",
                             z_top=f"{td.z_model.median():.1f}",
                             k_top1=f"{td.k.median():.0f} ({100 * fr.median():.2g}\\%) [{100 * fr.quantile(.25):.2g}, {100 * fr.quantile(.75):.2g}]",
                             k_flip=f"{t_flip.loc[keys].k.median():.0f}", k_add=f"{t_add.loc[keys].k.median():.0f}",
                             med_adj=f"{100 * med.median():.2g}\\%",
                             p_small=f"{100 * np.mean(a.frac <= 0.01):.0f}\\%",
                             p_sep=f"{100 * np.mean(a[a.z_model > 1.96].frac <= 0.01):.0f}\\% (n={int((a.z_model > 1.96).sum())})"))
            continue
        if ds not in t_drop.index:
            continue
        td = t_drop.loc[ds]
        a = adj[adj.dataset == ds]
        sep = a[a.z_model > 1.96]
        rows.append(dict(dataset=nice(ds), N=f"{int(td.N)}", m=f"{int(td.m)}", pair=f"{td.i} > {td.j}",
                         z_top=f"{td.z_model:.1f}", k_top1=fmt_k(td.k, td.N),
                         k_flip=f"{int(t_flip.loc[ds].k)}", k_add=f"{int(t_add.loc[ds].k)}",
                         med_adj=f"{100 * a.frac.median():.2g}\\%",
                         p_small=f"{100 * np.mean(a.frac <= 0.01):.0f}\\%",
                         p_sep=(f"{100 * np.mean(sep.frac <= 0.01):.0f}\\% (n={len(sep)})" if len(sep) else "--")))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(TAB, "t_main.csv"), index=False)
    return df


def design_of(ds):
    if ds.startswith("nba"):
        return "sports"
    if ds in ("arena140k", "arena55k", "st_crowd"):
        return "crowd"
    if ds == "mt_human":
        return "expert"
    return "llm-judge"


def fig_overview(e1):
    d = e1[(e1.kind == "drop") & (e1.k > 0)].copy()
    t1 = top1(e1, "drop").reset_index()
    t1["group"] = np.where(t1.dataset.str.startswith("nba"), "nba", t1.dataset)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), sharey=True)
    groups = [g for g in ORDER if g in set(d.group)]
    rng = np.random.default_rng(0)
    for ax, col, xl in [(axes[0], "frac", "verified drops / all comparisons $N$"),
                        (axes[1], "frac_local", "verified drops / local comparisons $n_{\\mathrm{loc}}$")]:
        for yi, g in enumerate(groups[::-1]):
            s = d[(d.group == g) & (d.pair_type == "adjacent")]
            c = DESIGN_COLOR[design_of(g if g != "nba" else "nba2015")]
            jit = rng.uniform(-0.18, 0.18, len(s))
            ax.scatter(s[col], yi + jit, s=6 if g == "nba" else 10, color=c, alpha=0.35 if g == "nba" else 0.7, lw=0)
            tt = t1[t1.group == g]
            tt = tt[tt.k > 0]
            if col == "frac":
                v = tt.k / tt.N
            else:
                v = tt.k / (tt.n_i + tt.n_j - tt.n_ij)
            if g == "nba":
                ax.plot([v.quantile(.25), v.quantile(.75)], [yi + 0.3, yi + 0.3], color="k", lw=1.2)
                ax.scatter([v.median()], [yi + 0.3], marker="*", s=40, color="k", zorder=5)
            else:
                ax.scatter(v, [yi + 0.3] * len(v), marker="*", s=40, color="k", zorder=5)
        ax.set_xscale("log")
        ax.set_xlabel(xl)
        ax.grid(axis="x", alpha=0.3)
        for v in (1e-3, 1e-2):
            ax.axvline(v, color="grey", lw=0.6, ls=":")
    axes[0].set_yticks(range(len(groups)))
    axes[0].set_yticklabels([nice(g) for g in groups[::-1]])
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=DESIGN_COLOR[k], label=k) for k in DESIGN_COLOR]
    h.append(Line2D([], [], marker="*", ls="", color="k", label="top-1 (k*$_{top1}$)"))
    axes[1].legend(handles=h, loc="lower right", frameon=True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_overview.pdf"))
    fig.savefig(os.path.join(FIG, "fig1_overview.png"))
    plt.close(fig)


def fig_decomposition(e1):
    d = e1[(e1.kind == "drop") & (e1.k > 0)].copy()
    d["kl"] = d.z_sand * np.sqrt(d.local) / d.k
    d["x"] = d.z_sand * np.sqrt(d.local)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = axes[0]
    for des in ["sports", "crowd", "llm-judge", "expert"]:
        s = d[d.dataset.map(design_of) == des]
        ax.scatter(s.x, s.k, s=5 if des == "sports" else 9, alpha=0.4 if des == "sports" else 0.75,
                   color=DESIGN_COLOR[des], lw=0, label=des)
    xs = np.logspace(np.log10(d.x.min() * 0.8), np.log10(d.x.max() * 1.2), 50)
    for kap, ls in [(1.5, ":"), (2.5, "--"), (4.0, "-.")]:
        ax.plot(xs, xs / kap, color="grey", ls=ls, lw=0.8, label=f"$k=z\\sqrt{{n_{{loc}}}}/{kap}$")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("$z_{\\mathrm{sand}}\\,\\sqrt{n_{\\mathrm{loc}}}$")
    ax.set_ylabel("verified min. drops $k^*$")
    ax.legend(fontsize=6, loc="upper left")
    ax.grid(alpha=0.3)
    ax = axes[1]
    groups = [g for g in ORDER if g in set(d.group)]
    data = [d[d.group == g].kl.values for g in groups]
    bp = ax.boxplot(data, vert=False, widths=0.6, showfliers=False, patch_artist=True)
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(DESIGN_COLOR[design_of(g if g != "nba" else "nba2015")]); patch.set_alpha(0.5)
    ax.set_yticks(range(1, len(groups) + 1)); ax.set_yticklabels([nice(g) for g in groups])
    ax.invert_yaxis()
    ax.set_xlabel("$\\hat\\kappa_{\\mathrm{loc}} = z_{\\mathrm{sand}}\\sqrt{n_{\\mathrm{loc}}}/k^*$")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_decomposition.pdf"))
    fig.savefig(os.path.join(FIG, "fig2_decomposition.png"))
    plt.close(fig)
    # regression table
    rows = []
    sub = d.copy()
    for name, cols in [("log z + log n_loc", ["lz", "lnl"]), ("log z + log N", ["lz", "lN"]),
                       ("log z + log n_loc + design", ["lz", "lnl", "D"])]:
        sub["lz"], sub["lnl"], sub["lN"] = np.log(sub.z_sand), np.log(sub.local), np.log(sub.N)
        X = [np.ones(len(sub))] + [sub[c].values for c in cols if c != "D"]
        names = ["const"] + [c for c in cols if c != "D"]
        if "D" in cols:
            for des in ["crowd", "llm-judge", "expert"]:
                X.append((sub.dataset.map(design_of) == des).astype(float).values)
                names.append("D_" + des)
        X = np.column_stack(X)
        yv = np.log(sub.k.values)
        # each dataset group (NBA seasons pooled into one group) gets equal total weight
        w = 1.0 / sub.groupby("group").k.transform("size").values
        sw = np.sqrt(w)
        b = np.linalg.lstsq(X * sw[:, None], yv * sw, rcond=None)[0]
        res = yv - X @ b
        # cluster bootstrap over groups for CIs
        rng = np.random.default_rng(1)
        keys = sub.group.unique()
        bs = []
        for _ in range(1000):
            pick = rng.choice(keys, len(keys), replace=True)
            ii = np.concatenate([np.where(sub.group.values == k)[0] for k in pick])
            try:
                bs.append(np.linalg.lstsq(X[ii] * sw[ii, None], yv[ii] * sw[ii], rcond=None)[0])
            except Exception:
                pass
        bs = np.array(bs)
        for nm, bb, lo, hi in zip(names, b, np.nanpercentile(bs, 2.5, axis=0), np.nanpercentile(bs, 97.5, axis=0)):
            r2 = 1 - np.sum(w * res ** 2) / np.sum(w * (yv - np.sum(w * yv) / np.sum(w)) ** 2)
            rows.append(dict(model=name, term=nm, coef=bb, lo=lo, hi=hi, R2_weighted=r2, n=len(yv)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB, "t_regression.csv"), index=False)
    g = d.groupby("group").agg(n_pairs=("k", "size"), kappa_loc_med=("kl", "median"),
                               kappa_loc_q1=("kl", lambda x: x.quantile(.25)), kappa_loc_q3=("kl", lambda x: x.quantile(.75)),
                               kappa_glob_med=("kappa", "median"),
                               share_local=("local", "median"), N=("N", "median"))
    g.to_csv(os.path.join(TAB, "t_kappa.csv"))
    return pd.DataFrame(rows), g


def main():
    e1 = load_e1()
    print(table_main(e1).to_string())
    fig_overview(e1)
    reg, kap = fig_decomposition(e1)
    print(reg.round(3).to_string())
    print(kap.round(3).to_string())


if __name__ == "__main__":
    main()
