#!/usr/bin/env python3
"""Format checks for the delivered paper against the NeurIPS 2026 main-track requirements (venue/VENUE.md, R1-R6, R9).

usage: python3 venue/check_venue.py PAPER.pdf PAPER_DIR [README.md]
  PAPER_DIR holds the LaTeX source (main .tex files, neurips_2026.sty).
Prints one line per check (PASS/FAIL/WARN) and exits 1 on any FAIL. Needs `pdftotext` (poppler).
"""
import hashlib, re, subprocess, sys
from pathlib import Path

STY_SHA256 = "c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a"  # official neurips_2026.sty
MAX_CONTENT_PAGES = 9
res = []

def chk(ok, name, detail="", warn=False):
    res.append((("PASS" if ok else ("WARN" if warn else "FAIL")), name, detail))

def pages_text(pdf):
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return txt.split("\f")[:-1] if txt.endswith("\f") else txt.split("\f")

def main(pdf, src, readme=None):
    pdf, src = Path(pdf), Path(src)
    pages = pages_text(pdf)
    n = len(pages)
    chk(pdf.stat().st_size <= 50e6, "R3 file size <= 50 MB", f"{pdf.stat().st_size/1e6:.1f} MB")
    # R2: page where the References heading first appears (as a line of its own, not in the contents of a sentence)
    ref = next((i + 1 for i, t in enumerate(pages) if re.search(r"^\s*(\d+\s+)?References\s*$", t, re.M)), None)
    chk(ref is not None, "R3 References heading found")
    if ref:
        chk(ref <= MAX_CONTENT_PAGES, f"R2 content pages <= {MAX_CONTENT_PAGES}",
            f"References heading on page {ref} (content pages <= {ref}); total pages {n}")
        later = "\n".join(pages[ref - 1:])
        ck = [i + 1 for i, t in enumerate(pages) if "NeurIPS Paper Checklist" in t and i + 1 >= ref]
        chk(bool(ck), "R4 checklist present after the references", f"page(s) {ck}")
        if ck:
            ck_text = "\n".join(pages[ck[0] - 1:])
            chk(ck_text.count("Answer:") >= 15, "R4 15 checklist answers present", f"{ck_text.count('Answer:')} 'Answer:' lines")
            chk("TODO" not in ck_text and "Delete this instruction" not in ck_text and "IMPORTANT, please" not in ck_text,
                "R4 no TODO / instruction block left in checklist")
            chk(ck[0] >= ref, "R3 checklist after references")
    chk("Submitted to" in pages[0], "R1 anonymous-submission footer on page 1 (default 'main' option)",
        "page 1 has no 'Submitted to' footer: final/preprint option or wrong style?")
    tex = {p: p.read_text(errors="ignore") for p in src.rglob("*.tex")}
    chk(bool(tex), "R6 LaTeX source present", f"{len(tex)} .tex files")
    alltex = "\n".join(re.sub(r"(?m)^\s*%.*$", "", t) for t in tex.values())
    m = re.search(r"\\usepackage(\[[^\]]*\])?\{neurips_2026\}", alltex)
    chk(bool(m), "R1 \\usepackage{neurips_2026}")
    if m and m.group(1):
        chk(not re.search(r"final|preprint", m.group(1)), "R1 no final/preprint option", m.group(1))
    sty = next(iter(src.rglob("neurips_2026.sty")), None)
    chk(sty is not None and hashlib.sha256(sty.read_bytes()).hexdigest() == STY_SHA256,
        "R1 neurips_2026.sty unmodified (sha256)")
    low = alltex.lower()
    for name, pat in [("abstract", r"\\begin\{abstract\}"), ("introduction", r"\\section\*?\{introduction"),
                      ("related work", r"\\(sub)?section\*?\{[^}]*related work"),
                      ("method", r"\\section\*?\{[^}]*(method|approach|estimator|framework)"),
                      ("experiments", r"\\section\*?\{[^}]*(experiment|empirical|evaluation|result)"),
                      ("discussion/limitations", r"\\(sub)?section\*?\{[^}]*(discussion|limitation)")]:
        chk(re.search(pat, low) is not None, f"R5 section: {name}")
    chk(re.search(r"\\bibliography\{|\\begin\{thebibliography\}|\\printbibliography", alltex) is not None, "R5 bibliography")
    chk(re.search(r"\\url\{https?://(github|gitlab)", alltex) is None, "R1 no repository link in source (anonymity)",
        "a repository URL is in the source; it must be anonymized", warn=True)
    if readme:
        r = Path(readme).read_text(errors="ignore").lower()
        for name, pats in [("environment/dependency versions", ["version", "requirements|environment|pip|conda"]),
                           ("data acquisition + version", ["ppi-python", "0.2.3"]),
                           ("random seeds", ["seed"]), ("run commands + expected time", ["command|run|make", "hour|minute|time"]),
                           ("figure/table -> script map", ["figure|fig\\.", "script|\\.py"]),
                           ("forbidden-content log", ["forbidden|withheld|not encountered|encountered"])]:
            chk(all(re.search(p, r) for p in pats), f"R9/R11 README: {name}", warn=True)
    else:
        chk(False, "R9 README given", "pass README.md as third argument", warn=True)
    return res

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out = main(*sys.argv[1:4])
    for st, name, d in out:
        print(f"{st:4} {name}" + (f" -- {d}" if d else ""))
    sys.exit(1 if any(s == "FAIL" for s, *_ in out) else 0)
