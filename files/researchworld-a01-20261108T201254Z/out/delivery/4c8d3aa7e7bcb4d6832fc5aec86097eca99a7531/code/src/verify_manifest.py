"""Check every file listed in results/MANIFEST.json against its SHA-256 (run from any directory).
Usage: python3 src/verify_manifest.py [--allow-missing]   exit 1 on a mismatch (or a missing file unless --allow-missing)."""
import hashlib, json, pathlib, sys
import pandas as pd
root = pathlib.Path(__file__).resolve().parents[1]
ok = bad = miss = 0
for e in json.load(open(root / "results" / "MANIFEST.json"))["files"]:
    p = root / e["file"]
    if not p.exists(): miss += 1; print("MISSING", e["file"]); continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != e["sha256"] and "volatile_columns" in e:   # measured CPU seconds differ between runs; compare the rest of the file
        h2 = hashlib.sha256(pd.read_csv(p).drop(columns=e["volatile_columns"]).to_csv(index=False).encode()).hexdigest()
        if h2 == e["sha256_without_volatile"]: ok += 1; print("match without", e["volatile_columns"], e["file"]); continue
    if h == e["sha256"]: ok += 1
    else: bad += 1; print("MISMATCH", e["file"])
print(f"{ok} files match, {bad} differ, {miss} missing")
sys.exit(1 if bad or (miss and "--allow-missing" not in sys.argv) else 0)
