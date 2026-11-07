"""Seed-level (cluster) bootstrap, minimum detectable slope and threshold-rule table for the width slopes.

python3 robust_slopes.py SPEC.json OUT_PREFIX [--B 1000]

SPEC.json: list of {label, csv (path or list of paths), query (pandas, optional), group (free text)}.
For every setting and each generalisation threshold (0.99, 0.95, 0.50) it reports the lognormal right-censored (Tobit)
log-log slope of t_gen on width with two 95% percentile-bootstrap CIs, resampling (a) runs (as code/analysis.py) and (b) seeds:
a resampled seed brings all of its runs at every width (the train/val split depends on the seed only, so widths are paired).
Same for the OLS slope of t_fit. Censored runs enter at steps_run. Verdict classes as in analysis.py: flat / nonzero / inconclusive
against the +-0.15 band. Also per setting: within-cell SD of log t_gen (events only), the standard error of the slope implied
by the design, and the minimum detectable |slope| (80% power, two-sided 5%) = 2.8 * SE (a lower bound: censoring inflates SE).
Outputs OUT_PREFIX.json, OUT_PREFIX_table.csv and OUT_PREFIX_threshold_rule.md.
"""
import argparse, json, sys
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

BAND = 0.15
THR = {"99": "t_gen99_s", "95": "t_gen95_s", "50": "t_gen50_s"}


def tobit(lx, ly, ev):
    """log t = a + b lx + s eps, right-censored where ev is False. Returns b (nan if not estimable)."""
    if ev.sum() < 3 or len(np.unique(lx)) < 2:
        return np.nan
    b0, a0 = np.polyfit(lx[ev], ly[ev], 1) if len(np.unique(lx[ev])) > 1 else (0.0, ly[ev].mean())
    s0 = max(np.std(ly[ev] - (a0 + b0 * lx[ev])), 0.05)

    def nll(th):
        a, b, ls = th; s = np.exp(ls); z = (ly - a - b * lx) / s
        return -np.where(ev, norm.logpdf(z) - ls, norm.logsf(z)).sum()
    return minimize(nll, [a0, b0, np.log(s0)], method="Nelder-Mead", options=dict(xatol=1e-5, fatol=1e-8, maxiter=3000)).x[1]


def ols(lx, ly):
    return np.polyfit(lx, ly, 1)[0] if len(np.unique(lx)) > 1 and len(lx) > 2 else np.nan


def verdict(lo, hi):
    if np.isnan(lo):
        return "n/a"
    if lo >= -BAND and hi <= BAND:
        return "flat"
    return "nonzero" if (lo > 0 or hi < 0) else "inconclusive"


def boot(fn, d, B, rs, by_seed):
    """fn(df) -> slope. by_seed: resample seeds (all runs of a seed together), else resample runs."""
    out = []
    if by_seed:
        seeds = np.sort(d.seed.unique()); groups = {s: d[d.seed == s] for s in seeds}
        for _ in range(B):
            pick = rs.choice(seeds, len(seeds))
            out.append(fn(pd.concat([groups[s] for s in pick])))
    else:
        for _ in range(B):
            out.append(fn(d.iloc[rs.randint(0, len(d), len(d))]))
    out = np.array(out, float)
    return np.nanpercentile(out, [2.5, 97.5]) if np.isfinite(out).sum() > B / 2 else np.array([np.nan, np.nan]), int(np.isfinite(out).sum())


def tgen_fn(col):
    def f(g):
        t = g[col].fillna(g.steps_run).values.astype(float)
        return tobit(np.log(g.width.values.astype(float)), np.log(t), g[col].notna().values)
    return f


def tfit_fn(g):
    g = g[g.t_fit99_s.notna()]
    return ols(np.log(g.width.values.astype(float)), np.log(g.t_fit99_s.values.astype(float)))


def design(d, col):
    """SD of log t_gen within (width) cells among events, and the SE of the log-log slope implied by the design."""
    e = d[d[col].notna()].copy(); e["l"] = np.log(e[col])
    if len(e) < 6:
        return dict(sigma=None, se=None, mds80=None)
    res = e.l - e.groupby("width").l.transform("mean"); dof = len(e) - e.width.nunique()
    sigma = float(np.sqrt((res ** 2).sum() / max(dof, 1)))
    lx = np.log(d.width.values.astype(float)); sxx = ((lx - lx.mean()) ** 2).sum()
    se = sigma / np.sqrt(sxx)
    return dict(sigma=sigma, se=float(se), mds80=float(2.8 * se), se_target_band=BAND / 1.96, seeds_per_cell_for_flat=None)


