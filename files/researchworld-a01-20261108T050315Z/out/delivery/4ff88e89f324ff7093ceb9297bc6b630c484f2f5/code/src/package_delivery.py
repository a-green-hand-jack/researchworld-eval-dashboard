"""Assemble the delivered `code/` package (<= 100 MB) from this repository: sources, tests, processed data, entrypoints, notes,
tidy results and tables, raw experiment CSVs xz-compressed (results/raw/*.csv.xz; pandas reads them directly), and run logs reduced to their progress / timing / error lines (HiGHS output dropped).
Usage: python3 src/package_delivery.py OUT_DIR       (OUT_DIR is created; existing content under it is replaced)
"""
import sys, re, lzma, shutil, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; out = pathlib.Path(sys.argv[1])
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True)
ign = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
for d in ("src", "tests", "data"): shutil.copytree(ROOT / d, out / d, ignore=ign)
for f in("run.sh", "run_extra.sh", "README.md", "REPRODUCE.md"):
    if (ROOT / f).exists(): shutil.copy2(ROOT / f, out / f)
res = out / "results"; (res / "raw").mkdir(parents=True)
shutil.copytree(ROOT / "results" / "tidy", res / "tidy"); shutil.copytree(ROOT / "results" / "tables", res / "tables")
for f in sorted((ROOT / "results").glob("*.csv")):
    if f.name in ("theory_checks.csv", "time_milp_ollb.csv"): shutil.copy2(f, res / f.name)
    else:
        with open(f, "rb") as a, lzma.open(res / "raw" / (f.name + ".xz"), "wb", preset=6) as b: shutil.copyfileobj(a, b)
shutil.copy2(ROOT / "results" / "MANIFEST.sha256.json", res / "MANIFEST.sha256.json")
keep = re.compile(r"done \d+s|^draw|^\{|Error|error|Killed|Traceback|command not found|^\s+(File|\w+Error)|rows;|no data|passed|failed")
(out / "logs").mkdir()
for f in sorted((ROOT / "logs").glob("*.log")):
    lines = [l.rstrip() [:300] for l in f.read_text(errors="replace").splitlines() if keep.search(l)]
    (out / "logs" / f.name).write_text("\n".join(lines) + "\n")
size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file()); print(f"{size / 1e6:.1f} MB in {out}")
