"""Table of datasets / models / AUCs used (paper Table 1)."""
import pickle, glob, numpy as np, os
from common import *
rows = []
names = {"pima": "Pima Diabetes", "gmsc": "Give Me Some Credit", "acsincome": "ACSIncome (CA 2018)",
         "acsemployment": "ACSEmployment (CA 2018)", "german": "German Credit"}
L = ["\\begin{tabular}{lrrrrrcccc}", "\\toprule", "Dataset & $n$ & $n_{\\rm train}$ & $d$ & $b_{\\rm ref}$ & \\#inst. & \\multicolumn{4}{c}{test AUC}\\\\",
     "\\cmidrule(lr){7-10}", " & & & & & & LR & MLP & RF & XGB\\\\", "\\midrule"]
for ds in DATASETS:
    X, y, spec = load_dataset(ds)
    n = len(X); ntr = n - int(np.ceil(0.3 * n)); d = X.shape[1]
    aucs = []
    for k in MODELS:
        f = sorted(glob.glob(f"/work/results/main/{ds}_{k}/inst_*.pkl"))[0]
        aucs.append(pickle.load(open(f, "rb"))["auc"])
    ninst = len(glob.glob(f"/work/results/main/{ds}_lr/inst_*.pkl"))
    L.append(f"{names[ds]} & {n} & {ntr} & {d} & {min(TABLE_CFG[ds]['R'], ntr)} & {ninst} & " + " & ".join(f"{a:.3f}" for a in aucs) + "\\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open("/work/paper/gen/tab_setup.tex", "w").write("\n".join(L))
print("\n".join(L))
