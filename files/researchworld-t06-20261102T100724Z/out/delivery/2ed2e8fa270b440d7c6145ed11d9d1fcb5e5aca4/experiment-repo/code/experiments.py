"""Claim-level worst-case (P1-P3) and random (B1) / resampling (B2) analyses -> tidy rows."""
import numpy as np
from btlib import Board, min_edits_to_flip, wald_se, sig

PERT = {"P1": (("remove",), False), "P2": (("flip",), False), "P3": (("inject",), True)}
NCAND = 8      # C1: challengers considered = the NCAND best-ranked others
MAXADJ = 10    # C2/C4: adjacent pairs among the top MAXADJ ranks (ranks 1..MAXADJ -> pairs (r, r+1))
ZCRIT = 1.959964


def local_n(board, ids):
    m = np.isin(board.i, ids) | np.isin(board.j, ids)
    return float((board.W + board.L + board.T)[m].sum())


def mask_for(board, b):
    return (board.i == b) | (board.j == b)


def pair_search(board, beta, a, b, pert, claim, kcap):
    fams, targeted = PERT[pert]
    mask = mask_for(board, b) if targeted else None
    return min_edits_to_flip(board, a, b, fams, cell_mask=mask, beta0=beta, claim=claim, max_edits=kcap)


def claim_rows(board, beta, perts=("P1", "P2", "P3"), claims=("C1", "C2", "C4", "C3"), kcap_frac=0.25,
               topks=(3, 5, 10)):
    """Rows of k* for every (claim, perturbation) for one fitted board."""
    P = board.P
    order = np.argsort(-beta[:P])
    N = board.N
    tie = float(board.T.sum() / N)
    kcap = int(kcap_frac * N)
    rows = []

    def base(claim, cid, pert, res, ids, gap, se):
        return dict(claim=claim, claim_id=cid, pert=pert, k_star=res["k"], found=res["k"] is not None,
                    k_max=kcap, k_lin=res.get("k_lin"), N=N, N_local=local_n(board, ids), n_part=P,
                    gap=gap, se=se, z=gap / se if se > 0 else np.nan, tie_rate=tie)

    def gse(a, b):
        c = np.zeros(board.d); c[a], c[b] = 1, -1
        return beta[a] - beta[b], wald_se(board, beta, c)

    for pert in perts:
        if "C2" in claims or "C4" in claims:
            for r in range(min(MAXADJ, P - 1)):
                a, b = order[r], order[r + 1]
                gap, se = gse(a, b)
                if "C2" in claims:
                    rows.append(base("C2", r + 1, pert, pair_search(board, beta, a, b, pert, "order", kcap), [a, b], gap, se))
                if "C4" in claims and gap / se > ZCRIT:
                    rows.append(base("C4", r + 1, pert, pair_search(board, beta, a, b, pert, "sig", kcap), [a, b], gap, se))
        if "C1" in claims:
            best, barg = None, None
            for b in order[1: 1 + NCAND]:
                res = pair_search(board, beta, order[0], b, pert, "order", kcap if best is None else min(kcap, best))
                if res["k"] is not None and (best is None or res["k"] < best):
                    best, barg, bres = res["k"], b, res
            if best is None:
                bres, barg = dict(k=None, k_lin=None), order[1]
            gap, se = gse(order[0], barg)
            rows.append(base("C1", 0, pert, bres, [order[0], barg], gap, se))
        if "C3" in claims:
            for K in topks:
                if K >= P:
                    continue
                best, barg, bres = None, None, dict(k=None, k_lin=None)
                for a in order[max(0, K - 4): K]:
                    for b in order[K: K + 4]:
                        res = pair_search(board, beta, a, b, pert, "order", kcap if best is None else min(kcap, best))
                        if res["k"] is not None and (best is None or res["k"] < best):
                            best, barg, bres = res["k"], (a, b), res
                ids = list(barg) if barg else [order[K - 1], order[K]]
                gap, se = gse(*ids)
                rows.append(base("C3", K, pert, bres, ids, gap, se))
    return rows


# ------------------------------------------------------------------ B1 random baselines
def _counts(board):
    return np.concatenate([board.W, board.L, board.T]).astype(np.int64)


def _board_from_counts(board, cnt):
    m = board.n_cells
    return Board(board.P, board.i, board.j, cnt[:m], cnt[m:2 * m], cnt[2 * m:], board.home, board.names)


