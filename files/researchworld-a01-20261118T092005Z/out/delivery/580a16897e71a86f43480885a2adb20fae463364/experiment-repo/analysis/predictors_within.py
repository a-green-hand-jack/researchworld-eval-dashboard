"""E4 / R3, within-board: cross-validated R^2 of log price on the rule-specific gap (and gap + dispersion + correlation), by board and rule.
usage: predictors_within.py TABLES_DIR   reads price.csv; writes predictors_within.csv.  The transfer test of predictors.py stays the stated R3 verdict; this table answers a different question:
is the price predictable from the gap on the board it is fitted on?  Data as in predictors.py (own incumbent, targets with a positive gap and a positive finite depth at the cap B; all HELM models, top-30 OLLB targets).
Models: 'rank' (log initial rank), 'gap' (log rule-specific gap), 'gap+disp+corr' (+ target dispersion, incumbent dispersion, profile correlation); OLS.
Grouped cross-validation, out-of-fold prediction for every target from a fit on the other groups: cv = 'family' (leave one target family out) or 'incumbent' (leave one incumbent out; only when >= 4 distinct incumbents, which
the own-incumbent design rarely gives).  cv_r2 = 1 - SSE(model) / SSE(training-fold mean of y): out-of-fold R^2 against the intercept-only prediction of the same folds.  CI: cluster bootstrap over the target families of the out-of-fold
predictions (the fold fits are not refitted).  gain = cv_r2(gap+disp+corr) - cv_r2(gap) with its paired CI.  by_construction marks the mean rule, whose price is exactly m x gap (R^2 = 1 says nothing); zmean is linear in a gap in task-sigma units and median/min are monotone functions of one or a few task shortfalls, so their R^2 is high largely by definition.  r2_insample is the ordinary in-sample R^2 of the fit on all targets of the cell, for reference."""
import sys, os, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore", category=RuntimeWarning)
import numpy as np, pandas as pd
from features import features
T = sys.argv[1]; NB = int(os.environ.get("NBOOT", 2000))
p = pd.read_csv(f"{T}/price.csv"); p = p[p.incumbent == "own"]
MODELS = {"rank": ["lrank"], "gap": ["lgap"], "gap+disp+corr": ["lgap", "tdisp", "ldisp", "corr"]}
RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]


def design(d, cols): return np.column_stack([np.ones(len(d))] + [d[c].values for c in cols])


def oof(d, cols, groups):
    y = d.y.values; pred = np.full(len(d), np.nan); base = np.full(len(d), np.nan)
    for g in np.unique(groups):
        te = groups == g; tr = ~te
        beta = np.linalg.lstsq(design(d[tr], cols), y[tr], rcond=None)[0]
        pred[te] = design(d[te], cols) @ beta; base[te] = y[tr].mean()
    return pred, base


def r2(y, pred, base):
    sst = ((y - base) ** 2).sum(); return 1 - ((y - pred) ** 2).sum() / sst if sst > 0 else np.nan


rows = []
for B in (10.0, 20.0, 100.0):
    q = p[(p.B == B) & p.rule.isin(RULES) & (p.gap > 0) & (p.depth_star > 0) & np.isfinite(p.depth_star)].copy()
    q = pd.concat([features(b, g) for b, g in q.groupby("board")]); q["y"] = np.log(q.depth_star)
    for (board, rule), d in q.groupby(["board", "rule"]):
        d = d.reset_index(drop=True)
        if len(d) < 12 or d.family.nunique() < 4: continue
        for cv, col in (("family", "family"), ("incumbent", "incumbent_id")):
            groups = pd.factorize(d[col])[0]
            if len(np.unique(groups)) < 4: continue
            fam = pd.factorize(d.family)[0]; k = fam.max() + 1; grp = [np.flatnonzero(fam == c) for c in range(k)]
            rng = np.random.default_rng(31); picks = [np.concatenate([grp[c] for c in rng.integers(0, k, k)]) for _ in range(NB)]
            res = {}
            for name, cols in MODELS.items():
                pred, base = oof(d, cols, groups); res[name] = (pred, base)
            for name, cols in MODELS.items():
                pred, base = res[name]; y = d.y.values
                bs = np.array([r2(y[ix], pred[ix], base[ix]) for ix in picks])
                A = design(d, cols); beta = np.linalg.lstsq(A, y, rcond=None)[0]
                gain = gci = (np.nan, np.nan, np.nan)
                if name == "gap+disp+corr":
                    g0 = res["gap"]; gb = np.array([r2(y[ix], pred[ix], base[ix]) - r2(y[ix], g0[0][ix], g0[1][ix]) for ix in picks])
                    gain = (r2(y, pred, base) - r2(y, *g0), np.nanpercentile(gb, 2.5), np.nanpercentile(gb, 97.5))
                rows.append(dict(board=board, rule=rule, B=B, model=name, cv=cv, cv_r2=r2(y, pred, base), ci_lo=np.nanpercentile(bs, 2.5), ci_hi=np.nanpercentile(bs, 97.5),
                                 gain_vs_gap=gain[0], gain_ci_lo=gain[1], gain_ci_hi=gain[2], r2_insample=1 - ((y - A @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum(),
                                 n=len(d), n_groups=len(np.unique(groups)), n_families=k, by_construction=(rule == "mean")))
r = pd.DataFrame(rows); r.to_csv(f"{T}/predictors_within.csv", index=False); print(len(r))
print(r[(r.B == 100.0) & (r.cv == "family")].pivot_table(index=["board", "rule"], columns="model", values="cv_r2").round(2).to_string())
print(r[(r.B == 100.0) & (r.cv == "family") & (r.model == "gap+disp+corr")][["board", "rule", "gain_vs_gap", "gain_ci_lo", "gain_ci_hi"]].round(2).to_string())
