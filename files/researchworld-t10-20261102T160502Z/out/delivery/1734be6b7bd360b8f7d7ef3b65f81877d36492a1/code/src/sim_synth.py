"""Synthetic sweep: how much can calibration shorten intervals as E[Y|f] departs from linear?"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import sim, pandas as pd
from multiprocessing import Pool

if __name__ == "__main__":
    sim.RAW = "results/raw_synth"; os.makedirs(sim.RAW, exist_ok=True)
    names = []
    for kind in ["quad", "tanh"]:
        for kappa in [0.0, 0.25, 0.5, 0.75, 1.0]:
            names.append(f"syn:{kind}:{kappa}:1.0")
    for kappa in [0.0, 0.5, 1.0]:
        names.append(f"syn:bin:{kappa}:1.0")
    cells = [(nm, n, N, 1000, False) for nm in names for n in [50, 100, 200, 400, 1000] for N in ([4 * n, 20000])]
    with Pool(2) as p:
        res = p.map(sim.run_cell, cells, chunksize=1)
    pd.DataFrame([r for rs in res for r in rs]).to_csv("results/sim_synth.csv", index=False)
