"""Synthetic generator matched to the real correctness matrix, and its naive gap against the real replay.
usage: calibrated_generator.py MATRIX.npz REAL_SUMMARY.csv OUTDIR [P] [M]
 (a) synthetic_phi_map.csv : mean pairwise 0/1 item correlation (phi) of two configs of the Gaussian-copula generator as a function of (accuracy m, latent rho), exact (bivariate normal cdf)
 (b) generator_calibration.csv : real accuracy / sd across configs / mean pairwise phi, the latent rho that reproduces phi at that accuracy, item-count profile (share of items solved by j of the K configs), pairwise phi range
 (c) generator_vs_real_gap.csv : naive gap (bias of the naive report, argmax) in P independent generator pools of N = N_real items with K = K_pool configs, M replications each, vs the real replay, per truth arm. Generators: `uniform_rho` = Gaussian copula with one latent rho (matched to the mean pairwise phi) and the real accuracies as thresholds; `tetrachoric` = Gaussian copula whose full latent correlation matrix reproduces every pairwise phi of the real matrix (pairwise tetrachoric inversion, nearest PSD)."""
import sys, os, numpy as np, pandas as pd
from scipy.stats import norm, multivariate_normal
from scipy.optimize import brentq
from synth import make_pool; from run_grid import run, summarize
mat, summ, outd = sys.argv[1:4]; P = int(sys.argv[4]) if len(sys.argv) > 4 else 10; M = int(sys.argv[5]) if len(sys.argv) > 5 else 300; os.makedirs(outd, exist_ok=True)
Y = np.load(mat, allow_pickle=True)["Y"]; Kp, N = Y.shape; acc = Y.mean(1); m = acc.mean(); tau = acc.std(ddof=1)
def phi_of(p, rho):
    if rho <= 0: return 0.0
    a = norm.ppf(p); p11 = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]]).cdf([a, a]); return float((p11 - p * p) / (p * (1 - p)))
mp_ = pd.DataFrame([dict(m=mm, rho=r, phi=phi_of(mm, r)) for mm in (.05, .1, .195, .3, .5, .7) for r in (0, .1, .3, .5, .6, .7, .8, .9, .95)]); mp_.to_csv(f"{outd}/synthetic_phi_map.csv", index=False)
C = np.corrcoef(Y.astype(float)); iu = np.triu_indices(Kp, 1); phi_real = C[iu].mean(); rho_m = brentq(lambda r: phi_of(m, r) - phi_real, 1e-6, .999)
prof = lambda Z: np.bincount(Z.sum(0), minlength=Kp + 1) / Z.shape[1]
_r = np.random.default_rng(1); Z = (np.sqrt(rho_m) * _r.standard_normal(200000)[None, :] + np.sqrt(1 - rho_m) * _r.standard_normal((Kp, 200000))) < norm.ppf(acc)[:, None]; Zc = np.corrcoef(Z[:, :50000].astype(float))[iu]
cal = [dict(item="accuracy mean", real=m, generator=Z.mean()), dict(item="accuracy sd across configs", real=tau, generator=Z.mean(1).std(ddof=1)),
       dict(item="mean pairwise phi", real=phi_real, generator=Zc.mean()), dict(item="min pairwise phi", real=C[iu].min(), generator=Zc.min()), dict(item="max pairwise phi", real=C[iu].max(), generator=Zc.max()),
       dict(item="latent rho matched to the real phi", real=np.nan, generator=rho_m), dict(item="sd of item-mean accuracy across items", real=Y.mean(0).std(), generator=Z.mean(0).std())]
pr, pg = prof(Y), prof(Z); cal += [dict(item=f"share of items solved by exactly {j} of {Kp} configs", real=pr[j], generator=pg[j]) for j in range(Kp + 1)]
pd.DataFrame(cal).to_csv(f"{outd}/generator_calibration.csv", index=False); print(pd.DataFrame(cal).to_string())
def pair_phi(p1, p2, r):
    a, b = norm.ppf(p1), norm.ppf(p2); p11 = multivariate_normal(mean=[0, 0], cov=[[1, r], [r, 1]]).cdf([a, b]); return (p11 - p1 * p2) / np.sqrt(p1 * (1 - p1) * p2 * (1 - p2))
