"""(a) exact_check: greedy k* vs exhaustive minimum on small real instances (3 participants, ~40 votes, no ties);
(b) approx_check: linear (one-shot influence) prediction vs exact refit as a function of the edit budget.
-> results/exact_check.csv, results/approx_check.csv"""
import sys, os, itertools
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import *
from btlib import *
from experiments import PERT, mask_for
import provenance as pv

SEED = 20261105
KMAX = 14


def compositions(k, d):
    if d == 1:
        yield (k,)
        return
    for x in range(k + 1):
        for rest in compositions(k - x, d - 1):
            yield (x,) + rest


def brute_min(B, a, b, fam, mask):
    """Smallest k <= KMAX for which some allocation of k edits makes theta_a < theta_b; None if > KMAX."""
    types = []
    for c in range(B.n_cells):
        if mask is not None and not mask[c]:
            continue
        for (name, dw, dn, src) in EDITS[fam]:
            if name in ("rT", "T>W", "T>L", "W>T", "L>T", "iT"):
                continue
            avail = np.inf if src is None else getattr(B, src)[c]
            if avail >= 1:
                types.append((c, name, avail))
    for k in range(1, KMAX + 1):
        for comp in compositions(k, len(types)):
            if any(x > t[2] for x, t in zip(comp, types)):
                continue
            B2 = B.copy()
            apply_edits(B2, [(t[0], t[1], x) for x, t in zip(comp, types) if x])
            bt = B2.fit()
            if bt[a] - bt[b] < -EPS:
                return k
    return None


def small_instances(rng, n_inst):
    a, an = arena55k(); a = a[a.o != 0.5]
    mt, mn = mtbench("human"); mt = mt[mt.o != 0.5]
    nb = nba()
    out = []
    sources = []
    for kind in ("arena", "mtbench", "nba"):
        for _ in range(n_inst):
            if kind == "arena":
                top = pd.concat([a.a, a.b]).value_counts().index[:12]
                S = list(rng.choice(top, 3, replace=False))
                d = a[a.a.isin(S) & a.b.isin(S)]
                names = an
            elif kind == "mtbench":
                S = list(rng.choice(6, 3, replace=False))
                d = mt[mt.a.isin(S) & mt.b.isin(S)]
                names = mn
            else:
                y = int(rng.integers(1985, 2011))
                dd = nb[(nb.year_id >= y) & (nb.year_id < y + 5) & (nb._iscopy == 0) & (nb.is_playoffs == 0)]
                always = set.intersection(*[set(dd[dd.year_id == t].team_id) for t in range(y, y + 5)])
                teams = list(rng.choice(sorted(always), 3, replace=False))
                dd = dd[dd.team_id.isin(teams) & dd.opp_id.isin(teams)]
                if len(dd) < 6:
                    continue
                ix = {t: k for k, t in enumerate(teams)}
                d = pd.DataFrame(dict(a=dd.team_id.map(ix), b=dd.opp_id.map(ix), o=(dd.game_result == "W") * 1.0))
                S = [0, 1, 2]; names = teams
            if len(d) < 12:
                continue
            n = min(len(d), int(rng.integers(24, 45)))
            d = d.sample(n, random_state=int(rng.integers(1 << 30)))
            ix = {m: k for k, m in enumerate(S)} if kind != "nba" else {0: 0, 1: 1, 2: 2}
            B = board_from_records(d.a.map(ix).values, d.b.map(ix).values, d.o.values, 3, [str(s) for s in S])
            out.append((kind, B))
    return out


def exact_check():
    rng = np.random.default_rng(SEED)
    rows = []
    for kind, B in small_instances(rng, 30):
        beta = B.fit(); order = np.argsort(-beta); a, b = order[0], order[1]
        if beta[a] - beta[b] < 1e-6:
            continue
        for pert, (fam, targeted) in PERT.items():
            mask = mask_for(B, b) if targeted else None
            g = min_edits_to_flip(B, a, b, fam, cell_mask=mask, beta0=beta)
            ex = brute_min(B, a, b, fam[0], mask)
            rows.append(dict(source=kind, pert=pert, N=B.N, gap=beta[a] - beta[b], k_greedy=g["k"], k_exact=ex,
                             k_lin=g["k_lin"], exact_capped=ex is None))
    return pd.DataFrame(rows)


def oneshot_edits(B, beta, a, b, fam, m):
    c = np.zeros(B.d); c[a], c[b] = 1, -1
    inf = influence(B, beta, c, fam)
    names = [n for n, _, _ in inf]
    eff = np.stack([e for _, e, _ in inf]); av = np.stack([x for _, _, x in inf])
    order = np.argsort(eff.ravel())
    edits, pred, left = [], 0.0, m
    for idx in order:
        t, cell = divmod(idx, eff.shape[1])
        if eff[t, cell] >= 0 or left <= 0:
            break
        k = int(min(left, av[t, cell] if np.isfinite(av[t, cell]) else left))
        if k < 1:
            continue
        edits.append((cell, names[t], k)); pred += k * eff[t, cell]; left -= k
    return edits, pred


def approx_check():
    rows = []
    a_, an = arena55k(); mt, mn = mtbench("human"); nb = nba()
    boards = [("arena55k", arena_board(a_, an)), ("mtbench_human", mt_board(mt, mn)),
              ("nba_2015", nba_season_board(nb, 2015, True))]
    for label, B in boards:
        beta = B.fit(); order = np.argsort(-beta)
        for r in range(5):
            a, b = order[r], order[r + 1]
            k1 = min_edits_to_flip(B, a, b, ("remove",), beta0=beta)["k"]
            if not k1:
                continue
            for pert, (fam, targeted) in PERT.items():
                for frac in (0.1, 0.25, 0.5, 1.0, 2.0):
                    m = max(1, int(round(frac * k1)))
                    edits, pred = oneshot_edits(B, beta, a, b, fam, m)
                    B2 = B.copy(); apply_edits(B2, edits)
                    b2 = B2.fit(beta)
                    rows.append(dict(board=label, rank=r + 1, pert=pert, m_edits=m, frac_of_kstar_P1=frac,
                                     gap0=beta[a] - beta[b], pred_change=pred,
                                     actual_change=(b2[a] - b2[b]) - (beta[a] - beta[b])))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    src = [f"{DATA}/arena55k/train.csv", f"{DATA}/nba/nbaallelo.csv"] + sorted(
        f"{DATA}/mtbench/{f}" for f in os.listdir(f"{DATA}/mtbench"))
    pv.save(approx_check(), "approx_check.csv", "run_exact.py", SEED, src)
    pv.save(exact_check(), "exact_check.csv", "run_exact.py", SEED, src,
            note=f"exhaustive search capped at k<={KMAX}; exact_capped rows have no exact value")
