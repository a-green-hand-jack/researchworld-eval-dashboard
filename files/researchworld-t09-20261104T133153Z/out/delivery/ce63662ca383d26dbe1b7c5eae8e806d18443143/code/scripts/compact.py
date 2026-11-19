#!/usr/bin/env python3
"""Compact replicate-level data (experiment-repo#16(1)): results/compact/<exp>.parquet, one row per (cell, world, replicate, estimator), with every column the
aggregation uses (estimate, GATE, the standard errors, bootstrap bounds, exposure diagnostics, cell parameters). Floats other than est and gate are stored as float32 (relative error
6e-8), repeated strings as dictionary columns; the file is zstd-compressed with byte-stream-split floats. `python3 scripts/aggregate.py --compact e2` rebuilds
summary/<exp>.csv from these files without the raw csv.gz; `scripts/compact.py --check` compares such a rebuild with the shipped summaries."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import glob, os, sys
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

ROOT = str(results_dir())
DROP = ["secs"]  # wall-clock of the cell, not a result


def load_raw(exp):
    files = sorted(glob.glob(os.path.join(ROOT, "raw", exp, "*.csv.gz")))
    return pd.concat((pd.read_csv(f) for f in files), ignore_index=True) if files else None


def shrink(df):
    df = df.drop(columns=[c for c in DROP if c in df.columns])
    for c in df.columns:
        if df[c].dtype == "float64" and c not in ("est", "gate"):  # est and gate stay float64: noiseless cells compare errors of ~1e-12 with SEs of ~1e-12
            df[c] = df[c].astype("float32")
        elif c in ("est_name", "graph", "design", "tag", "o_mech", "o_kind", "exp"):
            df[c] = df[c].astype("category")
        elif c in ("world", "rep"):
            df[c] = df[c].astype("int16")
        elif c in ("cell", "n"):
            df[c] = df[c].astype("int32")
    return df


def write(exp):
    df = load_raw(exp)
    if df is None:
        return
    df = shrink(df)
    float_cols = [c for c in df.columns if df[c].dtype == "float32"]
    os.makedirs(os.path.join(ROOT, "compact"), exist_ok=True)
    path = os.path.join(ROOT, "compact", f"{exp}.parquet")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), path, compression="zstd", compression_level=19,
                   use_dictionary=[c for c in df.columns if c not in float_cols], use_byte_stream_split=float_cols)
    print(exp, len(df), "rows", round(os.path.getsize(path) / 1e6, 2), "MB")


def check(exps):
    import importlib.util
    spec = importlib.util.spec_from_file_location("aggregate", os.path.join(os.path.dirname(os.path.abspath(__file__)), "aggregate.py"))
    agg = importlib.util.module_from_spec(spec); spec.loader.exec_module(agg)
    worst = 0
    for exp in exps:
        S = agg.summarize_frame(pd.read_parquet(os.path.join(ROOT, "compact", f"{exp}.parquet")))
        ref = pd.read_csv(os.path.join(ROOT, "summary", f"{exp}.csv"))
        assert len(S) == len(ref) and (S.cell.values == ref.cell.values).all() and (S.est_name.values == ref.est_name.values).all(), exp
        num = [c for c in ref.columns if ref[c].dtype.kind == "f"]
        rel = (S[num].values - ref[num].values) / np.maximum(1e-3, np.abs(ref[num].values))
        m = np.nanmax(np.abs(rel)); worst = max(worst, m)
        print(exp, "rebuilt from compact: max relative difference to summary", f"{m:.2e}", "(NaN pattern equal: %s)" % bool((S[num].isna().values == ref[num].isna().values).all()))
    return worst


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--check":
        check(a[1:]); sys.exit(0)
    for e in a or [f"e{i}" for i in range(1, 22)]:
        write(e)
