"""E5b: covariate shift on CIFAR-10H.  Calibration images are drawn with probability proportional to exp(gamma * u),
u = confidence rank of the classifier (so calibration over-represents easy images); test images are uniform.
Compares naive split CP, weighted CP with known / estimated weights (Tibshirani et al. 2019) and Mondrian-by-confidence.
Writes results/e5b_shift.csv"""
import numpy as np, pandas as pd
from scipy.special import softmax
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from joblib import Parallel, delayed
from ccp.geometry import SCORES
from ccp.conformal import conformal_quantile

ALPHA, N_CAL, NB, R = 0.1, 1500, 10, 200
Y = np.load("/work/data/cifar10h/probs.npy")
L = np.load("/work/data/logits_resnet56.npy")
N = len(Y)
perm0 = np.random.default_rng(0).permutation(N)
tr, pool = perm0[:1000], perm0[1000:]


def fit_T():
    def ce(lt):
        p = softmax(L[tr] / np.exp(lt), 1)
        return -(Y[tr] * np.log(np.maximum(p, 1e-300))).sum(1).mean()
    return float(np.exp(minimize_scalar(ce, bounds=(-2, 3), method="bounded").x))


T = fit_T()
P = softmax(L / T, 1)
conf = P.max(1)
ent = -(P * np.log(np.maximum(P, 1e-12))).sum(1)
rank_u = np.zeros(N)
rank_u[pool] = np.argsort(np.argsort(conf[pool])) / (len(pool) - 1)
edges = np.quantile(conf[tr], np.linspace(0, 1, NB + 1)[1:-1])
bconf = np.searchsorted(edges, conf, side="right")
SC = {k: SCORES[k](Y, P) for k in ("euclid", "chi2", "kl")}
feats = np.stack([np.log(1 - conf + 1e-6), np.log(ent + 1e-6), rank_u], 1)  # rank_u is a deterministic function of conf


def weighted_thresholds(s_cal, w_cal, w_test):
    o = np.argsort(s_cal)
    s, cw = s_cal[o], np.cumsum(w_cal[o])
    idx = np.searchsorted(cw, (1 - ALPHA) * (cw[-1] + w_test), side="left")
    return np.where(idx < len(s), s[np.minimum(idx, len(s) - 1)], np.inf)


def one(gamma, r):
    rng = np.random.default_rng([8, int(gamma * 10), r])
    pp = rng.permutation(pool)
    cpool, te = pp[:4500], pp[4500:]
    pi = np.exp(gamma * rank_u[cpool]); pi /= pi.sum()
    ca = rng.choice(cpool, N_CAL, replace=False, p=pi)
    pi_all = np.exp(gamma * rank_u)
    w_known_cal, w_known_te = 1.0 / pi_all[ca], 1.0 / pi_all[te]
    # estimated weights: logistic regression calibration-vs-test (test labels are not used)
    Xd = np.concatenate([feats[ca], feats[te]]); yd = np.r_[np.zeros(len(ca)), np.ones(len(te))]
    clf = LogisticRegression(C=10.0, max_iter=500).fit(Xd, yd)
    def wfun(idx):
        p = np.clip(clf.predict_proba(feats[idx])[:, 1], 1e-3, 1 - 1e-3)
        return p / (1 - p)
    w_est_cal, w_est_te = wfun(ca), wfun(te)
    rows = []
    for name, s in SC.items():
        meths = {}
        q = conformal_quantile(s[ca], ALPHA)
        meths["split"] = np.full(len(te), q)
        qb = np.array([conformal_quantile(s[ca][bconf[ca] == b], ALPHA) for b in range(NB)])
        meths["mondrian_conf"] = qb[bconf[te]]
        meths["weighted_known"] = weighted_thresholds(s[ca], w_known_cal, w_known_te)
        meths["weighted_est"] = weighted_thresholds(s[ca], w_est_cal, w_est_te)
        for m, qq in meths.items():
            cov = s[te] <= qq
            hi = bconf[te] >= NB // 2
            rows.append(dict(gamma=gamma, rep=r, score=name, method=m, cov=cov.mean(), cov_low_conf_half=cov[~hi].mean(),
                             cov_high_conf_half=cov[hi].mean(), ess=(w_known_cal.sum() ** 2 / (w_known_cal ** 2).sum())))
    return rows


if __name__ == "__main__":
    out = Parallel(n_jobs=8)(delayed(one)(g, r) for g in (0.0, 1.0, 2.0, 3.0, 4.0) for r in range(R))
    df = pd.DataFrame([x for rows in out for x in rows])
    df.to_csv("/work/results/e5b_shift.csv", index=False)
    pd.set_option("display.width", 200)
    print(df.groupby(["score", "gamma", "method"])[["cov", "cov_low_conf_half", "cov_high_conf_half"]].mean().round(3).loc["chi2"].unstack("method"))
