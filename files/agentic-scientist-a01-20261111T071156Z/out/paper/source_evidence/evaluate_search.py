#!/usr/bin/env python3
"""Search-plane evaluator (development-only score; HELM MMLU v1.13.0).

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

PLANE = "search"
SEEDS = [11, 12]
METRIC_NAMES = ["combined_score", "main_efficiency", "control_efficiency", "plan_validity_rate"]
ROOT_RELATIVE = "resources/search"
WIRE_LIMIT = 64 * 1024 * 1024
PROXY_PATH = "/broker-code/candidate_proxy.py"
CANDIDATE_THREADS = 4
WALL_SECONDS = 1800
RESET_TIMEOUT = 8.0
EPISODE_OVERHEAD = 3.0
EPISODE_SECONDS = 12.0
RPC_CAP_SECONDS = 10.0
CONTRACT_MAX_RPC_CALLS = 582
PRODUCTION_PLAN = dict(wall_seconds=1800, finish_reserve=20.0, prepass_seconds=240.0, restarts=4,
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


# ---------------------------------------------------------------------------
# Search plane data: HELM MMLU v1.13.0 per-subject model-score tables (public).
# ---------------------------------------------------------------------------
HELM_PREFIX = "helm_mmlu_v1.13.0/subjects/"


def load_boards(root, smoke):
    with open(os.path.join(root, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    verify_manifest(root, manifest)
    rels = sorted(r for r in manifest["files"] if r.startswith(HELM_PREFIX))
    tables = []
    for rel in rels:
        with open(os.path.join(root, rel), encoding="utf-8") as handle:
            doc = json.load(handle)
        header = [c["value"] for c in doc["header"]]
        em = header.index("EM")
        tables.append({row[0]["value"]: row[em].get("value") for row in doc["rows"]})
    models = sorted(m for m in tables[0] if all(m in t and t[m] is not None for t in tables))
    X = np.array([[t[m] for t in tables] for m in models], dtype=np.float64) * 100.0
    if not np.isfinite(X).all() or X.min() < 0 or X.max() > SCORE_SCALE + 1e-9:
        raise RuntimeError("score range violation")
    row_h = sorted(hash_values(X[i]) for i in range(X.shape[0]))
    col_h = sorted(hash_values(X[:, t]) for t in range(X.shape[1]))
    file_h = sorted(manifest["files"].values())
    hashes = manifest["hashes"]
    hash_ok = (row_h == sorted(hashes["rows"]) and col_h == sorted(hashes["cols"]) and file_h == sorted(hashes["files"])
               and len(models) == manifest["inclusion"]["n_models"] and X.shape[1] == manifest["inclusion"]["n_tasks"])
    keep = order_field(X, models)
    Xf = X[keep]
    if smoke:
        Xf = Xf[:20, :8]
    return [{"name": "board0", "X": np.ascontiguousarray(Xf)}], True, bool(hash_ok)


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
