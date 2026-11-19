"""Claims, random perturbations, bootstrap and adversarial flip budgets on a `Unit` (one leaderboard)."""
from __future__ import annotations

import numpy as np

from . import core
from .core import Counts


class Unit:
    """A leaderboard: fitted participants + the subset `elig` (indices) that claims are made about.

    `window` (optional): claims concern the top-`window` ranks of the base fit (C2 adjacent pairs, C4 tau and the sizes k of
    C3 are limited to them), but the challengers of C1 and C3 are all of `elig` (so a runner-up outside the window cannot be missed)."""

    def __init__(self, name, design, counts: Counts, elig=None, lam=1.0, lam_h=1.0, meta=None, window=None):
        self.name, self.design, self.c = name, design, counts
        self.lam, self.lam_h = lam, lam_h
        self.elig = np.arange(counts.K) if elig is None else np.asarray(elig)
        self.meta = meta or {}
        self.x0 = core.fit(counts, lam, lam_h)
        th = self.x0[: counts.K][self.elig]
        self.order = self.elig[np.argsort(-th, kind="stable")]  # eligible participants, best first
        self.E = len(self.elig)
        self.W = self.E if window is None else min(int(window), self.E)
        self.window = window
        self.ks = [k for k in (3, 5, 10) if k <= self.W - 2]

    # --- claim bookkeeping -----------------------------------------------------------------------
    def claim_outcomes(self, theta):
        """Return dict of arrays describing the claims under parameter theta (length K)."""
        t = theta[self.order]  # scores of eligible participants in *base* rank order
        out = {"c1": bool(np.argmax(t) == 0)}
        W = self.W
        out["c2"] = t[: W - 1] > t[1:W]  # adjacent pair order preserved (pair r, r+1), r < W-1
        for k in self.ks:
            top = np.argpartition(-t, k - 1)[:k]
            out[f"c3_{k}"] = bool(np.all(top < k))
        # Kendall tau with base order (base scores are decreasing in this indexing)
        iu = np.triu_indices(W, 1)
        diff = t[iu[0]] - t[iu[1]]
        out["tau"] = float((np.sum(diff > 0) - np.sum(diff < 0)) / len(diff))
        return out

    def base_gap(self, a, b):
        return float(self.x0[a] - self.x0[b])


# ---------------------------------------------------------------------------------------------
# perturbation samplers on the count tensor


def sample_bootstrap(c: Counts, rng):
    n = c.n.ravel()
    return rng.multinomial(int(n.sum()), n / n.sum()).astype(float).reshape(-1, 3)


def sample_remove(c: Counts, m, rng):
    n = c.n.ravel().astype(np.int64)
    rem = rng.multivariate_hypergeometric(n, int(m))
    return (n - rem).astype(float).reshape(-1, 3)


def sample_flip(c: Counts, f, rng, has_ties):
    """Each comparison is, with probability f, relabelled uniformly to one of the other outcomes."""
    n = c.n.astype(np.int64)
    out = n.copy()
    for o in range(3):
        if o == 1 and not has_ties:
            continue
        moved = rng.binomial(n[:, o], f)
        out[:, o] -= moved
        others = [q for q in range(3) if q != o and (has_ties or q != 1)]
        if len(others) == 1:
            out[:, others[0]] += moved
        else:
            to_first = rng.binomial(moved, 0.5)
            out[:, others[0]] += to_first
            out[:, others[1]] += moved - to_first
    return out.astype(float)


def run_random(unit: Unit, kind, fracs, seeds, has_ties, base_seed=0):
    """Survival of each claim under random perturbation. Returns list of dict rows (aggregated over seeds)."""
    c = unit.c
    N = c.N
    rows = []
    for fi, f in enumerate(fracs):
        acc = {"c1": [], "tau": []}
        c2 = []
        c3 = {k: [] for k in unit.ks}
        for s in range(seeds):
            rng = np.random.default_rng([base_seed, fi, s])
            if kind == "remove":
                n2 = sample_remove(c, round(f * N), rng)
            elif kind == "flip":
                n2 = sample_flip(c, f, rng, has_ties)
            elif kind == "bootstrap":
                n2 = sample_bootstrap(c, rng)
            else:
                raise ValueError(kind)
            x = core.fit(c.with_n(n2), unit.lam, unit.lam_h, theta0=unit.x0)
            o = unit.claim_outcomes(x[: c.K])
            acc["c1"].append(o["c1"]); acc["tau"].append(o["tau"]); c2.append(o["c2"])
            for k in unit.ks:
                c3[k].append(o[f"c3_{k}"])
            if kind == "bootstrap":
                pass
        c2 = np.array(c2)
        row = dict(unit=unit.name, kind=kind, frac=f, m=round(f * N) if kind == "remove" else np.nan, seeds=seeds,
                   c1_survive=float(np.mean(acc["c1"])), tau_mean=float(np.mean(acc["tau"])),
                   tau_p05=float(np.percentile(acc["tau"], 5)), c2_survive_mean=float(c2.mean()),
                   c2_survive_min=float(c2.mean(0).min()), c2_survive_each=";".join(f"{v:.4f}" for v in c2.mean(0)))
        for k in unit.ks:
            row[f"c3_{k}_survive"] = float(np.mean(c3[k]))
        rows.append(row)
    return rows


