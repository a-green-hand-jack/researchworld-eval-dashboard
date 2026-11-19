"""Cluster-level deletion on MT-Bench: the unit of deletion is a whole benchmark question (all judgments
of both turns / all judges).  Greedy first-order ranking of questions, refit, bisect (same scheme as bt.min_edits).
Writes results/cluster.csv"""
import numpy as np, pandas as pd
from bt import *
from cluster import min_clusters, votes_index
import datasets as ds

D = "/work/data"

def question_votes(which):
    if which == "mt_human":
        d = pd.read_parquet(f"{D}/mtbench/human-00000-of-00001-25f4910818759289.parquet")
        y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5}).values
        board = ds.mtbench_human()
    else:
        d = pd.read_parquet(f"{D}/mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet")
        y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (inconsistent)": 0.5}).values
        board = ds.mtbench_gpt4()
    idx = {s: k for k, s in enumerate(board.names)}
    ia = d.model_a.map(idx).values; ib = d.model_b.map(idx).values
    sw = ia > ib
    lo, hi = np.where(sw, ib, ia), np.where(sw, ia, ib); yy = np.where(sw, 1 - y, y)
    v_cfg, v_lab = votes_index(board, lo, hi, np.rint(yy * 2).astype(int))
    v_cl = pd.factorize(d.question_id.values)[0]
    return board, v_cfg, v_lab, v_cl

if __name__ == "__main__":
    rows = []
    for which in ("mt_human", "mt_gpt4"):
        board, v_cfg, v_lab, v_cl = question_votes(which); nq = int(v_cl.max()) + 1
        th = board.fit(); s = th[: board.m]
        for i in range(board.m):
            for j in range(board.m):
                if s[i] > s[j]:
                    se = board.ij_se(th, i, j); z = (s[i] - s[j]) / se
                    kq = min_clusters(board, v_cfg, v_lab, v_cl, i, j)
                    ks = min_clusters(board, v_cfg, v_lab, v_cl, i, j, zcrit=1.96) if z > 1.96 else np.nan
                    kv = min_edits(board, i, j, "drop", int(.3 * board.n), th0=th)["k"]
                    rows.append(dict(board=which, i=i, j=j, z=z, gap=s[i] - s[j], nq=nq, n=board.n,
                                     k_questions=kq, k_questions_sig=ks, k_votes=kv, ri=int((s > s[i]).sum())))
    pd.DataFrame(rows).to_csv("/work/results/cluster.csv", index=False)
    d = pd.DataFrame(rows); d["fq"] = d.k_questions / d.nq; d["fv"] = d.k_votes / d.n
    print(d.groupby("board")[["k_questions", "fq", "fv"]].median())
