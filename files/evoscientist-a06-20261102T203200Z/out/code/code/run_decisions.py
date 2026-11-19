"""Downstream-decision experiments.

C1 (tuned vs fixed baseline): baseline = one fixed config b (each of the K configs in turn); the 'tuned system'
   = argmax over Kc other random configs on n selection questions.  Compare the *reported* gain
   (naive: m_khat - m_b;  corrected: estimator_khat - m_b) with the *true* gain (held-out).
   Decision 'claim improvement' if lower 95% bound of gain > 0.
C2 (tuned vs tuned, unequal search budgets): systems A (K_A configs) and B (K_B configs), disjoint random
   config sets from the same pool, both tuned on the SAME n questions; reported difference vs true difference.

python run_decisions.py <real api MODEL | real local MODEL | synth> OUT_PREFIX R
"""
import sys, os, numpy as np, pandas as pd, time
from multiprocessing import Pool
import sel_lib as sl
import data_mats as dm
from synth import PRESETS

G = {}


def tune_report(Ssel, rng, B=100):
    """returns dict of estimates for the winner, plus winner index"""
    out = sl.estimate(Ssel, rng, np.zeros(Ssel.shape[0]), np.zeros(Ssel.shape[0]), B=B)
    k = int(sl.argmax_tb(Ssel.mean(1), rng))  # same rule; recompute index (tie-break may differ -> consistent below)
    return out


def winner_and_est(Ssel, rng, B=100):
    m = Ssel.mean(1); k = int(sl.argmax_tb(m, rng))
    Kc, n = Ssel.shape
    est = {"naive": m[k]}
    # cross-fit
    if Kc > 1:
        folds = np.array_split(np.arange(n), 5); e = []
        for f in folds:
            tr = np.setdiff1d(np.arange(n), f)
            kk = int(sl.argmax_tb(Ssel[:, tr].mean(1), rng)); e.append(Ssel[kk, f].mean())
        est["cv"] = float(np.mean(e))
        W = rng.multinomial(n, np.ones(n) / n, size=B).T.astype(np.float64)
        mb = Ssel @ W / n; kb = sl.argmax_tb(mb.T, rng)
        est["boot"] = m[k] - (mb[kb, np.arange(B)] - m[kb]).mean()
    else:
        est["cv"] = m[k]; est["boot"] = m[k]
    est["eb"] = sl.eb_estimate(Ssel)[0][k] if Kc > 2 else m[k]
    # holdout-split winner
    nh = n // 2
    k2 = int(sl.argmax_tb(Ssel[:, : n - nh].mean(1), rng))
    est["hold"] = Ssel[k2, n - nh:].mean(); est["hold_k"] = k2
    return k, est


def c1_cell(args):
    n, Kc, seed, R = args
    rng = np.random.default_rng(seed)
    S = G["S"]; K, N = S.shape
    rows = []
    for r in range(R):
        b = int(rng.integers(K))
        others = np.setdiff1d(np.arange(K), [b])
        cand = rng.choice(others, Kc, replace=False)
        perm = rng.permutation(N); si, hi = perm[:n], perm[n:]
        Ssel = S[np.ix_(cand, si)]; Shold = S[np.ix_(cand, hi)]
        mb_sel = S[b, si].mean(); mb_hold = S[b, hi].mean()
        k, est = winner_and_est(Ssel, rng)
        h = Shold.mean(1)
        # paired CI for naive gain
        dpair = Ssel[k] - S[b, si]
        se = dpair.std(ddof=1) / np.sqrt(n)
        # simultaneous max-t over candidates for paired gains
        D = Ssel - S[b, si][None, :]
        mD = D.mean(1); sD = np.maximum(D.std(1, ddof=1) / np.sqrt(n), 1e-6)
        W = rng.multinomial(n, np.ones(n) / n, size=200).T.astype(np.float64)
        mbD = D @ W / n
        c = np.quantile((np.abs(mbD - mD[:, None]) / sD[:, None]).max(0), 0.95)
        # holdout: select on first half, gain on second half
        k2 = est["hold_k"]; nh = n // 2
        dh = Ssel[k2, n - nh:] - S[b, si][n - nh:]
        row = dict(true_gain=h[k] - mb_hold, true_gain_hold=h[k2] - mb_hold,
                   naive_gain=est["naive"] - mb_sel, cv_gain=est["cv"] - mb_sel, boot_gain=est["boot"] - mb_sel,
                   eb_gain=est["eb"] - mb_sel, hold_gain=dh.mean(),
                   naive_lb=mD[k] - 1.645 * sD[k], sim_lb=mD[k] - c * sD[k],
                   hold_lb=dh.mean() - 1.645 * dh.std(ddof=1) / np.sqrt(nh))
        rows.append(row)
    df = pd.DataFrame(rows)
    res = dict(n=n, K=Kc, R=R)
    for e in ["naive", "cv", "boot", "eb", "hold"]:
        tg = df["true_gain_hold"] if e == "hold" else df["true_gain"]
        res[f"{e}_gain_bias"] = (df[f"{e}_gain"] - tg).mean()
        res[f"{e}_sign_err"] = ((df[f"{e}_gain"] > 0) & (tg <= 0)).mean()  # reported gain >0 but true <= 0
        res[f"{e}_claim2"] = (df[f"{e}_gain"] > 0.02).mean()
        res[f"{e}_claim2_false"] = ((df[f"{e}_gain"] > 0.02) & (tg <= 0.02)).mean()
    for e, col in [("naive", "naive_lb"), ("sim", "sim_lb"), ("hold", "hold_lb")]:
        tg = df["true_gain_hold"] if e == "hold" else df["true_gain"]
        res[f"{e}_lb_claim"] = (df[col] > 0).mean()
        res[f"{e}_lb_false"] = ((df[col] > 0) & (tg <= 0)).mean()
        res[f"{e}_lb_prec"] = ((df[col] > 0) & (tg > 0)).sum() / max(1, (df[col] > 0).sum())
    res["true_gain_mean"] = df["true_gain"].mean(); res["P_true_gain_pos"] = (df["true_gain"] > 0).mean()
    return res


