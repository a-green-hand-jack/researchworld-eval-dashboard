"""E0-E3: main experiments on the three public boards.
  E0  who wins under each rule; rule agreement (Kendall tau)
  E1  contenders (mean-rank 2..11): minimal depth/breadth to be #1 under each rule, ceiling cap and gain caps
  E2  cost vs. starting rank under each rule (ceiling cap)
Outputs: results/e0_winners.csv, e0_kendall_<board>.csv, e1_contenders.csv, e2_rank_sweep.csv
Usage: python code/run_main.py [board ...]
"""
import os, sys, itertools
import numpy as np, pandas as pd
from multiprocessing import Pool
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lb import agg, boards, runner

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(OUT, exist_ok=True)
RULES = agg.ALL_RULES
B = {}


def job_e1(args):
    bname, scenario = args
    S = B[bname].S
    rows = runner.contender_costs(S, RULES, scenario, 10)
    for r in rows:
        r.update(board=bname, scenario=str(scenario))
    return rows


RANK_GRID = [2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 100, 200, 500, 1000]


def job_e2(args):
    bname, rule = args
    S = B[bname].S
    n = S.shape[0]
    order, v = runner.rule_rank_order(rule, S)
    fv = v if rule in agg.SCORE_RULES else None
    rows = []
    for rk in RANK_GRID:
        if rk > n or (rule in ("borda", "plural") and rk > 200) or rule == "plural":
            continue
        t = int(order[rk - 1])
        # skip targets that tie the leader (cost 0 by convention) only for reporting: still included
        c = runner.one_cost(rule, S, t, "ceil", fv)
        rows.append(dict(board=bname, rule=rule, rule_rank=rk, target=t, l1=c["l1"], br=c["br"],
                         l1_lb=c.get("l1_lb", c["l1"]), br_lb=c.get("br_lb", c["br"])))
    return rows


if __name__ == "__main__":
    names = sys.argv[1:] or boards.BOARDS
    for nm in names:
        B[nm] = boards.load(nm)
    # ---------------- E0
    win_rows = []
    for nm in names:
        b = B[nm]
        order_mean = runner.mean_rank_order(b.S)
        ranks = {}
        for rule in RULES:
            order, v = runner.rule_rank_order(rule, b.S)
            ranks[rule] = pd.Series(np.argsort(order), dtype=float)  # rank position per model (0 = best)
            win_rows.append(dict(board=nm, rule=rule, n=b.n, m=b.m, winner=b.models[order[0]], winner_value=float(v[order[0]]),
                                 second=b.models[order[1]], second_value=float(v[order[1]]),
                                 mean_rank_of_winner=int(np.where(order_mean == order[0])[0][0]) + 1))
        K = pd.DataFrame(index=RULES, columns=RULES, dtype=float)
        top = order_mean[: min(b.n, 200)]
        for r1, r2 in itertools.product(RULES, RULES):
            if r1 == r2:
                K.loc[r1, r2] = 1.0
            else:
                K.loc[r1, r2] = kendalltau(ranks[r1].values[top], ranks[r2].values[top])[0]
        K.to_csv(os.path.join(OUT, f"e0_kendall_{nm}.csv"))
    pd.DataFrame(win_rows).to_csv(os.path.join(OUT, "e0_winners.csv"), index=False)
    print("E0 done", flush=True)
    # ---------------- E1
    jobs = [(nm, sc) for nm in names for sc in ["ceil"] + runner.G_GRID]
    with Pool(32) as pool:
        res = pool.map(job_e1, jobs, chunksize=1)
    df = pd.DataFrame([r for rows in res for r in rows])
    df["model"] = [B[b].models[t] for b, t in zip(df.board, df.target)]
    df.to_csv(os.path.join(OUT, "e1_contenders.csv"), index=False)
    print("E1 done", len(df), flush=True)
    # ---------------- E2
    jobs = [(nm, r) for nm in names for r in RULES]
    with Pool(32) as pool:
        res = pool.map(job_e2, jobs, chunksize=1)
    pd.DataFrame([r for rows in res for r in rows]).to_csv(os.path.join(OUT, "e2_rank_sweep.csv"), index=False)
    print("E2 done", flush=True)
