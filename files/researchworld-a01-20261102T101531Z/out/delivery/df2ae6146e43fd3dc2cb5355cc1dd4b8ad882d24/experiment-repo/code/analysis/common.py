import os, sys
import numpy as np, pandas as pd
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../code
ROOT = os.path.dirname(CODE)
sys.path.insert(0, CODE)
from lbattack import rules as R, solvers as V

OLB_TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]

def load_helm():
    df = pd.read_csv(f"{ROOT}/data/processed/helm_mmlu_v1.13.0.csv", index_col=0)
    return df

def load_olb(variant="main", raw=False):
    """variant: main (dedup by fullname keeping best average, unflagged),
    all (4576 rows), official, nomerge, small (<=8B), chat, pretrained."""
    o = pd.read_csv(f"{ROOT}/data/processed/olb_contents.csv")
    o["avg"] = o["Average ⬆️"]
    if variant != "all":
        o = o[~o["Flagged"]]
        o = o.sort_values("avg", ascending=False).drop_duplicates("fullname")
    if variant == "official": o = o[o["Official Providers"]]
    if variant == "nomerge": o = o[~o["Merged"] & ~o["Type"].str.contains("merges")]
    if variant == "small": o = o[o["#Params (B)"] <= 8]
    if variant == "chat": o = o[o["Type"].str.contains("chat")]
    if variant == "pretrained": o = o[o["Type"].str.contains("pretrained")]
    cols = [c + " Raw" if raw else c for c in OLB_TASKS]
    S = o[cols].astype(float).values * (100 if raw else 1)
    return o.reset_index(drop=True), S

def pick_targets(S, n_log=300, n_top=30, seed=0):
    """top-n_top by mean plus log-spaced ranks; returns row indices."""
    m = S.shape[0]
    order = np.argsort(-S.mean(1), kind="stable")
    ranks = set(range(n_top)) | set(np.unique(np.round(np.logspace(0, np.log10(m - 1), n_log)).astype(int)))
    ranks = sorted(r for r in ranks if r < m)
    return order[ranks], ranks

def initial_ranks(S, rule):
    sc = R.scores(S, rule)
    return (sc[None, :] > sc[:, None]).sum(1) + 1
