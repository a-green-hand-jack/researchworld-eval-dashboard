"""Width trend of t_gen / t_fit at each train fraction f (P5): python3 e2_slopes.py OUT.json RUNS_CSV:LABEL [...]
Uses analysis.analyse on the runs of one f at a time (E1 supplies f=0.5)."""
import sys, json
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import analysis as A

out = {}
for spec in sys.argv[2:]:
    path, label = spec.split(":")
    d = pd.read_csv(path)
    for f, g in d.groupby("train_frac"):
        if g.width.nunique() < 3:
            continue
        res = {}
        for thr in ("99", "95"):
            if g[f"t_gen{thr}_s"].notna().sum() < 3:      # too few generalising runs for a slope: record the counts only
                res[thr] = dict(n=len(g), n_gen=int(g[f"t_gen{thr}_s"].notna().sum()), tgen_slope=None)
                continue
            r = A.analyse(g, thr)
            res[thr] = dict(n=len(g), n_gen=int(sum(c["n_gen"] for c in r["cells"])), tgen_slope=r["tgen_tobit_slope"], tfit_slope=r["tfit_slope"],
                            cells=[{k: c[k] for k in ("width", "n", "n_gen", "t_gen_km_median", "t_fit_median", "delay_median")} for c in r["cells"]])
        out[f"{label}_f{f:g}"] = res
        print(label, f, flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)
