"""Post-processing of the tidy result files into summary tables (no new fits). Usage: 06_summaries.py
Writes results/summary_decisions.csv, summary_b50.csv, summary_fragility_vs_gap.csv, summary_groups.csv"""
import numpy as np, pandas as pd, os, glob
R = os.path.dirname(os.path.abspath(__file__)) + "/../results/"; rng = np.random.default_rng(6)
DS = ["arena55k", "mtbench_human", "mtbench_gpt4", "nba"]
adj = {d: pd.read_csv(R + f"adjacent_pairs_{d}.csv") for d in DS if os.path.exists(R + f"adjacent_pairs_{d}.csv")}

# ---- 1. decisions: original budget, bootstrap spread, normalisations, benign-noise probability at the adversarial budget
rows = []
for d in DS:
    f = R + f"decisions_{d}.csv"
    if not os.path.exists(f): continue
    x = pd.read_csv(f); a = adj[d]; N = int(x.N.iloc[0])
    cnt = pd.concat([a.set_index("a").n_a, a.set_index("b").n_b]).groupby(level=0).first()
    ben = pd.read_csv(R + f"benign_{d}.csv")
    for (dec, meth, pt), g in x[x.method.isin(["influence_exact", "influence_exact_greedy"])].groupby(["decision", "method", "perturbation_type"]):
        o = g[g.replicate == -1]; b = g[g.replicate >= 0].budget_k.dropna()
        if o.empty: continue
        k = o.budget_k.iloc[0]; pair = str(o.pair.iloc[0]); mi = np.nan
        if ">" in pair and k == k:
            u, v = pair.split(">"); mi = k / (cnt.get(u, np.nan) + cnt.get(v, np.nan))   # approx.: ignores head-to-head overlap
        bm = {"drop": "random_drop", "flip": "random_flip"}.get(pt.replace("add_a_wins", "drop").replace("add_b_loses", "drop"))
        met = {"top1": "p_top1", "topk3": "p_topk3", "topk5": "p_topk5", "topk10": "p_topk10", "tau0.95": "p_tau<0.95", "tau0.9": "p_tau<0.9"}[dec]
        bb = ben[(ben.perturbation_type == bm) & (ben.metric == met) & (ben.budget_k >= k)].sort_values("budget_k") if k == k else pd.DataFrame()
        rows.append(dict(dataset=d, eval_design=o.eval_design.iloc[0], decision=dec, perturbation_type=pt, N=N, k=k, k_frac=k / N, k_over_participant_comps=mi,
                         boot_n=len(b), boot_median_frac=b.median() / N if len(b) else np.nan, boot_lo_frac=b.quantile(.025) / N if len(b) else np.nan,
                         boot_hi_frac=b.quantile(.975) / N if len(b) else np.nan, boot_frac_not_found=float(g[g.replicate >= 0].budget_k.isna().mean()),
                         benign_p_upper_at_k=bb.value.iloc[0] if len(bb) else np.nan, benign_grid_k=bb.budget_k.iloc[0] if len(bb) else np.nan))
pd.DataFrame(rows).to_csv(R + "summary_decisions.csv", index=False)

# ---- 2. b50: subsample fraction at which P(decision changes vs full data) = 0.5 (log-linear interpolation; CI from the Wilson bands)
def cross(f, v, q):
    """f where the curve v(f) (decreasing in f, up to noise) falls through q (log-linear interpolation). Returns (value, flag):
    flag 'below_grid' if v < q already at the smallest f, 'above_grid' if v >= q at the largest f."""
    f, v = np.asarray(f), np.asarray(v)
    if v[0] < q: return np.nan, "below_grid"
    for i in range(len(f) - 1):
        if v[i] >= q > v[i + 1]:
            t = (q - v[i]) / (v[i + 1] - v[i]); return float(np.exp(np.log(f[i]) + t * (np.log(f[i + 1]) - np.log(f[i])))), "ok"
    return np.nan, "above_grid"
# For a pairwise-order decision the chance level is 0.5 and is approached only as f -> 0, so b50 is generally not reached; we therefore report
# b_q for q in {0.1, 0.25, 0.5} (b50 is meaningful for top-1, whose chance level is (p-1)/p).
rows = []
for fn in sorted(glob.glob(R + "subsample_*.csv")):
    x = pd.read_csv(fn)
    for (d, dec), g in x.groupby(["dataset", "decision"]):
        g = g.sort_values("subsample_frac")
        for q in (0.1, 0.25, 0.5):
            b, fl = cross(g.subsample_frac, g.value, q); lo, _ = cross(g.subsample_frac, g.ci_lo, q); hi, _ = cross(g.subsample_frac, g.ci_hi, q)
            rows.append(dict(dataset=d, eval_design=g.eval_design.iloc[0], decision=dec, q=q, N=g.N.iloc[0], p=g.p.iloc[0], b_frac=b, b_n=b * g.N.iloc[0], flag=fl,
                             b_lo_frac=lo, b_hi_frac=hi, p_change_at_min_frac=g.value.iloc[0], p_change_at_max_frac=g.value.iloc[-1], min_frac=g.subsample_frac.iloc[0], max_frac=g.subsample_frac.iloc[-1]))
