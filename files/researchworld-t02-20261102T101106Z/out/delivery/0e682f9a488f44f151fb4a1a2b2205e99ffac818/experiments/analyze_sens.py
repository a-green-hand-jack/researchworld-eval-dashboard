"""Sensitivity analyses for A1 (plan, amendment 2): step budget, accuracy threshold, width-scaled lr. Writes results/sens_stats.json.

(S1) budget: `long` runs (T_max 100000, widths 16/32, seeds 0-2) reproduce the `main` runs bit-for-bit up to step 30000
     (checked here), so they replace the censored `main` runs; seeds 3-4 stay censored at 30000. AFT slope of log t_gen on log2 width, widths >= w_min.
(S2) threshold 1.0: first logged step with val (train) acc >= 1.0; a run that ends without it is censored at steps_run
     (early stop is 500 steps after the 0.99 crossing, so this is a conservative bound on t_gen at 1.0).
(S3) width-scaled lr (`lrscale`, lr*sqrt(64/width)) vs `main` on the same seeds 0-2 at widths 32, 128: AFT slope on log2 width.
"""
import glob, json, os
import numpy as np
import pandas as pd
import analyze as A

OUT = A.OUT


def times(row, thr):
    r = json.load(open(os.path.join(A.HERE, row.file)))
    tg = next((l["step"] for l in r["log"] if l["val_acc"] >= thr), None)
    tf = next((l["step"] for l in r["log"] if l["train_acc"] >= thr), None)
    return tf, tg


def slope(df, tcol="t_gen", ev="grokked", wmin=None):
    wm = wmin if wmin is not None else A.w_min(df)
    g = df[df.width >= wm]
    X = np.c_[np.ones(len(g)), np.log2(g.width.values)]
    y = np.log(g[tcol].fillna(g.steps_run).values.astype(float))
    b, lo, hi, sg, nb = A.aft_boot(X, y, g[ev].values, strata=g.width.values)
    return dict(w_min=wm, slope=float(b[1]), ci95=[float(lo[1]), float(hi[1])], sigma=float(sg), n_runs=len(g), n_censored=int((~g[ev]).sum()), n_boot_ok=nb)


