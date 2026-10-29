"""Shared helpers for the experiment scripts."""
import copy
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bt import Board, min_perturbation, first_order_k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DER = os.path.join(ROOT, "derived")
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figs")

MAIN_BOARDS = ["arena55k", "arena140k", "webdev", "mtbench_human", "mtbench_gpt4", "arena55k_mt6",
               "arenaJ_crowd", "arenaJ_Athene-70B", "arenaJ_Meta-Llama-3-70B-Instruct",
               "arenaJ_Meta-Llama-3-8B-Instruct", "arenaJ_Mistral-7B-Instruct-v0.1",
               "arenaJ_Qwen2-72B-Instruct"]
NBA_RECENT = [f"nba_{y}" for y in range(2005, 2016)]


def load_board(name):
    base = name.replace("__noties", "")
    df = pd.read_parquet(os.path.join(DER, base + ".parquet"))
    if name.endswith("__noties"):
        from data_prep import filter_min
        df = filter_min(df[df.y != 0.5])
    return Board(df)


def with_weights(board, W):
    b = copy.copy(board)
    b.W0 = W
    b.N = int(W.sum())
    return b


def best_k(board, i, j, mode):
    """Best verified perturbation size: min of iterated greedy and refit-checked one-shot."""
    r = min_perturbation(board, i, j, mode)
    fo = first_order_k(board, i, j, mode)
    ks = [x for x in (r["k"] if r["verified"] else None, fo.get("k_os")) if x is not None]
    return min(ks) if ks else None


def top1_k(board, mode, th=None, n_chall=5):
    """Smallest perturbation that changes the identity of the top-ranked competitor."""
    if th is None:
        th = board.fit()[0]
    r = board.ranking(th)
    ks = [best_k(board, r[0], r[j], mode) for j in range(1, min(n_chall + 1, board.K))]
    ks = [k for k in ks if k is not None]
    return min(ks) if ks else None


def resample_weights(board, rng):
    """Nonparametric bootstrap over comparisons, expressed as a new weight table."""
    W = np.zeros_like(board.W0)
    cnt = rng.multinomial(board.N, board.W0.ravel() / board.N)
    return cnt.reshape(board.W0.shape).astype(float)
