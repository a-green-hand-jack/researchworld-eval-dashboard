import numpy as np, pandas as pd, json, os
from btlib import build_board

D = os.environ.get("DATA_DIR", "/work/data")


def _from_names(df, ca, cb, y, outcomes=(0.0, 0.5, 1.0), h=None, min_comp=0, **kw):
    names = sorted(set(df[ca]) | set(df[cb]))
    idx = {n: i for i, n in enumerate(names)}
    return build_board(names, df[ca].map(idx).values, df[cb].map(idx).values, y,
                       h=h, outcomes=outcomes, **kw)


def arena55k(ties="half", **kw):
    df = pd.read_csv(f"{D}/arena55k/train.csv", usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(df.winner_tie == 1, 0.5, np.where(df.winner_model_a == 1, 1.0, 0.0))
    if ties == "drop":
        keep = df.winner_tie.values == 0
        return _from_names(df[keep], "model_a", "model_b", y[keep], outcomes=(0.0, 1.0), **kw)
    return _from_names(df, "model_a", "model_b", y, **kw)


def mtbench(kind="human", turn=None, **kw):
    f = "human" if kind == "human" else "gpt4_pair"
    df = pd.read_parquet(f"{D}/mtbench/{f}.parquet", columns=["model_a", "model_b", "winner", "turn"])
    if turn is not None:
        df = df[df.turn == turn]
    w = df.winner.values
    y = np.where(w == "model_a", 1.0, np.where(w == "model_b", 0.0, 0.5))
    return _from_names(df, "model_a", "model_b", y, **kw)


JUDGES = ["Athene-70B", "Hermes-3-Llama-3.1-70B", "Meta-Llama-3-70B-Instruct", "Meta-Llama-3-8B-Instruct",
          "Meta-Llama-3-8B", "Mistral-7B-Instruct-v0.1", "Mistral-7B-Instruct-v0.2", "Mistral-7B-OpenOrca",
          "Mixtral-8x7B-Instruct-v0.1", "OpenHermes-2-Mistral-7B", "OpenHermes-2.5-Mistral-7B", "Qwen2-72B-Instruct",
          "StableBeluga-7B", "Starling-LM-7B-alpha", "dolphin-2.1-mistral-7b", "dolphin-2.5-mixtral-8x7b", "zephyr-7b-beta"]


def arena_judged(judge="human", **kw):
    """Same 49,938 single-turn Arena battles; outcome from the human vote ('human') or from an LLM judge."""
    base = pd.read_json(f"{D}/judges/train.single-turn.json")[["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"]]
    if judge == "human":
        y = np.where(base.winner_tie == 1, 0.5, np.where(base.winner_model_a == 1, 1.0, 0.0))
        return _from_names(base, "model_a", "model_b", y, **kw)
    rows = pd.read_json(f"{D}/judges/{judge}.jsonl", lines=True)[["id", "winner_pred"]]
    df = base.merge(rows, on="id", how="inner")
    assert len(df) == len(base)
    y = df.winner_pred.map({"A": 1.0, "B": 0.0, "tie": 0.5}).values
    return _from_names(df, "model_a", "model_b", y, **kw)


def nba_seasons(playoffs=False, home=True, **kw):
    df = pd.read_csv(f"{D}/nba/nbaallelo.csv", usecols=["game_id", "_iscopy", "year_id", "is_playoffs", "fran_id", "opp_fran", "game_location", "game_result"])
    df = df[(df._iscopy == 0) & (df.is_playoffs == (1 if playoffs else 0))]
    out = {}
    for yr, g in df.groupby("year_id"):
        y = (g.game_result == "W").astype(float).values
        h = (g.game_location == "H").astype(int).values
        # 'A' rows: team is away -> swap so that first listed team is home
        aw = (g.game_location == "A").values
        ca = np.where(aw, g.opp_fran, g.fran_id); cb = np.where(aw, g.fran_id, g.opp_fran)
        y = np.where(aw, 1 - y, y)
        h = np.where(aw, 1, h)
        gg = pd.DataFrame(dict(a=ca, b=cb))
        out[int(yr)] = _from_names(gg, "a", "b", y, outcomes=(0.0, 1.0), h=h if home else None, all_pairs=False, **kw)
    return out


def arena140k(**kw):
    """Arena 140k snapshot: ties and 'both_bad' are both scored as ties (half win)."""
    import glob, pyarrow.parquet as pq
    cache = f"{D}/arena140k_min.csv"
    if not os.path.exists(cache):
        fs = sorted(glob.glob(f"{D}/arena140k/*.parquet"))
        df = pd.concat([pq.read_table(f, columns=["model_a", "model_b", "winner"]).to_pandas() for f in fs])
        df.to_csv(cache, index=False)
    df = pd.read_csv(cache)
    y = np.where(df.winner == "model_a", 1.0, np.where(df.winner == "model_b", 0.0, 0.5))
    return _from_names(df, "model_a", "model_b", y, **kw)
