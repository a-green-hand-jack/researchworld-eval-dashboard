"""E5/E7 (real data): CIFAR-10H (default) or ChaosNLI (--data chaosnli) with softmax outputs of pretrained classifiers.
y = human label distribution (composition with many exact zeros), yhat = softmax(logits / T), T fitted on a separate split.
Repeated random splits: train(T) 1000 / calibration 2000 / test 7000.   Writes results/e5_rep.csv, results/e5_img.npz"""
import sys, time
import numpy as np, pandas as pd
from scipy.special import softmax
from scipy.optimize import minimize_scalar
from joblib import Parallel, delayed
from ccp.geometry import SCORES, make_aitchison, fit_mahal_ilr
from ccp.conformal import conformal_quantile
from ccp.evalkit import MassLookup

ALPHA = float(sys.argv[sys.argv.index("--alpha") + 1]) if "--alpha" in sys.argv else 0.1
DATA = sys.argv[sys.argv.index("--data") + 1] if "--data" in sys.argv else "cifar10h"
R = 20 if "--quick" in sys.argv else 100
NB = 10
if DATA == "cifar10h":
    Y = np.load("/work/data/cifar10h/probs.npy")
    N_TR, N_CAL, N_CENT = 1000, 2000, 300
    CONFIGS = [("resnet56", "T"), ("resnet56", "raw"), ("resnet20", "T"), ("vgg11_bn", "T")]
    LOGITS = lambda m: np.load(f"/work/data/logits_{m}.npy")
else:
    Y = np.load("/work/data/chaosnli/labels.npy")
    N_TR, N_CAL, N_CENT = 500, 1000, 300
    CONFIGS = [("roberta-large", "T"), ("roberta-large", "raw"), ("distilroberta", "T")]
    LOGITS = lambda m: np.load(f"/work/data/chaosnli/logits_{m}.npy")
    import os
    CONFIGS = [c for c in CONFIGS if os.path.exists(f"/work/data/chaosnli/logits_{c[0]}.npy")]
N = len(Y)
S = {k: SCORES[k] for k in ("euclid", "tv", "hellinger", "chi2", "kl")}
for d in ("1e-4", "1e-3", "1e-2", "1e-1"):
    S["aitchison_" + d] = make_aitchison(float(d))
NAMES = list(S)


def fit_T(L, idx):
    def ce(lt):
        p = softmax(L[idx] / np.exp(lt), 1)
        return -(Y[idx] * np.log(np.maximum(p, 1e-300))).sum(1).mean()
    return float(np.exp(minimize_scalar(ce, bounds=(-2, 3), method="bounded").x))


def null_worst(sizes, rng, nsim=200):
    sims = np.stack([rng.binomial(s, 1 - ALPHA, nsim) / s for s in sizes])
    return np.abs(sims - (1 - ALPHA)).max(0).mean()


def run(model, mode):
    L = LOGITS(model)
    rng0 = np.random.default_rng(123)
    perm0 = np.random.default_rng(0).permutation(N)
    tr, pool = perm0[:N_TR], perm0[N_TR:]          # fixed split: 1000 images fit T; 9000-image pool is re-split per rep
    T = fit_T(L, tr) if mode == "T" else 1.0
    P = softmax(L / T, 1)
    conf, cls = P.max(-1), P.argmax(-1)
    edges = np.quantile(conf[tr], np.linspace(0, 1, NB + 1)[1:-1])
    bconf = np.searchsorted(edges, conf, side="right")
    cent = rng0.choice(pool, N_CENT, replace=False)
    Sx = dict(S)
    for d in ("1e-3", "1e-2"):     # ellipsoidal baseline: global ilr covariance fitted on the T-fit images only
        Sx["mahal_ilr_" + d] = fit_mahal_ilr(Y[tr], P[tr], float(d))
    S_all = Sx
    Sc = {name: Sx[name](Y, P) for name in Sx}
    NAMES_ = list(Sx)
    ml = {a: MassLookup(P[cent], Sx, a=a, seed=7) for a in (1.0, 0.5)}
    cov_cnt, te_cnt, rows = {}, np.zeros(N), []
    lm_sum, lm_cnt = {}, np.zeros(N_CENT)
    for r in range(R):
        rng = np.random.default_rng([5, r])
        pp = rng.permutation(pool)
        ca, te = pp[:N_CAL], pp[N_CAL:]
        te_cnt[te] += 1
        in_te = np.isin(cent, te)
        lm_cnt += in_te
        for name in NAMES_:
            s = Sc[name]
            for meth in ("split", "mondrian_conf", "mondrian_class"):
                if meth == "split":
                    q = np.full(N, conformal_quantile(s[ca], ALPHA))
                else:
                    key = bconf if meth == "mondrian_conf" else cls
                    nb = NB if meth == "mondrian_conf" else Y.shape[1]
                    qb = np.array([conformal_quantile(s[ca][key[ca] == b], ALPHA) for b in range(nb)])
                    q = qb[key]
                covd = (s <= q)
                cov_cnt.setdefault((meth, name), np.zeros(N))[te] += covd[te]
                row = dict(model=model, mode=mode, rep=r, T=T, method=meth, score=name, cov=covd[te].mean(),
                           q_median=np.median(q[te]))
                for var, key, nb in (("conf", bconf, NB), ("class", cls, Y.shape[1])):
                    sz = np.array([(key[te] == b).sum() for b in range(nb)])
                    cs = np.array([covd[te][key[te] == b].mean() for b in range(nb)])[sz > 0]
                    sz = sz[sz > 0]
                    row[f"worst_{var}"] = np.abs(cs - (1 - ALPHA)).max()
                    row[f"min_{var}"] = cs.min()
                    row[f"null_worst_{var}"] = null_worst(sz, rng0, 100)
                idx = np.where(in_te)[0]
                for a, kname in ((1.0, "lm1"), (0.5, "lm05")):
                    m = np.array([ml[a].mass(name, int(c), q[cent[c]]) for c in idx])
                    lm = np.log(np.maximum(m, 1e-300))
                    row[kname], row[kname + "_med"] = lm.mean(), np.median(lm)
                    if a == 1.0:
                        lm_sum.setdefault((meth, name), np.zeros(N_CENT))[idx] += lm
                rows.append(row)
    img = {f"{model}_{mode}|{k[0]}|{k[1]}": v for k, v in cov_cnt.items()}
    img.update({f"{model}_{mode}|lm|{k[0]}|{k[1]}": v for k, v in lm_sum.items()})
    img[f"{model}_{mode}|lm_cnt"] = lm_cnt
    img[f"{model}_{mode}|cent"] = cent
    img[f"{model}_{mode}|te_cnt"] = te_cnt
    img[f"{model}_{mode}|conf"] = conf
    img[f"{model}_{mode}|cls"] = cls
    img[f"{model}_{mode}|bconf"] = bconf
    return rows, img


if __name__ == "__main__":
    t0 = time.time()
    out = Parallel(n_jobs=len(CONFIGS))(delayed(run)(m, md) for m, md in CONFIGS)
    df = pd.DataFrame([r for rows, _ in out for r in rows])
    suffix = ("" if DATA == "cifar10h" else "_" + DATA) + ("" if ALPHA == 0.1 else "_a%g" % ALPHA) + ("_quick" if "--quick" in sys.argv else "")
    df.to_csv(f"/work/results/e5_rep{suffix}.csv", index=False)
    img = {}
    for _, d in out:
        img.update(d)
    np.savez_compressed(f"/work/results/e5_img{suffix}.npz", **img)
    print("done", time.time() - t0)
