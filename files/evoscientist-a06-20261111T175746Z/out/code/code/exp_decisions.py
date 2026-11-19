"""E4/E5: do selection effects change conclusions drawn from reported scores?

E4a  improvement claims vs a fixed baseline prompt (baseline = rank-r config by true accuracy, excluded from search)
E4b  comparing two systems with unequal tuning budgets (K_A vs K_B random disjoint config subsets)
E5   selecting on one subject group (STEM) and deploying on another (non-STEM)

python code/exp_decisions.py --tag Qwen2.5-0.5B-Instruct_fp32 --out results/dec_05B.json
"""
import argparse, json, math, sys
import numpy as np
sys.path.insert(0, "code")
import sel
from common import load_matrix, pmap, to_py

ap = argparse.ArgumentParser()
ap.add_argument("--tag", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--R", type=int, default=1000); ap.add_argument("--nproc", type=int, default=3)
ap.add_argument("--ns", default="100,200,400,800"); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--nmax", type=int, default=0)
a = ap.parse_args()
Y, meta = load_matrix(a.tag, a.nmax or None)
Ktot, N = Y.shape
mu = Y.mean(1)
order = np.argsort(-mu)
ns = [int(x) for x in a.ns.split(",")]
cats = np.array(meta["category"])
STEM = {"math", "physics", "chemistry", "biology", "engineering", "computer science"}
is_stem = np.array([c in STEM for c in cats])
print(a.tag, "K", Ktot, "N", N, "STEM share", is_stem.mean(), flush=True)
Z1 = sel.Z95_1


def paired_t(D):
    n = D.shape[-1]
    return D.mean(-1) / (D.std(-1, ddof=1) / math.sqrt(n) + 1e-12)


def claims_job(args):
    """Improvement claim: 'tuned beats baseline' declared when one-sided paired test (5%) rejects.
    Methods: naive (same S for selection and test), split (select on half, test on other half),
    maxt (simultaneous over all searched configs, so the test is valid after selection)."""
    base_rank, K, n, R, seed = args
    rng = np.random.default_rng(seed)
    b = order[base_rank]
    rest = np.array([i for i in range(Ktot) if i != b])
    res = dict(naive_claim=[], split_claim=[], maxt_claim=[], true_impr=[], rep_impr=[], split_true_impr=[])
    for _ in range(R):
        idx = rng.choice(rest, K, replace=False)
        S = rng.integers(0, N, n)
        Ys = Y[idx][:, S]; yb = Y[b, S]
        k = sel.opt_exh(Ys, rng)
        D = Ys - yb[None, :]
        # naive
        res["naive_claim"].append(float(paired_t(D[k]) > Z1))
        res["rep_impr"].append(D[k].mean()); res["true_impr"].append(mu[idx[k]] - mu[b])
        # split
        n1 = n // 2
        k1 = sel.opt_exh(Ys[:, :n1], rng)
        res["split_claim"].append(float(paired_t(D[k1, n1:]) > Z1)); res["split_true_impr"].append(mu[idx[k1]] - mu[b])
        # max-T over searched configs (paired differences vs baseline)
        W = sel.boot_counts(rng, n, 200)
        Dm = D @ W / n                       # (K,B)
        dh = D.mean(1); sd = D.std(1, ddof=1) / math.sqrt(n) + 1e-9
        T = ((Dm - dh[:, None]) / sd[:, None]).max(0)
        c = np.quantile(T, 0.95)
        res["maxt_claim"].append(float(dh[k] / sd[k] > c))
    return dict(base_rank=base_rank, K=K, n=n, R=R, **{k: np.array(v) for k, v in res.items()})


def systems_job(args):
    """Two 'systems' tuned on the same benchmark: A searches K_A configs, B searches K_B (disjoint random subsets)."""
    KA, KB, n, R, seed = args
    rng = np.random.default_rng(seed)
    out = dict(rep_gap=[], true_gap=[], naive_claim=[], split_claim=[], split_true_gap=[], rep_gap_split=[])
    for _ in range(R):
        perm = rng.permutation(Ktot)
        A, Bc = perm[:KA], perm[KA:KA + KB]
        S = rng.integers(0, N, n)
        YA, YB = Y[A][:, S], Y[Bc][:, S]
        kA, kB = sel.opt_exh(YA, rng), sel.opt_exh(YB, rng)
        D = YA[kA] - YB[kB]
        out["rep_gap"].append(D.mean()); out["true_gap"].append(mu[A[kA]] - mu[Bc[kB]])
        out["naive_claim"].append(float(paired_t(D) > Z1))      # claims A better than B
        n1 = n // 2
        k1A, k1B = sel.opt_exh(YA[:, :n1], rng), sel.opt_exh(YB[:, :n1], rng)
        D2 = YA[k1A, n1:] - YB[k1B, n1:]
        out["split_claim"].append(float(paired_t(D2) > Z1)); out["split_true_gap"].append(mu[A[k1A]] - mu[Bc[k1B]])
        out["rep_gap_split"].append(D2.mean())
    return dict(KA=KA, KB=KB, n=n, R=R, **{k: np.array(v) for k, v in out.items()})


def shift_job(args):
    """Selection set drawn only from STEM questions; truth on STEM (in-distribution) and non-STEM (deployment)."""
    K, n, R, seed = args
    rng = np.random.default_rng(seed)
    ids_in = np.where(is_stem)[0]
    mu_in = Y[:, is_stem].mean(1); mu_out = Y[:, ~is_stem].mean(1)
    rows = dict(naive=[], t_in=[], t_out=[], best_out=[], mean_out=[])
    for _ in range(R):
        idx = rng.choice(Ktot, K, replace=False) if K < Ktot else np.arange(Ktot)
        S = rng.choice(ids_in, n)
        Ys = Y[idx][:, S]
        k = sel.opt_exh(Ys, rng)
        rows["naive"].append(Ys[k].mean()); rows["t_in"].append(mu_in[idx[k]]); rows["t_out"].append(mu_out[idx[k]])
        rows["best_out"].append(mu_out[idx].max()); rows["mean_out"].append(mu_out[idx].mean())
    r = {k: np.array(v) for k, v in rows.items()}
    se = lambda x: float(x.std(ddof=1) / math.sqrt(len(x)))
    return dict(K=K, n=n, R=R, naive=float(r["naive"].mean()), t_in=float(r["t_in"].mean()), t_out=float(r["t_out"].mean()),
                best_out=float(r["best_out"].mean()), mean_out=float(r["mean_out"].mean()),
                curse=float((r["naive"] - r["t_in"]).mean()), curse_se=se(r["naive"] - r["t_in"]),
                shift=float((r["t_in"] - r["t_out"]).mean()), shift_se=se(r["t_in"] - r["t_out"]),
                total_gap=float((r["naive"] - r["t_out"]).mean()), total_gap_se=se(r["naive"] - r["t_out"]),
                regret_out=float((r["best_out"] - r["t_out"]).mean()))


def summ_claims(r):
    ti = r["true_impr"]
    false_ = ti <= 0
    d = dict(base_rank=r["base_rank"], K=r["K"], n=r["n"], R=r["R"], mu_base=None,
             mean_rep_impr=float(r["rep_impr"].mean()), mean_true_impr=float(ti.mean()), frac_true_impr_le0=float(false_.mean()))
    for m in ("naive", "split", "maxt"):
        c = r[m + "_claim"]
        tt = r["split_true_impr"] if m == "split" else ti
        d[m + "_claim_rate"] = float(c.mean())
        d[m + "_false_claim_rate"] = float((c * (tt <= 0)).mean())            # P(claim and truly not better)
        d[m + "_claim_given_not_better"] = float(c[tt <= 0].mean()) if (tt <= 0).any() else None
        d[m + "_claim_given_better"] = float(c[tt > 0].mean()) if (tt > 0).any() else None
    return d


def summ_sys(r):
    tg = r["true_gap"]
    d = dict(KA=r["KA"], KB=r["KB"], n=r["n"], R=r["R"], mean_rep_gap=float(r["rep_gap"].mean()), mean_true_gap=float(tg.mean()),
             rep_gap_se=float(r["rep_gap"].std(ddof=1) / math.sqrt(r["R"])),
             p_rep_A_better=float((r["rep_gap"] > 0).mean()), p_true_A_better=float((tg > 0).mean()),
             naive_claim_rate=float(r["naive_claim"].mean()),
             naive_claim_given_A_not_better=float(r["naive_claim"][tg <= 0].mean()) if (tg <= 0).any() else None,
             split_claim_given_A_not_better=float(r["split_claim"][r["split_true_gap"] <= 0].mean()) if (r["split_true_gap"] <= 0).any() else None,
             split_claim_rate=float(r["split_claim"].mean()), mean_true_gap_split=float(r["split_true_gap"].mean()),
             sign_error_naive=float(((r["rep_gap"] > 0) != (tg > 0)).mean()),
             sign_error_split=float(((r["rep_gap_split"] > 0) != (r["split_true_gap"] > 0)).mean()))
    return d


if __name__ == "__main__":
    out = dict(tag=a.tag, K=Ktot, N=N)
    jobs = [(rk, K, n, a.R, a.seed + 100 * rk + K * 7 + n) for rk in (0, 3) for K in (4, 16, min(31, Ktot - 1)) if K < Ktot - 0 for n in ns]
    out["claims"] = [summ_claims(r) for r in pmap(claims_job, jobs, a.nproc)]
    out["mu_base"] = {int(rk): float(mu[order[rk]]) for rk in (0, 3)}
    jobs = [(KA, KB, n, a.R, a.seed + 5 + KA * 3 + n) for (KA, KB) in ((16, 2), (8, 2), (2, 2)) if KA + KB <= Ktot for n in ns]
    out["systems"] = [summ_sys(r) for r in pmap(systems_job, jobs, a.nproc)]
    jobs = [(K, n, a.R, a.seed + 11 + K + n) for K in (4, 16, Ktot) for n in (100, 200, 400)]
    out["shift"] = pmap(shift_job, jobs, a.nproc)
    json.dump(to_py(out), open(a.out, "w"))
    print("saved", a.out)
