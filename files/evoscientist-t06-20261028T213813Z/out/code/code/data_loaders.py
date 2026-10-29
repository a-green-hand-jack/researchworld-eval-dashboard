"""Load the raw datasets in /work/data into Board objects (aggregated pairwise-comparison cells)."""
import os
import numpy as np
import pandas as pd
import scipy.sparse as sp
from bt import Board

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def _unordered_board(name, dataset, design, df, ma='model_a', mb='model_b', outcome='outcome', cluster=None, meta=None):
    """df has columns ma, mb and outcome in {'a','b','tie'}; build unordered-pair cells."""
    ents = sorted(set(df[ma]) | set(df[mb]))
    idx = {e: i for i, e in enumerate(ents)}
    a = df[ma].map(idx).to_numpy()
    b = df[mb].map(idx).to_numpy()
    o = df[outcome].to_numpy()
    swap = a > b
    lo = np.where(swap, b, a)
    hi = np.where(swap, a, b)
    oc = np.where(o == 'tie', 2, np.where(o == 'a', 0, 1))
    oc = np.where(swap & (oc < 2), 1 - oc, oc)  # swapped => a-win becomes lo's loss
    n = len(ents)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    pid = {p: k for k, p in enumerate(pairs)}
    cell = np.array([pid[(i, j)] for i, j in zip(lo, hi)])
    C = len(pairs)
    W = np.zeros((C, 3))
    np.add.at(W, (cell, oc), 1)
    X = np.zeros((C, n))
    for k, (i, j) in enumerate(pairs):
        X[k, i], X[k, j] = 1, -1
    clusters = None
    if cluster is not None:
        cl = pd.factorize(df[cluster])[0]
        G = cl.max() + 1
        clusters = sp.csr_matrix((np.ones(len(cl)), (cl, cell * 3 + oc)), shape=(G, C * 3))
    return Board(name, dataset, design, ents, X, W, clusters=clusters, meta=meta)


def load_arena():
    df = pd.read_csv(os.path.join(DATA, 'arena55k.csv'),
                     usecols=['model_a', 'model_b', 'winner_model_a', 'winner_model_b', 'winner_tie'])
    df['outcome'] = np.where(df.winner_tie == 1, 'tie', np.where(df.winner_model_a == 1, 'a', 'b'))
    return _unordered_board('arena55k', 'Chatbot Arena (55k)', 'crowd votes', df)


def _mt(path):
    df = pd.read_parquet(os.path.join(DATA, path), columns=['question_id', 'model_a', 'model_b', 'winner', 'judge', 'turn'])
    df['outcome'] = df.winner.map(lambda w: 'a' if w == 'model_a' else ('b' if w == 'model_b' else 'tie'))
    return df


def load_mtbench():
    h = _mt('mt_human.parquet')
    g = _mt('mt_gpt4.parquet')
    key = lambda d: d.question_id.astype(str) + '|' + d.turn.astype(str) + '|' + d[['model_a', 'model_b']].apply(
        lambda r: '/'.join(sorted(r)), axis=1)
    h['key'], g['key'] = key(h), key(g)
    gm = g[g.key.isin(set(h.key))]
    return [
        _unordered_board('mt_human', 'MT-Bench human experts', 'expert annotation', h, cluster='question_id'),
        _unordered_board('mt_gpt4', 'MT-Bench GPT-4 judge', 'LLM judge', g, cluster='question_id'),
        _unordered_board('mt_gpt4_matched', 'MT-Bench GPT-4 judge (matched items)', 'LLM judge', gm, cluster='question_id'),
    ]


def load_nba(min_teams=8):
    n = pd.read_csv(os.path.join(DATA, 'nbaallelo.csv'),
                    usecols=['game_id', '_iscopy', 'year_id', 'is_playoffs', 'team_id', 'opp_id', 'game_location', 'game_result'])
    n = n[(n._iscopy == 0) & (n.is_playoffs == 0)]
    boards = []
    for yr, d in n.groupby('year_id'):
        loc = d.game_location.to_numpy()
        # orient so that 'a' = home team when location known
        a = np.where(loc == 'A', d.opp_id, d.team_id)
        b = np.where(loc == 'A', d.team_id, d.opp_id)
        res_team = np.where(d.game_result.to_numpy() == 'W', d.team_id.to_numpy(), d.opp_id.to_numpy())
        won_a = res_team == a
        home = (loc != 'N').astype(float)
        ents = sorted(set(a) | set(b))
        if len(ents) < min_teams:
            continue
        idx = {e: i for i, e in enumerate(ents)}
        ai = np.array([idx[x] for x in a]); bi = np.array([idx[x] for x in b])
        nt = len(ents)
        # cells: ordered (a,b,home flag)
        keys = {}
        rows = []
        for x, y, h in zip(ai, bi, home):
            k = (x, y, h)
            if k not in keys:
                keys[k] = len(keys)
        # add all home-oriented ordered pairs so inserted votes may land anywhere
        for x in range(nt):
            for y in range(nt):
                if x != y and (x, y, 1.0) not in keys:
                    keys[(x, y, 1.0)] = len(keys)
        C = len(keys)
        X = np.zeros((C, nt + 1))
        ins_ok = np.zeros(C, bool)
        for (x, y, h), c in keys.items():
            X[c, x], X[c, y], X[c, nt] = 1, -1, h
            ins_ok[c] = h == 1.0
        cell = np.array([keys[(x, y, h)] for x, y, h in zip(ai, bi, home)])
        W = np.zeros((C, 3))
        np.add.at(W, (cell, np.where(won_a, 0, 1)), 1)
        b_ = Board(f'nba_{int(yr)}', 'NBA regular seasons', 'sports results', ents + ['HOME'], X, W, ins_ok=ins_ok,
                   meta={'year': int(yr)})
        b_.n_ent = nt  # only team parameters are rankable
        boards.append(b_)
    return boards


def load_arena140k(min_battles=200):
    import glob
    fs = sorted(glob.glob(os.path.join(DATA, 'arena140k', '*.parquet')))
    df = pd.concat([pd.read_parquet(f, columns=['model_a', 'model_b', 'winner', 'evaluation_session_id']) for f in fs],
                   ignore_index=True)
    df['outcome'] = df.winner.map(lambda w: 'a' if w == 'model_a' else ('b' if w == 'model_b' else 'tie'))
    cnt = pd.concat([df.model_a, df.model_b]).value_counts()
    keep = set(cnt[cnt >= min_battles].index)
    df = df[df.model_a.isin(keep) & df.model_b.isin(keep) & (df.model_a != df.model_b)]
    return _unordered_board('arena140k', 'Chatbot Arena (140k)', 'crowd votes', df, cluster='evaluation_session_id')
