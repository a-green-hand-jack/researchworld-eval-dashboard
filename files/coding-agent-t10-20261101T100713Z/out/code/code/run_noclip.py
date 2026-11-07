"""Ablation: PPI++ with the power-tuning parameter clipped to [0,1] (as in ppi_py) vs unclipped (lam in R).
Real populations where the OLS slope of Y on Yhat is outside [0,1] (gene_expression, census_income, S1)."""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd, zlib
from multiprocessing import Pool
from datasets import get_pop
from run_experiments import BASE_SEED
import fast

def ppi_unclipped(Y, F, Fu):
    n, N = len(Y), len(Fu)
    th1 = (Y - F).mean() + Fu.mean(); g, gh = Y - th1, F - th1
    lam = np.mean((g - g.mean()) * (gh - gh.mean())) / ((1 + n / N) * np.var(np.r_[F, Fu], ddof=1))
    th = (Y - lam * F).mean() + lam * Fu.mean()
    return th, np.sqrt((lam * Fu).var(ddof=1) / N + (Y - lam * F).var(ddof=1) / n), lam

_P = {}
def one(a):
    name, n, rep = a
    if name not in _P: _P[name] = get_pop(name)
    pop = _P[name]
    rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 99, zlib.crc32(name.encode()), n, rep]))
    Y, F, _ = pop.draw(rng, n); _, Fu, _ = pop.draw(rng, 5000)
    out = []
    for m, (th, se) in [("ppi++clipped", fast.ppi_pp(Y, F, Fu)), ("ppi++unclipped", ppi_unclipped(Y, F, Fu)[:2])]:
        out.append(dict(dataset=name, n=n, rep=rep, method=m, est=th, se=se, truth=pop.truth))
    return out

if __name__ == "__main__":
    ds = ["gene_expression", "census_income", "S1_nonlinear_link", "alphafold", "S7_binary_miscal"]
    tasks = [(d, n, r) for d in ds for n in [50, 200, 1000] for r in range(2000)]
    with Pool(38) as p:
        rows = [x for rr in p.imap_unordered(one, tasks, chunksize=50) for x in rr]
    d = pd.DataFrame(rows); d["w"] = 2 * 1.959964 * d.se; d["cov"] = (abs(d.est - d.truth) <= 1.959964 * d.se)
    s = d.groupby(["dataset", "n", "method"]).agg(cov=("cov", "mean"), width=("w", "mean")).reset_index()
    s.to_csv("../results/noclip.csv", index=False); print(s.to_string())
