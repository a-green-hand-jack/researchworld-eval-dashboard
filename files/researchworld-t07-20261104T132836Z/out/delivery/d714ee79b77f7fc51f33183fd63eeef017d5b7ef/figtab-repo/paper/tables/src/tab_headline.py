"""C1: headline tables (LaTeX fragments).  Outputs (tables/):
  headline_<protocol>_n<n>.tex  -- cross-benchmark summary, one block per protocol (main text);
  perbench_<protocol>_n<n>.tex  -- per-benchmark RMSE and Kendall tau_b with model-level CIs (appendix).

Summary rows (all from cells.csv point estimates; the benchmark is the unit; HELM benchmarks share models):
  RMSE ratio = geometric mean over benchmarks of RMSE(method)/RMSE(random mean);  95% percentile bootstrap over benchmarks (B=2000).
  Kendall = mean over benchmarks.  Wins = number of benchmarks with RMSE below random mean.
Bold = not distinguishable from the best row of the column: paired bootstrap over benchmarks (same resamples) of the
log RMSE ratio / the Kendall difference to the best row has a 95% CI containing 0.  The `Sources only` row uses no target items.
Per-benchmark tables: RMSE in accuracy points (x100); brackets are the committed model/split-level 95% bootstrap CI;
bold = lowest RMSE (highest Kendall) in the row; a dagger marks a method whose paired difference to MASS-Ens has a 95% CI excluding 0
(paired.csv).
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figures", "src"))
import common as C

ROWS = ["sources_only", "random", "strat_random", "calib", "ridge", "anchor", "irt_rand", "irt_info", "anchor_irt",
        "aipw_rand", "aipw_ridge_cf", "ppi", "aipw_knn", "aipw_ens", "mass", "mass_ens"]
PB_COLS = ["sources_only", "random", "ridge", "anchor_irt", "aipw_rand", "mass", "mass_ens"]
B = 2000


def tex_esc(s):
    return s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")


def _col(lr, ix, ms):
    """Per-method geometric-mean ratio, bootstrap CI and 'tied with best' flag for one benchmark subset."""
    out = {m: dict(v=lr[m].values) for m in ms}
    for m in ms:
        v = out[m]["v"]; bv = v[ix].mean(1)
        out[m].update(val=np.exp(v.mean()), ci=np.exp(np.percentile(bv, [2.5, 97.5])), wins=int((v < 0).sum()))
    ref = min(ms, key=lambda m: out[m]["val"])
    for m in ms:
        d = out[m]["v"][ix].mean(1) - out[ref]["v"][ix].mean(1)
        out[m]["tie"] = (m == ref) or np.percentile(d, 2.5) <= 0 <= np.percentile(d, 97.5)
    return out


def summary(cells, proto, n):
    c = cells[(cells.protocol == proto) & (cells.n == n)]
    rm = c[c.metric == "rmse"].pivot(index="bench", columns="method", values="mean")
    ke = c[c.metric == "kendall"].pivot(index="bench", columns="method", values="mean")
    ms = [m for m in ROWS if m in rm.columns]
    lr = np.log(rm[ms].div(rm["random"], axis=0))      # log RMSE ratio per benchmark
    rng = np.random.default_rng(0)
    res = {}
    for key, bs in [("all", list(lr.index)), ("nondev", [b for b in lr.index if b not in C.DEV])]:
        ix = rng.integers(0, len(bs), (B, len(bs)))
        res[key] = _col(lr.loc[bs], ix, ms)
    bs = list(ke.index); ix = rng.integers(0, len(bs), (B, len(bs)))
    kc = {}
    for m in ms:
        k = ke[m].values; bk = k[ix].mean(1)
        kc[m] = dict(val=k.mean(), ci=np.percentile(bk, [2.5, 97.5]), k=k)
    ref_k = max(ms, key=lambda m: kc[m]["val"])
    for m in ms:
        d = kc[m]["k"][ix].mean(1) - kc[ref_k]["k"][ix].mean(1)
        kc[m]["tie"] = (m == ref_k) or np.percentile(d, 2.5) <= 0 <= np.percentile(d, 97.5)
    res["kendall"] = kc
    return ms, res, len(lr)


def bold(s, b):
    return f"\\textbf{{{s}}}" if b else s


def write_summary(cells, proto, n, outdir):
    ms, o, nb = summary(cells, proto, n)
    L = ["\\begin{tabular}{lcccc}", "\\toprule",
         f"Method & RMSE ratio, all {nb} & RMSE ratio, {nb - len(C.DEV)} non-dev. & wins (of {nb}) & Kendall $\\tau_b$ \\\\", "\\midrule"]
    fm = lambda r: f"{r['val']:.2f} [{r['ci'][0]:.2f}, {r['ci'][1]:.2f}]"
    for m in ms:
        a, d, k = o["all"][m], o["nondev"][m], o["kendall"][m]
        if m == "sources_only":
            ken = "-- (constant)"
        else:
            ken = bold(fm(k), k["tie"])
        wins = "--" if m == "random" else str(a["wins"])
        L.append(f"{tex_esc(C.ml(m))} & {bold(fm(a), a['tie'])} & {bold(fm(d), d['tie'])} & {wins} & {ken} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    p = os.path.join(outdir, f"headline_{proto}_n{n}.tex")
    open(p, "w").write("\n".join(L) + "\n"); print("wrote", p)


def write_perbench(cells, paired, proto, n, outdir, cols=PB_COLS):
    c = cells[(cells.protocol == proto) & (cells.n == n)]
    cols = [m for m in cols if m in set(c.method)]
    pp = paired[(paired.protocol == proto) & (paired.n == n) & (paired.method == "mass_ens")]
    allcols = cols
    for met, scale, fmt in [("rmse", 100, "{:.1f}"), ("kendall", 1, "{:.2f}")]:
        d = c[c.metric == met]
        cols = [m for m in allcols if not (met == "kendall" and m == "sources_only")]   # constant prediction: rank correlation undefined
        L = ["\\begin{tabular}{l" + "c" * len(cols) + "}", "\\toprule",
             "Benchmark & " + " & ".join(tex_esc(C.ml(m)) for m in cols) + " \\\\", "\\midrule"]
        for b in C.benches(d):
            g = d[d.bench == b].set_index("method")
            vals = {m: g.loc[m, "mean"] for m in cols if m in g.index}
            best = (min if met == "rmse" else max)(vals, key=vals.get)
            cells_ = []
            for m in cols:
                if m not in g.index:
                    cells_.append("--"); continue
                r = g.loc[m]
                s = f"{fmt.format(r['mean'] * scale)} [{fmt.format(r.ci_lo * scale)}, {fmt.format(r.ci_hi * scale)}]"
                if m != "mass_ens":
                    q = pp[(pp.bench == b) & (pp.metric == met) & (pp.ref == m)]
                    if len(q) and (q.ci_lo.iloc[0] > 0 or q.ci_hi.iloc[0] < 0):
                        s += "$^\\dagger$"
                cells_.append(bold(s, m == best))
            L.append(tex_esc(C.bl(b, tex=True)) + " & " + " & ".join(cells_) + " \\\\")
        L += ["\\bottomrule", "\\end{tabular}"]
        p = os.path.join(outdir, f"perbench_{met}_{proto}_n{n}.tex")
        open(p, "w").write("\n".join(L) + "\n"); print("wrote", p)


if __name__ == "__main__":
    os.makedirs(C.OUT_TAB, exist_ok=True)
    cells = C.load("cells.csv"); paired = C.load("paired.csv")
    for proto in ("extrap", "random"):
        for n in (50, 100):
            if len(cells[(cells.protocol == proto) & (cells.n == n)]):
                write_summary(cells, proto, n, C.OUT_TAB)
                write_perbench(cells, paired, proto, n, C.OUT_TAB)
