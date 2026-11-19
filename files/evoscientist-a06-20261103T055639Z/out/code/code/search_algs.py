"""Search algorithms (operate on the n x 72 matrix of per-question 0/1 scores of ALL configs on the search set; they only
'touch' (evaluate) the columns they visit, so the matrix is just a lookup table) and replay-bootstrap reporting."""
import numpy as np
from configs import N_I, N_F, N_D, CONFIGS
from selinf import argmax_rand, wilson, maxT, conditional, naive, holdout, boot_optimism, ladder, METHODS

IDX = {cfg: i for i, cfg in enumerate(CONFIGS)}
NC = len(CONFIGS)


def alg_grid(S, rng, K=None):
    m = S.mean(0); return argmax_rand(m, rng), np.arange(NC), False  # (selected, reachable/visited cols, adaptive?)


def alg_random(S, rng, K):
    cols = rng.choice(NC, K, replace=False)
    m = S[:, cols].mean(0); return int(cols[argmax_rand(m, rng)]), cols, False


def alg_coord(S, rng, K=None):
    """Coordinate ascent over the 3 factors (instruction, format, demo set), random start, <=3 sweeps. Adaptive."""
    m = S.mean(0)
    cur = [int(rng.randint(N_I)), int(rng.randint(N_F)), int(rng.randint(N_D))]
    sizes = [N_I, N_F, N_D]
    for _ in range(3):
        changed = False
        for f in rng.permutation(3):
            cands = []
            for lv in range(sizes[f]):
                t = list(cur); t[f] = lv; cands.append(IDX[tuple(t)])
            best = cands[argmax_rand(m[cands], rng)]
            if CONFIGS[best][f] != cur[f]:
                cur[f] = CONFIGS[best][f]; changed = True
        if not changed: break
    return IDX[tuple(cur)], np.arange(NC), True


def alg_sh(S, rng, K=None):
    """Successive halving over all 72 configs using disjoint question slices per rung (best-arm-identification flavour).
    Survivors halve each rung; final winner scored (as is common) on the entire search set by the caller."""
    n = S.shape[0]; arms = np.arange(NC); rungs = 4
    perm = rng.permutation(n); chunks = np.array_split(perm, rungs)
    stat = np.zeros(NC); cnt = 0
    for r in range(rungs):
        stat[arms] += S[np.ix_(chunks[r], arms)].sum(0); cnt += len(chunks[r])
        if r < rungs - 1:
            keep = max(len(arms) // 2, 1)
            order = np.argsort(-stat[arms] + 1e-9 * rng.rand(len(arms)))
            arms = arms[order[:keep]]
    return int(arms[argmax_rand(stat[arms], rng)]), np.arange(NC), True


ALGS = {"grid": alg_grid, "random": alg_random, "coord": alg_coord, "sh": alg_sh}


def replay_boot(alg, K, S, rng, alpha=0.1, B=100):
    """Replay the *entire search algorithm* on bootstrap resamples (any algorithm, adaptive or not)
    and subtract the average optimism  mean_b(c_b) - mean_orig(c_b)  from the naive score."""
    n = S.shape[0]; m = S.mean(0)
    sel, _, _ = alg(S, rng, K)
    opt = np.empty(B)
    for b in range(B):
        ix = rng.randint(0, n, n)
        Sb = S[ix]; cb, _, _ = alg(Sb, rng, K)
        opt[b] = Sb[:, cb].mean() - m[cb]
    est = m[sel] - opt.mean()
    se = np.sqrt(max(m[sel] * (1 - m[sel]), 1e-4) / n)
    dev = opt - opt.mean(); tot = dev + rng.randn(B) * se
    return est, est + np.quantile(-tot, alpha / 2), est + np.quantile(-tot, 1 - alpha / 2), sel
