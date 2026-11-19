"""E4 / R3: predictors of log price within a rule, fitted on one board and evaluated on another (held out).
usage: predictors.py TABLES_DIR   reads price.csv; writes predictors.csv (contract) in TABLES_DIR.
y = log depth_star at a fixed per-task cap B (points; own-leader incumbent; targets with a positive gap and positive price).
models: 'rank' (log initial official rank), 'gap' (log rule-specific gap), 'gap+disp+corr' (+ target score dispersion across tasks, leader dispersion, corr of the target's and leader's task profiles).
r2_heldout: R^2 of the fitted model's predictions on the other board with its intercept as fitted; r2_recentred: with the intercept re-estimated on the test board (slope transfer only).
CI: cluster bootstrap over the target families of the test board (fitted model fixed)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from stats import r2_heldout
from features import features, BM
T = sys.argv[1]; NB = int(os.environ.get("NBOOT", 2000))
p = pd.read_csv(f"{T}/price.csv"); p = p[p.incumbent == "own"]
MODELS = {"rank": ["lrank"], "gap": ["lgap"], "gap+disp+corr": ["lgap", "tdisp", "ldisp", "corr"]}


def design(d, cols): return np.column_stack([np.ones(len(d))] + [d[c].values for c in cols])


rows = []
for B in (10.0, 20.0, 100.0):
    q = p[(p.B == B) & (p.rule.isin(["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]))]
    q = q[(q.gap > 0) & (q.depth_star > 0) & np.isfinite(q.depth_star)].copy()
    q = pd.concat([features(b, g) for b, g in q.groupby("board")]); q["y"] = np.log(q.depth_star)
    for rule, qr in q.groupby("rule"):
        for fb in qr.board.unique():
            for tb in qr.board.unique():
                if fb == tb: continue
                tr, te = qr[qr.board == fb], qr[qr.board == tb]
                if len(tr) < 12 or len(te) < 8: continue
                for name, cols in MODELS.items():
                    beta = np.linalg.lstsq(design(tr, cols), tr.y.values, rcond=None)[0]
                    pred = design(te, cols) @ beta
                    r2 = r2_heldout(te.y, pred); r2c = r2_heldout(te.y, pred - (pred - te.y.values).mean())
                    fam = pd.factorize(te.family)[0]; k = fam.max() + 1; rng = np.random.default_rng(11); grp = [np.flatnonzero(fam == c) for c in range(k)]
                    bs = []
                    for _ in range(NB):
                        ix = np.concatenate([grp[c] for c in rng.integers(0, k, k)]); bs.append(r2_heldout(te.y.values[ix], pred[ix]))
                    rows.append(dict(fit_board=fb, test_board=tb, rule=rule, model=name, B=B, r2_heldout=r2, ci_lo=np.nanpercentile(bs, 2.5), ci_hi=np.nanpercentile(bs, 97.5),
                                     r2_recentred=r2c, n_fit=len(tr), n_test=len(te), n_clusters=k))
r = pd.DataFrame(rows); r.to_csv(f"{T}/predictors.csv", index=False); print(len(r))
print(r[r.B == 100.0].pivot_table(index=["fit_board", "test_board", "rule"], columns="model", values="r2_heldout").round(2).to_string())
