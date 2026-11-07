"""Main per-target tables (schema of figtab-repo/notes/result_schema_request.md).
  python 09_per_target.py <spec>   with spec in
   helm | olb_headline | olb_headline_raw | olb_subtask | ablation_<name>
writes results/per_target_<spec>.csv.  Concatenated into results/per_target.csv by 11_collect.py."""
import sys
from grid import *
spec = sys.argv[1]
CORE = R.RULES; ALLR = R.RULES + R.CARDINAL_POWER
def helm():
    df = load_helm(); return df.values, df.index.values, np.arange(len(df)), dict(leaderboard="helm_mmlu", granularity="headline", population="all")
def olb(pop="main", raw=False, n_log=300):
    o, S = load_olb(pop, raw); tg, _ = pick_targets(S, n_log)
    popname = {"main": "no_flagged", "all": "all", "nomerge": "no_merges", "official": "official_providers"}.get(pop, pop)
    return S, o["fullname"].values, tg, dict(leaderboard="openllm_v2", granularity="headline", population=popname)
out = None
if spec == "helm":
    S, nm, tg, tag = helm(); out = run(S, nm, tg, ALLR, GAINS, tag=tag)
elif spec == "olb_headline":
    S, nm, tg, tag = olb(); out = run(S, nm, tg, ALLR, GAINS, tag=tag)
elif spec == "olb_headline_raw":
    S, nm, tg, tag = olb(raw=True); tag["normalisation"] = "raw"; out = run(S, nm, tg, CORE, ["G1", "G2_0.5", "G1_add10", "ceil"], tag=tag)
elif spec == "olb_subtask":
    df = pd.read_csv(f"{ROOT}/data/processed/olb_subtask.csv", index_col=0); S = df.values; nm = df.index.values
    tg, _ = pick_targets(S, 150); tag = dict(leaderboard="openllm_v2", granularity="subtask", population="subtask_pool_699")
    out = run(S, nm, tg, ALLR, GAINS, tag=tag)
elif spec.startswith("ablation_"):
    which = spec[9:]
    cheap = ["G1", "G2_0.5", "G1_add10", "ceil"]
    if which.startswith("pop_"):
        S, nm, tg, tag = olb(which[4:], n_log=150); out = run(S, nm, tg, CORE, cheap, costs=("linear",), tag=tag)
    elif which.startswith("field_"):
        f = which[6:]; lb = "helm" if f.endswith("_helm") else "olb"; f = f.replace("_helm", "")
        S, nm, tg, tag = helm() if lb == "helm" else olb(n_log=150)
        out = run(S, nm, tg, CORE, cheap, costs=("linear",), field=f, tag=tag)
out.to_csv(f"{ROOT}/results/per_target_{spec}.csv", index=False)
print("done", spec, out.shape)
