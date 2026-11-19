import os, sys, time
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
import numpy as np
sys.path.insert(0, "code")
from ppi_lib import run_all, ALL_METHODS
rng = np.random.default_rng(0)
f = rng.normal(size=(10200, 2)); y = f[:200, 0] + rng.normal(size=200)
run_all(y, f[:200], f[200:], rng, methods=["classical"])
for m in ALL_METHODS:
    t = time.time()
    for _ in range(5): run_all(y, f[:200], f[200:], rng, methods=[m])
    print(m, round((time.time() - t) / 5, 4), flush=True)
