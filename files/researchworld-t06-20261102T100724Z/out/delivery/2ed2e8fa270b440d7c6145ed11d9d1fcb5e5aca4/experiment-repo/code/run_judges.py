"""Matched crowd-vs-model-judge contrast on the SAME Arena battles (E4 optional item).
Battles: the 49,938 single-turn battles of potsawee/chatbot-arena-llm-judges (a subset of Arena 55k, joined on `id`).
Boards: arena49k_h (human votes of those battles) and arena49k_<judge> (position-averaged LLM-judge verdict, argmax over
A / B / tie), for judges Meta-Llama-3-70B-Instruct, Athene-70B, Qwen2-72B-Instruct.  One battle bootstrap resample per
unit is shared by all boards (paired, as MT-Bench h/g).  C1, C2, C4 under P1 and P2 (same schema as kstar_units).
-> results/kstar_judges.csv.  Usage: python3 -I run_judges.py"""
import sys, os, json, time
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from experiments import *
from btlib import Board
import provenance as pv

SEED = 20261109
R = 40
JUDGES = ["Meta-Llama-3-70B-Instruct", "Athene-70B", "Qwen2-72B-Instruct"]
_CACHE = {}


def prepare():
    if _CACHE:
        return _CACHE
    a, names = arena55k()
    ids = [x["id"] for x in json.load(open(f"{DATA}/judges/train.single-turn.json"))]
    a = a.assign(id=a.id.astype(int)).set_index("id").loc[[int(i) for i in ids]]
    lo, hi = np.minimum(a.a.values, a.b.values), np.maximum(a.a.values, a.b.values)
    sw = a.a.values > a.b.values
    pairs, cell = np.unique(lo * len(names) + hi, return_inverse=True)
    labels = {"h": a.o.values}
    for j in JUDGES:
        pred = pd.read_json(f"{DATA}/judges/{j}.avg.jsonl", lines=True).set_index("id").loc[a.index, "winner_pred"]
        labels[j] = np.where(pred == "A", 1.0, np.where(pred == "B", 0.0, 0.5))
    typ = {}
    for k, o in labels.items():
        o = np.where(sw, 1 - o, o)          # outcome from the viewpoint of the lower-index participant
        typ[k] = np.where(o == 1, 0, np.where(o == 0, 1, 2))
    _CACHE.update(names=names, cell=cell, ncell=len(pairs), ii=pairs // len(names), jj=pairs % len(names), typ=typ,
                  n=len(a), idx=a.index.values)
    return _CACHE


def unit(rep):
    c = prepare()
    rng = np.random.default_rng([SEED, max(rep, 0)])
    w = np.ones(c["n"]) if rep < 0 else np.bincount(rng.integers(0, c["n"], c["n"]), minlength=c["n"]).astype(float)
    rows = []
    for k, t in c["typ"].items():
        cnt = [np.bincount(c["cell"][t == m], weights=w[t == m], minlength=c["ncell"]) for m in range(3)]
        keep = (cnt[0] + cnt[1] + cnt[2]) > 0
        B = Board(len(c["names"]), c["ii"][keep], c["jj"][keep], cnt[0][keep], cnt[1][keep], cnt[2][keep], names=c["names"])
        t0 = time.time()
        r = claim_rows(B, B.fit(), claims=("C1", "C2", "C4"), perts=("P1", "P2"))
        for x in r:
            x.update(board="arena49k_h" if k == "h" else "arena49k_" + k, design="crowd" if k == "h" else "model-judge",
                     unit_type="full" if rep < 0 else "boot", unit_id=rep)
        rows += r
    print(f"HUTIAN_WAKE: judges {rep} {time.time()-t0:.0f}s", flush=True) if rep % 10 == 0 else None
    return rows


if __name__ == "__main__":
    units = [-1] + list(range(R))
    if len(sys.argv) > 1:
        units = [int(u) for u in sys.argv[1:]]
    with Pool(2) as p:
        res = p.map(unit, units, chunksize=1)
    src = [f"{DATA}/judges/train.single-turn.json", f"{DATA}/arena55k/train.csv"] + [f"{DATA}/judges/{j}.avg.jsonl" for j in JUDGES]
    pv.save(pd.DataFrame([r for x in res for r in x]), "kstar_judges.csv" if len(sys.argv) == 1 else "kstar_judges_pilot.csv",
            "run_judges.py", SEED, src)
