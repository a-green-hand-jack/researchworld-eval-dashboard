"""Background-figure data (Fig. 1): the exposure g a Bernoulli(p) experiment produces versus the corner it must extrapolate to.
ER graph, n = 10^4, d in {10, 100}, p = 0.25, kappa = 1, shapes convex / thresh, noiseless (sigma = 0), REG-L fit.
Writes results/fig1_corner.parquet (long format): kind in
  sample  : g, z for each unit (value = observed y)
  curve   : value = fitted REG-L response (kind='fit') or true response (kind='true') on a grid of g, for z in {0, 1}
  corner  : value = all-treated / all-control mean outcome, true (kind='corner_true') and predicted (kind='corner_pred')
Same code and seeds as the grids (graph + assignment drawn from SeedSequence([SEED, d, shape-index]))."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from netgate.ctx import Ctx  # noqa: E402
from netgate.designs import Design  # noqa: E402
from netgate.estimators import FEATURES  # noqa: E402
from netgate.graphs import make_graph  # noqa: E402
from netgate.outcomes import OutSpec, freeze, potential  # noqa: E402

SEED, N, P = 0, 10000, 0.25
rows = []
for d in (10, 100):
    for si, shape in enumerate(("convex", "thresh")):
        rng = np.random.default_rng(np.random.SeedSequence([SEED, d, si]))
        spec = OutSpec(kappa=1.0, shape=shape, gamma=1.0, sigma=0.0)
        A, blocks = make_graph("er", N, d, rng)
        ctx = Ctx(A, blocks)
        fz = freeze(spec, ctx, rng)
        z = Design("bern", P).draw(ctx.n, rng)
        st = ctx.state(z)
        y = potential(spec, fz, ctx, st)
        Phi = FEATURES["REG-L"](st, ctx, spec)
        b = np.linalg.lstsq(Phi, y, rcond=None)[0]
        base = dict(d=d, d_mean=ctx.dbar, p=P, kappa=1.0, shape=shape, n=ctx.n)
        for i in range(ctx.n):
            rows.append(dict(base, kind="sample", z=z[i], g=st["g1"][i], value=y[i]))
        grid = np.linspace(0, 1, 101)
        for zz in (0.0, 1.0):
            rows += [dict(base, kind="fit", z=zz, g=g, value=b[0] + b[1] * zz + b[2] * g) for g in grid]
            rows += [dict(base, kind="true", z=zz, g=g, value=zz + spec.H(g)) for g in grid]   # alpha = 0, beta = gamma = 1
        for nm, zz in (("1", 1.0), ("0", 0.0)):
            rows.append(dict(base, kind="corner_true", z=zz, g=zz, value=float(potential(spec, fz, ctx, ctx.corner(zz)).mean())))
            rows.append(dict(base, kind="corner_pred", z=zz, g=zz, value=float(b[0] + b[1] * zz + b[2] * zz)))
        rows.append(dict(base, kind="gate", z=np.nan, g=np.nan, value=float(2.0)))
        rows.append(dict(base, kind="gate_hat", z=np.nan, g=np.nan, value=float(b[1] + b[2])))
        rows.append(dict(base, kind="g_sd", z=np.nan, g=np.nan, value=float(st["g1"].std())))
os.makedirs("results", exist_ok=True)
df = pd.DataFrame(rows)
df.to_parquet("results/fig1_corner.parquet", index=False)
print(df[df.kind.isin(["gate_hat", "g_sd"])][["d", "shape", "kind", "value"]])
