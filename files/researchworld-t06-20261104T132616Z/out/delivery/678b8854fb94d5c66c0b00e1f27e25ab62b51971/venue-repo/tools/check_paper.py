#!/usr/bin/env python3
"""Venue checks for a built NeurIPS 2026 paper.

usage: check_paper.py PAPER.pdf [PAPER_SRC_DIR]
Reports: main-text page count (limit 9), where References and the checklist start, leftover checklist
placeholders, template integrity, anonymity hints. Exit code 1 on any hard failure.
"""
import hashlib, pathlib, re, subprocess, sys

LIMIT = 9
_ME = pathlib.Path(__file__).resolve().parent
HERE = next(d for d in (_ME.parent / "neurips2026", _ME.parent / "templates" / "neurips2026") if d.exists())


def pages(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout).group(1))
    return [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout for i in range(1, n + 1)]


def main():
    pdf = sys.argv[1]
    src = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    bad = []
    pg = pages(pdf)
    ref = next((i for i, t in enumerate(pg, 1) if re.search(r"^\s*(\d+\s+)?References\s*$", t, re.M)), None)
    chk = next((i for i, t in enumerate(pg, 1) if "NeurIPS Paper Checklist" in t), None)
    print(f"total pages {len(pg)}; References heading on page {ref}; checklist on page {chk}")
    if ref is None:
        bad.append("no 'References' heading found")
    else:
        before = re.sub(r"\s+", " ", re.split(r"^\s*(?:\d+\s+)?References\s*$", pg[ref - 1], flags=re.M)[0])
        main_pages = ref if len(before) > 300 else ref - 1
        print(f"main text occupies {main_pages} pages (limit {LIMIT}); text before heading on its page: {len(before)} chars")
        if main_pages > LIMIT:
            bad.append(f"main text {main_pages} > {LIMIT} pages (acknowledgments/appendix before References would also be counted wrongly; check by eye)")
    if chk is None:
        bad.append("checklist missing (desk rejection)")
    else:
        if chk < (ref or 0):
            bad.append("checklist precedes references")
        ct = "\n".join(pg[chk - 1:])
        if re.search(r"TODO", ct):
            bad.append("checklist still has TODO placeholders")
        n = len(re.findall(r"Answer:\s*\[(Yes|No|NA|N/A)\]", ct))
        print(f"checklist answers found: {n} of 16")
        if n < 16:
            bad.append(f"only {n}/16 checklist answers recognised")
    if src:
        sty = src / "neurips_2026.sty"
        want = (HERE / "neurips_2026.sty").read_bytes()
        if not sty.exists() or sty.read_bytes() != want:
            bad.append("neurips_2026.sty missing or modified")
        texs = "\n".join(re.sub(r"(?m)^\s*%.*$", "", p.read_text(errors="ignore")) for p in src.rglob("*.tex"))
        if re.search(r"usepackage\[[^\]]*final[^\]]*\]\{neurips_2026\}", texs) or re.search(r"usepackage\[[^\]]*preprint", texs):
            bad.append("final/preprint option set: not the anonymous submission format")
    alltext = "\n".join(pg)
    for pat in (r"github\.com/(?!anonymous)", r"huggingface\.co/[^/\s]+/[^/\s]+"):
        hits = set(re.findall(pat + r"\S*", alltext))
        if hits:
            print("note: URLs in PDF (check anonymity / that they are third-party sources):", sorted(hits)[:5])
    for b in bad:
        print("FAIL:", b)
    print("OK" if not bad else "FAILED")
    sys.exit(1 if bad else 0)


main()
