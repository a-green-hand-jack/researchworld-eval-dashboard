import os
for _v in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[_v]="1"
import time, sys
import numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from gate_lib import *

for mech, kap in [("lin-frac", 1), ("pow", 2.0), ("pow", 4.0), ("thresh", 1), ("het-frac", 1)]:
    sc = dict(graph=dict(kind="er", n=4000, d=20, gseed=1), mech=mech, outcome=dict(kappa=kap),
              design=dict(kind="bern", p=0.5), estimators=ALL_EST, seed=1)
    t = time.time()
    ctx = Context(sc)
    t_init = time.time() - t
    rng = np.random.default_rng(5)
    rows = {k: [] for k in ALL_EST}
    ses = {k: [] for k in ALL_EST}
    t = time.time()
    R = 100
    for r in range(R):
        res = ctx.one_rep(rng)
        for k, v in res.items():
            rows[k].append(v[0]); ses[k].append(v[1])
    tt = (time.time() - t) / R
    print(f"== {mech} kappa={kap} GATE={ctx.out.gate:.3f} init {t_init:.1f}s, {tt:.2f}s/rep")
    for k in ALL_EST:
        a = np.array(rows[k], float)
        extra = ""
        if k.startswith("OLS") or k == "Oracle":
            b, v, vt, _ = predict_ols(ctx, k, R=100)
            extra = f" predbias={b:+.3f} predsd={np.sqrt(v):.3f} meanse={np.nanmean(ses[k]):.3f}"
        print(f"  {k:10s} bias={np.nanmean(a)-ctx.out.gate:+.3f} sd={np.nanstd(a):.3f} nvalid={np.sum(~np.isnan(a))}{extra}")
