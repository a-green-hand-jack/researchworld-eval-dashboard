"""Loaders turning each public dataset into aggregated CompData.

All raw files live under data/raw/ (see README for download commands and checksums).
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd

from .bt import from_records

RAW = os.environ.get("LB_RAW", "data/raw")
MIN_BATTLES = 50  # arena: drop models with fewer battles (removes 1 model in 140k)


def _filter_min(df, col_a="model_a", col_b="model_b", min_n=MIN_BATTLES):
    df = df[df[col_a] != df[col_b]]  # drop self-battles (present in arena-140k)
    cnt = pd.concat([df[col_a], df[col_b]]).value_counts()
    keep = set(cnt[cnt >= min_n].index)
    return df[df[col_a].isin(keep) & df[col_b].isin(keep)]


def arena55k(ties="half", return_df=False):
    df = pd.read_csv(f"{RAW}/arena55k_train.csv",
                     usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    df = _filter_min(df)
    y = np.where(df.winner_model_a == 1, 1.0, np.where(df.winner_model_b == 1, 0.0, 0.5))
    df = df.assign(y=y)
    if ties == "drop":
        df = df[df.y != 0.5]
    if return_df:
        return df
    return from_records(df.model_a.values, df.model_b.values, df.y.values,
                        meta=dict(name="Arena-55k", design="crowd"))


def arena140k(ties="half", return_df=False):
    fs = sorted(glob.glob(f"{RAW}/arena140k/*.parquet"))
    df = pd.concat([pd.read_parquet(f, columns=["id", "model_a", "model_b", "winner", "timestamp"])
                    for f in fs], ignore_index=True)
    df = _filter_min(df)
    # 'tie' and 'both_bad' are both treated as ties (as on the public leaderboard)
    y = np.where(df.winner == "model_a", 1.0, np.where(df.winner == "model_b", 0.0, 0.5))
    df = df.assign(y=y)
    if ties == "drop":
        df = df[df.y != 0.5]
    if return_df:
        return df
    return from_records(df.model_a.values, df.model_b.values, df.y.values,
                        meta=dict(name="Arena-140k", design="crowd"))


def _mt_winner(w):
    return np.where(w == "model_a", 1.0, np.where(w == "model_b", 0.0, 0.5))


def mtbench(judge="human", ties="half", return_df=False):
    """judge in {'human','gpt4'}; GPT-4 'tie (inconsistent)' (position-swap disagreement) = tie."""
    f = "mtbench_human.parquet" if judge == "human" else "mtbench_gpt4_pair.parquet"
    df = pd.read_parquet(f"{RAW}/{f}", columns=["question_id", "model_a", "model_b", "winner", "judge", "turn"])
    df = df.assign(y=_mt_winner(df.winner.values))
    if ties == "drop":
        df = df[df.y != 0.5]
    if return_df:
        return df
    name = "MT-Bench-Human" if judge == "human" else "MT-Bench-GPT4"
    design = "expert" if judge == "human" else "llm-judge"
    return from_records(df.model_a.values, df.model_b.values, df.y.values,
                        meta=dict(name=name, design=design))


def nba_season(year, return_df=False):
    """Regular-season NBA games of one season; first player = home team (home advantage term)."""
    df = _nba_all()
    df = df[df.year_id == year]
    if return_df:
        return df
    return from_records(df.team_id.values, df.opp_id.values, (df.game_result == "W").astype(float).values,
                        home=np.ones(len(df)), meta=dict(name=f"NBA-{year}", design="sports"))


_NBA = None


def _nba_all():
    global _NBA
    if _NBA is None:
        df = pd.read_csv(f"{RAW}/nbaallelo.csv",
                         usecols=["game_id", "lg_id", "_iscopy", "year_id", "is_playoffs", "team_id",
                                  "opp_id", "game_location", "game_result"])
        # one row per game from the home team's perspective; neutral-site games dropped (<=2/season)
        df = df[(df.lg_id == "NBA") & (df.is_playoffs == 0) & (df.game_location == "H")]
        _NBA = df
    return _NBA


NBA_YEARS = list(range(1990, 2016))


# ------------------------------------------------------------------------------------------
# LLM judges on the same Arena battles (potsawee/chatbot-arena-llm-judges)
# ------------------------------------------------------------------------------------------
JUDGES = ["Athene-70B", "Hermes-3-Llama-3.1-70B", "Meta-Llama-3-70B-Instruct", "Meta-Llama-3-8B-Instruct",
          "Meta-Llama-3-8B", "Mistral-7B-Instruct-v0.1", "Mistral-7B-Instruct-v0.2", "Mistral-7B-OpenOrca",
          "Mixtral-8x7B-Instruct-v0.1", "OpenHermes-2-Mistral-7B", "OpenHermes-2.5-Mistral-7B",
          "Qwen2-72B-Instruct", "StableBeluga-7B", "Starling-LM-7B-alpha", "dolphin-2.1-mistral-7b",
          "dolphin-2.5-mixtral-8x7b", "zephyr-7b-beta"]

_BATTLES = None


def _battles():
    global _BATTLES
    if _BATTLES is None:
        cache = "data/cache/llmjudge_battles.parquet"
        if os.path.exists(cache):
            _BATTLES = pd.read_parquet(cache)
        else:
            with open(f"{RAW}/llmjudges/train.single-turn.json") as fh:
                js = json.load(fh)
            b = pd.DataFrame([{k: r[k] for k in ("id", "model_a", "model_b", "winner_model_a",
                                                 "winner_model_b", "winner_tie")} for r in js])
            os.makedirs("data/cache", exist_ok=True)
            b.to_parquet(cache)
            _BATTLES = b
    return _BATTLES


def llmjudge_pair(judge, return_df=False):
    """Returns (human CompData, judge CompData) built on the identical set of battles."""
    b = _battles()
    j = pd.read_json(f"{RAW}/llmjudges/{judge}.jsonl", lines=True)
    j = j[["id", "winner_pred"]].dropna()
    df = b.merge(j, on="id", how="inner")
    df = _filter_min(df)
    yh = np.where(df.winner_model_a == 1, 1.0, np.where(df.winner_model_b == 1, 0.0, 0.5))
    yj = np.where(df.winner_pred == "A", 1.0, np.where(df.winner_pred == "B", 0.0, 0.5))
    df = df.assign(y_human=yh, y_judge=yj)
    if return_df:
        return df
    names = sorted(set(df.model_a) | set(df.model_b))
    dh = from_records(df.model_a.values, df.model_b.values, yh, names=names,
                      meta=dict(name=f"ArenaSub-Human[{judge}]", design="crowd"))
    dj = from_records(df.model_a.values, df.model_b.values, yj, names=names,
                      meta=dict(name=f"ArenaSub-{judge}", design="llm-judge"))
    return dh, dj


def mtbench_matched():
    """MT-Bench human and GPT-4 restricted to identical (question, pair, turn) items.

    Human items may carry several expert votes; GPT-4 has one judgment per item.  For the
    matched comparison we keep one human vote per item (the first by judge id order) so that
    both label sources have exactly the same design (same items, same n)."""
    h = mtbench("human", return_df=True)
    g = mtbench("gpt4", return_df=True)
    key = ["question_id", "model_a", "model_b", "turn"]
    h1 = h.sort_values(key + ["judge"]).drop_duplicates(key, keep="first")
    m = h1.merge(g[key + ["y"]], on=key, suffixes=("_h", "_g"))
    names = sorted(set(m.model_a) | set(m.model_b))
    dh = from_records(m.model_a.values, m.model_b.values, m.y_h.values, names=names,
                      meta=dict(name="MT-Matched-Human", design="expert"))
    dg = from_records(m.model_a.values, m.model_b.values, m.y_g.values, names=names,
                      meta=dict(name="MT-Matched-GPT4", design="llm-judge"))
    return dh, dg


def load(name, **kw):
    if name == "arena55k":
        return arena55k(**kw)
    if name == "arena140k":
        return arena140k(**kw)
    if name == "mt_human":
        return mtbench("human", **kw)
    if name == "mt_gpt4":
        return mtbench("gpt4", **kw)
    if name.startswith("nba"):
        return nba_season(int(name[3:]))
    raise KeyError(name)
