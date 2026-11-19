# held-out ROC AUC of the models explained in the paper (seed-0 split / seed-0 models) -> results/auc.csv
import pandas as pd
from sklearn.metrics import roc_auc_score
from common import *
rows = []
for ds in DATASETS:
    Xtr, Xte, ytr, yte = split(ds)
    for m in (["rf", "xgb"] if ds in TREE_ONLY else MODELS):
        mod = make_model(m, 0).fit(Xtr, ytr)
        rows.append(dict(ds=ds, model=m, auc=roc_auc_score(yte, mod.predict_proba(Xte)[:, 1]), ntrain=len(Xtr), ntest=len(Xte), d=Xtr.shape[1], pos_rate=ytr.mean()))
pd.DataFrame(rows).round(3).to_csv("/work/results/auc.csv", index=False)
print(pd.DataFrame(rows).round(3).to_string())
p = pd.DataFrame(rows).pivot(index="ds", columns="model", values="auc").reindex(DATASETS)[MODELS].round(3)
p.insert(0, "d", [dict((r["ds"], r["d"]) for r in rows)[x] for x in p.index])
L = ["\\begin{tabular}{lrcccc}\\toprule", "Data & $d$ & LR & RF & XGB & MLP\\\\\\midrule"]
for ds, r in p.iterrows():
    L.append(f"{ds} & {int(r['d'])} & " + " & ".join("--" if pd.isna(r[m]) else f"{r[m]:.3f}" for m in MODELS) + "\\\\")
L.append("\\bottomrule\\end{tabular}")
open("/work/results/tex_auc.tex", "w").write("\n".join(L))
