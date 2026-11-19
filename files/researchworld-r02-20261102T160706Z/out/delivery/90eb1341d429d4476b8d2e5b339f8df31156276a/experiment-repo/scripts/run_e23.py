"""E2 / E3 driver.  python scripts/run_e23.py --e 2 --logits results/e23/cnn_logits_ep12.npy --T 1 --n_cal 1000 --reps 200 --out ..."""
import argparse, os, sys
import numpy as np, pandas as pd
from scipy.special import softmax
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cpc.e23 import run_e2_rep, run_e3_rep

ap = argparse.ArgumentParser()
ap.add_argument("--e", type=int); ap.add_argument("--logits"); ap.add_argument("--T", type=float, default=1.0)
ap.add_argument("--n_cal", type=int, default=1000); ap.add_argument("--n_sig", type=int, default=2000)
ap.add_argument("--reps", type=int, default=200); ap.add_argument("--seed0", type=int, default=0); ap.add_argument("--out")
a = ap.parse_args()
P = softmax(np.load(a.logits) / a.T, axis=1)
rows, idents = [], []
if a.e == 2:
    y = np.load(os.path.join(os.path.dirname(a.logits), "cifar10_test_labels.npy"))
else:
    Y = np.load("/hutian/data/c10h/c10h.npy")
for r in range(a.reps):
    rng = np.random.default_rng(a.seed0 + r)
    if a.e == 2:
        out, ident = run_e2_rep(P, y, a.n_cal, rng)
        idents.append(ident)
    else:
        out = run_e3_rep(P, Y, a.n_sig, a.n_cal, rng)
    for o in out:
        o.update(rep=r, T=a.T, n_cal=a.n_cal, logits=os.path.basename(a.logits)); rows.append(o)
    if r % 10 == 0: print("rep", r, flush=True)
os.makedirs(os.path.dirname(a.out), exist_ok=True)
pd.DataFrame(rows).to_csv(a.out, index=False)
if idents:
    pd.DataFrame(idents).assign(T=a.T, n_cal=a.n_cal, logits=os.path.basename(a.logits)).to_csv(a.out.replace(".csv", "_ident.csv"), index=False)
