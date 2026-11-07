import time, numpy as np
from bp import *
for name in ["ifeval", "mmlu_pro"]:
    Y = load(name)[:313]
    for d in [1, 3]:
        t = time.time(); m, r = fit_latent(Y, d); print(name, d, round(time.time() - t, 1), "s", r.nit, "iters", flush=True)
