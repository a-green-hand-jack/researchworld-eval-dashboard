"""E0 sanity checks and bookkeeping: BT vs NBA 538-Elo ranking, BT vs raw win-rate order, MT-Bench alignment
counts, ABA handling, Wald vs bootstrap s.e.  -> results/sanity_fit.csv, results/alignment.csv, results/sens_aba.csv"""
import sys, os
import numpy as np, pandas as pd
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from experiments import *
import provenance as pv

SEED = 20261108


def sanity():
    rows = []
    n = nba()
    for y in range(1947, 2016):
        B = nba_season_board(n, y, True); beta = B.fit()
        d = n[(n.year_id == y) & (n.lg_id == "NBA")]
        # 538 Elo at the end of the regular season: last regular-season row of each team
        reg = d[d.is_playoffs == 0].sort_values("gameorder")
        last = reg.groupby("team_id").elo_n.last()
        t = kendalltau(beta[:B.P], last.reindex(B.names).values)[0]
        wr = np.zeros(B.P); gm = np.zeros(B.P)
        np.add.at(wr, B.i, B.W + 0.5 * B.T); np.add.at(wr, B.j, B.L + 0.5 * B.T)
        np.add.at(gm, B.i, B.W + B.L + B.T); np.add.at(gm, B.j, B.W + B.L + B.T)
        rows.append(dict(board="nba_season", unit_id=y, tau_bt_vs_538elo=t, tau_bt_vs_winrate=kendalltau(beta[:B.P], wr / gm)[0],
                         top1_bt=B.names[int(np.argmax(beta[:B.P]))], top1_elo=last.idxmax(), same_top1=B.names[int(np.argmax(beta[:B.P]))] == last.idxmax()))
    for lab, (df, nm) in dict(arena55k=arena55k(), mtbench_human=mtbench("human"), mtbench_gpt4=mtbench("gpt4")).items():
        B = mt_board(df, nm); beta = B.fit()
        wr = np.zeros(B.P); gm = np.zeros(B.P)
        np.add.at(wr, B.i, B.W + 0.5 * B.T); np.add.at(wr, B.j, B.L + 0.5 * B.T)
        np.add.at(gm, B.i, B.W + B.L + B.T); np.add.at(gm, B.j, B.W + B.L + B.T)
        rows.append(dict(board=lab, unit_id=0, tau_bt_vs_winrate=kendalltau(beta[:B.P], wr / gm)[0],
                         top1_bt=nm[int(np.argmax(beta[:B.P]))], order_bt=">".join(nm[k] for k in np.argsort(-beta[:B.P])[:8])))
    return pd.DataFrame(rows)


def alignment():
    mm, names = mt_matched()
    h, _ = mtbench("human"); g, _ = mtbench("gpt4")
    return pd.DataFrame([dict(item="human_rows_total", n=len(h)), dict(item="gpt4_rows_total", n=len(g)),
                         dict(item="keys_human", n=int(h.assign(k=[(q, t, min(a, b), max(a, b)) for q, t, a, b in zip(h.question_id, h.turn, h.model_a, h.model_b)]).k.nunique())),
                         dict(item="keys_common", n=int(mm["g"].key.nunique())),
                         dict(item="human_rows_matched", n=len(mm["h"])), dict(item="gpt4_rows_matched", n=len(mm["g"])),
                         dict(item="gpt4_rows_dropped_no_human", n=len(g) - len(mm["g"])),
                         dict(item="human_rows_dropped_no_gpt4", n=len(h) - len(mm["h"])),
                         dict(item="human_one_per_key_rows", n=len(mm["h1"]))])


def aba():
    n = nba()
    rows = []
    for y in range(1968, 1977):
        d = n[n.year_id == y]
        if "ABA" not in set(d.lg_id):
            continue
        for var, dd in (("all", d), ("nba_only", d[d.lg_id == "NBA"]), ("aba_only", d[d.lg_id == "ABA"])):
            teams = sorted(set(dd.team_id) | set(dd.opp_id)); ix = {t: k for k, t in enumerate(teams)}
            dd = dd[(dd.is_playoffs == 0)]
            if len(dd) < 100:
                continue
            away = (dd.game_location == "A").values
            a, b = dd.team_id.map(ix).values, dd.opp_id.map(ix).values
            o = np.where(dd.game_result == "W", 1.0, 0.0)
            B = board_from_records(np.where(away, b, a), np.where(away, a, b), np.where(away, 1 - o, o), len(teams), teams,
                                   home=(dd.game_location != "N").values.astype(float))
            r = claim_rows(B, B.fit(), claims=("C1", "C2"), perts=("P1",))
            for x in r:
                x.update(board="nba_season", variant="league_" + var, unit_id=y, design="sports")
            rows += r
    return pd.DataFrame(rows)


if __name__ == "__main__":
    src = [f"{DATA}/arena55k/train.csv", f"{DATA}/nba/nbaallelo.csv"] + sorted(
        f"{DATA}/mtbench/{f}" for f in os.listdir(f"{DATA}/mtbench"))
    pv.save(sanity(), "sanity_fit.csv", "run_extra.py", SEED, src)
    pv.save(alignment(), "alignment.csv", "run_extra.py", SEED, src)
    pv.save(aba(), "sens_aba.csv", "run_extra.py", SEED, src)
