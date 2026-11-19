"""Retrain standard: sensitivity to the subsample fraction, and the estimator-error part of the retrain disagreement.

usage: python3 analysis/retrain_sensitivity.py [raw_dir] [out_dir]
retrain stages: `retrain` (80% subsamples), `retrain_f50`, `retrain_f95` (K = 5 retrains each, same seeds / subsample seeds 500+k, model seeds 100+k).
Per cell, fraction and k in {1, 3, 5}: share of retrain PAIRS (K(K-1)/2 = 10 per instance) whose top-k sets are identical ('pair_match'), mean Jaccard, mean relative
L2 distance; n_pairs = instances x pairs.  95% CI: instance-cluster bootstrap (1000 resamples; the pairs of an instance are resampled together; the K = 5 retrains
are fixed, so the interval does not cover the choice of the retrains).  For d > 16 (German) the retrain explanations are single Kernel runs at 10000 coalitions;
`retrain_rep` explains the same 80% retrained models again with other Kernel seeds: its row (subsample = '80% (same model, second Kernel seed)')
gives the share of (retrain, instance) with identical top-k sets of the two explanations of the SAME model, i.e. pure estimator error, to be read
against the 80% retrain pair_match, which is the model-induced disagreement observed through that estimator.
Writes tables/retrain_sensitivity.csv.
"""
import glob, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rng = np.random.RandomState(21)
res = []


def boot(x):
    ix = rng.randint(0, len(x), (1000, len(x)))
    b = x[ix].mean(1)
    return float(np.quantile(b, .025)), float(np.quantile(b, .975))


for fr in sorted(glob.glob(f"{raw}/*__retrain.npz")):
    cell = os.path.basename(fr).rsplit("__", 1)[0]; ds, model = cell.split("__")
    if ds.endswith("_logit"):
        continue
    variants = {"80%": fr, "50%": f"{raw}/{cell}__retrain_f50.npz", "95%": f"{raw}/{cell}__retrain_f95.npz"}
    for name, f in variants.items():
        if not os.path.exists(f):
            continue
        z = np.load(f); P = z["phi"]; K, N, d = P.shape
        nr2 = np.linalg.norm(P, axis=2)
        iu = np.triu_indices(K, 1)
        for k in (1, 3, 5):
            if k >= d:
                continue
            pm = np.array([M.pairwise_set_match(M.topk_ind(P[:, i], k), k) for i in range(N)])
            dist = np.array([np.mean(np.linalg.norm(P[iu[0], i] - P[iu[1], i], axis=1) / np.sqrt(0.5 * (nr2[iu[0], i] ** 2 + nr2[iu[1], i] ** 2))) for i in range(N)])
            lo, hi = boot(pm[:, 0])
            res.append(dict(dataset=ds, model=model, d=d, subsample=name, k=k, K=K, n_inst=N, n_pairs=N * len(iu[0]), pair_match=pm[:, 0].mean(), pair_match_lo=lo,
                            pair_match_hi=hi, pair_jaccard=pm[:, 1].mean(), pair_reldist=dist.mean(), mean_test_auc=float(np.mean(z["auc"]))))
    frep = f"{raw}/{cell}__retrain_rep.npz"
    if os.path.exists(frep):
        A, B = np.load(fr)["phi"], np.load(frep)["phi"]; K, N, d = A.shape
        for k in (1, 3, 5):
            m = np.array([[(M.topk_ind(A[j, i], k) == M.topk_ind(B[j, i], k)).all() for j in range(K)] for i in range(N)], float).mean(1)
            lo, hi = boot(m)
            res.append(dict(dataset=ds, model=model, d=d, subsample="80% (same model, second Kernel seed)", k=k, K=K, n_inst=N, n_pairs=N * K,
                            pair_match=m.mean(), pair_match_lo=lo, pair_match_hi=hi, pair_jaccard=np.nan,
                            pair_reldist=float(np.mean(np.linalg.norm(A - B, axis=2) / np.sqrt(0.5 * (np.linalg.norm(A, axis=2) ** 2 + np.linalg.norm(B, axis=2) ** 2)))),
                            mean_test_auc=np.nan))
pd.DataFrame(res).to_csv(f"{out}/retrain_sensitivity.csv", index=False)
print(len(res), "rows")
