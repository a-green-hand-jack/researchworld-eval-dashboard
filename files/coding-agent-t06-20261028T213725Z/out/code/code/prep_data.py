"""Convert the raw public datasets into a common comparison format.

Every output file (data/processed/<name>.csv) has one row per comparison with
columns  a, b, y, h :
  a, b : competitor names
  y    : outcome for a (1 = a wins, 0 = b wins, 0.5 = tie)
  h    : home indicator for a (+1 home, -1 away, 0 neutral / not applicable)

Usage:  python -I code/prep_data.py  [--data data]
"""
import argparse
import json
import os

import pandas as pd

MIN_COMPARISONS = 100  # competitors with fewer comparisons are removed (see paper, Sec. 4)


def filter_rare(df, min_n=MIN_COMPARISONS):
    while True:
        cnt = pd.concat([df.a, df.b]).value_counts()
        rare = set(cnt[cnt < min_n].index)
        if not rare:
            return df.reset_index(drop=True)
        df = df[~df.a.isin(rare) & ~df.b.isin(rare)]


def save(df, out, name):
    df = filter_rare(df[["a", "b", "y", "h"]].copy())
    df.to_csv(os.path.join(out, name + ".csv"), index=False)
    k = len(set(df.a) | set(df.b))
    print(f"{name:28s} N={len(df):7d} K={k:3d} tie-rate={(df.y == 0.5).mean():.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    args = ap.parse_args()
    D = args.data
    out = os.path.join(D, "processed")
    os.makedirs(out, exist_ok=True)

    # ---- Chatbot Arena 55k (crowdsourced human votes) ----
    ar = pd.read_csv(os.path.join(D, "arena55k/train.csv"),
                     usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    ar["y"] = ar.winner_model_a * 1.0 + ar.winner_tie * 0.5
    ar = ar.rename(columns={"model_a": "a", "model_b": "b"})
    ar["h"] = 0
    save(ar, out, "arena55k")

    # ---- LLM judges on the single-turn subset of the same battles ----
    jfiles = sorted(os.listdir(os.path.join(D, "judges_avg")))
    ids = None
    for sub, tag in [("judges_avg", "judge"), ("judges", "judgeraw")]:
        for f in jfiles:
            j = pd.read_json(os.path.join(D, sub, f), lines=True)
            m = j.merge(ar[["id", "a", "b", "y"]], on="id", how="inner")
            assert len(m) == len(j)
            m["y"] = m.winner_pred.map({"A": 1.0, "B": 0.0, "tie": 0.5})
            m["h"] = 0
            save(m, out, f"{tag}_{f.replace('.jsonl', '')}")
            ids = set(j.id) if ids is None else ids & set(j.id)
    # matched human reference: the same single-turn battles labelled by Arena users
    hs = ar[ar.id.isin(ids)].copy()
    save(hs, out, "arena55k_singleturn_human")

    # ---- Chatbot Arena 140k (2025) ----
    import pyarrow.parquet as pq
    t = pq.read_table(os.path.join(D, "arena140k"), columns=["model_a", "model_b", "winner"]).to_pandas()
    t["y"] = t.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "both_bad": 0.5})
    t = t.rename(columns={"model_a": "a", "model_b": "b"})
    t["h"] = 0
    save(t, out, "arena140k")

    # ---- WebDev Arena ----
    w = pd.DataFrame(json.load(open(os.path.join(D, "webdev/webdev-arena-preference-10k.json"))))
    w["y"] = w.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (bothbad)": 0.5})
    w = w.rename(columns={"model_a": "a", "model_b": "b"})
    w["h"] = 0
    save(w, out, "webdev")

    # ---- MT-Bench: expert humans and GPT-4 pairwise judge ----
    for f, name in [("human.parquet", "mtbench_human"), ("gpt4_pair.parquet", "mtbench_gpt4")]:
        m = pd.read_parquet(os.path.join(D, "mtbench", f), columns=["model_a", "model_b", "winner", "turn"])
        m["y"] = m.winner.map({"model_a": 1.0, "model_b": 0.0, "tie": 0.5, "tie (inconsistent)": 0.5})
        m = m.rename(columns={"model_a": "a", "model_b": "b"})
        m["h"] = 0
        save(m, out, name)

    # ---- NBA regular seasons (one leaderboard per season) ----
    n = pd.read_csv(os.path.join(D, "nba/nbaallelo.csv"))
    n = n[(n.lg_id == "NBA") & (n._iscopy == 0) & (n.is_playoffs == 0)]
    n["y"] = (n.game_result == "W").astype(float)
    n["h"] = n.game_location.map({"H": 1, "A": -1, "N": 0})
    n = n.rename(columns={"team_id": "a", "opp_id": "b"})
    os.makedirs(os.path.join(out, "nba"), exist_ok=True)
    for yr, g in n.groupby("year_id"):
        g[["a", "b", "y", "h"]].to_csv(os.path.join(out, "nba", f"nba_{yr}.csv"), index=False)
    print("NBA seasons:", n.year_id.nunique(), "games:", len(n))


if __name__ == "__main__":
    main()
