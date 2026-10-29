"""C5: robustness of the main numbers to modelling choices. For each dataset and variant (primary, ties dropped, ridge 1e-1 /
1e-5, NBA without home term): ranking agreement with the primary fit and the worst-case budgets for top1 and the cheapest adjacent swap.
Usage: 08_sensitivity.py -> results/sensitivity.csv"""
import sys, numpy as np, pandas as pd, os
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"; rows = []
DESIGN = {"arena55k": "crowd", "mtbench_human": "expert", "mtbench_gpt4": "model_judge", "nba": "sports"}
variants = [("primary", {}, 1e-3), ("ties_dropped", {"keep_ties": False}, 1e-3), ("ridge_1e-1", {}, 1e-1), ("ridge_1e-5", {}, 1e-5), ("no_home_term", {"home": False}, 1e-3)]
for ds in DESIGN:
    rsens.LAM = 1e-3; ref = rsens.load(ds); th_ref = rsens.fit(ref); names_ref = ref.names
    for v, kw, lam in variants:
        if (v == "ties_dropped" and ds == "nba") or (v == "no_home_term" and ds != "nba"): continue
        rsens.LAM = lam; c = rsens.load(ds, **kw); th = rsens.fit(c); r = rsens.ranking(th, c.p)
        common = [n for n in names_ref if n in c.names]; a = [th_ref[names_ref.index(n)] for n in common]; b = [th[c.names.index(n)] for n in common]
        q = rsens.qvec(c, r[0], r[1]); z = (th[r[0]] - th[r[1]]) / np.sqrt(q @ np.linalg.inv(rsens.hess(c, th)) @ q)
        o = dict(dataset=ds, eval_design=DESIGN[ds], variant=v, N=c.n, p=c.p, tau_vs_primary=kendalltau(a, b).statistic, top1=c.names[r[0]], z_top=z)
        for m in ("drop", "flip"):
            o[f"top1_{m}"] = min(rsens.worst_case(c, r[0], r[j], m, th0=th)["k"] for j in (1, 2, 3))
            o[f"adjmin_{m}"] = min(rsens.worst_case(c, r[i], r[i + 1], m, th0=th)["k"] for i in range(c.p - 1))
        rows.append(o); print(ds, v, flush=True)
        pd.DataFrame(rows).to_csv(res + "sensitivity.csv", index=False)
