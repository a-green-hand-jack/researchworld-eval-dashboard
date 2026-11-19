"""R3 across boards on normalised quantities (reported variants of predictors.py; the pre-registered test is the raw-unit one in predictors.py).
usage: predictors_norm.py TABLES_DIR   reads price.csv; writes predictors_norm.csv in TABLES_DIR.
Same targets, incumbent ('own'), cap (B = ceilings), clusters and bootstrap as predictors.py; the held-out R^2 is that of the log price in the units of the variant.
variants (y ~ x, fitted on one board, evaluated on another):
  raw        log depth ~ log gap                                        (pre-registered; the same as predictors.py, model 'gap')
  per_task   log(depth/m) ~ log gap                                     (price per task, gap in the rule's own points or counts)
  per_task_sigma log(depth/(m*sbar)) ~ log(gap/sbar)                    (score rules only: sbar = mean over tasks of the board's task sd; for zmean the gap is already in sd units, so x = log gap)
  m_term     log depth ~ log gap + log m, fitted on the two other boards, evaluated on the third (leave-one-board-out; m = 57, 6, 39)
r2_recentred: intercept re-estimated on the test board (slope transfer only)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from stats import r2_heldout
from features import features, BM
T = sys.argv[1]; NB = int(os.environ.get("NBOOT", 2000))
RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]; SCORE = {"mean", "zmean", "median", "min"}
p = pd.read_csv(f"{T}/price.csv"); p = p[(p.incumbent == "own") & (p.B == 100.0) & p.rule.isin(RULES)]
p = p[(p.gap > 0) & (p.depth_star > 0) & np.isfinite(p.depth_star)].copy()
p = pd.concat([features(b, g) for b, g in p.groupby("board")])
SBAR = {b: float(BM[b]()["S"].std(axis=0).mean()) for b in p.board.unique()}
p["sbar"] = p.board.map(SBAR); p["lm"] = np.log(p.m.astype(float))
ly = np.log(p.depth_star)
p["y_raw"] = ly; p["x_raw"] = p.lgap
p["y_pt"] = ly - p.lm; p["x_pt"] = p.lgap
p["y_ps"] = ly - p.lm - np.log(p.sbar); p["x_ps"] = np.where(p.rule == "zmean", p.lgap, p.lgap - np.log(p.sbar))
VAR = {"raw": ("y_raw", ["x_raw"]), "per_task": ("y_pt", ["x_pt"]), "per_task_sigma": ("y_ps", ["x_ps"])}


def design(d, cols): return np.column_stack([np.ones(len(d))] + [d[c].values for c in cols])


def boot(te, y, pred):
    fam = pd.factorize(te.family)[0]; k = fam.max() + 1; rng = np.random.default_rng(11); grp = [np.flatnonzero(fam == c) for c in range(k)]; bs = []
    for _ in range(NB):
        ix = np.concatenate([grp[c] for c in rng.integers(0, k, k)]); bs.append(r2_heldout(y[ix], pred[ix]))
    return np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5), k


rows = []
for rule, qr in p.groupby("rule"):
    boards = list(qr.board.unique())
    for vname, (yc, xc) in VAR.items():
        if vname == "per_task_sigma" and rule not in SCORE: continue
        for fb in boards:
            for tb in boards:
                if fb == tb: continue
                tr, te = qr[qr.board == fb], qr[qr.board == tb]
                if len(tr) < 12 or len(te) < 8: continue
                beta = np.linalg.lstsq(design(tr, xc), tr[yc].values, rcond=None)[0]
                pred = design(te, xc) @ beta; y = te[yc].values
                lo, hi, k = boot(te, y, pred)
                rows.append(dict(variant=vname, fit_board=fb, test_board=tb, rule=rule, r2_heldout=r2_heldout(y, pred), ci_lo=lo, ci_hi=hi, r2_recentred=r2_heldout(y, pred - (pred - y).mean()),
                                 slope=beta[1], n_fit=len(tr), n_test=len(te), n_clusters=k))
    if len(boards) == 3:
        for tb in boards:
            tr, te = qr[qr.board != tb], qr[qr.board == tb]
            cols = ["x_raw", "lm"]; beta = np.linalg.lstsq(design(tr, cols), tr.y_raw.values, rcond=None)[0]
            pred = design(te, cols) @ beta; y = te.y_raw.values; lo, hi, k = boot(te, y, pred)
            rows.append(dict(variant="m_term", fit_board="other two", test_board=tb, rule=rule, r2_heldout=r2_heldout(y, pred), ci_lo=lo, ci_hi=hi, r2_recentred=r2_heldout(y, pred - (pred - y).mean()),
                             slope=beta[1], n_fit=len(tr), n_test=len(te), n_clusters=k))
r = pd.DataFrame(rows); r.to_csv(f"{T}/predictors_norm.csv", index=False)
pd.set_option("display.width", 250)
print(r.pivot_table(index=["rule", "fit_board", "test_board"], columns="variant", values="r2_heldout").round(2).to_string())
print(r.groupby(["variant", "rule"]).agg(worst=("r2_heldout", "min"), best=("r2_heldout", "max"), worst_lo=("ci_lo", "min"), best_hi=("ci_hi", "max"), rec_worst=("r2_recentred", "min")).round(2).to_string())
