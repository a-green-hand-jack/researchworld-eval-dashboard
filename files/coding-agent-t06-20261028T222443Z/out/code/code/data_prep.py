"""Convert the raw public datasets into a common comparison format.

Each leaderboard is stored as derived/<name>.parquet with columns
  a, b   : competitor names
  y      : outcome from a's perspective (1 = a wins, 0 = b wins, 0.5 = tie)
  home   : 1 if a is the home team (NBA only), else 0
Usage: python code/data_prep.py  (reads data/, writes derived/)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "derived")
MIN_GAMES = 50  # competitors with fewer comparisons are removed (iteratively)

# MT-Bench model -> closest Chatbot Arena (55k) model name
MT6_MAP = {"gpt-4": "gpt-4-0314", "claude-v1": "claude-1", "gpt-3.5-turbo": "gpt-3.5-turbo-0314",
           "vicuna-13b-v1.2": "vicuna-13b", "alpaca-13b": "alpaca-13b", "llama-13b": "llama-13b"}


def filter_min(df, m=MIN_GAMES):
    while True:
        cnt = pd.concat([df.a, df.b]).value_counts()
        keep = set(cnt[cnt >= m].index)
        new = df[df.a.isin(keep) & df.b.isin(keep)]
        if len(new) == len(df):
            return new.reset_index(drop=True)
        df = new


def save(name, df, meta):
    df = df[df.a != df.b]
    if "home" not in df:
        df = df.assign(home=0)
    df = filter_min(df[["a", "b", "y", "home"]].copy())
    if len(df) == 0:
        return
    df["y"] = df["y"].astype(float)
    df.to_parquet(os.path.join(OUT, name + ".parquet"), index=False)
    meta[name] = dict(N=int(len(df)), K=int(pd.concat([df.a, df.b]).nunique()),
                      tie_rate=float((df.y == 0.5).mean()))
    print(name, meta[name], flush=True)


def arena55k(meta):
    d = pd.read_csv(os.path.join(DATA, "arena55k/train.csv"),
                    usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(d.winner_model_a == 1, 1.0, np.where(d.winner_model_b == 1, 0.0, 0.5))
    df = pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y))
    save("arena55k", df, meta)
    inv = {v: k for k, v in MT6_MAP.items()}
    sub = df[df.a.isin(inv) & df.b.isin(inv)].copy()
    save("arena55k_mt6", sub, meta)


def arena140k(meta):
    import pyarrow.parquet as pq
    parts = []
    for f in sorted(os.listdir(os.path.join(DATA, "arena140k"))):
        if f.endswith(".parquet"):
            parts.append(pq.read_table(os.path.join(DATA, "arena140k", f),
                                       columns=["model_a", "model_b", "winner"]).to_pandas())
    d = pd.concat(parts)
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "both_bad": 0.5})
    df = pd.DataFrame(dict(a=d.model_a.values, b=d.model_b.values, y=y.values)).dropna()
    save("arena140k", df, meta)


def webdev(meta):
    d = pd.DataFrame(json.load(open(os.path.join(DATA, "webdev/webdev-arena-preference-10k.json"))))
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (bothbad)": 0.5})
    save("webdev", pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y)).dropna(), meta)


def mtbench(meta):
    for src, name in [("human", "mtbench_human"), ("gpt4_pair", "mtbench_gpt4")]:
        d = pd.read_parquet(os.path.join(DATA, "mtbench", src + ".parquet"),
                            columns=["question_id", "model_a", "model_b", "winner", "judge", "turn"])
        y = d.winner.map(lambda w: 1.0 if w == "model_a" else 0.0 if w == "model_b" else 0.5)
        save(name, pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y)), meta)


def softmax3(df):
    z = df[["logit_A", "logit_B", "logit_C"]].to_numpy(float)
    z = np.exp(z - z.max(1, keepdims=True))
    return z / z.sum(1, keepdims=True)


def arena_judges(meta):
    base = pd.DataFrame(json.load(open(os.path.join(DATA, "judges/train.single-turn.json"))))
    base["id"] = base["id"].astype(int)
    y = np.where(base.winner_model_a.astype(int) == 1, 1.0,
                 np.where(base.winner_model_b.astype(int) == 1, 0.0, 0.5))
    crowd = pd.DataFrame(dict(id=base.id, a=base.model_a, b=base.model_b, y=y))
    save("arenaJ_crowd", crowd, meta)
    jdir = os.path.join(DATA, "judges/llm-judges")
    for f in sorted(os.listdir(jdir)):
        judge = f.replace(".jsonl", "")
        o = pd.read_json(os.path.join(jdir, f), lines=True)
        r = pd.read_json(os.path.join(DATA, "judges/llm-judges-reversed", f), lines=True)
        po, pr = softmax3(o), softmax3(r)
        # reversed file shows model_b in position A: swap A/B to align with original order
        pa = (po[:, 0] + pr[:, 1]) / 2
        pb = (po[:, 1] + pr[:, 0]) / 2
        pc = (po[:, 2] + pr[:, 2]) / 2
        assert (o.id.values == r.id.values).all()
        lab = np.array([1.0, 0.0, 0.5])[np.argmax(np.stack([pa, pb, pc], 1), 1)]
        j = pd.DataFrame(dict(id=o.id.astype(int), yj=lab)).merge(crowd, on="id")
        # judge labels on exactly the same battles as the crowd labels
        save("arenaJ_" + judge, j[["a", "b"]].assign(y=j.yj.values), meta)


def nba(meta):
    d = pd.read_csv(os.path.join(DATA, "nba/nbaallelo.csv"))
    d = d[(d._iscopy == 0) & (d.lg_id == "NBA") & (d.is_playoffs == 0)]
    for yr, g in d.groupby("year_id"):
        if g.game_location.eq("N").mean() > 0.2:
            continue
        a = g.team_id.values
        b = g.opp_id.values
        y = (g.game_result == "W").astype(float).values
        home = (g.game_location == "H").astype(int).values
        save(f"nba_{yr}", pd.DataFrame(dict(a=a, b=b, y=y, home=home)), meta)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for fn in [arena55k, arena140k, webdev, mtbench, arena_judges, nba]:
        fn(meta)
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
