"""Stage 2 controls: synthetic BT data matched to each real dataset, N-matched subsampling, and the Arena 6-model subset.

Tasks (each yields a table of per-claim budgets via report.adv_table, written to results/parts2/):
  syn   <unit> rep      : SYNTHETIC data. Same pair-count matrix, same tie share per pair, outcomes drawn from the BT model
                          fitted to the real data (P(i wins)+0.5 P(tie) = sigmoid(theta_i - theta_j)). Never real data.
  sub   <unit> N rep    : uniform random subsample of N comparisons (without replacement) of the real data
  arena6                : Arena battles among the six models that also appear (as versions) in MT-Bench, full and N-matched
Usage: python code/s2_controls.py --tasks syn,sub,arena6 [--workers 2]"""
import argparse
import os
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an, core, data, prov, report, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
SYN_REPS = {"arena55k": 10, "mt_human": 20, "mt_gpt4": 20, "nba_all": 10}
NBA_SEASONS_SYN = [1950, 1960, 1970, 1980, 1990, 2000, 2010]  # seasons used for synthetic season controls
SYN_SEASON_REPS = 8
SUB_N = {"arena55k": [1367, 3355, 10000, 20000], "mt_human": [1000, 1367, 2400], "nba_all": [3355, 10000, 30000]}
SUB_REPS = 10
ARENA6 = ["gpt-4-0314", "claude-1", "gpt-3.5-turbo-0314", "vicuna-13b", "alpaca-13b", "llama-13b"]
BOOT = 200


def get_unit(name):
    if name == "arena55k":
        return units.arena_unit()[0]
    if name == "mt_human":
        return units.mt_unit("human")[0]
    if name == "mt_gpt4":
        return units.mt_unit("gpt4")[0]
    if name == "nba_all":
        return units.nba_all_unit()[0]
    if name.startswith("nba") and name[3:].isdigit():
        return units.nba_season_unit(data.load_nba(), int(name[3:]))[0]
    raise KeyError(name)


def synthetic_counts(u, rng):
    c = u.c
    N_p = c.n.sum(1)
    tie = np.divide(c.n[:, 1], N_p, out=np.zeros(c.P), where=N_p > 0)
    d = c.V @ u.x0
    pw = np.clip(core.sigmoid(d) - tie / 2, 0.0, 1 - tie)
    probs = np.stack([pw, tie, 1 - tie - pw], 1)
    probs /= probs.sum(1, keepdims=True)
    n = np.stack([rng.multinomial(int(N_p[p]), probs[p]) for p in range(c.P)]).astype(float)
    return n


def run_task(t):
    kind, name, par, rep = t
    rng = np.random.default_rng([11, zlib.crc32(f"{kind}|{name}|{par}".encode()), rep])
    if kind == "arena6":
        ds = data.load_arena55k()
        idx = [ds.names.index(m) for m in ARENA6]
        m = np.isin(ds.i, idx) & np.isin(ds.j, idx)
        d6 = ds.subset(m, "arena6")
        remap = {k: n for n, k in enumerate(idx)}
        d6.i = np.array([remap[v] for v in d6.i]); d6.j = np.array([remap[v] for v in d6.j]); d6.names = ARENA6
        if par:  # N-matched subsample
            sel = rng.choice(len(d6), par, replace=False)
            d6 = d6.subset(np.isin(np.arange(len(d6)), sel))
        u = an.Unit(f"arena6_N{par or len(d6)}_r{rep}", "crowd", d6.counts(), None, meta=dict(has_ties=True))
        label = dict(kind="arena6", base="arena55k", N_target=par or int(u.c.N), rep=rep)
    else:
        base = get_unit(name)
        if kind == "syn":
            c = base.c.with_n(synthetic_counts(base, rng))
            u = an.Unit(f"syn_{name}_r{rep}", "synthetic", c, base.elig, meta=base.meta, window=base.window)
            label = dict(kind="syn", base=name, N_target=int(base.c.N), rep=rep, base_design=base.design)
        else:
            N = par
            flat = np.repeat(np.arange(base.c.P * 3), base.c.n.ravel().astype(int))
            pick = rng.choice(flat, N, replace=False)
            n = np.bincount(pick, minlength=base.c.P * 3).astype(float).reshape(-1, 3)
            c = base.c.with_n(n)
            elig = np.argsort(-c.participant_counts(), kind="stable")[: len(base.elig)] if base.E < base.c.K else None
            u = an.Unit(f"sub_{name}_N{N}_r{rep}", base.design, c, elig, meta=base.meta, window=base.window)
            label = dict(kind="sub", base=name, N_target=N, rep=rep, base_design=base.design)
    t = report.adv_table(u, heur=False, rand=False, oneshot=False, boot=BOOT, raw=False, prune=10.0)
    for k, v in label.items():
        t[k] = v
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="syn,sub,arena6")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    tasks = []
    for k in a.tasks.split(","):
        if k == "syn":
            tasks += [("syn", n, 0, r) for n, R in SYN_REPS.items() for r in range(R)]
            tasks += [("syn", f"nba{y}", 0, r) for y in NBA_SEASONS_SYN for r in range(SYN_SEASON_REPS)]
        elif k == "sub":
            tasks += [("sub", n, N, r) for n, Ns in SUB_N.items() for N in Ns for r in range(SUB_REPS)]
        elif k == "arena6":
            tasks += [("arena6", "arena55k", 0, 0)] + [("arena6", "arena55k", N, r) for N in (1367 // 2, 700) for r in range(SUB_REPS)]
    os.makedirs(f"{OUT}/parts2", exist_ok=True)
    out = []
    with ProcessPoolExecutor(a.workers) as ex:
        for i, t in enumerate(ex.map(run_task, tasks)):
            out.append(t)
            if i % 10 == 0:
                print(i, len(tasks), flush=True)
    df = pd.concat(out, ignore_index=True)
    df.to_csv(f"{OUT}/s2_controls_{a.tasks.replace(',', '_')}.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s2_controls_{a.tasks.replace(',', '_')}.meta.json", script="code/s2_controls.py", args=vars(a),
                    note="rows with kind=syn are SYNTHETIC data", boot=BOOT, syn_reps=SYN_REPS, sub_n=SUB_N)


if __name__ == "__main__":
    main()
