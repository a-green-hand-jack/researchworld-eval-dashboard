"""E5 sensitivity: tie handling, home/no-home, playoffs, pooled NBA seasons, BT vs online-Elo ranker and arrival order.
-> results/sensitivity.csv (k* rows, same columns as kstar_full + variant), results/elo_order.csv"""
import sys, os, time
import numpy as np, pandas as pd
from scipy.stats import kendalltau
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from experiments import *
import provenance as pv

SEED = 20261106


def tag(rows, **kw):
    for r in rows:
        r.update(kw)
    return rows


def nba_games(years, home=True, playoffs=False):
    n = nba(playoffs=playoffs)
    d = n[n.year_id.isin(years)]
    teams = sorted(set(d.team_id) | set(d.opp_id))
    ix = {t: k for k, t in enumerate(teams)}
    a, b = d.team_id.map(ix).values, d.opp_id.map(ix).values
    o = np.where(d.game_result == "W", 1.0, 0.0)
    if not home:
        return board_from_records(a, b, o, len(teams), teams)
    away = (d.game_location == "A").values
    return board_from_records(np.where(away, b, a), np.where(away, a, b), np.where(away, 1 - o, o), len(teams), teams,
                              home=(d.game_location != "N").values.astype(float))


_JOBS = None


def variant_job(k):
    global _JOBS
    if _JOBS is not None:
        return _JOBS
    a, an = arena55k(); h, mn = mtbench("human"); g, _ = mtbench("gpt4")
    jobs = []
    for lab, df, nm, des in (("arena55k", a, an, "crowd"), ("mtbench_human", h, mn, "expert"), ("mtbench_gpt4", g, mn, "model-judge")):
        jobs.append((lab, des, "tie_half", lambda df=df, nm=nm: mt_board(df, nm)))
        jobs.append((lab, des, "tie_dropped", lambda df=df, nm=nm: mt_board(df[df.o != 0.5], nm)))
    # NBA season variants (every season 1947-2015 -> unit)
    for y in range(1947, 2016):
        jobs.append(("nba_season", "sports", "no_home", lambda y=y: nba_games([y], home=False)))
        jobs.append(("nba_season", "sports", "with_playoffs", lambda y=y: nba_games([y], home=True, playoffs=True)))
    for span in (5, 10, 20):
        jobs.append(("nba_pooled", "sports", f"pooled_{span}", lambda s=span: nba_games(range(2016 - s, 2016))))
    _JOBS = jobs
    return jobs


def run_variant(k):
    jobs = variant_job(0)
    lab, des, var, mk = jobs[k]
    B = mk(); beta = B.fit()
    claims = ("C1", "C2", "C4") if B.N > 1000 else ("C1", "C2", "C4")
    rows = claim_rows(B, beta, claims=claims)
    uid = int(var.split("_")[-1]) if var.startswith("pooled") else 0
    return tag(rows, board=lab, design=des, variant=var, unit_type="variant", unit_id=k)


# ---------------------------------------------------------------- BT vs online Elo, arrival order
def elo_run(order_idx, a_idx, b_idx, o, P, K, hfa=None, home=None):
    r = np.zeros(P)
    for t in order_idx:
        i, j = a_idx[t], b_idx[t]
        d = r[i] - r[j] + (hfa * home[t] if hfa else 0.0)
        e = 1.0 / (1.0 + 10 ** (-d / 400.0))
        r[i] += K * (o[t] - e); r[j] -= K * (o[t] - e)
    return r


def elo_study(label, a_idx, b_idx, o, P, K, nperm, rng, home=None, hfa=None, bt_beta=None):
    r0 = elo_run(np.arange(len(o)), a_idx, b_idx, o, P, K, hfa, home)
    rows = []
    top_ref = int(np.argmax(r0))
    taus_bt, taus_ref, same_top, same_top_bt = [], [], [], []
    for p in range(nperm):
        r = elo_run(rng.permutation(len(o)), a_idx, b_idx, o, P, K, hfa, home)
        taus_bt.append(kendalltau(r, bt_beta[:P])[0]); taus_ref.append(kendalltau(r, r0)[0])
        same_top.append(int(np.argmax(r)) == top_ref); same_top_bt.append(int(np.argmax(r)) == int(np.argmax(bt_beta[:P])))
    return dict(board=label, K=K, n_perm=nperm, tau_elo_vs_bt_mean=np.mean(taus_bt), tau_elo_vs_bt_sd=np.std(taus_bt),
                tau_perm_vs_ref_mean=np.mean(taus_ref), tau_perm_vs_ref_sd=np.std(taus_ref),
                p_top1_same_as_ref=np.mean(same_top), p_top1_same_as_bt=np.mean(same_top_bt))


def elo_all():
    rng = np.random.default_rng(SEED)
    rows = []
    a, an = arena55k()
    B = arena_board(a, an); bt = B.fit()
    for K in (4, 32):
        rows.append(elo_study("arena55k", a.a.values, a.b.values, a.o.values, len(an), K, 40, rng, bt_beta=bt))
    n = nba()
    for y in (1990, 2005, 2015):
        d = n[(n.year_id == y) & (n.is_playoffs == 0)]
        teams = sorted(set(d.team_id) | set(d.opp_id)); ix = {t: k for k, t in enumerate(teams)}
        ai, bi = d.team_id.map(ix).values, d.opp_id.map(ix).values
        o = np.where(d.game_result == "W", 1.0, 0.0)
        away = (d.game_location == "A").values
        ai2, bi2, o2 = np.where(away, bi, ai), np.where(away, ai, bi), np.where(away, 1 - o, o)
        hm = np.ones(len(d))
        Bn = nba_season_board(n, y, True); btn = Bn.fit()
        # the BT fit beta[:P] uses sorted team ids as does ix
        for K in (20,):
            rows.append(elo_study(f"nba_{y}", ai2, bi2, o2, len(teams), K, 200, rng, home=hm, hfa=100.0, bt_beta=btn))
    h, mn = mtbench("human"); Bm = mt_board(h, mn); btm = Bm.fit()
    for K in (4, 32):
        rows.append(elo_study("mtbench_human", h.a.values, h.b.values, h.o.values, len(mn), K, 200, rng, bt_beta=btm))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    src = [f"{DATA}/arena55k/train.csv", f"{DATA}/nba/nbaallelo.csv"] + sorted(
        f"{DATA}/mtbench/{f}" for f in os.listdir(f"{DATA}/mtbench"))
    n = len(variant_job(0))
    with Pool(2) as p:
        res = p.map(run_variant, range(n), chunksize=1)
    pv.save(pd.DataFrame([r for x in res for r in x]), "sensitivity.csv", "run_sens.py", SEED, src)
    pv.save(elo_all(), "elo_order.csv", "run_sens.py", SEED, src, note="uniform random arrival orders; no timestamps in Arena 55k")
