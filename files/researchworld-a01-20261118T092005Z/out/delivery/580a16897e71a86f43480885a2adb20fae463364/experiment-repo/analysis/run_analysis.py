"""Analyses on the delivered tables: paired price ratios (Fig. 4), rule orderings, R1-R3 verdicts at the E1 grid (points). usage: run_analysis.py TABLES_DIR
reads TABLES_DIR/price.csv (make_results.py) and writes paired.csv, rule_order.csv, verdicts_e1.csv in TABLES_DIR."""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from stats import cluster_ci, cluster_mean_ci, kendall_tau
T = sys.argv[1]
p = pd.read_csv(f"{T}/price.csv")
RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]
MEANFAM, MEDTYPE = ["mean", "zmean"], ["median", "plurality", "copeland"]
NB = int(os.environ.get("NBOOT", 2000))
top = p[p.init_rank <= 30]                       # the top-30 target set under the official rule (E1 also ran all HELM models)


def wide(d, value, B, inc):
    x = d[(d.B == B) & (d.incumbent == inc)]
    return x.pivot_table(index=["board", "target", "model", "family"], columns="rule", values=value, aggfunc="first")


def paired_rows():
    rows = []
    for board, d in top.groupby("board"):
        for inc in ("own", "common"):
            for B in sorted(d.B.unique()):
                for metric, val in (("depth", "depth_star"), ("breadth", "k_star")):
                    W = wide(d, val, B, inc)
                    inc_id = d[(d.B == B) & (d.incumbent == inc)].pivot_table(index=["board", "target", "model", "family"], columns="rule", values="incumbent_id", aggfunc="first")
                    for a, b in itertools.combinations([r for r in RULES if r in W], 2):
                        x = W[[a, b]].replace([np.inf], np.nan)
                        both = x.dropna()
                        # strictly cheaper share over targets where at least one is positive; infeasible = infinitely expensive
                        full = W[[a, b]].fillna(np.inf)
                        keep = ~((full[a] == full[b]))
                        df = pd.DataFrame(dict(sa=(full[a] < full[b])[keep].astype(float), family=[i[3] for i in full[keep].index], incumbent_id=inc_id.loc[full[keep].index, a].values))
                        pos = both[(both[a] > 0) & (both[b] > 0)]
                        lr = pd.DataFrame(dict(lr=np.log(pos[a] / pos[b]).values, family=[i[3] for i in pos.index], incumbent_id=inc_id.loc[pos.index, a].values))
                        est_s, *_ = (np.nan,) * 4
                        sh = cluster_mean_ci(df.sa, [df.family, df.incumbent_id], nboot=NB, seed=1) if len(df) else (np.nan,) * 4
                        ml = cluster_mean_ci(lr.lr, [lr.family, lr.incumbent_id], nboot=NB, seed=2) if len(lr) >= 3 else (np.nan,) * 4
                        rows.append(dict(board=board, rule_a=a, rule_b=b, incumbent=inc, B=B, metric=metric, unit="points", share_a_cheaper=sh[0], share_ci_lo=sh[1], share_ci_hi=sh[2],
                                         mean_log_ratio=ml[0], ci_lo=ml[1], ci_hi=ml[2], n_targets=len(lr), n_share=len(df), n_clusters=ml[3], ci_method="cluster bootstrap (family, incumbent; union), %d draws" % NB))
    return pd.DataFrame(rows)


def rule_order_rows():
    rows = []
    for board, d in top.groupby("board"):
        for inc in ("own", "common"):
            for B in sorted(d.B.unique()):
                W = wide(d, "depth_star", B, inc).replace(np.inf, 1e9)
                W = W[(W[RULES] > 0).all(axis=1)] if (W[RULES] > 0).all(axis=1).sum() >= 5 else W
                R = W[RULES].rank(axis=1)
                taus = []
                for i in range(len(R)):
                    oth = R.drop(R.index[i]).mean()
                    taus.append(kendall_tau(R.iloc[i].values, oth.values))
                df = pd.DataFrame(dict(tau=taus, family=[i[3] for i in R.index])).dropna()
                if len(df) < 3: continue
                est = cluster_mean_ci(df.tau, [df.family], nboot=NB, seed=3)
                rows.append(dict(board=board, incumbent=inc, B=B, kendall_tau_mean=est[0], ci_lo=est[1], ci_hi=est[2], n_targets=len(df), n_clusters=est[3],
                                 median_rank_order=" < ".join(R.mean().sort_values().index)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd_ = paired_rows(); pd_.to_csv(f"{T}/paired.csv", index=False); print("paired", len(pd_))
    ro = rule_order_rows(); ro.to_csv(f"{T}/rule_order.csv", index=False); print("rule_order", len(ro))
