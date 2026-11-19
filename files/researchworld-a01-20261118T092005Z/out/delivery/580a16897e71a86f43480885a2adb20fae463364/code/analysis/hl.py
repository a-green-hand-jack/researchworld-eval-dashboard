"""H-L (EXPLORATORY, post hoc; Brief rev 4 section 7): does the deficit profile of the target against its incumbent predict price beyond the rule-specific gap?
usage: hl.py TABLES_DIR   reads price.csv; writes predictors_hl.csv.
Deficit of the target t against its own-rule incumbent l on task j, in task-sigma units: e_j = (S[l,j] - S[t,j]) / sigma_j (sigma_j = sd of task j over the board's models).
Profile features (computed on the positive part p_j = max(e_j, 0)):
  gini  : Gini coefficient of p over the m tasks;
  l50   : Lorenz curve of p at 0.5 (share of the total deficit carried by the *smaller* half of the tasks; low = concentrated deficit);
  near  : share of tasks within 1 sigma of the incumbent (e_j <= 1; includes tasks where the target is ahead).
Models for y = log depth* at a per-task cap B (points; own incumbent; positive gap and positive finite price), per rule, fitted on one board and scored on another:
  'gap' (log rule-specific gap) vs 'gap+gini', 'gap+l50', 'gap+near', 'gap+profile' (all three).
gain = R^2_heldout(model) - R^2_heldout('gap'); two variants of R^2: r2_heldout (the fitted intercept is kept) and r2_recentred (intercept re-estimated on the test board: slope transfer only).
CI of the gain: paired cluster bootstrap over the target families of the test board (fitted models fixed). H-L is retained for a (rule, B, direction) only if gain >= 0.1 and the CI excludes 0 (Brief section 7);
'loo_family' is the within-board variant (leave-one-target-family-out; both fit and test on one board); the primary summary is the model 'gap+profile', the single-feature models are reported for diagnosis (multiplicity: 5 models x rules x directions x 3 caps; nothing here is confirmatory)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from stats import r2_heldout
from lbprice.boards import load_helm, load_ollb
T = sys.argv[1]; NB = int(os.environ.get("NBOOT", 2000))
p = pd.read_csv(f"{T}/price.csv"); p = p[p.incumbent == "own"]
BM = {"helm_mmlu": load_helm, "ollb_bench": lambda: load_ollb("m6"), "ollb_sub": lambda: load_ollb("m39")}
MODELS = {"gap": ["lgap"], "gap+gini": ["lgap", "gini"], "gap+l50": ["lgap", "l50"], "gap+near": ["lgap", "near"], "gap+profile": ["lgap", "gini", "l50", "near"]}


def gini(x):
    x = np.sort(x); n = len(x); s = x.sum()
    return 0.0 if s <= 0 else float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * s))


def features(board, d):
    b = BM[board](); S = b["S"]; sig = S.std(0); ix = {n: i for i, n in enumerate(b["names"])}
    t = np.array([int(x) for x in d.target]); l = np.array([ix[x] for x in d.incumbent_id])
    e = (S[l] - S[t]) / sig; pos = np.clip(e, 0, None)
    out = d.copy(); out["gini"] = [gini(r) for r in pos]; out["near"] = (e <= 1.0).mean(1)
    out["l50"] = [np.sort(r)[: (len(r) + 1) // 2].sum() / max(r.sum(), 1e-12) for r in pos]
    out["lgap"] = np.log(out.gap.clip(lower=1e-9)); return out


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
                pred = {}
                for name, cols in MODELS.items():
                    beta = np.linalg.lstsq(design(tr, cols), tr.y.values, rcond=None)[0]; pred[name] = design(te, cols) @ beta
                y = te.y.values; fam = pd.factorize(te.family)[0]; k = fam.max() + 1
                grp = [np.flatnonzero(fam == c) for c in range(k)]; rng = np.random.default_rng(13)
                picks = [np.concatenate([grp[c] for c in rng.integers(0, k, k)]) for _ in range(NB)]
                rc = lambda yy, pp: r2_heldout(yy, pp - (pp - yy).mean())
                for name in MODELS:
                    if name == "gap": continue
                    for var, f in (("heldout", r2_heldout), ("recentred", rc)):
                        g0 = f(y, pred[name]) - f(y, pred["gap"])
                        bs = [f(y[ix], pred[name][ix]) - f(y[ix], pred["gap"][ix]) for ix in picks]
                        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
                        rows.append(dict(fit_board=fb, test_board=tb, rule=rule, B=B, model=name, r2_variant=var, r2_gap=f(y, pred["gap"]), r2_model=f(y, pred[name]), gain=g0, ci_lo=lo, ci_hi=hi,
                                         retained=bool(g0 >= 0.1 and lo > 0), n_fit=len(tr), n_test=len(te), n_clusters=k))
        # within-board check: leave-one-family-out predictions on each board (fit_board == test_board; intercept always re-estimated on the training families)
        for b_, qb in qr.groupby("board"):
            if len(qb) < 12: continue
            y = qb.y.values; fam = pd.factorize(qb.family)[0]; k = fam.max() + 1; pred = {n: np.zeros(len(qb)) for n in MODELS}
            for c in range(k):
                trm = fam != c
                for name, cols in MODELS.items():
                    beta = np.linalg.lstsq(design(qb[trm], cols), y[trm], rcond=None)[0]; pred[name][~trm] = design(qb[~trm], cols) @ beta
            grp = [np.flatnonzero(fam == c) for c in range(k)]; rng = np.random.default_rng(13)
            picks = [np.concatenate([grp[c] for c in rng.integers(0, k, k)]) for _ in range(NB)]
            for name in MODELS:
                if name == "gap": continue
                g0 = r2_heldout(y, pred[name]) - r2_heldout(y, pred["gap"]); bs = [r2_heldout(y[ix], pred[name][ix]) - r2_heldout(y[ix], pred["gap"][ix]) for ix in picks]
                lo, hi = np.nanpercentile(bs, [2.5, 97.5])
                rows.append(dict(fit_board=b_, test_board=b_, rule=rule, B=B, model=name, r2_variant="loo_family", r2_gap=r2_heldout(y, pred["gap"]), r2_model=r2_heldout(y, pred[name]), gain=g0, ci_lo=lo, ci_hi=hi,
                                 retained=bool(g0 >= 0.1 and lo > 0), n_fit=len(qb), n_test=len(qb), n_clusters=k))
r = pd.DataFrame(rows); r.to_csv(f"{T}/predictors_hl.csv", index=False); print(len(r))
for var in ("heldout", "recentred", "loo_family"):
    s = r[(r.model == "gap+profile") & (r.r2_variant == var)]
    print(var, "retained", int(s.retained.sum()), "of", len(s), "; median gain", round(s.gain.median(), 3))
    print(s[s.B == 100.0].pivot_table(index=["fit_board", "test_board"], columns="rule", values="gain").round(2).to_string())
    print(s[s.retained][["fit_board", "test_board", "rule", "B", "r2_gap", "r2_model", "gain", "ci_lo"]].round(2).to_string())
