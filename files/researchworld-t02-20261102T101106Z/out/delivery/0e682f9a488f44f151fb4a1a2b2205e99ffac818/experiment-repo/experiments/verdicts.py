"""Adds a `verdict` (supported / refuted / inconclusive / not tested) and the `band` used to each estimand in results/*_stats.json,
mech_stats.json and sens_stats.json, from the negligible bands of story-repo plan/VERDICTS.md ("Negligible bands"; set after the first
results were seen, as that file discloses). Also writes results/verdicts.json (summary + A3 contrasts). Run after analyze*.py; idempotent.

Rules as implemented (CI = 95% bootstrap CI; lo, hi its ends):
 A1  slope of log t_gen per log2 width:        supported  hi < -0.10;  refuted lo > 0 or (lo > -0.10 and hi < 0.10);  else inconclusive.
 A2-i exponent b of log y on log wd:           supported  -1.3 <= lo and hi <= -0.7;  refuted hi < -1.3 or lo > -0.7;  else inconclusive.
 A2-ii norm coefficient (prediction > 0):      supported  lo > 0.25;  refuted hi < 0.25;  else inconclusive.   (log norm at fit; `_gen` models are outcome-contaminated: not rated)
       width coefficient in the model with width: `verdict_only_through_norm` = refuted if its CI excludes 0, else inconclusive.
 A2-iii alpha slope of log y on log alpha, where norm at fit rises monotonically with alpha (mediation predicts slope > 0):
       supported (mediation direction) lo > 0.10;  refuted hi < -0.10;  else inconclusive;  `verdict_direction_only`: refuted hi < 0, supported lo > 0.
       The band text says "refuted ... beyond the band" but also calls hi = -0.08 refuted; `verdict` uses the strict reading, `verdict_direction_only` the loose one.
       Where norm at fit is not monotone in alpha: "not tested".
 A3  grok fractions: supported (a difference) if the Wilson 95% CIs do not overlap, else inconclusive.
"""
import json, os
import numpy as np
import pandas as pd
import analyze as A

R = A.OUT


def a1(lo, hi):
    if hi < -0.10: return "supported"
    if lo > 0 or (lo > -0.10 and hi < 0.10): return "refuted"
    return "inconclusive"


def wd(lo, hi):
    if lo >= -1.3 and hi <= -0.7: return "supported"
    if hi < -1.3 or lo > -0.7: return "refuted"
    return "inconclusive"


def norm_c(lo, hi):
    if lo > 0.25: return "supported"
    if hi < 0.25: return "refuted"
    return "inconclusive"


def alpha_strict(lo, hi):
    if lo > 0.10: return "supported"
    if hi < -0.10: return "refuted"
    return "inconclusive"


def alpha_dir(lo, hi):
    return "supported" if lo > 0 else "refuted" if hi < 0 else "inconclusive"


def load(n): return json.load(open(os.path.join(R, n)))
def save(n, d): json.dump(d, open(os.path.join(R, n), "w"), indent=1)


