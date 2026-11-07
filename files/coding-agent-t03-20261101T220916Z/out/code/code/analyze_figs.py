"""Figures and tables for the paper from results/summary (+ bg / retrain / bgpair / shaplib / highd).
Outputs: /work/paper/figs/*.pdf, /work/paper/gen/*.tex, /work/paper/gen/numbers.json"""
import os, json, pickle, glob, itertools
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
from metrics import pair_metrics

S = "/work/results/summary"; FIG = "/work/paper/figs"; GEN = "/work/paper/gen"
os.makedirs("/tmp/tmp_png", exist_ok=True); os.makedirs(FIG, exist_ok=True); os.makedirs(GEN, exist_ok=True)
rng = np.random.default_rng(2026)
DSN = {"pima": "Pima (d=8)", "gmsc": "GMSC (d=10)", "acsincome": "ACSIncome (d=10)",
       "acsemployment": "ACSEmployment (d=16)", "german": "German (d=20)"}
DSO = ["pima", "gmsc", "acsincome", "acsemployment", "german"]
KIND = ["lr", "mlp", "rf", "xgb"]
KN = {"lr": "LR", "mlp": "MLP", "rf": "RF", "xgb": "XGB"}
COL = {"pima": "#0072B2", "gmsc": "#E69F00", "acsincome": "#009E73", "acsemployment": "#CC79A7", "german": "#D55E00"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
                     "lines.linewidth": 1.4, "pdf.fonttype": 42, "axes.grid": True, "grid.alpha": 0.25,
                     "grid.linewidth": 0.5, "legend.frameon": False})
NUM = {}
MMIN = 64  # below this the Shapley regression is under-determined for d>=16 (see text)

inst = pd.read_parquet(f"{S}/inst_level.parquet")
inst = inst[inst.m >= MMIN].copy()
inst["rel90"] = (inst.t_topk >= 0.9).astype(float)
inst["top1_90"] = (inst.t_top1 >= 0.9).astype(float)
inst["maxm"] = (2 ** inst.d - 2)


def boot_pooled(cells, B=1000):
    """cells: list of 1-D arrays (instance-level values, one per ds x model cell). Equal weight per cell.
    Returns mean and 95% percentile CI from resampling instances within cells."""
    cells = [np.asarray(c, float) for c in cells if len(c)]
    mean = np.mean([c.mean() for c in cells])
    bs = np.zeros(B)
    for c in cells:
        idx = rng.integers(0, len(c), (B, len(c)))
        bs += c[idx].mean(1)
    bs /= len(cells)
    return mean, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def curve(df, ds, metric, est="kernel", kinds=KIND):
    out = []
    for m in sorted(df[df.ds == ds].m.unique()):
        cells = [df[(df.ds == ds) & (df.kind == k) & (df.est == est) & (df.m == m)][metric].values for k in kinds]
        if all(len(c) for c in cells):
            out.append((m,) + boot_pooled(cells))
    d = df[df.ds == ds].d.iloc[0]
    out.append((2 ** d - 2, 1.0, 1.0, 1.0))  # complete enumeration is exact
    return np.array(out)


# ------------------------------------------------------------------ Fig 1: reliability vs budget
def fig1():
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.3), sharex=True)
    for ax, (metric, ttl) in zip(axs, [("t_top1", "top-1 feature correct"), ("t_topk", "top-3 set exactly correct"),
                                       ("rel90", "instances with P(top-3 ok)$\\geq$0.9")]):
        for ds in DSO:
            c = curve(inst, ds, metric)
            ax.plot(c[:, 0], c[:, 1], color=COL[ds], marker="o", ms=3, label=DSN[ds])
            ax.fill_between(c[:, 0], c[:, 2], c[:, 3], color=COL[ds], alpha=0.18, lw=0)
        ax.set_xscale("log", base=2); ax.set_title(ttl, fontsize=8); ax.set_xlabel("budget $m$ (coalition evaluations)")
        ax.set_ylim(0.5 if metric != "t_top1" else 0.85, 1.005)
    axs[0].set_ylabel("single-run probability / fraction")
    axs[0].legend(fontsize=6, loc="lower right")
    fig.tight_layout(); fig.savefig(f"{FIG}/fig_reliability_budget.pdf"); fig.savefig("/tmp/tmp_png/f1.png", dpi=110); plt.close(fig)


