import os, sys, time
os.environ["OMP_NUM_THREADS"] = "1"; os.environ["OPENBLAS_NUM_THREADS"] = "1"
import numpy as np
from joblib import Parallel, delayed
sys.path.insert(0, "code")


def work(i):
    from ppi_lib import run_all
    rng = np.random.default_rng(i)
    f = rng.normal(size=(10200, 1)); y = f[:200, 0] + rng.normal(size=200)
    for _ in range(3):
        run_all(y, f[:200], f[200:], rng)
    return 0


if __name__ == "__main__":
    for nj in (1, 4, 16, 32):
        with Parallel(n_jobs=nj) as par:
            par(delayed(work)(i) for i in range(nj))  # warm up (imports)
            t = time.time(); par(delayed(work)(i) for i in range(nj * 2)); dt = time.time() - t
        print(nj, "jobs: wall", round(dt, 1), "reps/s", round(nj * 2 * 3 / dt, 2), flush=True)
