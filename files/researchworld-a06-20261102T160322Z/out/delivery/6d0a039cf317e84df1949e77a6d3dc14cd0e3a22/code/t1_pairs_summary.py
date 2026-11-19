"""Pair design summary: decisions_ab_t1.csv (claim 'A better than B by > m' from point estimates / interval bounds, by true regime),
methods_t1_pairs.parquet and a bias/RMSE table of the per-system estimates. usage: t1_pairs_summary.py MODEL"""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import aggregate as A
R = A.R
model = sys.argv[1]
runs = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{R}/t1pairs/{model}.n*.runs.parquet"))], ignore_index=True)
meth = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{R}/t1pairs/{model}.n*.methods.parquet"))], ignore_index=True)
meth.to_parquet(f"{R}/methods_t1_pairs.parquet"); runs.to_parquet(f"{R}/runs_t1_pairs.parquet")
pairs = [(c[:-2] + "|A", c[:-2] + "|B") for c in sorted(runs.cell_id.unique()) if c.endswith("|A")]
ab = A.ab_decisions(meth, pairs)
ab["n"] = ab.cell_A.str.extract(r"n=(\d+)")[0].astype(int); ab["K_A"] = ab.cell_A.str.extract(r"KA=(\d+)")[0].astype(int); ab["K_B"] = ab.cell_A.str.extract(r"KB=(\d+)")[0].astype(int)
ab.to_csv(f"{R}/decisions_ab_t1.csv", index=False)
# true-difference summary per pair: how often the more-tuned system is truly better
r = runs.pivot_table(index=["n", "rep", "cell_id"], values=["reported_naive", "theta"]).reset_index(); r["pair"] = r.cell_id.str[:-2]; r["side"] = r.cell_id.str[-1]
w = r.pivot_table(index=["pair", "n", "rep"], columns="side", values=["reported_naive", "theta"]).reset_index(); w.columns = ["_".join(c).strip("_") for c in w.columns]
w["reported_diff"] = w.reported_naive_A - w.reported_naive_B; w["true_diff"] = w.theta_A - w.theta_B
s = w.groupby(["pair", "n"]).agg(reps=("rep", "size"), reported_diff_mean=("reported_diff", "mean"), true_diff_mean=("true_diff", "mean"), p_true_A_better=("true_diff", lambda x: (x > 0).mean()),
                                  p_reported_A_better=("reported_diff", lambda x: (x > 0).mean()), p_flip=("reported_diff", lambda x: np.nan)).reset_index().drop(columns="p_flip")
w["flip"] = np.sign(w.reported_diff) != np.sign(w.true_diff); s = s.merge(w.groupby(["pair", "n"]).flip.mean().rename("p_rank_flip").reset_index(), on=["pair", "n"])
s.to_csv(f"{R}/summary_pairs_t1.csv", index=False); print(s.round(3).to_string())