b50 = pd.DataFrame(rows); b50.to_csv(R + "summary_b50.csv", index=False)

# ---- 3. fragility vs gap (adjacent pairs): rank correlation and log-log slope of k_flip on z
from scipy.stats import spearmanr
rows = []
for d, a in adj.items():
    for m in ("drop", "flip"):
        g = a[(a["k_" + m].notna()) & (a.z > 0)]
        sl = np.polyfit(np.log(g.z), np.log(g["k_" + m].clip(lower=1)), 1) if len(g) > 3 else [np.nan, np.nan]
        rows.append(dict(dataset=d, perturbation_type=m, n_pairs=len(g), spearman_k_z=spearmanr(g.z, g["k_" + m]).statistic, loglog_slope=sl[0], loglog_intercept=sl[1],
                         median_k=g["k_" + m].median(), median_k_frac=(g["k_" + m] / g.N).median(), frac_pairs_k_le_10=(g["k_" + m] <= 10).mean(),
                         frac_pairs_z_lt_2=(g.z < 2).mean(), approx_vs_exact_median_ratio=(a["k1_" + m] / a["k_" + m]).median()))
pd.DataFrame(rows).to_csv(R + "summary_fragility_vs_gap.csv", index=False)

# ---- 4. groups for the design/size contrasts: bootstrap CI (over replicates) of median budget fraction
def boot_ci(v, B=2000):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    if len(v) == 0: return (np.nan, np.nan, np.nan)
    m = [np.median(rng.choice(v, len(v))) for _ in range(B)]; return np.median(v), np.percentile(m, 2.5), np.percentile(m, 97.5)
rows = []
def add(group, g, cols):
    for c in cols:
        med, lo, hi = boot_ci(g[c]); rows.append(dict(group=group, metric=c, n_rep=len(g), median=med, ci_lo=lo, ci_hi=hi, median_frac=boot_ci(g[c] / g.N)[0], frac_lo=boot_ci(g[c] / g.N)[1], frac_hi=boot_ci(g[c] / g.N)[2]))
if os.path.exists(R + "nba_seasons.csv"):
    s = pd.read_csv(R + "nba_seasons.csv"); add("nba_seasons", s, ["top1_drop", "top1_flip", "top1_add_a_wins", "adjmin_drop", "adjmin_flip"])
    rows.append(dict(group="nba_seasons", metric="median_z_top", n_rep=len(s), median=s.z_top.median()))
for fn, key in ((R + "commonN.csv", ["dataset", "control"]), (R + "arena_controls.csv", ["control", "N"])):
    if os.path.exists(fn):
        x = pd.read_csv(fn)
        for k, g in x.groupby(key): add("|".join(map(str, k)), g, ["top1_drop", "top1_flip", "top1_add_a_wins", "adjmin_drop", "adjmin_flip"])
if os.path.exists(R + "mtbench_contrast.csv"):
    x = pd.read_csv(R + "mtbench_contrast.csv")
    for k, g in x.groupby("source"): add("mtbench_contrast|" + k, g, ["top1_drop", "top1_flip", "adjmin_drop", "adjmin_flip"])
pd.DataFrame(rows).to_csv(R + "summary_groups.csv", index=False)
print("ok")

# ---- 5. SYNTHETIC calibration (RQ4): log-log regression of the top-1 flip budget on the gap in SE units, N, p, tie-free sigma
if os.path.exists(R + "synthetic.csv"):
    s = pd.read_csv(R + "synthetic.csv"); rows = []
    for y in ("top1_drop", "top1_flip", "adjmin_drop", "adjmin_flip"):
        g = s[s[y].notna() & (s.z_top > 0)].copy()
        if len(g) < 20: continue
        g["ly"] = np.log(g[y].clip(lower=1)); X = np.column_stack([np.ones(len(g)), np.log(g.z_top), np.log(g.N), np.log(g.p), g.sigma])
        beta, *_ = np.linalg.lstsq(X, g.ly, rcond=None); res = g.ly - X @ beta
        bs = [np.linalg.lstsq(X[i], g.ly.values[i], rcond=None)[0] for i in (rng.integers(0, len(g), len(g)) for _ in range(500))]
        lo, hi = np.percentile(bs, 2.5, 0), np.percentile(bs, 97.5, 0)
        for j, nm in enumerate(["intercept", "log_z", "log_N", "log_p", "sigma"]):
            rows.append(dict(response=y, term=nm, coef=beta[j], ci_lo=lo[j], ci_hi=hi[j], n=len(g), r2=1 - res.var() / g.ly.var()))
    pd.DataFrame(rows).to_csv(R + "summary_synthetic_regression.csv", index=False)
    s.groupby(["p", "N", "sigma"]).agg(n_rep=("replicate", "size"), z_top=("z_top", "median"), top1_flip_med=("top1_flip", "median"), top1_drop_med=("top1_drop", "median"),
                                       adjmin_flip_med=("adjmin_flip", "median"), top1_correct=("top1_correct", "mean"), tau_true=("tau_true", "mean")).reset_index().to_csv(R + "summary_synthetic_cells.csv", index=False)
