"""Load tables/data/log_results.csv and recompute gaps; check them against the logged gaps."""
import csv, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
COLS = ["test", "remaining", "forget", "mia"]

def load():
    rows = list(csv.DictReader(open(ROOT / "tables" / "data" / "log_results.csv")))
    for r in rows:
        for c in COLS:
            r[c] = float(r[c])
    return rows

def sel(rows, table, setting=None, method=None):
    return [r for r in rows if r["table"] == table
            and (setting is None or r["setting"] == str(setting))
            and (method is None or r["method"] == method)]

def reference(rows, r):
    """Row a logged gap refers to: Retrained of the same table (and setting if it has one)."""
    ref = r["gap_ref"]
    same = [x for x in rows if x["table"] == r["table"] and x["method"] == ref
            and x["setting"] in (r["setting"],)]
    if not same:  # perturb/lambda ablations: one Retrained row shared by the table
        same = [x for x in rows if x["table"] == r["table"] and x["method"] == ref]
    return same[0]

def check():
    rows = load(); bad = 0
    for r in rows:
        if not r["gap_ref"]:
            continue
        ref = reference(rows, r)
        for c in COLS:
            mine = round(abs(r[c] - ref[c]), 1)
            logged = float(r["logged_gap_" + ("remaining" if c == "remaining" else c)])
            if abs(mine - logged) > 1e-9:
                bad += 1
                print(f"MISMATCH {r['table']} {r['setting']} {r['method']} {c}: recomputed {mine} vs logged {logged}")
    print(f"gap check: {bad} mismatches")
    return bad

if __name__ == "__main__":
    sys.exit(1 if check() else 0)