R = np.eye(Kp)
for i, j in zip(*iu):
    t = C[i, j]
    if t <= 1e-6: r = 0.0
    else: r = brentq(lambda r_: pair_phi(acc[i], acc[j], r_) - t, 1e-6, .999)
    R[i, j] = R[j, i] = r
w, V = np.linalg.eigh(R); n_neg = int((w < 1e-8).sum()); R = (V * np.clip(w, 1e-8, None)) @ V.T; dd = np.sqrt(np.diag(R)); R = R / np.outer(dd, dd)
LR = np.linalg.cholesky(R)
def gen(kind, N_, seed):
    rng = np.random.default_rng(seed)
    if kind == "uniform_rho":
        q = rng.standard_normal(N_); U = np.sqrt(rho_m) * q[None, :] + np.sqrt(1 - rho_m) * rng.standard_normal((Kp, N_))
    else: U = LR @ rng.standard_normal((Kp, N_))
    return U < norm.ppf(acc)[:, None]
Zt = gen("tetrachoric", 200000, 2); Ct = np.corrcoef(Zt[:, :50000].astype(float))[iu]
pd.DataFrame([dict(item="pairwise phi: max |generator - real| over pairs", uniform_rho=np.abs(Zc - C[iu]).max(), tetrachoric=np.abs(Ct - C[iu]).max()),
              dict(item="pairwise phi: rms difference", uniform_rho=np.sqrt(((Zc - C[iu]) ** 2).mean()), tetrachoric=np.sqrt(((Ct - C[iu]) ** 2).mean())),
              dict(item="latent rho over pairs: min / median / max", uniform_rho=rho_m, tetrachoric=f"{R[iu].min():.3f} / {np.median(R[iu]):.3f} / {R[iu].max():.3f}"),
              dict(item="tetrachoric R: eigenvalues clipped (count)", uniform_rho=np.nan, tetrachoric=n_neg)]).to_csv(f"{outd}/generator_pairwise_fit.csv", index=False)
S0 = pd.read_csv(summ); S0 = S0[(S0.proc == "argmax") & (S0.est_name == "naive")]
rows = []
for arm in sorted(S0.truth_arm.unique()):
    S = S0[S0.truth_arm == arm]; Ks = sorted(S.K.unique()); ns = sorted(S.n.unique())
    for kind in ("uniform_rho", "tetrachoric"):
        for pidx in range(P):
            G = gen(kind, N, 900 + pidx)
            d = run(G, 0, ["argmax"], ns, Ks, ["naive"], M, seed=50 + pidx, tag=f"gen{pidx}", disjoint=(arm == "disjoint")); d["generator"] = kind; d["truth_arm"] = arm; rows.append(d)
D = pd.concat(rows); D["err"] = D.est - D.mu
g = D.groupby(["truth_arm", "generator", "n", "K"]).err.agg(["mean", "std", "size"]).reset_index(); g["gen_se"] = g["std"] / np.sqrt(g["size"])
r = S0[["truth_arm", "n", "K", "bias", "bias_se"]].rename(columns={"bias": "real_gap", "bias_se": "real_se"}); g = g.rename(columns={"mean": "gen_gap"}).merge(r, on=["truth_arm", "n", "K"])
g["K_pool"] = Kp; g["pools"] = P; g["reps_per_pool"] = M; g["z"] = (g.gen_gap - g.real_gap) / np.hypot(g.gen_se, g.real_se)
g[["truth_arm", "generator", "K_pool", "n", "K", "gen_gap", "gen_se", "real_gap", "real_se", "z", "pools", "reps_per_pool"]].to_csv(f"{outd}/generator_vs_real_gap.csv", index=False); print(g.round(4).to_string())
