"""CIFAR-10H experiment: predictor = CNN softmax trained on CIFAR-10 train; target = human label
proportions of the 10000 CIFAR-10 test images. Usage: python code/run_cifar10h.py [R] [nproc]
Writes results/cifar10h.csv"""
import os, sys, time
import numpy as np, pandas as pd
from scipy.special import softmax, logsumexp
from scipy.optimize import minimize_scalar
from multiprocessing import Pool
from compconf import *

ALPHA = 0.1
EPS_DEFAULT = 0.01  # ~ half a vote out of ~50 annotators
N_AUX, N_TEST = 1000, 2000
LOG = np.load("data/cifar_test_logits.npy").astype(np.float64)
H = np.load("data/cifar10h-probs.npy").astype(np.float64)
LABELS = np.load("data/cifar_test_labels.npy")
K = 10


def fit_temp(logits, Y):
    f = lambda t: -(Y * (logits / t - logsumexp(logits / t, axis=1, keepdims=True))).sum(1).mean()
    return minimize_scalar(f, bounds=(0.3, 20), method="bounded").x


def run_one(args):
    n_cal, rep = args
    rng = np.random.default_rng(np.random.SeedSequence([20261112, n_cal, rep]))
    perm = rng.permutation(10000)
    ia, ic, it = perm[:N_AUX], perm[N_AUX:N_AUX + n_cal], perm[N_AUX + 2000:N_AUX + 2000 + N_TEST]
    T = fit_temp(LOG[ia], H[ia])
    rows = []
    for variant, F_all in [("raw", softmax(LOG, axis=1)), ("ts", softmax(LOG / T, axis=1))]:
        Fa, Ya, Fc, Yc, Ft, Yt = F_all[ia], H[ia], F_all[ic], H[ic], F_all[it], H[it]
        pool = Ya
        edges = ent_edges(Fa)
        gc, gt = group_of(Fc, edges), group_of(Ft, edges)
        specs = [(s, s, EPS_DEFAULT, False) for s in ["l2", "l1", "linf", "hell", "kl", "ait", "mah", "l2n"]]
        specs += [("l2_mond", "l2", EPS_DEFAULT, True), ("ait_mond", "ait", EPS_DEFAULT, True)]
        specs += [(f"ait_eps{e:g}", "ait", e, False) for e in [1e-8, 1e-6, 1e-4, 1e-3, 1e-1]]
        for name, sname, eps, mond in specs:
            aux = fit_aux(Ya, Fa, eps)
            sc = Score(sname, K, eps, aux)
            scal = sc.paired(Yc, Fc)
            qt = mondrian_thresholds(scal, gc, gt, ALPHA) if mond else np.full(len(Ft), conf_quantile(scal, ALPHA))
            cov, sp, _ = evaluate(sc, Ft, Yt, qt, pool, None)
            row = dict(variant=variant, n_cal=n_cal, rep=rep, method=name, cov=cov.mean(), size_pool=sp.mean(),
                       q=np.mean(qt), temp=T)
            for k, (c, m) in group_summary(cov, Ft, Yt, edges, K).items():
                row[f"g_{k}_c"], row[f"g_{k}_n"] = c, m
            rows.append(row)
    return rows


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    P = softmax(LOG, axis=1)
    info = dict(acc_softmax_vs_trueclass=(P.argmax(1) == LABELS).mean(),
                acc_human_majority_vs_trueclass=(H.argmax(1) == LABELS).mean(),
                argmax_agreement_model_vs_human=(P.argmax(1) == H.argmax(1)).mean(),
                frac_Y_with_zero=(H <= 0).any(1).mean(), mean_zero_entries=(H <= 0).sum(1).mean(),
                frac_unanimous=(H.max(1) >= 1 - 1e-9).mean(), mean_entropy_H=entropy(H).mean(),
                mean_entropy_model=entropy(P).mean(), mean_L2_model_human=np.sqrt(((P - H) ** 2).sum(1)).mean())
    print(info)
    pd.Series(info).to_csv("results/cifar10h_info.csv")
    jobs = [(n, r) for n in [100, 500, 2000] for r in range(R)]
    t = time.time()
    with Pool(nproc) as p:
        res = p.map(run_one, jobs, chunksize=2)
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv("results/cifar10h.csv", index=False)
    print(df.shape, f"{time.time() - t:.0f}s")