# ------------------------------------------------------------------ Table: per dataset x model at fixed budgets
def table_reliability():
    rows = []
    for ds in DSO:
        for k in KIND:
            r = {"ds": ds, "kind": k}
            for m in (256, 2048):
                s = inst[(inst.ds == ds) & (inst.kind == k) & (inst.est == "kernel") & (inst.m == m)]
                if len(s) == 0:
                    r[f"top3_{m}"] = None; continue
                r[f"top3_{m}"] = boot_pooled([s.t_topk.values]); r[f"rel90_{m}"] = boot_pooled([s.rel90.values])
                r[f"top1_{m}"] = boot_pooled([s.t_top1.values]); r[f"relL2_{m}"] = float(s.t_rel.median())
            rows.append(r)
    return rows


def fmt(t, pct=True):
    if t is None:
        return "--"
    m, lo, hi = t
    return f"{100*m:.1f} [{100*lo:.1f}, {100*hi:.1f}]" if pct else f"{m:.3f}"


def write_table_reliability(rows):
    L = ["\\begin{tabular}{llcccccc}", "\\toprule",
         " & & \\multicolumn{3}{c}{$m=256$} & \\multicolumn{3}{c}{$m=2048$}\\\\",
         "\\cmidrule(lr){3-5}\\cmidrule(lr){6-8}",
         "Dataset & Model & top-1 & top-3 set & \\% inst.\\ $\\ge$0.9 & top-1 & top-3 set & \\% inst.\\ $\\ge$0.9\\\\", "\\midrule"]
    for r in rows:
        def c(key):
            t = r.get(key)
            return "enum." if t is None and False else (f"{100*t[0]:.1f}" if t is not None else "enum.")
        L.append(f"{DSN[r['ds']]} & {KN[r['kind']]} & {c('top1_256')} & {c('top3_256')} & {c('rel90_256')} & {c('top1_2048')} & {c('top3_2048')} & {c('rel90_2048')}\\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(f"{GEN}/tab_reliability.tex", "w").write("\n".join(L))
    # also machine-readable
    NUM["table_reliability"] = rows


# ------------------------------------------------------------------ Fig 2: mechanism
def fig2():
    k = inst[(inst.est == "kernel")].copy()
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
    ax = axs[0]
    bins = [0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 6, 1e9]
    k["zb"] = pd.cut(k.oz3, bins)
    from scipy.stats import norm
    zz = np.linspace(0, 5, 100)
    for d, mk in [(8, "s"), (10, "o"), (16, "^"), (20, "D")]:
        s = k[k.d == d]
        g = s.groupby("zb", observed=True).agg(z=("oz3", "median"), p=("t_topk", "mean"), n=("t_topk", "size"))
        g = g[g.n >= 20]
        ax.plot(g.z.clip(upper=5), g.p, marker=mk, ms=3.5, lw=0.8, label=f"d={d}")
    ax.plot(zz, norm.cdf(zz / np.sqrt(2) * 1.0) * 0 + norm.cdf(zz), color="k", lw=0.8, ls="--", label=r"$\Phi(z)$")
    ax.set_xlabel("oracle gap-to-noise $z=(a_{(3)}-a_{(4)})/\\sqrt{\\sigma_{(3)}^2+\\sigma_{(4)}^2}$")
    ax.set_ylabel("P(top-3 set correct)"); ax.legend(fontsize=6); ax.set_title("(a) one curve for all $d$, models, budgets", fontsize=8)
    ax = axs[1]
    s = k[(k.m == 2048) & (k.d >= 16)].copy()
    s["gb"] = pd.cut(s.gap3, [0, 0.01, 0.02, 0.04, 0.08, 0.16, 1])
    for kind in KIND:
        g = s[s.kind == kind].groupby("gb", observed=True).t_topk.mean()
        ax.plot(range(len(g)), g.values, marker="o", ms=3, label=KN[kind])
    ax.set_xticks(range(6)); ax.set_xticklabels(["<.01", ".01-.02", ".02-.04", ".04-.08", ".08-.16", ">.16"], fontsize=6)
    ax.set_xlabel("exact gap $(a_{(3)}-a_{(4)})/\\|\\phi\\|_2$"); ax.set_ylabel("P(top-3 set correct), $m=2048$")
    ax.set_title("(b) failures sit at near-ties ($d\\geq16$)", fontsize=8); ax.legend(fontsize=6)
    fig.tight_layout(); fig.savefig(f"{FIG}/fig_mechanism.pdf"); fig.savefig("/tmp/tmp_png/f2.png", dpi=110); plt.close(fig)
    # numbers
    s = k[(k.m == 2048) & (k.d >= 16)]
    NUM["frac_gap3_lt_0.02"] = float((s.drop_duplicates(["ds", "kind", "inst"]).gap3 < 0.02).mean())
    NUM["fail_share_gap_lt_0.04"] = float(((1 - s.t_topk) * (s.gap3 < 0.04)).sum() / (1 - s.t_topk).sum())
    NUM["collapse_table"] = k.groupby("zb", observed=True).t_topk.agg(["mean", "size"]).reset_index().astype(str).values.tolist()


# ------------------------------------------------------------------ certificate
def cert():
    rl = pd.read_parquet(f"{S}/run_level.parquet")
    rl = rl[(rl.est == "kernel") & (rl.m >= MMIN) & rl.ds.isin(["acsemployment", "german"])].copy()
    rl["z3"] = rl.z3.replace([np.inf], 1e6).fillna(0).clip(upper=1e6)
    two = pd.read_parquet(f"{S}/tworun.parquet")
    two = two[(two.m // 2 >= MMIN) & two.ds.isin(["acsemployment", "german"])]
    # drop budgets where the instance is fully enumerated (z=inf) from certificate statistics? keep, report separately
    rows = []
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
    for m, c in [(128, "#0072B2"), (512, "#009E73"), (2048, "#D55E00")]:
        s = rl[rl.m == m]
        cs = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 6])
        cov = [(s.z3 >= c0).mean() for c0 in cs]
        err = [1 - s.ok3[s.z3 >= c0].mean() for c0 in cs]
        axs[0].plot(cov, np.maximum(err, 1e-5), marker="o", ms=3, color=c, label=f"single run, $m={m}$")
        t = two[two.m == m]
        axs[0].scatter([t.agree.mean()], [1 - t.ok3_pooled[t.agree == 1].mean()], marker="*", s=60, color=c, edgecolor="k", lw=0.5, zorder=5)
        auc = roc_auc_score(s.ok3, np.minimum(s.z3, 50))
        for c0, cv, er in zip(cs, cov, err):
            rows.append(dict(m=m, c=c0, coverage=cv, err_certified=er))
        rows.append(dict(m=m, c="2run", coverage=t.agree.mean(), err_certified=1 - t.ok3_pooled[t.agree == 1].mean(),
                         base_err=1 - s.ok3.mean(), auc=auc))
    axs[0].set_yscale("log"); axs[0].set_xlabel("fraction of runs certified (coverage)")
    axs[0].set_ylabel("P(top-3 set wrong | certified)"); axs[0].legend(fontsize=6, loc="lower left")
    axs[0].set_title("(a) $z\\geq c$ certificate (lines) vs. cost-matched 2-run check ($\\star$)", fontsize=7)
    # (b) calibration of SE: SE / empirical SD
    ax = axs[1]
    for est, c in [("kernel", "#0072B2"), ("leverage", "#009E73"), ("perm", "#D55E00")]:
        s = inst[(inst.est == est)].groupby(["d", "m"]).se_over_sd.median().reset_index()
        for d, ls in [(10, "-"), (20, "--")]:
            q = s[s.d == d]
            ax.plot(q.m, q.se_over_sd, ls=ls, color=c, marker="o", ms=2.5, label=f"{est}, d={d}" if d == 20 or True else None)
    ax.axhline(1, color="k", lw=0.6); ax.set_xscale("log", base=2); ax.set_ylim(0.4, 1.3)
    ax.set_xlabel("budget $m$"); ax.set_ylabel("median SE / empirical SD")
    ax.set_title("(b) within-run SE tracks true run-to-run SD", fontsize=7); ax.legend(fontsize=5.5, ncol=2)
    fig.tight_layout(); fig.savefig(f"{FIG}/fig_certificate.pdf"); fig.savefig("/tmp/tmp_png/f3.png", dpi=110); plt.close(fig)
    NUM["cert_rows"] = rows

    # cluster-bootstrap CIs (clusters = explained instance x model pair) + matched-coverage comparison
    def cboot(num, den, B=2000):
        num, den = np.asarray(num, float), np.asarray(den, float); n = len(num)
        idx = rng.integers(0, n, (B, n)); r = num[idx].sum(1) / np.maximum(den[idx].sum(1), 1)
        return num.sum() / den.sum(), np.percentile(r, 2.5), np.percentile(r, 97.5)
    NUM["cert_ci"] = {}
    for m in (128, 512, 2048):
        s = rl[rl.m == m]; t = two[two.m == m]
        g = s.assign(cert2=(s.z3 >= 2), wrong2=((s.z3 >= 2) & (s.ok3 == 0))).groupby(["ds", "kind", "inst"]).agg(w=("wrong2", "sum"), c=("cert2", "sum"), n=("cert2", "size"))
        e_z2 = cboot(g.w, g.c); cov_z2 = cboot(g.c, g.n)
        h = t.assign(w=((t.agree == 1) & (t.ok3_pooled == 0))).groupby(["ds", "kind", "inst"]).agg(w=("w", "sum"), c=("agree", "sum"), n=("agree", "size"))
        e_2r = cboot(h.w, h.c); cov_2r = cboot(h.c, h.n)
        thr = np.quantile(s.z3.values, 1 - cov_2r[0])
        g2 = s.assign(cert2=(s.z3 >= thr), wrong2=((s.z3 >= thr) & (s.ok3 == 0))).groupby(["ds", "kind", "inst"]).agg(w=("wrong2", "sum"), c=("cert2", "sum"), n=("cert2", "size"))
        e_zm = cboot(g2.w, g2.c)
        NUM["cert_ci"][m] = dict(err_z2=e_z2, cov_z2=cov_z2, err_2run=e_2r, cov_2run=cov_2r, err_z_matched=e_zm, thr_matched=float(thr))
    L = ["\\begin{tabular}{rccccc}", "\\toprule", "$m$ & all runs: err.\\ (\\%) & AUROC($z_3$) & $z_3\\ge2$: cov.\\ / err.\\ (\\%) & 2-run agree: cov.\\ / err.\\ (\\%) & $z_3$ at 2-run coverage: err.\\ (\\%)\\\\", "\\midrule"]
    for m in (128, 512, 2048):
        r2 = [r for r in rows if r["m"] == m and r["c"] == "2run"][0]; c = NUM["cert_ci"][m]
        f = lambda t: f"{100*t[0]:.2f} [{100*t[1]:.2f}, {100*t[2]:.2f}]"
        L.append(f"{m} & {100*r2['base_err']:.2f} & {r2['auc']:.3f} & {c['cov_z2'][0]:.2f} / {f(c['err_z2'])} & {c['cov_2run'][0]:.2f} / {f(c['err_2run'])} & {f(c['err_z_matched'])}\\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(f"{GEN}/tab_cert.tex", "w").write("\n".join(L))


# ------------------------------------------------------------------ estimator comparison
def est_table():
    p = inst[inst.d >= 16].pivot_table(index=["ds", "kind", "inst", "m"], columns="est", values=["t_topk", "t_rel"])
    L = ["\\begin{tabular}{rcccccc}", "\\toprule", "$m$ & \\multicolumn{3}{c}{P(top-3 set correct), \\%} & \\multicolumn{3}{c}{median rel.\\ $\\ell_2$ error, \\%}\\\\",
         "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}", " & Kernel & Leverage & Perm. & Kernel & Leverage & Perm.\\\\", "\\midrule"]
    out = {}
    for m in (64, 128, 256, 512, 2048, 8192):
        q = p.xs(m, level="m").dropna()
        if len(q) == 0:
            continue
        cells = {e: [g["t_topk"][e].values for _, g in q.groupby(level=["ds", "kind"])] for e in ("kernel", "leverage", "perm")}
        a = {e: boot_pooled(cells[e]) for e in cells}
        rel = {e: 100 * q["t_rel"][e].median() for e in cells}
        # paired difference leverage-kernel and perm-kernel
        dl = boot_pooled([(g["t_topk"]["leverage"] - g["t_topk"]["kernel"]).values for _, g in q.groupby(level=["ds", "kind"])])
        dp = boot_pooled([(g["t_topk"]["perm"] - g["t_topk"]["kernel"]).values for _, g in q.groupby(level=["ds", "kind"])])
        out[m] = dict(a=a, rel=rel, d_lev=dl, d_perm=dp, n=len(q))
        L.append(f"{m} & {100*a['kernel'][0]:.1f} & {100*a['leverage'][0]:.1f} & {100*a['perm'][0]:.1f} & {rel['kernel']:.2f} & {rel['leverage']:.2f} & {rel['perm']:.2f}\\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(f"{GEN}/tab_est.tex", "w").write("\n".join(L)); NUM["est"] = {str(k): v for k, v in out.items()}


# ------------------------------------------------------------------ comparison standards (retrain, background)
def standards():
    res = pickle.load(open("/work/results/retrain/retrain.pkl", "rb"))
    bp = pd.DataFrame([dict(ds=r["ds"], kind=r["kind"], inst=r["inst"], b=b, **v) for r in pickle.load(open("/work/results/bgpair/bgpair.pkl", "rb")) for b, v in r["out"].items()])
    rows = []
    for ds in ["pima", "gmsc", "acsincome"]:
        for kind in KIND:
            rs = sorted([r for r in res if r["ds"] == ds and r["kind"] == kind], key=lambda r: r["k"])
            pm = [pair_metrics(rs[a]["Phi"], rs[b]["Phi"], 3) for a, b in itertools.combinations(range(len(rs)), 2)]
            ret = {k: np.mean([p[k] for p in pm], axis=0) for k in pm[0]}  # per-instance means over model pairs
            aucs = [r["auc"] for r in rs]
            row = dict(ds=ds, kind=kind, auc_range=(min(aucs), max(aucs)))
            for k in ("top1", "topk", "rbo", "rel"):
                row[f"retrain_{k}"] = float(ret[k].mean())
            for b in (25, 100):
                q = bp[(bp.ds == ds) & (bp.kind == kind) & (bp.b == b)]
                for k in ("top1", "topk", "rbo", "rel"):
                    row[f"bg{b}_{k}"] = float(q[k].mean())
            for m in (64, 128, 256, 512):
                q = inst[(inst.ds == ds) & (inst.kind == kind) & (inst.est == "kernel") & (inst.m == m)]
                if len(q) == 0:
                    continue
                for k, key in (("top1", "r2r_top1"), ("topk", "r2r_topk"), ("rbo", "r2r_rbo"), ("rel", "r2r_rel")):
                    row[f"est{m}_{k}"] = float(q[key].mean())
            rows.append(row)
    df = pd.DataFrame(rows)
    NUM["standards"] = df.to_dict("records")
    df.to_csv(f"{GEN}/standards.csv", index=False)
    # figure: pairwise top-3 agreement and relative l2 for each source of variation
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
    for ax, key, ttl in [(axs[0], "topk", "two explanations agree on the top-3 set"), (axs[1], "rel", "relative $\\ell_2$ difference")]:
        x = np.arange(len(df)); w = 0.16
        srcs = [("est64", "coalition noise $m$=64", "#9ecae1"), ("est128", "coalition noise $m$=128", "#4292c6"),
                ("bg100", "new 100-row background (exact)", "#E69F00"), ("retrain", "retrained model (exact)", "#D55E00")]
        for i, (pre, lab, c) in enumerate(srcs):
            v = [r.get(f"{pre}_{key}", np.nan) for r in rows]
            ax.bar(x + (i - 1.5) * w, v, w, color=c, label=lab)
        ax.set_xticks(x); ax.set_xticklabels([f"{r['ds'][:4]}\n{KN[r['kind']]}" for r in rows], fontsize=5.5)
        ax.set_title(ttl, fontsize=8)
    axs[0].set_ylim(0, 1.0)
    h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, fontsize=6, loc="lower center", ncol=4)
    fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(f"{FIG}/fig_standards.pdf"); fig.savefig("/tmp/tmp_png/f4.png", dpi=110); plt.close(fig)
    # LaTeX table, dataset-level averages over models
    L = ["\\begin{tabular}{llcccc}", "\\toprule", "Dataset & Source of variation & top-1 agree & top-3 set agree & RBO & rel.\\ $\\ell_2$ diff.\\\\", "\\midrule"]
    for ds in ["pima", "gmsc", "acsincome"]:
        q = df[df.ds == ds]
        for pre, lab in [("est64", "coalition sampling, $m{=}64$"), ("est128", "coalition sampling, $m{=}128$"),
                         ("bg25", "new 25-row background (exact)"), ("bg100", "new 100-row background (exact)"), ("retrain", "retrained model (exact)")]:
            if f"{pre}_topk" not in q or q[f"{pre}_topk"].isna().all():
                continue
            L.append(f"{DSN[ds].split(' (')[0]} & {lab} & " + " & ".join(f"{q[f'{pre}_{k}'].mean():.3f}" for k in ("top1", "topk", "rbo", "rel")) + "\\\\")
        L.append("\\midrule")
    L[-1] = "\\bottomrule"; L.append("\\end{tabular}")
    open(f"{GEN}/tab_standards.tex", "w").write("\n".join(L))


# ------------------------------------------------------------------ background experiment
def bg_fig():
    B = []; A = []
    for f in glob.glob("/work/results/bg/*/inst_*.pkl"):
        r = pickle.load(open(f, "rb"))
        for b, v in r["A"].items():
            A.append(dict(ds=r["ds"], kind=r["kind"], b=b, rel=v["rel"].mean(), top3=v["topk"].mean(), top1=v["top1"].mean()))
        for (N, b), v in r["B"].items():
            B.append(dict(ds=r["ds"], kind=r["kind"], N=N, b=b, m=v["m"], rel=v["rel"].mean(), top3=v["topk"].mean(), top1=v["top1"].mean()))
    A, B = pd.DataFrame(A), pd.DataFrame(B)
    B = B[B.m >= MMIN]
    NUM["bgA"] = A.groupby(["ds", "b"])[["rel", "top1", "top3"]].mean().reset_index().to_dict("records")
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.3), sharey=True)
    for ax, ds in zip(axs, ["pima", "gmsc", "acsincome"]):
        q = B[B.ds == ds].groupby(["N", "b"]).top3.mean().unstack("b")
        a = A[A.ds == ds].groupby("b").top3.mean()
        for b in q.columns:
            ax.plot(q.index, q[b], marker="o", ms=2.5, label=f"b={b}")
        ax.set_xscale("log"); ax.set_xlabel("total budget $N=m\\cdot b$ (model calls)"); ax.set_title(DSN[ds], fontsize=8)
    axs[0].set_ylabel("P(top-3 set = reference top-3)"); axs[0].legend(fontsize=5.5, ncol=2, loc="lower right")
    fig.tight_layout(); fig.savefig(f"{FIG}/fig_background.pdf"); fig.savefig("/tmp/tmp_png/f5.png", dpi=110); plt.close(fig)
    q = B.groupby(["ds", "N", "b"]).agg(top3=("top3", "mean"), rel=("rel", "mean"), m=("m", "mean")).reset_index()
    q.to_csv(f"{GEN}/bg_fixedN.csv", index=False)
    A.groupby(["ds", "b"])[["rel", "top1", "top3"]].mean().reset_index().to_csv(f"{GEN}/bg_partA.csv", index=False)


