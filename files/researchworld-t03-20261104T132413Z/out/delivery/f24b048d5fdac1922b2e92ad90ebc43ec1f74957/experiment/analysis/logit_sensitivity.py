"""Sensitivity of the conclusions to the explained output: P(y=1) (main) versus log-odds.

usage: python3 analysis/logit_sensitivity.py [raw_dir] [out_dir]
For each cell that has a log-odds run (<ds>_logit__<model>__*.npz) and its probability counterpart, per explainer and budget:
mean top-k match to the own reference, median relative error and the run-to-run top-3 agreement, each with an
instance-cluster bootstrap CI, plus the agreement between the two references (share of instances whose top-k sets of
phi*(prob) and phi*(logit) coincide: how much the choice of output changes *what* is explained).
Writes <out>/logit_sensitivity.csv and <out>/logit_reference_agreement.csv.
"""
import glob, os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

raw = sys.argv[1] if len(sys.argv) > 1 else "results/raw"
out = sys.argv[2] if len(sys.argv) > 2 else "results/tables"
rng = np.random.RandomState(12345)
rows, agree = [], []
for f in sorted(glob.glob(f"{raw}/*_logit__*__ref.npz")):
    tag = os.path.basename(f)[:-len("__ref.npz")]
    ds, model = tag.split("__")
    base = ds[:-len("_logit")]
    pairs = {"prob": f"{raw}/{base}__{model}", "logit": f"{raw}/{tag}"}
    if not os.path.exists(pairs["prob"] + "__ref.npz"):
        continue
    refs = {o: np.load(p + "__ref.npz")["ref"] for o, p in pairs.items()}
    for k in (1, 3, 5):
        same = (M.topk_ind(refs["prob"], k) == M.topk_ind(refs["logit"], k)).all(1).astype(float)
        m, lo, hi = M.boot_ci(same, rng, B=1000)
        agree.append(dict(dataset=base, model=model, k=k, topk_same_prob_vs_logit=m, lo=lo, hi=hi, n_inst=len(same)))
    for ex in ("kernel", "perm"):
        if not all(os.path.exists(f"{p}__{ex}.npz") for p in pairs.values()):
            continue
        z = {o: np.load(f"{p}__{ex}.npz") for o, p in pairs.items()}
        for b in range(z["prob"]["phi"].shape[1]):
            for o in pairs:
                per = pd.DataFrame([M.instance_metrics(z[o]["phi"][i, b], refs[o][i]) for i in range(len(refs[o]))])
                r = dict(dataset=base, model=model, explainer=ex, output=o, budget=int(z[o]["budgets"][b]), n_inst=len(per))
                for col in ("relerr_med", "match_ref_k1", "match_ref_k3", "match_ref_k5", "pair_match_k3"):
                    m, lo, hi = M.boot_ci(per[col].values, rng, B=1000)
                    r.update({col: m, col + "_lo": lo, col + "_hi": hi})
                rows.append(r)
os.makedirs(out, exist_ok=True)
pd.DataFrame(rows).to_csv(f"{out}/logit_sensitivity.csv", index=False)
pd.DataFrame(agree).to_csv(f"{out}/logit_reference_agreement.csv", index=False)
print(pd.DataFrame(agree).round(2).to_string())
