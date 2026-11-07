"""E4: covariate shift. Calibration x ~ N(0,I); test x ~ N(delta*w, I) (w = noise direction of the world). Unweighted split
conformal vs weighted split conformal with the exact likelihood ratio (Tibshirani et al. 2019)."""
import argparse, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cpc.data import World
from cpc.simplex import BASE_SCORES
from cpc.conformal import SigmaModel, conf_quantile
from cpc.predictors import SoftmaxLinear

SC = ["l2", "hell", "kl", "ait"]
SIG = ["l2", "l1", "hell", "kl", "ait", "linf"]


def wquant(sc, wc, wt, alpha):
    """Per-test-point weighted conformal threshold; sc calibration scores, wc cal weights, wt test weights (nt,)."""
    o = np.argsort(sc)
    s, w = sc[o], wc[o]
    cw = np.cumsum(w)
    target = (1 - alpha) * (w.sum() + wt)
    idx = np.searchsorted(cw, target, side="left")
    return np.where(idx >= len(s), np.inf, s[np.minimum(idx, len(s) - 1)])


ap = argparse.ArgumentParser()
ap.add_argument("--family"); ap.add_argument("--reps", type=int, default=100); ap.add_argument("--out")
a = ap.parse_args()
world = World(a.family, 5, 1, seed=0)
rows = []
for rep in range(a.reps):
    rng = np.random.default_rng(rep)
    Xf, Yf = world.sample(1000, rng); Xs, Ys = world.sample(500, rng); Xc, Yc = world.sample(500, rng)
    mdl = SoftmaxLinear().fit(Xf, Yf)
    Ps, Pc = mdl.predict(Xs), mdl.predict(Xc)
    S_s = {k: BASE_SCORES[k](Ys, Ps) for k in SIG}
    sig = SigmaModel(rep).fit(np.c_[Xs, Ps], np.stack([S_s[k] for k in SIG], 1))
    sgc = sig.predict(np.c_[Xc, Pc])
    for delta in [0.0, 0.5, 1.0, 1.5]:
        Xt = rng.normal(size=(2000, world.p)) + delta * world.w
        Yt = world.sample_y(Xt, rng)
        Pt = mdl.predict(Xt)
        sgt = sig.predict(np.c_[Xt, Pt])
        lr = lambda X: np.exp(delta * X @ world.w - delta ** 2 / 2)  # density ratio N(delta w, I)/N(0, I)
        wc, wt = lr(Xc), lr(Xt)
        ess = wc.sum() ** 2 / (wc ** 2).sum()
        for s in SC:
            for norm in (False, True):
                if norm and s not in SIG:
                    continue
                sc = BASE_SCORES[s](Yc, Pc); st = BASE_SCORES[s](Yt, Pt)
                if norm:
                    sc, st = sc / sgc[:, SIG.index(s)], st / sgt[:, SIG.index(s)]
                for wtd in (False, True):
                    for al in (0.1,):
                        q = wquant(sc, wc, wt, al) if wtd else np.full(len(st), conf_quantile(sc, al))
                        c = st <= q
                        rows.append(dict(rep=rep, delta=delta, method=s + ("_n" if norm else ""), weighted=int(wtd), cov10=c.mean(),
                                         ess=ess, inf_frac=float(np.mean(~np.isfinite(q))), family=a.family))
    if rep % 20 == 0: print("rep", rep, flush=True)
pd.DataFrame(rows).to_csv(a.out, index=False)
