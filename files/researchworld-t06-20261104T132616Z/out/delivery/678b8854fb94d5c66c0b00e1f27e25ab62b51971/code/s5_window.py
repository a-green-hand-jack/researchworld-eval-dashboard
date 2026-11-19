"""Claim-window sweep, the reason for the 20-participant window and the era overlap of the pooled NBA fit (internal-review #6 scope addition by paper-repo).

Window rules for Arena (64 models) and pooled NBA (53 franchises):
  score_w  : the top-w ranks of the base fit (w = 10, 20, 30, 40, all). C2 (adjacent pairs) and C3_k (k <= w-2) concern those ranks; the challengers of C1 and C3
             are ALL participants, so C1 and every claim pair is the same pair as in the all-participant run and the sweep is read from ONE run of the
             all-participant unit (C2_r and C3_k do not depend on w; only the set of claims entering the median does).
  count_n  : the n participants with the most comparisons (n = 10, 20, 30, 40), the challengers and the claims restricted to them (own run).
Budgets are polished greedy removal budgets with pruning factor 10 (as the other secondary analyses; the primary set of the headline table is unpruned).
Support descriptors (share of comparisons inside the window, direct comparisons between adjacent pairs, comparisons of the least-compared member) justify w = 20.
Pooled NBA: franchise first / last season, pairs that were never contemporaries, direct games between the window franchises.
Writes results/s5_window_budgets.csv, s5_window_sweep.csv, s5_window_support.csv, s5_nba_eras.csv, s5_nba_eras_pairs.csv.
Usage: python code/s5_window.py --part score|count|support"""
import argparse
import os

import numpy as np
import pandas as pd

from btlib import analysis as an, data, prov, report, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
SIZES = [10, 20, 30, 40]


def make(ds_name, kind, n=None):
    if ds_name == "arena55k":
        u, ds = units.arena_unit(top=n, by_count=(kind == "count"), name=f"arena55k_{kind}{n or 'all'}")
    else:
        u, ds = units.nba_all_unit(top=n, by_count=(kind == "count"))
        u.name = f"nba_all_{kind}{n or 'all'}"
    return u, ds


def run(ds_name, kind, n):
    u, _ = make(ds_name, kind, n)
    t = report.adv_table(u, heur=False, rand=False, oneshot=False, boot=0, raw=False, prune=10.0)
    t["dataset"], t["rule"], t["size"] = ds_name, kind, n if n else u.E
    return t


def sweep(budgets):
    rows = []
    for (ds, rule, size), g in budgets.groupby(["dataset", "rule", "size"]):
        pass
    for ds in budgets.dataset.unique():
        full = budgets[(budgets.dataset == ds) & (budgets.rule == "score") & (budgets["size"] == budgets[(budgets.dataset == ds) & (budgets.rule == "score")]["size"].max())]
        N = full.N.iloc[0]
        c2 = full[full.claim.str.startswith("c2_")].copy()
        c2["r"] = c2.claim.str[3:].astype(int)
        for w in SIZES + ["all"]:
            wi = int(full["size"].max()) if w == "all" else w
            s = c2[c2.r < wi - 1]
            c3 = full[full.claim.str.startswith("c3_")]
            c3 = c3[c3.claim.str[3:].astype(int) <= wi - 2]
            rows.append(dict(dataset=ds, rule="score", size=wi, c1=full[full.claim == "c1"].budget.iloc[0], n_c2=len(s), median_c2=s.budget.median(),
                             q25_c2=s.budget.quantile(0.25), q75_c2=s.budget.quantile(0.75), min_c2=s.budget.min(),
                             **{f"c3_{int(k.split('_')[1])}": v for k, v in zip(c3.claim, c3.budget)}, N=N, median_c2_frac_N=s.budget.median() / N))
        for n in SIZES:
            g = budgets[(budgets.dataset == ds) & (budgets.rule == "count") & (budgets["size"] == n)]
            if not len(g):
                continue
            c2 = g[g.claim.str.startswith("c2_")]
            c3 = g[g.claim.str.startswith("c3_")]
            rows.append(dict(dataset=ds, rule="count", size=n, c1=g[g.claim == "c1"].budget.iloc[0], n_c2=len(c2), median_c2=c2.budget.median(),
                             q25_c2=c2.budget.quantile(0.25), q75_c2=c2.budget.quantile(0.75), min_c2=c2.budget.min(),
                             **{k: v for k, v in zip(c3.claim, c3.budget)}, N=N, median_c2_frac_N=c2.budget.median() / N))
    return pd.DataFrame(rows)


