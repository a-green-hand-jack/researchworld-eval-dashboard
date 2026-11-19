"""CIFAR-10 / CIFAR-10H experiment. Usage: python code/exp_cifar.py [REPS] [NPROC] [LOGITS_PATTERN] [OUT_CSV]
Predictor: small CNN trained on CIFAR-10 train with hard labels (code/cifar_train.py, 2 seeds), logits on the 10k test images.
Compositional target: CIFAR-10H human label distribution (Peterson et al. 2019; ~50 annotators/image; 10-dim simplex vectors).
Per (seed, rep): random split of the 10k test images into tune (1000: temperature + sigma-hat) and a 9000-image pool.
Settings:
  iid   - calibration = first n_cal of a random permutation of the pool; eval = other pool images (exchangeable)
  soft  - covariate shift: pool images enter the calibration set independently with prob proportional to exp(GAMMA*u),
          u = within-pool confidence rank in [0,1]  (cal over-represents confident images); eval ~ uniform on the pool.
          Test/cal likelihood ratio w(x) = exp(-GAMMA*u(x)) is known => weighted conformal (Tibshirani et al. 2019) applies.
  hard  - cal drawn only from the 50% most confident pool images, eval from the rest (disjoint supports; stress test)
Methods: plain, norm (locally weighted by sigma-hat), mond (Mondrian over 5 confidence bins), wplain (weighted; soft only),
         wmond (not run).
Writes OUT_CSV (default results/cifar_raw.csv).
"""
import sys, time, numpy as np, pandas as pd
from multiprocessing import Pool
from scipy.special import softmax
from scipy.optimize import minimize_scalar
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import cp
from exp_synth import pair_scores

ALPHA = 0.1; NB = 5; GAMMA = 3.0
SCORES = ["l2", "l1", "linf", "hell", "aitch", "aitch@0.001", "aitch@0.1", "kl"]
NCALS = [100, 500, 2000]
LOGITS = sys.argv[3] if len(sys.argv) > 3 else "results/cifar_logits_seed{seed}.npy"
H = np.load("data/cifar10h-probs.npy").astype(np.float64)
YHARD = np.load("data/cifar10_test.npz")["y"]
ent = lambda P: -(P * np.log(np.maximum(P, 1e-12))).sum(1)
H_ent = ent(H)
feats = lambda P: np.stack([P.max(1), ent(P), np.sort(P, 1)[:, -1] - np.sort(P, 1)[:, -2]], 1)


def wquantile(s_cal, w_cal, w_test, alpha):
    """Weighted conformal quantile for each test weight: smallest s with sum_{s_i<=s} w_i >= (1-alpha)(sum w + w_test)."""
    o = np.argsort(s_cal); ss = s_cal[o]; cw = np.cumsum(w_cal[o]); tot = cw[-1]
    target = (1 - alpha) * (tot + w_test)
    idx = np.searchsorted(cw, target, side="left")
    return np.where(idx < len(ss), ss[np.minimum(idx, len(ss) - 1)], np.inf)


def one(args):
    seed, rep = args
    L = np.load(LOGITS.format(seed=seed)).astype(np.float64)
    acc = (L.argmax(1) == YHARD).mean()
    rng = np.random.default_rng([777, seed, rep])
    perm = rng.permutation(10000); tune, pool = perm[:1000], perm[1000:]
    nll = lambda T: -(H[tune] * np.log(np.maximum(softmax(L[tune] / T, 1), 1e-12))).sum(1).mean()
    T = minimize_scalar(nll, bounds=(0.2, 5), method="bounded").x
    P = softmax(L / T, axis=1); F = feats(P); conf = P.max(1)
    edges = np.quantile(conf[tune], np.linspace(0, 1, NB + 1)[1:-1]); grp = np.searchsorted(edges, conf, side="right")
    u = np.empty(10000); u[pool] = (np.argsort(np.argsort(conf[pool])) + 0.5) / len(pool)
    rows = []
    for setting in ["iid", "soft", "hard"]:
        for ncal in NCALS:
            if setting == "iid":
                cal, ev_pool = pool[:ncal], pool[ncal:]
            elif setting == "soft":
                pi = np.exp(GAMMA * (u[pool] - 1.0)); sel = rng.random(len(pool)) < pi * (3.0 * ncal / pi.sum())
                cs = pool[sel]; cs = cs[rng.permutation(len(cs))]
                if len(cs) < ncal: continue
                cal = cs[:ncal]; ev_pool = np.setdiff1d(pool, cal)
            else:
                med = np.median(conf[pool]); hi = pool[conf[pool] >= med]; cal = hi[:ncal]; ev_pool = pool[conf[pool] < med]
            ev, ref = ev_pool[:min(3000, len(ev_pool) - 500)], ev_pool[-500:]
            cb = cp.quantile_bins(conf[ev], NB); eb = cp.quantile_bins(H_ent[ev], NB)
            w_cal, w_ev = np.exp(-GAMMA * u[cal]), np.exp(-GAMMA * u[ev])
            for sc in SCORES:
                f = cp.make_score(sc); s_all = f(H, P)
                sig = cp.fit_logscale(F[tune], s_all[tune]); sg_cal, sg_ev = sig(F[cal]), sig(F[ev])
                M = pair_scores(f, P[ev], H[ref])
                for meth in ["plain", "norm", "mond", "wplain"]:
                    if meth == "wplain" and setting != "soft": continue
                    den = np.ones(len(ev))
                    if meth == "plain": q = np.full(len(ev), cp.conf_quantile(s_all[cal], ALPHA))
                    elif meth == "norm": q = np.full(len(ev), cp.conf_quantile(s_all[cal] / sg_cal, ALPHA)); den = sg_ev
                    elif meth == "mond": q = cp.mondrian_quantiles(s_all[cal], grp[cal], grp[ev], ALPHA)
                    else: q = wquantile(s_all[cal], w_cal, w_ev, ALPHA)
                    covd = s_all[ev] / den <= q
                    mass = (M / den[:, None] <= q[:, None]).mean()
                    bc = cp.slice_cov(covd, cb, NB); be = cp.slice_cov(covd, eb, NB)
                    fin = np.isfinite(q)
                    rows.append(dict(seed=seed, rep=rep, setting=setting, ncal=ncal, score=sc, method=meth, T=T, acc=acc,
                                     cov=covd.mean(), mass=mass, inf_frac=1 - fin.mean(),
                                     mass_fin=(M[fin] / den[fin, None] <= q[fin, None]).mean() if fin.any() else np.nan,
                                     wsc_conf=bc.min(), wsc_ent=be.min(),
                                     maxdev_conf=np.abs(bc - 1 + ALPHA).max(), maxdev_ent=np.abs(be - 1 + ALPHA).max(),
                                     radius=np.median(q[fin]) if fin.any() else np.nan))
    return rows


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    out = sys.argv[4] if len(sys.argv) > 4 else "results/cifar_raw.csv"
    seeds = [0, 1] if "seed{seed}" in LOGITS else [0]
    jobs = [(s, r) for s in seeds for r in range(reps)]
    t0 = time.time(); res = []
    with Pool(nproc) as p:
        for i, rr in enumerate(p.imap_unordered(one, jobs)):
            res += rr
            if i % 5 == 0: print(i, len(jobs), f"{time.time()-t0:.0f}s", flush=True)
    pd.DataFrame(res).to_csv(out, index=False); print("done", time.time() - t0)
