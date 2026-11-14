"""Assemble the leaf-task run (code/run_leaf.sh) and write the summaries.
Usage: python3 code/assemble_leaf.py [DIR=results/leaf]
Writes DIR/core_leaf.csv (same columns and status as core_ollb.csv; dataset = ollb_leaf (39 leaves) | ollb6_leafslice (six published
tasks of the same 499 models)), DIR/summary_leaf_groups.csv (via summarize.py), DIR/paired_leaf_vs_six.csv: for the same model, cost under
the leaf partition over cost under the six-task partition (targets feasible under both, grouped by the target's rank under the
six-task mean) with a bootstrap CI over targets and the counts (L1_per_task_ratio = the L1 ratio rescaled by 6/39, i.e. points per task), and DIR/frontier_leaf.csv (feasible share by rank stratum)."""
import sys, pathlib, subprocess
import numpy as np, pandas as pd
D = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "results/leaf")
FILES = ["runs_closed_leaf.csv", "runs_ord_leaf.csv", "runs_closed_six.csv", "runs_ord_six.csv"]
COLS = ["dataset", "cap", "cap_role", "rule", "target", "target_idx", "rank_mean", "rank_rule", "gap", "L1", "K", "Linf", "L2", "status"]
d = pd.concat([pd.read_csv(D / f) for f in FILES if (D / f).exists()], ignore_index=True)
d = d.drop_duplicates(["dataset", "cap", "rule", "target_idx"], keep="last")
d["cap_role"] = d.cap.map({"ceil": "oracle", "gain10": "sensitivity", "emp99": "primary-analogue", "emp99task": "primary-analogue"})
for c in COLS:
    if c not in d: d[c] = np.nan
d["status"] = np.where(d.L1.isna(), "censored", np.where(np.isinf(d.L1), "infeasible", np.where(d.L1 == 0, "already_first", "ok")))
d = d[COLS].sort_values(["dataset", "cap", "rule", "rank_mean", "target_idx"], kind="stable")
d.to_csv(D / "core_leaf.csv", index=False); print(len(d), d.groupby(["dataset", "cap"]).size().to_dict())
subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "summarize.py"), str(D / "core_leaf.csv"), str(D / "summary_leaf")], check=True,
               stdout=subprocess.DEVNULL)

subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "frontier.py"), str(D / "core_leaf.csv"), str(D / "frontier_leaf.csv")], check=True,
               stdout=subprocess.DEVNULL)

# paired: same model, leaf vs six (cap pairs: emp99task <-> emp99)
rng = np.random.default_rng(0)
cap_pair = {"ceil": ("ceil", "ceil"), "gain10": ("gain10", "gain10"), "emp99task": ("emp99task", "emp99")}
rows = []
Lf, Sx = d[d.dataset == "ollb_leaf"], d[d.dataset == "ollb6_leafslice"]
rank6 = Sx.drop_duplicates("target_idx").set_index("target_idx").rank_mean
for lc, (cl, cs) in cap_pair.items():
    for rule in sorted(set(Lf.rule) & set(Sx.rule)):
        a = Lf[(Lf.cap == cl) & (Lf.rule == rule)].set_index("target_idx"); b = Sx[(Sx.cap == cs) & (Sx.rule == rule)].set_index("target_idx")
        j = a.index.intersection(b.index)
        for grp, (lo, hi) in {"2-10": (2, 10), "11-100": (11, 100), ">100": (101, 10**6), "all": (2, 10**6)}.items():
            jj = [t for t in j if lo <= rank6.get(t, 0) <= hi]
            both = [t for t in jj if np.isfinite(a.L1[t]) and np.isfinite(b.L1[t]) and a.L1[t] > 0 and b.L1[t] > 0]
            r = dict(cap=cl, rule=rule, group_by_six_rank=grp, n_targets=len(jj), n_feasible_leaf=int(np.sum(np.isfinite(a.L1[jj]))),
                     n_feasible_six=int(np.sum(np.isfinite(b.L1[jj]))), n_both=len(both))
            if both:
                ratio = np.array([a.L1[t] / b.L1[t] for t in both]); bs = [np.median(rng.choice(ratio, len(ratio))) for _ in range(1000)]
                r.update(L1_ratio_med=float(np.median(ratio)), L1_ratio_lo=float(np.percentile(bs, 2.5)), L1_ratio_hi=float(np.percentile(bs, 97.5)),
                         L1_leaf_med=float(np.median([a.L1[t] for t in both])), L1_six_med=float(np.median([b.L1[t] for t in both])),
                         L1_per_task_ratio_med=float(np.median(ratio)) * 6 / 39, K_ratio_med=float(np.median([a.K[t] / b.K[t] for t in both])))
            rows.append(r)
pd.DataFrame(rows).to_csv(D / "paired_leaf_vs_six.csv", index=False)
print(pd.DataFrame(rows).round(2).to_string())
