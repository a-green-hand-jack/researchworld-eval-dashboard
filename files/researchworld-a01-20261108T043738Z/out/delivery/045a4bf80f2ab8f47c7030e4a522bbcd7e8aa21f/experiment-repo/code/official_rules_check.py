"""Does the aggregation the experiments use equal the one the sites publish?
OLLB: published 'Average' column vs the mean of the six normalised task scores (data/processed/ollb6.csv).
HELM: published 'MMLU All Subjects' EM column (groups/json/mmlu_mmlu.json) vs the mean of the 57 per-subject EM values.
Usage: python3 code/official_rules_check.py HELM_DIR OUT.csv
"""
import sys, json, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt

helm_dir, out = pathlib.Path(sys.argv[1]), sys.argv[2]
rows = []
d = pd.read_csv(dt.PROC / "ollb6.csv"); d
m = d[dt.OLLB_TASKS].mean(axis=1)
rows.append(dict(dataset="ollb", published="Average", reproduced="mean of 6 normalised task scores", n_models=len(d),
                 max_abs_dev=float((m - d["Average"]).abs().max()), unit="points (0-100)"))
t = json.load(open(helm_dir / "groups" / "json" / "mmlu_mmlu.json"))
iem = [h["value"] for h in t["header"]].index("EM")
pub = pd.Series({r[0]["value"]: r[iem]["value"] * 100 for r in t["rows"]})
sc = pd.read_csv(dt.PROC / "helm_mmlu_all.csv", index_col=0)
mm = sc.mean(axis=1)
rows.append(dict(dataset="helm", published="MMLU All Subjects - EM", reproduced="mean of 57 per-subject EM", n_models=len(pub),
                 max_abs_dev=float((mm.reindex(pub.index) - pub).abs().max()), unit="points (0-100)"))
rows.append(dict(dataset="helm", published="(none in the downloaded files)", reproduced="mean win rate = Borda on subjects (not published here)", n_models=np.nan,
                 max_abs_dev=np.nan, unit=""))
pd.DataFrame(rows).to_csv(out, index=False); print(pd.DataFrame(rows).to_string())
