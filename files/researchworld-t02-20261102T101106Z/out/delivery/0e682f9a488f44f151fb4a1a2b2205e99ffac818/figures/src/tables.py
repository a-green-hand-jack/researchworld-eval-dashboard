"""T1 per-cell main table, T2 scope conditions, T3 trend tests -> tables/*.tex and *.csv  (python tables.py)"""
import os
import numpy as np
import pandas as pd
import common as C


def lower_bound(runs, r, what="delay"):
    """Smallest observed delay in the cell: every seed's delay is at least this (censored runs count at their censoring time)."""
    g = runs[(runs.width == r.width) & (runs.frac == r.frac) & (runs.wd == r.wd) & (runs.arch == r.arch) & (runs.op == r.op)
             & (runs.init_mult == r.init_mult) & (runs.lr_ref == r.lr_ref) & (runs.split_seed == r.split_seed)]
    if what == "tgen":
        return np.where(g.grokked, g.t_gen, g.steps_run).min()
    return g[g.fit].delay_obs.min()


def fmt_ci(m, lo, hi, lb):
    """Median [lo, hi]; hi = infinity when censored runs make the resampled median undefined; '>lb' if the KM median is undefined."""
    if not np.isfinite(m):
        return r"$>$" + f"{lb:,.0f}"
    up = f"{hi:,.0f}" if np.isfinite(hi) else r"$\infty$"
    return f"{m:,.0f} [{lo:,.0f}, {up}]"


def cell_table(cells, label_cols, runs):
    rows = []
    for r in cells.itertuples():
        d = {c: getattr(r, c) for c in label_cols}
        d.update(width=int(r.width), params=int(r.nparams), grokked=f"{r.n_grok}/{r.n}")
        g = runs[(runs.width == r.width) & (runs.frac == r.frac) & (runs.wd == r.wd) & (runs.arch == r.arch) & (runs.op == r.op)
                 & (runs.init_mult == r.init_mult) & (runs.lr_ref == r.lr_ref) & (runs.split_seed == r.split_seed)]
        d["regimes G/D/M/N"] = "/".join(str(int((g.regime == k).sum())) for k in ("grok", "direct", "memorise-only", "neither"))
        d[r"KM median $t_{\mathrm{gen}}$ [95\% CI]"] = fmt_ci(r.tgen_km_median, r.tgen_lo, r.tgen_hi, lower_bound(runs, r, "tgen")) if np.isfinite(r.tgen_lo) or not np.isfinite(r.tgen_km_median) else f"{r.tgen_km_median:,.0f} [n/a]"
        d[r"median $t_{\mathrm{fit}}$ [95\% CI]"] = f"{r.tfit_median:,.0f} [{r.tfit_lo:,.0f}, {r.tfit_hi:,.0f}]" if r.n_fit else "–"
        d[r"KM median delay [95\% CI]"] = (fmt_ci(r.delay_km_median, r.delay_lo, r.delay_hi, lower_bound(runs, r)) if r.n_fit else "–")
        rows.append(d)
    return pd.DataFrame(rows)


def write(df, name, caption, label, tex_df=None, latex=True, align="r"):
    os.makedirs(C.TABDIR, exist_ok=True)
    df.to_csv(os.path.join(C.TABDIR, name + ".csv"), index=False)
    if not latex: return
    tex_df = df if tex_df is None else tex_df
    def tx(x):
        if not isinstance(x, str): return x
        x = x.replace("≥", "$\\geq$").replace("≤", "$\\leq$").replace("–", "--")
        return "$".join(p.replace("_", "\\_") if i % 2 == 0 and "\\_" not in p else p for i, p in enumerate(x.split("$")))
    tex_df = tex_df.map(tx)
    tex_df.columns = [c if "$" in c or "\\_" in c else c.replace("_", "\\_") for c in tex_df.columns]
    out = tex_df.to_latex(index=False, escape=False, column_format=align * len(tex_df.columns), caption=caption, label=label, position="t")
    # booktabs rules as emitted by pandas; shrink font
    out = out.replace("\\centering", "\\centering\\small")
    out = out.replace("\\begin{tabular}", "\\resizebox{\\linewidth}{!}{%\n\\begin{tabular}").replace("\\end{tabular}", "\\end{tabular}}")
    open(os.path.join(C.TABDIR, name + ".tex"), "w").write(out)


