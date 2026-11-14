#!/usr/bin/env python3
"""Sealed final evaluator (Open LLM Leaderboard snapshots).

Self-contained evaluator for the 'strategic targeted investment' task. Candidates implement
handle(request) -> response (python_rpc_v1). The evaluator owns the rule engine, the plan
verifier, the reference solver, the naive baselines and the controls; candidate-reported
state is never trusted. All scores come from evaluator-side recomputation of the leaderboard.

Declared before scoring (fixed weights, no renormalisation):
  episode efficiency = min(2, ref_cost / verified_plan_cost) for a verified successful plan (costs under
    0.01 point count as 0.01; L0 costs are task counts); 1 for a correct 'infeasible' claim or a correct
    empty plan on an already-first target; 0 for anything else, including every failed/timed-out/malformed
    episode (worst-case contribution retained, never retried or dropped).
  main_efficiency    = mean over boards of mean over main cases of mean over seeds of episode efficiency
  control_efficiency = mean over boards of mean(permuted-input efficiency, shuffled-null efficiency)
  plan_validity_rate = fraction of all declared episodes with a well-formed in-bounds response
  combined_score     = 0.8 * main_efficiency + 0.2 * control_efficiency
  baseline_main_efficiency (final only) = same hierarchy over main cases, per case the better of the naive
    uniform-gain and greedy marginal-cost baselines, scored against the same reference
  search correct = integrity only (exact declared reset transcript, finite trusted metrics, completed
    reference/baseline pre-pass, non-vacuous controls, snapshot checksums and content-hash checks, no
    wire/RPC violation); final correct = integrity AND main_efficiency > baseline_main_efficiency AND the
    optional trailing replay (first seed, first case) reproduces the first episode's verified cost.
Expected control behaviour is listed in CONTROL_EXPECTATIONS.
"""
import argparse
import base64
import collections
import concurrent.futures
import hashlib
import importlib.util
import json
import math
import os
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import zlib

import numpy as np

PLANE = "final"
SEEDS = [9001, 9002]
METRIC_NAMES = ["combined_score", "main_efficiency", "control_efficiency", "plan_validity_rate", "baseline_main_efficiency"]
ROOT_RELATIVE = "resources/final"
WIRE_LIMIT = 64 * 1024 * 1024
PROXY_PATH = "/broker-code/candidate_proxy.py"
CANDIDATE_THREADS = 4
WALL_SECONDS = 3600
RESET_TIMEOUT = 8.0
EPISODE_OVERHEAD = 3.0
EPISODE_SECONDS = 12.0
RPC_CAP_SECONDS = 10.0
CONTRACT_MAX_RPC_CALLS = 1158
PRODUCTION_PLAN = dict(wall_seconds=3600, finish_reserve=30.0, prepass_seconds=500.0, restarts=4,
                       startup_seconds=60.0)
SMOKE_PLAN = dict(wall_seconds=110.0, finish_reserve=8.0, prepass_seconds=30.0, restarts=1,
                  startup_seconds=5.0)



# ---------------------------------------------------------------------------
# Trusted rule engine, verifier and reference solvers (evaluator-owned).
# ---------------------------------------------------------------------------
RULES = ("mean", "median", "trimmed_mean_20", "zscore_mean", "borda", "plurality", "copeland", "maximin")
COST_MODELS = ("l1_points", "l0_tasks")
SCORE_SCALE = 100.0
TOL = 1e-9          # strict-first margin used by the verifier
SAFE = 1e-7         # margin demanded by solvers so the verifier never flips on rounding
STRICT_EPS = 1e-6   # smallest lead increment used to break ties
GAIN_EPS = 1e-9     # bound tolerance on candidate gains


def rule_scores(X, rule):
    """Independent, naive full recomputation of the aggregate (higher is better)."""
    X = np.asarray(X, dtype=np.float64)
    N, T = X.shape
    if rule == "mean":
        return X.mean(axis=1)
    if rule == "median":
        return np.median(X, axis=1)
    if rule == "trimmed_mean_20":
        k = T // 5
        return np.sort(X, axis=1)[:, k:T - k].mean(axis=1)
    if rule == "zscore_mean":
        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        ok = sd > 1e-12
        z = np.where(ok, (X - mu) / np.where(ok, sd, 1.0), 0.0)
        return z.mean(axis=1)
    if rule == "borda":
        total = np.zeros(N)
        for t in range(T):
            col = X[:, t]
            gt = (col[None, :] > col[:, None]).sum(axis=1)
            eq = (col[None, :] == col[:, None]).sum(axis=1)
            total += 1.0 + gt + 0.5 * (eq - 1)
        return -total / T
    if rule == "plurality":
        wins = np.zeros(N)
        for t in range(T):
            col = X[:, t]
            mx = col.max()
            if int((col == mx).sum()) == 1:
                wins[int(np.argmax(col))] += 1.0
        return wins
    if rule == "copeland":
        C = (X[:, None, :] > X[None, :, :]).sum(axis=2)
        beats = (C > C.T).sum(axis=1)
        ties = (C == C.T).sum(axis=1) - 1
        return beats + 0.5 * ties
    if rule == "maximin":
        return X.min(axis=1)
    raise ValueError("unknown rule")


def strictly_first(X, target, rule):
    v = rule_scores(X, rule)
    others = np.delete(v, target)
    return bool(v[target] > others.max() + TOL)


class Instance:
    """One leaderboard instance for one target; fast margin machinery for solvers."""

    def __init__(self, X, target, rule, cost_model, scale=SCORE_SCALE):
        self.X = np.ascontiguousarray(X, dtype=np.float64)
        self.N, self.T = self.X.shape
        self.i = int(target)
        self.rule = rule
        self.cost_model = cost_model
        self.scale = float(scale)
        self.x = self.X[self.i].copy()
        self.O = np.delete(self.X, self.i, axis=0)
        fmax = self.X.max(axis=0)
        uniq = (self.X == fmax[None, :]).sum(axis=0) == 1
        lead = uniq & (self.x == fmax)
        if cost_model == "l1_points":
            self.cap = np.maximum(np.full(self.T, self.scale), self.x)
        else:
            self.cap = np.where(lead, self.x, fmax + STRICT_EPS)
        self.room = np.maximum(self.cap - self.x, 0.0)
        self._prep()

    # -- per-rule precomputation -------------------------------------------------
    def _prep(self):
        O, T, N = self.O, self.T, self.N
        r = self.rule
        self.additive = r in ("mean", "zscore_mean", "borda", "plurality", "copeland")
        if r in ("mean", "median", "trimmed_mean_20", "maximin"):
            self.omax = float(rule_scores(O, r).max())
        if r == "borda":
            self.rb = np.zeros_like(O)
            for t in range(T):
                col = O[:, t]
                gt = (col[None, :] > col[:, None]).sum(axis=1)
                eq = (col[None, :] == col[:, None]).sum(axis=1)
                self.rb[:, t] = 1.0 + gt + 0.5 * (eq - 1)
        elif r == "plurality":
            self.M1 = O.max(axis=0)
            cnt = (O == self.M1[None, :]).sum(axis=0)
            self.leader = np.where(cnt == 1, O.argmax(axis=0), -1)
        elif r == "copeland":
            C = (O[:, None, :] > O[None, :, :]).sum(axis=2)
            self.cp = (C > C.T).sum(axis=1) + 0.5 * ((C == C.T).sum(axis=1) - 1)
        elif r == "zscore_mean":
            self.S1 = O.sum(axis=0)
            self.S2 = (O ** 2).sum(axis=0)

    # -- additive contributions of task t at values v (L,) -------------------------
    def contrib(self, t, v):
        v = np.asarray(v, dtype=np.float64)
        O, N, T = self.O, self.N, self.T
        r = self.rule
        L = v.shape[0]
        col = O[:, t]
        if r == "mean":
            return v / T, None
        if r == "borda":
            gt = (col[None, :] > v[:, None])
            lt = (col[None, :] < v[:, None])
            eqm = (col[None, :] == v[:, None])
            tg = -(1.0 + gt.sum(axis=1) + 0.5 * eqm.sum(axis=1)) / T
            og = -(self.rb[:, t][None, :] + lt + 0.5 * eqm) / T
            return tg, og
        if r == "plurality":
            tg = (v > self.M1[t]).astype(np.float64)
            og = np.zeros((L, N - 1))
            if self.leader[t] >= 0:
                og[:, self.leader[t]] = (v < self.M1[t])
            return tg, og
        if r == "copeland":
            return np.zeros(L), np.sign(v[:, None] - col[None, :])
        if r == "zscore_mean":
            mu = (self.S1[t] + v) / N
            var = (self.S2[t] + v * v) / N - mu * mu
            sd = np.sqrt(np.maximum(var, 0.0))
            inv = np.where(sd > 1e-12, 1.0 / np.where(sd > 1e-12, sd, 1.0), 0.0)
            tg = (v - mu) * inv / T
            og = (col[None, :] - mu[:, None]) * inv[:, None] / T
            return tg, og
        raise ValueError("not additive")

    def finalize(self, tsum, osum):
        r = self.rule
        if r == "mean":
            return tsum - self.omax
        if r == "copeland":
            d = osum
            ts = (d > 0).sum(axis=-1) + 0.5 * (d == 0).sum(axis=-1)
            os_ = self.cp + (d < 0) + 0.5 * (d == 0)
            return ts - os_.max(axis=-1)
        return tsum - osum.max(axis=-1)

    def direct_value(self, Y):
        r = self.rule
        if r == "median":
            return np.median(Y, axis=1)
        if r == "trimmed_mean_20":
            k = self.T // 5
            return np.sort(Y, axis=1)[:, k:self.T - k].mean(axis=1)
        if r == "maximin":
            return Y.min(axis=1)
        raise ValueError("not direct")

    def margin_rows(self, Y):
        """Margin (target aggregate minus best other aggregate) for candidate target rows Y (B,T)."""
        Y = np.atleast_2d(np.asarray(Y, dtype=np.float64))
        if not self.additive:
            return self.direct_value(Y) - self.omax
        B = Y.shape[0]
        tsum = np.zeros(B)
        osum = None
        for t in range(self.T):
            tg, og = self.contrib(t, Y[:, t])
            tsum += tg
            if og is not None:
                osum = og.copy() if osum is None else osum + og
        return self.finalize(tsum, osum)

    # -- plans ----------------------------------------------------------------------
    def row_after(self, gains):
        return self.x + gains

    def plan_cost(self, gains):
        g = np.asarray(gains)
        return float(g.sum()) if self.cost_model == "l1_points" else float((g > 0).sum())


def verify_plan(inst, gains):
    """Trusted verification: gains already clipped to bounds. Returns bool success (naive recompute)."""
    Xm = inst.X.copy()
    Xm[inst.i] = inst.x + gains
    return strictly_first(Xm, inst.i, inst.rule)


# ---------------------------------------------------------------------------
# Reference solvers
# ---------------------------------------------------------------------------
class Deadline:
    def __init__(self, clock, until):
        self.clock, self.until = clock, until

    def check(self):
        if self.until is not None and self.clock() > self.until:
            raise TimeoutError("solver deadline exceeded")


