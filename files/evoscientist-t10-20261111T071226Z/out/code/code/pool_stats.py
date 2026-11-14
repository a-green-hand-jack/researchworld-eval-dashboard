"""Population (pool) statistics behind the headroom analysis -> results/pool_stats.csv, paper/tables/tab_pool.tex"""
import os
import numpy as np
import pandas as pd
from real_lib import load, cached_oracle, DATASETS

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for ds in DATASETS:
    Y, F, _ = load(ds)
    g = cached_oracle(ds)  # E[Y|f]: exact group means for discrete f, 10-fold cross-fitted boosting otherwise
    EV = np.mean((Y - g) ** 2)
    varY = Y.var()
    varg = varY - EV
    gs = g.copy()
    rho2 = np.corrcoef(gs, F)[0, 1] ** 2 if len(np.unique(F)) > 1 else np.nan
    cov_gf = np.mean((g - g.mean()) * (F - F.mean()))
    # (the cross-fitted g has Var slightly different from varg; rescale covariance accordingly)
    scale = np.sqrt(max(varg, 0) / g.var()) if g.var() > 0 else 0
    lam200 = scale * cov_gf / ((1 + 200 / 1e4) * F.var())
    rows.append(dict(dataset=ds, pool=len(Y), uniq_f=len(np.unique(F)), meanY=Y.mean(), corrYf=np.corrcoef(Y, F)[0, 1],
                     R2_g=varg / varY, rho2_gf=rho2, lam_star_n200=lam200))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "..", "results", "pool_stats.csv"), index=False)
DS = {"galaxies": "Galaxies", "forest": "Forest", "alphafold": "AlphaFold", "gene_expression": "Gene expr.",
      "census_income": "Census income", "census_healthcare": "Census health", "census_education": "Census educ.",
      "plankton": "Plankton", "ballots": "Ballots"}
out = ["\\begin{tabular}{lrrrrrr}", "\\toprule",
       "Dataset & pool & distinct $f$ & Corr$(Y,f)$ & $\\mathrm{Var}(g)/\\mathrm{Var}(Y)$ & $\\rho^2$ & $\\lambda^\\star$ ($n{=}200$) \\\\", "\\midrule"]
for r in rows:
    uf = r["uniq_f"] if r["uniq_f"] < 100 else "$>10^2$"
    out.append(f"{DS[r['dataset']]} & {r['pool']:,} & {uf} & {r['corrYf']:.3f} & {r['R2_g']:.3f} & {r['rho2_gf']:.3f} & {r['lam_star_n200']:.2f} \\\\")
out += ["\\bottomrule", "\\end{tabular}"]
os.makedirs(os.path.join(HERE, "..", "paper", "tables"), exist_ok=True)
open(os.path.join(HERE, "..", "paper", "tables", "tab_pool.tex"), "w").write("\n".join(out))
print(df.round(4).to_string())
