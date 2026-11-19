"""Merge shards and aggregate: summary_gap, summary_methods, decisions, theory_curve.
usage: aggregate.py TIER(T0|T1) [MODEL]  -> results/{runs,methods}_<tier>.parquet and results/summary_*_<tier>.csv"""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import lib, t0
from scipy import stats
R = "/hutian/repo/results"

def wilson_ci(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d

def load(tier, model=None):
    d = f"{R}/{tier.lower()}"; pat = f"{d}/{model}.shard*" if model else f"{d}/shard*"
    extra = f"{R}/{tier.lower()}leak/shard*" if not model else None  # leakage cells are run as a separate job
    pats = [pat] + ([extra] if extra else [])
    runs = pd.concat([pd.read_parquet(f) for p in pats for f in sorted(glob.glob(p + ".runs.parquet"))], ignore_index=True)
    meth = pd.concat([pd.read_parquet(f) for p in pats for f in sorted(glob.glob(p + ".methods.parquet"))], ignore_index=True)
    runs = runs.drop_duplicates(["cell_id", "rep"], ignore_index=True)   # leakage cells are in the main grid and in the separate job (same seeds)
    meth = meth.drop_duplicates(["cell_id", "rep", "method"], ignore_index=True)
    meth["leakage"] = meth.cell_id.str.contains("leak=1", regex=False).astype(int)
    return runs, meth

def summarise(runs, meth):
    runs = runs.copy(); runs["gap"] = runs.reported_naive - runs.theta
    keys = ["tier", "cell_id", "n", "K", "tau", "rho", "base_acc", "procedure"]
    g = runs.groupby(keys, dropna=False)
    gap = g.agg(reps=("gap", "size"), gap_mean=("gap", "mean"), gap_sd=("gap", "std"), gap_q05=("gap", lambda x: x.quantile(.05)),
                gap_q50=("gap", "median"), gap_q95=("gap", lambda x: x.quantile(.95)), reported_mean=("reported_naive", "mean"), theta_mean=("theta", "mean"),
                theta_pop_mean=("theta_pop_mean", "mean"), theta_best_mean=("theta_best", "mean"), K_eval_mean=("K_eval", "mean"),
                gain_vs_base_mean=("tuned_untuned_fresh_gain", "mean")).reset_index()
    gap["gap_mcse"] = gap.gap_sd / np.sqrt(gap.reps)
    m = meth.copy(); m["err"] = m.estimate - m.theta_target; m["has_ci"] = np.isfinite(m.lo) | np.isfinite(m.hi)
    m["cover"] = (m.lo <= m.theta_target) & (m.theta_target <= m.hi); m["width"] = m.hi - m.lo
    m["err_chat"] = m.estimate - m.theta_chat
    rows = []
    for k, d in m.groupby(keys + ["method"], dropna=False):
        e = d.err.dropna(); r = dict(zip(keys + ["method"], k)); r.update(reps=len(d), bias=e.mean(), bias_mcse=e.std() / np.sqrt(len(e)) if len(e) > 1 else np.nan,
                                                                  rmse=float(np.sqrt((e ** 2).mean())), bias_vs_final_chat=d.err_chat.mean(),
                                                                  items_search=d.items_search.mean(), items_report=d.items_report.mean(), frac_estimate_missing=d.estimate.isna().mean())
        if d.has_ci.any():
            dd = d[d.lo.notna() | d.hi.notna()]; c = dd.cover.sum(); nn = len(dd); lo, hi = wilson_ci(c, nn)
            w = dd.width.replace([np.inf, -np.inf], np.nan)
            r.update(coverage=c / nn, cov_lo=lo, cov_hi=hi, width_median=w.median(), frac_infinite_width=float(np.isinf(dd.width).mean()))
        rows.append(r)
    return gap, pd.DataFrame(rows)

def theory(gap):
    out = []
    for _, r in gap[(gap.procedure == "exhaustive") & gap.tau.notna() & ~gap.cell_id.str.contains("leak=1", regex=False)].iterrows():
        a = stats.norm.ppf(r.base_acc); th = r.base_acc; sig = np.sqrt(th * (1 - th)); rb = t0.binary_corr(a, r.rho)
        # tau on probit scale -> probability scale slope at the base: phi(a); config effects are N(0, tau^2) mixed additive+idiosyncratic (variance tau^2)
        tp = r.tau * stats.norm.pdf(a)
        out.append(dict(cell_id=r.cell_id, n=r.n, K=r.K, tau=r.tau, rho=r.rho, base_acc=r.base_acc, sigma=sig, r_binary=rb, tau_prob=tp,
                        gap_theory=lib.theory_gap(r.n, r.K, sig, rb, tp), gap_measured=r.gap_mean, gap_mcse=r.gap_mcse))
    return pd.DataFrame(out)

def decisions(meth, runs):
    """tuned-vs-baseline rule: claim 'tuned beats baseline by > m' from the method's estimate (point) or lower bound (lo)."""
    rows = []
    m = meth[meth.method.str.startswith(("M0", "M1", "M2", "M3", "M4", "M5"))].copy()
    m["gain_true"] = m.theta_target - m.theta_base
    for marg in (0.0, 0.02):
        reg = np.where(m.gain_true <= 0, "gain<=0", np.where(m.gain_true < marg, "0<gain<m", "gain>=m")) if marg > 0 else np.where(m.gain_true <= 0, "gain<=0", "gain>0")
        m["regime"] = reg
        m["claim_point"] = (m.estimate - m.base_est) > marg
        m["claim_lo"] = (m.lo - m.base_est) > marg
        for var in ("point", "lo"):
            sub = m if var == "point" else m[m.lo.notna()]
            g = sub.groupby(["tier", "cell_id", "n", "K", "tau", "procedure", "method", "regime"], dropna=False).agg(n_reps=("rep", "size"), n_reject=(f"claim_{var}", "sum")).reset_index()
            g["rule"] = "tuned_gt_baseline_by_m"; g["variant"] = var; g["margin_m"] = marg; rows.append(g)
    return pd.concat(rows, ignore_index=True)

def ab_decisions(meth, pairs):
    """A vs B: two independent systems (cells A,B), replicate i of A paired with replicate i of B. Claim 'A better than B by > m'."""
    rows = []
    for ca, cb in pairs:
        a = meth[meth.cell_id == ca].set_index(["rep", "method"]); b = meth[meth.cell_id == cb].set_index(["rep", "method"])
        j = a.join(b, lsuffix="_A", rsuffix="_B", how="inner").reset_index()
        j["gain_true"] = j.theta_chat_A - j.theta_chat_B
        for marg in (0.0, 0.02):
            j["regime"] = np.where(j.gain_true <= 0, "A_not_better", np.where(j.gain_true < marg, "0<gain<m", "gain>=m")) if marg > 0 else np.where(j.gain_true <= 0, "A_not_better", "A_better")
            j["claim_point"] = (j.estimate_A - j.estimate_B) > marg
            j["claim_lo"] = (j.lo_A - j.hi_B) > marg
            for var in ("point", "lo"):
                s = j if var == "point" else j[j.lo_A.notna() & j.hi_B.notna()]
                g = s.groupby(["method", "regime"]).agg(n_reps=("rep", "size"), n_reject=(f"claim_{var}", "sum")).reset_index()
                g["cell_A"], g["cell_B"], g["rule"], g["variant"], g["margin_m"] = ca, cb, "A_gt_B", var, marg; rows.append(g)
    return pd.concat(rows, ignore_index=True)

if __name__ == "__main__":
    tier = sys.argv[1]; model = sys.argv[2] if len(sys.argv) > 2 else None
    runs, meth = load(tier, model); suf = tier.lower() + (f"_{model}" if model else "")
    if tier == "T1": raise SystemExit("use t1_summary.py for T1")
    runs.to_parquet(f"{R}/runs_{suf}.parquet"); meth.to_parquet(f"{R}/methods_{suf}.parquet")
    gap, ms = summarise(runs, meth); gap.to_csv(f"{R}/summary_gap_{suf}.csv", index=False); ms.to_csv(f"{R}/summary_methods_{suf}.csv", index=False)
    dec = decisions(meth, runs); dec.to_csv(f"{R}/decisions_{suf}.csv", index=False)
    if tier == "T0":
        theory(gap).to_csv(f"{R}/theory_curve_t0.csv", index=False)
        P = lambda n1, K1, n2, K2, tau: (f"n={n1}|K={K1}|tau={tau}|rho=0.6|acc=0.3|proc=exhaustive", f"n={n2}|K={K2}|tau={tau}|rho=0.6|acc=0.3|proc=exhaustive")
        pairs = [P(n, KA, n, KB, tau) for n in (200, 500) for (KA, KB) in ((200, 5), (50, 5), (200, 20)) for tau in (0.0, 0.05, 0.1)] + [P(50, 20, 500, 20, tau) for tau in (0.0, 0.1)] + [P(50, 50, 500, 50, tau) for tau in (0.0, 0.1)]
        ab = ab_decisions(meth, pairs); ab.to_csv(f"{R}/decisions_ab_{suf}.csv", index=False)
    print(gap.shape, ms.shape, dec.shape)
