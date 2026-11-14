"""Run methods x budgets x reps for one benchmark and protocol; write per-target predictions (parquet)."""
import argparse, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import data, protocol as P, methods as M, methods2, methods3, methods4

ap = argparse.ArgumentParser()
ap.add_argument("--bench", required=True)
ap.add_argument("--protocol", default="random")
ap.add_argument("--frac", type=float, default=0.2)
ap.add_argument("--methods", default="random,strat_random,anchor,calib,ridge,irt_rand,aipw_rand,irt_info,anchor_irt,anchor_aipw")
ap.add_argument("--budgets", default="10,20,50,100,200")
ap.add_argument("--reps", type=int, default=10)
ap.add_argument("--src_frac", type=float, default=1.0)
ap.add_argument("--label", default=None)
ap.add_argument("--no_dedup", action="store_true")
ap.add_argument("--out", default="/hutian/repo/results/raw")
a = ap.parse_args()

X, models = data.load(a.bench)
if not a.no_dedup:
    X, models = P.dedup(X, models)
acc = X.mean(1)
rows = []
t0 = time.time()
for rep in range(a.reps):
    src, tgt = P.split(a.protocol, acc, rep, a.frac, models)
    if a.src_frac < 1:  # keep a random subset of the source models (target set unchanged)
        src = np.sort(np.random.default_rng(777 + rep).choice(src, max(10, int(round(a.src_frac * len(src)))), replace=False))
    Xs, Xt = X[src], X[tgt]
    ctx = {}
    for n in map(int, a.budgets.split(",")):
        for name in a.methods.split(","):
            m = M.ALL[name]()
            tt = time.time()
            idx = m.fit(Xs, n, 10_000 * rep + n, ctx)
            pred = np.asarray(m.predict(Xt[:, idx]), dtype=np.float64)
            se = getattr(m, "se", None)
            se = np.full(len(pred), np.nan) if se is None else np.asarray(se)
            for k, (ti, p) in enumerate(zip(tgt, pred)):
                rows.append((a.bench, a.protocol, rep, name, n, int(ti), float(acc[ti]), float(p), float(se[k])))
    print(f"{a.bench} {a.protocol} rep {rep} {time.time()-t0:.0f}s", flush=True)
df = pd.DataFrame(rows, columns="bench protocol rep method n model true pred se".split())
df["n_src"] = len(src)
if a.label:
    df["protocol"] = a.label
os.makedirs(a.out, exist_ok=True)
df.to_parquet(f"{a.out}/{a.bench}__{a.label or a.protocol}.parquet")
