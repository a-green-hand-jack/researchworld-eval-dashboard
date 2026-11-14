"""Stage 1: random perturbation survival curves and adversarial flip budgets for every unit.

Usage: python code/s1_run.py --what random|adv [--units arena55k,mt_human,mt_gpt4,nba_all,nba_seasons]
Writes results/s1_<what>_<unit>.csv (per-unit parts; concatenated by s2_collect.py)."""
import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import data, prov, report, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def build(name):
    if name == "arena55k":
        return units.arena_unit()[0]
    if name == "arena55k_top20count":
        return units.arena_unit(by_count=True)[0]
    if name == "nba_all_top20count":
        return units.nba_all_unit(by_count=True)[0]
    if name == "mt_human":
        return units.mt_unit("human")[0]
    if name == "mt_gpt4":
        return units.mt_unit("gpt4")[0]
    if name == "nba_all":
        return units.nba_all_unit()[0]
    if name.startswith("nba") and name[3:].isdigit():
        nba = data.load_nba()
        return units.nba_season_unit(nba, int(name[3:]))[0]
    raise KeyError(name)


def do_random(name):
    return report.random_table(build(name))


def do_adv(name):
    return report.adv_table(build(name))


def work(args):
    what, name = args
    df = do_random(name) if what == "random" else do_adv(name)
    df.to_csv(os.path.join(OUT, "parts", f"s1_{what}_{name}.csv"), index=False, float_format="%.6g")
    return name, len(df)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", required=True, choices=["random", "adv"])
    ap.add_argument("--units", default="arena55k,mt_human,mt_gpt4,nba_all")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
    names = []
    for u in a.units.split(","):
        if u == "nba_seasons":
            nba = data.load_nba()
            names += [f"nba{y}" for y in sorted(set(nba.season))]
        else:
            names.append(u)
    with ProcessPoolExecutor(a.workers) as ex:
        for n, m in ex.map(work, [(a.what, n) for n in names]):
            print(n, m, flush=True)
    prov.write_meta(os.path.join(OUT, f"s1_{a.what}.meta.json"), script="code/s1_run.py", args=vars(a), seeds=report.SEEDS,
                    fracs=report.FRACS, bootstrap_B=report.B_BOOT, heuristic_seeds=report.HEUR_SEEDS)


if __name__ == "__main__":
    main()