def _exact_threshold_plan(inst, need_sum=None, level=None, odd_median=False):
    """Closed forms (None = infeasible)."""
    T, x, room = inst.T, inst.x, inst.room
    r = inst.rule
    g = np.zeros(T)
    if r == "mean":
        gap = inst.omax - x.mean()
        need = max(T * (gap + 2 * SAFE), T * SAFE)
        if need > room.sum() + 1e-12:
            return None
        if inst.cost_model == "l1_points":
            g = room * (need / room.sum()) if need > 0 else g
        else:
            order = np.argsort(-room, kind="stable")
            left = need
            for t in order:
                if left <= 1e-15:
                    break
                take = min(room[t], left)
                g[t] = take
                left -= take
        return g
    if r == "maximin":
        L = inst.omax + 2 * SAFE
        deficit = np.maximum(L - x, 0.0)
        if np.any(deficit > room + 1e-12):
            return None
        return np.minimum(deficit, room)
    if r == "median":
        L = inst.omax + 2 * SAFE
        need_cnt = (T + 1) // 2 - int((x >= L).sum())
        if need_cnt <= 0:
            return g
        deficit = np.maximum(L - x, 0.0)
        ok = (x < L) & (room >= deficit - 1e-12)
        if int(ok.sum()) < need_cnt:
            return None
        idx = np.where(ok)[0]
        if inst.cost_model == "l1_points":
            idx = idx[np.argsort(deficit[idx], kind="stable")]
        else:
            idx = idx[np.argsort(-room[idx], kind="stable")]
        for t in idx[:need_cnt]:
            g[t] = min(deficit[t], room[t])
        return g
    return None


def _levels(inst, t):
    """Candidate target values for task t (index 0 = unchanged)."""
    x_t, cap = inst.x[t], inst.cap[t]
    r = inst.rule
    if cap <= x_t:
        return np.array([x_t])
    if r in ("borda", "plurality", "copeland"):
        c_all = inst.O[:, t]
        v = np.concatenate([c_all[c_all > x_t], c_all[c_all >= x_t] + STRICT_EPS])
        v = v[v <= cap + 1e-12]
    elif r == "zscore_mean":
        q = np.unique(np.concatenate([2.0 ** -np.arange(0, 11), np.arange(1, 17) / 16.0]))
        v = x_t + inst.room[t] * q
    else:
        c = inst.x[inst.x > x_t]
        v = np.concatenate([c, [cap]])
        v = v[v <= cap + 1e-12]
    v = np.unique(np.minimum(v, cap))
    v = v[v > x_t]
    return np.concatenate([[x_t], v])


class Tables:
    """Precomputed per-task contributions at every candidate level (additive rules)."""

    def __init__(self, inst):
        self.inst = inst
        self.vals = [_levels(inst, t) for t in range(inst.T)]
        self.tg, self.og = [], []
        for t in range(inst.T):
            tg, og = inst.contrib(t, self.vals[t])
            self.tg.append(tg)
            self.og.append(og)
        self.cost = [v - inst.x[t] for t, v in enumerate(self.vals)]


def _final_margin(inst, tsum, osum):
    return inst.finalize(tsum, osum)


def _l1_greedy_additive(inst, tab, rng, noise, dl):
    T = inst.T
    lev = np.zeros(T, dtype=int)
    tsum = float(sum(tab.tg[t][0] for t in range(T)))
    osum = None
    for t in range(T):
        if tab.og[t] is not None:
            osum = tab.og[t][0].copy() if osum is None else osum + tab.og[t][0]
    cost = 0.0
    best = None
    for _ in range(4 * T + 8):
        dl.check()
        m_cur = float(inst.finalize(np.array(tsum), osum))
        if m_cur >= SAFE:
            best = (cost, lev.copy())
            break
        bratio, bmove = -np.inf, None
        fin = None
        for t in range(T):
            L = len(tab.vals[t])
            l0 = lev[t]
            if l0 >= L - 1:
                continue
            ls = np.arange(l0 + 1, L)
            ts = tsum - tab.tg[t][l0] + tab.tg[t][ls]
            os_ = None if osum is None else osum[None, :] - tab.og[t][l0][None, :] + tab.og[t][ls]
            m = inst.finalize(ts, os_)
            dc = tab.cost[t][ls] - tab.cost[t][l0]
            done = m >= SAFE
            if done.any():
                k = int(np.argmax(done))  # cheapest finishing level for this task
                cand = (cost + dc[k], t, int(ls[k]))
                if fin is None or cand[0] < fin[0]:
                    fin = cand
            ratio = (m - m_cur) / dc
            if noise:
                ratio = ratio * (1.0 + noise * rng.random(ratio.shape[0]) )
            j = int(np.argmax(ratio))
            if ratio[j] > bratio:
                bratio, bmove = ratio[j], (t, int(ls[j]))
        if fin is not None and (best is None or fin[0] < best[0]):
            lv = lev.copy()
            lv[fin[1]] = fin[2]
            best = (fin[0], lv)
        if bmove is None:
            break
        t, l1 = bmove
        if bratio <= 0:
            # plateau: take the cheapest strictly-improving-or-neutral step on the cheapest task
            cands = [(tab.cost[t2][lev[t2] + 1] - tab.cost[t2][lev[t2]], t2) for t2 in range(T) if lev[t2] < len(tab.vals[t2]) - 1]
            if not cands:
                break
            t = min(cands)[1]
            l1 = lev[t] + 1
        l0 = lev[t]
        tsum += tab.tg[t][l1] - tab.tg[t][l0]
        if osum is not None:
            osum = osum + tab.og[t][l1] - tab.og[t][l0]
        cost += tab.cost[t][l1] - tab.cost[t][l0]
        lev[t] = l1
        if best is not None and cost >= best[0]:
            break
    return best


def _rank_family(inst, tab, dl):
    """Start points 'exceed all but the k strongest competitors on every task' (rank-based rules)."""
    T = inst.T
    S = np.sort(inst.O, axis=0)[::-1]
    best = None
    for k in range(S.shape[0]):
        dl.check()
        lev = np.zeros(T, dtype=int)
        for t in range(T):
            want = S[k, t] + STRICT_EPS
            if want > inst.x[t]:
                lev[t] = min(int(np.searchsorted(tab.vals[t], want - 1e-12, side="left")), len(tab.vals[t]) - 1)
        tsum = float(sum(tab.tg[t][lev[t]] for t in range(T)))
        osum = None
        for t in range(T):
            if tab.og[t] is not None:
                osum = tab.og[t][lev[t]].copy() if osum is None else osum + tab.og[t][lev[t]]
        if float(inst.finalize(np.array(tsum), osum)) >= SAFE:
            c = float(sum(tab.cost[t][lev[t]] for t in range(T)))
            if best is None or c < best[0]:
                best = (c, lev)
    return best


def _prune_additive(inst, tab, lev, dl):
    T = inst.T
    lev = lev.copy()
    tsum = float(sum(tab.tg[t][lev[t]] for t in range(T)))
    osum = None
    for t in range(T):
        if tab.og[t] is not None:
            osum = tab.og[t][lev[t]].copy() if osum is None else osum + tab.og[t][lev[t]]
    changed = True
    while changed:
        changed = False
        order = sorted(range(T), key=lambda t: -tab.cost[t][lev[t]])
        for t in order:
            dl.check()
            if lev[t] == 0:
                continue
            ls = np.arange(0, lev[t])
            ts = tsum - tab.tg[t][lev[t]] + tab.tg[t][ls]
            os_ = None if osum is None else osum[None, :] - tab.og[t][lev[t]][None, :] + tab.og[t][ls]
            m = inst.finalize(ts, os_)
            ok = np.where(m >= SAFE)[0]
            if ok.size:
                k = int(ok[0])
                tsum = tsum - tab.tg[t][lev[t]] + tab.tg[t][k]
                if osum is not None:
                    osum = osum - tab.og[t][lev[t]] + tab.og[t][k]
                lev[t] = k
                changed = True
    return lev


def _polish_continuous(inst, gains, dl):
    """Coordinate-wise grid refinement lowering each gain while the margin stays >= SAFE."""
    g = gains.copy()
    frac = np.linspace(0.0, 1.0, 65)[:-1]
    for _ in range(2):
        for t in np.argsort(-g, kind="stable"):
            dl.check()
            if g[t] <= 0:
                continue
            lo, hi = 0.0, g[t]
            for _round in range(2):
                grid = lo + (hi - lo) * frac
                Y = np.tile(inst.x + g, (grid.size, 1))
                Y[:, t] = inst.x[t] + grid
                ok = np.where(inst.margin_rows(Y) >= SAFE)[0]
                if ok.size == 0:
                    break
                k = int(ok[0])
                new_hi = grid[k]
                lo = grid[k - 1] if k > 0 else lo
                hi = new_hi
            g[t] = hi
    return g


def _l1_direct(inst, rng, restarts, dl):
    """Greedy over breakpoints for median/trimmed (others fixed), direct row evaluation."""
    T = inst.T
    vals = [_levels(inst, t) for t in range(T)]
    best = None
    for rep in range(restarts + 1):
        noise = 0.0 if rep == 0 else 0.5
        y = inst.x.copy()
        cost = 0.0
        for _ in range(4 * T + 8):
            dl.check()
            m_cur = float(inst.margin_rows(y)[0])
            if m_cur >= SAFE:
                break
            rows, meta = [], []
            for t in range(T):
                v = vals[t][vals[t] > y[t]]
                if v.size == 0:
                    continue
                Y = np.tile(y, (v.size, 1))
                Y[:, t] = v
                rows.append(Y)
                meta.extend((t, float(a)) for a in v)
            if not rows:
                break
            Y = np.vstack(rows)
            m = inst.margin_rows(Y)
            dc = np.array([a - y[t] for t, a in meta])
            ratio = (m - m_cur) / dc
            done = m >= SAFE
            if done.any():
                k = np.where(done)[0][np.argmin(dc[done])]
                cand_cost = cost + dc[k]
                if best is None or cand_cost < best[0] - 1e-12:
                    yy = y.copy()
                    yy[meta[k][0]] = meta[k][1]
                    best = (cand_cost, yy - inst.x)
            if noise:
                ratio = ratio * (1.0 + noise * rng.random(ratio.shape[0]))
            j = int(np.argmax(ratio))
            if ratio[j] <= 0:
                j = int(np.argmin(dc))
            t, v = meta[j]
            cost += v - y[t]
            y[t] = v
            if best is not None and cost >= best[0]:
                break
        else:
            pass
        if inst.margin_rows(y)[0] >= SAFE:
            if best is None or cost < best[0] - 1e-12:
                best = (cost, y - inst.x)
    if best is None:
        return None
    g = _polish_continuous(inst, best[1], dl)
    return g


def _set_margin_fn(inst):
    """Return f(M) -> margins for boolean (B,T) masks of tasks lifted to caps (L0)."""
    T = inst.T
    if inst.additive:
        tg0, og0 = inst.contrib_all(inst.x)
        tg1, og1 = inst.contrib_all(inst.cap)
        base_t = float(tg0.sum())
        base_o = None if og0 is None else og0.sum(axis=0)
        dT = tg1 - tg0
        dO = None if og0 is None else (og1 - og0)

        def f(M):
            M = np.asarray(M, dtype=np.float64)
            ts = base_t + M @ dT
            os_ = None if dO is None else base_o[None, :] + M @ dO
            return inst.finalize(ts, os_)
        return f

    def f(M):
        M = np.asarray(M, dtype=bool)
        Y = np.where(M, inst.cap[None, :], inst.x[None, :])
        return inst.margin_rows(Y)
    return f


