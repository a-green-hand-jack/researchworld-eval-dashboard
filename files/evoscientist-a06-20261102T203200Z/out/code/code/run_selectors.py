"""Optimism under different search procedures (real matrices): full-evaluation argmax vs successive halving
vs sequential hill-climbing-like 'adaptive best-so-far' search (evaluates configs one by one on growing subsets).
Reported score = winner's mean on ALL n selection questions (as practitioners do). Truth = held-out mean.
python run_selectors.py api MODEL OUT.csv R
"""
import sys, numpy as np, pandas as pd
import sel_lib as sl, data_mats as dm


def sh_select(Ssel, rng):
    Kc, n = Ssel.shape
    alive = np.arange(Kc); rounds = max(1, int(np.ceil(np.log2(Kc))))
    per = n // rounds; used = 0
    for r in range(rounds):
        if len(alive) == 1: break
        blk = Ssel[alive][:, used:used + per] if r < rounds - 1 else Ssel[alive][:, used:]
        sc = blk.mean(1) + 1e-9 * rng.random(len(alive))
        keep = max(1, int(np.ceil(len(alive) / 2)))
        alive = alive[np.argsort(-sc)[:keep]]; used += per
    return int(alive[0])


def racing_select(Ssel, rng):
    """sequential: keep incumbent; challenger replaces it if its mean on the first n/2 questions beats incumbent's by >0 (greedy search)."""
    Kc, n = Ssel.shape
    h = n // 2
    inc = 0
    for c in range(1, Kc):
        if Ssel[c, :h].mean() > Ssel[inc, :h].mean(): inc = c
    return inc


def main():
    model, out, R = sys.argv[2], sys.argv[3], int(sys.argv[4])
    S, _, _ = dm.api_matrix(model); S = S[:, ~np.isnan(S).any(0)]
    K, N = S.shape; rng = np.random.default_rng(2024); rows = []
    for n in [50, 100, 200, 400]:
        for Kc in [4, 8, 16, 32]:
            if Kc > K: continue
            acc = {s: [] for s in ["argmax", "sh", "greedy"]}
            for r in range(R):
                cfg = rng.choice(K, Kc, replace=False); perm = rng.permutation(N); si, hi = perm[:n], perm[n:]
                Ssel = S[np.ix_(cfg, si)]; Sh = S[np.ix_(cfg, hi)]
                for name, f in [("argmax", lambda A, g: int(sl.argmax_tb(A.mean(1), g))), ("sh", sh_select), ("greedy", racing_select)]:
                    k = f(Ssel, rng)
                    acc[name].append((Ssel[k].mean(), Sh[k].mean(), Sh.mean()))
            for name, v in acc.items():
                v = np.array(v)
                rows.append(dict(n=n, K=Kc, selector=name, naive=v[:, 0].mean(), truth=v[:, 1].mean(), mean_cfg=v[:, 2].mean(),
                                 optimism=(v[:, 0] - v[:, 1]).mean(), optimism_se=(v[:, 0] - v[:, 1]).std() / np.sqrt(len(v)),
                                 gain_over_random=(v[:, 1] - v[:, 2]).mean()))
    pd.DataFrame(rows).to_csv(out, index=False); print("ok")


main()
