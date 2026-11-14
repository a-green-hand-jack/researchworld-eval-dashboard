"""Load the four evaluation designs into a common format.

A dataset is a dict with
  names : list[str]           participant names
  a, b  : int arrays (N,)     participant indices of the two sides of each comparison
  y     : float array (N,)    outcome for side a: 1 (a wins), 0.5 (tie), 0 (b wins)
Ties are kept as 0.5 outcomes (half a win for each side).
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)


def _pack(ia, ib, y, names, g=None):
    out = dict(names=list(names), a=np.asarray(ia, int), b=np.asarray(ib, int), y=np.asarray(y, float))
    if g is not None:
        out["g"] = np.asarray(g)
    return out


def _from_names(na, nb, y, g=None):
    names = sorted(set(na) | set(nb))
    idx = {n: i for i, n in enumerate(names)}
    ia = np.array([idx[n] for n in na]); ib = np.array([idx[n] for n in nb])
    keep = ia != ib
    return _pack(ia[keep], ib[keep], np.asarray(y)[keep], names, None if g is None else np.asarray(g)[keep])


def load_arena():
    d = pd.read_csv(os.path.join(DATA, "arena55k.csv"),
                    usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(d.winner_model_a == 1, 1.0, np.where(d.winner_model_b == 1, 0.0, 0.5))
    assert ((d.winner_model_a + d.winner_model_b + d.winner_tie) == 1).all()
    return _from_names(d.model_a.values, d.model_b.values, y)


def _mt(fn):
    d = pd.read_parquet(os.path.join(DATA, fn))
    y = d.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (inconsistent)": 0.5}).values
    assert not np.isnan(y).any()
    return _from_names(d.model_a.values, d.model_b.values, y, d.question_id.values)


def load_mt_human():
    return _mt("mt_human.parquet")


def load_mt_gpt4():
    return _mt("mt_gpt4pair.parquet")


def load_nba_season(year, playoffs=False):
    """Regular-season games of NBA season `year_id` (year the season ends). Franchise level."""
    d = pd.read_csv(os.path.join(DATA, "nbaallelo.csv"),
                    usecols=["game_id", "_iscopy", "year_id", "is_playoffs", "fran_id", "opp_fran", "game_result"])
    d = d[(d._iscopy == 0) & (d.year_id == year) & (d.is_playoffs == int(playoffs))]
    y = np.where(d.game_result == "W", 1.0, 0.0)
    return _from_names(d.fran_id.values, d.opp_fran.values, y)


def load_all():
    out = {"Arena (crowd)": load_arena(), "MT-Bench (human)": load_mt_human(),
           "MT-Bench (GPT-4 judge)": load_mt_gpt4()}
    return out


def describe(ds):
    n = len(ds["names"]); N = len(ds["y"])
    return dict(players=n, comparisons=N, tie_frac=float((ds["y"] == 0.5).mean()))


if __name__ == "__main__":
    for k, v in load_all().items():
        print(k, describe(v))
    for yr in (2000, 2015):
        print("NBA", yr, describe(load_nba_season(yr)))
