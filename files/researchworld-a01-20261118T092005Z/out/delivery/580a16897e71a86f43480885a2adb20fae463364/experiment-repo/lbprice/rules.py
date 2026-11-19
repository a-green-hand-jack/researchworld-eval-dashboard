"""Aggregation rules and the evaluator that decides whether a model is first.

Scores S are (N models x m tasks) arrays in *points* (0..100). Every rule maps S to a vector of aggregate
scores (higher is better); a model is first when its aggregate exceeds every rival's by a margin.
Rules: mean, zmean (mean of scores / sigma_j), median, min, quantile r (r-th largest), borda (= mean win
rate, ties count 1/2), plurality (strict task wins), copeland (pairwise majority, ties 1/2).
"""
import numpy as np

RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]
# aggregate-valued rules: rival's score does not depend on the target
AGG_RULES = {"mean", "zmean", "median", "min", "quantile", "gmean"}
RANK_RULES = {"borda", "plurality", "copeland"}


def borda_scores(S):
    """Sum over tasks and rivals of [s_ij > s_kj] + 0.5 [s_ij == s_kj]; divided by m (N-1) gives the mean win rate."""
    N, m = S.shape
    out = np.zeros(N)
    for j in range(m):
        col = S[:, j]
        srt = np.sort(col)
        less = np.searchsorted(srt, col, side="left")
        leq = np.searchsorted(srt, col, side="right")
        out += less + 0.5 * (leq - less - 1)
    return out


def plurality_scores(S):
    """Number of tasks on which the model is strictly best."""
    top = S.argmax(axis=0)
    mx = S.max(axis=0)
    unique = (S == mx).sum(axis=0) == 1
    out = np.zeros(S.shape[0])
    for j in np.where(unique)[0]:
        out[top[j]] += 1
    return out


def copeland_scores(S, chunk=256):
    """Copeland score with ties 1/2: number of rivals beaten on more tasks than they win, plus 1/2 per pairwise tie."""
    N, m = S.shape
    out = np.zeros(N)
    for a in range(0, N, chunk):
        blk = S[a:a + chunk]
        win = (blk[:, None, :] > S[None, :, :]).sum(axis=2)
        los = (blk[:, None, :] < S[None, :, :]).sum(axis=2)
        res = np.sign(win - los).astype(float)
        idx = np.arange(a, min(a + chunk, N))
        res[idx - a, idx] = -1.0  # exclude self
        out[a:a + chunk] = (res == 1).sum(axis=1) + 0.5 * (res == 0).sum(axis=1)
    return out


_C0_CACHE = {}


def copeland_cached(S):
    """Copeland scores of S, cached on the board (target-independent)."""
    key = (S.shape, float(S.sum()), float((S * np.arange(1, S.shape[1] + 1)).sum()), float(S[:, 0] @ np.arange(S.shape[0])))
    if key not in _C0_CACHE:
        if len(_C0_CACHE) > 3: _C0_CACHE.clear()
        _C0_CACHE[key] = copeland_scores(S)
    return _C0_CACHE[key]


def copeland_after_boost(S, t, row, C0):
    """Copeland scores of S with row t replaced by `row`, from the cached scores C0 of S (O(N m))."""
    N = S.shape[0]
    others = np.delete(np.arange(N), t)
    def out(r):  # what each other model earns against a model with score row r
        win = (S[others] > r[None, :]).sum(1); los = (S[others] < r[None, :]).sum(1)
        return np.where(win > los, 1.0, np.where(win == los, 0.5, 0.0))
    old, new = out(S[t]), out(row)
    C = C0.copy(); C[others] = C0[others] - old + new
    C[t] = (1.0 - new).sum()
    return C


def scores(S, rule, *, sigma=None, r=None, w=None, kw_cache=False):
    S = np.asarray(S, float)
    N, m = S.shape
    if rule == "mean":
        if w is None:
            return S.mean(axis=1)
        return S @ (np.asarray(w, float) / np.sum(w))
    if rule == "zmean":
        sg = S.std(axis=0, ddof=0) if sigma is None else np.asarray(sigma, float)
        return (S / sg).mean(axis=1)
    if rule == "median":
        return np.median(S, axis=1)
    if rule == "min":
        return S.min(axis=1)
    if rule == "quantile":  # r-th largest, r = 1..m
        return -np.sort(-S, axis=1)[:, r - 1]
    if rule == "gmean":
        return np.exp(np.log(np.maximum(S, 1e-9)).mean(axis=1))
    if rule == "borda":
        return borda_scores(S)
    if rule == "plurality":
        return plurality_scores(S)
    if rule == "copeland":
        return copeland_cached(S) if kw_cache else copeland_scores(S)
    raise ValueError(rule)


def margin(S, t, rule, rivals=None, **kw):
    """Aggregate of t minus the best aggregate among `rivals` (default all other models)."""
    A = scores(S, rule, **kw)
    if rivals is None:
        rivals = np.delete(np.arange(S.shape[0]), t)
    return A[t] - A[rivals].max()


def is_first(S, t, rule, rivals=None, eps_agg=1e-6, **kw):
    mg = margin(S, t, rule, rivals, **kw)
    if rule in RANK_RULES:
        return mg > 0
    return mg >= eps_agg - 1e-9


def leader(S, rule, exclude=None, **kw):
    A = scores(S, rule, **kw).astype(float)
    if exclude is not None:
        A[exclude] = -np.inf
    return int(np.argmax(A))
