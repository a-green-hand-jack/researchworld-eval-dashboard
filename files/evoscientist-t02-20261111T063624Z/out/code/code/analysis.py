"""Produces every figure/table/number used in the paper from results/*.jsonl.
Run:  python analysis.py   (writes ../paper/figs/*.pdf, ../paper/tables/*.tex, ../results/summary.json)"""
import os, json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from analysis_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "paper", "figs")
TAB = os.path.join(HERE, "..", "paper", "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.25})
S = {}  # summary numbers
XT = [[8, 16, 32, 64, 128, 256, 512]]
rng2 = np.random.default_rng(1)


def exists(n):
    return os.path.exists(os.path.join(RES, n + ".jsonl"))


def loglog_slope(widths, vals_by_w, n=2000):
    """OLS slope of log(median over seeds) on log(width); bootstrap CI by resampling seeds within width."""
    ws = np.array(sorted(vals_by_w))
    def fit(vs):
        y = np.log([np.median(v) for v in vs]); x = np.log(ws)
        return np.polyfit(x, y, 1)[0]
    pt = fit([vals_by_w[w] for w in ws])
    bs = []
    for _ in range(n):
        vs = [rng2.choice(vals_by_w[w], len(vals_by_w[w])) for w in ws]
        bs.append(fit(vs))
    return pt, float(np.quantile(bs, .025)), float(np.quantile(bs, .975))


def spearman_boot(x, y, n=2000):
    x = np.asarray(x, float); y = np.asarray(y, float)
    rho, p = stats.spearmanr(x, y)
    bs = []
    for _ in range(n):
        i = rng2.integers(0, len(x), len(x))
        if len(set(x[i])) > 1 and len(set(y[i])) > 1:
            bs.append(stats.spearmanr(x[i], y[i])[0])
    return float(rho), float(p), float(np.quantile(bs, .025)), float(np.quantile(bs, .975))


def errbar(ax, xs, stat, cens=None, **kw):
    """Median + bootstrap 95% CI. Points flagged in `cens` (>=50% of runs censored: values are lower bounds)
    are drawn hollow."""
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return
    m = np.array([s[0] for s in stat]); lo = np.array([s[1] for s in stat]); hi = np.array([s[2] for s in stat])
    cens = np.array([bool(s[3]) if len(s) > 3 else False for s in stat]) if cens is None else np.asarray(cens, bool)
    line = ax.errorbar(xs, m, yerr=[m - lo, hi - m], capsize=2, marker=None, lw=1, **kw)
    c = line[0].get_color()
    ax.plot(xs[~cens], m[~cens], "o", ms=3, color=c)
    if cens.any():
        ax.plot(xs[cens], m[cens], "o", ms=3.5, mfc="white", mec=c)


def cflag(rs):
    return n_cens(rs) * 2 >= len(rs)


def wticks(ax, ws):
    ws = sorted(set(ws))
    ax.set_xscale("log")
    ax.set_xticks(ws); ax.set_xticklabels([str(w) for w in ws], rotation=90, fontsize=5.5)
    ax.minorticks_off()


# ============================================================ E1 : core width sweep (MLP)
def e1():
    rows = load("e1_mlp_width")
    g = group(rows, lambda r: r["cfg"]["width"])
    ws = list(g)
    fig, ax = plt.subplots(1, 4, figsize=(11, 2.5))
    # (a) example curves
    cols = plt.cm.viridis(np.linspace(0, .9, 3))
    for w, c in zip([w for w in (48, 128, 512) if w in g], cols):
        r = [x for x in g[w] if x["cfg"]["seed"] == 100][0]
        cv = np.array(r["curve"])
        ax[0].plot(cv[:, 0] + 1, cv[:, 1], color=c, ls="--", lw=1)
        ax[0].plot(cv[:, 0] + 1, cv[:, 3], color=c, lw=1.2, label=f"w={w}")
    ax[0].set_xscale("log"); ax[0].set_xlabel("step"); ax[0].set_ylabel("accuracy"); ax[0].legend()
    ax[0].set_title("(a) train (dashed) / val (solid)")
    # (b) t_train, t_val vs width
    tt = [summarize(g[w], "tt") for w in ws]; tv = [summarize(g[w], "tv") for w in ws]
    errbar(ax[1], ws, tt, label=r"$t_{train}$"); errbar(ax[1], ws, tv, label=r"$t_{val}$")
    for w in ws:
        k = n_cens(g[w])
        if k:
            ax[1].annotate(f"{k}c", (w, summarize(g[w], "tv")[0]), fontsize=6, color="C1", xytext=(0, 4), textcoords="offset points")
    ax[1].set_yscale("log"); wticks(ax[1], ws); ax[1].set_xlabel("width"); ax[1].legend(); ax[1].set_title("(b) time to 99% acc. (hollow: censored)")
    # (c) R
    R = [summarize(g[w], "R") for w in ws]
    errbar(ax[2], ws, R, color="C2")
    ax[2].set_yscale("log"); wticks(ax[2], ws); ax[2].set_xlabel("width"); ax[2].set_title(r"(c) relative delay $t_{val}/t_{train}$")
    D = [summarize(g[w], "D") for w in ws]
    errbar(ax[3], ws, D, color="C3")
    ax[3].set_yscale("log"); wticks(ax[3], ws); ax[3].set_xlabel("width"); ax[3].set_title(r"(d) absolute delay $t_{val}-t_{train}$")
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_e1.pdf")); plt.close()
    # statistics
    S["e1_n_runs"] = len(rows)
    S["e1_final_param_L2norm_mean_sd"] = {str(w): (float(np.mean([r["final"][5] for r in g[w]])), float(np.std([r["final"][5] for r in g[w]], ddof=1))) for w in ws}
    S["e1_final_val_acc_min_over_seeds"] = {str(w): float(min(r["final"][3] for r in g[w])) for w in ws}
    S["e1_slope_tt"] = loglog_slope(ws, {w: [r["tt"] for r in g[w]] for w in ws})
    ob = [w for w in ws if n_cens(g[w]) == 0]
    S["e1_widths_uncensored"] = ob
    S["e1_slope_tt_uncens"] = loglog_slope(ob, {w: [r["tt"] for r in g[w]] for w in ob})
    S["e1_slope_tv_uncens"] = loglog_slope(ob, {w: [r["tv"] for r in g[w]] for w in ob}) if len(ob) > 2 else None
    S["e1_slope_R_uncens"] = loglog_slope(ob, {w: [r["tv"] / r["tt"] for r in g[w]] for w in ob}) if len(ob) > 2 else None
    S["e1_slope_D_uncens"] = loglog_slope(ob, {w: [r["tv"] - r["tt"] for r in g[w]] for w in ob}) if len(ob) > 2 else None
    xs = [r["cfg"]["width"] for r in rows if r["cfg"]["width"] in ob]
    for f, fn in (("tt", lambda r: r["tt"]), ("tv", lambda r: r["tv"]), ("R", lambda r: r["tv"] / r["tt"]),
                  ("D", lambda r: r["tv"] - r["tt"])):
        ys = [fn(r) for r in rows if r["cfg"]["width"] in ob]
        S[f"e1_spearman_{f}"] = spearman_boot(xs, ys)
    # table
    lines = [r"\begin{tabular}{rrcccccc}", r"\toprule",
             r"width & params & $t_{train}$ & $t_{val}$ & $R$ & $D$ & cens. & $n$ \\", r"\midrule"]
    for w in ws:
        a = summarize(g[w], "tt"); b = summarize(g[w], "tv"); c = summarize(g[w], "R"); d = summarize(g[w], "D")
        f = lambda s: f"{s[0]:.0f} [{s[1]:.0f},{s[2]:.0f}]"
        fr = lambda s: f"{s[0]:.0f} [{s[1]:.0f},{s[2]:.0f}]"
        pre = r"$\geq$" if n_cens(g[w]) * 2 >= len(g[w]) else ""
        lines.append(f"{w} & {g[w][0]['n_params']/1e3:.0f}k & {f(a)} & {pre}{f(b)} & {pre}{fr(c)} & {pre}{f(d)} & {n_cens(g[w])}/{len(g[w])} & {len(g[w])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "tab_e1.tex"), "w").write("\n".join(lines))


# ============================================================ memorisation probes (E2,E3,E8)
def probe():
    rows = []
    for n in ("e1_mlp_width", "e2_random", "e3_frac", "e8_small"):
        if exists(n):
            rows += load(n)
    for r in rows:
        r["frac"] = r["cfg"]["train_frac"]; r["rand"] = r["cfg"]["shuffle_labels"]
    g = group(rows, lambda r: (r["frac"], r["rand"], r["cfg"]["width"]))
    fracs = sorted({k[0] for k in g})
    fig, ax = plt.subplots(1, 3, figsize=(8.5, 2.6))
    for i, f in enumerate(fracs):
        for rand, ls, mk in ((False, "-", "o"), (True, "--", "s")):
            ks = [k for k in g if k[0] == f and k[1] == rand]
            ws = [k[2] for k in ks]
            fit = [np.mean([not r["train_cens"] for r in g[k]]) for k in ks]
            ax[0].plot(ws, fit, ls=ls, marker=mk, ms=3, color=f"C{i}", label=f"f={f} {'random' if rand else 'real'}")
    ax[0].set_xscale("log"); ax[0].set_xlabel("width"); ax[0].set_ylabel("fraction of runs reaching 99% train acc.")
    ax[0].legend(ncol=1, fontsize=5.5); ax[0].set_title("(a) fits training set within budget")
    # (b) real vs random t_train for matching groups
    xs, ys, cs = [], [], []
    for k in g:
        if k[1]:
            kr = (k[0], False, k[2])
            if kr in g:
                a = [r["tt"] for r in g[kr] if not r["train_cens"]]; b = [r["tt"] for r in g[k] if not r["train_cens"]]
                if a and b:
                    xs.append(np.median(a)); ys.append(np.median(b)); cs.append(fracs.index(k[0]))
    for i, f in enumerate(fracs):
        sel = [j for j, c in enumerate(cs) if c == i]
        ax[1].scatter(np.array(xs)[sel], np.array(ys)[sel], s=10, color=f"C{i}", label=f"f={f}")
    lim = [min(xs + ys) * .8, max(xs + ys) * 1.25]
    ax[1].plot(lim, lim, "k:", lw=.8); ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_xlabel(r"$t_{train}$ real labels (median)"); ax[1].set_ylabel(r"$t_{fit}$ random labels (median)")
    ax[1].legend(); ax[1].set_title("(b) memorisation time, real vs random")
    S["probe_n_pairs"] = len(xs)
    S["probe_spearman_real_vs_random"] = spearman_boot(np.log(xs), np.log(ys))
    S["probe_median_ratio_random_over_real"] = float(np.median(np.array(ys) / np.array(xs)))
    # (c) t_train vs width for each fraction (real labels)
    for i, f in enumerate(fracs):
        ks = [k for k in g if k[0] == f and not k[1]]
        ws = [k[2] for k in ks]
        errbar(ax[2], ws, [summarize(g[k], "tt") for k in ks], color=f"C{i}", label=f"f={f}")
        ks2 = [k for k in ks if n_cens(g[k], "train") == 0 and k[2] >= 32]  # fully-fitting widths, w>=32
        S[f"probe_slope_tt_f{f}"] = loglog_slope([k[2] for k in ks2], {k[2]: [r["tt"] for r in g[k]] for k in ks2})
        S[f"probe_slope_tt_f{f}_widths"] = [k[2] for k in ks2]
    ax[2].set_xscale("log"); ax[2].set_yscale("log"); ax[2].set_xlabel("width"); ax[2].set_title(r"(c) $t_{train}$ vs width by train fraction")
    ax[2].legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_probe.pdf")); plt.close()
    # capacity threshold table: smallest width where >=50% of runs fit
    S["capacity_threshold"] = {}
    for f in fracs:
        for rand in (False, True):
            ks = sorted(k for k in g if k[0] == f and k[1] == rand)
            ok = [k[2] for k in ks if np.mean([not r["train_cens"] for r in g[k]]) >= .5]
            wmin = min(ok) if ok else None
            npar = g[(f, rand, wmin)][0]["n_params"] if ok else None
            ntr = int(round(f * 53 * 53))
            S["capacity_threshold"][f"f={f},{'random' if rand else 'real'}"] = dict(
                width=wmin, params=npar, n_train=ntr, params_per_train_example=(npar / ntr if ok else None),
                fit_counts={k[2]: f"{sum(not r['train_cens'] for r in g[k])}/{len(g[k])}" for k in ks})
    # delay vs width per fraction (real labels)
    fig, ax = plt.subplots(1, 3, figsize=(8.5, 2.5))
    for i, f in enumerate(fracs):
        ks = [k for k in g if k[0] == f and not k[1]]
        ws = [k[2] for k in ks]
        errbar(ax[0], ws, [summarize(g[k], "tv") for k in ks], color=f"C{i}", label=f"f={f}")
        errbar(ax[1], ws, [summarize(g[k], "R") for k in ks], color=f"C{i}")
        errbar(ax[2], ws, [summarize(g[k], "D") for k in ks], color=f"C{i}")
        S[f"probe_cens_f{f}"] = {k[2]: f"{n_cens(g[k])}/{len(g[k])}" for k in ks}
    for a, t in zip(ax, (r"$t_{val}$", r"$R=t_{val}/t_{train}$", r"$D=t_{val}-t_{train}$")):
        a.set_yscale("log"); wticks(a, XT[0]); a.set_xlabel("width"); a.set_title(t)
    ax[0].legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_frac.pdf")); plt.close()


# ============================================================ E4 time scale
def e4():
    rows = load("e4_timescale")
    g = group(rows, lambda r: (r["cfg"]["lr"], r["cfg"]["wd"]))
    fig, ax = plt.subplots(1, 3, figsize=(9, 2.5))
    mk = {5e-4: "v", 1e-3: "o", 2e-3: "^"}
    seen_lr = set()
    for (lr, wd), rs in g.items():
        m = summarize(rs, "tv")
        ax[0].errorbar(lr * wd, m[0], yerr=[[m[0] - m[1]], [m[2] - m[0]]], fmt=mk[lr], ms=4, capsize=2, color={0.3: "C0", 0.5: "C1", 1.0: "C2", 2.0: "C3", 3.0: "C4"}[wd],
                       mfc="white" if m[3] else None, label=f"lr={lr:g}" if lr not in seen_lr else None)
        seen_lr.add(lr)
        ax[0].annotate(f"wd={wd:g}", (lr * wd, m[0]), fontsize=5, xytext=(3, -8), textcoords="offset points")
    pr = [3e-4, 5e-4, 1e-3, 2e-3, 3e-3]
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel(r"lr$\cdot$wd"); ax[0].set_ylabel(r"$t_{val}$")
    ax[0].set_xticks(pr); ax[0].set_xticklabels([f"{p:g}" for p in pr], fontsize=6); ax[0].minorticks_off()
    ax[0].legend(); ax[0].set_title(r"(a) $w{=}128$: $t_{val}$ vs lr$\cdot$wd (hollow: censored)")
    ax[1].set_title(r"(b) $w{=}128$: $t_{train}$ vs lr")
    gl = group(rows, lambda r: r["cfg"]["lr"])
    errbar(ax[1], list(gl), [summarize(rs, "tt") for rs in gl.values()])
    ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].set_xlabel("lr")
    ax[1].set_xticks([5e-4, 1e-3, 2e-3]); ax[1].set_xticklabels(["5e-4", "1e-3", "2e-3"]); ax[1].minorticks_off()
    if exists("e11_saturation"):
        b384 = [r["tv"] for r in load("e1_mlp_width") if r["cfg"]["width"] == 384]
        e11 = group(load("e11_saturation"), lambda r: (r["cfg"]["lr"], r["cfg"]["wd"]))
        labs = ["lr 1e-3\nwd 1\n(base)", "lr 2e-3\nwd 1", "lr 1e-3\nwd 3"]
        sets = [b384] + [[r["tv"] for r in e11[k]] for k in ((2e-3, 1.0), (1e-3, 3.0))]
        for j, v in enumerate(sets):
            ax[2].scatter([j] * len(v), v, s=10, color=f"C{j}")
            ax[2].hlines(np.median(v), j - .25, j + .25, color="k", lw=1)
        ax[2].set_xticks(range(3)); ax[2].set_xticklabels(labs, fontsize=6); ax[2].set_ylabel(r"$t_{val}$")
        ax[2].set_title(r"(c) $w{=}384$ (post hoc): $t_{val}$, bar = median")
        ax[2].set_ylim(0, None)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_e4.pdf")); plt.close()
    # slope of log t_val vs log(lr*wd): pooled run-level regression with bootstrap over runs
    cens = sum(r["val_cens"] for r in rows)
    S["e4_cens"] = f"{cens}/{len(rows)}"
    x = np.log([r["cfg"]["lr"] * r["cfg"]["wd"] for r in rows]); y = np.log([r["tv"] for r in rows])
    pt = np.polyfit(x, y, 1)[0]
    bs = []
    for _ in range(2000):
        i = rng2.integers(0, len(x), len(x)); bs.append(np.polyfit(x[i], y[i], 1)[0])
    S["e4_slope_tv_vs_lrwd"] = (float(pt), float(np.quantile(bs, .025)), float(np.quantile(bs, .975)))
    X = np.column_stack([np.ones(len(x)), np.log([r["cfg"]["lr"] for r in rows]), np.log([r["cfg"]["wd"] for r in rows])])
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    bs = []
    for _ in range(2000):
        i = rng2.integers(0, len(x), len(x)); bs.append(np.linalg.lstsq(X[i], y[i], rcond=None)[0])
    bs = np.array(bs)
    S["e4_exponents_lr_wd_all_runs_cens_as_bound"] = dict(
        lr=(float(coef[1]), float(np.quantile(bs[:, 1], .025)), float(np.quantile(bs[:, 1], .975))),
        wd=(float(coef[2]), float(np.quantile(bs[:, 2], .025)), float(np.quantile(bs[:, 2], .975))))
    un = [k for k, r in enumerate(rows) if not r["val_cens"]]
    coef2 = np.linalg.lstsq(X[un], y[un], rcond=None)[0]
    S["e4_exponents_lr_wd_uncensored_runs_only"] = dict(lr=float(coef2[1]), wd=float(coef2[2]), n=len(un))
    S["e4_tt_exponent_lr"] = float(np.polyfit(np.log([r["cfg"]["lr"] for r in rows]), np.log([r["tt"] for r in rows]), 1)[0])
    S["e4_table"] = {f"lr={lr:g},wd={wd:g}": dict(prod=lr * wd, tv=summarize(rs, "tv"), tt=summarize(rs, "tt"), cens=n_cens(rs), n=len(rs))
                     for (lr, wd), rs in g.items()}
    # equal-product pairs
    eq = [rs for (lr, wd), rs in g.items() if abs(lr * wd - 1e-3) < 1e-9]
    if len(eq) >= 2:
        meds_eq = [np.median([r["tv"] for r in rs]) for rs in eq]
        S["e4_equal_product_ratio_max_over_min"] = float(max(meds_eq) / min(meds_eq))


# ============================================================ E6 generality
def e6():
    XT[0] = [64, 128, 256]
    rows = load("e6_generality") + load("e1_mlp_width")
    def cond(r):
        c = r["cfg"]
        return (c["op"], c["p"])
    rows = [r for r in rows if r["cfg"]["width"] in (64, 128, 256) and r["cfg"]["train_frac"] == 0.3
            and r["cfg"]["lr"] == 1e-3 and r["cfg"]["wd"] == 1.0]
    g = group(rows, lambda r: (cond(r), r["cfg"]["width"]))
    conds = sorted({k[0] for k in g})
    fig, ax = plt.subplots(1, 3, figsize=(8.5, 2.5))
    S["e6"] = {}
    for i, cd in enumerate(conds):
        ks = [k for k in g if k[0] == cd]; ws = [k[1] for k in ks]
        lab = f"{cd[0]}, p={cd[1]}"
        errbar(ax[0], ws, [summarize(g[k], "tt") for k in ks], color=f"C{i}", label=lab)
        errbar(ax[1], ws, [summarize(g[k], "tv") for k in ks], color=f"C{i}")
        errbar(ax[2], ws, [summarize(g[k], "R") for k in ks], color=f"C{i}")
        S["e6"][lab] = {str(k[1]): dict(tt=summarize(g[k], "tt"), tv=summarize(g[k], "tv"), R=summarize(g[k], "R"),
                                        D=summarize(g[k], "D"), cens=n_cens(g[k]), n=len(g[k])) for k in ks}
    for a, t in zip(ax, (r"$t_{train}$", r"$t_{val}$", r"$R$")):
        a.set_yscale("log"); wticks(a, XT[0]); a.set_xlabel("width"); a.set_title(t)
    ax[0].legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_e6.pdf")); plt.close()
    L = [r"\begin{tabular}{llrcccc}", r"\toprule", r"task & $p$ & width & $t_{train}$ & $t_{val}$ & $R=t_{val}/t_{train}$ & cens./$n$ \\", r"\midrule"]
    for lab, d in S["e6"].items():
        op, p = lab.split(", p=")
        for w, v in d.items():
            pre = r"$\geq$" if v["cens"] * 2 >= v["n"] else ""
            L.append(f"{op} & {p} & {w} & {v['tt'][0]:.0f} & {pre}{v['tv'][0]:.0f} [{v['tv'][1]:.0f},{v['tv'][2]:.0f}] & {pre}{v['R'][0]:.0f} & {v['cens']}/{v['n']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "tab_e6.tex"), "w").write("\n".join(L))


# ============================================================ E7 parameterisation
def e7():
    XT[0] = [64, 128, 256, 512]
    rows = load("e7_param")
    base = [r for r in load("e1_mlp_width") if r["cfg"]["width"] in (64, 128, 256, 512)]
    for r in base:
        r["cfg"]["tag"] = "SP"
    rows += base
    g = group(rows, lambda r: (r["cfg"]["tag"], r["cfg"]["width"]))
    fig, ax = plt.subplots(1, 3, figsize=(8.5, 2.5))
    names = {"SP": "fixed lr, wd", "a": r"lr$\propto1/w$, lr$\cdot$wd fixed", "b": r"lr$\propto1/w$, wd fixed"}
    S["e7"] = {}
    for i, tag in enumerate(("SP", "a", "b")):
        ks = [k for k in g if k[0] == tag]; ws = [k[1] for k in ks]
        errbar(ax[0], ws, [summarize(g[k], "tt") for k in ks], color=f"C{i}", label=names[tag])
        errbar(ax[1], ws, [summarize(g[k], "tv") for k in ks], color=f"C{i}")
        errbar(ax[2], ws, [summarize(g[k], "R") for k in ks], color=f"C{i}")
        S["e7"][tag] = {str(k[1]): dict(tt=summarize(g[k], "tt"), tv=summarize(g[k], "tv"), R=summarize(g[k], "R"),
                                        cens=n_cens(g[k]), n=len(g[k])) for k in ks}
        ks2 = [k for k in ks if k[1] >= 128]  # uncensored widths only (w=64 is censored at 100k in all variants)
        if len(ks2) > 2:
            S["e7"][tag]["slope_tt_w128+"] = loglog_slope([k[1] for k in ks2], {k[1]: [r["tt"] for r in g[k]] for k in ks2})
            S["e7"][tag]["slope_tv_w128+"] = loglog_slope([k[1] for k in ks2], {k[1]: [r["tv"] for r in g[k]] for k in ks2})
            S["e7"][tag]["slope_R_w128+"] = loglog_slope([k[1] for k in ks2], {k[1]: [r["tv"] / r["tt"] for r in g[k]] for k in ks2})
    for a, t in zip(ax, (r"$t_{train}$", r"$t_{val}$", r"$R$")):
        a.set_yscale("log"); wticks(a, XT[0]); a.set_xlabel("width"); a.set_title(t)
    ax[0].legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_e7.pdf")); plt.close()
    L = [r"\begin{tabular}{llrcccc}", r"\toprule", r"setting & width & lr & $t_{train}$ & $t_{val}$ & $R$ & cens./$n$ \\", r"\midrule"]
    for tag in ("SP", "a", "b"):
        for w, v in S["e7"][tag].items():
            if not isinstance(v, dict):
                continue
            lr = 1e-3 * (128 / int(w)) if tag != "SP" else 1e-3
            pre = r"$\geq$" if v["cens"] * 2 >= v["n"] else ""
            L.append(f"{names[tag]} & {w} & {lr:.2g} & {v['tt'][0]:.0f} & {pre}{v['tv'][0]:.0f} [{v['tv'][1]:.0f},{v['tv'][2]:.0f}] & {pre}{v['R'][0]:.0f} & {v['cens']}/{v['n']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "tab_e7.tex"), "w").write("\n".join(L))


# ============================================================ E5 transformer
def e5():
    rows = load("e5_tf") if exists("e5_tf") else []
    if exists("e5b_tf_small"):
        have = {r["key"] for r in rows}
        rows += [r for r in load("e5b_tf_small") if r["key"] not in have]
    S["e5_w128_at_40k_budget"] = [dict(t_train=r["t_train"], t_val=r["t_val"], final_val_acc=r["final"][3]) for r in rows if r["cfg"]["width"] == 128]
    if exists("e12_tf128_long"):
        rows = [r for r in rows if r["cfg"]["width"] != 128] + load("e12_tf128_long")
    g = group(rows, lambda r: r["cfg"]["width"]); ws = list(g)
    fig, ax = plt.subplots(1, 3, figsize=(8.5, 2.5))
    errbar(ax[0], ws, [summarize(g[w], "tt") for w in ws]); errbar(ax[0], ws, [summarize(g[w], "tv") for w in ws])
    errbar(ax[1], ws, [summarize(g[w], "R") for w in ws], color="C2")
    errbar(ax[2], ws, [summarize(g[w], "D") for w in ws], color="C3")
    for a, t in zip(ax, (r"$t_{train}$ (blue), $t_{val}$ (orange)", r"$R$", r"$D$")):
        a.set_yscale("log"); wticks(a, ws); a.set_xlabel("d_model"); a.set_title(t)
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_e5.pdf")); plt.close()
    S["e5"] = {str(w): dict(params=g[w][0]["n_params"], tt=summarize(g[w], "tt"), tv=summarize(g[w], "tv"),
                            R=summarize(g[w], "R"), D=summarize(g[w], "D"), cens=n_cens(g[w]), n=len(g[w]),
                            tt_cens=n_cens(g[w], "train")) for w in ws}
    S["e5_slope_tt"] = loglog_slope(ws, {w: [r["tt"] for r in g[w]] for w in ws}) if len(ws) > 2 else None
    S["e5_values"] = {str(w): dict(t_train=[r["t_train"] for r in g[w]], t_val=[r["t_val"] for r in g[w]],
                                   budget=g[w][0]["cfg"]["max_steps"]) for w in ws}
    def first_cross(r, thr):
        cv = np.array(r["curve"]); idx = np.where(cv[:, 3] >= thr)[0]
        return int(cv[idx[0], 0]) if len(idx) else None
    for w in ws:
        for r in g[w]:
            r["t_val95"] = first_cross(r, 0.95)
    S["e5_tv95"] = {str(w): [r["t_val95"] for r in sorted(g[w], key=lambda r: r["cfg"]["seed"])] for w in ws}
    S["e5_max_val_acc"] = {str(w): [round(float(np.max(np.array(r["curve"])[:, 3])), 3) for r in sorted(g[w], key=lambda r: r["cfg"]["seed"])] for w in ws}
    L = [r"\begin{tabular}{rrrcccc}", r"\toprule", r"$d_{model}$ & params & budget & $t_{train}$ & $t_{val}$, 99\% (per seed) & $t_{val}$, 95\% (per seed) & max val.\ acc.\ \\", r"\midrule"]
    fmt = lambda v: f"{v/1000:.1f}k" if v is not None else "$-$"
    for w in ws:
        gs = sorted(g[w], key=lambda r: r["cfg"]["seed"])
        L.append(f"{w} & {g[w][0]['n_params']/1e3:.0f}k & {g[w][0]['cfg']['max_steps']//1000}k & {np.median([r['tt'] for r in g[w]]):.0f} & {', '.join(fmt(r['t_val']) for r in gs)} & {', '.join(fmt(r['t_val95']) for r in gs)} & {', '.join(f'{x:.2f}' for x in S['e5_max_val_acc'][str(w)])} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "tab_e5.tex"), "w").write("\n".join(L))



# ============================================================ generalisation threshold vs width and data fraction
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def thresh():
    BUD = 60000
    rows = []
    for n in ("e1_mlp_width", "e3_frac", "e8_small", "e10_threshold"):
        if exists(n):
            rows += [r for r in load(n) if not r["cfg"]["shuffle_labels"]]
    g = group(rows, lambda r: (r["cfg"]["train_frac"], r["cfg"]["width"]))
    fracs = sorted({k[0] for k in g})
    fig, ax = plt.subplots(1, 3, figsize=(10, 2.6))
    S["thresh"] = {}
    for i, f in enumerate(fracs):
        ks = [k for k in g if k[0] == f]
        ws = [k[1] for k in ks]
        gen = [sum((r["t_val"] is not None and r["t_val"] <= BUD) for r in g[k]) for k in ks]
        fit = [sum((r["t_train"] is not None and r["t_train"] <= BUD) for r in g[k]) for k in ks]
        n = [len(g[k]) for k in ks]
        for a, v, lab in ((ax[0], fit, "fits train"), (ax[1], gen, "generalises")):
            p = np.array(v) / np.array(n)
            ci = np.array([wilson(x, m) for x, m in zip(v, n)])
            a.errorbar(ws, p, yerr=[np.clip(p - ci[:, 0], 0, None), np.clip(ci[:, 1] - p, 0, None)], marker="o", ms=3, lw=1, capsize=2, color=f"C{i}", label=f"f={f}")
        S["thresh"][f"f={f}"] = {str(w): f"gen {a}/{m}, fit {b}/{m}" for w, a, b, m in zip(ws, gen, fit, n)}
        ok = [w for w, a, m in zip(ws, gen, n) if a / m >= 0.5]
        S["thresh"][f"f={f}_w50"] = min(ok) if ok else None
        okf = [w for w, a, m in zip(ws, fit, n) if a / m >= 0.5]
        S["thresh"][f"f={f}_fit_w50"] = min(okf) if okf else None
    S["direct_generalisation"] = [dict(frac=r["cfg"]["train_frac"], width=r["cfg"]["width"], seed=r["cfg"]["seed"],
                                       t_train=r["t_train"], t_val=r["t_val"], R=r["t_val"] / r["t_train"])
                                  for r in rows if r["t_val"] is not None and r["t_train"] is not None
                                  and r["t_val"] / r["t_train"] <= 5]
    S["n_generalised_total"] = sum(r["t_val"] is not None for r in rows)
    if exists("e9_long"):
        for w, c in ((48, "C0"), (64, "C1")):
            for j, r in enumerate([r for r in load("e9_long") if r["cfg"]["width"] == w]):
                cv = np.array(r["curve"])
                ax[2].plot(cv[:, 0] + 1, cv[:, 3], color=c, lw=.9, label=f"w={w}" if j == 0 else None)
        ax[2].set_xscale("log"); ax[2].set_xlabel("step"); ax[2].set_ylabel("validation accuracy"); ax[2].legend()
        ax[2].set_title(r"(c) stuck MLPs, $f{=}0.3$, $4\times10^5$-step budget")
    for a, t in zip(ax[:2], (f"(a) reaches 99% train acc. within {BUD//1000}k steps", f"(b) reaches 99% val acc. within {BUD//1000}k steps")):
        a.set_xscale("log"); a.set_xlabel("width"); a.set_title(t); a.set_ylabel("fraction of runs (Wilson 95% CI)")
        a.set_xticks([8, 16, 32, 64, 128, 256, 512]); a.set_xticklabels(["8", "16", "32", "64", "128", "256", "512"]); a.minorticks_off()
    ax[1].legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_thresh.pdf")); plt.close()


# ============================================================ E9 (long budget), local slopes, E11 (saturation)
def ratio_ci(a, b, n=4000):
    """median(a)/median(b) with bootstrap 95% CI (resample both groups)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    rs = [np.median(rng2.choice(a, len(a))) / np.median(rng2.choice(b, len(b))) for _ in range(n)]
    return float(np.median(a) / np.median(b)), float(np.quantile(rs, .025)), float(np.quantile(rs, .975))


def extras():
    base = group(load("e1_mlp_width"), lambda r: r["cfg"]["width"])
    med = {w: np.median([r["tv"] for r in rs]) for w, rs in base.items() if n_cens(rs) * 2 < len(rs)}
    ws = sorted(med)
    S["local_slopes_tv"] = {f"{a}->{b}": float(np.log(med[b] / med[a]) / np.log(b / a)) for a, b in zip(ws[:-1], ws[1:])}
    S["local_slopes_tt"] = {f"{a}->{b}": float(np.log(np.median([r['tt'] for r in base[b]]) / np.median([r['tt'] for r in base[a]])) / np.log(b / a))
                            for a, b in zip(ws[:-1], ws[1:])}
    if exists("e9_long"):
        g = group(load("e9_long"), lambda r: r["cfg"]["width"])
        S["e9"] = {str(w): dict(t_val=[r["t_val"] for r in rs], t_train=[r["t_train"] for r in rs],
                                final_val_acc=[round(r["final"][3], 3) for r in rs]) for w, rs in g.items()}
        fig, ax = plt.subplots(1, 1, figsize=(3.4, 2.5))
        for w, c in ((48, "C0"), (64, "C1")):
            for r in g.get(w, []):
                cv = np.array(r["curve"])
                ax.plot(cv[:, 0] + 1, cv[:, 3], color=c, lw=.9, label=f"w={w}" if r is g[w][0] else None)
        ax.set_xscale("log"); ax.set_xlabel("step"); ax.set_ylabel("validation accuracy"); ax.legend()
        plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_e9.pdf")); plt.close()
    if exists("e11_saturation"):
        b384 = [r["tv"] for r in base[384]]
        rows = load("e11_saturation")
        g = group(rows, lambda r: (r["cfg"]["lr"], r["cfg"]["wd"]))
        S["e11"] = {"baseline_lr1e-3_wd1": dict(tv=b384)}
        for k, rs in g.items():
            S["e11"][f"lr={k[0]:g},wd={k[1]:g}"] = dict(tv=[r["tv"] for r in rs], cens=n_cens(rs),
                                                      tt=[r["tt"] for r in rs],
                                                      ratio_baseline_over_this=ratio_ci(b384, [r["tv"] for r in rs]))


if __name__ == "__main__":
    which = sys.argv[1:] or ["e1", "probe", "thresh", "e4", "e6", "e7", "e5", "extras"]
    need = dict(extras="e1_mlp_width", thresh="e1_mlp_width", e1="e1_mlp_width", probe="e2_random", e4="e4_timescale", e6="e6_generality", e7="e7_param", e5="e5_tf")
    for k in which:
        if exists(need[k]):
            print("running", k, flush=True)
            globals()[k]()
    json.dump(S, open(os.path.join(RES, "summary.json"), "w"), indent=1, default=float)
    print(json.dumps(S, indent=1, default=float)[:6000])
