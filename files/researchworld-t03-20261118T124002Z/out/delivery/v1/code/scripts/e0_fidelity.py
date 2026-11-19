"""E0: fidelity of the table-engine re-implementations against the live shap 0.51.0 classes on the real model.
For a few instances of a cell, run shap.KernelExplainer (shipped default and l1_reg=False) and shap.PermutationExplainer
R times with different seeds on the real model, and the same estimators of shapaudit on the exact table; compare the
distribution of the read-outs (r_k, per-feature mean / sd).  Players = attributes (the model is wrapped in attribute space)."""
import sys, json, time, argparse, warnings; sys.path.insert(0, __file__.rsplit("/scripts", 1)[0])
import numpy as np, shap
from shapaudit import cells, estimators as E, metrics as M, runs
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--cell"); ap.add_argument("--inst", default="0,1,2,3,4"); ap.add_argument("--R", type=int, default=100)
ap.add_argument("--mults", default="1,0.25")
a = ap.parse_args()
cdir = f"{cells.WORK}/cells/{a.cell}"
meta = json.load(open(f"{cdir}/meta.json")); mz = np.load(f"{cdir}/meta.npz")
ds, enc, mod, bg_idx, inst_idx, _ = cells.setup(meta["dataset"], meta["d_sub"], meta["model"], meta["seed"], meta["m"], meta["n_inst"], out=meta.get("output", "prob"))
d = ds.d
f = lambda X: mod.predict(enc(X))
bg = ds.X[bg_idx]
res = []
for t in [int(x) for x in a.inst.split(",")]:
    x = ds.X[inst_idx[t]]
    phis = mz["phi_star"][t]
    var = cells.varying(ds, x, bg_idx)
    orc = runs._oracle(meta, cdir, t, ds, enc, mod, bg_idx, inst_idx, var, d)
    for mult in [float(v) for v in a.mults.split(",")]:
        N = int(round((2 * d + 2048) * mult))
        for arm in ["kshap_default", "kshap_l1off", "perm"]:
            live, mine = np.zeros((a.R, d)), np.zeros((a.R, d))
            t_live = 0
            for r in range(a.R):
                np.random.seed(1000 + r)
                t0 = time.perf_counter()
                if arm == "perm":
                    ex = shap.PermutationExplainer(f, bg, seed=1000 + r)
                    live[r] = ex(x[None], max_evals=N).values[0]
                else:
                    ex = shap.KernelExplainer(f, bg)
                    live[r] = ex.shap_values(x[None], nsamples=N, l1_reg="num_features(10)" if arm == "kshap_default" else False, silent=True)[0]
                t_live += time.perf_counter() - t0
                rng = np.random.default_rng(5000 + r)
                ph, _ = runs.run_arm(arm, orc, N, rng)
                mine[r, var] = ph
            row = dict(inst=t, mult=mult, arm=arm, N=N, M=len(var), live_sec=t_live / a.R)
            for k in (1, 3, 5):
                row[f"r{k}_live"] = float(M.exact_topk(live, phis, k).mean()); row[f"r{k}_mine"] = float(M.exact_topk(mine, phis, k).mean())
            sd_l, sd_m = live.std(0, ddof=1), mine.std(0, ddof=1)
            row["mean_diff_in_se"] = float(np.max(np.abs(live.mean(0) - mine.mean(0)) / (np.sqrt((sd_l ** 2 + sd_m ** 2) / a.R) + 1e-9)))
            row["sd_ratio_median"] = float(np.median(sd_m[sd_l > 1e-6] / sd_l[sd_l > 1e-6])) if (sd_l > 1e-6).any() else None
            row["bias_live"] = float(np.linalg.norm(live.mean(0) - phis) / np.linalg.norm(phis))
            row["bias_mine"] = float(np.linalg.norm(mine.mean(0) - phis) / np.linalg.norm(phis))
            row["relL2_live"] = float(M.rel_l2(live, phis).mean()); row["relL2_mine"] = float(M.rel_l2(mine, phis).mean())
            res.append(row); print(row, flush=True)
json.dump(res, open(f"/hutian/repo/results/e0_fidelity_{a.cell}.json", "w"), indent=1)
