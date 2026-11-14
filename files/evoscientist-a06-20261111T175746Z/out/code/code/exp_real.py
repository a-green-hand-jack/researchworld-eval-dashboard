"""E1-E3 on the real LLM correctness matrices: winner's-curse bias scaling, optimizers, reporting protocols.

python code/exp_real.py --tag Qwen2.5-0.5B-Instruct_fp32 --R 1000 --out results/real_05B.json
"""
import argparse, json, math, sys, time
import numpy as np
sys.path.insert(0, "code")
import sel
from common import load_matrix, pmap, to_py

ap = argparse.ArgumentParser()
ap.add_argument("--tag", required=True); ap.add_argument("--R", type=int, default=1000)
ap.add_argument("--R_sh", type=int, default=400); ap.add_argument("--out", required=True)
ap.add_argument("--ns", default="50,100,200,400,800"); ap.add_argument("--Ks", default="2,4,8,16,32")
ap.add_argument("--nproc", type=int, default=3); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--nmax", type=int, default=0)
a = ap.parse_args()
Y, meta = load_matrix(a.tag, a.nmax or None)
Ktot, N = Y.shape
ns = [int(x) for x in a.ns.split(",")]
Ks = [k for k in (int(x) for x in a.Ks.split(",")) if k <= Ktot]
if Ks[-1] != Ktot and Ktot not in Ks: Ks.append(Ktot)
mu = Y.mean(1)
print(f"{a.tag}: K={Ktot} N={N}; true acc min/median/max = {mu.min():.4f}/{np.median(mu):.4f}/{mu.max():.4f}", flush=True)


def gauss_pred(K, n, nsub=100, ndraw=4000, seed=1):
    """Gaussian-approximation prediction of E[naive - truth] for exhaustive best-of-K:
    eps ~ N(0, Cov_q(Y)/n) over random K-subsets of configs (uses the true covariance of per-question outcomes)."""
    rng = np.random.default_rng(seed)
    bias = []
    for _ in range(nsub):
        idx = rng.choice(Ktot, K, replace=False) if K < Ktot else np.arange(Ktot)
        Ysub = Y[idx]; m = Ysub.mean(1)
        C = np.cov(Ysub) / n + 1e-12 * np.eye(K)
        L = np.linalg.cholesky(C)
        eps = rng.standard_normal((ndraw, K)) @ L.T
        k = np.argmax(m[None, :] + eps, axis=1)
        bias.append(eps[np.arange(ndraw), k].mean())
        if K == Ktot: break
    return float(np.mean(bias))


def null_pred(K, n):
    """Closed-form null approximation: sigma*sqrt((1-rho)/n) * E[max of K iid N(0,1)] (sigma, rho estimated from Y)."""
    p = Y.mean()
    var = (Y.var(1)).mean()
    cov = np.cov(Y); off = (cov.sum() - np.trace(cov)) / (Ktot * (Ktot - 1)); rho = off / var
    # E max of K iid std normals via numerical integration
    from scipy import stats
    x = np.linspace(-8, 8, 20001); Fx = stats.norm.cdf(x); fx = stats.norm.pdf(x)
    emax = np.trapezoid(x * K * Fx ** (K - 1) * fx, x)
    return float(math.sqrt(var) * math.sqrt(max(0, 1 - rho) / n) * emax), float(rho), float(math.sqrt(var))


def job(args):
    optname, K, n, R, seed = args
    t = time.time()
    res = sel.run_many(Y, K, n, optname, R, seed, B=200, split_fracs=(0.2, 0.5))
    s = sel.summarize(res)
    s.update(K=K, n=n, opt=optname, R=R)
    if optname == "sh":
        s["budget"] = sel.sh_cost(K, n); s["budget_exh"] = K * n
    return s, {k: v.astype(np.float32) for k, v in res.items() if k in ("naive", "truth", "oracle", "k", "boot_optimism")}, time.time() - t


jobs = [("exh", K, n, a.R, a.seed + 1000 * K + n) for K in Ks for n in ns]
jobs += [("sh", K, n, a.R_sh, a.seed + 7 + 1000 * K + n) for K in Ks if K >= 4 for n in ns]
t0 = time.time()
outs = pmap(job, jobs, a.nproc)
print(f"done {len(jobs)} settings in {time.time()-t0:.0f}s", flush=True)
rows = []
for (s, raw, dt) in outs:
    if s["opt"] == "exh":
        s["pred_gauss"] = gauss_pred(s["K"], s["n"])
        s["pred_null"], s["rho_hat"], s["sigma_hat"] = null_pred(s["K"], s["n"])
        s["pred_hoeffding"] = math.sqrt(math.log(s["K"]) / (2 * s["n"])) if s["K"] > 1 else 0.0
        s["pred_subgauss"] = s["sigma_hat"] * math.sqrt(2 * math.log(s["K"]) / s["n"]) if s["K"] > 1 else 0.0
    rows.append(s)
json.dump(to_py(dict(tag=a.tag, K=Ktot, N=N, true_acc=mu, cfg_ids=meta["cfg_ids"], rows=rows)), open(a.out, "w"))
print("saved", a.out)
