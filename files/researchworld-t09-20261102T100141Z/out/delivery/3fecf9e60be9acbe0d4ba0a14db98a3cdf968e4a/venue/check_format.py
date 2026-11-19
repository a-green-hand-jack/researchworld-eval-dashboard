#!/usr/bin/env python3
"""Check a built NeurIPS-2026 PDF against venue/VENUE.md (V2, V3, V4).

usage: python3 venue/check_format.py paper.pdf [paper/main.tex]
Content pages = pages before the first page that starts the References heading
(or the checklist/appendix, whichever comes first). Exit code 1 on any failure.
"""
import re, subprocess, sys

pdf = sys.argv[1]
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout).group(1))
pages = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout for i in range(1, n + 1)]
ok = True

def first(pat):
    for i, t in enumerate(pages, 1):
        if re.search(pat, t, re.M):
            return i
    return None

ref = first(r"^\s*(\d+\s+)?References\s*$")
app = first(r"^\s*(Appendix|A\s+Appendix|\d*\s*Technical appendices)")
chk = first(r"NeurIPS Paper Checklist")
ends = [p for p in (ref, app, chk) if p]
last_content = (min(ends) if ends else n + 1)  # page where non-counting material starts
print(f"pages={n} references@{ref} appendix@{app} checklist@{chk}")
# content may end mid-page where References starts, so that page counts as content
if ref and ref > 9 + 0:
    print("FAIL V2: References start after page 9, main text exceeds 9 pages"); ok = False
elif not ref:
    print("FAIL V3: no References heading found"); ok = False
else:
    print(f"OK V2: main text ends on page <= {ref} (limit 9)")
if not chk:
    print("FAIL V3: NeurIPS Paper Checklist missing"); ok = False
elif ref and chk < ref:
    print("FAIL V3: checklist precedes references"); ok = False
else:
    print("OK V3: checklist present after references")
txt = "\n".join(pages)
for bad in ("TODO", "BEGIN INSTRUCTIONS"):
    if bad in txt:
        print(f"FAIL V4: '{bad}' left in PDF"); ok = False
if len(sys.argv) > 2:
    src = open(sys.argv[2]).read()
    if re.search(r"^[^%]*\\usepackage\[[^\]]*(final|preprint)", src, re.M):
        print("FAIL V1: final/preprint option used (must be anonymous submission mode)"); ok = False
    if "neurips_2026" not in src:
        print("FAIL V1: neurips_2026 style not used"); ok = False
print("PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