def bootstrap_fits(unit: Unit, B, seed=0):
    """B bootstrap fits; returns (B, K) score matrix (natural-log BT scale)."""
    c = unit.c
    out = np.empty((B, c.K))
    for b in range(B):
        rng = np.random.default_rng([seed, 10_000 + b])
        n2 = sample_bootstrap(c, rng)
        out[b] = core.fit(c.with_n(n2), unit.lam, unit.lam_h, theta0=unit.x0)[: c.K]
    return out


# ---------------------------------------------------------------------------------------------
# flip budgets


def claim_pairs(unit: Unit, window=None):
    """Claim -> list of (a, b) candidate pairs (a ranked above b in the base fit) whose reversal flips the claim."""
    o = unit.order
    E = unit.E
    pairs = {"c1": [(o[0], o[b]) for b in range(1, E)]}
    for r in range(unit.W - 1):
        pairs[f"c2_{r}"] = [(o[r], o[r + 1])]
    for k in unit.ks:
        w = E if window is None else window
        pairs[f"c3_{k}"] = [(o[i], o[j]) for i in range(max(0, k - w), k) for j in range(k, min(E, k + w))]
    return pairs


def all_pairs(unit: Unit, members=None):
    """Every unordered pair of `members` (default eligible set) as one claim 'pair_<a>|<b>' oriented by the base fit (a above b)."""
    mem = list(unit.elig if members is None else members)
    out = {}
    for x in range(len(mem)):
        for y in range(x + 1, len(mem)):
            a, b = (mem[x], mem[y]) if unit.x0[mem[x]] >= unit.x0[mem[y]] else (mem[y], mem[x])
            out[f"pair_{unit.c.names[a]}|{unit.c.names[b]}"] = [(a, b)]
    return out


def budgets(unit: Unit, mode="remove", strategy="greedy", window=None, c1_challengers=None, pairs=None, prune=None, **kw):
    """Flip budget per claim: min over the candidate pairs of the verified search. Returns list of rows.
    `pairs` replaces the standard claim set (C1-C3) by an explicit claim -> candidate pairs mapping.
    `prune` (a factor, default None = search every candidate pair): candidate pairs are searched in increasing order of their
    linearised estimate and a pair is skipped once its estimate exceeds `prune` x the best verified budget of the claim so far."""
    c = unit.c
    pairs = claim_pairs(unit, window) if pairs is None else pairs
    cache = {}
    rows = []
    for claim, plist in pairs.items():
        if claim == "c1" and c1_challengers is not None:
            plist = plist[:c1_challengers]
        best = None
        ests = {}
        if prune is not None and len(plist) > 1:
            for (a, b) in plist:
                if (a, b) not in cache:
                    ests[(a, b)] = core.adversarial_flip(c, a, b, unit.lam, mode="remove" if mode == "relabel" else mode, x0=unit.x0, lam_h=unit.lam_h,
                                                         est_only=True, **{k: v for k, v in kw.items() if k in ("frac", "small", "max_units")})["est"]
            plist = sorted(plist, key=lambda p: ests.get(p, 0.0))
        for (a, b) in plist:
            if prune is not None and best is not None and best[0][0] is False and ests.get((a, b), 0.0) > prune * best[0][1]:
                continue
            if (a, b) not in cache and mode == "relabel":
                cache[(a, b)] = core.relabel_flip(c, a, b, unit.lam, unit.lam_h, x0=unit.x0)
                cache[(a, b)]["est"], cache[(a, b)]["steps"] = np.nan, 0
            elif (a, b) not in cache:
                cache[(a, b)] = core.adversarial_flip(c, a, b, unit.lam, mode=mode, strategy=strategy, x0=unit.x0,
                                                      lam_h=unit.lam_h, **kw)
            r = cache[(a, b)]
            key = (not r["flipped"], r["k"])
            if best is None or key < best[0]:
                best = (key, (a, b), r)
        _, (a, b), r = best
        rows.append(dict(unit=unit.name, claim=claim, mode=mode, strategy=strategy, a=unit.c.names[a], b=unit.c.names[b],
                         gap=unit.base_gap(a, b), budget=r["k"] if r["flipped"] else np.nan, flipped=r["flipped"],
                         lin_est=r["est"], steps=r["steps"]))
    return rows
