"""CIFAR-10 / CIFAR-10H experiment. Usage: python code/exp_cifar.py [REPS]
Predictor: small CNN trained on CIFAR-10 train with hard labels (code/cifar_train.py, 2 seeds), logits on the 10k test images.
Compositional target: CIFAR-10H human label distribution (Peterson et al. 2019, ~50 annotators/image, 10-dim simplex vectors).
Per rep: random split of the 10k test images into tune (1000: temperature + sigma-hat) / cal (n_cal) / eval (rest, 3000 max) / ref (500).
Settings:  iid   - cal and eval exchangeable (random split)
           shift - cal drawn only from the 50% most-confident images (by predictor), eval from the rest (covariate shift)
Writes scratch/cifar_fake.csv
"""
import sys, time, numpy as np, pandas as pd
from scipy.special import softmax
from scipy.optimize import minimize_scalar
sys.path.insert(0, "code")
import cp
from exp_synth import pair_scores

ALPHA = 0.1; NB = 5
SCORES = ["l2", "l1", "linf", "hell", "aitch", "aitch@0.001", "aitch@0.1", "kl"]
reps = int(sys.argv[1]) if len(sys.argv) > 1 else 50
H = np.load("data/cifar10h-probs.npy").astype(np.float64)
ent = lambda P: -(P * np.log(np.maximum(P, 1e-12))).sum(1)
H_ent = ent(H)
feats = lambda P: np.stack([P.max(1), ent(P), np.sort(P, 1)[:, -1] - np.sort(P, 1)[:, -2]], 1)
rows = []; t0 = time.time()
for seed in [0]:
    L = np.load(f"scratch/fake.npy").astype(np.float64)
    acc = (L.argmax(1) == np.load("data/cifar10_test.npz")["y"]).mean()
    print("seed", seed, "acc", acc, flush=True)
    for rep in range(reps):
        rng = np.random.default_rng([777, seed, rep])
        perm = rng.permutation(10000)
        tune, rest = perm[:1000], perm[1000:]
        # temperature on tune split: NLL against human soft labels
        nll = lambda T: -(H[tune] * np.log(np.maximum(softmax(L[tune] / T, 1), 1e-12))).sum(1).mean()
        T = minimize_scalar(nll, bounds=(0.2, 5), method="bounded").x
        P = softmax(L / T, axis=1)
        F = feats(P)
        for setting in ["iid", "shift"]:
            for ncal in [100, 500, 2000]:
                if setting == "iid":
                    cal = rest[:ncal]; pool = rest[ncal:]
                else:
                    conf_rest = P[rest].max(1); med = np.median(conf_rest)
                    hi = rest[conf_rest >= med]; lo = rest[conf_rest < med]
                    cal = hi[:ncal]; pool = lo
                ev, ref = pool[:min(3000, len(pool) - 500)], pool[-500:]
                edges = np.quantile(P[tune].max(1), np.linspace(0, 1, NB + 1)[1:-1])
                grp = np.searchsorted(edges, P.max(1), side="right")
                cb = cp.quantile_bins(P[ev].max(1), NB); eb = cp.quantile_bins(H_ent[ev], NB)
                for sc in SCORES:
                    f = cp.make_score(sc)
                    s_all = f(H, P)
                    sig = cp.fit_logscale(F[tune], s_all[tune])
                    sg_cal, sg_ev = sig(F[cal]), sig(F[ev])
                    M = pair_scores(f, P[ev], H[ref])
                    for meth in ["plain", "norm", "mond"]:
                        if meth == "plain": q = np.full(len(ev), cp.conf_quantile(s_all[cal], ALPHA)); den = np.ones(len(ev))
                        elif meth == "norm": q = np.full(len(ev), cp.conf_quantile(s_all[cal] / sg_cal, ALPHA)); den = sg_ev
                        else: q = cp.mondrian_quantiles(s_all[cal], grp[cal], grp[ev], ALPHA); den = np.ones(len(ev))
                        covd = s_all[ev] / den <= q
                        mass = (M / den[:, None] <= q[:, None]).mean()
                        bc = cp.slice_cov(covd, cb, NB); be = cp.slice_cov(covd, eb, NB)
                        rows.append(dict(seed=seed, rep=rep, setting=setting, ncal=ncal, score=sc, method=meth, T=T, acc=acc,
                                         cov=covd.mean(), mass=mass, wsc_conf=bc.min(), wsc_ent=be.min(),
                                         maxdev_conf=np.abs(bc - 1 + ALPHA).max(), maxdev_ent=np.abs(be - 1 + ALPHA).max(),
                                         radius=np.median(q)))
        if rep % 10 == 0: print(seed, rep, f"{time.time()-t0:.0f}s", flush=True)
pd.DataFrame(rows).to_csv("scratch/cifar_fake.csv", index=False)
print("done")
