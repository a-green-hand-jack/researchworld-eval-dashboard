"""Merge raw per-experiment parquet files into the tidy delivery tables (schema agreed in experiment-repo#4).
Writes results/replicates.parquet, results/summary.csv, results/diagnostics.csv, results/config.json, results/MANIFEST.md.
Usage: python3 scripts/export.py [EXP ...]   (default: every experiment found in results/raw)"""
import sys, os, json, glob, hashlib, subprocess
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from aggregate import summarize

R = os.path.join(os.path.dirname(__file__), "..", "..", "results")
exps = sys.argv[1:] or sorted(os.path.basename(f)[:-8] for f in glob.glob(os.path.join(R, "raw", "*.parquet")))
reps, cfg, diag_rows = [], {}, []
MECH_NAMES = {("lin_frac", 0): "M1", ("sat", 0): "M3", ("lin_2hop", 0): "M4", ("lin_frac", 0.5): "M5"}
for e in exps:
    df = pd.read_parquet(os.path.join(R, "raw", f"{e}.parquet"))
    specs = json.load(open(os.path.join(R, "raw", f"{e}.specs.json")))
    cfg[e] = specs
    sp = {s["tag"]: s for s in specs}
    info = pd.DataFrame([dict(tag=t, graph=s["graph"]["kind"], mech_kind=s["outcome"]["kind"], het=s["outcome"].get("het", 0),
                              rho=s["outcome"].get("gamma", 1.0) / s["outcome"].get("tau", 1.0), sigma=s["outcome"].get("sigma_e", 1.0),
                              design=s["design"]["kind"], p=s["design"]["p"], cluster_res=s["design"].get("res", np.nan),
                              graph_error_rate=s.get("graph_err", 0.0), R_per_graph=s["R"], G=s["G"]) for t, s in sp.items()])
    info["mechanism"] = [MECH_NAMES.get((k, h), k) if k in ("lin_frac", "sat", "lin_2hop") else k for k, h in zip(info.mech_kind, info.het)]
    if "th_sd" not in df:
        df["th_sd"] = np.nan
    d = df.merge(info.drop(columns=["mech_kind"]), on="tag")
    d["experiment"] = e
    d["fit_data"] = np.where(d.est_name.str.endswith("@pop"), "population", "observed")
    d["estimator"] = d.est_name.str.replace("@pop", "", regex=False)
    z = 1.959964
    d["ci_lo"], d["ci_hi"] = d.est - z * d.se, d.est + z * d.se
    d = d.rename(columns={"g": "graph_id", "est": "tau_hat", "gate": "tau_true", "dbar": "mean_degree", "cell": "seed", "ov1": "overlap_treated", "ov0": "overlap_control", "th_sd": "theory_sd"})
    reps.append(d[["experiment", "tag", "graph", "graph_id", "n", "mean_degree", "mechanism", "rho", "sigma", "design", "p", "cluster_res",
                   "graph_error_rate", "estimator", "fit_data", "seed", "rep", "tau_true", "tau_hat", "ci_lo", "ci_hi",
                   "f_mean", "f_sd", "overlap_treated", "overlap_control", "theory_sd"]])
rep = pd.concat(reps, ignore_index=True)
rep.to_parquet(os.path.join(R, "replicates.parquet"), index=False)

# summaries (observed fits only) + population-level approximation error per cell/estimator
raw = pd.concat([pd.read_parquet(os.path.join(R, "raw", f"{e}.parquet")).assign(experiment=e) for e in exps], ignore_index=True)
raw["tag"] = raw.experiment + "::" + raw.tag
summ = summarize(raw[~raw.est_name.str.endswith("@pop")])
summ[["experiment", "tag"]] = summ.tag.str.split("::", n=1, expand=True)
summ.to_csv(os.path.join(R, "summary.csv"), index=False)
pop = raw[raw.est_name.str.endswith("@pop")].copy()
pop["err"] = pop.est - pop.gate
dg = pop.groupby(["experiment", "tag", "est_name"]).err.agg(pop_bias="mean", pop_bias_sd="std").reset_index()
dg["estimator"] = dg.est_name.str.replace("@pop", "", regex=False)
ex = raw[~raw.est_name.str.endswith("@pop")].groupby(["experiment", "tag"])[["f_mean", "f_sd", "ov1", "ov0", "n", "dbar"]].mean().reset_index()
dg = dg.drop(columns="est_name").merge(ex, on=["experiment", "tag"])
dg["tag"] = dg.tag.str.split("::").str[-1]
dg.rename(columns={"ov1": "overlap_treated", "ov0": "overlap_control", "dbar": "mean_degree"}).to_csv(os.path.join(R, "diagnostics.csv"), index=False)
json.dump(cfg, open(os.path.join(R, "config.json"), "w"), indent=1)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=R).stdout.strip()
dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "../code", "../scripts"], capture_output=True, text=True, cwd=R).stdout.strip())
with open(os.path.join(R, "MANIFEST.md"), "w") as f:
    f.write(f"# Manifest\n\nCode revision at export: `{rev}`{' (+ uncommitted changes in code/ or scripts/)' if dirty else ''}\n\nBase seed: 20261102 (per cell/graph via numpy SeedSequence, see code/netgate/sim.py).\n\n")
    f.write("Inputs (sha256 verified against data.md): socfb-Stanford3.zip b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d; facebook_combined.txt.gz 125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7.\n\n")
    f.write("| experiment | cells | graph draws per cell | reps per graph draw | rows in replicates |\n|---|---|---|---|---|\n")
    for e in exps:
        s = cfg[e]; n_rows = int((rep.experiment == e).sum())
        f.write(f"| {e} | {len(s)} | {sorted({c['G'] for c in s})} | {sorted({c['R'] for c in s})} | {n_rows} |\n")
    f.write("\nFiles: " + ", ".join(f"`{x}` ({sha(os.path.join(R, x))[:12]})" for x in ["replicates.parquet", "summary.csv", "diagnostics.csv", "config.json"]) + "\n")
print(len(rep), "replicate rows;", len(summ), "summary rows")
