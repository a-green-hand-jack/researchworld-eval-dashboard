"""Loaders that turn the raw public files in ./data into comparison lists (a, b, y, h).

Every loader returns a dict with keys a, b, y, h (numpy arrays), use_home, design, label.
Outcome convention: y = 1 if a won, 0 if b won, 0.5 tie.  Preprocessing choices
(documented in the paper):
  * ties (incl. 'both bad' / GPT-4 'inconsistent' verdicts) are half-wins;
  * players with fewer than MIN_GAMES comparisons are removed (iteratively) together with
    their comparisons (affects only Arena data; ablation in exp_ablations.py);
  * NBA: one BT fit per regular season, a = home team with home-advantage covariate h = 1
    (h = 0 for neutral-site games).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(DATA, "processed")
MIN_GAMES = 50

JUDGES = ["Qwen2-72B-Instruct", "Meta-Llama-3-70B-Instruct", "Athene-70B",
          "Meta-Llama-3-8B-Instruct", "Mistral-7B-Instruct-v0.2"]


def _filter_min_games(df, min_games):
    while True:
        cnt = pd.concat([df.a, df.b]).value_counts()
        keep = set(cnt[cnt >= min_games].index)
        m = df.a.isin(keep) & df.b.isin(keep)
        if m.all():
            return df
        df = df[m]


def _pack(df, design, label, use_home=False, min_games=MIN_GAMES):
    df = df[df.a != df.b]
    if min_games:
        df = _filter_min_games(df, min_games)
    h = df.h.values.astype(float) if "h" in df else np.zeros(len(df))
    return dict(a=np.asarray(df.a.values, dtype=object), b=np.asarray(df.b.values, dtype=object),
                y=np.asarray(df.y.values, dtype=float), h=np.asarray(h, dtype=float),
                use_home=use_home, design=design, label=label)


def _cached(name, builder):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".csv.gz")
    if os.path.exists(path):
        return pd.read_csv(path)
    df = builder()
    df.to_csv(path, index=False)
    return df


def mtbench(which="human", min_games=MIN_GAMES):
    fn = {"human": "human.parquet", "gpt4": "gpt4_pair.parquet"}[which]

    def build():
        d = pd.read_parquet(os.path.join(DATA, "mtbench", fn),
                            columns=["question_id", "model_a", "model_b", "winner", "judge", "turn"])
        y = d.winner.map({"model_a": 1.0, "model_b": 0.0}).fillna(0.5)  # 'tie', 'tie (inconsistent)'
        return pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y, qid=d.question_id, turn=d.turn, judge=d.judge))
    df = _cached("mtbench_" + which, build)
    lab = {"human": "MT-Bench (expert humans)", "gpt4": "MT-Bench (GPT-4 judge)"}[which]
    des = {"human": "expert", "gpt4": "llm-judge"}[which]
    return _pack(df, des, lab, min_games=min_games), df


def arena55k(min_games=MIN_GAMES):
    def build():
        d = pd.read_csv(os.path.join(DATA, "arena55k", "train.csv"),
                        usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
        y = np.where(d.winner_model_a == 1, 1.0, np.where(d.winner_model_b == 1, 0.0, 0.5))
        return pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y, id=d.id))
    df = _cached("arena55k", build)
    return _pack(df, "crowd", "Arena-55k (crowd, 2023-24)", min_games=min_games), df


def arena140k(min_games=MIN_GAMES):
    def build():
        d = pd.read_parquet(os.path.join(DATA, "arena140k"), columns=["id", "model_a", "model_b", "winner", "timestamp"])
        y = d.winner.map({"model_a": 1.0, "model_b": 0.0}).fillna(0.5)   # tie, both_bad -> tie
        return pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y, id=d.id, ts=d.timestamp.astype(str)))
    df = _cached("arena140k", build)
    return _pack(df, "crowd", "Arena-140k (crowd, 2025)", min_games=min_games), df


def arena_single_turn(judge=None, min_games=MIN_GAMES):
    """Single-turn Arena battles (subset of Arena-55k) labelled by the crowd (judge=None) or by
    an LLM judge (verdict = argmax of position-swapped averaged probabilities)."""
    def build_base():
        with open(os.path.join(DATA, "arena_judges", "train.single-turn.json")) as f:
            js = json.load(f)
        d = pd.DataFrame([{k: r[k] for k in ("id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie")} for r in js])
        y = np.where(d.winner_model_a == 1, 1.0, np.where(d.winner_model_b == 1, 0.0, 0.5))
        return pd.DataFrame(dict(a=d.model_a, b=d.model_b, y=y, id=d.id))
    base = _cached("arena_st_crowd", build_base)
    if judge is None:
        return _pack(base, "crowd", "Arena single-turn (crowd)", min_games=min_games), base

    def build_j():
        rows = []
        with open(os.path.join(DATA, "arena_judges", "llm-judges-prob-avg", judge + ".jsonl")) as f:
            for line in f:
                r = json.loads(line)
                rows.append((r["id"], r["prob_A"], r["prob_B"], r["prob_C"]))
        pj = pd.DataFrame(rows, columns=["id", "pA", "pB", "pC"])
        m = base.merge(pj, on="id", how="inner")
        arg = np.argmax(m[["pA", "pB", "pC"]].values, axis=1)
        m["y"] = np.array([1.0, 0.0, 0.5])[arg]
        return m[["a", "b", "y", "id"]]
    df = _cached("arena_st_" + judge, build_j)
    return _pack(df, "llm-judge", f"Arena single-turn ({judge} judge)", min_games=min_games), df


def nba_games():
    def build():
        d = pd.read_csv(os.path.join(DATA, "nba", "nbaallelo.csv"))
        d = d[(d._iscopy == 0)]
        # orient each game home vs away; neutral ('N') games keep listed order with h = 0
        home = d.game_location == "H"
        away = d.game_location == "A"
        a = np.where(away, d.opp_id, d.team_id)
        b = np.where(away, d.team_id, d.opp_id)
        a_won = np.where(away, d.game_result == "L", d.game_result == "W")
        h = np.where(home | away, 1.0, 0.0)
        return pd.DataFrame(dict(a=a, b=b, y=a_won.astype(float), h=h, season=d.year_id.values,
                                 lg=d.lg_id.values, playoffs=d.is_playoffs.values, date=d.date_game.values))
    return _cached("nba_games", build)


def nba_season(year, playoffs=False):
    g = nba_games()
    s = g[(g.season == year) & (g.lg == "NBA")]
    if not playoffs:
        s = s[s.playoffs == 0]
    return _pack(s, "sports", f"NBA {year - 1}-{str(year)[-2:]}", use_home=True, min_games=0), s


NBA_SEASONS = list(range(1977, 2016))   # post ABA-NBA merger seasons available in the file


def all_main(include_nba_all=False):
    """Main datasets in the order used in the paper."""
    out = {}
    out["arena140k"] = arena140k()[0]
    out["arena55k"] = arena55k()[0]
    out["st_crowd"] = arena_single_turn(None)[0]
    for jn in JUDGES:
        out["st_" + jn] = arena_single_turn(jn)[0]
    out["mt_human"] = mtbench("human")[0]
    out["mt_gpt4"] = mtbench("gpt4")[0]
    seasons = NBA_SEASONS if include_nba_all else [2015]
    for yr in seasons:
        out[f"nba{yr}"] = nba_season(yr)[0]
    return out
