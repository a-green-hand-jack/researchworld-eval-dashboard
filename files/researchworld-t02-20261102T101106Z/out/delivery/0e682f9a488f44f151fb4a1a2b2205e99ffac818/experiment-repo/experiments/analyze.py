"""Aggregate runs/<sweep>/*.json into per-cell tables with uncertainty.

python analyze.py SWEEP [SWEEP ...]   -> results/<sweep>_cells.csv, results/<sweep>_runs.csv, results/<sweep>_stats.json
Censoring: a run with t_gen=None did not generalise within max_steps; it enters the delay/t_gen
statistics as right-censored (at steps_run), never dropped. Cell medians are Kaplan-Meier medians;
CIs are percentile bootstrap over seeds (2000 resamples). Trend: Jonckheere-Terpstra-type statistic with
pairwise comparison (see `pair_less`).
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")
rng = np.random.default_rng(0)


def km_median(t, event):
    """Kaplan-Meier median of right-censored times; inf if the curve never drops to 0.5."""
    t, event = np.asarray(t, float), np.asarray(event, bool)
    order = np.argsort(t, kind="stable"); t, event = t[order], event[order]
    n, S = len(t), 1.0
    for i, (ti, ei) in enumerate(zip(t, event)):
        if ei:
            S *= 1 - 1 / (n - i)
            if S <= 0.5:
                return ti
    return np.inf


def boot_ci(t, event, f=km_median, B=2000):
    t, event = np.asarray(t, float), np.asarray(event, bool)
    vals = []
    for _ in range(B):
        idx = rng.integers(0, len(t), len(t))
        vals.append(f(t[idx], event[idx]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return lo, hi


def pair_less(x, ex, y, ey):
    """+1 if x<y is certain, -1 if x>y certain, 0 if undetermined (censoring)."""
    if ex and ey: return (x < y) - (x > y)
    if ex and not ey: return 1 if x < y else 0       # y censored at y: true y >= y
    if ey and not ex: return -1 if y < x else 0
    return 0


def jt_trend(groups, B=5000):
    """Jonckheere-Terpstra-type statistic over ordered groups of (time,event); permutation p (two-sided)."""
    def stat(gs):
        s = 0
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                for (x, ex) in gs[i]:
                    for (y, ey) in gs[j]:
                        s += pair_less(x, ex, y, ey)
        return s  # >0: times increase with group index
    obs = stat(groups)
    sizes = [len(g) for g in groups]; flat = [z for g in groups for z in g]
    cnt = 0
    for _ in range(B):
        perm = rng.permutation(len(flat)); gs, k = [], 0
        for n in sizes:
            gs.append([flat[i] for i in perm[k:k + n]]); k += n
        cnt += abs(stat(gs)) >= abs(obs)
    return obs, (cnt + 1) / (B + 1)


def aft_fit(X, logy, event, ridge=1e-3):
    """Lognormal accelerated-failure-time MLE with right censoring: logy = X b + sigma*eps. X includes the intercept column
    (first). Non-intercept columns are standardised internally; a tiny ridge (1e-3 on standardised coefficients, per run)
    keeps the likelihood finite under near-separation (e.g. all runs of a cell censored). Returns (b, sigma) on the original scale."""
    from scipy.optimize import minimize
    from scipy.stats import norm
    X, logy, event = np.asarray(X, float), np.asarray(logy, float), np.asarray(event, bool)
    mu, sd = X[:, 1:].mean(0), X[:, 1:].std(0)
    sd[sd == 0] = 1.0
    Z = np.c_[X[:, 0], (X[:, 1:] - mu) / sd]
    n = len(logy)

    def nll(th):
        b, ls = th[:-1], th[-1]; sg = np.exp(ls)
        z = (logy - Z @ b) / sg
        lsf = norm.logsf(z); hz = np.exp(norm.logpdf(z) - lsf)  # hazard
        ll = np.where(event, norm.logpdf(z) - ls, lsf).sum()
        dz = np.where(event, -z, hz)  # d ll / d z
        gb = (Z * (dz * (-1 / sg))[:, None]).sum(0)
        gls = (dz * (-z)).sum() - event.sum()
        pen = ridge * n * (b[1:] ** 2).sum()
        gpen = np.r_[0, 2 * ridge * n * b[1:]]
        return -ll + pen, -np.r_[gb, gls] + np.r_[gpen, 0]
    b0 = np.linalg.lstsq(Z, logy, rcond=None)[0]
    th0 = np.r_[b0, np.log(max(np.std(logy - Z @ b0), 0.1))]
    r = minimize(nll, th0, jac=True, method="L-BFGS-B", bounds=[(None, None)] * len(b0) + [(np.log(0.05), np.log(20.0))])
    b = r.x[:-1].copy()
    b[1:] = b[1:] / sd
    b[0] = b[0] - (b[1:] * mu).sum()
    return b, float(np.exp(r.x[-1]))


def aft_boot(X, logy, event, B=500, strata=None):
    """Percentile bootstrap (resampling runs, within `strata` if given) of AFT coefficients -> (b, lo, hi, sigma)."""
    X, logy, event = np.asarray(X, float), np.asarray(logy, float), np.asarray(event, bool)
    b, sg = aft_fit(X, logy, event)
    strata = np.zeros(len(logy), int) if strata is None else np.asarray(strata)
    idx_by = [np.where(strata == k)[0] for k in np.unique(strata)]
    bs = []
    for _ in range(B):
        idx = np.concatenate([rng.choice(ix, len(ix)) for ix in idx_by])
        try:
            bs.append(aft_fit(X[idx], logy[idx], event[idx])[0])
        except Exception:
            pass
    bs = np.array(bs)
    return b, np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0), sg, len(bs)


def w_min(df, thr_frac=0.8):
    """Smallest width at which >= 80% of seeds reach train acc >= 0.99 within the step budget (plan, amendment 2)."""
    ok = df.groupby("width").fit.mean()
    ok = ok[ok >= thr_frac]
    return int(ok.index.min()) if len(ok) else None


def load(sweep):
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "runs", sweep, "*.json"))):
        r = json.load(open(f)); c = r["config"]
        tf, tg, T = r["t_fit"], r["t_gen"], r["steps_run"]
        log = r["log"]
        rows.append(dict(sweep=sweep, arch=c["arch"], op=c["op"], p=c["p"], frac=c["frac"], wd=c["wd"], lr=c["lr"], init_mult=c.get("init_mult", 1.0), split_seed=c.get("split_seed", -1), lr_ref=c.get("lr_ref", 0),
                         width=c["width"], seed=c["seed"], nparams=r["nparams"], max_steps=c["max_steps"],
                         steps_run=T, t_fit=tf, t_gen=tg, grokked=tg is not None, fit=tf is not None,
                         delay=(tg - tf) if (tg is not None and tf is not None) else np.nan,
                         delay_obs=(tg - tf) if (tg is not None and tf is not None) else (T - tf if tf is not None else np.nan),
                         final_train=log[-1]["train_acc"], final_val=log[-1]["val_acc"],
                         max_val=max(l["val_acc"] for l in log), wnorm_fit=next((l["wnorm"] for l in log if tf is not None and l["step"] >= tf), np.nan),
                         wnorm_gen=next((l["wnorm"] for l in log if tg is not None and l["step"] >= tg), np.nan), wnorm_final=log[-1]["wnorm"], nparams_f=float(r["nparams"]), wall_s=r["wall_s"], file=os.path.relpath(f, HERE)))
    df = pd.DataFrame(rows)
    if not df.empty:
        # grok: fits train then generalises later; direct: generalises without a preceding fit;
        # memorise-only: fits but never generalises within max_steps; neither: does neither.
        df["wrms_fit"] = df.wnorm_fit / np.sqrt(df.nparams_f)  # per-parameter RMS weight at fit (total L2 grows with sqrt(#params))
        df["regime"] = np.select([df.fit & df.grokked & (df.t_gen > df.t_fit), df.grokked, df.fit], ["grok", "direct", "memorise-only"], "neither")
    return df


def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    ph = k / n; d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d; h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def main(sweeps):
    os.makedirs(OUT, exist_ok=True)
    for sw in sweeps:
        df = load(sw)
        if df.empty: print("no runs", sw); continue
        df.to_csv(os.path.join(OUT, f"{sw}_runs.csv"), index=False)
        keys = ["arch", "op", "p", "frac", "wd", "lr", "init_mult", "split_seed", "lr_ref"]
        cells, stats = [], {}
        for key, g in df.groupby(keys):
            rec = []
            for w, h in g.groupby("width"):
                fit_ = h[h.fit]
                lo, hi = wilson(int(h.grokked.sum()), len(h))
                d = dict(zip(keys, key)); d.update(width=w, nparams=int(h.nparams.iloc[0]), n=len(h), n_fit=len(fit_), n_grok=int(h.grokked.sum()),
                         grok_lo=lo, grok_hi=hi)
                if len(fit_):
                    d["tfit_median"] = float(fit_.t_fit.median()); d["tfit_lo"], d["tfit_hi"] = boot_ci(fit_.t_fit, np.ones(len(fit_)), lambda t, e: np.median(t))
                    t, e = fit_.delay_obs.values, fit_.grokked.values
                    d["delay_km_median"] = float(km_median(t, e)); d["delay_lo"], d["delay_hi"] = boot_ci(t, e)
                    d["wnorm_fit_mean"] = float(fit_.wnorm_fit.mean())
                d["tgen_km_median"] = float(km_median(h.t_gen.fillna(h.steps_run), h.grokked))  # all runs, censored at steps_run
                d["tgen_lo"], d["tgen_hi"] = boot_ci(h.t_gen.fillna(h.steps_run).values, h.grokked.values)
                d["final_val_mean"] = float(h.final_val.mean())
                rec.append(d)
            cells += rec
            groups = [[(r.delay_obs, r.grokked) for r in g[(g.width == w) & g.fit].itertuples()] for w in sorted(g.width.unique())]
            groups = [x for x in groups if x]
            gall = [[(r.t_gen if r.grokked else r.steps_run, r.grokked) for r in g[g.width == w].itertuples()] for w in sorted(g.width.unique())]
            if len(gall) >= 3:
                s2, p2 = jt_trend(gall)
                stats["|".join(map(str, key)) + "|t_gen_all_widths"] = dict(JT_stat=s2, perm_p=p2, n_groups=len(gall), note="t_gen over all runs, censored at steps_run; stat>0: t_gen increases with width")
                wm = w_min(g)
                if wm is not None:
                    gw = g[g.width >= wm]
                    if gw.width.nunique() >= 2:
                        X = np.c_[np.ones(len(gw)), np.log2(gw.width.values)]
                        y = np.log(gw.t_gen.fillna(gw.steps_run).values.astype(float))
                        b, lo, hi, sg, nb = aft_boot(X, y, gw.grokked.values, strata=gw.width.values)
                        stats["|".join(map(str, key)) + "|A1_aft_slope"] = dict(w_min=wm, slope_log_tgen_per_log2_width=float(b[1]), ci95=[float(lo[1]), float(hi[1])],
                            sigma=sg, n_runs=len(gw), n_censored=int((~gw.grokked).sum()), n_boot_ok=nb,
                            note="lognormal AFT, right-censored at steps_run; bootstrap over runs within width; widths >= w_min (>=80% of seeds reach train acc 0.99); negative slope = faster generalisation for wider nets")
            if len(groups) >= 3:
                s, p_ = jt_trend(groups)
                stats["|".join(map(str, key)) + "|delay_fitted_runs"] = dict(JT_stat=s, perm_p=p_, n_groups=len(groups), note="delay over runs that fit; stat>0: delay increases with width")
        pd.DataFrame(cells).to_csv(os.path.join(OUT, f"{sw}_cells.csv"), index=False)
        json.dump(stats, open(os.path.join(OUT, f"{sw}_stats.json"), "w"), indent=1)
        print(sw, len(df), "runs"); print(pd.DataFrame(cells).round(3).to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
