"""Theory checks.  T1: finite-sample law of split-conformal coverage (Beta) per score and family.
T4: delta-method (large-precision Gaussian) prediction of the pointwise conditional coverage of
    L2 / Aitchison / Hellinger scores for Dirichlet noise, checked against simulation with the oracle mean predictor."""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cpc.data import World
from cpc.simplex import BASE_SCORES
from cpc.conformal import conf_quantile
from cpc.predictors import SoftmaxLinear

os.makedirs("results/theory", exist_ok=True)
rng = np.random.default_rng(2024)

# ---------------- T1: Beta law ----------------
rows = []
for fam in ["dirichlet", "multinomial"]:
    w = World(fam, 5, 0, seed=0)
    Xf, Yf = w.sample(5000, rng)
    mdl = SoftmaxLinear().fit(Xf, Yf)
    Xp, Yp = w.sample(2_000_000, rng)
    Pp = mdl.predict(Xp)
    for sname in ["l2", "hell", "ait"]:
        f = BASE_SCORES[sname]
        sp = np.sort(f(Yp, Pp))
        for n in [19, 50, 100, 500]:
            alpha = 0.1
            k = int(np.ceil((n + 1) * (1 - alpha)))
            covs = []
            for _ in range(3000):
                Xc, Yc = w.sample(n, rng)  # fresh calibration set each time
                q = conf_quantile(f(Yc, mdl.predict(Xc)), alpha)
                covs.append(np.searchsorted(sp, q, side="right") / len(sp))
            covs = np.array(covs)
            beta = stats.beta(k, n + 1 - k)
            rows.append(dict(family=fam, score=sname, n=n, k=k, mean_emp=covs.mean(), mean_beta=beta.mean(),
                             sd_emp=covs.std(), sd_beta=beta.std(), q05_emp=np.quantile(covs, .05), q05_beta=beta.ppf(.05),
                             q95_emp=np.quantile(covs, .95), q95_beta=beta.ppf(.95),
                             ks=stats.kstest(covs, beta.cdf).statistic, ks_p=stats.kstest(covs, beta.cdf).pvalue))
pd.DataFrame(rows).to_csv("results/theory/t1_beta_law.csv", index=False)
print("T1 done", flush=True)


# ---------------- T4: delta-method conditional coverage ----------------
from scipy.special import digamma, polygamma


def ait_moments(mu, phi):
    a = phi * mu
    m = digamma(a) - np.log(a)
    m = m - m.mean()  # E[clr(y) - clr(mu)]
    G = np.eye(len(mu)) - 1.0 / len(mu)
    return m, G @ np.diag(polygamma(1, a)) @ G


def eig_cov(mu, kind, phi):
    """Eigenvalues of the (delta-method) covariance of the residual in the score's coordinates."""
    D = len(mu)
    if kind == "l2":
        C = (np.diag(mu) - np.outer(mu, mu)) / (phi + 1)
    elif kind == "ait":
        G = np.eye(D) - 1.0 / D
        C = G @ np.diag(1 / mu) @ G / (phi + 1)
    elif kind == "hell":
        C = (np.eye(D) - np.outer(np.sqrt(mu), np.sqrt(mu))) / (4 * (phi + 1))
    return np.clip(np.linalg.eigvalsh(C), 0, None)


def pred_cov_curve(MU, kind, phi, alpha=0.1, m=4000, r=np.random.default_rng(5)):
    if kind == "ait2":
        s2 = []
        for mu in MU:
            mm, C = ait_moments(mu, phi)
            w_, V_ = np.linalg.eigh(C)
            L = V_ * np.sqrt(np.clip(w_, 0, None))
            s2.append(((mm + r.normal(size=(m, len(mu))) @ L.T) ** 2).sum(1))
        s2 = np.stack(s2)
        q2 = np.quantile(s2.ravel(), 1 - alpha)
        return (s2 <= q2).mean(1), np.sqrt(q2)
    Z2 = r.chisquare(1, size=(m, MU.shape[1]))
    lam = np.stack([eig_cov(mu, kind, phi) for mu in MU])  # (nx, D)
    s2 = lam @ Z2.T  # (nx, m) squared score under Gaussian approx
    q2 = np.quantile(s2.ravel(), 1 - alpha)  # marginal threshold under the x-mixture
    return (s2 <= q2).mean(1), np.sqrt(q2)


rows = []
for phi in [200.0, 50.0, 20.0, 8.0]:
    w = World("dirichlet", 5, 0, seed=0, phi0=phi)
    Xs = w.sample_x(300, rng)
    MU = w.mean(Xs)
    for kind in ["l2", "ait", "ait2", "hell"]:
        f = BASE_SCORES["ait" if kind == "ait2" else kind]
        pred, _ = pred_cov_curve(MU, kind, phi)
        # simulation: marginal threshold with oracle predictor, then pointwise coverage over fresh draws
        Xm = w.sample_x(40_000, rng)
        Ym = w.sample_y(Xm, rng)
        q = conf_quantile(f(Ym, w.mean(Xm)), 0.1)
        reps = 2000
        emp = np.array([(f(w.sample_y(np.repeat(Xs[i:i + 1], reps, 0), rng), MU[i]) <= q).mean() for i in range(len(Xs))])
        rows.append(dict(phi=phi, score=kind, rmse=np.sqrt(np.mean((pred - emp) ** 2)), max_abs=np.abs(pred - emp).max(),
                         emp_min=emp.min(), emp_max=emp.max(), pred_min=pred.min(), pred_max=pred.max(),
                         emp_sd=emp.std(), pred_sd=pred.std(), corr=np.corrcoef(pred, emp)[0, 1] if pred.std() > 1e-9 else np.nan))
        pd.DataFrame({"phi": phi, "score": kind, "x_id": np.arange(len(Xs)), "pred": pred, "emp": emp,
                      "mu_max": MU.max(1), "mu_min": MU.min(1)}).to_csv(f"results/theory/t4_points_{kind}_phi{int(phi)}.csv", index=False)
        print("T4", phi, kind, flush=True)
pd.DataFrame(rows).to_csv("results/theory/t4_cond_coverage.csv", index=False)
