"""E3 analysis (P4, P7b/c): python3 analyze_e3.py RUNS_CSV OUT_JSON [--fresh FRESH_RUNS_CSV]

(i) time-scale test, per (model, width): OLS of log t_gen on log lr and log wd over the runs that generalised (bootstrap CI
    over runs). Time-scale prediction of a decoupled-weight-decay account: both exponents -1 (t_gen ~ 1/(lr*wd)); a pure
    learning-speed account: lr -1, wd 0. Collapse: SD of log10 of cell medians of t_gen vs of t_gen*lr*wd.
(ii) tuning test: per (model, width) the (lr, wd) cell with the smallest median t_gen (censored runs enter at steps_run) is
    selected on the seeds in RUNS_CSV (seeds 0-2); the width trend of t_gen is reported (a) at the baseline cell (lr 1e-3,
    wd 1), (b) at the selected cells on the selection seeds (optimistic: winner's curse), (c) at the selected cells on fresh
    seeds (--fresh) and (d) in every one of the (lr, wd) cells separately. Trends use analysis.analyse (Tobit slope, +-0.15 band).
"""
import argparse, json, sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import stats as S
import analysis as A


def ols_exponents(g, col, B=2000, seed=0):
    g = g[g[col].notna()]
    if len(g) < 5 or g.lr.nunique() < 2:
        return None
    X = np.c_[np.ones(len(g)), np.log(g.lr), np.log(g.wd)]; y = np.log(g[col].values)
    f = lambda X, y: np.linalg.lstsq(X, y, rcond=None)[0]
    b = f(X, y); rs = np.random.RandomState(seed); bs = []
    for _ in range(B):
        i = rs.randint(0, len(y), len(y))
        if len(np.unique(X[i, 1])) > 1 and len(np.unique(X[i, 2])) > 1:
            bs.append(f(X[i], y[i]))
    ci = np.percentile(bs, [2.5, 97.5], axis=0)
    return dict(n=len(g), lr_exp=float(b[1]), lr_ci=[float(ci[0, 1]), float(ci[1, 1])], wd_exp=float(b[2]), wd_ci=[float(ci[0, 2]), float(ci[1, 2])])


def collapse(g, col):
    c = g[g[col].notna()].groupby(["lr", "wd"])[col].agg(["median", "size"]).reset_index()
    c = c[c["size"] >= 2]
    if len(c) < 3:
        return None
    raw = np.log10(c["median"]); resc = np.log10(c["median"] * c.lr * c.wd); lrs = np.log10(c["median"] * c.lr)
    return dict(n_cells=len(c), sd_log10_raw=float(raw.std()), sd_log10_times_lr_wd=float(resc.std()), sd_log10_times_lr=float(lrs.std()))


def selected_cells(d, thr="99"):
    d = A.prep(d, thr); rows = []
    for (m, w), g in d.groupby(["model", "width"]):
        c = g.groupby(["lr", "wd"]).agg(med=("tgc", "median"), n_gen=("ev", "sum"), n=("ev", "size")).reset_index()
        c = c[c.n_gen >= 2]
        if len(c):
            r = c.sort_values("med").iloc[0]
            rows.append(dict(model=m, width=int(w), lr=float(r.lr), wd=float(r.wd), median_t_gen=float(r.med), n_gen=int(r.n_gen), n=int(r.n)))
    return pd.DataFrame(rows)


def pick(d, sel):
    parts = [d[(d.model == r.model) & (d.width == r.width) & np.isclose(d.lr, r.lr) & np.isclose(d.wd, r.wd)] for r in sel.itertuples()]
    return pd.concat(parts) if parts else d.iloc[:0]


def trend(d):
    if d.width.nunique() < 3 or len(d) < 6:
        return None
    return {t: A.analyse(d, t) for t in ("99", "95")}


def slim(t):
    if t is None:
        return None
    out = {}
    for thr, r in t.items():
        out[thr] = dict(n=int(sum(c["n"] for c in r["cells"])), tgen_slope=r["tgen_tobit_slope"], tfit_slope=r["tfit_slope"],
                        cells=[{k: c[k] for k in ("width", "n", "n_gen", "t_gen_km_median", "t_gen_km_ci", "t_fit_median")} for c in r["cells"]])
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("runs"); ap.add_argument("out"); ap.add_argument("--fresh", default="")
    ap.add_argument("--wd3-only", action="store_true", help="only add the wd=3 (d>=32) width trends to the existing OUT json")
    a = ap.parse_args()
    if a.wd3_only:
        # The selected tuned series switches from (lr 3e-3, wd 1) at d=16 to (3e-3, wd 3) at d>=32 (d=16 does not fit at wd 3), so
        # width is confounded with wd. Here the width trend is taken inside wd=3 only (d>=32), on the selection and the fresh seeds.
        d = pd.read_csv(a.runs); f = pd.read_csv(a.fresh); res = json.load(open(a.out))
        sel = pd.DataFrame(res["tuning"]["mlp"]["selected_99"]); sel = sel[sel.wd == 3.0]
        w3 = lambda x: x[(x.model == "mlp") & np.isclose(x.wd, 3.0) & (x.width >= 32)]
        out = res["tuning"]["mlp"]
        out["selected_cells_fresh_seeds_wd3"] = slim(trend(pick(f, sel))); out["selected_cells_selection_seeds_wd3"] = slim(trend(pick(d, sel)))
        out["wd3_d32_128_per_lr_selection_seeds"] = {f"lr{lr:g}": slim(trend(g)) for lr, g in w3(d).groupby("lr")}
        json.dump(res, open(a.out, "w"), indent=1, default=float); print("updated", a.out); sys.exit()
    d = pd.read_csv(a.runs); res = {"runs_file": a.runs, "n_runs": len(d), "time_scale": {}, "collapse": {}, "tuning": {}}
    for (m, w), g in d.groupby(["model", "width"]):
        k = f"{m}_d{w}"
        res["time_scale"][k] = {c: ols_exponents(g, c) for c in ("t_gen99_s", "t_gen95_s", "t_fit99_s")}
        res["collapse"][k] = {c: collapse(g, c) for c in ("t_gen99_s", "t_gen95_s", "t_fit99_s")}
    for m, gm in d.groupby("model"):
        tun = res["tuning"].setdefault(m, {})
        for thr in ("99", "95"):
            sel = selected_cells(gm, thr)
            tun[f"selected_{thr}"] = sel.to_dict("records")
        sel = selected_cells(gm, "99")
        base = gm[np.isclose(gm.lr, 1e-3) & np.isclose(gm.wd, 1.0)]
        tun["baseline_cell"] = slim(trend(base))
        tun["selected_cells_selection_seeds"] = slim(trend(pick(gm, sel)))
        tun["per_cell"] = {f"lr{lr:g}_wd{wd:g}": slim(trend(g)) for (lr, wd), g in gm.groupby(["lr", "wd"])}
        if a.fresh:
            f = pd.read_csv(a.fresh); f = f[f.model == m]
            tun["selected_cells_fresh_seeds"] = slim(trend(pick(f, sel)))
            tun["n_fresh_runs"] = int(len(pick(f, sel)))
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print("wrote", a.out)
