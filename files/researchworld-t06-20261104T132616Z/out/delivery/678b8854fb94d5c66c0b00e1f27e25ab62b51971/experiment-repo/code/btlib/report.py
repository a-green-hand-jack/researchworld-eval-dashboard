"""Shared reporting routines: per-claim adversarial budget tables and random-perturbation tables for a Unit."""
import time

import numpy as np
import pandas as pd

from . import analysis as an, core

SEEDS = 200
B_BOOT = 1000
HEUR_SEEDS = 10
FRACS = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5]


def random_table(u, kinds=("remove", "flip"), fracs=FRACS, seeds=SEEDS, boot=B_BOOT):
    rows = []
    for kind in kinds:
        rows += an.run_random(u, kind, fracs, seeds, u.meta["has_ties"], base_seed=1)
    if boot:
        rows += an.run_random(u, "bootstrap", [1.0], boot, u.meta["has_ties"], base_seed=1)
    df = pd.DataFrame(rows)
    df.insert(1, "design", u.design)
    df["N"] = int(u.c.N)
    return df


def random_removal_shift(u, a, b, k, seeds=SEEDS, base_seed=3):
    """SD of the change in theta_a - theta_b, flip probability and mean shift under random removal of k comparisons."""
    c = u.c
    gaps = np.empty(seeds)
    for s in range(seeds):
        rng = np.random.default_rng([base_seed, a, b, k, s])
        x = core.fit(c.with_n(an.sample_remove(c, k, rng)), u.lam, u.lam_h, theta0=u.x0)
        gaps[s] = x[a] - x[b]
    g0 = u.x0[a] - u.x0[b]
    return float(np.std(gaps - g0, ddof=1)), float(np.mean(gaps <= 0)), float(np.mean(gaps - g0))


def adv_table(u, mode="remove", heur=True, rand=True, oneshot=True, boot=B_BOOT, window=None, seed=2, raw=True, pairs=None, prune=None):
    """Per-claim table. Budget = polished greedy search (verified upper bound); raw greedy / one-shot / heuristics for Q6."""
    c = u.c
    t0 = time.time()
    rows = an.budgets(u, mode, "greedy", window=window, pairs=pairs, prune=prune)
    rawd = {r["claim"]: r for r in an.budgets(u, mode, "greedy", window=window, do_polish=False, pairs=pairs, prune=prune)} if raw else {}
    ones = {r["claim"]: r for r in an.budgets(u, mode, "oneshot", window=window, pairs=pairs, prune=prune)} if oneshot else {}
    cnt = c.participant_counts()
    pair_tot = c.pair_totals()
    Bs = an.bootstrap_fits(u, boot, seed=seed) if boot else np.full((2, c.K), np.nan)
    names = {n: i for i, n in enumerate(c.names)}
    out = []
    for r in rows:
        a, b = names[r["a"]], names[r["b"]]
        r = dict(r)
        r["design"] = u.design
        r["N"] = int(c.N)
        r["K"] = c.K
        r["n_a"], r["n_b"] = int(cnt[a]), int(cnt[b])
        r["n_ab"] = int(pair_tot.get((min(a, b), max(a, b)), 0))
        r["n_a_or_b"] = int(cnt[a] + cnt[b] - r["n_ab"])
        r["se_gap"] = float(np.std(Bs[:, a] - Bs[:, b], ddof=1))
        r["z"] = r["gap"] / r["se_gap"]
        r["p_boot_pair_holds"] = float(np.mean(Bs[:, a] > Bs[:, b]))
        if raw:
            rr = rawd[r["claim"]]
            r["budget_greedy_raw"] = rr["budget"] if rr["flipped"] else np.nan
        if oneshot:
            o = ones[r["claim"]]
            r["budget_oneshot"] = o["budget"] if o["flipped"] else np.nan
        if rand and mode == "remove" and r["flipped"]:
            sd, pf, mean = random_removal_shift(u, a, b, int(r["budget"]))
            r["rand_shift_sd_at_k"], r["rand_flip_prob_at_k"], r["rand_shift_mean_at_k"] = sd, pf, mean
        if heur and mode == "remove" and r["claim"].startswith("c2"):
            for kind in ("direct", "own_wins"):
                ks = []
                for s in range(HEUR_SEEDS if kind == "own_wins" else 1):
                    k = core.heuristic_flip(c, a, b, kind, u.lam, u.lam_h, u.x0, np.random.default_rng([4, a, b, s]))
                    ks.append(np.nan if k is None else k)
                r[f"budget_heur_{kind}"] = float(np.nanmedian(ks)) if not np.all(np.isnan(ks)) else np.nan
        out.append(r)
    df = pd.DataFrame(out)
    df["seconds"] = time.time() - t0
    return df
