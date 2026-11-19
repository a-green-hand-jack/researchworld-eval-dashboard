"""results/manifest.csv: SHA-256, size, row count, producing script/command and seed of every file under results/ (and the data manifest hash).
Usage: python3 src/manifest.py   (run after the final commit of the code and results; code_commit = HEAD at that moment, 'dirty' if the working tree
differs from HEAD in src/ or data/)
"""
import hashlib, subprocess, pathlib, gzip, csv
ROOT = pathlib.Path(__file__).resolve().parents[1]; R = ROOT / "results"
sh = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True).stdout.strip()
head = sh("git", "rev-parse", "HEAD"); dirty = bool(sh("git", "status", "--porcelain", "src", "data", "tests"))
code = head + ("+dirty" if dirty else "")
MK = (ROOT / "Makefile").read_text().splitlines()
def make_cmd(stem):   # the Makefile line that writes results/<stem>.csv
    for l in MK:
        if f"results/{stem}.csv" in l and "src/" in l: return l.strip().split("$(PY) ", 1)[-1]
    return ""
def producer(p):
    rel = p.relative_to(R); s = p.name.split(".")[0]
    if rel.parts[0] == "final":
        if s == "helm_near_tie": return "python3 src/helm_neartie.py", ""
        if s == "copeland_vs_condorcet": return "python3 src/copeland_table.py", ""
        if s.startswith(("random_control", "leaf")): return "python3 src/summarize_extras.py", 0
        return "python3 src/finalize.py", 0
    if rel.parts[0] == "tables": return ("python3 src/analyze.py" if not s.startswith("summary_") else "python3 src/summarize.py results/<name>.csv results/tables/summary_<name>"), 0
    if s == "theory_checks": return "python3 src/theory_checks.py", ""
    if s.startswith("recheck_inf"): return "python3 src/recheck_inf.py", ""
    if s == "manifest": return "", ""
    c = make_cmd(s)
    return ("python3 " + c if c else "see Makefile"), 0
rows = []
for p in sorted(R.rglob("*")):
    if not p.is_file() or p.name.startswith("_") or p.name == "manifest.csv": continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    op = gzip.open if p.suffix == ".gz" else open
    n = sum(1 for _ in op(p, "rt")) - 1 if p.suffix in (".csv", ".gz") else ""
    cmd, seed = producer(p)
    rows.append(dict(file=str(p.relative_to(ROOT)), sha256=h, bytes=p.stat().st_size, rows=n, command=cmd, seed=seed, code_commit=code))
dm = ROOT / "data/processed/manifest.json"
rows.append(dict(file="data/processed/manifest.json", sha256=hashlib.sha256(dm.read_bytes()).hexdigest(), bytes=dm.stat().st_size, rows="",
                 command="src/build_data.py (inputs pinned inside)", seed="", code_commit=code))
lm = ROOT / "data/processed/ollb_leaf_manifest.json"
if lm.exists():
    rows.append(dict(file="data/processed/ollb_leaf_manifest.json", sha256=hashlib.sha256(lm.read_bytes()).hexdigest(), bytes=lm.stat().st_size, rows="",
                     command="src/build_leaf.py (inputs pinned inside)", seed="", code_commit=code))
with open(R / "manifest.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "files; code", code)