def support():
    rows = []
    for ds_name in ("arena55k", "nba_all"):
        u, _ = make(ds_name, "score", None)
        c = u.c
        cnt = c.participant_counts()
        pt = c.pair_totals()
        tot = c.N
        by_score = list(u.order)
        by_count = list(np.argsort(-cnt, kind="stable"))
        for rule, order in (("score", by_score), ("count", by_count)):
            for n in SIZES + [len(order)]:
                mem = order[:n]
                inside = sum(v for (a, b), v in pt.items() if a in mem and b in mem)
                touch = sum(v for (a, b), v in pt.items() if a in mem or b in mem)
                srt = [m for m in by_score if m in mem]  # adjacent pairs in score order inside the window
                adj = [(min(srt[k], srt[k + 1]), max(srt[k], srt[k + 1])) for k in range(len(srt) - 1)]
                direct = np.array([pt.get(p, 0) for p in adj])
                rows.append(dict(dataset=ds_name, rule=rule, size=n, members_min_comparisons=int(cnt[mem].min()), members_median_comparisons=float(np.median(cnt[mem])),
                                 share_comparisons_both_inside=inside / tot, share_comparisons_touching=touch / tot,
                                 adjacent_pairs=len(adj), adjacent_pairs_ge100_direct=int((direct >= 100).sum()), adjacent_pairs_min_direct=int(direct.min()) if len(direct) else 0,
                                 members_lt200=int((cnt[mem] < 200).sum()), members_lt1000=int((cnt[mem] < 1000).sum())))
    pd.DataFrame(rows).to_csv(f"{OUT}/s5_window_support.csv", index=False, float_format="%.5g")
    # --- pooled NBA: eras
    nba = data.load_nba()
    seas = pd.DataFrame(dict(i=nba.i, j=nba.j, s=nba.season))
    long = pd.concat([seas.rename(columns={"i": "t"})[["t", "s"]], seas.rename(columns={"j": "t"})[["t", "s"]]])
    span = long.groupby("t").s.agg(first="min", last="max", seasons="nunique", games="size")
    span["franchise"] = [nba.names[k] for k in span.index]
    u, _ = make("nba_all", "score", None)
    rank = {m: r + 1 for r, m in enumerate(u.order)}
    span["rank_base_fit"] = [rank[k] for k in span.index]
    span["score_elo"] = [u.x0[k] * 400 / np.log(10) for k in span.index]
    span.sort_values("rank_base_fit").to_csv(f"{OUT}/s5_nba_eras.csv", index=False, float_format="%.5g")
    teams = list(span.index)
    act = {t: set(long[long.t == t].s.unique()) for t in teams}
    pt = u.c.pair_totals()
    pr = []
    for x in range(len(teams)):
        for y in range(x + 1, len(teams)):
            a, b = teams[x], teams[y]
            pr.append(dict(a=nba.names[a], b=nba.names[b], common_seasons=len(act[a] & act[b]), direct_games=pt.get((min(a, b), max(a, b)), 0),
                           span_overlap_years=max(0, min(span.loc[a, "last"], span.loc[b, "last"]) - max(span.loc[a, "first"], span.loc[b, "first"]) + 1),
                           in_top20_both=bool(rank[a] <= 20 and rank[b] <= 20)))
    pr = pd.DataFrame(pr)
    pr.to_csv(f"{OUT}/s5_nba_eras_pairs.csv", index=False)
    return pr, span


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="score")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(f"{OUT}/parts", exist_ok=True)
    if a.part == "support":
        pr, span = support()
        print(pr.describe().T, span.describe().T)
    elif a.part in ("score", "count"):
        from concurrent.futures import ProcessPoolExecutor
        tasks = [(d, a.part, None if a.part == "score" else n) for d in ("arena55k", "nba_all") for n in ([None] if a.part == "score" else SIZES)]
        with ProcessPoolExecutor(a.workers) as ex:
            res = list(ex.map(run, *zip(*tasks)))
        pd.concat(res, ignore_index=True).to_csv(f"{OUT}/parts/s5_window_{a.part}.csv", index=False, float_format="%.6g")
        prov.write_meta(f"{OUT}/parts/s5_window_{a.part}.meta.json", script="code/s5_window.py", part=a.part)
    else:  # merge
        b = pd.concat([pd.read_csv(f"{OUT}/parts/s5_window_{p}.csv") for p in ("score", "count")], ignore_index=True)
        b.drop(columns=["lin_est", "steps", "mode", "strategy"], errors="ignore").to_csv(f"{OUT}/s5_window_budgets.csv", index=False, float_format="%.6g")
        sweep(b).to_csv(f"{OUT}/s5_window_sweep.csv", index=False, float_format="%.5g")


if __name__ == "__main__":
    main()
