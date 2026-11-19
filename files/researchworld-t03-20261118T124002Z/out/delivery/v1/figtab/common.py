"""Loading of result tables and the shared statistics of the figure generators.
Everything is read from RESULTS (experiment-repo's `results/`); nothing is typed by hand.
Files whose name contains `_test` or `pilot` are pilot data: usable only with --pilot, and
then written to figtab/_pilot/ (never delivered)."""
import glob, os, re, argparse, subprocess
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.environ.get("FIGTAB_RESULTS", os.path.join(HERE, "..", "results"))
PILOT_DIR = os.path.join(HERE, "_pilot")
DEFAULT_ARM = "kshap_default"
ARMS = ["kshap_default", "kshap_l1off", "perm", "covert_lee"]   # result-file arm names
BUDGETS = ["x0.25", "x0.5", "x1", "x2", "x4", "x16"]
MODEL_LABEL = {"lr": "LR", "mlp": "MLP", "gbdt": "GBDT", "hgb": "GBDT", "rf": "RF"}
DATA_LABEL = {"ACSEmployment": "ACS-Emp", "german": "German", "acs": "ACS", "arrhythmia": "Arrhythmia"}


def args(desc="", extra=()):
    ap = argparse.ArgumentParser(description=desc)
    for e in extra:
        ap.add_argument(e, action="store_true")
    ap.add_argument("--pilot", action="store_true", help="use *_test/pilot result files; output to figtab/_pilot/")
    ap.add_argument("--out", default=None)
    return ap.parse_args()


def outdir(a):
    d = PILOT_DIR if a.pilot else (a.out or HERE)
    os.makedirs(d, exist_ok=True)
    return d


def _is_pilot(path):
    b = os.path.basename(path)
    return "_test" in b or "pilot" in b


def parse_cell(c):
    """cell name `<dataset>_d<dim|full>_<model>_s<seed>` -> dict"""
    m = re.match(r"(?P<data>[A-Za-z0-9]+)_d(?P<d>[a-z0-9]+)_(?P<model>[a-z0-9_]+?)_s(?P<seed>\d+)$", c)
    if not m:
        raise ValueError(f"unparsable cell name {c!r}")
    return m.groupdict()


def load_tidy(pilot=False, subsets=False):
    """Tier-1 main cells (full dimension, R=20 reruns). `subsets=True` returns the d-curve cells
    (feature subsets) instead. R200 and T2 files are never mixed in; margin-scale (`*_logit_*`) cells are a different scale (the Arrhythmia
    cells and the GBDT controls) and are not loaded here."""
    files = sorted(glob.glob(os.path.join(RESULTS, "tidy_*_R20.csv")))
    files = [f for f in files if _is_pilot(f) == pilot and (("_dfull_" in f) != subsets) and "_logit_" not in f]
    if not files:
        raise SystemExit(f"no {'pilot' if pilot else 'final'} tidy_*.csv in {RESULTS}")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    p = df["cell"].map(parse_cell).apply(pd.Series)
    df = pd.concat([df, p.rename(columns={"data": "dataset", "d": "dtag"})], axis=1)
    df["seed"] = df["seed"].astype(int)
    return df, files


def provenance(files):
    try:
        c = subprocess.check_output(["git", "-C", HERE, "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        c = "unknown"
    return {"inputs": [os.path.basename(f) for f in files], "figtab_commit": c}


def cp_interval(k, n, alpha=0.05):
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def cluster_boot(df, stat, B=2000, seed=0, alpha=0.05):
    """Two-level cluster bootstrap as in the protocol: resample model seeds, then instances
    within each drawn seed. `stat` maps a frame -> float."""
    rng = np.random.default_rng(seed)
    groups = {s: g for s, g in df.groupby("seed")}
    seeds = list(groups)
    out = np.empty(B)
    for b in range(B):
        parts = []
        for s in rng.choice(seeds, len(seeds)):
            g = groups[s]
            parts.append(g.iloc[rng.integers(0, len(g), len(g))])
        out[b] = stat(pd.concat(parts))
    return stat(df), np.quantile(out, alpha / 2), np.quantile(out, 1 - alpha / 2)


def ecdf(x):
    x = np.sort(np.asarray(x))
    return x, np.arange(1, len(x) + 1) / len(x)