def c2_cell(args):
    n, KA, KB, seed, R = args
    rng = np.random.default_rng(seed)
    S = G["S"]; K, N = S.shape
    rows = []
    for r in range(R):
        perm_c = rng.permutation(K); ca, cb = perm_c[:KA], perm_c[KA:KA + KB]
        perm = rng.permutation(N); si, hi = perm[:n], perm[n:]
        kA, eA = winner_and_est(S[np.ix_(ca, si)], rng)
        kB, eB = winner_and_est(S[np.ix_(cb, si)], rng)
        hA = S[ca[kA], hi].mean(); hB = S[cb[kB], hi].mean()
        row = dict(true=hA - hB)
        for e in ["naive", "cv", "boot", "eb"]:
            row[e] = eA[e] - eB[e]
        # holdout: each system tuned on first half; both reported on second half
        kA2, kB2 = eA["hold_k"], eB["hold_k"]
        row["hold"] = eA["hold"] - eB["hold"]; row["true_hold"] = S[ca[kA2], hi].mean() - S[cb[kB2], hi].mean()
        rows.append(row)
    df = pd.DataFrame(rows)
    res = dict(n=n, KA=KA, KB=KB, R=R, true_diff_mean=df["true"].mean(), P_A_truly_better=(df["true"] > 0).mean())
    for e in ["naive", "cv", "boot", "eb", "hold"]:
        tg = df["true_hold"] if e == "hold" else df["true"]
        res[f"{e}_diff_bias"] = (df[e] - tg).mean()
        res[f"{e}_says_A_better"] = (df[e] > 0).mean()
        res[f"{e}_wrong_sign"] = (np.sign(df[e]) != np.sign(tg)).mean()
        res[f"{e}_falseA"] = ((df[e] > 0.01) & (tg <= 0)).mean()  # claims A better by >1pp while truly not better
    return res


def init(S):
    G["S"] = S


if __name__ == "__main__":
    kind = sys.argv[1]
    nproc = int(os.environ.get("NPROC", 6))
    if kind == "synth":
        # synthetic pool matrix with exact large N: one draw of a 200-config x 20000-question matrix per preset
        out, R = sys.argv[2], int(sys.argv[3])
        tag = os.environ.get("PRESET", "base_tau.1")
        m = PRESETS[tag]; rng = np.random.default_rng(7)
        b = m.draw_b(40, rng); S = m.sample(b, 6000, rng)
        name = f"synth-{tag}"
    else:
        model, out, R = sys.argv[2], sys.argv[3], int(sys.argv[4])
        S, _, _ = dm.api_matrix(model) if kind == "api" else dm.local_matrix(model)
        S = S[:, ~np.isnan(S).any(0)]; name = model
    K, N = S.shape
    ns = [n for n in [50, 100, 200, 400] if n <= N // 2]
    jobs1 = [(n, Kc, 777 + 31 * i + j, R) for i, n in enumerate(ns) for j, Kc in enumerate([1, 3, 10, 30]) if Kc <= K - 1]
    jobs2 = [(n, KA, KB, 999 + 17 * i + j, R) for i, n in enumerate(ns) for j, (KA, KB) in enumerate([(5, 5), (25, 5), (30, 2), (30, 10)]) if KA + KB <= K]
    t0 = time.time()
    with Pool(nproc, initializer=init, initargs=(S,)) as p:
        r1 = p.map(c1_cell, jobs1, chunksize=1)
        r2 = p.map(c2_cell, jobs2, chunksize=1)
    pd.DataFrame(r1).assign(setting=name).to_csv(out + "_c1.csv", index=False)
    pd.DataFrame(r2).assign(setting=name).to_csv(out + "_c2.csv", index=False)
    print("done", time.time() - t0, flush=True)
