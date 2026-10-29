"""Build comparison data sets (a, b, y, names[, extra]) from raw files in data/.
Output: data/processed/<name>.npz   (run: python code/data_prep.py)
y = 1 if a wins, 0 if b wins, 0.5 for a tie.
"""
import json, os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data")
OUT = os.path.join(RAW, "processed")
os.makedirs(OUT, exist_ok=True)


def save(name, a_names, b_names, y, extra=None, meta=None):
    names = sorted(set(a_names) | set(b_names))
    idx = {n: k for k, n in enumerate(names)}
    a = np.array([idx[n] for n in a_names])
    b = np.array([idx[n] for n in b_names])
    d = dict(a=a, b=b, y=np.asarray(y, float), names=np.array(names))
    if extra is not None:
        d["extra"] = np.asarray(extra, float)
    np.savez(os.path.join(OUT, name + ".npz"), **d)
    print(f"{name}: N={len(a)} M={len(names)} tie_frac={(np.asarray(y)==0.5).mean():.3f}")


def arena():
    df = pd.read_csv(os.path.join(RAW, "arena55k.csv"),
                     usecols=["id", "model_a", "model_b", "winner_model_a", "winner_model_b", "winner_tie"])
    y = np.where(df.winner_tie == 1, 0.5, df.winner_model_a.astype(float))
    assert ((df.winner_model_a + df.winner_model_b + df.winner_tie) == 1).all()
    save("arena55k_human", df.model_a, df.model_b, y)
    m = (df.winner_tie == 0).values  # sensitivity variant: ties removed
    save("arena55k_noties", df.model_a[m], df.model_b[m], y[m])


def mtbench():
    for nm, f in [("mtbench_human", "mt_human.parquet"), ("mtbench_gpt4", "mt_gpt4.parquet")]:
        df = pd.read_parquet(os.path.join(RAW, f), columns=["model_a", "model_b", "winner", "judge", "turn"])
        y = df.winner.map({"model_a": 1.0, "model_b": 0.0}).fillna(0.5).values  # tie / tie (inconsistent) -> .5
        save(nm, df.model_a, df.model_b, y)


def nba():
    df = pd.read_csv(os.path.join(RAW, "nbaallelo.csv"))
    df = df[df._iscopy == 0]
    assert len(df) == 63157
    y = (df.game_result == "W").astype(float).values
    loc = df.game_location.map({"H": 1.0, "A": -1.0, "N": 0.0}).values
    reg = df.is_playoffs.values == 0
    for yr in range(1980, 2016):
        m = reg & (df.year_id.values == yr)
        save(f"nba_{yr}", df.fran_id[m], df.opp_fran[m], y[m], extra=loc[m].reshape(-1, 1))
        save(f"nba_{yr}_nohome", df.fran_id[m], df.opp_fran[m], y[m])  # sensitivity: no home-advantage term
    # all-time regular season, franchises
    save("nba_alltime", df.fran_id[reg], df.opp_fran[reg], y[reg], extra=loc[reg].reshape(-1, 1))


def judges():
    tr = json.load(open(os.path.join(RAW, "train.single-turn.json")))
    meta = {int(r["id"]): (r["model_a"], r["model_b"], r["winner_model_a"], r["winner_tie"]) for r in tr}
    ids = np.array(sorted(meta))
    ma = [meta[i][0] for i in ids]
    mb = [meta[i][1] for i in ids]
    yh = np.array([0.5 if int(meta[i][3]) == 1 else float(int(meta[i][2])) for i in ids])
    save("arenaST_human", ma, mb, yh)
    pos = {i: k for k, i in enumerate(ids)}
    for fn in sorted(os.listdir(os.path.join(RAW, "judges"))):
        jn = fn.replace(".avg.jsonl", "")
        yj = np.full(len(ids), np.nan)
        for line in open(os.path.join(RAW, "judges", fn)):
            r = json.loads(line)
            yj[pos[r["id"]]] = {"A": 1.0, "B": 0.0, "C": 0.5, "tie": 0.5}[r["winner_pred"]]
        assert not np.isnan(yj).any()
        print(jn, "agreement with human (3-way):", (yj == yh).mean().round(4))
        save("arenaST_judge_" + jn, ma, mb, yj)


if __name__ == "__main__":
    arena(); mtbench(); nba(); judges()
