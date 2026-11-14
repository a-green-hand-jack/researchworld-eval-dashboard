"""Which paired differences to the Euclidean baseline are resolved (95% paired-bootstrap CI excludes 0) at the replication counts used?
Reads results/tables/A1_paired_vs_euc.csv (+ A1m_ for the Mahalanobis score); writes A1_resolved.csv (per config/method/metric flag) and prints shares."""
import pandas as pd
P = pd.concat([pd.read_csv("results/tables/A1_paired_vs_euc.csv"),
               pd.read_csv("results/tables/A1m_paired_vs_euc.csv").query("method == 'maha'").assign(config=lambda d: d.config.str.replace("A1m_", "A1_"))])
P["resolved"] = (P.lo > 0) | (P.hi < 0)
def lab(r):
    if pd.isna(r.lo):
        return "not computed"
    if not r.resolved:
        return "unresolved"
    return "better" if ((r.diff_vs_euc < 0) == (r.metric in ("log_vol_ratio", "true_x0_10_dev"))) else "worse"


P["direction"] = [lab(r) for r in P.itertuples()]
P.to_csv("results/tables/A1_resolved.csv", index=False)
print(P.groupby(["metric", "direction"]).size().unstack(fill_value=0))
print(P[P.metric == "log_vol_ratio"].groupby(["method", "direction"]).size().unstack(fill_value=0))