def _contrib_all(self, y):
    tg = np.zeros(self.T)
    og = None
    rows = []
    for t in range(self.T):
        a, b = self.contrib(t, np.array([y[t]]))
        tg[t] = a[0]
        if b is not None:
            rows.append(b[0])
    return tg, (np.array(rows) if rows else None)


Instance.contrib_all = _contrib_all


def _l0_search(inst, rng, restarts, dl):
    T = inst.T
    f = _set_margin_fn(inst)
    movable = inst.room > 0
    idx_m = np.where(movable)[0]
    full = movable.copy()
    if f(full[None, :])[0] < SAFE:
        return None
    if T <= 12:
        sub = np.array([[(s >> t) & 1 for t in range(T)] for s in range(1 << T)], dtype=bool)
        sub &= movable[None, :]
        pc = sub.sum(axis=1)
        m = f(sub)
        ok = m >= SAFE
        kmin = pc[ok].min()
        cand = np.where(ok & (pc == kmin))[0]
        s = cand[np.argmax(m[cand])]
        return sub[s]

    def greedy(noise):
        S = np.zeros(T, dtype=bool)
        while True:
            dl.check()
            if f(S[None, :])[0] >= SAFE:
                return S
            cand = np.where(movable & ~S)[0]
            if cand.size == 0:
                return None
            M = np.tile(S, (cand.size, 1))
            M[np.arange(cand.size), cand] = True
            m = f(M)
            if noise:
                m = m + noise * rng.random(m.shape[0]) * (np.abs(m).max() + 1e-12)
            S[cand[int(np.argmax(m))]] = True

    def prune(S):
        S = S.copy()
        for t in np.where(S)[0]:
            S[t] = False
            if f(S[None, :])[0] < SAFE:
                S[t] = True
        return S

    def descend(S):
        """Try to find a feasible set of size |S|-1 by hill-climbing swaps."""
        k = int(S.sum())
        if k <= 1:
            return None
        cur = S.copy()
        ins = np.where(cur)[0]
        # drop the member whose removal hurts least
        M = np.tile(cur, (ins.size, 1))
        M[np.arange(ins.size), ins] = False
        cur = M[int(np.argmax(f(M)))]
        for _ in range(25):
            dl.check()
            mc = f(cur[None, :])[0]
            if mc >= SAFE:
                return cur
            ins = np.where(cur)[0]
            outs = np.where(movable & ~cur)[0]
            if outs.size == 0:
                return None
            A = np.repeat(ins, outs.size)
            B = np.tile(outs, ins.size)
            M = np.tile(cur, (A.size, 1))
            M[np.arange(A.size), A] = False
            M[np.arange(A.size), B] = True
            m = f(M)
            j = int(np.argmax(m))
            if m[j] <= mc + 1e-15:
                return None
            cur = M[j]
        return None

    best = None
    for rep in range(restarts + 1):
        S = greedy(0.0 if rep == 0 else 0.3)
        if S is None:
            continue
        S = prune(S)
        while True:
            S2 = descend(S)
            if S2 is None:
                break
            S = prune(S2)
        if best is None or S.sum() < best.sum():
            best = S
    return best


def reference_solve(inst, *, seed, restarts, clock, until):
    """Returns dict(status in {'first','infeasible','plan'}, gains, cost, exact)."""
    dl = Deadline(clock, until)
    T = inst.T
    if strictly_first(inst.X, inst.i, inst.rule):
        return {"status": "first", "gains": np.zeros(T), "cost": 0.0, "exact": True}
    rng = np.random.default_rng(seed)
    gains, exact = None, False
    if inst.rule in ("mean", "maximin") or (inst.rule == "median" and T % 2 == 1):
        gains = _exact_threshold_plan(inst)
        exact = True
        if gains is not None and not verify_plan(inst, np.minimum(gains, inst.room)):
            gains = None
    else:
        if inst.cost_model == "l0_tasks":
            S = _l0_search(inst, rng, restarts, dl)
            if S is not None:
                gains = np.where(S, inst.room, 0.0)
        elif inst.additive:
            tab = Tables(inst)
            best = None
            if inst.rule in ("borda", "plurality", "copeland"):
                fam = _rank_family(inst, tab, dl)
                if fam is not None:
                    lev = _prune_additive(inst, tab, fam[1], dl)
                    best = (float(sum(tab.cost[t][lev[t]] for t in range(T))), lev)
            for rep in range(restarts + 1):
                res = _l1_greedy_additive(inst, tab, rng, 0.0 if rep == 0 else 0.4, dl)
                if res is None:
                    continue
                lev = _prune_additive(inst, tab, res[1], dl)
                c = float(sum(tab.cost[t][lev[t]] for t in range(T)))
                if best is None or c < best[0] - 1e-12:
                    best = (c, lev)
            if best is not None:
                gains = np.array([tab.vals[t][best[1][t]] - inst.x[t] for t in range(T)])
                if inst.rule == "zscore_mean":
                    gains = _polish_continuous(inst, gains, dl)
        else:
            gains = _l1_direct(inst, rng, restarts, dl)
        if inst.cost_model == "l1_points":
            # the naive baselines are also admissible reference candidates (after polishing)
            for fn in (baseline_uniform, baseline_greedy):
                b = fn(inst, clock, until)
                if b["status"] == "plan":
                    cand = _polish_continuous(inst, np.minimum(b["gains"], inst.room), dl)
                    if verify_plan(inst, cand) and (gains is None or inst.plan_cost(cand) < inst.plan_cost(np.minimum(gains, inst.room)) - 1e-12):
                        gains = cand
        # safety net: the full-lift plan
        if gains is None or not verify_plan(inst, np.minimum(gains, inst.room)):
            gains = None
            full = inst.room.copy()
            if verify_plan(inst, full):
                gains = full
    if gains is None:
        return {"status": "infeasible", "gains": np.zeros(T), "cost": float("inf"), "exact": exact}
    gains = np.minimum(np.maximum(gains, 0.0), inst.room)
    if not verify_plan(inst, gains):
        raise RuntimeError("reference plan failed verification")
    return {"status": "plan", "gains": gains, "cost": inst.plan_cost(gains), "exact": exact}


# ---------------------------------------------------------------------------
# Evaluator-owned naive baselines
# ---------------------------------------------------------------------------
def baseline_uniform(inst, clock, until):
    dl = Deadline(clock, until)
    if strictly_first(inst.X, inst.i, inst.rule):
        return {"status": "first", "gains": np.zeros(inst.T)}
    hi = float(inst.room.max())

    def ok(g):
        dl.check()
        gains = np.minimum(g, inst.room)
        return inst.margin_rows(inst.x + gains)[0] >= SAFE, gains
    good, gains = ok(hi)
    if not good:
        return {"status": "infeasible", "gains": np.zeros(inst.T)}
    lo = 0.0
    best = gains
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        good, gg = ok(mid)
        if good:
            hi, best = mid, gg
        else:
            lo = mid
    return {"status": "plan", "gains": best}


def baseline_greedy(inst, clock, until):
    dl = Deadline(clock, until)
    T = inst.T
    if strictly_first(inst.X, inst.i, inst.rule):
        return {"status": "first", "gains": np.zeros(T)}
    if inst.cost_model == "l0_tasks":
        f = _set_margin_fn(inst)
        movable = inst.room > 0
        S = np.zeros(T, dtype=bool)
        while f(S[None, :])[0] < SAFE:
            dl.check()
            cand = np.where(movable & ~S)[0]
            if cand.size == 0:
                return {"status": "infeasible", "gains": np.zeros(T)}
            M = np.tile(S, (cand.size, 1))
            M[np.arange(cand.size), cand] = True
            S[cand[int(np.argmax(f(M)))]] = True
        return {"status": "plan", "gains": np.where(S, inst.room, 0.0)}
    # L1: unit-step greedy on the best marginal margin gain per point
    step = inst.scale / 20.0
    if inst.margin_rows(inst.x + inst.room)[0] < SAFE:
        return {"status": "infeasible", "gains": np.zeros(T)}
    g = np.zeros(T)
    for _ in range(int(inst.room.sum() / step) + T + 5):
        dl.check()
        if inst.margin_rows(inst.x + g)[0] >= SAFE:
            return {"status": "plan", "gains": g}
        cand = np.where(g < inst.room - 1e-12)[0]
        if cand.size == 0:
            break
        d = np.minimum(step, inst.room[cand] - g[cand])
        Y = np.tile(inst.x + g, (cand.size, 1))
        Y[np.arange(cand.size), cand] += d
        m = inst.margin_rows(Y) / d
        k = int(np.argmax(m))
        g[cand[k]] += d[k]
    if inst.margin_rows(inst.x + g)[0] >= SAFE:
        return {"status": "plan", "gains": g}
    return {"status": "infeasible", "gains": np.zeros(T)}


def baseline_copy_leader(inst):
    v = rule_scores(inst.X, inst.rule)
    v[inst.i] = -np.inf
    leader = int(np.argmax(v))
    gains = np.minimum(np.maximum(inst.X[leader] - inst.x, 0.0), inst.room)
    return {"status": "plan", "gains": gains}


# ---------------------------------------------------------------------------
# Harness-facing machinery: failure identity, diagnostics, transport, scheduling.
# ---------------------------------------------------------------------------
class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class ProtocolViolation(RuntimeError):
    """Candidate response violated the documented schema (explicit, fixed category)."""

    def __init__(self, operation):
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("malformed candidate response")


class CandidateError(RuntimeError):
    """Candidate crashed / exited / raised (explicit, fixed category)."""

    def __init__(self, category, operation="unknown"):
        self.category = bounded_failure_name(category, "candidate_exception")
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("candidate failure")


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


def bounded_failure_name(value, fallback):
    import re
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, ProtocolViolation):
            return {"component": "candidate", "category": "malformed_response", "operation": context.operation}
        if isinstance(context, CandidateError):
            return {"component": "candidate", "category": context.category, "operation": context.operation}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout", "operation": bounded_failure_name(operation, "unknown")}


def fail_required_baseline(category, cancel_work, record_failure):
    failure = RequiredBaselineFailure(category)
    try:
        record_failure(failure.category)
    except Exception:
        failure.add_note("baseline diagnostic recording failed")
    try:
        cancel_work()
    except Exception:
        failure.add_note("baseline cleanup failed")
    raise failure from None


def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError("work allowance must be positive")
    return value


def require_joint_workload_budget(*, plane):
    """Joint feasibility of the declared plane budget (productive work counted per episode)."""
    episodes = plane["episode_count"]
    needed = (plane["startup_seconds"] + plane["finish_seconds"] + plane["prepass_seconds"]
              + episodes * (plane["episode_seconds"] + plane["cleanup_seconds"]))
    if needed > plane["wall_seconds"]:
        raise ValueError("productive work exceeds the declared wall budget")
    return needed


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


