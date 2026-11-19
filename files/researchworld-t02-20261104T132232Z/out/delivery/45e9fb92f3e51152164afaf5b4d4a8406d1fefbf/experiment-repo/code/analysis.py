"""Width-trend analysis used for E1/E2/E3 settings: python3 analysis.py e1 RUNS_CSV OUT_JSON [--max-seed N] [--label TXT]

For one (model, task, p, f, lr, wd) setting with runs over widths it reports, for both sustained thresholds (0.99, 0.95):
per-width cells (n, censored, fraction generalising with Wilson CI, KM median t_gen with bootstrap CI, medians of t_fit and
delay with CI), the t_gen-vs-width Tobit log-log slope with bootstrap CI and the verdict against the +-0.15 'flat' band,
the permutation Spearman test, and pre-stated contrasts (smallest vs largest width, d=32 vs d=256) as bootstrap CIs of
differences in log10 medians. Censored runs enter at steps_run and are flagged; nothing is dropped.
"""
import argparse, json, sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import stats as S

FLAT = 0.15


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def prep(d, thr):
    d = d.copy()
    d["tg"] = d[f"t_gen{thr}_s"]; d["tf"] = d["t_fit99_s"]
    d["ev"] = d.tg.notna(); d["tgc"] = d.tg.fillna(d.steps_run)
    d["fitted"] = d.tf.notna()
    d["delay"] = d.tg - d.tf
    return d


def med_ci(x, B=3000):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    lo, hi = S.boot_ci(x, np.median, B)
    return (float(np.median(x)), float(lo), float(hi))


def contrast(d, w1, w2, col, B=3000):
    a = d[d.width == w1][col].dropna().values; b = d[d.width == w2][col].dropna().values
    if len(a) < 2 or len(b) < 2:
        return None
    f = lambda x, y: np.log10(np.median(y)) - np.log10(np.median(x))
    ests = [f(S.RNG.choice(a, len(a)), S.RNG.choice(b, len(b))) for _ in range(B)]
    return dict(w1=w1, w2=w2, log10_ratio_median=float(f(a, b)), ci=[float(x) for x in np.percentile(ests, [2.5, 97.5])])


def analyse(d, thr):
    d = prep(d, thr); out = {"threshold": thr, "cells": []}
    for w, g in d.groupby("width"):
        n = len(g); k = int(g.ev.sum()); lo, hi = wilson(k, n)
        kmc = S.boot_ci((g.tgc.values, g.ev.values), S.km_median, 2000) if n > 1 else (np.nan, np.nan)
        tf = med_ci(g.tf.dropna()); dl = med_ci(g.delay.dropna())
        plateau = int(((~g.ev) & (g.max_val_acc >= 0.95)).sum())
        out["cells"].append(dict(width=int(w), n=n, n_params=int(g.n_params.iloc[0]), n_gen=k, frac_gen=k / n, frac_gen_ci=[lo, hi],
                                 n_plateau_cens=plateau, t_gen_km_median=float(S.km_median(g.tgc, g.ev)), t_gen_km_ci=[float(kmc[0]), float(kmc[1])],
                                 t_fit_median=tf[0], t_fit_ci=list(tf[1:]), delay_median=dl[0], delay_ci=list(dl[1:]),
                                 sd_log10_tgen=float(np.log10(g.tg.dropna()).std()) if g.ev.sum() > 1 else None))
    w = d.width.values
    b, ci = S.tobit_slope(w, d.tgc.values, d.ev.values, 1000)
    out["tgen_tobit_slope"] = dict(slope=float(b), ci=[float(ci[0]), float(ci[1])],
                                    flat=bool(ci[0] >= -FLAT and ci[1] <= FLAT), band=FLAT,
                                    verdict="flat (CI inside band)" if (ci[0] >= -FLAT and ci[1] <= FLAT) else ("nonzero (CI excludes 0)" if (ci[0] > 0 or ci[1] < 0) else "inconclusive (CI overlaps 0 and exceeds band)"))
    r, p = S.perm_spearman(w, d.tgc.values, 5000); out["tgen_spearman"] = dict(rho=float(r), perm_p=float(p), note="censored at steps_run")
    dd = d[d.delay.notna()]
    if len(dd) > 3:
        r, p = S.perm_spearman(dd.width.values, dd.delay.values, 5000); out["delay_spearman"] = dict(rho=float(r), perm_p=float(p), n=len(dd))
    ft = d[d.fitted]
    sl, sci = S.loglog_slope(ft.width.values, ft.tf.values, 2000); out["tfit_slope"] = dict(slope=float(sl), ci=[float(sci[0]), float(sci[1])])
    ws = sorted(d.width.unique())
    out["contrasts"] = {"tgen_c_smallest_vs_largest": contrast(d, ws[0], ws[-1], "tgc"), "delay_smallest_vs_largest": contrast(d, ws[0], ws[-1], "delay"),
                        "delay_32_vs_256": contrast(d, 32, 256, "delay") if 32 in ws and 256 in ws else None}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("runs"); ap.add_argument("out")
    ap.add_argument("--max-seed", type=int, default=10**9); ap.add_argument("--label", default="")
    ap.add_argument("--where", default="")      # pandas query, e.g. "model=='mlp' and train_frac==0.5"
    a = ap.parse_args()
    d = pd.read_csv(a.runs)
    if a.where:
        d = d.query(a.where)
    d = d[d.seed <= a.max_seed]
    res = dict(label=a.label, runs_file=a.runs, where=a.where, max_seed=a.max_seed, n_runs=len(d), by_threshold=[analyse(d, t) for t in ("99", "95")])
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    for t in res["by_threshold"]:
        s = t["tgen_tobit_slope"]
        print(f"[{a.label}] thr {t['threshold']}: n={res['n_runs']} t_gen Tobit slope {s['slope']:.2f} CI {s['ci'][0]:.2f},{s['ci'][1]:.2f} {s['verdict']}; spearman {t['tgen_spearman']}")
        for c in t["cells"]:
            print("   w", c["width"], "n", c["n"], "gen", c["n_gen"], "plateau", c["n_plateau_cens"], "KM", c["t_gen_km_median"], "fit", c["t_fit_median"], "delay", c["delay_median"])