def main():
    main_, long_, ls_all = A.load("main"), A.load("long"), pd.concat([A.load("lrscale"), A.load("lrscale2")], ignore_index=True)
    ls = ls_all[ls_all.width.isin([32, 128])]
    res = {}
    res["S0_main_default"] = dict(slope(main_), note="as in main_stats.json: T_max 30000, threshold 0.99")
    # S1 budget
    ok = True
    for r in long_.itertuples():
        m = main_[(main_.width == r.width) & (main_.seed == r.seed)].iloc[0]
        a, b = json.load(open(os.path.join(A.HERE, m.file))), json.load(open(os.path.join(A.HERE, r.file)))
        lb = {l["step"]: l for l in b["log"]}
        ok &= all(lb[l["step"]]["val_acc"] == l["val_acc"] and lb[l["step"]]["wnorm"] == l["wnorm"] for l in a["log"])
    ext = pd.concat([main_[~main_.set_index(["width", "seed"]).index.isin(long_.set_index(["width", "seed"]).index)], long_], ignore_index=True)
    res["S1_extended_budget"] = dict(slope(ext), long_reproduces_main_through_30000=bool(ok),
        n_grok_by_width={int(w): [int(h.grokked.sum()), len(h)] for w, h in ext.groupby("width")},
        note="w16/w32 seeds 0-2 taken from `long` (T_max 100000), other runs as in `main` (censored at 30000); mixed censoring times handled per run. Includes w=8 in the table only; slope uses widths >= w_min")
    ext_wmin = dict(slope(ext, wmin=32), note="same, widths >= 32 only (the narrower widths still have censored runs at 100000 steps)")
    res["S1b_extended_budget_w>=32"] = ext_wmin
    # S2 threshold 1.0
    t1 = main_.copy()
    tt = [times(r, 1.0) for r in t1.itertuples()]
    t1["t_fit_1"] = [x[0] for x in tt]; t1["t_gen_1"] = [x[1] for x in tt]
    t1["grokked_1"] = t1.t_gen_1.notna()
    reach = t1[t1.grokked]
    res["S2_threshold_1.0"] = dict(slope(t1, tcol="t_gen_1", ev="grokked_1"),
        n_grok_099=int(t1.grokked.sum()), n_reach_val_1_within_run=int(t1.grokked_1.sum()),
        median_lag_099_to_1_steps=float((reach.t_gen_1 - reach.t_gen).median()),
        n_fit_1=int(sum(x[0] is not None for x in tt)),
        note="val acc >= 1.0; runs stopped (500 steps after the 0.99 crossing) before reaching 1.0 are censored at steps_run")
    # S2b lower thresholds (exact: crossing observed before the early stop)
    for thr in (0.9, 0.95):
        tg = [times(r, thr)[1] for r in main_.itertuples()]
        d = main_.copy(); d["t_g"] = tg; d["g"] = d.t_g.notna()
        res[f"S2b_threshold_{thr}"] = dict(slope(d, tcol="t_g", ev="g"), n_grok=int(d.g.sum()))
    # S2c exact threshold 1.0 on the w>=64 cells: `thr1` re-runs (deterministic) the `main` runs that reached 0.99, continued 5000 steps past t_gen
    th = A.load("thr1")
    if len(th):
        th = th.copy(); tt = [times(r, 1.0) for r in th.itertuples()]
        th["t_gen_1"] = [x[1] for x in tt]; th["g1"] = th.t_gen_1.notna()
        same = all(main_[(main_.width == r.width) & (main_.seed == r.seed)].t_gen.iloc[0] == r.t_gen for r in th.itertuples())
        rest = main_[(main_.width >= 64) & ~main_.set_index(["width", "seed"]).index.isin(th.set_index(["width", "seed"]).index)].copy()  # censored at 30000 for 0.99, hence for 1.0
        rest["t_gen_1"] = np.nan; rest["g1"] = False
        c = pd.concat([th, rest], ignore_index=True)
        lag = (th.t_gen_1 - th.t_gen).dropna()
        res["S2c_threshold_1.0_exact_w>=64"] = dict(slope(c, tcol="t_gen_1", ev="g1", wmin=64), n_thr1_runs=len(th), thr1_reproduces_main_t_gen=bool(same),
            n_reach_val_1=int(th.g1.sum()), lag_099_to_1_steps_median=float(lag.median()) if len(lag) else None, lag_max=float(lag.max()) if len(lag) else None,
            slope_099_same_runs=slope(c.assign(g=c.t_gen.notna()), tcol="t_gen", ev="g", wmin=64),
            note="widths >= 64 of f=0.4 `main`; runs that did not reach val 0.99 in 30000 steps are censored there for 1.0 too; thr1 runs continue 5000 steps after t_gen(0.99), val acc 1.0 not reached by then is censored at steps_run")
    # S3 lr scaling: counts only (3-5 seeds, most runs censored in the lrscale cells: an AFT slope is degenerate there)
    from scipy.stats import fisher_exact
    ns = int(ls.seed.max()) + 1 if len(ls) else 3
    m3 = main_[main_.width.isin([32, 128]) & (main_.seed < ns)]
    cells = {}
    for lab, d in (("main_same_seeds", m3), ("lrscale", ls)):
        cells[lab] = {int(w): dict(n=len(h), n_grok=int(h.grokked.sum()), tfit_median=float(h.t_fit.median())) for w, h in d.groupby("width")}
        k = [cells[lab][w]["n_grok"] for w in (32, 128)]
        nn = [cells[lab][w]["n"] for w in (32, 128)]
        cells[lab]["fisher_p_w128_vs_w32_grok"] = float(fisher_exact([[k[1], nn[1] - k[1]], [k[0], nn[0] - k[0]]])[1])
    res["S3_cells"] = dict(cells, note="lr multiplied by sqrt(64/width) (1.41e-3 at w=32, 0.71e-3 at w=128); same seeds in both arms (n per cell in the table); counts only")
    # S3b: lr*sqrt(64/width) over the whole width range (lrscale + lrscale2), seeds 0-2 common to all widths, vs the same seeds of `main`
    if ls_all.width.nunique() >= 3:
        sd = ls_all[ls_all.seed < 3]; mm = main_[main_.seed < 3]
        rows = []
        for lab, d in (("fixed_lr (main)", mm), ("lr*sqrt(64/width)", sd)):
            for w, h in d[d.width.isin(sorted(ls_all.width.unique()))].groupby("width"):
                t = h.t_gen.fillna(h.steps_run).values
                lo, hi = A.boot_ci(t, h.grokked.values)
                rows.append(dict(arm=lab, width=int(w), n=len(h), n_grok=int(h.grokked.sum()), tfit_median=float(h.t_fit.median()), tgen_km_median=float(A.km_median(t, h.grokked.values)), tgen_lo=lo, tgen_hi=hi))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, "sens_lrscale_grid.csv"), index=False)
        res["S3b_lrscale_grid_A1"] = dict(slope(sd, wmin=A.w_min(sd)), arm="lr*sqrt(64/width), seeds 0-2, widths " + str(sorted(map(int, sd.width.unique()))),
            main_same_seeds=slope(mm[mm.width.isin(sd.width.unique())], wmin=A.w_min(mm[mm.width.isin(sd.width.unique())])),
            note="AFT slope of log t_gen on log2 width over widths >= w_min of each arm (w_min by the 80% rule within the arm); T_max 30000; heavy censoring in the lrscale arm makes the slope a bound; per-cell table in sens_lrscale_grid.csv")
    json.dump(res, open(os.path.join(OUT, "sens_stats.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