def load(spec):
    csvs = spec["csv"] if isinstance(spec["csv"], list) else [spec["csv"]]
    d = pd.concat([pd.read_csv(c) for c in csvs]).drop_duplicates("run_id")
    return d.query(spec["query"]) if spec.get("query") else d


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("out"); ap.add_argument("--B", type=int, default=1000)
    a = ap.parse_args()
    res, rows = [], []
    for spec in json.load(open(a.spec)):
        d = load(spec); rs = np.random.RandomState(0)
        r = dict(label=spec["label"], group=spec.get("group", ""), n_runs=len(d), n_seeds=int(d.seed.nunique()), widths=sorted(int(w) for w in d.width.unique()),
                 seeds_per_width={int(w): int(g.seed.nunique()) for w, g in d.groupby("width")}, thr={})
        for k, col in THR.items():
            if col not in d:
                continue
            f = tgen_fn(col); b = f(d)
            run_ci, nr = boot(f, d, a.B, rs, False); seed_ci, ns = boot(f, d, a.B, rs, True)
            r["thr"][k] = dict(n_events=int(d[col].notna().sum()), slope=float(b), run_ci=run_ci.tolist(), seed_ci=seed_ci.tolist(),
                               verdict_run=verdict(*run_ci), verdict_seed=verdict(*seed_ci), design=design(d, col))
            rows.append(dict(label=spec["label"], group=spec.get("group", ""), thr=k, n_runs=len(d), n_seeds=r["n_seeds"], n_events=r["thr"][k]["n_events"],
                             slope=b, run_lo=run_ci[0], run_hi=run_ci[1], seed_lo=seed_ci[0], seed_hi=seed_ci[1], verdict_run=verdict(*run_ci), verdict_seed=verdict(*seed_ci),
                             sigma_within=r["thr"][k]["design"]["sigma"], se_design=r["thr"][k]["design"]["se"], mds80=r["thr"][k]["design"]["mds80"]))
        fit = tfit_fn(d); run_ci, _ = boot(tfit_fn, d, a.B, rs, False); seed_ci, _ = boot(tfit_fn, d, a.B, rs, True)
        r["tfit"] = dict(slope=float(fit), run_ci=run_ci.tolist(), seed_ci=seed_ci.tolist())
        rows.append(dict(label=spec["label"], group=spec.get("group", ""), thr="tfit", n_runs=len(d), n_seeds=r["n_seeds"], n_events=int(d.t_fit99_s.notna().sum()),
                         slope=fit, run_lo=run_ci[0], run_hi=run_ci[1], seed_lo=seed_ci[0], seed_hi=seed_ci[1], verdict_run=verdict(*run_ci), verdict_seed=verdict(*seed_ci)))
        res.append(r); print(spec["label"], {k: round(v["slope"], 2) for k, v in r["thr"].items()}, flush=True)
    json.dump(res, open(a.out + ".json", "w"), indent=1, default=float)
    T = pd.DataFrame(rows); T.to_csv(a.out + "_table.csv", index=False)
    # threshold rule: a t_gen verdict counts only if the class is the same at 0.99 and 0.95 (50% reported alongside)
    lines = ["| setting | class @0.99 | class @0.95 | class @0.50 | survives both-threshold rule | class (seed-level CI) @0.99 / @0.95 |", "|---|---|---|---|---|---|"]
    for lab, g in T[T.thr != "tfit"].groupby("label", sort=False):
        v = {r.thr: r.verdict_run for r in g.itertuples()}; vs = {r.thr: r.verdict_seed for r in g.itertuples()}
        ok = v.get("99") == v.get("95")
        lines.append(f"| {lab} | {v.get('99','-')} | {v.get('95','-')} | {v.get('50','-')} | {'yes: ' + v['99'] if ok else 'no (classes differ)'} | {vs.get('99','-')} / {vs.get('95','-')} |")
    open(a.out + "_threshold_rule.md", "w").write("\n".join(lines) + "\n")
    print("wrote", a.out)
