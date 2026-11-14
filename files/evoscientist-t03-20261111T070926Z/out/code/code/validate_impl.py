"""Validate the re-implemented estimators against the `shap` package (Pima, d=8, exact reference from the
full coalition table). Output: results/validate_impl.csv  (RMSE to exact Shapley values, 100 runs/instance)."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import numpy as np, pandas as pd, shap, time, warnings
from data import load, RESULTS
from models import Model
from shapsim import *

warnings.filterwarnings("ignore")
D = load("pima")
rng = np.random.default_rng(123)
X = D["X"]
rows = []
for kind in ["xgb", "mlp", "rf"]:
    M = Model(kind, D, seed=0)
    bg = X[D["train"]][rng.choice(len(D["train"]), 100, replace=False)]
    kex = shap.KernelExplainer(M.proba, bg)
    pex = shap.PermutationExplainer(M.proba, bg)
    for i in D["test"][:10]:
        x = X[i]
        tab = build_table(M.proba, x, bg)
        phi = exact_shapley(tab)
        V = TableV(tab)
        d = 8
        for m in (16, 32, 64, 128):
            mine_k = np.array([kernel_shap(V, d, tab[0], tab[-1], m, rng)[0] for _ in range(100)])
            lib_k = np.array([kex.shap_values(x[None], nsamples=m, l1_reg=0, silent=True)[0] for _ in range(100)])
            mine_p = np.array([perm_shap(V, d, tab[0], tab[-1], m, rng)[0] for _ in range(100)])
            # permutation explainer: max_evals = evals incl. the 2 fixed endpoints; npermutations = max_evals//(2d)
            lib_p = np.array([pex(x[None], max_evals=m + 2 * d, silent=True).values[0] for _ in range(100)])
            r = lambda a: float(np.sqrt(((a - phi) ** 2).mean()))
            rows.append(dict(model=kind, inst=int(i), m=m, kernel_mine=r(mine_k), kernel_lib=r(lib_k),
                             perm_mine=r(mine_p), perm_lib=r(lib_p)))
df = pd.DataFrame(rows)
df.to_csv(RESULTS + "/validate_impl.csv", index=False)
g = df.groupby(["model", "m"])[["kernel_mine", "kernel_lib", "perm_mine", "perm_lib"]].mean()
print(g.round(5))
print("median ratio kernel mine/lib:", (df.kernel_mine / df.kernel_lib).median(), " perm mine/lib:", (df.perm_mine / df.perm_lib).median())
