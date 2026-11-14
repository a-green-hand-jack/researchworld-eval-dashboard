"""Analyse the end-to-end DSPy runs (results/dspy/rep_*.json): optimism of the reported score and offline reporting corrections on the candidate matrix."""
import sys, glob, json, numpy as np, pandas as pd
sys.path.insert(0, "/work/code")
from sel import *
reps = [json.load(open(f)) for f in sorted(glob.glob("/work/results/dspy/rep_*.json"))]
base = json.load(open("/work/results/dspy/baseline_zeroshot.json"))
rng = np.random.default_rng(0); rows = []
for r in reps:
    C = np.array([c["subscores"] for c in r["cands"]]).T          # n x ncand (0/1)
    seeds = [c["seed"] for c in r["cands"]]
    n, B = C.shape
    win = int(np.argmax(C.mean(0))); rep = 100 * C[:, win].mean(); test = 100 * r["test_acc"]
    zs = 100 * C[:, seeds.index(-3)].mean()
    # replay bootstrap over the evaluated candidates
    opt = []
    for b in range(200):
        idx = rng.integers(n, size=n); Cb = C[idx]; w = int(np.argmax(Cb.mean(0) + 1e-9 * rng.random(B)))
        opt.append(100 * (Cb[:, w].mean() - C[:, w].mean()))
    boot = rep - np.mean(opt)
    # hold-out (30%) on the candidate matrix; reported value = held-out accuracy of the candidate chosen on the rest
    perm = rng.permutation(n); H, T = perm[:int(round(0.3 * n))], perm[int(round(0.3 * n)):]
    wh = int(np.argmax(C[T].mean(0))); hold = 100 * C[H, wh].mean()
    # worst-case analytic correction
    Sg = np.cov(C.T, ddof=1) / n; P = np.eye(B) - 1.0 / B; sg = float(np.sqrt(np.trace(P @ Sg @ P) / (B - 1)))
    em = float(np.random.default_rng(99).standard_normal((40000, B)).max(1).mean()); worst = rep - 100 * sg * em
    rows.append(dict(rep=r["rep"], reported=rep, test=test, zs_S=zs, base_test=100 * base["acc"], boot=boot, hold=hold, worst=worst, n=n, B=B, winner_seed=r["cands"][win]["seed"]))
df = pd.DataFrame(rows); df.to_csv("/work/results/dspy_summary.csv", index=False)
df["opt"] = df.reported - df.test
def ci(x): x = np.asarray(x); return x.mean(), 1.96 * x.std(ddof=1) / np.sqrt(len(x))
print(len(df), "reps"); print(df.round(1).to_string(index=False))
for k, v in (("optimism reported-test", df.reported - df.test), ("replay-boot - test", df.boot - df.test), ("hold-out - test", df.hold - df.test), ("worst-case - test", df.worst - df.test),
             ("reported gain vs zero-shot (S)", df.reported - df.zs_S), ("true gain vs zero-shot (test)", df.test - df.base_test)):
    m, h = ci(v); print(f"{k}: {m:+.2f} +- {h:.2f}")
