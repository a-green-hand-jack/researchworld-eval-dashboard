"""results/provenance.json: for every raw/summary/derived file: the command that produces it, seed, library versions, a hash of the
code (netgate/ + scripts/), size, and the cells requested by the grid but absent from the raw file ('not_run')."""
import hashlib
import importlib.metadata as md
import json
import os
import platform
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from netgate.grids import GRIDS  # noqa: E402
from netgate.summ import CELL  # noqa: E402

root = os.path.join(os.path.dirname(__file__), "..")
h = hashlib.sha256()
for d in ("netgate", "scripts"):
    for f in sorted(os.listdir(os.path.join(root, d))):
        if f.endswith(".py"):
            h.update(open(os.path.join(root, d, f), "rb").read())
sys.path.insert(0, os.path.join(root, "scripts"))
vers = {p: md.version(p) for p in ("numpy", "scipy", "pandas", "pyarrow", "networkx", "scikit-learn", "torch")}
vers["python"] = platform.python_version()
prov = dict(code_sha256=h.hexdigest(), versions=vers, default_seed=0, files={})


def flat(prefix, d, out):
    for k, v in d.items():
        if isinstance(v, dict):
            flat(prefix + k + ".", v, out)
        elif not isinstance(v, (list, tuple)):
            out[prefix + k] = v


for g, fn in GRIDS.items():
    raw = os.path.join(root, "results/raw", g + ".parquet")
    req = fn()
    entry = dict(command=f"python scripts/run_grid.py {g} --workers 2 && python scripts/summarize.py {g}", seed=0,
                 cells_requested=len(req), replicates_per_cell=req[0]["n_rep"], grid_doc=(fn.__doc__ or "").strip().split("\n")[0])
    if not os.path.exists(raw):
        entry.update(state="not run (no raw file yet)", cells_run=0, not_run=len(req))
    else:
        df = pd.read_parquet(raw, columns=[c for c in CELL if c in pd.read_parquet(raw).columns] + ["rep"])
        cols = [c for c in df.columns if c != "rep"]
        have = df.groupby(cols, dropna=False).size().reset_index(name="n")
        entry.update(state="done" if len(have) >= len(req) else "partial", cells_run=int(len(have)), not_run=max(len(req) - len(have), 0),
                     rows=int(len(df)), bytes=os.path.getsize(raw))
    prov["files"][f"results/raw/{g}.parquet"] = entry
prov["files"]["results/fig1_corner.parquet"] = dict(command="python scripts/fig1_corner.py", seed="SeedSequence([0, d, shape_index])")
prov["files"]["results/summary/c3_pairs.csv"] = dict(command="python scripts/analyze_c3.py", seed="numpy default_rng(0) for the paired bootstrap (400 draws)")
json.dump(prov, open(os.path.join(root, "results/provenance.json"), "w"), indent=1)
print(json.dumps({k: v.get("state") for k, v in prov["files"].items()}, indent=0))
