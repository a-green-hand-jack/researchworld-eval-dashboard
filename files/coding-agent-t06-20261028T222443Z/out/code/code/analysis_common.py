"""Shared loading / labelling for the analysis (tables & figures)."""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figs")
TAB = os.path.join(ROOT, "paper", "tables")

LABEL = {
    "arena55k": "Arena-55k", "arena140k": "Arena-140k", "webdev": "WebDev Arena",
    "mtbench_human": "MT-Bench (expert)", "mtbench_gpt4": "MT-Bench (GPT-4 judge)",
    "arena55k_mt6": "Arena-55k, MT-Bench 6 models",
    "arenaJ_crowd": "Arena-50k single-turn (crowd)",
    "arenaJ_Athene-70B": "Arena-50k: Athene-70B judge",
    "arenaJ_Meta-Llama-3-70B-Instruct": "Arena-50k: Llama-3-70B judge",
    "arenaJ_Meta-Llama-3-8B-Instruct": "Arena-50k: Llama-3-8B judge",
    "arenaJ_Mistral-7B-Instruct-v0.1": "Arena-50k: Mistral-7B judge",
    "arenaJ_Qwen2-72B-Instruct": "Arena-50k: Qwen2-72B judge",
}
DESIGN_ORDER = ["crowd", "expert", "llm_judge", "sports"]
DESIGN_LABEL = {"crowd": "Crowd vote", "expert": "Expert", "llm_judge": "LLM judge", "sports": "Sports (NBA)"}


def design(b):
    b = b.replace("__noties", "")
    if b.startswith("nba"):
        return "sports"
    if b == "mtbench_human":
        return "expert"
    if b == "mtbench_gpt4" or (b.startswith("arenaJ") and b != "arenaJ_crowd"):
        return "llm_judge"
    return "crowd"


def label(b):
    if b.startswith("nba_"):
        return "NBA " + str(int(b[4:]) - 1) + "/" + b[6:].replace("__noties", "")
    s = LABEL.get(b.replace("__noties", ""), b)
    return s + (" (no ties)" if b.endswith("__noties") else "")


def load_pairs():
    d = pd.read_parquet(os.path.join(RES, "pairs.parquet"))
    I = pd.read_parquet(os.path.join(RES, "pair_influence.parquet"))
    d = d.sort_values(["board", "mode", "ri", "rj"]).reset_index(drop=True)  # deterministic tie-breaking
    d["kb"] = d[["k", "k_os"]].min(axis=1)  # best verified perturbation (both are refit-verified)
    d = d.merge(I, on=["board", "ri", "rj"], suffixes=("", "_inf"))
    d["design"] = d.board.map(design)
    d["noties"] = d.board.str.endswith("__noties")
    d["alpha"] = d.kb / d.N
    d["Rm"] = np.where(d["mode"] == "drop", d.R, np.where(d["mode"] == "flip", d.R_flip, d.R_add))
    d["pred"] = d.z_ij * d.Rm
    d["ratio"] = d.kb / d.pred
    return d


def outcome_table(d):
    """Per board & mode: top-1 change, top-3 set change, any adjacent change (min over pairs)."""
    rows = []
    for (b, m), g in d.groupby(["board", "mode"]):
        top1 = g[g.ri == 1]
        top1 = top1.loc[top1.kb.idxmin()]
        t3 = g[(g.ri <= 3) & (g.rj >= 4)]
        t3 = t3.loc[t3.kb.idxmin()] if len(t3) else None
        adj = g[g.rj == g.ri + 1]
        top10adj = adj[adj.ri < 10]
        rows.append(dict(board=b, mode=m, N=int(g.N.iloc[0]), K=int(g.K.iloc[0]), design=design(b),
                         k_top1=top1.kb, j_top1=int(top1.rj), z_top1=top1.z_ij, R_top1=top1.Rm,
                         nloc_top1=top1.n_loc,
                         k_top3=None if t3 is None else t3.kb,
                         k_any10=top10adj.kb.min(), k_med_adj10=top10adj.kb.median()))
    return pd.DataFrame(rows)
