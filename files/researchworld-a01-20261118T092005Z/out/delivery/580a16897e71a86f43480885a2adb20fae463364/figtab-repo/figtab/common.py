"""Loading of result files and saving of outputs with provenance."""
import hashlib
import json
import os
import sys

import pandas as pd


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find(results, name):
    for ext in (".csv", ".parquet"):
        p = os.path.join(results, name + ext)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"{name}.csv/.parquet not in {results}")


def load(results, name):
    p = find(results, name)
    df = pd.read_parquet(p) if p.endswith(".parquet") else pd.read_csv(p)
    return df, p


def save_fig(fig, out, name, inputs, note=""):
    """Write figures/<name>.pdf and <name>.provenance.json (inputs with sha256)."""
    os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, name + ".pdf"))
    prov = {"output": name + ".pdf", "script": os.path.basename(sys.argv[0]),
            "inputs": {os.path.basename(p): sha256(p) for p in inputs}, "note": note}
    json.dump(prov, open(os.path.join(out, name + ".provenance.json"), "w"), indent=1)


def save_table(tex, out, name, inputs):
    os.makedirs(out, exist_ok=True)
    srcs = ", ".join(f"\\texttt{{results/{os.path.basename(p)}}}" for p in inputs)
    open(os.path.join(out, name + ".tex"), "w").write(tex.rstrip() + f"\n% source: {srcs}\n")
    prov = {"output": name + ".tex", "script": os.path.basename(sys.argv[0]),
            "inputs": {os.path.basename(p): sha256(p) for p in inputs}}
    json.dump(prov, open(os.path.join(out, name + ".provenance.json"), "w"), indent=1)


def source_note(ax_or_fig, files, fig=None):
    """One-line source note is kept in the provenance file; figures carry none in the image."""
    return ", ".join(os.path.basename(f) for f in files)
