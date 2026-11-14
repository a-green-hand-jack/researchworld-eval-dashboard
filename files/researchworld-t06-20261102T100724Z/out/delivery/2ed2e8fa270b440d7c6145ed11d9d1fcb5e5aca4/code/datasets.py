"""Loaders: raw files -> Board objects. Raw data lives in $DATA_DIR (default /hutian/data)."""
import os
import numpy as np
import pandas as pd
from btlib import Board

DATA = os.environ.get("DATA_DIR", "/hutian/data")


def board_from_records(a_idx, b_idx, outcome, P, names, home=None):
    """a_idx,b_idx: participants; outcome: 1 a wins, 0 b wins, .5 tie.  home: None or array
    (1 if a is home, 0 if b is home) -> separate cells per orientation."""
    df = pd.DataFrame(dict(a=a_idx, b=b_idx, o=outcome))
    if home is None:
        lo = np.minimum(df.a, df.b)
        hi = np.maximum(df.a, df.b)
        sw = df.a > df.b
        o = np.where(sw, 1 - df.o, df.o)
        df = pd.DataFrame(dict(i=lo, j=hi, o=o))
        keys = ["i", "j"]
    else:
        df = pd.DataFrame(dict(i=df.a, j=df.b, o=df.o, h=home))
        keys = ["i", "j", "h"]
    g = df.groupby(keys)["o"]
    cells = pd.DataFrame(dict(W=g.apply(lambda s: (s == 1).sum()), L=g.apply(lambda s: (s == 0).sum()),
                              T=g.apply(lambda s: (s == 0.5).sum()))).reset_index()
    return Board(P, cells.i.values, cells.j.values, cells.W.values, cells.L.values, cells["T"].values,
                 home=cells.h.values if home is not None else None, names=names)


def records_from_board(board):
    """Expand a board back to individual comparisons (arrays i, j, h, outcome)."""
    rows = []
    for c in range(board.n_cells):
        for val, cnt in ((1.0, board.W[c]), (0.0, board.L[c]), (0.5, board.T[c])):
            rows.append((c, val, int(cnt)))
    cells = np.repeat([r[0] for r in rows], [r[2] for r in rows])
    out = np.repeat([r[1] for r in rows], [r[2] for r in rows])
    return cells, out


def arena55k():
    df = pd.read_csv(f"{DATA}/arena55k/train.csv",
                     usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    names = sorted(set(df.model_a) | set(df.model_b))
    ix = {m: k for k, m in enumerate(names)}
    o = np.where(df.winner_model_a == 1, 1.0, np.where(df.winner_model_b == 1, 0.0, 0.5))
    return df.assign(o=o, a=df.model_a.map(ix), b=df.model_b.map(ix)), names


def mtbench(kind="human"):
    f = {"human": "mtbench/human-00000-of-00001-25f4910818759289.parquet",
         "gpt4": "mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet"}[kind]
    df = pd.read_parquet(f"{DATA}/{f}", columns=["question_id", "model_a", "model_b", "winner", "judge", "turn"])
    names = sorted(set(df.model_a) | set(df.model_b))
    ix = {m: k for k, m in enumerate(names)}
    o = np.where(df.winner == "model_a", 1.0, np.where(df.winner == "model_b", 0.0, 0.5))
    return df.assign(o=o, a=df.model_a.map(ix), b=df.model_b.map(ix)), names


def nba(playoffs=False):
    df = pd.read_csv(f"{DATA}/nba/nbaallelo.csv")
    df = df[df._iscopy == 0]
    if not playoffs:
        df = df[df.is_playoffs == 0]
    return df


def nba_season_board(df, year, home=True, league="NBA"):
    """Regular-season board for one NBA season (year_id = year of the season's end).  Only `league` games are kept:
    in 1968-76 the file also holds the ABA, a disconnected comparison graph on which the BT scale between the two
    leagues is set by the ridge alone (se ~ 400)."""
    d = df[(df.year_id == year) & (df.lg_id == league)]
    teams = sorted(set(d.team_id) | set(d.opp_id))
    ix = {t: k for k, t in enumerate(teams)}
    a = d.team_id.map(ix).values
    b = d.opp_id.map(ix).values
    o = np.where(d.game_result == "W", 1.0, 0.0)
    if not home:
        return board_from_records(a, b, o, len(teams), teams)
    away = (d.game_location == "A").values
    a2 = np.where(away, b, a)
    b2 = np.where(away, a, b)
    o2 = np.where(away, 1 - o, o)
    h = (d.game_location != "N").values.astype(float)
    return board_from_records(a2, b2, o2, len(teams), teams, home=h)


def arena_board(df, names, idx=None):
    if idx is not None:
        df = df.iloc[idx]
    return board_from_records(df.a.values, df.b.values, df.o.values, len(names), names)


def mt_board(df, names):
    return board_from_records(df.a.values, df.b.values, df.o.values, len(names), names)


def mt_matched(seed=0):
    """Aligned MT-Bench boards on the (question, turn, unordered model pair) keys present in BOTH the human and
    the GPT-4 files.  Returns dict(label -> (df, names, key_series)); `h1` keeps one random human judgment per key."""
    h, names = mtbench("human")
    g, names_g = mtbench("gpt4")
    assert names == names_g
    for d in (h, g):
        d["key"] = [(q, t, min(a, b), max(a, b)) for q, t, a, b in zip(d.question_id, d.turn, d.model_a, d.model_b)]
    common = set(h.key) & set(g.key)
    hm, gm = h[h.key.isin(common)].copy(), g[g.key.isin(common)].copy()
    h1 = hm.sample(frac=1.0, random_state=seed).drop_duplicates("key").sort_index()
    return dict(h=hm, g=gm, h1=h1), names
