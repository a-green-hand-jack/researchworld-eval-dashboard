"""Tidy per-(instance, arm, budget, k) results from runs_<tag>.npz of one cell -> results/tidy_<cell>_<tag>.csv
(+ per-run plug-in z for the Covert-Lee arm -> results/plugz_<cell>_<tag>.npz)."""
import argparse, json, os
import numpy as np, pandas as pd
from shapaudit import metrics as M, cells

ap = argparse.ArgumentParser(); ap.add_argument("--cell"); ap.add_argument("--tag", default="R20"); a = ap.parse_args()
cdir = os.path.join(cells.WORK, "cells", a.cell)
meta = json.load(open(os.path.join(cdir, "meta.json"))); mz = np.load(os.path.join(cdir, "meta.npz"))
z = np.load(os.path.join(cdir, f"runs_{a.tag}.npz")); rj = json.load(open(os.path.join(cdir, f"runs_{a.tag}.json")))
inst = z["inst"]; ps = mz["phi_star"][inst]                         # (n, d)
d = ps.shape[1]; KS = (1, 3, 5)
rows = []; plug = {}
for key in z.files:
    if not key.startswith("phi/"): continue
    _, arm, b = key.split("/")
    ph = z[key].astype(np.float64)                                  # (n, R, d)
    n, R, _ = ph.shape
    cost = z[f"cost/{arm}/{b}"].mean(1); sec = z[f"sec/{arm}/{b}"].mean(1)
    if cost.max() == 0: continue                                    # arm not run at this budget (perm500 is perm-only)
    l2 = M.rel_l2(ph, ps[:, None]).mean(1)
    bias = np.linalg.norm(ph.mean(1) - ps, axis=-1) / (np.linalg.norm(ps, axis=-1) + 1e-12)
    for k in KS:
        T = M.topk_mask(ph, k)
        ok = M.exact_topk(ph, ps[:, None], k); oke = M.eps_topk(ph, ps[:, None], k, 0.1)
        ok25 = M.eps_topk(ph, ps[:, None], k, 0.25)
        sg = M.sign_topk(ph, ps[:, None], k)
        ordr = np.argsort(-np.abs(ps), 1); i1, i2 = ordr[:, k - 1], ordr[:, k]
        ar = np.abs(ph); diff = np.take_along_axis(ar, i1[:, None, None], 2)[..., 0] - np.take_along_axis(ar, i2[:, None, None], 2)[..., 0]
        gp = M.gap(ps, k); sdg = diff.std(1, ddof=1)
        # bias of the expected estimate at the boundary: does the mean attribution already rank the true set?
        ok_mean = M.exact_topk(ph.mean(1), ps, k)
        jac = M.pairwise_jaccard(T); nog = M.nogueira(T)
        rb = np.array([np.mean([M.rbo(ph[i, r], ph[i, s]) for r, s in zip(*np.triu_indices(min(R, 10), 1))]) for i in range(n)])
        for i in range(n):
            rows.append(dict(cell=a.cell, inst=int(inst[i]), arm=arm, budget=b, k=k, N=float(cost[i]), sec=float(sec[i]),
                             r=ok[i].mean(), r_eps10=oke[i].mean(), r_eps25=ok25[i].mean(), r_sign=sg[i].mean(), jacc=jac[i], nog=nog[i], rbo=rb[i],
                             rel_l2=l2[i], rel_bias=bias[i], gap=gp[i], sd_gap=sdg[i], z_true=gp[i] / max(sdg[i], 1e-12), mean_ok=bool(ok_mean[i]),
                             nvar=int(z["nvar"][i]), d=d, R=R))
    if arm == "covert_lee" and f"se/covert_lee/{b}" in z.files:
        se = z[f"se/covert_lee/{b}"].astype(np.float64)
        for k in KS:
            o = np.argsort(-ar, -1)                                  # each run's own ranking
            j1, j2 = o[..., k - 1], o[..., k]
            dd = np.take_along_axis(ar, j1[..., None], -1)[..., 0] - np.take_along_axis(ar, j2[..., None], -1)[..., 0]
            s1 = np.take_along_axis(se, j1[..., None], -1)[..., 0]; s2 = np.take_along_axis(se, j2[..., None], -1)[..., 0]
            zp = dd / np.sqrt(s1 ** 2 + s2 ** 2 + 1e-18)             # plug-in z (independent-pair SE; ignores the covariance)
            plug[f"zplug/{b}/k{k}"] = zp; plug[f"ok/{b}/k{k}"] = M.exact_topk(ph, ps[:, None], k)
os.makedirs("results", exist_ok=True)
pd.DataFrame(rows).to_csv(f"results/tidy_{a.cell}_{a.tag}.csv", index=False)
np.savez_compressed(f"results/plugz_{a.cell}_{a.tag}.npz", inst=inst, **plug)
print("wrote", len(rows), "rows")
