"""Width and accuracy of the conditional / hybrid winner inference as a function of the standardised lead (x_k - V-)/se_k of the winner over the
runner-up (the information the selection event leaves: with a small lead the truncation set [V-, V+] starts at x_k and the conditional distribution
carries almost no information about theta_k). Known Sigma, exact Gaussian draws, so any behaviour is that of the method, not of Sigma-estimation or discreteness.
usage: validate_cond_lead.py OUT_CSV     cases: reference cell (tau .01, K 16, n 200); small-lead-free case: one clearly better config (outlier +5 pp, K 16, n 500)."""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from lib import winner_truncation, cond_ci, hybrid_ci, hybrid_median
from synth import make_pool
rng = np.random.default_rng(5); rows = []
def case(name, K, tau, n, outlier=0.0, R=6000):
    Y = make_pool(K, 20000, m=.3, tau=tau, rho=.5, seed=1, outlier=outlier); th = Y.mean(1); Sig = np.cov(Y.astype(float)) / n; L = np.linalg.cholesky(Sig); sd = np.sqrt(np.diag(Sig))
    w, V = np.linalg.eigh(Sig / np.outer(sd, sd)); Lc = V * np.sqrt(np.clip(w, 0, None)); cb = float(np.quantile(np.abs(rng.standard_normal((4000, K)) @ Lc.T).max(1), .995)); out = []
    for _ in range(R):
        x = th + L @ rng.standard_normal(K); k = int(np.argmax(x)); Vm, Vp, sk = winner_truncation(x, Sig, k); lead = (x[k] - Vm) / sk
        if _ < 2500:
            e, lo, hi = cond_ci(x[k], sk, Vm, Vp); hl, hh = hybrid_ci(x[k], sk, Vm, Vp, cb); hm = hybrid_median(x[k], sk, Vm, Vp, cb)
            out.append((lead, e - th[k], lo <= th[k] <= hi, hi - lo, hm - th[k], hl <= th[k] <= hh, hh - hl, x[k] - th[k], int(k == int(np.argmax(th)))))
    d = pd.DataFrame(out, columns=["lead", "cond_err", "cond_cov", "cond_w", "hyb_err", "hyb_cov", "hyb_w", "naive_err", "top_is_truly_best"])
    d["bin"] = pd.cut(d.lead, [0, .25, .5, 1, 2, 4, np.inf], right=False)
    g = d.groupby("bin", observed=True).agg(n=("lead", "size"), cond_cov=("cond_cov", "mean"), cond_width_median=("cond_w", "median"), cond_width_mean=("cond_w", "mean"), cond_err_median=("cond_err", "median"),
                                            cond_err_mean=("cond_err", "mean"), hyb_cov=("hyb_cov", "mean"), hyb_width_mean=("hyb_w", "mean"), hyb_err_mean=("hyb_err", "mean"), naive_err_mean=("naive_err", "mean")).reset_index()
    g.insert(0, "case", name); g["share"] = g.n / len(d); g["winner_is_truly_best"] = d.groupby("bin", observed=True).top_is_truly_best.mean().values
    tot = pd.DataFrame([dict(case=name, bin="all", n=len(d), share=1.0, cond_cov=d.cond_cov.mean(), cond_width_median=d.cond_w.median(), cond_width_mean=d.cond_w.mean(), cond_err_median=d.cond_err.median(), cond_err_mean=d.cond_err.mean(),
                             hyb_cov=d.hyb_cov.mean(), hyb_width_mean=d.hyb_w.mean(), hyb_err_mean=d.hyb_err.mean(), naive_err_mean=d.naive_err.mean(), winner_is_truly_best=d.top_is_truly_best.mean())])
    return pd.concat([g, tot])
rows.append(case("reference cell K=16 tau=.01 n=200", 16, .01, 200)); rows.append(case("one clearly better config (+5pp) K=16 tau=0 n=500", 16, 0.0, 500, outlier=.05)); rows.append(case("one clearly better config (+5pp) K=16 tau=0 n=1000", 16, 0.0, 1000, outlier=.05))
d = pd.concat(rows); d["bin"] = d["bin"].astype(str); d.to_csv(sys.argv[1], index=False); print(d.round(3).to_string())