class BoundedWorkerStderr:
    LIMIT = 4096

    def __init__(self, stream):
        self.stream = stream
        self.fd = stream.fileno()
        os.set_blocking(self.fd, False)
        self.lines = collections.deque()
        self.pending = bytearray()
        self.dropping_line = False
        self.observed_bytes = 0
        self.retained_bytes = 0
        self.truncated = False
        self.capture_error = None
        self.stop = threading.Event()
        self.result = None
        self.reader = threading.Thread(target=self._drain, name="worker-stderr-reader")
        self.reader.start()

    def _accept(self, chunk):
        self.observed_bytes += len(chunk)
        for segment in chunk.splitlines(keepends=True):
            complete = segment.endswith(b"\n")
            if not self.dropping_line:
                if len(self.pending) + len(segment) > self.LIMIT:
                    self.pending.clear()
                    self.dropping_line = True
                    self.truncated = True
                else:
                    self.pending.extend(segment)
            if complete:
                if not self.dropping_line:
                    line = bytes(self.pending).decode("utf-8", errors="replace")
                    size = len(line.encode("utf-8"))
                    if size <= self.LIMIT:
                        while self.retained_bytes + size > self.LIMIT:
                            self.retained_bytes -= len(self.lines.popleft().encode("utf-8"))
                            self.truncated = True
                        self.lines.append(line)
                        self.retained_bytes += size
                    else:
                        self.truncated = True
                self.pending.clear()
                self.dropping_line = False

    def _drain(self):
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.fd, selectors.EVENT_READ)
                while not self.stop.is_set():
                    if not selector.select(timeout=.05):
                        continue
                    try:
                        chunk = os.read(self.fd, 8192)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        return
                    self._accept(chunk)
                self.capture_error = "reader_stopped_before_eof"
                self.truncated = True
        except (OSError, ValueError):
            self.capture_error = "stderr_capture_failed"
            self.truncated = True
        finally:
            if self.pending or self.dropping_line:
                self.truncated = True
            self.pending.clear()
            self.stream.close()

    def close(self):
        if self.result is not None:
            return dict(self.result)
        self.reader.join(timeout=.2)
        if self.reader.is_alive():
            self.stop.set()
            self.reader.join(timeout=.2)
        if self.reader.is_alive():
            raise RuntimeError("stderr reader cleanup unresolved")
        self.result = {
            "stderr": "".join(self.lines),
            "observed_bytes": self.observed_bytes,
            "retained_bytes": self.retained_bytes,
            "truncated": self.truncated,
            "capture_error": self.capture_error,
        }
        return dict(self.result)


def repair_visibility():
    return PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                  or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


