"""Dataset loaders. Raw files live outside the repository: set BT_DATA to their directory (default: <repository root>/data)."""
from __future__ import annotations

import hashlib
import os

import numpy as np
import pandas as pd

from .core import Counts

DATA = os.environ.get("BT_DATA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")

CHECKSUMS = {
    "arena55k.csv": "0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2",
    "mt_human.parquet": "4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769",
    "mt_gpt4.parquet": "57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71",
    "nbaallelo.csv": "d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc",
}
SOURCES = {
    "arena55k.csv": "HF lmarena-ai/arena-human-preference-55k @18c298340948c0e7f7727399fd459cca6ce0ca6f train.csv",
    "mt_human.parquet": "HF lmsys/mt_bench_human_judgments @f7d2896d2cc5d80f8b55c2bbc722613555233c25 data/human-00000-of-00001-25f4910818759289.parquet",
    "mt_gpt4.parquet": "HF lmsys/mt_bench_human_judgments @f7d2896d2cc5d80f8b55c2bbc722613555233c25 data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet",
    "nbaallelo.csv": "github fivethirtyeight/data @4c1ff5e3aef1816ae04af63218015066e186c147 nba-elo/nbaallelo.csv",
}


def sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def path(fname, verify=True):
    p = os.path.join(DATA, fname)
    if verify and fname in CHECKSUMS:
        got = sha256(p)
        if got != CHECKSUMS[fname]:
            raise RuntimeError(f"checksum mismatch for {fname}: {got}")
    return p


class Dataset:
    """Rows of comparisons: names, i, j, y (0 i wins, 1 tie, 2 j wins), optional h (home flag of i) and group."""

    def __init__(self, name, design, names, i, j, y, h=None, meta=None, key=None, cluster=None):
        self.name, self.design, self.names = name, design, list(names)
        self.i, self.j, self.y = np.asarray(i), np.asarray(j), np.asarray(y)
        self.h = None if h is None else np.asarray(h, dtype=float)
        self.meta = meta or {}
        self.key = key  # optional per-row id used for matching datasets
        self.cluster = cluster  # optional per-row cluster id used by the cluster / block bootstrap (code/btlib/cluster.py)

    def __len__(self):
        return len(self.i)

    def counts(self, home=False, drop_ties=False, rows=None):
        sel = slice(None) if rows is None else rows
        return Counts.from_rows(self.names, self.i[sel], self.j[sel], self.y[sel],
                                None if self.h is None else self.h[sel], home=home, drop_ties=drop_ties)

    def subset(self, mask, name=None):
        mask = np.asarray(mask)
        d = Dataset(name or self.name, self.design, self.names, self.i[mask], self.j[mask], self.y[mask],
                    None if self.h is None else self.h[mask], dict(self.meta),
                    None if self.key is None else self.key[mask], None if self.cluster is None else self.cluster[mask])
        if hasattr(self, "date"):
            d.date = self.date[mask]
        return d


def _encode(a, b):
    names = sorted(set(a) | set(b))
    idx = {m: k for k, m in enumerate(names)}
    return names, np.array([idx[m] for m in a]), np.array([idx[m] for m in b])


def load_arena55k():
    p = path("arena55k.csv")
    d = pd.read_csv(p, usecols=["id", "prompt", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(d.winner_model_a == 1, 0, np.where(d.winner_model_b == 1, 2, 1))
    names, i, j = _encode(d.model_a, d.model_b)
    return Dataset("arena55k", "crowd", names, i, j, y, meta=dict(source=SOURCES["arena55k.csv"]), key=d.id.values,
                   cluster=pd.factorize(d.prompt)[0])  # cluster = identical prompt text (the released file has no user id)


def load_mt(kind="human", ties="tie"):
    """kind: 'human' (expert annotators) or 'gpt4' (GPT-4 pairwise judge). GPT-4's 'tie (inconsistent)' = tie."""
    fname = "mt_human.parquet" if kind == "human" else "mt_gpt4.parquet"
    d = pd.read_parquet(path(fname, verify=fname in CHECKSUMS), columns=["question_id", "model_a", "model_b", "winner", "judge", "turn"])
    names, i, j = _encode(d.model_a, d.model_b)
    y = d.winner.map({"model_a": 0, "model_b": 2}).fillna(1).astype(int).values
    key = np.array([f"{q}|{t}|{min(a, b)}|{max(a, b)}" for q, t, a, b in zip(d.question_id, d.turn, d.model_a, d.model_b)])
    ds = Dataset(f"mt_{kind}", "expert" if kind == "human" else "llm_judge", names, i, j, y,
                 meta=dict(source=SOURCES[fname], inconsistent=int((d.winner == "tie (inconsistent)").sum())), key=key,
                 cluster=pd.factorize(d.question_id)[0])  # cluster = MT-Bench question (80, shared by all model pairs)
    ds.judge = d.judge.values
    ds.question = d.question_id.values
    ds.turn = d.turn.values
    return ds


def load_nba(playoffs=False):
    """One row per game (_iscopy == 0); i = team_id franchise (fran_id), j = opponent franchise; h = +1 if i at home."""
    d = pd.read_csv(path("nbaallelo.csv"), usecols=["_iscopy", "year_id", "date_game", "is_playoffs", "fran_id", "opp_fran", "game_result", "game_location", "game_id"])
    d = d[d._iscopy == 0]
    if not playoffs:
        d = d[d.is_playoffs == 0]
    names, i, j = _encode(d.fran_id, d.opp_fran)
    y = np.where(d.game_result == "W", 0, 2)
    h = d.game_location.map({"H": 1.0, "A": -1.0, "N": 0.0}).values
    ds = Dataset("nba", "sports", names, i, j, y, h=h, meta=dict(source=SOURCES["nbaallelo.csv"], playoffs=playoffs))
    ds.season = d.year_id.values
    ds.date = pd.to_datetime(d.date_game, format="%m/%d/%Y").values.astype("datetime64[D]")
    ds.cluster = ds.season.copy()  # pooled fit: one cluster per season
    return ds


def nba_season(ds, year):
    m = ds.season == year
    d = ds.subset(m, name=f"nba{year}")
    # restrict names to teams that played
    used = np.unique(np.concatenate([d.i, d.j]))
    remap = -np.ones(len(d.names), dtype=int)
    remap[used] = np.arange(len(used))
    d.names = [d.names[k] for k in used]
    d.i, d.j = remap[d.i], remap[d.j]
    d.meta["season"] = int(year)
    d.cluster = ((d.date - d.date.min()).astype(int) // 7)  # one season: block = 7-day week from the first game
    return d
