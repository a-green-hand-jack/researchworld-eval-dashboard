import os
for _v in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[_v]="1"
import time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_experiments import *
kind = sys.argv[1] if len(sys.argv) > 1 else "stanford3"
t = time.time()
S = mk("E1", kind, "pow", kappa=2.0, chunks=5)[0]
S['reps'] = 2; S['seed'] = 1
ctx = Context(S); print("ctx", time.time() - t, flush=True)
t = time.time(); rng = np.random.default_rng(1)
for _ in range(2):
    ctx.one_rep(rng)
print("2 reps", time.time() - t, flush=True)
t = time.time(); print(predict_ols(ctx, "OLS-f", R=10), time.time() - t)
