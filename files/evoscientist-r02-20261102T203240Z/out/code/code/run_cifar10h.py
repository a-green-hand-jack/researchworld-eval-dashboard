"""Real-data experiment: target = CIFAR-10H human label distribution (10-dim composition, ~80% exact zeros),
predicted composition = softmax output of a CNN trained on CIFAR-10 train.   usage: python code/run_cifar10h.py [R]
Writes results/cifar10h.csv"""
import sys, time
import numpy as np, pandas as pd
from scipy.special import softmax
from joblib import Parallel, delayed
from cpcomp import *

MODELS = ["resnet20", "rf", "lin"]
R = int(sys.argv[1]) if len(sys.argv) > 1 else 300
Y = np.load("data/c10h.npy").astype(float)
Y = Y / Y.sum(1, keepdims=True)
H = {k: softmax(np.load(f"data/cifar_logits_{k}.npy").astype(float), 1) for k in MODELS}
H = {k: np.maximum(v, 1e-12) / np.maximum(v, 1e-12).sum(1, keepdims=True) for k, v in H.items()}
N_AUX, N_CAL_POOL, N_TE = 2000, 4000, 4000
NCALS = [100, 500, 2000]
EXTRA = (1e-4, 1e-2, 1e-1)


def rep_job(model, rep):
    rng = np.random.default_rng([20261103, MODELS.index(model), rep])
    perm = rng.permutation(len(Y))
    ia, ic, it = perm[:N_AUX], perm[N_AUX:N_AUX + N_CAL_POOL], perm[N_AUX + N_CAL_POOL:N_AUX + N_CAL_POOL + N_TE]
    h, y = H[model], Y
    Z = hfeats(h)
    rows = []
    scores = make_scores(ALL_SCORES) + [Aitchison(d) for d in EXTRA]
    for sc in scores:
        sc.fit(h[ia], y[ia], Z[ia])
        s_all = sc(h[ic], y[ic], Z[ic]); g_all = sc.group(h[ic], Z[ic])
        for n in NCALS:
            for k, alpha in enumerate([0.1, 0.05, 0.2]):
                q = calibrate(sc, s_all[:n], g_all[:n], alpha)
                m = evaluate(sc, q, h[it], y[it], Z[it], rng, alpha, full=(k == 0))
                m.update(model=model, n_cal=n, alpha=alpha, rep=rep, score=sc.name)
                rows.append(m)
    return rows


if __name__ == "__main__":
    t0 = time.time()
    res = Parallel(n_jobs=36)(delayed(rep_job)(m, r) for m in MODELS for r in range(R))
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv("results/cifar10h.csv", index=False)
    print(df.shape, f"{time.time()-t0:.0f}s")
    for m in MODELS:
        print(m, "argmax-vs-human-mode agreement", (H[m].argmax(1) == Y.argmax(1)).mean(),
              "mean L2", np.sqrt(((H[m] - Y) ** 2).sum(1)).mean())
