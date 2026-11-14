#!/usr/bin/env python3
"""Check a built paper against the NeurIPS 2026 main-track requirements recorded in
VENUE.md. Usage: check_venue.py PAPER_DIR MAIN_TEX_STEM [REPRO_DOC [PDF]]
(e.g. check_venue.py paper main README.md paper/main.pdf; PDF defaults to PAPER_DIR/STEM.pdf). Exit status 1 if any FAIL.
Needs poppler's pdftotext/pdfinfo/pdffonts on PATH. Text checks are heuristics
(marked WARN) where the rule cannot be verified mechanically."""
import hashlib, re, subprocess, sys
from pathlib import Path

STY_SHA256 = "c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a"
CHECKLIST_SHA256 = "780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6"
MAX_CONTENT_PAGES = 9          # submission; camera-ready would be 10
N_QUESTIONS = 16
SYNONYMS = {"method": "method|approach|estimator|procedure"}   # a section presenting the route
SECTIONS = ["introduction", "related work", "method", "experiment", "discussion", "limitation"]

res = []
def rec(level, name, msg=""):
    res.append((level, name, msg)); print(f"{level:4s} {name}: {msg}")

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout

def main(pdir, stem, repro=None, pdfpath=None):
    pdir = Path(pdir); tex = pdir / f"{stem}.tex"; pdf = Path(pdfpath) if pdfpath else pdir / f"{stem}.pdf"
    src = tex.read_text(errors="replace") if tex.exists() else ""
    # follow \input / \include one level so sections kept in separate files are read
    for f in re.findall(r"\\(?:input|include)\{([^}]+)\}", src):
        g = pdir / (f if f.endswith(".tex") else f + ".tex")
        if g.exists() and g.name != "checklist.tex":
            src += "\n" + g.read_text(errors="replace")
    # sources need the style file unmodified
    sty = pdir / "neurips_2026.sty"
    if sty.exists():
        ok = hashlib.sha256(sty.read_bytes()).hexdigest() == STY_SHA256
        rec("PASS" if ok else "FAIL", "style file unmodified", str(sty))
    else:
        rec("FAIL", "style file present", "neurips_2026.sty missing next to the tex source")
    rec("PASS" if tex.exists() else "FAIL", "LaTeX source present", str(tex))
    m = re.search(r"\\usepackage\[([^\]]*)\]\{neurips_2026\}", src)
    opts = m.group(1) if m else ""
    uses = re.search(r"\\usepackage(\[[^\]]*\])?\{neurips_2026\}", src)
    rec("PASS" if uses else "FAIL", "uses neurips_2026 package")
    bad = [o for o in ("final", "preprint", "nonanonymous", "position", "eandd") if o in opts]
    rec("PASS" if not bad else "FAIL", "submission-mode options (anonymous, main track)", ",".join(bad) or "none")
    # placeholders
    ph = [w for w in ("TITLE", "ABSTRACT", "TODO", "lorem", "XXX") if re.search(w, src)]
    rec("PASS" if not ph else "FAIL", "no placeholders in tex", ",".join(ph) or "none")
    # sections
    low = src.lower()
    miss = [s for s in SECTIONS if not re.search(r"\\(sub)*section\*?\{[^}]*(" + SYNONYMS.get(s, s) + ")", low)]
    rec("PASS" if not miss and "\\begin{abstract}" in low else "FAIL", "required sections", "missing: " + ",".join(miss) if miss else "abstract+all present")
    rec("PASS" if re.search(r"\\(bibliography|printbibliography|begin\{thebibliography)", src) else "FAIL", "reference list")
    # pdf
    if not pdf.exists():
        rec("FAIL", "PDF present", str(pdf)); return
    info = sh("pdfinfo", str(pdf))
    rec("PASS" if "612 x 792" in info else "FAIL", "US letter page size")
    npages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    pages = sh("pdftotext", "-layout", str(pdf), "-").split("\f")[:npages]
    ref_re = re.compile(r"^\s*(?:\d+\s+)?(?:\d+\s+)?References\s*$", re.M)
    ref_page = next((i for i, p in enumerate(pages, 1) if ref_re.search(p)), None)
    if ref_page is None:
        rec("FAIL", "content pages <= %d" % MAX_CONTENT_PAGES, "no 'References' heading found in PDF")
    else:
        before = ref_re.split(pages[ref_page - 1])[0]
        last = ref_page if len(re.findall(r"[A-Za-z]{3,}", before)) > 8 else ref_page - 1
        rec("PASS" if last <= MAX_CONTENT_PAGES else "FAIL", "content pages <= %d" % MAX_CONTENT_PAGES,
            f"content ends on page {last} (References on page {ref_page}; PDF has {npages})")
    ck = next((i for i, p in enumerate(pages, 1) if "NeurIPS Paper Checklist" in p), None)
    rec("PASS" if ck and (ref_page is None or ck >= ref_page) else "FAIL", "checklist in PDF after references", f"page {ck}")
    if ck:
        ctext = "\n".join(pages[ck - 1:])
        qs = len(re.findall(r"Question:", ctext)); ans = len(re.findall(r"Answer:\s*\[(Yes|No|N/A)\]", ctext))
        rec("PASS" if qs == N_QUESTIONS and ans == N_QUESTIONS else "FAIL", "checklist: %d questions answered" % N_QUESTIONS, f"questions={qs} answered={ans}")
        rec("PASS" if "[TODO]" not in ctext and "TODO" not in ctext else "FAIL", "checklist has no TODO")
        rec("PASS" if "Delete this instruction block" not in ctext and "BEGIN INSTRUCTIONS" not in ctext and "IMPORTANT, please" not in ctext else "FAIL", "checklist instruction block removed")
    cl = pdir / "checklist.tex"
    if cl.exists():
        t = cl.read_text(errors="replace")
        qtext = re.findall(r"Question:(.*)", t)
        rec("PASS" if "answerTODO" not in t and "justificationTODO" not in t else "FAIL", "checklist.tex answered")
        rec("PASS" if len(qtext) == N_QUESTIONS else "FAIL", "checklist.tex question count", str(len(qtext)))
    # anonymity heuristics
    full = "\n".join(pages)
    hits = []
    if re.search(r"github\.com|gitlab|huggingface\.co/[^/\s]+/|forgejo", src + full, re.I): hits.append("public/forge URL")
    if re.search(r"Acknowledg", full) : hits.append("Acknowledgments text")
    if re.search(r"\\author\{(?!Anonymous)", src): hits.append("named \\author")
    rec("PASS" if not hits else "WARN", "anonymity heuristics (links, acknowledgments, authors)", ",".join(hits) or "none found")
    # fonts / citations
    fonts = sh("pdffonts", str(pdf)).splitlines()[2:]
    nonemb = [f for f in fonts if f.split() and f.split()[-5] == "no"] if fonts else []
    rec("PASS" if not nonemb else "FAIL", "all fonts embedded", f"{len(fonts)} fonts")
    log = pdir / f"{stem}.log"
    if log.exists():
        lt = log.read_text(errors="replace")
        und = len(re.findall(r"(Citation|Reference) `[^']*' .*undefined", lt))
        rec("PASS" if not und else "FAIL", "no undefined citations/references", str(und))
        ov = len(re.findall(r"Overfull \\hbox \((\d+)", lt))
        rec("PASS" if not ov else "WARN", "overfull hboxes", str(ov))
    # reproduction document
    if repro:
        r = Path(repro)
        if not r.exists():
            rec("FAIL", "reproduction document present", repro)
        else:
            t = r.read_text(errors="replace").lower()
            need = {"environment/versions": r"python.*\d|requirements|lock", "data steps/version": r"data.*(version|download|checksum|sha)|ppi-python",
                    "random seeds": r"seed", "run commands": r"```|\bmake\b|python3? ", "expected runtime": r"(hour|minute|runtime|wall)",
                    "figure/table -> script map": r"(figure|fig\.|table).*(script|\.py)|(script|\.py).*(figure|table)",
                    "forbidden-content disclosure": r"(forbidden|not to access|prohibited|disclos|encounter)"}
            for k, rx in need.items():
                rec("PASS" if re.search(rx, t) else "FAIL", f"repro doc covers {k}")
    print()
    nf = sum(1 for l, *_ in res if l == "FAIL"); nw = sum(1 for l, *_ in res if l == "WARN")
    print(f"{nf} FAIL, {nw} WARN, {sum(1 for l,*_ in res if l=='PASS')} PASS"); return nf

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    sys.exit(1 if main(*sys.argv[1:5]) else 0)
