"""Loaders: every dataset -> list of named leaderboards, each a table of comparisons.

A comparison is (a, b, h, y): item a vs item b; h=1 if a has a home/first-position flag
(only NBA), y in {0, 0.5, 1} = outcome for a (0.5 = tie).
"""
import json, os
import numpy as np
import pandas as pd

DATA = os.environ.get("BT_DATA", "/work/data")


def _encode(names_a, names_b, y, h=None, items=None):
    names_a = np.asarray(names_a); names_b = np.asarray(names_b)
    if items is None:
        items = sorted(set(names_a) | set(names_b))
    idx = {n: k for k, n in enumerate(items)}
    a = np.array([idx[n] for n in names_a]); b = np.array([idx[n] for n in names_b])
    y = np.asarray(y, dtype=float)
    h = np.zeros(len(a), dtype=int) if h is None else np.asarray(h, dtype=int)
    # canonical orientation when there is no home flag
    sw = (h == 0) & (a > b)
    a2 = np.where(sw, b, a); b2 = np.where(sw, a, b); y2 = np.where(sw, 1 - y, y)
    return dict(items=list(items), a=a2, b=b2, h=h, y=y2)


def arena55k(min_comparisons=0):
    df = pd.read_csv(f"{DATA}/arena55k/train.csv",
                     usecols=["model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(df.winner_model_a == 1, 1.0, np.where(df.winner_model_b == 1, 0.0, 0.5))
    return _encode(df.model_a, df.model_b, y)


def mtbench(kind="human"):
    if kind == "human":
        df = pd.read_parquet(f"{DATA}/mtbench/human.parquet", columns=["question_id", "model_a", "model_b", "winner", "turn"])
    else:
        df = pd.read_parquet(f"{DATA}/mtbench/gpt4_pair.parquet", columns=["question_id", "model_a", "model_b", "winner", "turn"])
    y = np.where(df.winner == "model_a", 1.0, np.where(df.winner == "model_b", 0.0, 0.5))
    d = _encode(df.model_a, df.model_b, y)
    d["qid"] = df.question_id.values; d["turn"] = df.turn.values
    return d


def mtbench_matched():
    """Human judgments restricted to the (question, turn, model pair) cells the GPT-4 judge also covers."""
    h = pd.read_parquet(f"{DATA}/mtbench/human.parquet", columns=["question_id", "model_a", "model_b", "winner", "turn"])
    g = pd.read_parquet(f"{DATA}/mtbench/gpt4_pair.parquet", columns=["question_id", "model_a", "model_b", "winner", "turn"])
    key = lambda d: d.question_id.astype(str) + "|" + d.turn.astype(str) + "|" + d.apply(lambda r: "|".join(sorted([r.model_a, r.model_b])), axis=1)
    kg = set(key(g)); h = h[key(h).isin(kg)]
    y = np.where(h.winner == "model_a", 1.0, np.where(h.winner == "model_b", 0.0, 0.5))
    return _encode(h.model_a, h.model_b, y)


def nba_seasons(min_year=None):
    df = pd.read_csv(f"{DATA}/nba/nbaallelo.csv",
                     usecols=["game_id", "_iscopy", "year_id", "is_playoffs", "team_id", "opp_id", "game_location", "game_result", "lg_id"])
    df = df[(df._iscopy == 0) & (df.is_playoffs == 0)]
    out = {}
    for yr, g in df.groupby("year_id"):
        win = (g.game_result == "W").values.astype(float)
        loc = g.game_location.values
        ta, tb = g.team_id.values, g.opp_id.values
        # orient so that a is the home team when location is known
        away = loc == "A"
        a = np.where(away, tb, ta); b = np.where(away, ta, tb)
        y = np.where(away, 1 - win, win)
        h = (loc != "N").astype(int)
        out[int(yr)] = _encode(a, b, y, h)
    return out


_META = None


def arena_judge(judge):
    """Arena single-turn battles (49,938) with labels from an LLM judge (prob-avg over both orders)."""
    base = f"{DATA}/judges"
    global _META
    if _META is None:
        with open(f"{base}/train.single-turn.json") as f:
            raw = json.load(f)
        _META = {r["id"]: (r["model_a"], r["model_b"], r["winner_model_a"], r["winner_model_b"]) for r in raw}
        del raw
    meta = _META
    ids, ma, mb, yh, yj = [], [], [], [], []
    if judge is not None:
        with open(f"{base}/{judge}.jsonl") as f:
            for line in f:
                r = json.loads(line)
                m = meta[r["id"]]
                ids.append(r["id"]); ma.append(m[0]); mb.append(m[1])
                yh.append(1.0 if m[2] == 1 else (0.0 if m[3] == 1 else 0.5))
                yj.append({"A": 1.0, "B": 0.0, "tie": 0.5}[r["winner_pred"]])
    return ma, mb, np.array(yh), np.array(yj)


def arena140k():
    """Arena 140k release (commit 6322995): model_a/model_b/winner only; 'both_bad' is treated as a tie."""
    import glob
    cache = f"{DATA}/arena140k_small.parquet"
    if not os.path.exists(cache):
        fs = sorted(glob.glob(f"{DATA}/arena140k/*.parquet"))
        pd.concat([pd.read_parquet(f, columns=["model_a", "model_b", "winner"]) for f in fs], ignore_index=True).to_parquet(cache)
    df = pd.read_parquet(cache)
    y = np.where(df.winner == "model_a", 1.0, np.where(df.winner == "model_b", 0.0, 0.5))
    return _encode(df.model_a, df.model_b, y)