def ci(x, B=2000):
    x = np.asarray(x, float); idx = rng.integers(0, len(x), (B, len(x))); b = x[idx].mean(1)
    return x.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)


def highd_and_lib():
    from metrics import vs_truth
    D = pickle.load(open("/work/results/highd/highd.pkl", "rb")); d = D["d"]
    rows = {}
    for r in D["res"]:
        for (mode, m), P in r["runs"].items():
            v = vs_truth(P.astype(float), r["phi"]); rows.setdefault((mode, m), []).append((np.median(v["rel"]), v["top1"].mean(), v["topk"].mean()))
        for name in ("lib_noL1", "lib_default"):
            v = vs_truth(r[name].astype(float), r["phi"]); rows.setdefault((name, 2 * d + 2048), []).append((np.median(v["rel"]), v["top1"].mean(), v["topk"].mean()))
    L = ["\\begin{tabular}{llccc}", "\\toprule", "Estimator & $m$ & median rel.\\ $\\ell_2$ err. & top-1 correct & top-3 set correct\\\\", "\\midrule"]
    nm = {"kernel": "Kernel SHAP (ours, no L1)", "leverage": "Leverage SHAP (ours)", "lib_noL1": "shap.KernelExplainer, l1\\_reg=False",
          "lib_default": "shap.KernelExplainer, default"}
    for (mode, m), v in rows.items():
        if mode in ("kernel", "leverage") and m not in (1024, 2048, 8192):
            continue
        a = np.array(v); c = [ci(a[:, j]) for j in range(3)]
        L.append(f"{nm[mode]} & {m} & {c[0][0]:.3f} & {c[1][0]:.3f} [{c[1][1]:.2f},{c[1][2]:.2f}] & {c[2][0]:.3f} [{c[2][1]:.2f},{c[2][2]:.2f}]\\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(f"{GEN}/tab_highd.tex", "w").write("\n".join(L))
    NUM["highd"] = {f"{k[0]}_{k[1]}": np.mean(v, 0).tolist() for k, v in rows.items()}
    NUM["highd_info"] = dict(d=D["d"], auc=D["auc"], ntrain=D["ntrain"], n=len(D["res"]))
    # shap library validation
    res = pickle.load(open("/work/results/shaplib/shaplib.pkl", "rb"))
    ids = {(r["ds"], r["inst"]) for r in res}
    sim = inst[(inst.kind == "xgb") & (inst.est.isin(["kernel", "perm"]))]
    sim = sim[[(a, b) in ids for a, b in zip(sim.ds, sim.inst)]]
    L = ["\\begin{tabular}{llrcccc}", "\\toprule", "Dataset & Variant & $m$ & lib: med.\\ rel.\\ err. & sim: med.\\ rel.\\ err. & lib: top-3 ok & sim: top-3 ok\\\\", "\\midrule"]
    out = []
    for ds in ["pima", "acsincome", "acsemployment", "german"]:
        for variant, simest in [("kernel_noL1", "kernel"), ("perm", "perm"), ("kernel_default", "kernel")]:
            for m in [64, 256, 1024, "auto"]:
                rr = [(np.median(o["rel"]), o["topk"].mean()) for r in res if r["ds"] == ds for (v, mm), o in r["out"].items() if v == variant and mm == m]
                if not rr:
                    continue
                mm_sim = 2 * len(next(r for r in res if r["ds"] == ds)["phi"]) + 2048 if m == "auto" else m
                sq = sim[(sim.ds == ds) & (sim.est == simest) & (sim.m == (2048 if m == "auto" else m))]
                lab = {"kernel_noL1": "Kernel, l1\\_reg=False", "perm": "Permutation", "kernel_default": "Kernel, default l1\\_reg"}[variant]
                if variant == "kernel_default" and m != "auto" and m != 256:
                    continue
                if variant != "kernel_default" and m not in (64, 256, "auto"):
                    continue
                if m == "auto" and variant == "perm":
                    continue
                simrel = f"{sq.t_rel.median():.3f}" if len(sq) else "--"; simtop = f"{sq.t_topk.mean():.3f}" if len(sq) else "--"
                L.append(f"{DSN[ds].split(' (')[0]} & {lab} & {m if m != 'auto' else str(mm_sim)} & {np.mean([x[0] for x in rr]):.3f} & {simrel} & {np.mean([x[1] for x in rr]):.3f} & {simtop}\\\\")
        L.append("\\midrule")
    L[-1] = "\\bottomrule"; L.append("\\end{tabular}")
    open(f"{GEN}/tab_shaplib.tex", "w").write("\n".join(L))


def fig_sd():
    fig, ax = plt.subplots(figsize=(3.6, 2.3))
    for ds in DSO:
        q = inst[(inst.ds == ds) & (inst.est == "kernel")].groupby("m").sd_rel.median()
        ax.plot(q.index, q.values, marker="o", ms=3, color=COL[ds], label=DSN[ds])
    m = np.array([64, 8192.]); ax.plot(m, 0.16 * (m / 64) ** -0.5, "k--", lw=0.7, label="slope $-1/2$")
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("budget $m$"); ax.set_ylabel("run-to-run SD / $\\|\\phi\\|_2$")
    ax.legend(fontsize=5.5)
    fig.tight_layout(); fig.savefig(f"{FIG}/fig_sd.pdf"); plt.close(fig)


if __name__ == "__main__":
    fig1(); rows = table_reliability(); write_table_reliability(rows); fig2(); cert(); est_table()
    bg_fig(); highd_and_lib(); fig_sd()
    if os.path.exists("/work/results/bgpair/bgpair.pkl"):
        standards()
    json.dump(NUM, open(f"{GEN}/numbers.json", "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
    print("ok")
