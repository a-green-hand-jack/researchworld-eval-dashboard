"""Wall-clock cost of one explainer call by dataset x model x explainer x budget (single thread, shared host: indicative)."""
import os, sys, time, json
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
sys.path.insert(0, os.path.dirname(__file__))
import data as datamod, models, explain
from run_cell import BUDGETS

out = []
B = 50
for ds in sys.argv[1:] or list(BUDGETS):
    D = datamod.LOADERS[ds]()
    itr, ite = train_test_split(np.arange(len(D.y)), test_size=0.3, random_state=0, stratify=D.y)
    Atr, ytr, Ate = D.A[itr], D.y[itr], D.A[ite]
    rng = np.random.RandomState(1000)
    bg = Atr[rng.choice(len(Atr), B, replace=False)]
    X = Ate[rng.choice(len(Ate), 3, replace=False)]
    for mn in models.MODELS:
        mdl = models.fit(mn, D.encode(Atr), ytr, 0)
        f = lambda Z: models.predict_pos(mdl, D.encode(Z))
        explain.perm_shap(f, X[0], bg, 3 * D.d, 0)  # warm-up (numba compile)
        for ex, fn in (("kernel", explain.kernel_shap), ("perm", explain.perm_shap)):
            for m in BUDGETS[ds]:
                ts, rs = [], []
                for i in range(3):
                    for r in range(2):
                        t = time.perf_counter(); _, rows = fn(f, X[i], bg, m, r); ts.append(time.perf_counter() - t); rs.append(rows)
                out.append(dict(dataset=ds, model=mn, explainer=ex, budget=m, rows=float(np.mean(rs)), sec_per_call=float(np.mean(ts)),
                                sec_per_call_sd=float(np.std(ts, ddof=1)), n_calls=len(ts)))
        print(ds, mn, "done", flush=True)
os.makedirs("results/tables", exist_ok=True)
pd.DataFrame(out).to_csv("results/tables/timing.csv", index=False)
