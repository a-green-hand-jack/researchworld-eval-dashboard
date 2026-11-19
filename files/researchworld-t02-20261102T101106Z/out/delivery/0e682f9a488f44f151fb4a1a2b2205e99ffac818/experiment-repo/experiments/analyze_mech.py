"""Mechanism analyses for A2 (plan, amendment 2). Reads runs/{main,wd,alpha}/ via analyze.load; writes results/mech_*.json|csv.

(a) wd: AFT slope of log D and log t_gen on log wd, per width (main wd=1 cell + `wd` sweep), bootstrap CI over runs.
(b) regression (supporting only): AFT of log D on log t_fit and log norm (at fit, or at t_gen), with/without log width.
(c) init scale alpha: per (width, alpha) cell stats; AFT effect of log alpha on log t_gen and log D, per width.
(d) norm-matched comparison table: norm at fit and t_gen / D per (width, alpha) so a wide net at alpha matching the narrow net's norm can be compared.
All censoring-aware (lognormal AFT, censored at steps_run); a run with no t_fit is excluded from D analyses (reported by count).
"""
import json, os
import numpy as np
import pandas as pd
import analyze as A

OUT = A.OUT


def base(df):
    return df[(df.arch == "tf") & (df.op == "add") & (df.p == 53) & (df.lr == 1e-3) & (df.lr_ref == 0) & (df.split_seed == -1)]


def aft_table(d, xcols, yname, label):
    """d: runs with fit; y = log(D_obs) or log(t_gen or censor). Returns dict of coefficient estimates with CI."""
    y = d[yname].values.astype(float)
    ev = d.grokked.values
    X = np.c_[np.ones(len(d))] if not xcols else np.c_[np.ones(len(d)), *[d[c].values for c in xcols]]
    b, lo, hi, sg, nb = A.aft_boot(X, np.log(y), ev, strata=d.stratum.values if "stratum" in d else None)
    names = ["intercept"] + xcols
    return dict(model=label, n_runs=len(d), n_censored=int((~ev).sum()), sigma=sg, n_boot_ok=nb,
                coef={n: dict(est=float(b[i]), lo=float(lo[i]), hi=float(hi[i])) for i, n in enumerate(names)})


