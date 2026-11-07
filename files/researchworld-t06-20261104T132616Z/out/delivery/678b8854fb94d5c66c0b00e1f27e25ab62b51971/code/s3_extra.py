"""Stage 3: adversarial additions / relabelling (rigging), modelling-choice ablations, budget uncertainty by resampling.

  --what rigging   : mode add and relabel budgets for the base units and every NBA season   -> results/s3_rigging.csv
  --what ablation  : lam, tie handling, eligible set, home advantage, playoffs               -> results/s3_ablations.csv
  --what uncert    : budgets recomputed on B dataset-bootstrap resamples                      -> results/s3_uncert.csv
Usage: python code/s3_extra.py --what rigging|ablation|uncert [--workers 2]"""
import argparse
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an, data, prov, report, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
BOOT = 200
UNC_B = {"arena55k": 100, "mt_human": 200, "mt_gpt4": 200, "nba_all": 100}
UNC_SEASONS = [1950, 1960, 1970, 1980, 1990, 2000, 2010]
UNC_SEASON_B = 100
PRUNE = 10.0  # secondary analyses: skip candidate pairs whose linearised estimate exceeds 10x the best verified budget of the claim


def base_unit(name):
    from s2_controls import get_unit
    return get_unit(name)


def rigging_task(name):
    u = base_unit(name)
    out = []
    for mode in ("add", "relabel"):
        t = report.adv_table(u, mode=mode, heur=False, rand=False, oneshot=False, boot=BOOT, raw=False, prune=PRUNE)
        out.append(t)
    return pd.concat(out)


def ablation_task(spec):
    """spec = (variant, kind, kwargs) -> table"""
    variant, kind, kw = spec
    if kind == "arena":
        u = units.arena_unit(**kw)[0]
    elif kind == "arena_thr":
        ds = data.load_arena55k()
        c = ds.counts()
        elig = np.where(c.participant_counts() >= kw["thr"])[0]
        u = an.Unit("arena55k", "crowd", c, elig, meta=dict(has_ties=True))
    elif kind == "mt":
        u = units.mt_unit(**kw)[0]
    elif kind == "nba_all":
        u = units.nba_all_unit(**kw)[0]
    elif kind == "nba_season":
        nba = data.load_nba(playoffs=kw.pop("playoffs", False))
        u = units.nba_season_unit(nba, kw.pop("year"), **kw)[0]
    t = report.adv_table(u, heur=False, rand=False, oneshot=False, boot=BOOT, raw=False, prune=PRUNE)
    t.insert(0, "variant", variant)
    return t


def uncert_task(args):
    name, b = args
    u0 = base_unit(name)
    rng = np.random.default_rng([21, sum(map(ord, name)), b])
    c = u0.c.with_n(an.sample_bootstrap(u0.c, rng))
    u = an.Unit(name, u0.design, c, u0.elig, meta=u0.meta, window=u0.window)
    t = report.adv_table(u, heur=False, rand=False, oneshot=False, boot=0, raw=False, window=3, prune=PRUNE)
    t["resample"] = b
    t["unit_base"] = name
    return t[["unit_base", "resample", "claim", "a", "b", "gap", "budget", "flipped", "N", "design"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", required=True, choices=["rigging", "ablation", "uncert"])
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    nba = data.load_nba()
    seasons = sorted(set(nba.season))
    if a.what == "rigging":
        names = ["arena55k", "mt_human", "mt_gpt4", "nba_all"] + [f"nba{y}" for y in seasons]
        fn, tasks = rigging_task, names
    elif a.what == "ablation":
        fn = ablation_task
        tasks = []
        for lam in (0.01, 100.0):
            tasks += [(f"lam={lam}", "arena", dict(lam=lam)), (f"lam={lam}", "mt", dict(kind="human", lam=lam)),
                      (f"lam={lam}", "mt", dict(kind="gpt4", lam=lam)), (f"lam={lam}", "nba_all", dict(lam=lam))]
        tasks += [("drop_ties", "arena", dict(drop_ties=True)), ("drop_ties", "mt", dict(kind="human", drop_ties=True)),
                  ("drop_ties", "mt", dict(kind="gpt4", drop_ties=True)),
                  ("elig=all64", "arena", dict(top=None)), ("elig=n>=1000", "arena_thr", dict(thr=1000)),
                  ("claims=top20_by_count", "arena", dict(by_count=True)), ("claims=top20_by_count", "nba_all", dict(by_count=True)),
                  ("claims=top10", "arena", dict(top=10)),
                  ("home_param", "nba_all", dict(home=True))]
        for y in seasons:
            tasks += [("home_param", "nba_season", dict(year=int(y), home=True))]
            tasks += [("playoffs_incl", "nba_season", dict(year=int(y), playoffs=True))]
    else:
        fn = uncert_task
        tasks = [(n, b) for n, B in UNC_B.items() for b in range(B)] + [(f"nba{y}", b) for y in UNC_SEASONS for b in range(UNC_SEASON_B)]
    with ProcessPoolExecutor(a.workers) as ex:
        res = []
        for i, t in enumerate(ex.map(fn, tasks, chunksize=1)):
            res.append(t)
            if i % 20 == 0:
                print(i, len(tasks), flush=True)
    pd.concat(res, ignore_index=True).to_csv(f"{OUT}/s3_{ {'rigging': 'rigging', 'ablation': 'ablations', 'uncert': 'uncert'}[a.what]}.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s3_{a.what}.meta.json", script="code/s3_extra.py", args=vars(a), boot=BOOT)


if __name__ == "__main__":
    main()
