"""Starter planner for the *targeted-investment* leaderboard task (python_rpc_v1:handle).

PROBLEM
-------
A leaderboard is a score matrix X of shape [N, T] (N models = rows, T tasks = columns, scores on a
0..100 scale, higher is better). A *rule* maps X to one aggregate value per model (higher is better).
One row, the *target*, is a model whose developer wants it to be strictly first. The developer may
raise the target's score on chosen tasks ("targeted investment"); nothing else changes.

INVESTMENT MODEL (identical in every episode; fixed in advance)
  * A plan is a set of non-negative gains g[t] >= 0 (one per task, independent, no spillover); the
    target's new row is x + g. All other rows are unchanged.
  * g[t] <= caps[t] - x[target][t]  (caps arrive with the data; see load_begin).
  * cost_model "l1_points": cost = sum_t g[t]            (caps[t] = 100 for every task)
    cost_model "l0_tasks" : cost = #{t : g[t] > 0}        (caps[t] = best score of any model on task t,
                                                          plus 1e-6 so that a tie on the task can be broken;
                                                          caps[t] = x[target][t] if the target already
                                                          leads task t strictly)
  * SUCCESS: after applying the plan the target's aggregate is strictly larger than every other
    model's aggregate under the rule (margin > 1e-9; ties count against the target). The evaluator
    recomputes everything from scratch; nothing the candidate reports about itself is trusted.

RULES (aggregates recomputed on the *modified* matrix; N includes the target)
  mean            arithmetic mean over tasks
  median          median over tasks (mean of the two middle values when T is even)
  trimmed_mean_20 drop the k = T // 5 lowest and k highest task scores of the model, average the rest
  zscore_mean     per task standardize over all N models (population std; std < 1e-12 -> z = 0),
                  then average a model's z-scores over tasks
  borda           -(mean over tasks of the model's rank on the task); rank = 1 + #models strictly higher
                  + 0.5 * #other models tied with it
  plurality       number of tasks on which the model is strictly first (strictly above all others)
  copeland        for each other model j: +1 if the model beats j on strictly more tasks than j beats it,
                  +0.5 on equal counts, 0 otherwise; sum over j
  maximin         minimum over tasks

SCORING OF A SOLVE (evaluator-side, for orientation)
  Each episode is one instance. An 'infeasible' claim is correct iff the evaluator's reference solver
  finds no successful plan. A plan is credited by min(2, reference_cost / plan_cost) when it verifies
  (costs below 0.01 point are treated as 0.01); an empty plan is correct iff the target is already
  first. Controls reuse the same operations on matched inputs: rows and tasks permuted (rule values
  must be permutation invariant), or every task column shuffled across models (a null leaderboard).

PROTOCOL (all requests/responses are finite JSON objects; unknown extra keys are rejected)
  Per episode the evaluator sends, in order, exactly:
    {"op": "reset", "seed": int >= 0}
        -> {"ok": true}.  Wipes ALL state; seeds only your own randomness (any seed is valid).
    {"op": "load_begin", "rule": str, "cost_model": str, "target_row": int, "tie_policy": str,
     "score_scale": float, "shape": [N, T], "dtype": "float64", "byte_order": "little",
     "layout": "row_major", "encoding": "base64", "chunk_count": int,
     "caps": {"dtype": "float64", "byte_order": "little", "encoding": "base64", "shape": [T], "data": str}}
        -> {"ok": true}.  Announces the instance. caps[t] is the largest *final* score the target may
           have on task t. Rows and tasks are opaque indices (no names, no source labels).
    {"op": "load_chunk", "chunk_index": int, "chunk_count": int, "row_start": int, "row_end": int,
     "data": str}   (1..chunk_count chunks, in order; each carries rows row_start:row_end of X as
                     little-endian float64, row-major, base64; at most 2 chunks, <= 1 MiB base64 each)
        -> {"ok": true}
    {"op": "load_commit"}
        -> {"ok": true}.  All chunks have been delivered; the matrix is complete.
    {"op": "solve"}
        -> {"status": "plan", "gains": [{"task": int, "gain": float}, ...]}   gains only for tasks you
              raise (0 <= task < T, each task at most once, 0 <= gain <= caps[task] - x[target][task]
              + 1e-9, finite); an empty list means "do nothing"
         | {"status": "infeasible"}   (no plan can make the target strictly first)
           No other keys are allowed in either response. A malformed or out-of-bounds response, an
           exception, a crash or a timeout earns 0 for the episode (the harness restarts you at the
           next reset).
  There are at most 6 RPCs per episode (reset, load_begin, <=2 load_chunk, load_commit, solve).
  Wall-clock limit: 12 s per episode in total (reset + load + solve); a single RPC may take at most 10 s.
  The instance is small (N <= 200, T <= ~60); the evaluator never sends names, labels, reference
  costs, baseline plans, metrics or file paths. Candidates run without network or shared files.

THIS STARTER (deliberately simple; the evaluator's naive baselines are typically at least as good)
  * infeasible iff raising every task to its cap does not make the target strictly first;
  * l1_points: one uniform gain on every task (bounded by the caps), found by bisection;
  * l0_tasks: lift tasks to their caps in order of decreasing headroom until the target wins.
"""
import base64

