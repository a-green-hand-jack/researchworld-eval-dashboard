"""Aggregate raw result files into the tables the paper uses (results/tab_*.csv).
Bands are initial ranks under the *mean* rule.  inf (infeasible) counts are kept
separate so that medians are over feasible targets and the infeasible share is
reported next to them."""
import glob, os
from common import *
RES = f"{ROOT}/results"
BANDS = [0, 1, 2, 5, 20, 100, 1000, 10**6]
LAB = ["1", "2", "3-5", "6-20", "21-100", "101-1000", ">1000"]
RULE_ORDER = R.RULES

def band(x): return pd.cut(x, BANDS, labels=LAB)

def summarize_mink(name):
    d = pd.read_csv(f"{RES}/mink_{name}.csv")
    d["band"] = band(d.rank_mean); d["frac"] = d.k / d.n_tasks
    d["feasible"] = np.isfinite(d.k)
    g = d.groupby(["cap", "delta", "rule", "band"], observed=True)
    t = g.agg(n_targets=("k", "size"), feasible_share=("feasible", "mean"),
              k_median=("k", lambda s: s[np.isfinite(s)].median() if np.isfinite(s).any() else np.nan),
              k_q25=("k", lambda s: s[np.isfinite(s)].quantile(.25) if np.isfinite(s).any() else np.nan),
              k_q75=("k", lambda s: s[np.isfinite(s)].quantile(.75) if np.isfinite(s).any() else np.nan),
              frac_median=("frac", lambda s: s[np.isfinite(s)].median() if np.isfinite(s).any() else np.nan)).reset_index()
    t.to_csv(f"{RES}/tab_mink_{name}.csv", index=False)
    return d

def mean_formula_check(board_name, S, d):
    """k*_mean vs ceil(n*gap/delta) (no-headroom formula)."""
    n = S.shape[1]; mean = S.mean(1)
    rows = []
    for t in d.idx.unique():
        c = np.delete(mean, t).max(); gap = max(c - mean[t], 0)
        for dl in [2, 5, 10, 20, 40, 100]:
            k = d[(d.idx == t) & (d.rule == "mean") & (d.cap == "ceiling") & (d.delta == dl)].k.iloc[0]
            pred = int(np.floor(n * gap / dl)) + 1 if gap > 0 else 0   # strict >
            rows.append((board_name, t, dl, k, pred))
    r = pd.DataFrame(rows, columns=["board", "idx", "delta", "k", "k_formula"])
    r["exact"] = r.k == r.k_formula; r["formula_le_k"] = r.k_formula <= r.k
    r.groupby(["board", "delta"]).agg(share_equal=("exact", "mean"), formula_is_lower_bound=("formula_le_k", "mean")).reset_index().to_csv(f"{RES}/tab_mean_formula_{board_name}.csv", index=False)

def rank_agreement():
    rows = []
    from scipy.stats import kendalltau
    for board in ["helm", "olb"]:
        S = load_helm().values if board == "helm" else load_olb("main")[1]
        sc = {r: R.scores(S, r) for r in R.RULES}
        for a in R.RULES:
            for b in R.RULES:
                if a < b:
                    rows.append((board, a, b, kendalltau(sc[a], sc[b])[0]))
        top = {r: int(np.argmax(sc[r])) for r in R.RULES}
        for r in R.RULES: rows.append((board, r, "WINNER_IDX", top[r]))
    pd.DataFrame(rows, columns=["board", "rule_a", "rule_b", "value"]).to_csv(f"{RES}/tab_rule_agreement.csv", index=False)

def noise(board):
    f = f"{RES}/noise_{board}.csv"
    if not os.path.exists(f): return
    d = pd.read_csv(f)
    d["feas"] = np.isfinite(d.k)
    g = d.groupby(["model", "rank_obs_mean", "rule", "delta"])
    t = g.agg(k_obs_median=("k", lambda s: s[np.isfinite(s)].median() if np.isfinite(s).any() else np.nan),
              k_q05=("k", lambda s: s[np.isfinite(s)].quantile(.05) if np.isfinite(s).any() else np.nan),
              k_q95=("k", lambda s: s[np.isfinite(s)].quantile(.95) if np.isfinite(s).any() else np.nan),
              feasible_share=("feas", "mean"), rank_draw_q05=("rank_draw", lambda s: s.quantile(.05)),
              rank_draw_q95=("rank_draw", lambda s: s.quantile(.95)), p_first_without_attack=("k", lambda s: (s == 0).mean())).reset_index()
    t.to_csv(f"{RES}/tab_noise_{board}.csv", index=False)

if __name__ == "__main__":
    for f in sorted(glob.glob(f"{RES}/mink_*.csv")):
        name = os.path.basename(f)[5:-4]
        d = summarize_mink(name)
        if name in ("helm_main", "olb_main"):
            S = load_helm().values if name.startswith("helm") else load_olb("main")[1]
            mean_formula_check(name.split("_")[0], S, d)
    rank_agreement(); noise("helm"); noise("olb")
    # frontier summary: median total points to first, by rule and band
    for f in sorted(glob.glob(f"{RES}/frontier_*.csv")):
        d = pd.read_csv(f); d["band"] = band(d.rank_mean)
        tot = d.groupby(["model", "rank_mean", "rule", "cap"]).total_points.min().reset_index()  # best k
        tot["band"] = band(tot.rank_mean)
        tot.groupby(["cap", "rule", "band"], observed=True).total_points.agg(["size", lambda s: np.isfinite(s).mean(), lambda s: s[np.isfinite(s)].median()]).rename(columns=lambda c: {"<lambda_0>": "feasible_share", "<lambda_1>": "total_points_median"}.get(c, c)).reset_index().to_csv(f.replace("frontier_", "tab_frontier_total_"), index=False)
    print("ok")