RUNNER_SOURCE = r'''
import sys, os, json, importlib.util
program_dir, program_path, repair = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
out = sys.stdout
sys.stdout = sys.stderr
def die(error, category):
    if repair:
        name = type(error).__name__
        if not name.isascii() or not name.isidentifier() or len(name) > 80:
            name = "WorkerException"
        try:
            message = str(error)
        except Exception:
            message = "<exception message unavailable>"
        if len(message) > 2048:
            message = "<exception message omitted: too large>"
        print("worker_exception type=%s\n%s" % (name, message), file=sys.stderr, flush=True)
    else:
        print("worker_failure category=" + category, file=sys.stderr, flush=True)
    os._exit(3)
try:
    sys.path.insert(0, program_dir)
    spec = importlib.util.spec_from_file_location("candidate_program", program_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    handle = module.handle
except BaseException as error:
    die(error, "candidate_import_failure")
for line in sys.stdin.buffer:
    try:
        response = handle(json.loads(line))
        payload = json.dumps(response, allow_nan=False, separators=(",", ":"))
    except BaseException as error:
        die(error, "candidate_handle_failure")
    out.write(payload + "\n")
    out.flush()
'''


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke runs only)."""

    def __init__(self, program_path, clock):
        self.program_path = os.path.abspath(program_path)
        self.clock = clock
        self.proc = None
        self.err = None
        self.stderr_snapshot = ""
        self.tmp = tempfile.mkdtemp(prefix="cand_")
        self.copy_dir = os.path.join(self.tmp, "src")
        shutil.copytree(os.path.dirname(self.program_path), self.copy_dir,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.entry = os.path.join(self.copy_dir, os.path.basename(self.program_path))
        self.buf = b""

    def _limits(self):
        cpu = cpu_limit_seconds(WALL_SECONDS, CANDIDATE_THREADS)

        def apply():
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            limit = 8 * 1024 ** 3
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
            except (ValueError, OSError):
                pass
        return apply

    def start(self):
        self.stop()
        python, env = candidate_subprocess_settings(os.environ)
        env.update(OMP_NUM_THREADS=str(CANDIDATE_THREADS), OPENBLAS_NUM_THREADS=str(CANDIDATE_THREADS),
                   MKL_NUM_THREADS=str(CANDIDATE_THREADS))
        self.proc = subprocess.Popen(
            [python, "-I", "-c", RUNNER_SOURCE, self.copy_dir, self.entry, "1" if repair_visibility() else "0"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.tmp,
            env=env, shell=False, start_new_session=True, preexec_fn=self._limits(), close_fds=True)
        self.err = BoundedWorkerStderr(self.proc.stderr)
        self.buf = b""

    def rpc(self, request, timeout):
        data = bounded_json_line(request)
        if self.proc is None or self.proc.poll() is not None:
            raise CandidateError("candidate_exit", request.get("op", "unknown"))
        deadline = self.clock() + timeout
        try:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise CandidateError("candidate_exit", request.get("op", "unknown")) from None
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buf:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    self.stop()
                    raise TimeoutError("candidate response timeout")
                if not selector.select(timeout=min(remaining, 0.25)):
                    continue
                chunk = os.read(fd, 1 << 20)
                if not chunk:
                    self.stop()
                    raise CandidateError("candidate_exit", request.get("op", "unknown"))
                self.buf += chunk
                if len(self.buf) >= WIRE_LIMIT:
                    self.stop()
                    raise ProtocolViolation(request.get("op", "unknown"))
        line, _, self.buf = self.buf.partition(b"\n")
        if len(line) + 1 >= WIRE_LIMIT:
            raise ProtocolViolation(request.get("op", "unknown"))
        try:
            return json.loads(line, parse_constant=_reject_constant)
        except ValueError:
            raise ProtocolViolation(request.get("op", "unknown")) from None

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except OSError:
                    pass
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except OSError:
                        pass
                    try:
                        proc.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        pass
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
        finally:
            if self.err is not None:
                try:
                    self.stderr_snapshot = self.err.close()["stderr"]
                except RuntimeError:
                    self.stderr_snapshot = ""
                self.err = None

    def cleanup(self):
        self.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)


def _reject_constant(name):
    raise ValueError("non-finite constant")


class BrokeredCandidate:
    """The harness proxy runs in-process (never re-isolated); calls get a wall timeout."""

    def __init__(self, proxy_path, clock):
        spec = importlib.util.spec_from_file_location("candidate_proxy", proxy_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.clock = clock
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.pending = None

    def rpc(self, request, timeout):
        bounded_json_line(request)
        # Always submit: the single worker queues behind any slow earlier call (FIFO), so every
        # declared request, including each reset, reaches the broker exactly once and in order.
        future = self.pool.submit(self.handle, request)
        self.pending = future
        try:
            response = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError("candidate response timeout") from None
        except Exception:
            raise CandidateError("candidate_exception", request.get("op", "unknown")) from None
        try:
            bounded_json_line(response)
        except (ValueError, TypeError, RecursionError):
            raise ProtocolViolation(request.get("op", "unknown")) from None
        return response

    def cleanup(self):
        self.pool.shutdown(wait=False, cancel_futures=True)


class RpcLedger:
    """Counts every broker-visible call; enforces the contract budget and the reset transcript."""

    def __init__(self, cap):
        self.cap = cap
        self.calls = 0
        self.by_op = collections.Counter()
        self.resets = []

    def note(self, request):
        self.calls += 1
        if self.calls > self.cap:
            raise RuntimeError("candidate RPC budget exceeded")
        op = request.get("op")
        self.by_op[op] += 1
        if op == "reset":
            self.resets.append(request["seed"])


def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead, episode_cap,
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = min(episode_deadline - episode_overhead, clock() + episode_cap)

        current_operation = "reset"
        primary_failure = None

        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolViolation, CandidateError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolViolation, CandidateError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure, index)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ---------------------------------------------------------------------------
# Cases, instances, protocol, scoring, aggregation, outputs.
# ---------------------------------------------------------------------------
RANKS = (2, 10)
COST_FLOOR = 0.01          # points; sub-0.01-point cost differences (tie breaking) are equivalent
ZERO_COST = 1e-9
MAX_FIELD = 200
CHUNK_RAW_BYTES = 3 * (1 << 18)   # 786432 raw bytes -> exactly 1 MiB of base64 per chunk
MAX_CHUNKS = 2
OPS_PER_EPISODE_MAX = 1 + 1 + MAX_CHUNKS + 1 + 1   # reset, load_begin, load_chunk x2, load_commit, solve
TIE_POLICY = "target_must_strictly_exceed_every_other_model"
OPS_TABLE = {"reset": 1, "load_begin": 1, "load_chunk": MAX_CHUNKS, "load_commit": 1, "solve": 1}


def episode_rpc_counts(episodes, replays):
    n = episodes + replays
    return {op: n * c for op, c in OPS_TABLE.items()}


def declared_cases(n_boards, smoke):
    if smoke:
        return [dict(kind="main", board=0, rule="mean", rank=2, cost="l1_points"),
                dict(kind="main", board=0, rule="median", rank=2, cost="l0_tasks"),
                dict(kind="perm", board=0, rule="borda", rank=2, cost="l1_points"),
                dict(kind="null", board=0, rule="zscore_mean", rank=2, cost="l1_points")]
    cases = []
    for b in range(n_boards):
        for r in RULES:
            for k in RANKS:
                for c in COST_MODELS:
                    cases.append(dict(kind="main", board=b, rule=r, rank=k, cost=c))
    for b in range(n_boards):
        for kind in ("perm", "null"):
            for r in RULES:
                cases.append(dict(kind=kind, board=b, rule=r, rank=2, cost="l1_points"))
    return cases


def build_episodes(seeds, cases):
    episodes = []
    for seed in seeds:
        for case in cases:
            episodes.append({"seed": int(seed), "case": case, "index": len(episodes)})
    return episodes


def b64(arr):
    return base64.b64encode(np.ascontiguousarray(arr, dtype="<f8").tobytes()).decode("ascii")


def build_requests(Xs, target, rule, cost, caps):
    """Candidate-visible load protocol: begin, chunk(s), commit. Opaque indices only."""
    N, T = Xs.shape
    rows_per_chunk = max(1, CHUNK_RAW_BYTES // (8 * T))
    chunk_count = -(-N // rows_per_chunk)
    if chunk_count > MAX_CHUNKS:
        raise ValueError("instance needs more chunks than the declared maximum")
    reqs = [{"op": "load_begin", "rule": rule, "cost_model": cost, "target_row": int(target),
             "tie_policy": TIE_POLICY, "score_scale": SCORE_SCALE, "shape": [int(N), int(T)],
             "dtype": "float64", "byte_order": "little", "layout": "row_major", "encoding": "base64",
             "chunk_count": int(chunk_count),
             "caps": {"dtype": "float64", "byte_order": "little", "encoding": "base64",
                      "shape": [int(T)], "data": b64(caps)}}]
    for c in range(chunk_count):
        a, b = c * rows_per_chunk, min(N, (c + 1) * rows_per_chunk)
        reqs.append({"op": "load_chunk", "chunk_index": c, "chunk_count": int(chunk_count),
                     "row_start": int(a), "row_end": int(b), "data": b64(Xs[a:b])})
    reqs.append({"op": "load_commit"})
    return reqs


def preflight_wire():
    """Serialize a representative worst-case instance and response; count envelope + base64."""
    rng = np.random.default_rng(0)
    Xw = rng.random((1000, 100)) * 100.0
    caps = np.full(100, 100.0)
    reqs = build_requests(Xw, 999, "copeland", "l1_points", caps)
    sizes = [len(bounded_json_line(r)) for r in reqs]
    resp = {"status": "plan", "gains": [{"task": t, "gain": 100.0 * (t + 1) / 101.0} for t in range(100)]}
    sizes.append(len(bounded_json_line(resp)))
    if max(sizes) >= WIRE_LIMIT:
        raise ValueError("preflight message exceeds wire limit")
    counts = episode_rpc_counts(1, 0)
    if sum(counts.values()) != OPS_PER_EPISODE_MAX:
        raise ValueError("operation table inconsistent")
    return max(sizes)


# -- trusted reference and baseline computation (pre-pass, before any reset) ------------------
def stable_seed(*parts):
    return zlib.crc32(repr(parts).encode("utf-8")) & 0x7FFFFFFF


def score_claim(inst, ref, claim, gains):
    """Evaluator-owned scoring of a (claim, gains) pair. Returns dict(eff, success, cost)."""
    l1 = inst.cost_model == "l1_points"
    if claim == "infeasible":
        eff = 1.0 if ref["status"] == "infeasible" else 0.0
        return {"eff": eff, "success": False, "cost": None}
    g = np.minimum(np.maximum(gains, 0.0), inst.room)
    success = verify_plan(inst, g)
    cost = inst.plan_cost(g)
    if ref["status"] == "first":
        eff = 1.0 if (success and cost <= ZERO_COST) else 0.0
    elif ref["status"] == "infeasible":
        eff = 2.0 if success else 0.0
    elif not success:
        eff = 0.0
    else:
        floor = COST_FLOOR if l1 else 1.0
        eff = min(2.0, max(ref["cost"], floor) / max(cost, floor))
    return {"eff": float(eff), "success": bool(success), "cost": float(cost)}


def key_main(board, rule, rank, cost):
    return ("main", board, rule, rank, cost)


def build_pack(boards, ep, ctx):
    case, seed = ep["case"], ep["seed"]
    b = case["board"]
    X = boards[b]["X"]
    N, T = X.shape
    rule, cost, rank = case["rule"], case["cost"], case["rank"]
    kind = case["kind"]
    if kind == "main":
        inst = Instance(X, rank - 1, rule, cost)
        pack = {"inst": inst, "Xs": X, "ts": inst.i, "caps_s": inst.cap, "map": np.arange(T), "key": key_main(b, rule, rank, cost)}
    elif kind == "perm":
        base = Instance(X, rank - 1, rule, cost)
        rng = np.random.default_rng([seed, 7919, b, RULES.index(rule)])
        for _ in range(100):
            rp, cp = rng.permutation(N), rng.permutation(T)
            if not np.array_equal(rp, np.arange(N)) and not np.array_equal(cp, np.arange(T)):
                break
        else:
            raise RuntimeError("could not draw a non-identity permutation")
        Xs = X[rp][:, cp]
        ts = int(np.where(rp == base.i)[0][0])
        pack = {"inst": base, "Xs": Xs, "ts": ts, "caps_s": base.cap[cp], "map": cp,
                "key": key_main(b, rule, rank, cost), "nonvacuous": True}
    elif kind == "null":
        rng = np.random.default_rng([seed, 104729, b, RULES.index(rule)])
        Xn = X.copy()
        for t in range(T):
            Xn[:, t] = rng.permutation(Xn[:, t])
        if not (Xn != X).any():
            raise RuntimeError("shuffled null equals the original matrix")
        order = np.argsort(-Xn.mean(axis=1), kind="stable")
        Xn = Xn[order]
        inst = Instance(Xn, rank - 1, rule, cost)
        pack = {"inst": inst, "Xs": Xn, "ts": inst.i, "caps_s": inst.cap, "map": np.arange(T),
                "key": ("null", seed, b, rule), "nonvacuous": True}
    else:
        raise ValueError("unknown case kind")
    pack["requests"] = build_requests(pack["Xs"], pack["ts"], rule, cost, pack["caps_s"])
    pack["x_s"] = pack["Xs"][pack["ts"]].copy()
    return pack


def run_prepass(packs, episodes, *, clock, until, restarts, record):
    """Reference solutions and naive baselines for every unique instance; fatal on failure."""
    results = {}
    timeouts = {"n": 0}

    def cancel():
        timeouts["n"] += 1

    for ep, pack in zip(episodes, packs):
        key = pack["key"]
        if key in results:
            continue
        inst = pack["inst"]
        try:
            if clock() > until:
                raise TimeoutError()
            ref = reference_solve(inst, seed=stable_seed(key), restarts=restarts, clock=clock, until=until)
            entry = {"ref": ref}
            if key[0] == "main":
                u = baseline_uniform(inst, clock, until)
                g = baseline_greedy(inst, clock, until)
                cl = baseline_copy_leader(inst)
                entry["uniform"] = score_claim(inst, ref, "infeasible" if u["status"] == "infeasible" else "plan", u["gains"])
                entry["greedy"] = score_claim(inst, ref, "infeasible" if g["status"] == "infeasible" else "plan", g["gains"])
                entry["copy_leader"] = score_claim(inst, ref, "plan", cl["gains"])
            zero = verify_plan(inst, np.zeros(inst.T))
            entry["degenerate"] = ref["status"] == "first"
            entry["zero_fails"] = (not zero) if not entry["degenerate"] else True
            results[key] = entry
        except TimeoutError:
            fail_required_baseline("baseline_timeout", cancel, record)
        except (RuntimeError, ValueError, FloatingPointError):
            fail_required_baseline("baseline_result_failure", cancel, record)
    return results


# -- candidate response handling -----------------------------------------------------------------
def require_ack(response, op):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise ProtocolViolation(op)


def parse_solve(response, room_s):
    T = len(room_s)
    if type(response) is not dict:
        raise ProtocolViolation("solve")
    if response.get("status") == "infeasible" and set(response) == {"status"}:
        return "infeasible", None
    if response.get("status") != "plan" or set(response) != {"status", "gains"} or type(response["gains"]) is not list:
        raise ProtocolViolation("solve")
    if len(response["gains"]) > T:
        raise ProtocolViolation("solve")
    g = np.zeros(T)
    seen = set()
    for item in response["gains"]:
        if type(item) is not dict or set(item) != {"task", "gain"}:
            raise ProtocolViolation("solve")
        t, v = item["task"], item["gain"]
        if type(t) is not int or not 0 <= t < T or t in seen:
            raise ProtocolViolation("solve")
        if type(v) not in (int, float) or not math.isfinite(v) or v < 0 or v > room_s[t] + GAIN_EPS:
            raise ProtocolViolation("solve")
        seen.add(t)
        g[t] = min(float(v), room_s[t])
    return "plan", g


def evaluate_episode(pack, prepass, call, clock):
    t0 = clock()
    for req in pack["requests"]:
        require_ack(call(req), req["op"])
    claim, g = parse_solve(call({"op": "solve"}), np.maximum(pack["caps_s"] - pack["x_s"], 0.0))
    ref = prepass[pack["key"]]["ref"]
    gains_orig = None
    if claim == "plan":
        gains_orig = np.zeros(pack["inst"].T)
        gains_orig[pack["map"]] = g
    res = score_claim(pack["inst"], ref, claim, gains_orig)
    return {"eff": res["eff"], "valid": True, "cost": res["cost"], "claim": claim,
            "success": res["success"], "duration": clock() - t0}


def worst_case_outcome():
    return {"eff": 0.0, "valid": False, "cost": None, "claim": None, "success": False, "duration": 0.0}


# -- aggregation (declared hierarchy, fixed equal weights) -------------------------------------------
def mean_of(values):
    values = list(values)
    return sum(values) / len(values)


def group_mean(items):
    """items: list of (key, value); equal-weight mean of per-key means."""
    d = collections.OrderedDict()
    for k, v in items:
        d.setdefault(k, []).append(v)
    return mean_of(mean_of(v) for v in d.values())


def aggregate(episodes, outcomes, prepass, packs):
    """Hierarchy: episode -> mean over seeds within case -> mean over cases of a board -> mean over boards."""
    boards = sorted({e["case"]["board"] for e in episodes})
    main_b, ctrl_b, base_b = [], [], []
    for b in boards:
        mains = [(((e["case"]["rule"], e["case"]["rank"], e["case"]["cost"])), o["eff"])
                 for e, o in zip(episodes, outcomes) if e["case"]["board"] == b and e["case"]["kind"] == "main"]
        main_b.append(group_mean(mains))
        types = []
        for kind in ("perm", "null"):
            vals = [(e["case"]["rule"], o["eff"]) for e, o in zip(episodes, outcomes)
                    if e["case"]["board"] == b and e["case"]["kind"] == kind]
            if vals:
                types.append(mean_of(v for _, v in vals))
        ctrl_b.append(mean_of(types))
        seen, base = set(), []
        for e, p in zip(episodes, packs):
            if e["case"]["board"] == b and e["case"]["kind"] == "main" and p["key"] not in seen:
                seen.add(p["key"])
                pr = prepass[p["key"]]
                base.append(max(pr["uniform"]["eff"], pr["greedy"]["eff"]))
        base_b.append(mean_of(base))
    main_eff, ctrl_eff = mean_of(main_b), mean_of(ctrl_b)
    return {
        "main_efficiency": main_eff,
        "control_efficiency": ctrl_eff,
        "plan_validity_rate": mean_of(1.0 if o["valid"] else 0.0 for o in outcomes),
        "baseline_main_efficiency": mean_of(base_b),
        "combined_score": 0.8 * main_eff + 0.2 * ctrl_eff,
    }


def per_seed_scores(episodes, outcomes, prepass, packs, seeds):
    out = {}
    for s in seeds:
        idx = [i for i, e in enumerate(episodes) if e["seed"] == s]
        agg = aggregate([episodes[i] for i in idx], [outcomes[i] for i in idx], prepass, [packs[i] for i in idx])
        out[s] = agg
    return out


CONTROL_EXPECTATIONS = {
    # Declared before scoring; evaluator-owned unless marked 'candidate'.
    "zero_gain": "empty plan scored by the verifier; must FAIL on every non-degenerate case (integrity gate)",
    "copy_leader": "raise the target to the best other model's row; high-cost control, reported never gated",
    "perm": "candidate episode on the same instance with non-identity row AND task permutations; plan is mapped "
            "back and verified on the original; reference cost is invariant (identity permutations are rejected)",
    "null": "candidate episode on a matrix whose task columns are shuffled across models (must differ from the "
            "original); target = rank-2 model by mean of the shuffled matrix; own reference solved on it",
}


def require_controls(expected, completed):
    if set(expected) - set(completed):
        raise ValueError("required control did not complete")


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, allow_nan=False, sort_keys=True)
        handle.write("\n")


def make_evaluation_evidence(seed_records):
    return {"schema_version": 1, "episodes": seed_records}


def write_results(results_dir, metrics, correct, evidence, feasible):
    os.makedirs(results_dir, exist_ok=True)
    for name, value in metrics.items():
        if type(value) is not float or not math.isfinite(value):
            raise ValueError("non-finite metric")
    write_json(os.path.join(results_dir, "metrics.json"), metrics)
    write_json(os.path.join(results_dir, "correct.json"), {"correct": bool(correct)})
    if evidence is not None:
        write_json(os.path.join(results_dir, "evaluation_evidence.json"), evidence)
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        write_json(os.path.join(results_dir, "qualification.json"), {"schema_version": 1, "feasible": bool(feasible)})


def penalty_metrics():
    return {name: 0.0 for name in METRIC_NAMES}


def hash_values(values, decimals=6):
    arr = np.sort(np.round(np.asarray(values, dtype=np.float64).ravel(), decimals) + 0.0)
    return hashlib.sha256(json.dumps([float(v) for v in arr], separators=(",", ":")).encode()).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ROOT_RELATIVE)


def verify_manifest(root, manifest):
    """Snapshot integrity: every declared data file must match its recorded SHA-256."""
    for rel, digest in sorted(manifest["files"].items()):
        if sha256_file(os.path.join(root, rel)) != digest:
            raise RuntimeError("resource checksum mismatch")


def finish(args, *, t_start, clock, smoke, packs, episodes, outcomes, prepass, ledger, complete, replay,
           flags, seeds):
    metrics = aggregate(episodes, outcomes, prepass, packs)
    metrics = {name: float(metrics[name]) for name in METRIC_NAMES}
    if not all(math.isfinite(v) for v in metrics.values()):
        raise ValueError("non-finite metric")
    declared = [e["seed"] for e in episodes]
    transcript = ledger.resets
    resets_exact = transcript[:len(declared)] == declared and (
        len(transcript) == len(declared) or (replay["ran"] and transcript == declared + [declared[0]]))
    integrity = bool(resets_exact and flags["prepass_ok"] and flags["controls_ok"] and flags["hash_ok"]
                     and flags["snapshot_ok"] and flags["wire_ok"])
    correct = integrity
    if PLANE == "final":
        correct = bool(integrity and metrics["main_efficiency"] > metrics["baseline_main_efficiency"] and replay["ok"])
    expected = {(e["seed"], e["case"]["board"], e["case"]["kind"], e["case"]["rule"]) for e in episodes
                if e["case"]["kind"] in ("perm", "null")}
    done = {(e["seed"], e["case"]["board"], e["case"]["kind"], e["case"]["rule"]) for e, o in zip(episodes, outcomes)
            if e["case"]["kind"] in ("perm", "null") and o["valid"]}
    try:
        require_controls(expected, done)
        controls_complete = True
    except ValueError:
        controls_complete = False
    feasible = bool(complete and controls_complete and integrity and not smoke)
    scores = per_seed_scores(episodes, outcomes, prepass, packs, seeds)
    records = []
    for s in seeds:
        dur = sum(o["duration"] for e, o in zip(episodes, outcomes) if e["seed"] == s)
        sc = scores[s]
        seed_correct = integrity
        if PLANE == "final":
            seed_correct = bool(integrity and sc["main_efficiency"] > sc["baseline_main_efficiency"])
        records.append({"seed": int(s), "score": float(sc["combined_score"]), "correct": bool(seed_correct),
                        "duration_seconds": float(max(dur, 0.0))})
    write_results(args.results_dir, metrics, correct, make_evaluation_evidence(records), feasible)


def order_field(X, names):
    mean = X.mean(axis=1)
    order = sorted(range(X.shape[0]), key=lambda i: (-mean[i], names[i]))
    return order[:min(X.shape[0], MAX_FIELD)]


SEARCH_HASHES = {
"files": [
"027591994936c655adadc4d6990cac7cd76d8e6b8255586b6a62bbefa26e7d30",
"03002bfb1ac6b398c4f0664a1c36c00956b2c0a1860c51edeb906a13a1231cda",
"0510ed00555a5768af674ee43402df8e4e69af6e102673dc573c161302f9321d",
"0efb60d3ec46c5f9e2fb410457d32984f5b382e195da5142b3a4741d54b86a43",
"13bfb2354e66206b5ec3ddb1833782c7785d2d9be767250645b834ca7044db57",
"13caae6f05c5ffe3bfc3a3298677e4a19ea39cf7274a3c3cecd660161091cf24",
"14a74cc87803d8ea030361e494b7944ff4c4eaef9f3ec621d984c97cc7c1cb02",
"1a94ed0bac004b3e914c529594578f7384b046661fa2a096ca67458fd4cb6033",
"259bafb7578db0f202164a1151eae3c68f8a6030e8e199e822dc9a4743589dff",
"29f6d35568e04c914539abcab1ff8284ea3994c6ed740d12ca39e9794ed4a8d5",
"2cbe8856bc90af01c27700564d65a2861a5fd2502378c8596a7e09199095f684",
"2e9abd088f955c28ad1954dc824e14ee6b7c9bfc33e40494cfa7737df5f60fe5",
"3095e864643345affd5df5e59112779c53c4204b8718e4637357aa92d3a80aae",
"3195f35287c8f167ed09aa0bab6cd552414831f48f11f548730f091c3b8b396b",
"322f81764ac82717b3ed7bd34f50083f5f98c9416603dfbc03a1bfee0837489e",
"364ead89ea463845346bf21b95dca67b0ebcd173739e31ba2efbe8de70a5f246",
"36768820eeebeeb3cc9827a878243af7fd8297e30f15131a671aeeeba205a23b",
"3e1fb538f7688e2eded8f6cfac22837161d4ae2e1d01a8fcf7b92bc4b07ba2d4",
"43a16e2acd68908880f7b36643308f469700437d8bf1815501a1887245ed32a0",
"489c6888b493292acfe2621f1a400f1f8270ef46d5d5ccf6ddd136cf5316bf04",
"4f6ddb2e2836a0dd742c6e8df6aab0e34f103def651bccbb1d0d48f44819da51",
"4ff35142c74a87fbddc78e8d63c27a088b08b1745c2ef3286b9ed5bf3b910518",
"508c56bd74d2642999dbb6309a7b63f75a328224afeac42627aa9a576438da93",
"528184662f51f0063181914a78589c2545639136ae22d608a60f22186fc86c6d",
"53d88ac43310fba81fc065c3a57ab4076416130f6c9baea92fccfebb0ccda7a6",
"5f890131f02ed82ab73af73e6db08d93ccd43945388f398489cc7ef17d550bbe",
"64323a36020de7366703539ace2766f1ee517b893ac819080dc2f399cb982d68",
"6794f6c1e6b39a97cbe5b79430c1dfc1ed030a3035f8de58efd82afff8696fc6",
"6b1844b2f2766b162bbb27251dd1f6ff89b78c02dd3345707a43af71d4bdcbaa",
"6bca8a3bd0d63851cec24a51886a06a13546ea070acf917c3dd2a8ff4e1f3f3c",
"6eaf2c080d5e22c493541ffb79f2167b7c9890bf9d71b56c7627868f37a32d8c",
"73e71281cad4952898eaea489176bff3a3f92190331e99e2af6bc5aa154ab6f2",
"78f9d25432c2561f34d212157ed942b23528e2d1e827b7843554349128bf7ca3",
"7cbc485cdcdb3f9daf7238071a9ec15653102026914bffcdbec38d2bb50e6595",
"862995eea7c6e7590c212ac923505e0426de1f6bbdfcc47f3eb747903c4f6e7c",
"8b743ea30c75d733afef4017d78863d539fa260e985961b571da45e408da4ab7",
"95959418f2aaf8f5afbc80dde81da180a01e4b2c59cc8a10f61010275065055f",
"978809f25fc9f2496812d85e7bab46a9a3cc2116ee03cc1da3201c65317cdcb3",
"a2c56d3d26b7169bfff7f130d8be48fe9ba774a40b3630f5f53b86d4f3802704",
"a33c2ba245af81dc1bb1603bcd338b8abcfb0ba056a20b6d6c1e77637adca658",
"b2c0c5f8aac86fdfdb4ad93a3d625eb45db9e3753789c0662a03ea1d695cdd67",
"b892611a057b481399855abbaf65cb8c3a987a9ffca7ed458db82a714cbb4320",
"baf246e4d3b6e11bd0d0335dacc6283806cff2b389f20dd81c1c94bb845fafd3",
"c557c91a4df94ee811fe05565623be7525f78ec51bd2e8e36b55cf1388f3756e",
"cbc4df07281bd5b4393d17f0f5fc2c2857e75f8edb0a54f152f44059f6ae03ea",
"d08865d3aafcebd7a74e5197a4eaabbb7881a797e5e7d9fa783ab4368e86cd58",
"d4eb487e79bcdd7329bdcb10f5116364c2501842fe5e58da6e0bd717f90ee71e",
"d7759c485ad6ce5820c3e08b2d9127ea6b139611aaa21e72b8e6d7f755532933",
"d9397f112735a5cd8bc97d78e67494790736d0376904f676c143363e56d1db3c",
"e6d5138a73d510339a2673969dc08a00b9dffa6dd3ae9bc4c61060f8ee171ffb",
"e8b5f4538548b0a890de6a969c214d941ad5d91fbe537d8c4ee7b5300ca02a90",
"ea5aba01688004fdcae8469a3e1e5c108578786519eacec763958af7578ea286",
"f035273568b79cffb0357ad1bd35fce0b75795022f8b629674cbaef8119f3dfa",
"f0f94e7ef2a2217886ec9e19570e80d53e639d42e13cf572b15f5bbb999d4c32",
"f37ed208e0f43c5d7c216650178bfb71989a709943286e5bff1178a37ae14886",
"f5c6e79530da2d383c77d2725e022cfb53be002b9bb6fd1e23d3bdfd81c471d3",
"f62be97588388fc141a9ddb25a47f30941da170b18a032583fb3f9dab4aecb1a",
"f9719df0982b06fb29f7372dc5c1c6be06f9e6017aef1f9ba17eb8db6be4b989"
],
"rows": [
"0082785b7fcda494dde7617c21d89720435b630e094b7ec525ff087be94fd587",
"0290d87d38c2d6209db6784f0ec3ff1078fdae026b75b8f5febda45df611c5f4",
"1197396c0729a85ce5352336d23ee3da90ccd1d9569e11d3b51663ad8a73619d",
"12fec50bbf3432ca8abb77937f4482b4b48d0e6666b0bb99686206cfb7f38a4f",
"15ad0c3cd9638e49457adb1b229b91ad814c4de639ec27d5b23fd48074bc0be3",
"1919e0bab10a3acd0a417ac7b8649daa3b160ab0516ff58cde1089c4d6fb0b67",
"1b65fe7c828d832902991bfaa1711d43b166d49ad4fa45397b1141c603e38aad",
"1bae85f805be677f2739ce68ae87c515097ffd000c7b1257ca06d884a3086556",
"1c3bf1511f4a5207bbd472ec1f7025226907936207d39a02023eb11eef43522a",
"1c76cb5b0beaa5a9e2fe7b9dd19c08b81fe04ab376bec8648c2ea391463c351a",
"1ddabc0e275b00aeb74cd80aa1a089773576a989b05504fc27199ad2cc66b43a",
"1eb3038f5eee89cc0bae0bf896d25fe07f064d5e4b13de4a77e3d2cabdd2c37d",
"22351695fbf02e0416508588073ecb24a55fabf7c7fef50cbfea7a59da57ade4",
"2899d79c0c62bf4e2452dd442d8359436583107ad92f02e27e6e7f772c39e6da",
"28e7a310fedc21e775cbd88dc2b6c378530ab6d067096b8df465277a2fe076a0",
"290d797e67be9ad1c71f5a3a6be88960c51295382884e5747df2b220a95446ce",
"2acad3447cd69a9b25d7c5b61f98d2caae6aeb682fa343864a0ccbcd4905f120",
"2d6be3b89222fe29b07e5dc8c40a59fcd9608270168030fa332e934d404d676a",
"321973f817b1db0e235373de6fe1e4fbcea0db053501222e167959072ecd0024",
"32d05a09322edf70746495305089f52a35a9d054a79045d6dc5ea6b27a971120",
"376a2889e58945798df650426aafb00ea280855a9f703dea7936cf9e63144121",
"3e9609b50b034971857adeafa4ef7c84093d01856077dde9a28b72b5eed4b930",
"42d102ac6404349649ae6fe4088901e596df6859247e62b768d6fb806a8becd0",
"46f16fc0f19ea520c41b2f422dd7c9e3b274c0a1662be6bb8c0f3e3779482f5f",
"47586b15053474f88d7794b16c4d009cf1cfdb38dd4ba5329fc8c2e17e5c2cb1",
"4a227e29df2011c7406dc3bc33428749a92063bfeaee6f5c9167a95fd306d8e0",
"502bf44090664ff3cc41d0bdfc444ee5133a2fd81ea554c1ce85f24fb99607e6",
"5221e34ff248662672af6a82f4464b84717bfb7c4bacabcde3760b20445d6ec3",
"53aa33967385e246fb882b90ed14c1652b7cee9a13d5cbae52a3f331a8955eab",
"57ce37ec95190c1ad5d11d98c7267e1565932c6ae6c5b1d4fd816cbc516d1527",
"5e22e5a6d77a954dd0bd9cb55fe6b5aa99d113a78ed8f4aa9bdf21f6d9798757",
"614febbc55f7eb36dd396aa2f2b679b099fc707d7814c7b34066f8ce2f6527ae",
"651a609dd169a597029fad2f06821c01d33ce26b42d112aa36a3d07dd922c177",
"6a4f5a46498b422edf005a4fb4e5a1e3f49f1100972bda52309b8dc097c0d946",
"6d1b9f4ed0c5cee7cd73cce2df4620c0031c0f8de17c873213d6c8563da84b76",
"6fe8ecc9bf6926aa313163afc6aff378d305034748543e599b017dedff960fb4",
"71ef4c4efab9c1bcd5a50bca3dd58e53040f2d4a9cfe6853ba4da106e52e4817",
"73a5b4fe11d475fad653b8aa4defaba927fa1467d43d7f31dbd9ca5e01edc5db",
"7540e8f8ceaf5efbc21bf9e0c61ac4ac161c7d1ba3ce948c07d35dd32af769f8",
"79842214bb73f4657dc4cee663920fdc6e2218305542b95f872d99ebcf9fdfc7",
"7cd9b392df6bf81ff68e0c4c340d38ffdd7b485097ad6397548d8d38e195bfd7",
"7f2122cc40c97355a12d35599b50f69710c6be0c73a5645e2e3f6faadbfa5b18",
"803837e9d323b323af5700b847c7242503084d3d758b1fe962c1d10e410ab7e2",
"85ec0551cba2e8e47c3dbb9803feb3b02126953c150d562d680e4a12277e88c1",
"8a7a4d2a9a6ee1b2d471391dee792bbd489d65a5870d7584e65a0cc941fb79c0",
"8b12e5bc57caf2d90d652899d62202bca2107e973062703ff434ee12f8a869f8",
"8d44f41444a32b39c12241811f00b31542db3fd77ab46a56b8cea6783c69617d",
"901752b2e4589eb44012578d77b3be50c890dd3186e3c9c7e7b7c4cf5751e316",
"923e76a4ac73b0be944a6bb16ef7d2ca0e780abfe6bea9f1fddc6b737779d501",
"9421be7ab592efa3e512efcfc3ddfa78c3cbc93cfd3dbab22d71b4d4a3e4cf93",
"9cc608f3652d86748cd512613ae77aa3a8af22a3cdfb0af6c2892795fa092b48",
"a3993374f1179bc428eb42b8f3ccf856fb5a51ba8341c96e34ff560fd1897988",
"a475be873ee49a1a7bdc4cd8356b143799f95d33acba8dfd7aa842063bf00bc5",
"a832e2ee06ee93c56b7398c1c79584290147b6d0fd527967d6b84ff789171f44",
"aa430f8a08bdfd5c034ecb36fc78cff00d1ffa66af30c67ad99cb32e102eccb9",
"aaaa6e6b0376e2caecf11b3b263d30afdecb089f8cc7751ed9221ef7362f00f1",
"ab59b2b73cc42b3c9e4aadada458b54691a3889c0cf7294f12ba11692a3d155c",
"b128113c433a1d046a05c4c23da53bc55164ad7c6525cf1b0330dd2041731541",
"b6366f60125365c1411cc8a93168c2926bf2427c98221f5ffb691ff6bd162e92",
"b64f11cb10c15ee11ab4c2ae5adb84e07bbee62e611d1a898bb17749b3f6cbfa",
"bdf605d0c58bb1470fa2b5729200e50a84b35a9951c78ddf9f9a0e5de19c53ca",
"c4023fd6bc9541ae33bb6f6ba6b5ee743214a68159d43542d1ea592a356c832f",
"c84729a5bbf1e348de5ecee7bc7feae82b40a8acbfe463a1cef5db8054d11c71",
"ca475cb97ec784a367ed3543bbeb3ae4e572cca883ed36941792028c40af1268",
"cd4795b2655d3032c53164a1943e08b96ddf3afc9d9c889b11416067523eda1a",
"cda778df36e3d9a4a0b580dd4edef50ef1a3f20b80061b0386ad0a98ba257d98",
"d6aceb5f79872bc142b23bfc60fd1351000323d831b8c340a658428963e1de95",
"d81a914517ccbf7dd2f6f1dccfba61d37f711186d8e52e8729aa7bb8647c981c",
"db0e030f95fd74a8c9b98da69af7c2fe8602932e18ccc66aa6e25793fc96f925",
"dcdb92c6675d22a9d8efc7c36d2b0090ac707dd9c1c484291fe78c12db68626c",
"e248ee64ad35a061e1839ef6f978f195e9186baaac6d84226142b07c075869f7",
"e7e9177951898f017992fe049d3d5a782ef32b05456a111e3bc04457763aa70e",
"e8e6794706eeaa245b725f6ef148994f896c08e9960f0cfed34fd20e67ca87af",
"e96b954da5c5246eb11daf6317a0c6cc5ecac6b585e8168c862ecb937332803b",
"f22e6683b576e467aff2daa0df0b8cfcf5d9e94d840b6e6521b1b2378850b8a2",
"f325f25a4ad0c9d6d2548fd25897b1e4f27c1667103d7e6a8f9fa9e4461a62fc",
"f8b62edef038a2748a469acf958c370729c212cede1e8485b6dd70a69a49697f",
"fed930b03b6cf96b6bb2afa72ada2a6335c02faf8db19df15367282ef7afff56",
"ff633a55616a763434d419f303fabef61add01bd3134eaf45cd60a111dfb3cb3"
],
"cols": [
"06adce98076ec90357eec810bf5b90208187ec4a7b901a452ef36b04d5355eee",
"0cd71d0c700874dcca21a59e4acd9c2876ee7ee4fea30acbeffbef1877ee5338",
"11ee069b10a4ab97b3fe0e7ff7807c0bde2ae89e7bff8bd4cb76014f7c44a043",
"12cd75036bd3faf3e058eb250189efe36ae21cee9126e19214c9ae15f5e09caf",
"22909d2f54099d0e158bb80e1d4eec685b6eecb3c37cf33bac28a8257aa8ae50",
"2da48e594cfc797526798fc6dbf07eb7949a641c7fd7f66dd8b4e69554fa4fa1",
"312d110036524625c6383f73adc82e02754214509550fc04237a8f37d380f2e3",
"3196826021ddcf6f7df119849d82f42d95d0da3bc42f2bdb6b0bd3e56688444b",
"3946acc496c7374d9feed499592bd5e7139282a439b3f27e3ec6b95f1d44faaa",
"4163c3bd9e5dff076ea6fdc65b7d1805d24974b169dbb6448ea2da7602775d79",
"4522a482075a72fc22359e3b4084d0d7d2e57552fff438f6cdb90940f95d4c0d",
"51608786c3fb35b0220be0cd381b2746cdd0dbf17e7fbe82383d4744329488f2",
"5618c78d5594513d39dd56ad1732a059e9dd27c9d5fc18004e92b8a75b8d7049",
"57160edc1d1e1875b161a5bc846b373cc8bbf010835ee3faf3a4955107789c57",
"5bdcf47294aa8f15b6007e4ba2d3df5f5cef0ba69be823ab974202117aaf5cc3",
"5cf3541160d30ed35ba19d76476ba23de9aee52ceb7cb21c0c19e724b29be0f1",
"5dca547335a72bce01e5da20066ac0b805cc5c5127d80b85ac2b7718b69b0082",
"6745cfabf13ddd7765b6896f0901bb970b9f8896073b3d6fa27bffdbbb846d3e",
"6a06613e6b1b11a722548dfb0b1f829dc170117529840f6f4ea5fa18217ac416",
"6c88b01c252049b4f9507a7042de18facdf1cbd044c0c20f953d8d09abec20ff",
"6d0b4f3b84c6ebaec80d291386e500ac666169e39e58ad43f3a7ab12ddc25e40",
"7dff83086d4f18c0332a35a15d4b87200afdcc32e738564b4b92426aad17d583",
"7f44ba571cdbc62b5537a4800b1009224435010fe7209b6327f0243b3eac2fbe",
"8065ebcc49110ebf01ee5ebe4f89f50cfe3e7aff2906178c1a612bbccbf06ac3",
"8233cffe480023001bcbe02aa11c0b80c17fa7e30eb20b78407d44ee10120b45",
"86a7598761999564179536adffa00d83a3d6a45e5b561747b1f79727be530d11",
"8ca3b0576b8219da7c3b4467c3636a39b68dd5563751ade670064da254d446e3",
"8df401be81489f62e9015cc6d2a3cd529f187cc5463da54fec8cbe94a08f9c45",
"8f15ef389b03bf9ba7d1e78e13c10024592548f9af100f0c5fa39f4681917855",
"91ddf0d29aeafad206e3fb7301f312391f116942b7e47dcd1bc3e64d39aa8718",
"96a2c9be93f8bd93b0b32968595f54f08b5a7e6bcd3f93027c1f392dfab6d66b",
"9bb2521df4366d00823e4b9af0f53b1d93866c1342fe785981c32dcbbc4175e4",
"9c2aef7a596297cb0965b05b0a7af9146a0824d0fbb38f1d6836493e9d58085e",
"9d55fffd0f8ee7f89b2133a879fad3a1851a929fc964176b42a93266030179df",
"a49e13ccd7043a237a1f66ede642d2f69f8a77fe621378b2584406241b28c3fc",
"a697f6244c351a4a92763e05fef2b9a1feb4fc0289ad2556ba84a511e6031124",
"a7b903550a266d76b52bddd22b2fcefa1069d3b9c99bc4959dfdd95193fc2549",
"a7d082edd185df64af83d29f1c4faab59b90f91148358279b0cf3ce739c3cf6f",
"b1e968a9cc1d3f581474294402a2b4a555f3b06dd0a95d409e28d25922179922",
"b2f6fa39c1dafbf69093ad8b57a51dadafbfa277a2e4797a25cabe8f45bd4e39",
"b4cea550123e3292a9c6c3b9e3460ec10645d11227893f9112108599a887c8a2",
"b7e2dfe2643466849d6f596549cac1810fb3f052d387308235c23842ae17e1e6",
"bc25631becfbf11774746b26802bb0a3ea034ac2aae2a9cbc5daf6f7d3d59084",
"bcb88100e738cefe81cc891c5459deb9137a61d0b09f693ffd9b19bef130c857",
"be16a15cb6832dcdb876561cacef0139df5fb84162daba6dfe2b5bb0c5d65053",
"bef0de01eea3f5948fb822364e7a04c10a3954fdeb90d3d4680784e5a95b44ad",
"c2d3346b93e3f7f7d5446d07fa9b669e41e6243fac30a23a7aacf4df9f7516c2",
"c8a5fc18749a9ed9f3273338250bf8ab62566166c25902b63d8aaecc10e9bc94",
"d18a2eb8c59e8aa46bedb40b9f124d2d8018d95fcd6e4148b1010ad78f880fd4",
"da9fb38ce3997a76e3e1d457a403c6f72b6107b2683b45e5a408718fe39385b1",
"e8af95ada0b544a390f352da78c24761ce73fa6efa013b0122e34dae5afc7a4e",
"e9d6a0499c3dd13be9d0e4d9a80badf387229d4c436890e0ad1e581dd7012b4b",
"ec95fbaa24445d235d5145e33c59f3e8184f6298ff7b4e83d6bb442a4985c5ff",
"ed4afc6f4b0be6545e8f9d9cf37f0715d46e44a0f8852029d4fc7cbd0c76a11d",
"fc4e7b685401de3072ad6b07347ed029e74c88642d469af50c40cd336d621cea",
"fc5bfbcf5001ad87cb7bdf468cd8e9a1d6c52b2eefbb8b9ede362b11d518e9d5",
"ff06fbd17f22cf7606700a14c5548c9d412a3d93400133a66ef36f7ab84f71ca"
]
}



# ---------------------------------------------------------------------------
# Final plane data: Open LLM Leaderboard snapshots (public) -- two boards.
#   board 0: 'contents' parquet, six normalized benchmark scores per model
#   board 1: 'results' dataset, subtask-level scores for the same model pool
# ---------------------------------------------------------------------------
CONTENT_COLUMNS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
CONTENTS_REL = "olb_contents/train-00000-of-00001.parquet"
SUBTASKS_REL = "olb_results/subtask_scores.json"


def pool_hashes(X):
    return sorted(hash_values(X[i]) for i in range(X.shape[0])), sorted(hash_values(X[:, t]) for t in range(X.shape[1]))


def load_boards(root, smoke):
    import pyarrow.parquet as pq
    with open(os.path.join(root, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    verify_manifest(root, manifest)
    rows = pq.read_table(os.path.join(root, CONTENTS_REL)).to_pylist()
    pool = {}
    for r in sorted(rows, key=lambda r: (r["Submission Date"] or "", r["eval_name"])):
        vals = [r[c] for c in CONTENT_COLUMNS]
        if r["Flagged"] or any(v is None or not math.isfinite(v) for v in vals):
            continue
        pool[r["fullname"]] = vals          # later (newer) submission replaces an older duplicate
    names1 = sorted(pool)
    X1 = np.array([pool[n] for n in names1], dtype=np.float64)
    with open(os.path.join(root, SUBTASKS_REL), encoding="utf-8") as handle:
        sub = json.load(handle)
    sub_scores = {m["fullname"]: m["scores"] for m in sub["models"]}
    names2 = sorted(n for n in names1 if n in sub_scores)
    X2 = np.array([sub_scores[n] for n in names2], dtype=np.float64) * 100.0
    for X in (X1, X2):
        if not np.isfinite(X).all() or X.min() < -1e-9 or X.max() > SCORE_SCALE + 1e-9:
            raise RuntimeError("score range violation")
    r1, c1 = pool_hashes(X1)
    r2, c2 = pool_hashes(X2)
    file_h = sorted(manifest["files"].values())
    h = manifest["hashes"]
    own_ok = (r1 == sorted(h["boards"][0]["rows"]) and c1 == sorted(h["boards"][0]["cols"])
              and r2 == sorted(h["boards"][1]["rows"]) and c2 == sorted(h["boards"][1]["cols"])
              and file_h == sorted(h["files"]) and len(names1) == manifest["inclusion"]["n_models_board0"]
              and len(names2) == manifest["inclusion"]["n_models_board1"])
    src_h = sorted(m["source_sha256"] for m in sub["models"])
    disjoint = (not (set(file_h) | set(src_h)) & set(SEARCH_HASHES["files"])
                and not (set(r1) | set(r2)) & set(SEARCH_HASHES["rows"])
                and not (set(c1) | set(c2)) & set(SEARCH_HASHES["cols"]))
    boards = []
    for X, names in ((X1, names1), (X2, names2)):
        keep = order_field(X, names)
        Xf = X[keep]
        if smoke:
            Xf = Xf[:20, :8]
        boards.append({"name": "board%d" % len(boards), "X": np.ascontiguousarray(Xf)})
    return boards, True, bool(own_ok and disjoint)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def bounded_line(text, limit=256):
    return "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in str(text))[:limit]


def record_episode_failure(failure, index):
    if PLANE != "search":
        return
    line = "episode_failure plane=search index=%d component=%s category=%s operation=%s" % (
        index, failure["component"], failure["category"], failure["operation"])
    print(line[:256], file=sys.stderr, flush=True)


def record_baseline_failure(category):
    if PLANE == "search":
        print(bounded_line("baseline_failure plane=search category=%s" % bounded_failure_name(category, "unknown")),
              file=sys.stderr, flush=True)


def run(args, t_start, clock, smoke):
    plan = SMOKE_PLAN if smoke else PRODUCTION_PLAN
    flags = dict(prepass_ok=False, controls_ok=False, hash_ok=False, snapshot_ok=False, wire_ok=False)
    preflight_wire()
    flags["wire_ok"] = True
    boards, flags["snapshot_ok"], flags["hash_ok"] = load_boards(resource_root(), smoke)
    if smoke:
        boards = boards[:1]
    cases = declared_cases(len(boards), smoke)
    seeds = SEEDS[:1] if smoke else SEEDS
    episodes = build_episodes(seeds, cases)
    n_replay = 0 if smoke else 1
    rpc_cap = sum(episode_rpc_counts(len(episodes), n_replay).values())
    if not smoke and rpc_cap != CONTRACT_MAX_RPC_CALLS:
        raise RuntimeError("RPC budget does not match the declared contract total")
    require_joint_workload_budget(plane=dict(
        wall_seconds=plan["wall_seconds"], startup_seconds=plan["startup_seconds"], finish_seconds=plan["finish_reserve"],
        prepass_seconds=plan["prepass_seconds"], episode_count=len(episodes) + n_replay,
        episode_seconds=EPISODE_SECONDS, cleanup_seconds=EPISODE_OVERHEAD))
    packs = [build_pack(boards, ep, None) for ep in episodes]
    prepass = run_prepass(packs, episodes, clock=clock, until=clock() + plan["prepass_seconds"],
                          restarts=plan["restarts"], record=record_baseline_failure)
    flags["prepass_ok"] = True
    nondeg = collections.defaultdict(bool)
    ok = True
    for e, p in zip(episodes, packs):
        entry = prepass[p["key"]]
        ok = ok and entry["zero_fails"]
        if e["case"]["kind"] == "main" and not entry["degenerate"]:
            nondeg[e["case"]["board"]] = True
        if e["case"]["kind"] in ("perm", "null") and not p.get("nonvacuous"):
            ok = False
    flags["controls_ok"] = bool(ok and all(nondeg[b] for b in range(len(boards))))

    brokered = args.program_path == PROXY_PATH
    if brokered and not os.environ.get("AGENTIC_CANDIDATE_SOCKET"):
        raise RuntimeError("broker proxy path without broker socket")
    cand = BrokeredCandidate(PROXY_PATH, clock) if brokered else NativeCandidate(args.program_path, clock)
    ledger = RpcLedger(rpc_cap)

    def rpc(request, timeout):
        ledger.note(request)
        if not brokered and request.get("op") == "reset":
            try:
                cand.start()
            except OSError:
                raise CandidateError("candidate_start_failure", "reset") from None
        return cand.rpc(request, timeout)

    hard_deadline = t_start + plan["wall_seconds"] - plan["startup_seconds"]
    common = dict(hard_deadline=hard_deadline, finish_reserve=plan["finish_reserve"], reset_timeout=RESET_TIMEOUT,
                  episode_overhead=EPISODE_OVERHEAD, episode_cap=EPISODE_SECONDS, rpc_cap=RPC_CAP_SECONDS,
                  clock=clock, rpc=rpc, worst_case=lambda ep: worst_case_outcome(),
                  record_failure=record_episode_failure)

    def evaluate(ep, call, work_deadline):
        return evaluate_episode(packs[ep["index"]], prepass, call, clock)

    replay = {"ran": False, "ok": True}
    try:
        outcomes, complete = run_declared_episodes(episodes, evaluate=evaluate, **common)
        if not smoke and clock() + RESET_TIMEOUT + EPISODE_SECONDS + 2 * EPISODE_OVERHEAD + plan["finish_reserve"] <= hard_deadline:
            rep_outs, rep_complete = run_declared_episodes([dict(episodes[0], replay=True)], evaluate=evaluate, **common)
            replay["ran"] = True
            a, b = outcomes[0], rep_outs[0]
            same = (a["valid"] == b["valid"] and a["claim"] == b["claim"] and
                    ((a["cost"] is None) == (b["cost"] is None)) and
                    (a["cost"] is None or abs(a["cost"] - b["cost"]) <= 1e-6 * max(1.0, abs(a["cost"]))))
            replay["ok"] = bool(same)
    finally:
        try:
            if not brokered:
                cand.stop()
                if not complete_flag(locals()) and repair_visibility() and cand.stderr_snapshot:
                    sys.stderr.write(cand.stderr_snapshot[-4096:])
        finally:
            cand.cleanup()
    finish(args, t_start=t_start, clock=clock, smoke=smoke, packs=packs, episodes=episodes, outcomes=outcomes,
           prepass=prepass, ledger=ledger, complete=complete, replay=replay, flags=flags, seeds=seeds)


def complete_flag(local_vars):
    return bool(local_vars.get("complete", False))


def write_penalty(args, t_start, smoke):
    seeds = SEEDS[:1] if smoke else SEEDS
    elapsed = max(time.monotonic() - t_start, 0.0)
    records = [{"seed": int(s), "score": 0.0, "correct": False, "duration_seconds": float(elapsed)} for s in seeds]
    write_results(args.results_dir, penalty_metrics(), False, make_evaluation_evidence(records), False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    t_start = time.monotonic()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    try:
        run(args, t_start, time.monotonic, smoke)
    except SystemExit:
        raise
    except BaseException as error:
        name = type(error).__name__
        name = name if name.isascii() and name.isidentifier() and len(name) <= 80 else "Exception"
        if PLANE == "search":
            try:
                message = bounded_line(str(error), 200)
            except Exception:
                message = "message unavailable"
        else:
            message = "message withheld (sealed final)"
        print(bounded_line("evaluator_error type=%s message=%s" % (name, message)), file=sys.stderr, flush=True)
        try:
            write_penalty(args, t_start, smoke)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
