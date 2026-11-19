"""Anonymised supplementary ZIP: code, derived data, results, figure/table generators, REPRODUCE.md.
Run from the repository root: python3 paper/make_supplement.py"""
import os, re, zipfile

POS = re.compile(r"(experiment|story|figtab|paper|venue)-repo")
TEXT = (".md", ".py", ".sh", ".tex", ".txt")


def add(z, path):
    """Position names of the working process are replaced by 'the project' so the ZIP carries no identifying names."""
    if path.endswith(TEXT):
        z.writestr(path, POS.sub("the project", open(path, encoding="utf-8").read()))
    else:
        z.write(path)

out = "paper/supplement_code.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    add(z, "REPRODUCE.md")
    add(z, "paper/aux_numbers.py")
    for top in ["code", "data", "results", "figures", "tables"]:
        for d, _, fs in os.walk(top):
            if "__pycache__" in d:
                continue
            for f in sorted(fs):
                if not f.endswith(".pyc"):
                    add(z, os.path.join(d, f))
print(out, os.path.getsize(out) / 1e6, "MB")