import numpy as np

_MARGIN = 1e-7
_STATE = {}


def _b64_array(spec_or_text, shape=None):
    raw = base64.b64decode(spec_or_text, validate=True)
    arr = np.frombuffer(raw, dtype="<f8")
    return arr.reshape(shape) if shape is not None else arr


def _scores(X, rule):
    N, T = X.shape
    if rule == "mean":
        return X.mean(axis=1)
    if rule == "median":
        return np.median(X, axis=1)
    if rule == "trimmed_mean_20":
        k = T // 5
        return np.sort(X, axis=1)[:, k:T - k].mean(axis=1)
    if rule == "zscore_mean":
        sd = X.std(axis=0)
        z = np.where(sd > 1e-12, (X - X.mean(axis=0)) / np.where(sd > 1e-12, sd, 1.0), 0.0)
        return z.mean(axis=1)
    if rule == "borda":
        total = np.zeros(N)
        for t in range(T):
            c = X[:, t]
            higher = (c[None, :] > c[:, None]).sum(axis=1)
            tied = (c[None, :] == c[:, None]).sum(axis=1) - 1
            total += 1.0 + higher + 0.5 * tied
        return -total / T
    if rule == "plurality":
        wins = np.zeros(N)
        for t in range(T):
            c = X[:, t]
            if (c == c.max()).sum() == 1:
                wins[int(np.argmax(c))] += 1.0
        return wins
    if rule == "copeland":
        better = (X[:, None, :] > X[None, :, :]).sum(axis=2)
        return (better > better.T).sum(axis=1) + 0.5 * ((better == better.T).sum(axis=1) - 1)
    if rule == "maximin":
        return X.min(axis=1)
    raise ValueError("unknown rule")


def _margin(gains):
    X = _STATE["X"].copy()
    i = _STATE["target"]
    X[i] = X[i] + gains
    v = _scores(X, _STATE["rule"])
    return v[i] - np.delete(v, i).max()


def _plan(gains):
    return {"status": "plan", "gains": [{"task": int(t), "gain": float(g)} for t, g in enumerate(gains) if g > 0]}


def _solve():
    s = _STATE
    x = s["X"][s["target"]]
    room = np.maximum(s["caps"] - x, 0.0)
    if _margin(np.zeros_like(room)) >= _MARGIN:
        return {"status": "plan", "gains": []}
    if _margin(room) < _MARGIN:
        return {"status": "infeasible"}
    if s["cost_model"] == "l1_points":
        lo, hi = 0.0, float(room.max())
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if _margin(np.minimum(mid, room)) >= _MARGIN:
                hi = mid
            else:
                lo = mid
        return _plan(np.minimum(hi, room))
    gains = np.zeros_like(room)
    for t in np.argsort(-room, kind="stable"):
        gains[t] = room[t]
        if _margin(gains) >= _MARGIN:
            break
    return _plan(gains)


def handle(request):
    op = request.get("op")
    if op == "reset":
        _STATE.clear()
        _STATE["rng"] = np.random.default_rng(int(request["seed"]))
        return {"ok": True}
    if op == "load_begin":
        N, T = request["shape"]
        _STATE.update(rule=request["rule"], cost_model=request["cost_model"], target=int(request["target_row"]),
                      shape=(int(N), int(T)), chunk_count=int(request["chunk_count"]), chunks=[], committed=False,
                      caps=_b64_array(request["caps"]["data"], (int(T),)).copy())
        return {"ok": True}
    if op == "load_chunk":
        _STATE["chunks"].append(_b64_array(request["data"]).copy())
        return {"ok": True}
    if op == "load_commit":
        N, T = _STATE["shape"]
        _STATE["X"] = np.concatenate(_STATE["chunks"]).reshape(N, T)
        _STATE["committed"] = True
        return {"ok": True}
    if op == "solve":
        return _solve()
    raise ValueError("unknown op")