def main():
    runs = {}
    for sw in ("main", "wd", "alpha"):
        d = A.load(sw)
        if not d.empty: runs[sw] = d
    if "main" not in runs: return
    allr = base(pd.concat(runs.values(), ignore_index=True))
    allr["delay_obs"] = allr.delay_obs.astype(float)
    res = {}
    # (a) wd slope
    wd_rows = allr[(allr.frac == 0.4) & (allr.init_mult == 1.0)]
    for w, g in wd_rows.groupby("width"):
        g = g[g.fit].copy()
        if g.wd.nunique() < 2 or g.wd.eq(0).any(): g = g[g.wd > 0]
        if g.wd.nunique() < 2: continue
        g["logwd"] = np.log(g.wd); g["stratum"] = g.wd
        g["tgen_obs"] = g.t_gen.fillna(g.steps_run)
        for yname, lab in (("delay_obs", "log D"), ("tgen_obs", "log t_gen")):
            gg = g[g[yname] > 0]
            res[f"wd_slope|width={w}|{lab}"] = dict(aft_table(gg, ["logwd"], yname, lab),
                                                  wd_levels=sorted(map(float, g.wd.unique())),
                                                  note="slope = d log y / d log wd; plan A2-i predicts -1 for D (CI containing both -1 and 0 = inconclusive)")
    # (b) regression on all alpha=1 runs and on everything incl. alpha runs
    for lab, sub in (("main_only", allr[(allr.wd == 1.0) & (allr.init_mult == 1.0) & (allr.frac == 0.4)]), ("all_tf_add_f0.4", allr[allr.frac == 0.4])):
        g = sub[sub.fit & (sub.wd > 0)].copy()
        g = g[g.delay_obs > 0]
        if len(g) < 8: continue
        g["logtfit"] = np.log(g.t_fit); g["lognorm_fit"] = np.log(g.wnorm_fit); g["logwidth"] = np.log(g.width)
        g["lognorm_gen"] = np.log(g.wnorm_gen.fillna(g.wnorm_final))  # censored runs: norm at the end of the run
        g["stratum"] = g.width
        for cols in (["logtfit", "lognorm_fit"], ["logtfit", "lognorm_fit", "logwidth"], ["logtfit", "lognorm_gen"], ["logtfit", "lognorm_gen", "logwidth"]):
            res[f"reg|{lab}|logD~{'+'.join(cols)}"] = dict(aft_table(g, cols, "delay_obs", "log D"),
                note="supporting only: width and norm are nearly collinear, t_fit is on both sides; total L2 norm of all parameters. lognorm_gen is measured at/after the outcome (end of run for censored runs), so it is not an admissible predictor of D: read only the *_fit models as tests of the norm mechanism")
    # (c)(d) init scale
    al = allr[(allr.wd == 1.0) & (allr.frac == 0.4)]
    if (al.init_mult != 1.0).any():
        cells = []
        for (w, a), h in al.groupby(["width", "init_mult"]):
            fit_ = h[h.fit]
            c = dict(width=w, alpha=a, n=len(h), n_fit=len(fit_), n_grok=int(h.grokked.sum()),
                     tfit_median=float(fit_.t_fit.median()) if len(fit_) else np.nan,
                     tgen_km_median=float(A.km_median(h.t_gen.fillna(h.steps_run), h.grokked)),
                     wnorm_fit_mean=float(fit_.wnorm_fit.mean()) if len(fit_) else np.nan,
                     wnorm_gen_mean=float(h.wnorm_gen.mean()) if h.wnorm_gen.notna().any() else np.nan,
                     wnorm_final_mean=float(h.wnorm_final.mean()))
            if len(fit_):
                c["tgen_lo"], c["tgen_hi"] = A.boot_ci(h.t_gen.fillna(h.steps_run).values, h.grokked.values)
                c["D_km_median"] = float(A.km_median(fit_.delay_obs.values, fit_.grokked.values))
            cells.append(c)
        cdf = pd.DataFrame(cells)
        cdf.to_csv(os.path.join(OUT, "mech_alpha_cells.csv"), index=False)
        nf = cdf.set_index(["width", "alpha"]).wnorm_fit_mean
        res["norm_matched"] = dict(wnorm_fit_mean={f"w{w}|alpha{a}": float(v) for (w, a), v in nf.items()},
            note="Norm-matched comparison (wide net at an alpha whose norm at fit equals the narrow net's) is not achievable with alpha: the norm at t_fit (first logged step >= t_fit, 250-500 steps) is measured after 250-500 optimiser steps, and alpha does not set it cleanly: at w=32 it is 34.0/32.6/34.8 for alpha 0.5/1/2 (non-monotone, within 7%), at w=128 39.1/42.8/48.3. The lowest norm at fit at w=128 (alpha 0.5, 39.1) still exceeds w=32 alpha=1 (32.6), so no alpha in the run grid matches them; alpha<0.5 was not run (budget). The alpha effect on t_gen is therefore reported as a total effect of init scale, not as an effect through norm at fit.")
        for w, h in al.groupby("width"):
            if h.init_mult.nunique() < 2: continue
            h = h.copy(); h["logalpha"] = np.log(h.init_mult); h["stratum"] = h.init_mult
            h["tgen_obs"] = h.t_gen.fillna(h.steps_run)
            res[f"alpha_effect|width={w}|log t_gen"] = dict(aft_table(h, ["logalpha"], "tgen_obs", "log t_gen"), note="d log t_gen / d log alpha; all runs, censored at steps_run")
            hf = h[h.fit & (h.delay_obs > 0)]
            if len(hf) > 6: res[f"alpha_effect|width={w}|log D"] = dict(aft_table(hf, ["logalpha"], "delay_obs", "log D"), note="runs that fit; D censored at steps_run - t_fit")
    # (b') same regressions with the per-parameter RMS norm at fit (L2/sqrt(#params)); run last so the RNG stream of the models above is unchanged
    for lab, sub in (("main_only", allr[(allr.wd == 1.0) & (allr.init_mult == 1.0) & (allr.frac == 0.4)]), ("all_tf_add_f0.4", allr[allr.frac == 0.4])):
        g = sub[sub.fit & (sub.wd > 0)].copy(); g = g[g.delay_obs > 0]
        if len(g) < 8: continue
        g["logtfit"] = np.log(g.t_fit); g["lognorm_rms"] = np.log(g.wrms_fit); g["logwidth"] = np.log(g.width); g["stratum"] = g.width
        for cols in (["logtfit", "lognorm_rms"], ["logtfit", "lognorm_rms", "logwidth"]):
            res[f"reg|{lab}|logD~{'+'.join(cols)}"] = dict(aft_table(g, cols, "delay_obs", "log D"),
                note="per-parameter RMS weight at fit = total L2 / sqrt(#params); total L2 grows with sqrt(#params) and so with width, RMS does not by construction. Width and norm remain collinear; supporting only")
    json.dump(res, open(os.path.join(OUT, "mech_stats.json"), "w"), indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("coef", "n_runs", "n_censored")} for k, v in res.items()}, indent=1)[:3000])


if __name__ == "__main__":
    main()
