"""Offline (paper-pipeline) helpers: pinned-data loaders with sha256 checks, bootstrap rank-flip
probability and size-matched subsampling. NOT imported by ``program.py`` (the evaluator's RPC
interface only supplies anonymised tables). Not executed/tested when this candidate was written.

All loaders emit a common comparison table (i, j, outcome) with outcome in {0, 0.5, 1}
(1 = player i wins) and the list of player names. Raw data live under ``data/`` (not in the repo).
Expected files / pinned versions:
  arena-human-preference-55k  commit 18c298340948c0e7f7727399fd459cca6ce0ca6f  train.csv
  mt_bench_human_judgments    commit f7d2896d2cc5d80f8b55c2bbc722613555233c25   human / gpt4_pair parquet
  fivethirtyeight/data nba-elo commit 4c1ff5e3aef1816ae04af63218015066e186c147  nbaallelo.csv
"""
import hashlib

import numpy as np

SHA256 = {
    "arena_55k_train.csv": "0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2",
    "mt_bench_human.parquet": "4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769",
    "nbaallelo.csv": "d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _check(path, key):
    got = sha256_file(path)
    if key in SHA256 and got != SHA256[key]:
        raise ValueError(f"sha256 mismatch for {path}: {got}")
    return got


def _to_table(names_i, names_j, outcome):
    players = sorted(set(names_i) | set(names_j))
    idx = {p: k for k, p in enumerate(players)}
    i = np.array([idx[x] for x in names_i], dtype=np.int64)
    j = np.array([idx[x] for x in names_j], dtype=np.int64)
    return i, j, np.asarray(outcome, dtype=float), players


def load_arena_55k(path):
    import pandas as pd
    _check(path, "arena_55k_train.csv")
    df = pd.read_csv(path, usecols=["model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    out = np.where(df.winner_model_a == 1, 1.0, np.where(df.winner_model_b == 1, 0.0, 0.5))
    return _to_table(df.model_a.tolist(), df.model_b.tolist(), out)


def load_mt_bench(path, judge_filter=None):
    """MT-Bench human or gpt4_pair parquet (columns model_a, model_b, winner in model_a/model_b/tie)."""
    import pandas as pd
    if "human" in str(path):
        _check(path, "mt_bench_human.parquet")
    df = pd.read_parquet(path)
    if judge_filter is not None:
        df = df[df.judge.isin(judge_filter)]
    out = np.where(df.winner == "model_a", 1.0, np.where(df.winner == "model_b", 0.0, 0.5))
    return _to_table(df.model_a.tolist(), df.model_b.tolist(), out)


def load_nba(path):
    """One row per game (_iscopy == 0); home advantage ignored; no ties."""
    import pandas as pd
    _check(path, "nbaallelo.csv")
    df = pd.read_csv(path, usecols=["team_id", "opp_id", "game_result", "_iscopy"])
    df = df[df["_iscopy"] == 0]
    return _to_table(df.team_id.tolist(), df.opp_id.tolist(), (df.game_result == "W").astype(float))


def size_matched_subsample(i, j, y, n_target, seed):
    """Uniform subsample (without replacement) of n_target comparisons, to separate size from design."""
    rng = np.random.default_rng(seed)
    sel = np.sort(rng.choice(len(y), size=min(n_target, len(y)), replace=False))
    return i[sel], j[sel], y[sel]


def bootstrap_rank_flip_probability(i, j, y, m, hi, lo, n_boot=200, seed=0, ridge=1e-3):
    """Fraction of bootstrap resamples (over comparisons) in which ``lo`` is ranked above ``hi``."""
    from program import fit_bradley_terry  # requires src/ on sys.path
    rng = np.random.default_rng(seed)
    theta0 = fit_bradley_terry(i, j, y, m, ridge)
    flips = 0
    for _ in range(n_boot):
        sel = rng.integers(0, len(y), len(y))
        th = fit_bradley_terry(i[sel], j[sel], y[sel], m, ridge, theta0)
        flips += th[lo] > th[hi]
    return flips / n_boot
