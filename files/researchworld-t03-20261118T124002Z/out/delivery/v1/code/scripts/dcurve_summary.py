"""d-curve table from results/verdicts_R20.csv: per dataset x model (x output scale) and number of attributes d, the shipped-default read-outs at the shipped budget.
Group ids are <dataset>_d<sub|full>_<model>[_logit]; d is taken from the verdicts file. Writes results/dcurve_summary.csv.
usage: python3 scripts/dcurve_summary.py"""
import re, pandas as pd
V = pd.read_csv("results/verdicts_R20.csv")
V = V[(V.k == 3) & (((V.budget == "x1") & V.arm.isin(["kshap_default", "kshap_l1off", "covert_lee"])) | ((V.budget == "perm500") & (V.arm == "perm")))].copy()
m = V.group.str.extract(r"^(?P<dataset>german|ACSEmployment|arrhythmia)_d(?P<dsub>sub|full|\d+)_(?P<model>lr|mlp|gbdt)(?P<scale>_logit)?$")
V = pd.concat([V, m], axis=1)
V["scale"] = V.scale.fillna("").str.strip("_").replace("", "prob")
cols = ["dataset", "model", "scale", "d", "n_seeds", "arm", "budget", "mean_r", "r_lo", "r_hi", "U_delta10", "nog", "C1_outcome", "C5_bias_share", "group"]
D = V[cols].sort_values(["dataset", "model", "scale", "d", "arm"])
D.to_csv("results/dcurve_summary.csv", index=False)
pd.set_option("display.width", 220)
print(D[D.arm.isin(["kshap_default", "kshap_l1off"])].pivot_table(index=["dataset", "model", "scale", "d"], columns="arm", values=["mean_r", "C5_bias_share"]).round(3).to_string())
