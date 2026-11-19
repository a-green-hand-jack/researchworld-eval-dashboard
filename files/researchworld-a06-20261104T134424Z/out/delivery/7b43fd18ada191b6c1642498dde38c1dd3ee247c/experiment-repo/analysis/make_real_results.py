"""Real-LLM summaries. usage: make_real_results.py REPLAYDIR RESULTSDIR  (REPLAYDIR holds <pool>_<arm>.parquet from run_real.py; results/matrix.npz must exist)"""
import sys, glob, os, json, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from run_grid import summarize
W, R = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(glob.glob(f"{W}/*_*.parquet")):
    pool, arm = os.path.basename(f)[:-8].rsplit("_", 1)
    d = pd.read_parquet(f); s = summarize(d, groupcols=("proc", "n", "K", "est_name")).reset_index(); s["pool"] = pool; s["truth_arm"] = arm; rows.append(s)
pd.concat(rows).to_csv(f"{R}/real_summary.csv", index=False)
m = np.load(f"{R}/matrix.npz", allow_pickle=True); cfgs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code", "config_pool.json")))
Y = m["Y"]; c = pd.DataFrame([cfgs[i] for i in m["cfg_idx"]]); c["cfg_idx"] = m["cfg_idx"]; c["acc"] = Y.mean(1); c["acc_se"] = np.sqrt(c.acc * (1 - c.acc) / Y.shape[1])
c.drop(columns=[x for x in c.columns if x in ("demos", "demo_text")], errors="ignore").to_csv(f"{R}/matrix_composition.csv", index=False)
# spread of true (pool) accuracies and its sampling-noise share, and inter-config item correlation
mu = Y.mean(1); sd = mu.std(ddof=1); N = Y.shape[1]; noise_sd = np.sqrt((mu * (1 - mu)).mean() / N) if len(mu) > 1 else np.nan
cor = np.corrcoef(Y.astype(float)) if len(mu) > 1 else np.array([[1.0]])
pd.DataFrame([dict(configs=len(mu), items=N, acc_mean=mu.mean(), sd_acc_across_configs=sd, min_acc=mu.min(), max_acc=mu.max(),
                   mean_pairwise_item_corr=float(cor[np.triu_indices(len(mu), 1)].mean()) if len(mu) > 1 else np.nan)]).to_csv(f"{R}/matrix_spread.csv", index=False)
print(len(c), "configs;", "sd acc", sd)
