"""Aggregation rules (reference implementations on a full score matrix).

S is an (m models x n tasks) array of scores in points (higher is better).
Every rule maps S to a length-m vector of aggregate scores; model t is
"first" iff its score is strictly larger than every other model's score.
These are deliberately simple, independent of the solvers in `solvers.py`,
and are used to validate them.
"""
import numpy as np

CARDINAL = ["mean", "geo", "median", "min", "trim"]
POWER_PS = [-2.0, -1.0, 0.5, 2.0, 4.0, 8.0]          # power-mean grid besides min, geo(p=0), mean(p=1)
CARDINAL_POWER = [f"pmean:{p:g}" for p in POWER_PS]
ORDINAL = ["borda", "plurality", "copeland", "condorcet"]
TRIM = 0.2      # trimmed mean: drop floor(TRIM*n) tasks at each end
RULES = CARDINAL + ORDINAL                           # core set (all boards)
ALL_RULES = RULES + CARDINAL_POWER


def _cmp(a, b):
    """1 if a>b, .5 if equal, 0 if a<b (elementwise)."""
    return (a > b) + 0.5 * (a == b)


def scores(S, rule):
    S = np.asarray(S, float)
    m, n = S.shape
    if rule == "mean":
        return S.mean(1)
    if rule == "geo":  # geometric mean of (s+1), minus 1: defined at s=0
        return np.exp(np.log(S + 1.0).mean(1)) - 1.0
    if rule == "median":
        return np.median(S, 1)
    if rule == "trim":
        h = int(TRIM * n)
        return np.sort(S, 1)[:, h:n - h].mean(1)
    if rule.startswith("pmean:"):  # power mean of (s+1), minus 1 (shift keeps p<0 defined at s=0)
        p = float(rule.split(":")[1])
        return np.mean((S + 1.0) ** p, 1) ** (1.0 / p) - 1.0
    if rule == "min":
        return S.min(1)
    if rule == "borda":  # sum over tasks of #models beaten (ties half)
        from scipy.stats import rankdata
        return sum(rankdata(S[:, j]) - 1.0 for j in range(n))  # = #below + .5 #ties
    if rule == "plurality":  # #tasks on which the model is best (ties split)
        out = np.zeros(m)
        for j in range(n):
            top = S[:, j] == S[:, j].max()
            out += top / top.sum()
        return out
    if rule == "copeland":  # pairwise-majority wins + half the draws
        W = np.zeros((m, m))
        for j in range(n):
            W += _cmp(S[:, j][:, None], S[:, j][None, :])
        res = (W > n / 2) + 0.5 * (W == n / 2)
        np.fill_diagonal(res, 0.0)
        return res.sum(1)
    if rule == "condorcet":
        # score = number of rivals beaten by strict pairwise majority of tasks;
        # the Condorcet winner (m-1) is the only model that can be "first"
        # (every other model has a loss, so it scores below m-1).
        W = np.zeros((m, m))
        for j in range(n):
            W += _cmp(S[:, j][:, None], S[:, j][None, :])
        beat = W > n / 2
        np.fill_diagonal(beat, False)
        return beat.sum(1).astype(float)
    raise ValueError(rule)


def is_first(S, t, rule):
    if rule == "condorcet":  # must beat every rival by pairwise majority
        W = _cmp(S[t][None, :], S).sum(1)
        W = np.delete(W, t)
        return bool(np.all(W > S.shape[1] / 2))
    sc = scores(S, rule)
    other = np.delete(sc, t)
    return bool(sc[t] > other.max())
