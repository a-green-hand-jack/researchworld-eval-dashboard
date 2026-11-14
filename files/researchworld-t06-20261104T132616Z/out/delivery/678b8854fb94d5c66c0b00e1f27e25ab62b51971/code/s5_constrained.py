"""Constrained adversary budgets (paper-repo request #8a): additions / relabellings restricted to comparisons of one target participant.

For C1 (min over all challengers b of the top participant) and every C2 claim of the units of results/budgets_remove.csv (arena55k, mt_human, mt_gpt4,
nba_all, every NBA season): the verified budget of the constrained adversary on side a_down (higher-ranked participant pushed down) and b_up (lower-ranked
pushed up), for add and relabel; budget_* = min over the two sides. Definitions: code/btlib/constrained.py. Writes results/s5_constrained.csv."""
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an
from btlib import constrained as cs
from btlib import prov
from s1_run import build

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
UNITS_MAIN = ["arena55k", "mt_human", "mt_gpt4", "nba_all"]


def work(name):
    u = build(name)
    c = u.c
    P = an.claim_pairs(u)
    rows = []
    for claim, plist in P.items():
        if not (claim == "c1" or claim.startswith("c2")):
            continue
        res = {}
        for mode in ("add", "relabel"):
            for side in ("a_down", "b_up"):
                best, arg = np.nan, None
                for (a, b) in plist:
                    k = cs.budget(c, a, b, u.lam, u.lam_h, u.x0, mode, side)
                    if np.isfinite(k) and (not np.isfinite(best) or k < best):
                        best, arg = k, (a, b)
                res[f"{mode}_{side}"] = best
        row = dict(unit=name, claim=claim, a=c.names[plist[0][0]], N=int(c.N), gap_first_pair=u.base_gap(*plist[0]))
        row.update({f"budget_con_{k}": v for k, v in res.items()})
        for mode in ("add", "relabel"):
            row[f"budget_con_{mode}"] = np.nanmin([res[f"{mode}_a_down"], res[f"{mode}_b_up"]]) if np.isfinite([res[f"{mode}_a_down"], res[f"{mode}_b_up"]]).any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    names = [n for n in d.unit.unique() if n in UNITS_MAIN or (n.startswith("nba") and n[3:].isdigit())]
    with ProcessPoolExecutor(2) as ex:
        res = list(ex.map(work, names, chunksize=1))
    pd.concat(res, ignore_index=True).to_csv(f"{OUT}/s5_constrained.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s5_constrained.meta.json", script="code/s5_constrained.py")


if __name__ == "__main__":
    main()
