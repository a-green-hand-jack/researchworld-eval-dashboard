"""Produce all tables / figures of the paper from results/raw/<tag>. Usage: analyze.py TAG [OUTDIR]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_results import load_all
from stats_util import *

TAG = sys.argv[1] if len(sys.argv) > 1 else "main"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/work/paper"
os.makedirs(f"{OUT}/tables", exist_ok=True); os.makedirs(f"{OUT}/figs", exist_ok=True)
df = load_all(TAG)
if TAG == "shift":  # add the main-run 'top' split (seeds 0-9 only, same seeds as the shift run) as the reference severity
    _m = load_all("main")
    df = pd.concat([df, _m[(_m.protocol == "top") & (_m.seed <= 9)]], ignore_index=True)
df["method"] = np.where(df.design == "AUTO", "AUTO/" + df.est, df.method)
df["mse"] = df.rmse ** 2
df["bias2"] = df.bias ** 2
PROTS = [p for p in ["random", "org", "top10", "top", "top50", "bottom"] if p in set(df.protocol)]
PNAME = {"random": "Random split", "org": "Held-out organisations", "top": "Stronger targets (extrapolation)", "top10": "Top-10\\% targets", "top50": "Top-50\\% targets", "bottom": "Weakest-25\\% targets"}
NS = sorted(n for n in df.n.unique() if n > 0)

NAMES = {
    "rand/mean": "Random sampling",
    "strat/mean": "Difficulty-stratified sampling",
    "rand/lin": "Random + linear calibration",
    "rand/ridge": "Random + ridge regression",
    "anchor/mean": "Anchor points (weighted mean)",
    "anchor/plug4": "Anchor points + IRT (tinyBenchmarks-style)",
    "dopt4/plug": "D-optimal items + IRT (info-based)",
    "rand/irt4": "Random + IRT (pure)",
    "rand/greg4": "Random + IRT-AIPW",
    "pps1.0/greg4": "VA-PPS + IRT-AIPW",
    "pps1.0/irt4": "VA-PPS + IRT (pure)",
    "pps1.0/cal4": "VA-PPS + Cal-IRT (ours)",
    "pps1.0/shrcal4": "VA-PPS + ShrinkCal-IRT (ours)",
    "AUTO/minimax": "AUTO (pseudo-shift, minimax)",
    "AUTO/mean": "AUTO (pseudo-shift, mean)",
}
MAIN = list(NAMES)
KEYFIG = ["rand/mean", "strat/mean", "anchor/plug4", "rand/ridge", "rand/greg4", "pps1.0/irt4", "pps1.0/cal4", "pps1.0/shrcal4"]
COL = {"rand/mean": "#000000", "strat/mean": "#7f7f7f", "anchor/plug4": "#E69F00", "rand/ridge": "#56B4E9", "rand/greg4": "#009E73",
       "pps1.0/irt4": "#CC79A7", "pps1.0/cal4": "#D55E00", "pps1.0/shrcal4": "#0072B2"}


def fmt(v, lo, hi):
    return f"{v:.2f}\\,\\scriptsize({lo:.2f}--{hi:.2f})"


def rel_table(methods, ns, fname, caption_only=False):
    rows = {m: [] for m in methods}
    res = {}
    for p in PROTS:
        for n in ns:
            arr, benches = tensor(df, methods, p, n, "mse")
            bi = methods.index("rand/mean")
            pt, lo, hi, _ = boot_rel(arr, bi, B=1000)
            for i, m in enumerate(methods):
                res[(m, p, n)] = (pt[i], lo[i], hi[i])
    lines = []
    for m in methods:
        cells = []
        for p in PROTS:
            for n in ns:
                v = res[(m, p, n)]
                cells.append(fmt(*v))
        lines.append(f"{NAMES.get(m, m.replace('_', ' '))} & " + " & ".join(cells) + r" \\")
    hdr1 = " & ".join([f"\\multicolumn{{{len(ns)}}}{{c}}{{{PNAME[p]}}}" for p in PROTS])
    hdr2 = " & ".join([f"$n$={n}" for p in PROTS for n in ns])
    tab = "\\begin{tabular}{l" + "c" * (len(PROTS) * len(ns)) + "}\n\\toprule\n & " + hdr1 + " \\\\\n" + " & " + hdr2 + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)
    pd.Series({f"{m}|{p}|{n}": v for (m, p, n), v in res.items()}).to_csv(f"{OUT}/tables/{fname}.csv")
    return res


def abs_rmse_table():
    rows = []
    for p in PROTS:
        for n in NS:
            s = df[(df.protocol == p) & (df.n == n) & (df.method == "rand/mean")]
            g = s.groupby("bench").mse.mean().pow(0.5)
            rows.append(dict(protocol=p, n=n, **{b: v for b, v in g.items()}))
    pd.DataFrame(rows).to_csv(f"{OUT}/tables/abs_rmse_random.csv", index=False)


def pair_tests(pairs, ns, fname):
    """log-ratio CIs for pairs (a vs b): relative RMSE a / b, hierarchical bootstrap."""
    lines = []
    for a, b in pairs:
        cells = []
        for p in PROTS:
            for n in ns:
                ms = [a, b, "rand/mean"]
                arr, _ = tensor(df, ms, p, n, "mse")
                pt, lo, hi, d = boot_rel(arr, 2, B=1000, diff_pairs=[(0, 1)])
                v, l, h = d[(0, 1)]
                star = "*" if (l > 0 or h < 0) else ""
                cells.append(f"{np.exp(v):.2f}\\,\\scriptsize({np.exp(l):.2f}--{np.exp(h):.2f}){star}")
        lines.append(f"{NAMES.get(a, a)} vs.\\ {NAMES.get(b, b)} & " + " & ".join(cells) + r" \\")
    hdr1 = " & ".join([f"\\multicolumn{{{len(ns)}}}{{c}}{{{PNAME[p]}}}" for p in PROTS])
    hdr2 = " & ".join([f"$n$={n}" for p in PROTS for n in ns])
    tab = "\\begin{tabular}{l" + "c" * (len(PROTS) * len(ns)) + "}\n\\toprule\n & " + hdr1 + " \\\\\n" + " & " + hdr2 + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)


def rank_table(methods, ns, fname, metric):
    lines = []
    res = {}
    for p in PROTS:
        for n in ns:
            arr, _ = tensor(df, methods, p, n, metric)
            pt, lo, hi = boot_mean_diff(arr, methods.index("rand/mean"), B=500)
            base = np.nanmean(arr[methods.index("rand/mean")])
            for i, m in enumerate(methods):
                res[(m, p, n)] = (base + pt[i], pt[i], lo[i], hi[i])
    for m in methods:
        cells = []
        for p in PROTS:
            for n in ns:
                a, d, l, h = res[(m, p, n)]
                cells.append(f"{a:.3f}" if m == "rand/mean" else f"{a:.3f}\\,\\scriptsize({d:+.3f}; {l:+.3f}..{h:+.3f})")
        lines.append(f"{NAMES.get(m, m)} & " + " & ".join(cells) + r" \\")
    hdr1 = " & ".join([f"\\multicolumn{{{len(ns)}}}{{c}}{{{PNAME[p]}}}" for p in PROTS])
    hdr2 = " & ".join([f"$n$={n}" for p in PROTS for n in ns])
    tab = "\\begin{tabular}{l" + "c" * (len(PROTS) * len(ns)) + "}\n\\toprule\n & " + hdr1 + " \\\\\n" + " & " + hdr2 + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)
    pd.Series({f"{m}|{p}|{n}": v[0] for (m, p, n), v in res.items()}).to_csv(f"{OUT}/tables/{fname}.csv")


def fig_curves(methods, fname):
    fig, axs = plt.subplots(1, len(PROTS), figsize=(3.4 * len(PROTS), 3.1), sharey=True)
    for ax, p in zip(np.atleast_1d(axs), PROTS):
        data = {m: [] for m in methods}
        for n in NS:
            arr, _ = tensor(df, methods, p, n, "mse")
            pt, lo, hi, _ = boot_rel(arr, methods.index("rand/mean"), B=500)
            for i, m in enumerate(methods):
                data[m].append((pt[i], lo[i], hi[i]))
        for m in methods:
            if m == "rand/mean":
                continue
            a = np.array(data[m])
            ax.plot(NS, a[:, 0], "-o", ms=3, lw=1.4, color=COL.get(m), label=NAMES.get(m, m))
            ax.fill_between(NS, a[:, 1], a[:, 2], color=COL.get(m), alpha=0.12, lw=0)
        ax.axhline(1, color="k", lw=0.8, ls="--")
        ax.set_xscale("log"); ax.set_xticks(NS); ax.set_xticklabels(NS)
        ax.set_title(PNAME[p], fontsize=10); ax.set_xlabel("coreset size $n$", fontsize=9)
        ax.tick_params(labelsize=8.5); ax.grid(alpha=0.25)
    np.atleast_1d(axs)[0].set_ylabel("RMSE relative to random sampling", fontsize=9)
    np.atleast_1d(axs)[0].set_ylim(0.3, 2.0)
    h, l = np.atleast_1d(axs)[-1].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    fig.savefig(f"{OUT}/figs/{fname}.pdf", bbox_inches="tight"); plt.close(fig)


def bias_table(methods, n, fname):
    lines = []
    out = {}
    for m in methods:
        cells = []
        for p in PROTS:
            s = df[(df.protocol == p) & (df.n == n) & (df.method == m)]
            share = s.bias2.mean() / s.mse.mean()
            # signed bias in accuracy points, benchmark-averaged
            sb = s.groupby("bench").bias.mean().mean() * 100
            cells.append(f"{sb:+.2f} & {100*share:.0f}\\%")
            out[(m, p)] = (sb, share)
        lines.append(f"{NAMES.get(m, m)} & " + " & ".join(cells) + r" \\")
    hdr1 = " & ".join([f"\\multicolumn{{2}}{{c}}{{{PNAME[p]}}}" for p in PROTS])
    hdr2 = " & ".join(["mean err (pts)", "bias$^2$/MSE"] * len(PROTS))
    tab = "\\begin{tabular}{l" + "cc" * len(PROTS) + "}\n\\toprule\n & " + hdr1 + " \\\\\n & " + hdr2 + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)


def per_bench(methods, p, n, fname):
    arr, benches = tensor(df, methods, p, n, "mse")
    base = methods.index("rand/mean")
    rel = np.sqrt(np.nanmean(arr, 2) / np.nanmean(arr[base], 1)[None])  # [M,B]
    fig, ax = plt.subplots(figsize=(7.2, 0.32 * len(methods) + 0.9))
    im = ax.imshow(np.log2(rel), cmap="RdBu_r", vmin=-1.5, vmax=1.5, aspect="auto")
    ax.set_xticks(range(len(benches))); ax.set_xticklabels([b.replace("_", " ") for b in benches], rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(methods))); ax.set_yticklabels([NAMES.get(m, m) for m in methods], fontsize=7)
    for i in range(rel.shape[0]):
        for j in range(rel.shape[1]):
            ax.text(j, i, f"{rel[i, j]:.2f}", ha="center", va="center", fontsize=5.5)
    fig.colorbar(im, ax=ax, label="log2 relative RMSE", fraction=0.025)
    fig.tight_layout(); fig.savefig(f"{OUT}/figs/{fname}.pdf", bbox_inches="tight"); plt.close(fig)
    pd.DataFrame(rel, index=methods, columns=benches).to_csv(f"{OUT}/tables/{fname}.csv")


def auto_choice_table(fname):
    """Share of AUTO selections (minimax criterion) by estimator family, per split type and budget."""
    s = df[(df.design == "AUTO") & (df.est == "minimax")].copy()
    s["fam"] = s.chosen.str.split("/").str[1].str.replace(r"\d+$", "", regex=True)
    t = s.groupby(["protocol", "n"]).fam.value_counts(normalize=True).unstack(fill_value=0)
    t.to_csv(f"{OUT}/tables/{fname}.csv")
    fams = ["cal", "shrcal", "calgreg", "greg", "plug", "irt", "ridge", "lin", "mean"]
    for f in fams:
        if f not in t.columns:
            t[f] = 0.0
    lab = {"cal": "Cal", "shrcal": "ShrinkCal", "calgreg": "Cal+AIPW", "greg": "AIPW", "plug": "plug-in", "irt": "IRT", "ridge": "ridge", "lin": "linear", "mean": "mean"}
    lines = []
    for (p, n), row in t.iterrows():
        if n in (25, 100):
            lines.append(f"{PNAME[p]} & {n} & " + " & ".join(f"{100*row[f]:.0f}" for f in fams) + r" \\")
    tab = "\\begin{tabular}{lr" + "r" * len(fams) + "}\n\\toprule\nsplit & $n$ & " + " & ".join(lab[f] for f in fams) + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)


def design_effects(fname):
    """Paired design effect: same estimator, different design (relative RMSE of A / B)."""
    pairs = []
    for e in ["cal4", "shrcal4", "greg4", "mean"]:
        pairs += [(f"strat/{e}", f"rand/{e}"), (f"pps0.5/{e}", f"strat/{e}"), (f"pps1.0/{e}", f"strat/{e}"), (f"pps1.0/{e}", f"rand/{e}")]
    pairs = [(a, b) for a, b in pairs if a in set(df.method) and b in set(df.method)]
    for a, b in pairs:
        NAMES.setdefault(a, a); NAMES.setdefault(b, b)
    pair_tests(pairs, [25, 100], fname)


def win_counts(methods, fname):
    """number of benchmarks (out of those available) where method has lower MSE than random sampling (seed-averaged)."""
    lines = []
    for m in methods:
        cells = []
        for p in PROTS:
            for n in [25, 100]:
                arr, benches = tensor(df, [m, "rand/mean"], p, n, "mse")
                w = int((np.nanmean(arr[0], 1) < np.nanmean(arr[1], 1)).sum())
                cells.append(f"{w}/{len(benches)}")
        lines.append(f"{NAMES.get(m, m)} & " + " & ".join(cells) + r" \\")
    hdr1 = " & ".join([f"\\multicolumn{{2}}{{c}}{{{PNAME[p]}}}" for p in PROTS])
    hdr2 = " & ".join([f"$n$={n}" for p in PROTS for n in [25, 100]])
    tab = "\\begin{tabular}{l" + "c" * (len(PROTS) * 2) + "}\n\\toprule\n & " + hdr1 + " \\\\\n & " + hdr2 + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)


def abs_rmse_methods(methods, protos, n, fname):
    """absolute RMSE (accuracy points) per benchmark, averaged over seeds as sqrt(mean MSE)."""
    rows = {}
    for p in protos:
        for m in methods:
            s = df[(df.protocol == p) & (df.n == n) & (df.method == m)]
            rows[(p, NAMES.get(m, m))] = (100 * s.groupby("bench").mse.mean().pow(0.5))
    t = pd.DataFrame(rows).T
    t.to_csv(f"{OUT}/tables/{fname}.csv")
    cols = list(t.columns)
    lines = [f"{p[0] if False else ''}{PNAME[p[0]] if False else p[0]} & {p[1]} & " + " & ".join(f"{v:.1f}" for v in t.loc[p].values) + r" \\" for p in t.index]
    tab = "\\begin{tabular}{ll" + "r" * len(cols) + "}\n\\toprule\nsplit & method & " + " & ".join(c.replace("_", " ") for c in cols) + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n"
    open(f"{OUT}/tables/{fname}.tex", "w").write(tab)


if __name__ == "__main__":
    if TAG == "shift":
        sm = [m for m in ["rand/mean", "strat/mean", "anchor/plug4", "rand/ridge", "rand/greg4", "pps1.0/irt4", "pps1.0/cal4", "pps1.0/shrcal4"] if m in set(df.method)]
        rel_table(sm, [25, 100], "shift_rel")
        bias_table(sm, 100, "shift_bias_n100")
        print("done shift"); sys.exit()
    abs_rmse_table()
    avail = set(df.method)
    main = [m for m in MAIN if m in avail]
    rel_table(main, [25, 100], "main_rel_rmse")
    rel_table(main, NS, "full_rel_rmse")
    rank_table([m for m in main if m != "AUTO/mean"], [25, 100], "spearman", "spearman")
    rank_table([m for m in main if m != "AUTO/mean"], [25, 100], "kendall", "kendall")
    fig_curves([m for m in KEYFIG if m in avail], "curves")
    bias_table([m for m in main], 100, "bias_n100")
    bias_table([m for m in main], 25, "bias_n25")
    pair_tests([("pps1.0/cal4", "rand/greg4"), ("pps1.0/cal4", "strat/mean"), ("pps1.0/cal4", "rand/ridge"), ("pps1.0/shrcal4", "rand/ridge"),
                ("pps1.0/shrcal4", "pps1.0/cal4"), ("pps1.0/cal4", "pps1.0/greg4"), ("pps1.0/greg4", "strat/mean"), ("AUTO/minimax", "pps1.0/cal4")], [25, 100], "pairs")
    # ablations: design x estimator at fixed d=4
    ab = [f"{d}/{e}" for d in ["rand", "strat", "pps0.5", "pps1.0"] for e in ["mean", "irt4", "plug4", "greg4", "gregcf4", "cal4", "calgreg4", "shrcal4"] if f"{d}/{e}" in avail]
    for m in ab: NAMES.setdefault(m, m.replace("_", " "))
    rel_table(["rand/mean"] + [m for m in ab if m != "rand/mean"], [25, 100], "ablation_design_est")
    abd = [f"pps1.0/{e}{d}" for e in ["irt", "cal", "shrcal", "greg"] for d in (2, 4, 8) if f"pps1.0/{e}{d}" in avail]
    for m in abd: NAMES.setdefault(m, m)
    rel_table(["rand/mean"] + abd, [25, 100], "ablation_dim")
    other = [m for m in ["anchor/cal4", "anchor/ridge", "anchor/greg4", "dopt4/cal", "dopt4/irt", "dopt2/cal", "dopt8/cal", "strat/ridge", "pps1.0/ridge", "pps1.0/lin"] if m in avail]
    for m in other: NAMES.setdefault(m, m)
    rel_table(["rand/mean"] + other, [25, 100], "ablation_other")
    per_bench([m for m in KEYFIG if m in avail], "top", 100, "perbench_top100")
    per_bench([m for m in KEYFIG if m in avail], "random", 100, "perbench_random100")
    auto_choice_table("auto_choice")
    design_effects("design_effects")
    win_counts([m for m in main if m != "rand/mean"], "wins")
    abs_rmse_methods(["rand/mean", "strat/mean", "rand/greg4", "pps1.0/cal4", "pps1.0/shrcal4"], ["random", "top"], 100, "abs_rmse_n100")
    print("done")
