import numpy as np, time
from synth import PRESETS
import sel_lib as sl
import pandas as pd
rng = np.random.default_rng(0)
m = PRESETS["base_tau.1"]; t = time.time()
rows = [m.replicate(200, 20, rng) for _ in range(300)]
df = pd.DataFrame(rows); print("sec", time.time() - t)
for e in ["naive", "hold", "cv", "boot", "b632", "eb"]:
    tr = df["hold_truth"] if e == "hold" else df["truth"]
    print(e, round((df[e] - tr).mean(), 4), round(((df[e] - tr) ** 2).mean() ** .5, 4))
for e, (a, b) in {"naive": ("naive_lo", "naive_hi"), "sim": ("sim_lo", "sim_hi"), "boot": ("boot_lo", "boot_hi"), "hold": ("hold_lo", "hold_hi"), "eb": ("eb_lo", "eb_hi")}.items():
    tr = df["hold_truth"] if e == "hold" else df["truth"]
    print(e, sl.cover(df[a].values, df[b].values, tr.values, 0 * tr.values).mean(), (df[b] - df[a]).mean())