def random_perturb(board, cnt0, k, kind, rng):
    m = board.n_cells
    if kind == "remove":
        d = rng.multivariate_hypergeometric(cnt0, k)
        return cnt0 - d
    cnt = cnt0.copy()
    d = rng.multivariate_hypergeometric(cnt0, k)       # which votes get relabelled
    dW, dL, dT = d[:m], d[m:2 * m], d[2 * m:]
    toW = rng.binomial(dT, 0.5)                          # ties relabelled to a random decisive outcome
    cnt[:m] += dL - dW + toW
    cnt[m:2 * m] += dW - dL + (dT - toW)
    cnt[2 * m:] -= dT
    return cnt


def claim_state(board, beta):
    """What the claims say at a fit: top-1 id, order of the first MAXADJ adjacent pairs, C4 status."""
    P = board.P
    order = np.argsort(-beta[:P])
    top = int(order[0])
    return top, order


def random_curve(board, beta0, ks, n_rep, kind, rng):
    """P(claim changes) for random removal/flip of k comparisons; claims defined by the unperturbed fit."""
    P = board.P
    order0 = np.argsort(-beta0[:P])
    pairs = [(order0[r], order0[r + 1]) for r in range(min(MAXADJ, P - 1))]
    sigmask = []
    for a, b in pairs:
        c = np.zeros(board.d); c[a], c[b] = 1, -1
        sigmask.append((beta0[a] - beta0[b]) / wald_se(board, beta0, c) > ZCRIT)
    cnt0 = _counts(board)
    rows = []
    for k in ks:
        ch = np.zeros((n_rep, 1 + 2 * len(pairs)), bool)
        for rep in range(n_rep):
            bd = _board_from_counts(board, random_perturb(board, cnt0, int(k), kind, rng))
            bt = bd.fit(beta0)
            ch[rep, 0] = np.argmax(bt[:P]) != order0[0]
            for q, (a, b) in enumerate(pairs):
                ch[rep, 1 + q] = bt[a] <= bt[b]
                if sigmask[q]:
                    c = np.zeros(board.d); c[a], c[b] = 1, -1
                    ch[rep, 1 + len(pairs) + q] = (bt[a] - bt[b]) / wald_se(bd, bt, c) <= ZCRIT
        rows.append(dict(claim="C1", claim_id=0, k=int(k), n_rep=n_rep, n_changed=int(ch[:, 0].sum()), kind=kind))
        for q in range(len(pairs)):
            rows.append(dict(claim="C2", claim_id=q + 1, k=int(k), n_rep=n_rep, n_changed=int(ch[:, 1 + q].sum()), kind=kind))
            if sigmask[q]:
                rows.append(dict(claim="C4", claim_id=q + 1, k=int(k), n_rep=n_rep,
                                 n_changed=int(ch[:, 1 + len(pairs) + q].sum()), kind=kind))
    return rows


# ------------------------------------------------------------------ B2 resampling noise
def resample_curve(board, beta0, B, rng, frac=1.0):
    """Bootstrap (frac=1, with replacement) or subsample (frac<1, without replacement) flip rates."""
    P = board.P
    order0 = np.argsort(-beta0[:P])
    cnt0 = _counts(board)
    N = int(cnt0.sum())
    pairs = [(order0[r], order0[r + 1]) for r in range(min(MAXADJ, P - 1))]
    ch = np.zeros((B, 1 + len(pairs)), bool)
    gaps = np.zeros((B, len(pairs)))
    for rep in range(B):
        if frac == 1.0:
            cnt = rng.multinomial(N, cnt0 / N)
        else:
            cnt = rng.multivariate_hypergeometric(cnt0, int(frac * N))
        bt = _board_from_counts(board, cnt).fit(beta0)
        ch[rep, 0] = np.argmax(bt[:P]) != order0[0]
        for q, (a, b) in enumerate(pairs):
            ch[rep, 1 + q] = bt[a] <= bt[b]
            gaps[rep, q] = bt[a] - bt[b]
    rows = [dict(claim="C1", claim_id=0, n_rep=B, n_changed=int(ch[:, 0].sum()), frac=frac, gap_se_boot=np.nan)]
    for q in range(len(pairs)):
        rows.append(dict(claim="C2", claim_id=q + 1, n_rep=B, n_changed=int(ch[:, 1 + q].sum()), frac=frac,
                         gap_se_boot=float(gaps[:, q].std(ddof=1)) * (np.sqrt(frac / (1 - frac)) if frac < 1 else 1.0)))
    return rows
