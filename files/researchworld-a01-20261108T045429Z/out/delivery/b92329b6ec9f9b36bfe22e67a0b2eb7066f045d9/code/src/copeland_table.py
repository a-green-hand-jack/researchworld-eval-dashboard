"""Copeland (exact) vs Condorcet-winner requirement vs mean rule, per checked target -> results/final/copeland_vs_condorcet.csv
Inputs: results/copeland_check.csv (src/run_copeland.py), results/helm_main.csv, results/ollb_top500.csv.  L1 only.
Condorcet-winner cost is an upper bound on the Copeland cost (a Condorcet winner has the top Copeland score)."""
import pathlib, numpy as np, pandas as pd
R = pathlib.Path(__file__).resolve().parents[1] / "results"
cop = pd.read_csv(R / "copeland_check.csv")
main = pd.concat([pd.read_csv(R / "helm_main.csv"), pd.read_csv(R / "ollb_top500.csv")])
main = main[main.rule.isin(["condorcet", "mean"])].pivot_table(index=["dataset", "cap", "target_idx"], columns="rule", values="L1", aggfunc="first").reset_index()
d = cop.merge(main, on=["dataset", "cap", "target_idx"], how="left").rename(columns={"condorcet": "condorcet_winner_L1", "mean": "mean_L1"})
d["ratio_cw_over_copeland"] = d.condorcet_winner_L1 / d.copeland_L1
d["copeland_le_cw"] = d.copeland_L1 <= d.condorcet_winner_L1 + 1e-6
d.to_csv(R / "final" / "copeland_vs_condorcet.csv", index=False)
print(d.drop(columns=["target", "secs"]).to_string())
print("violations of Copeland <= CW:", int((~d.copeland_le_cw).sum()))
