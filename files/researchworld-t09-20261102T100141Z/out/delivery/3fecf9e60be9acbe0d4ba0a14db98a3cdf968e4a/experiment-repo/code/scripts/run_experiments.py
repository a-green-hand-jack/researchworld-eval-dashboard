"""Usage: python scripts/run_experiments.py E1_size [E2_degree ...] [--procs 2] [--scale 1.0] [--from-config results/config.json]
Writes results/raw/<exp>.parquet (per-rep estimates)."""
import sys, os, time, argparse, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import multiprocessing as mp, pandas as pd
from netgate.sim import run_cell, cell_id
from experiments import EXPS, SEEDS

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw")


SEED = 20261102


def work(spec):
    s = {k: v for k, v in spec.items() if k != "tag"}
    df = run_cell(s, base_seed=SEED)
    df["tag"] = spec["tag"]
    print(f"HUTIAN_PROGRESS {spec['tag']} {df.attrs['secs']:.1f}s", flush=True)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("exps", nargs="+"); ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--scale", type=float, default=1.0, help="multiply R (reps per graph)")
    ap.add_argument("--seed", type=int, default=20261102, help="base seed (robustness reruns use another one)")
    ap.add_argument("--only", default="", help="keep cells whose tag contains this substring (comma-separated alternatives)")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--from-config", default="", help="take the cell specs from this config.json (results/config.json) instead of experiments.py: "
                    "replays the delivered runs bit-for-bit (cell ids, hence random streams, depend on the exact spec)")
    a = ap.parse_args()
    seed_arg = a.seed
    os.makedirs(OUT, exist_ok=True)
    for e in a.exps:
        SEED = SEEDS.get(e, seed_arg) if seed_arg == 20261102 else seed_arg   # per-experiment default unless --seed is given
        cells = json.load(open(a.from_config))[e] if a.from_config else EXPS[e]()
        if a.only:
            cells = [c for c in cells if any(o in c["tag"] for o in a.only.split(","))]
        for c in cells:
            c["R"] = max(2, int(c["R"] * a.scale))
        t = time.time()
        with mp.Pool(a.procs) as pool:
            dfs = pool.map(work, cells, chunksize=1)
        df = pd.concat(dfs)
        df.to_parquet(os.path.join(OUT, f"{e}{a.suffix}.parquet"))
        json.dump(cells, open(os.path.join(OUT, f"{e}{a.suffix}.specs.json"), "w"), indent=1)
        print(f"HUTIAN_DONE {e} cells={len(cells)} rows={len(df)} secs={time.time() - t:.0f}", flush=True)
