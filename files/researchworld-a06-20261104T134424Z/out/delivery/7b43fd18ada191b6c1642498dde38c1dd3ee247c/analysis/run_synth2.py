"""Synthetic study part 2: conditional-on-selection (winner) inference for argmax, and comparisons of two tuned systems."""
import sys, numpy as np, pandas as pd, time, warnings; warnings.filterwarnings("ignore")
from synth import make_pool; from run_grid import run, run_compare
out = sys.argv[1]; M = int(sys.argv[2]) if len(sys.argv) > 2 else 500; t0 = time.time(); a = []; b = []
for tau in (0.0, 0.01, 0.03):
    for rho in (0.0, 0.5, 0.9):
        Y = make_pool(64, 20000, m=0.3, tau=tau, rho=rho, seed=7)
        d = run(Y, 0, ["argmax"], [100, 200, 400, 800], [4, 16, 64], ["cond"], M, seed=21, tag=f"tau={tau},rho={rho}"); d["tau"] = tau; d["rho"] = rho; a.append(d)
        if rho == 0.5:
            P = np.arange(64)
            for KA, KB in [(16, 16), (16, 4), (64, 4), (64, 1)]:
                c = run_compare(Y, dict(proc="argmax", K=KA, pool=P), dict(proc="argmax", K=KB, pool=P), [100, 200, 400, 800], M, 31,
                                est_kw=dict(boot_opt=dict(B=100)), tag=f"tau={tau},KA={KA},KB={KB}")
                c["tau"] = tau; c["KA"] = KA; c["KB"] = KB; b.append(c)
        print("done", tau, rho, time.time() - t0, flush=True)
        pd.concat(a).to_parquet(out + "_cond.parquet")
        if b: pd.concat(b).to_parquet(out + "_compare.parquet")