def main():
    m = C.load_cells("main")
    if not m.empty:
        t = cell_table(m.sort_values("width"), [], C.load_runs("main"))
        write(t, "t1_main", "Main sweep per width (5 seeds each). Regimes G/D/M/N: seeds that grok / generalise directly / memorise only / neither. Medians are Kaplan--Meier with 95\\% bootstrap CIs over seeds; $>x$: median undefined (over half the seeds censored at 30,000 steps), $x$ = smallest observed value; $\\infty$: CI bound undefined. Censored runs are never dropped.", "tab:main")
    rows = []
    for s in ("frac", "wd", "wd0", "alpha", "lrscale", "lrscale2", "splitfix", "mlp", "mul"):
        c = C.load_cells(s)
        if c.empty: continue
        c = c.copy(); c.insert(0, "sweep", s)
        t = cell_table(c.sort_values(["frac", "wd", "width"]), ["sweep", "arch", "op", "frac", "wd", "init_mult", "lr_ref", "split_seed"], C.load_runs(s))
        def cond(r):
            out = []
            if r.arch != "tf": out.append(f"arch {r.arch}")
            if r.op != "add": out.append(f"op {r.op}")
            if r.frac != 0.4: out.append(f"train frac {r.frac:g}")
            if r.wd != 1.0: out.append(f"wd {r.wd:g}")
            if r.init_mult != 1.0: out.append(f"init $\\times${r.init_mult:g}")
            if r.lr_ref: out.append(f"lr $\\propto 1/\\sqrt{{w}}$ (ref {int(r.lr_ref)})")
            if r.split_seed != -1: out.append(f"split seed {int(r.split_seed)}")
            return ", ".join(out)
        t.insert(1, "condition", [cond(r) for r in t.itertuples()])
        t = t.drop(columns=["arch", "op", "frac", "wd", "init_mult", "lr_ref", "split_seed", "params"])
        rows.append(t)
    if rows:
        write(pd.concat(rows), "t2_scope", "Scope sweeps: same columns as Table~\\ref{tab:main} for secondary conditions.", "tab:scope")
    st = []

    def aft_row(sweep, cond, v, label=None):
        lo, hi = v["ci95"]; sl = v.get("slope_log_tgen_per_log2_width", v.get("slope"))
        return dict(sweep=sweep, condition=cond, endpoint=label or f"log t_gen per doubling (AFT, w ≥ {v['w_min']})",
                    estimate=f"{sl:.2f} [{lo:.2f}, {hi:.2f}]", test=f"n = {v['n_runs']} ({v['n_censored']} censored)", verdict=v.get("verdict", "–"))
    for s_ in C.SWEEPS:
        for k, v in C.load_stats(s_).items():
            key, _, kind = k.rpartition("|"); key = {"tf": "transformer", "mlp": "MLP"}[key.split("|")[0]] + ", add mod 53, $f$=0.4"
            if "JT_stat" in v:
                name = {"t_gen_all_widths": "t_gen, all runs", "delay_fitted_runs": "delay, runs that fit"}.get(kind, "delay, runs that fit")
                if kind not in ("t_gen_all_widths", "delay_fitted_runs"): key = k.replace("|", "/")
                st.append(dict(sweep=s_, condition=key, endpoint=name, estimate=f"JT = {v['JT_stat']:.0f}", test=f"permutation p = {v['perm_p']:.4f}", verdict="–"))
            elif "slope_log_tgen_per_log2_width" in v:
                st.append(aft_row(s_, key, v))
    labels = {"S1_extended_budget": "100k-step ceiling for w ≤ 32, seeds 0–2", "S1b_extended_budget_w>=32": "same, widths ≥ 32 only",
              "S2_threshold_1.0": "threshold 1.0 (bound only)",
              "S2c_threshold_1.0_exact_w>=64": "threshold 1.0, exact re-runs (thr1)", "S2b_threshold_0.9": "threshold 0.90", "S2b_threshold_0.95": "threshold 0.95"}
    for k, v in C.load_stats("sens").items():
        if k in labels and "ci95" in v:
            st.append(aft_row("sensitivity", labels[k], v, label=f"log t_gen per doubling (AFT, w ≥ {v['w_min']})"))
    s3 = C.load_stats("sens").get("S3b_lrscale_grid_A1")
    if s3:
        st.append(aft_row("sensitivity", "lr $\\propto 1/\\sqrt{w}$, seeds 0--2, w 16--256", s3,
                          label=f"log t_gen per doubling (AFT, w ≥ {s3['w_min']}); CI unreliable"))
        if "main_same_seeds" in s3:
            st.append(aft_row("sensitivity", "fixed lr, same seeds and widths (reference)", s3["main_same_seeds"],
                              label=f"log t_gen per doubling (AFT, w ≥ {s3['main_same_seeds']['w_min']})"))
    if st:
        write(pd.DataFrame(st), "t3_trend", "Trend of generalisation time with width. JT: Jonckheere--Terpstra-type statistic, negative = faster for wider nets, "
              "two-sided permutation $p$, censoring-aware. AFT: lognormal accelerated-failure-time slope of $\\log t_{gen}$ on $\\log_2$ width, 95\\% bootstrap CI over seeds "
              "(the plan's A1 estimand; negative = wider nets generalise sooner). Verdict: the plan's rule with the negligible bands of story-repo's \\texttt{VERDICTS.md}, as written by the analysis position into the stats files "
              "(bands set after the results were seen). The scaled-learning-rate row is censored for 10 of 15 runs; with most runs sharing one censoring time the bootstrap CI collapses toward 0, "
              "so an interval inside the negligible band is not evidence of no effect (the verdict is inconclusive, not null).", "tab:trend", align="l")

    mech = C.load_mech()

    def est(c, k=None):
        c = c if k is None else c[k]
        return f"{c['est']:.2f} [{c['lo']:.2f}, {c['hi']:.2f}]" if isinstance(c, dict) else f"{c[0]:.2f} [{c[1]:.2f}, {c[2]:.2f}]"
    def cl(v, k):
        """(estimate [CI], verdict) of the norm coefficient (k='norm') or the width coefficient and the 'only through norm' verdict (k='width')."""
        if v is None: return "–", "–"
        if k == "norm":
            key = next(t for t in v["coef"] if t.startswith("lognorm"))
            return est(v["coef"][key]), v.get("verdict", "–")
        return est(v["coef"]["logwidth"]), v.get("verdict_only_through_norm", "–")
    rows = []
    for sample, lab in (("main_only", "main sweep (n=26, 12 cens.)"), ("all_tf_add_f0.4", "all $f$=0.4 runs (n=66, 24 cens.)")):
        for spec, term, slab in (("", "norm", "$\\log$ norm (given $\\log t_{fit}$)"), ("+logwidth", "norm", "$\\log$ norm (given $\\log t_{fit}$, $\\log$ width)"), ("+logwidth", "width", "$\\log$ width (given $\\log t_{fit}$, $\\log$ norm)")):
            d = {"sample": lab, "coefficient": slab}
            for meas, nm in (("fit", "total L2"), ("rms", "RMS")):
                v = mech.get(f"reg|{sample}|logD~logtfit+lognorm_{meas}{spec}")
                e, vd = cl(v, term)
                d[f"{nm} [CI]"] = e; d[f"{nm} verdict"] = vd
            rows.append(d)
    if rows:
        t4 = pd.DataFrame(rows)
        full = [dict(analysis=k, model=v.get("model", ""), n=v.get("n_runs", ""), censored=v.get("n_censored", ""), term=term, est=c["est"], lo=c["lo"], hi=c["hi"],
                     verdict=v.get("verdict", ""), verdict_only_through_norm=v.get("verdict_only_through_norm", ""))
                for k, v in mech.items() if "coef" in v for term, c in v["coef"].items() if term != "intercept"]
        write(pd.DataFrame(full), "t4_mechanism_all", "all mechanism coefficients (csv only)", "tab:mechall", latex=False)
        write(t4, "t4_mechanism", "A2(ii): regression of $\\log D$ (lognormal AFT, censored runs kept) on $\\log t_{fit}$ and the weight norm at $t_{fit}$ ($\\pm$ $\\log$ width), "
              "with the norm measured as the total L2 norm of all parameters and as the per-parameter RMS (total/$\\sqrt{\\mathrm{params}}$; total L2 grows with width by construction). "
              "Cells: coefficient [95\\% bootstrap CI] and the verdict under the plan's bands (norm coefficient predicted $>0$: supported if the CI lies above 0.25, refuted if below 0.25). "
              "For the width row the verdict is for ``width acts only through $t_{fit}$ and the norm'' (refuted if the width CI excludes 0). Width and norm are collinear, so these are supporting only. "
              "Regressions on the norm at $t_{gen}$ are outcome-contaminated and not shown.", "tab:mech", align="l")
    rows = []
    for k, v in mech.items():
        if k.startswith("wd_slope") and v.get("model") == "log D":
            rows.append({"estimand": "A2(i): $d\\log D/d\\log wd$ (predicted $-1$)", "setting": f"width {k.split('width=')[1].split('|')[0]}, wd $\\in$ {{0.5, 1, 2}}",
                         "n (censored)": f"{v['n_runs']} ({v['n_censored']})", "estimate [CI]": est(v["coef"]["logwd"]), "verdict": v.get("verdict", "–"), "direction-only": "–"})
    for k, v in mech.items():
        if k.startswith("alpha_effect") and v.get("model") == "log t_gen":
            rows.append({"estimand": "A2(iii): $d\\log t_{gen}/d\\log\\alpha$ (init scale)", "setting": f"width {k.split('width=')[1].split('|')[0]}, $\\alpha\\in${{0.5, 1, 2}}",
                         "n (censored)": f"{v['n_runs']} ({v['n_censored']})", "estimate [CI]": est(v["coef"]["logalpha"]), "verdict": v.get("verdict", "–"), "direction-only": v.get("verdict_direction_only", "–")})
    if rows:
        write(pd.DataFrame(rows), "t5_wd_alpha", "A2(i) weight-decay exponent and A2(iii) init-scale effect (lognormal AFT, censored runs kept; the $wd=0.5$ runs have a 60,000-step ceiling). "
              "A2(i): supported if the CI lies inside $[-1.3,-0.7]$, refuted if wholly outside. A2(iii): the mediation account predicts a positive slope where the norm at fit rises with $\\alpha$ "
              "(supported if lo $>0.10$, refuted if hi $<-0.10$; ``not tested'' where the norm at fit is not monotone in $\\alpha$); the direction-only column asks only whether hi $<0$.", "tab:wdalpha", align="l")


if __name__ == "__main__":
    main()
