"""Loaders that turn each raw public dataset into a table of comparisons
(a, b, y[, h]) with entity names.  Raw files live in $LBSTAB_DATA (default /work/data)."""
from __future__ import annotations

import glob
import os
import numpy as np
import pandas as pd

from .bt import cells_from_frame

DATA = os.environ.get("LBSTAB_DATA", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
PROC = os.path.join(DATA, "processed")

JUDGES = ["Athene-70B", "Qwen2-72B-Instruct", "Meta-Llama-3-70B-Instruct",
          "Hermes-3-Llama-3.1-70B", "Mixtral-8x7B-Instruct-v0.1", "Meta-Llama-3-8B-Instruct"]


def _encode(model_a, model_b, y, h=None):
    names = sorted(set(model_a) | set(model_b))
    idx = {n: k for k, n in enumerate(names)}
    df = pd.DataFrame({"a": [idx[x] for x in model_a], "b": [idx[x] for x in model_b],
                       "y": np.asarray(y, float)})
    if h is not None:
        df["h"] = np.asarray(h, float)
    return df, names


def load_arena55k():
    d = pd.read_csv(os.path.join(DATA, "arena55k", "train.csv"),
                    usecols=["model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = d.winner_model_a * 1.0 + d.winner_tie * 0.5
    return _encode(d.model_a.values, d.model_b.values, y.values)


def load_arena140k():
    fs = sorted(glob.glob(os.path.join(DATA, "arena140k", "train-*.parquet")))
    d = pd.concat([pd.read_parquet(f, columns=["model_a", "model_b", "winner"]) for f in fs])
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "both_bad": 0.5})
    return _encode(d.model_a.values, d.model_b.values, y.values)


def load_webdev():
    import json
    d = pd.DataFrame(json.load(open(os.path.join(DATA, "webdev", "webdev-arena-preference-10k.json"))))
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (bothbad)": 0.5})
    return _encode(d.model_a.values, d.model_b.values, y.values)


def _mt(fname):
    d = pd.read_parquet(os.path.join(DATA, "mtbench", fname), columns=["question_id", "model_a", "model_b", "winner", "judge", "turn"])
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (inconsistent)": 0.5})
    return d, y


def load_mtbench_human():
    d, y = _mt("human.parquet")
    return _encode(d.model_a.values, d.model_b.values, y.values)


def load_mtbench_gpt4():
    d, y = _mt("gpt4_pair.parquet")
    return _encode(d.model_a.values, d.model_b.values, y.values)


def _arena_single_turn():
    t = pd.read_json(os.path.join(DATA, "judges", "train.single-turn.json"))
    return t[["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"]]


def load_arena_st_human():
    t = _arena_single_turn()
    y = t.winner_model_a * 1.0 + t.winner_tie * 0.5
    return _encode(t.model_a.values, t.model_b.values, y.values)


def load_arena_st_judge(judge, variant="llm-judges-prob-avg"):
    t = _arena_single_turn()
    j = pd.read_json(os.path.join(DATA, "judges", variant, judge + ".jsonl"), lines=True)
    t = t.merge(j[["id", "winner_pred"]], on="id", how="inner")
    y = t.winner_pred.map({"A": 1.0, "B": 0.0, "tie": 0.5, "C": 0.5})
    assert y.notna().all()
    return _encode(t.model_a.values, t.model_b.values, y.values)


def load_nba(season):
    d = pd.read_csv(os.path.join(DATA, "nba", "nbaallelo.csv"),
                    usecols=["game_id", "_iscopy", "year_id", "lg_id", "is_playoffs", "team_id", "opp_id",
                             "game_location", "game_result"])
    d = d[(d.year_id == season) & (d.lg_id == "NBA") & (d.is_playoffs == 0) & (d._iscopy == 0)]
    # orient every game as home team = a (neutral-site games keep h=0)
    home = d.game_location == "H"
    away = d.game_location == "A"
    a = np.where(away, d.opp_id, d.team_id)
    b = np.where(away, d.team_id, d.opp_id)
    win_row = (d.game_result == "W").values
    y = np.where(away, ~win_row, win_row).astype(float)
    h = np.where(home | away, 1.0, 0.0)
    return _encode(a, b, y, h)


def nba_seasons():
    d = pd.read_csv(os.path.join(DATA, "nba", "nbaallelo.csv"), usecols=["year_id", "lg_id"])
    return sorted(d[d.lg_id == "NBA"].year_id.unique().tolist())


# registry: name -> (loader, design category, home-advantage flag)
def registry():
    R = {
        "arena55k": (load_arena55k, "crowd", False),
        "arena140k": (load_arena140k, "crowd", False),
        "webdev10k": (load_webdev, "crowd", False),
        "mtbench_human": (load_mtbench_human, "expert", False),
        "mtbench_gpt4": (load_mtbench_gpt4, "llm-judge", False),
        "arenaST_human": (load_arena_st_human, "crowd", False),
    }
    for jn in JUDGES:
        R["arenaST_" + jn] = ((lambda jn=jn: load_arena_st_judge(jn)), "llm-judge", False)
    return R


def load(name):
    """Return (df, names, home) with caching to data/processed."""
    os.makedirs(PROC, exist_ok=True)
    f = os.path.join(PROC, name + ".parquet")
    if name.startswith("nba"):
        home = True
        loader = lambda: load_nba(int(name[3:]))
    else:
        loader, _, home = registry()[name]
    if os.path.exists(f):
        df = pd.read_parquet(f)
        names = list(pd.read_parquet(f.replace(".parquet", ".names.parquet")).name)
    else:
        df, names = loader()
        df.to_parquet(f)
        pd.DataFrame({"name": names}).to_parquet(f.replace(".parquet", ".names.parquet"))
    return df, names, home


def load_cells(name):
    df, names, home = load(name)
    return cells_from_frame(df, names, home=home)


def design_of(name):
    if name.startswith("nba"):
        return "sports"
    return registry()[name][1]