def main():
    summ = {}
    # A1: every <sweep>_stats.json entry and the sensitivity entries
    for sw in ("main", "mlp", "frac", "wd", "alpha", "wd0", "lrscale", "long", "mul"):
        fn = f"{sw}_stats.json"
        if not os.path.exists(os.path.join(R, fn)): continue
        d = load(fn)
        for k, v in d.items():
            if k.endswith("A1_aft_slope"):
                v["verdict"] = a1(*v["ci95"]); v["band"] = "A1: supported if CI wholly < -0.10; refuted if wholly > 0 or inside +-0.10"
                summ[f"{sw}|A1_aft_slope"] = dict(slope=v["slope_log_tgen_per_log2_width"], ci95=v["ci95"], verdict=v["verdict"])
        save(fn, d)
    s = load("sens_stats.json")
    for k, v in s.items():
        if "slope" in v and "ci95" in v:
            v["verdict"] = a1(*v["ci95"]); v["band"] = "A1 band (see main)"
            if v.get("n_censored", 0) > 0.5 * v.get("n_runs", 1) and v["verdict"] == "refuted":
                v["verdict"] = "inconclusive"
                v["verdict_note"] = "more than half the runs are censored: the lognormal-AFT bootstrap CI collapses toward 0 when most runs share one censoring time, so a CI inside +-0.10 is not read as evidence of no effect"
            summ[f"sens|{k}"] = dict(slope=v["slope"], ci95=v["ci95"], verdict=v["verdict"])
    save("sens_stats.json", s)
    # A2
    m = load("mech_stats.json")
    ac = pd.read_csv(os.path.join(R, "mech_alpha_cells.csv")) if os.path.exists(os.path.join(R, "mech_alpha_cells.csv")) else pd.DataFrame()
    for k, v in m.items():
        if "coef" not in v: continue
        c = v["coef"]
        if k.startswith("wd_slope"):
            v["verdict"] = wd(c["logwd"]["lo"], c["logwd"]["hi"]); v["band"] = "A2-i: supported if CI inside [-1.3,-0.7]; refuted if wholly outside; prediction b=-1"
            summ[k] = dict(est=c["logwd"]["est"], ci95=[c["logwd"]["lo"], c["logwd"]["hi"]], verdict=v["verdict"])
        elif k.startswith("reg|"):
            nk = "lognorm_fit" if "lognorm_fit" in c else "lognorm_rms" if "lognorm_rms" in c else None
            if nk is None:
                v["verdict"] = "not rated"; v["band"] = "norm at t_gen is outcome-contaminated"; continue
            v["verdict"] = norm_c(c[nk]["lo"], c[nk]["hi"]); v["band"] = "A2-ii: norm coefficient predicted > 0; supported lo > 0.25, refuted hi < 0.25"
            if "logwidth" in c:
                v["verdict_only_through_norm"] = "refuted" if (c["logwidth"]["lo"] > 0 or c["logwidth"]["hi"] < 0) else "inconclusive"
                v["verdict_only_through_norm_band"] = "'width acts only through t_fit and norm' refuted if the width coefficient CI excludes 0 (collinear with norm: supporting only)"
            summ[k] = dict(norm_coef=[c[nk]["est"], c[nk]["lo"], c[nk]["hi"]], verdict=v["verdict"], only_through_norm=v.get("verdict_only_through_norm"),
                           width_coef=[c["logwidth"][x] for x in ("est", "lo", "hi")] if "logwidth" in c else None)
        elif k.startswith("alpha_effect"):
            w = int(k.split("width=")[1].split("|")[0]); h = ac[ac.width == w].sort_values("alpha")
            h = h[h.n_fit > 0]
            up = bool(h.wnorm_fit_mean.is_monotonic_increasing) if len(h) >= 3 else False
            lo, hi = c["logalpha"]["lo"], c["logalpha"]["hi"]
            if up:
                v["verdict"] = alpha_strict(lo, hi); v["verdict_direction_only"] = alpha_dir(lo, hi)
            else:
                v["verdict"] = v["verdict_direction_only"] = "not tested"
            v["band"] = "A2-iii: mediation predicts slope > 0 where norm at fit rises with alpha; supported lo > 0.10, refuted hi < -0.10 (strict); direction-only: hi < 0. Not tested if norm at fit is not monotone in alpha"
            v["norm_at_fit_monotone_increasing_in_alpha"] = up
            summ[k] = dict(est=c["logalpha"]["est"], ci95=[lo, hi], verdict=v["verdict"], verdict_direction_only=v["verdict_direction_only"], norm_monotone=up)
    save("mech_stats.json", m)
    # A3 contrasts (Wilson CIs non-overlapping)
    cells = {sw: pd.read_csv(os.path.join(R, f"{sw}_cells.csv")) for sw in ("main", "frac", "wd0") if os.path.exists(os.path.join(R, f"{sw}_cells.csv"))}
    def cell(sw, w, f=0.4, wdv=1.0):
        c = cells[sw]; r = c[(c.width == w) & (np.isclose(c.frac, f)) & (np.isclose(c.wd, wdv)) & (c.init_mult == 1.0) & (c.lr_ref == 0)]
        return None if r.empty else r.iloc[0]
    def contrast(label, a, b):
        if a is None or b is None: return None
        ov = not (a.grok_hi < b.grok_lo or b.grok_hi < a.grok_lo)
        return dict(contrast=label, a=f"{int(a.n_grok)}/{int(a.n)}", a_wilson=[a.grok_lo, a.grok_hi], b=f"{int(b.n_grok)}/{int(b.n)}", b_wilson=[b.grok_lo, b.grok_hi],
                    verdict="inconclusive" if ov else "supported", rule="supported (a difference) if Wilson 95% CIs do not overlap",
                    prestated_pattern_5of5_vs_le1of5=bool(a.n_grok == a.n and b.n_grok <= 1),
                    note="with n=5 the plan's pattern 5/5 vs <=1/5 cannot have non-overlapping Wilson CIs (1/5 upper 0.62 > 5/5 lower 0.57); the Wilson rule is used for `verdict`, the pattern flag is reported separately")
    a3 = []
    allc = pd.concat(cells.values(), ignore_index=True)
    for w in (32, 128):
        for f1, f2 in ((0.5, 0.25), (0.5, 0.4), (0.4, 0.25)):
            ca, cb = [None if allc[(allc.width == w) & np.isclose(allc.frac, f) & (allc.wd == 1.0) & (allc.init_mult == 1.0) & (allc.lr_ref == 0)].empty else
                      allc[(allc.width == w) & np.isclose(allc.frac, f) & (allc.wd == 1.0) & (allc.init_mult == 1.0) & (allc.lr_ref == 0)].iloc[0] for f in (f1, f2)]
            a3.append(contrast(f"width {w}: f={f1} vs f={f2}", ca, cb))
    for f in (0.25, 0.4, 0.5):
        g = allc[np.isclose(allc.frac, f) & (allc.wd == 1.0) & (allc.init_mult == 1.0) & (allc.lr_ref == 0)]
        a_, b_ = g[g.width == 128], g[g.width == 32]
        if len(a_) and len(b_): a3.append(contrast(f"f={f}: width 128 vs 32 (critical-f shift)", a_.iloc[0], b_.iloc[0]))
    w0 = allc[(allc.wd == 0.0) & (allc.width == 64)]; w1 = allc[(allc.wd == 1.0) & (allc.width == 64) & np.isclose(allc.frac, 0.4) & (allc.init_mult == 1.0) & (allc.lr_ref == 0)]
    if len(w0) and len(w1): a3.append(contrast("width 64, f=0.4: wd=0 vs wd=1", w0.iloc[0], w1.iloc[0]))
    a3 = [x for x in a3 if x]
    a2 = {}
    for lab in ("all_tf_add_f0.4", "main_only"):
        for meas, nk in (("total_L2", "lognorm_fit"), ("per_parameter_RMS", "lognorm_rms")):
            e0, e1 = m.get(f"reg|{lab}|logD~logtfit+{nk}"), m.get(f"reg|{lab}|logD~logtfit+{nk}+logwidth")
            if e0 and e1:
                a2[f"{lab}|{meas}"] = dict(n_runs=e0["n_runs"], norm_coef_no_width=[e0["coef"][nk][x] for x in ("est", "lo", "hi")], verdict_norm_coef=e0["verdict"],
                    width_coef_with_width=[e1["coef"]["logwidth"][x] for x in ("est", "lo", "hi")], verdict_only_through_norm=e1["verdict_only_through_norm"])
    a2["which_norm"] = ("Primary for comparing widths: per-parameter RMS weight at t_fit (L2/sqrt(#params)). Total L2 of all parameters grows with sqrt(#params), i.e. about linearly in width, "
        "even when every parameter has the same typical size, so it is collinear with width by construction and a coefficient on it cannot be told apart from a width effect. "
        "The RMS removes that built-in dependence. Total L2 is reported as the plan's original measure. 'Only through norm' is refuted under total L2 and inconclusive under RMS "
        "(all f=0.4 runs); the `main_only` fits (26 runs, 5 widths) are unstable under both and not used.")
    save("verdicts.json", dict(summary=summ, A2ii_norm_measure=a2, A3_contrasts=a3, bands_source="story-repo plan/VERDICTS.md 'Negligible bands' (set after results were seen)"))
    for k, v in summ.items(): print(k, v)
    for x in a3: print(x["contrast"], x["a"], x["b"], x["verdict"])


if __name__ == "__main__":
    main()
