"""Loaders turning the raw public files into count-based Boards."""
import numpy as np
import pandas as pd
from bt import Board

D = "/work/data"


def _board_from_votes(a, b, y, names=None, home=None, name=""):
    """a, b: item labels (first, second); y in {0,.5,1} from a's perspective.
    Pairs are canonicalised (index of first < index of second) unless `home` is
    given, in which case the orientation (home first) is kept."""
    if names is None:
        names = sorted(set(a) | set(b))
    idx = {s: k for k, s in enumerate(names)}
    ia = np.array([idx[s] for s in a]); ib = np.array([idx[s] for s in b])
    y = np.asarray(y, dtype=float)
    h = None if home is None else np.asarray(home, dtype=float)
    if h is None:
        sw = ia > ib
        ia, ib = np.where(sw, ib, ia), np.where(sw, ia, ib)
        y = np.where(sw, 1 - y, y)
    else:
        # neutral-site games (h == 0): canonicalise orientation
        sw = (h == 0) & (ia > ib)
        ia, ib = np.where(sw, ib, ia), np.where(sw, ia, ib)
        y = np.where(sw, 1 - y, y)
    lab = np.rint(y * 2).astype(int)
    key = (ia * len(names) + ib) * 2 + (0 if h is None else (h != 0).astype(int))
    df = pd.DataFrame(dict(key=key, ia=ia, ib=ib, lab=lab,
                           h=(np.zeros(len(ia)) if h is None else h)))
    g = df.groupby(["key", "ia", "ib", "h", "lab"]).size().unstack("lab", fill_value=0)
    for l in range(3):
        if l not in g.columns:
            g[l] = 0
    g = g[[0, 1, 2]].reset_index()
    return Board(names, g[["ia", "ib"]].values, g[[0, 1, 2]].values,
                 None if home is None else g["h"].values, name=name)


def arena55k():
    d = pd.read_csv(f"{D}/arena55k/train.csv",
                    usecols=["model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(d.winner_model_a == 1, 1.0, np.where(d.winner_model_b == 1, 0.0, 0.5))
    return _board_from_votes(d.model_a.values, d.model_b.values, y, name="Arena-55k (crowd)")


def mtbench_human(who=None):
    d = pd.read_parquet(f"{D}/mtbench/human-00000-of-00001-25f4910818759289.parquet")
    if who:
        d = d[d.judge.str.startswith(who)]
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5}).values
    return _board_from_votes(d.model_a.values, d.model_b.values, y, name="MT-Bench human (expert)")


def mtbench_gpt4():
    d = pd.read_parquet(f"{D}/mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet")
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (inconsistent)": 0.5}).values
    return _board_from_votes(d.model_a.values, d.model_b.values, y, name="MT-Bench GPT-4 judge")


def nba_seasons(playoffs=False):
    """dict year -> Board (regular season only by default; home-field parameter)."""
    d = pd.read_csv(f"{D}/nba/nbaallelo.csv",
                    usecols=["year_id", "_iscopy", "team_id", "opp_id", "game_location",
                             "game_result", "is_playoffs"])
    d = d[(d._iscopy == 0) & (d.is_playoffs == (1 if playoffs else 0))]
    out = {}
    for yr, g in d.groupby("year_id"):
        loc = g.game_location.map({"H": 1.0, "N": 0.0, "A": -1.0}).values
        a, b = g.team_id.values, g.opp_id.values
        y = (g.game_result == "W").astype(float).values
        # orient so that the home team is first
        away = loc < 0
        a2 = np.where(away, b, a); b2 = np.where(away, a, b)
        y2 = np.where(away, 1 - y, y)
        h = np.where(loc == 0, 0.0, 1.0)
        out[int(yr)] = _board_from_votes(a2, b2, y2, home=h, name=f"NBA {yr}")
    return out


def arena_single_turn(judge=None):
    """The 49,938 single-turn Arena battles (potsawee/chatbot-arena-llm-judges); labels from
    humans (judge=None) or from the position-averaged verdict (argmax) of an LLM judge."""
    import json
    with open(f"{D}/judges/train.single-turn.json") as f:
        raw = json.load(f)
    df = pd.DataFrame([{k: r[k] for k in ("id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie")}
                       for r in raw])
    if judge is None:
        y = np.where(df.winner_model_a == 1, 1.0, np.where(df.winner_model_b == 1, 0.0, 0.5))
        return _board_from_votes(df.model_a.values, df.model_b.values, y, name="Arena single-turn (human)")
    j = pd.read_json(f"{D}/judges/llm-judges-prob-avg/{judge}.jsonl", lines=True)
    pred = j.set_index("id").winner_pred
    p = df.id.map(pred)
    assert p.notna().all(), "missing judge verdicts"
    y = p.map({"A": 1.0, "B": 0.0, "tie": 0.5}).values
    assert not np.isnan(y).any(), set(pred.unique())
    return _board_from_votes(df.model_a.values, df.model_b.values, y, name=f"Arena single-turn ({judge})")


def arena140k_votes():
    """Arena-140k (April-July 2025 snapshot): DataFrame with model_a, model_b, y (1/0/0.5; 'both bad' counted as tie),
    session id and timestamp.  Only the needed columns are read."""
    import glob, pyarrow.parquet as pq
    fs = sorted(glob.glob(f"{D}/arena140k/train-*.parquet"))
    d = pd.concat([pq.read_table(f, columns=["model_a", "model_b", "winner", "evaluation_session_id", "timestamp"]).to_pandas()
                   for f in fs], ignore_index=True)
    d["y"] = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "both_bad": 0.5})
    assert d.y.notna().all()
    return d


def arena140k():
    d = arena140k_votes()
    return _board_from_votes(d.model_a.values, d.model_b.values, d.y.values, name="Arena-140k (crowd, 2025)")
