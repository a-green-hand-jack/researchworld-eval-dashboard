"""Minimal-perturbation search for Bradley-Terry leaderboards.

Three perturbation families (threat models), each counted in units of single comparisons:
  drop : delete an existing comparison                 (data cleaning / filtering / dropping)
  flip : change the label of an existing comparison    (label noise / corrupted annotator)
  add  : insert a new decisive comparison between any two existing players (vote injection)

For a target pair (hi, lo) with theta_hi > theta_lo we search for the smallest perturbation
after which the *refitted* model ranks lo strictly above hi.  Searches:
  * `amip`   : one-shot first-order ranking at the original fit (Broderick et al. style),
               then verified by refitting (doubling + bisection along the fixed ordering).
  * `greedy` : iterative first-order step with refits after every batch (batch size is a
               fraction of the current first-order estimate, minimum 1), final batch
               bisected.  Every reported number is verified by an exact refit, so all
               costs are *upper bounds* on the true minimum.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from .bt import CompData, fit_bt

FAMILIES = ("drop", "flip", "add")


# ---------------------------------------------------------------------------------------
# Full type table: every (i, j, label[, home]) combination so that flips/adds have a slot.
# ---------------------------------------------------------------------------------------
@dataclass
class Table:
    base: CompData          # full table with original counts (zeros where absent)
    n0: np.ndarray          # original counts
    pair_id: np.ndarray     # id of the unordered/ordered pair slot of each type
    lab_type: dict          # (pair_id, label) -> type index
    X: np.ndarray


def full_table(d: CompData, labels=(0.0, 0.5, 1.0)) -> Table:
    K = d.K
    if d.home is None:
        ii, jj = np.triu_indices(K, 1)
        hh = None
    else:
        ii, jj = np.where(~np.eye(K, dtype=bool))
        hh = np.ones(len(ii))  # NBA-style: first listed player is the home team
        if not np.all(d.home == 1):
            raise ValueError("home-advantage tables expect first player = home team")
    npairs = len(ii)
    L = len(labels)
    I = np.repeat(ii, L)
    J = np.repeat(jj, L)
    Y = np.tile(np.array(labels, float), npairs)
    H = None if hh is None else np.repeat(hh, L)
    pid = np.repeat(np.arange(npairs), L)
    # map original types into the table
    pair_index = {}
    for p_, (a, b) in enumerate(zip(ii, jj)):
        pair_index[(a, b)] = p_
    lab_index = {lab: k for k, lab in enumerate(labels)}
    n0 = np.zeros(len(I))
    for a, b, y, n in zip(d.i, d.j, d.y, d.n):
        t = pair_index[(int(a), int(b))] * L + lab_index[float(y)]
        n0[t] += n
    base = CompData(I, J, Y, n0.copy(), list(d.names), H, dict(d.meta))
    lab_type = {(int(p_), float(y)): int(t) for t, (p_, y) in enumerate(zip(pid, Y))}
    return Table(base=base, n0=n0, pair_id=pid, lab_type=lab_type, X=base.design())


class Searcher:
    def __init__(self, d: CompData, lam=1e-2, allow_tie_labels=None):
        labels = (0.0, 0.5, 1.0) if np.any(d.y == 0.5) else (0.0, 1.0)
        self.labels = labels
        self.tab = full_table(d, labels)
        self.lam = lam
        self.T = len(self.tab.n0)
        self.L = len(labels)
        # index of the "partner" decisive labels for flips/adds
        self.t_y0 = np.array([self.tab.lab_type[(int(p), 0.0)] for p in self.tab.pair_id])
        self.t_y1 = np.array([self.tab.lab_type[(int(p), 1.0)] for p in self.tab.pair_id])
        self.fit0 = self.fit(self.tab.n0)

    # -------------------------------------------------------------------------------
    def fit(self, n, theta0=None):
        d = self.tab.base
        d2 = CompData(d.i, d.j, d.y, n, d.names, d.home)
        return fit_bt(d2, lam=self.lam, theta0=theta0, X=self.tab.X)

    def gap(self, fit, hi, lo):
        return fit.theta[hi] - fit.theta[lo]

    # -------------------------------------------------------------------------------
    def action_scores(self, fit, hi, lo, family, removed, added):
        """First-order change of (theta_hi - theta_lo) per unit of each candidate action.

        Returns (delta, src, dst): arrays over candidate actions; src = type losing a unit
        (or -1), dst = type gaining a unit (or -1).
        """
        tab = self.tab
        c = np.zeros(len(fit.theta))
        c[hi] += 1
        c[lo] -= 1
        u = fit.Hinv @ c
        z = tab.X @ u                       # x_t^T H^-1 c
        y = tab.base.y
        p = fit.p
        avail = tab.n0 - removed           # original units still unmodified
        if family == "drop":
            delta = (p - y) * z
            ok = avail > 0.5
            src = np.arange(self.T)
            delta = np.where(ok, delta, np.inf)
            return delta, src, np.full(self.T, -1)
        if family == "flip":
            # flip to label 0 or 1 (whichever reduces the gap more)
            d0 = (0.0 - y) * z
            d1 = (1.0 - y) * z
            use0 = d0 <= d1
            delta = np.where(use0, d0, d1)
            dst = np.where(use0, self.t_y0, self.t_y1)
            same = dst == np.arange(self.T)
            ok = (avail > 0.5) & ~same
            delta = np.where(ok, delta, np.inf)
            return delta, np.arange(self.T), dst
        if family == "add":
            # adding a unit with label y': delta = -(p - y') z ; only decisive labels
            dec = (y == 0.0) | (y == 1.0)
            delta = np.where(dec, -(p - y) * z, np.inf)
            return delta, np.full(self.T, -1), np.arange(self.T)
        raise ValueError(family)

    def _apply(self, n, removed, added, src, dst, m):
        n = n.copy(); removed = removed.copy(); added = added.copy()
        if src >= 0:
            n[src] -= m; removed[src] += m
        if dst >= 0:
            n[dst] += m; added[dst] += m
        return n, removed, added

    # -------------------------------------------------------------------------------
    def greedy(self, hi, lo, family, step_frac=0.5, max_cost=None, max_iter=5000):
        """Greedy refit search. Returns dict(cost, success, refits, actions)."""
        N = self.tab.n0.sum()
        if max_cost is None:
            max_cost = N if family != "add" else 10 * N
        n = self.tab.n0.copy()
        removed = np.zeros(self.T)
        added = np.zeros(self.T)
        fit = self.fit0
        g = self.gap(fit, hi, lo)
        cost = 0
        refits = 0
        actions = []
        if g <= 0:
            return dict(cost=0, success=True, refits=0, actions=[])
        for _ in range(max_iter):
            delta, srcs, dsts = self.action_scores(fit, hi, lo, family, removed, added)
            b = int(np.argmin(delta))
            db = delta[b]
            if not np.isfinite(db) or db >= 0:
                return dict(cost=cost, success=False, refits=refits, actions=actions,
                            reason="no improving action")
            est = g / (-db)
            m = max(1, int(np.floor(step_frac * est)))
            src, dst = int(srcs[b]), int(dsts[b])
            if src >= 0:
                m = int(min(m, self.tab.n0[src] - removed[src]))
            m = int(min(m, max_cost - cost)) if max_cost - cost >= 1 else 0
            if m < 1:
                return dict(cost=cost, success=False, refits=refits, actions=actions,
                            reason="budget")
            n2, r2, a2 = self._apply(n, removed, added, src, dst, m)
            fit2 = self.fit(n2, theta0=fit.theta)
            refits += 1
            g2 = self.gap(fit2, hi, lo)
            if g2 < 0:
                # bisect smallest m' in [1, m] achieving reversal
                lo_m, hi_m = 0, m
                best_fit = fit2
                while hi_m - lo_m > 1:
                    mid = (lo_m + hi_m) // 2
                    n3, _, _ = self._apply(n, removed, added, src, dst, mid)
                    f3 = self.fit(n3, theta0=fit.theta)
                    refits += 1
                    if self.gap(f3, hi, lo) < 0:
                        hi_m, best_fit = mid, f3
                    else:
                        lo_m = mid
                actions.append((src, dst, hi_m))
                return dict(cost=cost + hi_m, success=True, refits=refits, actions=actions,
                            final_gap=float(self.gap(best_fit, hi, lo)))
            n, removed, added, fit, g = n2, r2, a2, fit2, g2
            cost += m
            actions.append((src, dst, m))
        return dict(cost=cost, success=False, refits=refits, actions=actions, reason="iters")

    # -------------------------------------------------------------------------------
    def amip(self, hi, lo, family):
        """One-shot first-order ordering at the original fit, verified by refits.

        Returns dict(pred, cost, success): pred = first-order predicted count,
        cost = smallest verified count along the one-shot ordering (upper bound).
        """
        fit = self.fit0
        g0 = self.gap(fit, hi, lo)
        if g0 <= 0:
            return dict(pred=0, cost=0, success=True, refits=0)
        zero = np.zeros(self.T)
        delta, srcs, dsts = self.action_scores(fit, hi, lo, family, zero, zero)
        order = np.argsort(delta)
        order = order[np.isfinite(delta[order]) & (delta[order] < 0)]
        if len(order) == 0:
            return dict(pred=np.inf, cost=np.inf, success=False, refits=0)
        if family == "add":
            # unlimited copies of the single best addition
            caps = np.array([np.inf])
            order = order[:1]
        else:
            caps = self.tab.n0[srcs[order]]
        dl = delta[order]
        cumcap = np.cumsum(caps)
        cumeff = np.cumsum(caps * dl) if family != "add" else None

        def first_order_count():
            if family == "add":
                return int(np.ceil(g0 / -dl[0]))
            k = np.searchsorted(-cumeff, g0)   # first index where cumulative >= g0
            if k >= len(order):
                return np.inf
            prev_cap = cumcap[k - 1] if k > 0 else 0
            prev_eff = cumeff[k - 1] if k > 0 else 0
            need = int(np.ceil((g0 + prev_eff) / -dl[k]))
            return int(prev_cap + need)

        pred = first_order_count()
        total = np.inf if family == "add" else int(cumcap[-1])
        refits = 0

        def counts_for(k):
            n = self.tab.n0.copy()
            if family == "add":
                n[dsts[order[0]]] += k
                return n
            full = np.searchsorted(cumcap, k, side="right")
            take = np.zeros(len(order))
            take[:full] = caps[:full]
            if full < len(order):
                take[full] = k - (cumcap[full - 1] if full > 0 else 0)
            for t_, m_ in zip(order, take):
                if m_ <= 0:
                    continue
                s_, d_ = srcs[t_], dsts[t_]
                if s_ >= 0:
                    n[s_] -= m_
                if d_ >= 0:
                    n[d_] += m_
            return n

        def flips(k):
            nonlocal refits
            refits += 1
            return self.gap(self.fit(counts_for(k), theta0=fit.theta), hi, lo) < 0

        start = int(max(1, pred if np.isfinite(pred) else 1))
        cap_total = total if np.isfinite(total) else 100 * self.tab.n0.sum()
        start = int(min(start, cap_total))
        if flips(start):
            lo_k, hi_k = 0, start
        else:
            lo_k, k = start, start
            while True:
                k = int(min(2 * k, cap_total))
                if flips(k):
                    hi_k = k
                    break
                lo_k = k
                if k >= cap_total:
                    return dict(pred=pred, cost=np.inf, success=False, refits=refits)
        while hi_k - lo_k > 1:
            mid = (lo_k + hi_k) // 2
            if flips(mid):
                hi_k = mid
            else:
                lo_k = mid
        return dict(pred=pred, cost=hi_k, success=True, refits=refits)

    # -------------------------------------------------------------------------------
    def leverage(self, hi, lo):
        """Pair diagnostics: gap, model SE, z, per-unit max drop influence, n_eff."""
        fit = self.fit0
        c = np.zeros(len(fit.theta)); c[hi] += 1; c[lo] -= 1
        se = float(np.sqrt(c @ fit.Hinv @ c))
        g = float(self.gap(fit, hi, lo))
        zero = np.zeros(self.T)
        out = dict(gap=g, se=se, z=g / se)
        for fam in FAMILIES:
            delta, _, _ = self.action_scores(fit, hi, lo, fam, zero, zero)
            lmax = float(-np.min(delta))
            out[f"lev_{fam}"] = lmax
            out[f"klin_{fam}"] = g / lmax if lmax > 0 else np.inf
        out["neff_drop"] = (se / out["lev_drop"]) ** 2
        return out

    # -------------------------------------------------------------------------------
    def exhaustive_drop_k1(self, hi, lo):
        """Exact check: does deleting any single comparison reverse (hi, lo)?"""
        for t in np.where(self.tab.n0 > 0)[0]:
            n = self.tab.n0.copy(); n[t] -= 1
            if self.gap(self.fit(n, theta0=self.fit0.theta), hi, lo) < 0:
                return True
        return False


def ranking(theta, K):
    return np.argsort(-theta[:K], kind="stable")
