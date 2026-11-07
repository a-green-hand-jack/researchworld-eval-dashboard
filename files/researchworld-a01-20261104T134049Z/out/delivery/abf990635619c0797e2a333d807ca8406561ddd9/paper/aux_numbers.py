"""Numbers quoted in the text that are not in a delivered table: HELM Copeland against the Condorcet-winner requirement.
Run from the repository root: python3 -I paper/aux_numbers.py"""
import pandas as pd

d = pd.read_csv("results/core_helm.csv")
for cap in ["emp99T", "ceil"]:
    a = d[(d.rule == "copeland") & (d.cap == cap)].set_index("target")
    b = d[(d.rule == "condorcet") & (d.cap == cap)].set_index("target")
    fa = a.status.isin(["ok", "already_first"])
    fb = b.status.isin(["ok", "already_first"])
    both = a.index[fa & fb.reindex(a.index).fillna(False)]
    print(cap, "targets", len(a), "feasible copeland", int(fa.sum()), "feasible condorcet", int(fb.sum()),
          "feasibility differs on", int((fa != fb.reindex(a.index)).sum()),
          "max |L1 diff|", float((a.loc[both, "L1"] - b.loc[both, "L1"]).abs().max()))
