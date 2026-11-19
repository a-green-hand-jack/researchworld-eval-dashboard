"""Core experiment: minimal number of targeted sub-datasets k*(rule, delta, cap)
for a target model to become strictly first, for many targets, both boards.
  python analysis/02_min_k.py {helm|olb} [variant] [--raw] [--out NAME]
Writes results/mink_<name>.csv  (one row per target x rule x delta x cap)."""
import argparse, time
from common import *

ap = argparse.ArgumentParser()
ap.add_argument("board"); ap.add_argument("variant", nargs="?", default="main")
ap.add_argument("--raw", action="store_true"); ap.add_argument("--name", default=None)
ap.add_argument("--n_log", type=int, default=300)
a = ap.parse_args()
DELTAS = [2, 5, 10, 20, 40, 100]
if a.board == "helm":
    df = load_helm(); S = df.values; names = df.index.values; tg = np.arange(len(S)); trank = None
else:
    o, S = load_olb(a.variant, a.raw); names = o["fullname"].values
    tg, _ = pick_targets(S, a.n_log)
m, n = S.shape
best = S.max(0)
caps = {"ceiling": np.full(n, 100.0), "sota+1": np.minimum(100.0, best + 1.0)}
base_rank = {r: initial_ranks(S, r) for r in R.RULES}
rows = []; t0 = time.time()
for ii, t in enumerate(tg):
    for rule in R.RULES:
        for cap, hi in caps.items():
            for d in DELTAS:
                if cap == "sota+1" and d == 100: continue  # == pure SOTA-cap
                k = V.min_k(S, int(t), rule, float(d), hi)
                rows.append((names[t], int(t), rule, cap, d, k, int(base_rank[rule][t]), int(base_rank["mean"][t])))
    if ii % 25 == 0: print(a.board, ii, len(tg), round(time.time() - t0), "s", flush=True)
out = pd.DataFrame(rows, columns=["model", "idx", "rule", "cap", "delta", "k", "rank_rule", "rank_mean"])
out["n_tasks"] = n; out["n_models"] = m
name = a.name or f"{a.board}_{a.variant}{'_raw' if a.raw else ''}"
out.to_csv(f"{ROOT}/results/mink_{name}.csv", index=False)
print("done", name, len(out), round(time.time() - t0), "s")
