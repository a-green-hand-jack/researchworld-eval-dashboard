"""Dataset registry and shared helpers."""
import glob
import os

import numpy as np
import pandas as pd

from bt import BT, Data, Target, greedy, ranking

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)

LAM = 1e-3  # ridge penalty (ablation in exp_ablation.py)
TOP1_CHALLENGERS = 10  # top-1 change = min over challengers at ranks 2..11

# name -> (design category, display label)
DATASETS = {
    "arena55k": ("crowd", "Arena-55k (human)"),
    "arena55k_singleturn_human": ("crowd", "Arena-55k single-turn (human)"),
    "arena140k": ("crowd", "Arena-140k (human)"),
    "webdev": ("crowd", "WebDev Arena (human)"),
    "mtbench_human": ("expert", "MT-Bench (experts)"),
    "mtbench_gpt4": ("llm-judge", "MT-Bench (GPT-4 judge)"),
    "judge_Qwen2-72B-Instruct": ("llm-judge", "Arena battles, Qwen2-72B judge"),
    "judge_Meta-Llama-3-70B-Instruct": ("llm-judge", "Arena battles, Llama-3-70B judge"),
    "judge_Athene-70B": ("llm-judge", "Arena battles, Athene-70B judge"),
    "judge_Meta-Llama-3-8B-Instruct": ("llm-judge", "Arena battles, Llama-3-8B judge"),
}
RAW_JUDGES = ["judgeraw_Qwen2-72B-Instruct", "judgeraw_Meta-Llama-3-70B-Instruct",
              "judgeraw_Athene-70B", "judgeraw_Meta-Llama-3-8B-Instruct"]


def nba_seasons():
    fs = sorted(glob.glob(os.path.join(PROC, "nba", "nba_*.csv")))
    return [os.path.basename(f)[:-4] for f in fs]


def category(name):
    if name.startswith("nba_"):
        return "sports"
    if name.startswith("judgeraw_"):
        return "llm-judge"
    return DATASETS[name][0]


def load_df(name):
    if name.startswith("nba_"):
        return pd.read_csv(os.path.join(PROC, "nba", name + ".csv"))
    return pd.read_csv(os.path.join(PROC, name + ".csv"))


def load(name, lam=LAM, all_pairs=False, df=None):
    df = load_df(name) if df is None else df
    d = Data(df, all_pairs=all_pairs)
    return d, BT(d, lam=lam)


def top1_drop(model, mode="drop", n_chal=TOP1_CHALLENGERS, C0=None):
    """Minimal (greedy) perturbation that changes the rank-1 competitor.

    Exact decomposition: the top changes iff some challenger c overtakes the leader,
    so m_top1 = min_c m(leader, c).  We search challengers at ranks 2..n_chal+1; the greedy
    search for later challengers is abandoned once it exceeds 2x the best value so far."""
    d = model.d
    th, _, _ = model.fit(d.C if C0 is None else C0)
    r = ranking(th, d.K)
    best, best_c = np.inf, None
    for c in r[1:n_chal + 1]:
        res = greedy(model, Target("pair", r[0], c), mode=mode, C0=C0, th0=th,
                     budget=None if not np.isfinite(best) else 2 * best + 10)
        if res["m"] < best:
            best, best_c = res["m"], c
    return best, r[0], best_c
