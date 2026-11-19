"""Cluster / block bootstrap SE and z for every claim pair of results/budgets_remove.csv (paper-repo request #7).

Clusters: MT-Bench (human, GPT-4): the question (80, shared by all model pairs); Arena 55k: identical prompt text (the released file has no user
or conversation id; 3,118 prompts occur more than once); NBA seasons: 7-day weeks of the season (block bootstrap); NBA pooled: season.
B = 1000 cluster-bootstrap refits per unit; se_gap_cluster = SD of theta_a - theta_b over them. Writes results/s5_cluster_se.csv.
Usage: python code/s5_cluster.py"""
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import cluster, data, prov, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
B = 1000
KIND = {"arena55k": "prompt", "arena55k_top20count": "prompt", "mt_human": "question", "mt_gpt4": "question", "nba_all": "season", "nba_all_top20count": "season"}


def build(name):
    if name.startswith("arena55k"):
        ds = data.load_arena55k()
        return units.arena_unit(ds=ds, by_count=name.endswith("count"))[0], ds
    if name in ("mt_human", "mt_gpt4"):
        return units.mt_unit(name[3:])[0:2]
    if name.startswith("nba_all"):
        nba = data.load_nba()
        return units.nba_all_unit(nba=nba, by_count=name.endswith("count"))[0], nba
    nba = data.load_nba()
    return units.nba_season_unit(nba, int(name[3:]))


def work(args):
    name, rows = args
    u, ds = build(name)
    Bs = cluster.cluster_bootstrap_fits(u, ds, B, seed=3)
    names = {n: i for i, n in enumerate(u.c.names)}
    kind = KIND.get(name, "week")
    ncl = len(np.unique(ds.cluster))
    out = []
    for r in rows.itertuples():
        a, b = names[r.a], names[r.b]
        se = float(np.std(Bs[:, a] - Bs[:, b], ddof=1))
        out.append(dict(unit=name, claim=r.claim, a=r.a, b=r.b, gap=r.gap, se_gap_iid=r.se_gap, se_gap_cluster=se, z_iid=r.z, z_cluster=r.gap / se,
                        p_cluster_pair_holds=float(np.mean(Bs[:, a] > Bs[:, b])), n_clusters=ncl, cluster_type=kind))
    return pd.DataFrame(out)


def main():
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    tasks = [(n, g) for n, g in d.groupby("unit", sort=False)]
    with ProcessPoolExecutor(2) as ex:
        res = list(ex.map(work, tasks, chunksize=1))
    pd.concat(res, ignore_index=True).to_csv(f"{OUT}/s5_cluster_se.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s5_cluster.meta.json", script="code/s5_cluster.py", B=B)


if __name__ == "__main__":
    main()
