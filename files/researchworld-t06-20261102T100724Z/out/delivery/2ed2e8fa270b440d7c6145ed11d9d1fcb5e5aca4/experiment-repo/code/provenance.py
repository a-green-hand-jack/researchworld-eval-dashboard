"""Write results CSVs with a sidecar manifest (seed, code commit, inputs)."""
import json, os, subprocess, hashlib, time
import pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def commit():
    try:
        return subprocess.check_output(["git", "-C", os.path.dirname(os.path.abspath(__file__)), "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "unknown"


def save(df, name, script, seed, inputs=(), note=""):
    os.makedirs(RES, exist_ok=True)
    path = os.path.join(RES, name)
    df.to_csv(path, index=False)
    man_path = os.path.join(RES, "MANIFEST.json")
    man = json.load(open(man_path)) if os.path.exists(man_path) else {}
    man[name] = dict(script=script, seed=seed, rows=len(df), code_commit=commit(), note=note,
                     inputs={os.path.basename(p): sha256(p) for p in inputs},
                     written=time.strftime("%Y-%m-%d %H:%M:%S"))
    json.dump(man, open(man_path, "w"), indent=1, sort_keys=True)
