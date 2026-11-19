"""E2 on OLLB: the same models at benchmark level (m=6, 'bundled': each benchmark is one task, a boost lifts its score) and at sub-task level (m=39, 'free').
usage: run_e2_ollb.py OUT.csv [shard n_shards] [ntargets=30] [boards=ollb|helm]  (boards=helm: the full HELM board, m=57, all models up to ntargets, sigma-unit budgets)
Models: main slice with a `results` row reproducing the `contents` row. Targets: top-N by the hierarchical official score (= mean of the six benchmark means).
Budgets in sigma of the granularity analysed. Rules: mean, zmean, median, min, borda, plurality, copeland (+ meanh on m39)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice.e2 import run_draw, RULES2
from lbprice.boards import load_ollb
out = sys.argv[1]
shard, ns = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
ntar = int(sys.argv[4]) if len(sys.argv) > 4 else 30
which = sys.argv[5] if len(sys.argv) > 5 else "ollb"
if which == "helm":
    from lbprice.boards import load_helm
    h = load_helm(); top = list(np.argsort(-h["official"], kind="stable")[:ntar]); boards = (("helm", h, RULES2, None),)
else:
    b6, b39 = load_ollb("m6raw"), load_ollb("m39")
    assert b6["names"] == b39["names"]
    top = list(np.argsort(-b39["official"], kind="stable")[:ntar])
    boards = (("m6raw", b6, RULES2, None), ("m39", b39, RULES2 + ["meanh"], b39["w_h"]))
rows = []; t0 = time.time(); k = 0
for name, b, rules, wh in boards:
    S = b["S"]; sig = S.std(axis=0)
    for t in top:
        k += 1
        if (k - 1) % ns != shard: continue
        rows += run_draw(S, [t], sig, 100.0, rules=rules, tl=30.0, meta=dict(board=name, model=b["names"][t], rank_official=int(list(top).index(t)) + 1), wh=wh)
        print(name, t, len(rows), round(time.time() - t0), flush=True)
        pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
