"""E7: ablations / robustness of the methodology.

(a) tie handling: ties as half wins (default) vs ties dropped;
(b) ridge strength lambda;
(c) greedy batch fraction (step_frac) - search-procedure sensitivity;
(d) exact certification: for every pair in e1_pairs.csv whose best cost is 2, check
    exhaustively that no single action (drop / flip / add) reverses it.
-> results/e7_ties.csv, e7_lambda.csv, e7_step.csv, e7_exact_k1.csv
"""
from common import *  # noqa
import multiprocessing as mp
import numpy as np
import pandas as pd
from lbrobust import data as D
from lbrobust.perturb import Searcher
from lbrobust.analysis import analyze_dataset


def ties_job(name):
    d = D.load(name, ties="drop")
    d.meta["name"] += "[ties dropped]"
    _, s = analyze_dataset(d)
    s.update(source=name, ties="drop")
    return s


def lam_job(spec):
    name, lam = spec
    _, s = analyze_dataset(D.load(name), lam=lam)
    s.update(source=name, lam=lam)
    return s


def step_job(spec):
    name, sf = spec
    pairs, s = analyze_dataset(D.load(name), step_frac=sf, methods=("greedy",))
    s.update(source=name, step_frac=sf)
    return s


def exact_k1(spec):
    name, hi, lo, fam = spec
    d = D.load(name)
    S = Searcher(d)
    th0 = S.fit0.theta
    n0 = S.tab.n0
    found = False
    tried = 0
    if fam == "drop":
        cands = [(t, -1) for t in np.where(n0 > 0)[0]]
    elif fam == "flip":
        cands = []
        for t in np.where(n0 > 0)[0]:
            p_ = S.tab.pair_id[t]
            for lab in S.labels:
                t2 = S.tab.lab_type[(int(p_), float(lab))]
                if t2 != t:
                    cands.append((t, t2))
    else:
        cands = [(-1, t) for t in range(S.T) if S.tab.base.y[t] in (0.0, 1.0)]
    for src, dst in cands:
        n = n0.copy()
        if src >= 0:
            n[src] -= 1
        if dst >= 0:
            n[dst] += 1
        f = S.fit(n, theta0=th0)
        tried += 1
        if f.theta[lo] > f.theta[hi]:
            found = True
            break
    return dict(source=name, hi=hi, lo=lo, family=fam, single_action_suffices=found, n_tried=tried)


if __name__ == "__main__":
    with Timer("e7"):
        with mp.Pool(NPROC) as p:
            ties = p.map(ties_job, ["arena55k", "arena140k", "mt_human", "mt_gpt4"])
            pd.DataFrame(ties).to_csv(f"{RES}/e7_ties.csv", index=False)
            lam = p.map(lam_job, [(n, l) for n in ("arena55k", "mt_human", "nba2015")
                                  for l in (1e-4, 1e-2, 1.0, 10.0)])
            pd.DataFrame(lam).to_csv(f"{RES}/e7_lambda.csv", index=False)
            st = p.map(step_job, [(n, sf) for n in ("arena55k", "mt_human", "nba2015", "mt_gpt4")
                                  for sf in (0.1, 0.5, 1.0)])
            pd.DataFrame(st).to_csv(f"{RES}/e7_step.csv", index=False)
            e1 = pd.read_csv(f"{RES}/e1_pairs.csv")
            name_map = {"Arena-55k": "arena55k", "Arena-140k": "arena140k", "MT-Bench-Human": "mt_human",
                        "MT-Bench-GPT4": "mt_gpt4"}
            specs = []
            for _, r in e1.iterrows():
                src = name_map.get(r.dataset, r.dataset.replace("NBA-", "nba"))
                for fam in ("drop", "flip", "add"):
                    if r[f"{fam}_best"] == 2:
                        specs.append((src, int(r.hi), int(r.lo), fam))
            print("exact k1 checks:", len(specs), flush=True)
            ex = p.map(exact_k1, specs, chunksize=1)
            pd.DataFrame(ex).to_csv(f"{RES}/e7_exact_k1.csv", index=False)
