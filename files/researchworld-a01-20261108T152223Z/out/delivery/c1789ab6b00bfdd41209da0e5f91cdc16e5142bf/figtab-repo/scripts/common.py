"""Shared helpers: loading experiment-repo results, rule order, provenance sidecars."""
import hashlib, json, pathlib, subprocess
import numpy as np, pandas as pd

RULE_ORDER = ["mean", "geomean", "harmonic", "median", "min", "plurality", "borda", "copeland", "condorcet"]  # headline rules
CAP_LABEL = {"ceil": "cap = 100 (ceil)", "front0": "cap = best existing +0", "front2": "cap = best existing +2",
             "gain5": "cap = base +5", "gain10": "cap = base +10", "gain20": "cap = base +20",
             "emp95": "cap = base + empirical 95th-pct. gain", "emp99": "cap = base + empirical 99th-pct. gain"}
CAP_ORDER = ["ceil", "front2", "front0", "gain20", "gain10", "gain5"]

def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def load_main(resdir, name):
    """Main-grid CSV. Infeasible (target, rule, cap) cells have K = L1 = inf in the file; `feasible` marks them."""
    d = pd.read_csv(pathlib.Path(resdir) / name)
    d["feasible"] = np.isfinite(d.L1)   # L1 = inf: infeasible; L1 = NaN: solver failure (neither feasible nor infeasible)
    d["failed"] = d.L1.isna()
    return d

OLLB_FILES = {  # target sets of the Open LLM Leaderboard runs (experiment-repo REPRODUCE.md section 3)
    "pop": ["ollb_score.csv.gz", "ollb_wmean.csv.gz", "ollb_ord_ceil.csv", "ollb_ord_front0.csv", "ollb_ord_gain10.csv", "ollb_ord_emp95.csv"],
    "top500": ["ollb_top500_a.csv", "ollb_top500_b.csv", "ollb_top500_c.csv", "ollb_top500_cope_ceil.csv"],
    "raw": ["ollb_raw_score.csv.gz", "ollb_raw_score_front0.csv.gz", "ollb_raw_score_gain10.csv.gz", "ollb_raw_score_gain20.csv.gz", "ollb_raw_ord.csv"],
}
def load_ollb(resdir, source):
    """Concatenated Open LLM Leaderboard grid files of one source: pop (score rules on all 4495 non-first targets, rank rules on 57 sampled targets),
    top500 (116 sampled targets of the top-500 slice, every rule; Copeland only at ceil on 30 targets and gain10), raw (raw-score variant)."""
    d = pd.concat([load_main(resdir, f) for f in OLLB_FILES[source]], ignore_index=True)
    return d[d.rank_mean > 1]

def write_provenance(out_stem, script, resdir, inputs, extra=None):
    """<out_stem>.inputs.json: generator script, input files with SHA-256, revision of the results repo."""
    resdir = pathlib.Path(resdir)
    try:
        rev = subprocess.run(["git", "-C", str(resdir), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        rev = None
    rec = {"script": script, "results_repo": "experiment-repo", "results_repo_revision": rev,
           "inputs": {f: sha256(resdir / f) for f in inputs}}
    rec.update(extra or {})
    pathlib.Path(f"{out_stem}.inputs.json").write_text(json.dumps(rec, indent=1) + "\n")

def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h
