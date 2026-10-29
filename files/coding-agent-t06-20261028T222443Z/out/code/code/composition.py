"""Composition of the worst-case drop sets for the top-1 change (which comparisons are removed).
Usage: python code/composition.py   -> results/composition.json"""
import json
import os
import numpy as np
from bt import OUT, min_perturbation
from common import RES, load_board

out = {}
for b in ["arena140k", "arena55k", "webdev", "mtbench_human", "mtbench_gpt4", "arena55k_mt6", "arenaJ_crowd", "nba_2015"]:
    B = load_board(b)
    th = B.fit()[0]
    r = B.ranking(th)
    best = None
    for jj in range(1, min(6, B.K)):
        res = min_perturbation(B, r[0], r[jj], "drop")
        if res["verified"] and (best is None or res["k"] < best[1]["k"]):
            best = (jj, res)
    jj, res = best
    i, j = r[0], r[jj]
    cat = {"i_beats_j": 0, "i_beats_other": 0, "other_beats_j": 0, "tie_involving": 0, "other": 0}
    opp_rank = []
    for (g, o), c in res["moves"].items():
        a, bb, y = B.ga[g], B.gb[g], OUT[o]
        win, lose = (a, bb) if y == 1 else (bb, a)
        if y == 0.5:
            cat["tie_involving"] += c
        elif {win, lose} == {i, j} and win == i:
            cat["i_beats_j"] += c
        elif win == i:
            cat["i_beats_other"] += c
            opp_rank += [int(np.where(r == lose)[0][0]) + 1] * c
        elif lose == j:
            cat["other_beats_j"] += c
            opp_rank += [int(np.where(r == win)[0][0]) + 1] * c
        else:
            cat["other"] += c
    out[b] = dict(k=res["k"], i=str(B.names[i]), j=str(B.names[j]), j_rank=jj + 1, **cat,
                  median_opp_rank=float(np.median(opp_rank)) if opp_rank else None)
    print(b, out[b], flush=True)
json.dump(out, open(os.path.join(RES, "composition.json"), "w"), indent=1)
