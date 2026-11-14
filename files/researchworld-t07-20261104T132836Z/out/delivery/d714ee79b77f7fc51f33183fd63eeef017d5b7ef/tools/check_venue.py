#!/usr/bin/env python3
"""Check a built paper against the NeurIPS 2026 main-track format rules we can verify mechanically.

usage: check_venue.py PAPER.pdf [MAIN.tex] [--max-content-pages 9]

Checks (each prints PASS/FAIL/WARN; exit status 1 if any FAIL):
  * page size is US letter;
  * the main text ends within the content-page limit (the page where the first
    "References" / "Acknowledgments" / "Appendix" / "NeurIPS Paper Checklist" heading
    starts is the last content page; a heading at the very top of page limit+1 is accepted);
  * the "NeurIPS Paper Checklist" section is present and comes after the references;
  * no template placeholders (\\answerTODO / \\justificationTODO) remain, and the checklist
    instruction block is gone (needs MAIN.tex and its \\input files);
  * the .tex loads neurips_2026 with the default/main option only (no final, preprint, nonanonymous),
    which keeps the submission anonymous with line numbers;
  * the required sections exist (abstract, introduction, related work, method, experiments,
    discussion/limitations, references).
It does NOT judge content; it cannot see margin/font tampering beyond reading the style file hash
(see template/SHA256SUMS).
"""
import re, sys, pathlib
import pymupdf as fitz  # PyMuPDF

HEAD = re.compile(r"^\s*(?:\d+(?:\.\d+)*\s+|[A-Z]\s+)?(references|acknowledg(?:e)?ments?|appendix|appendices|"
                  r"technical appendices.*|neurips paper checklist)\s*$", re.I)
SECTIONS = {
    "abstract": r"abstract",
    "introduction": r"introduction",
    "related work": r"related\s+work|background",
    "method": r"method|approach|setting|protocol",
    "experiments": r"experiment|results|evaluation",
    "discussion/limitations": r"limitation|discussion",
    "references": r"references",
}

def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    limit = 9
    if "--max-content-pages" in argv:
        limit = int(argv[argv.index("--max-content-pages") + 1])
        args = [a for a in args if a != str(limit)]
    pdf = pathlib.Path(args[0])
    tex = pathlib.Path(args[1]) if len(args) > 1 else None
    fails = 0
    def rep(ok, msg, warn=False):
        nonlocal fails
        tag = "PASS" if ok else ("WARN" if warn else "FAIL")
        fails += (not ok and not warn)
        print(f"{tag}  {msg}")

    doc = fitz.open(pdf)
    w, h = doc[0].rect.width, doc[0].rect.height
    rep(abs(w - 612) < 2 and abs(h - 792) < 2, f"page size {w:.0f}x{h:.0f} pt (US letter = 612x792)")

    first_end = None   # (page, y) of first end-of-main-text heading
    checklist_page = None
    last_ref_page = None
    texts = []
    for pno, page in enumerate(doc, 1):
        texts.append(page.get_text())
        for b in page.get_text("blocks"):
            # the anonymous style prints review line numbers as bare-digit lines; drop them
            line = " ".join(l.strip() for l in b[4].splitlines() if l.strip() and not l.strip().isdigit())
            if HEAD.match(line):
                kind = line.lower()
                if first_end is None and not kind.startswith("neurips paper"):
                    first_end = (pno, b[1])
                if "references" in kind:
                    last_ref_page = pno
                if kind.startswith("neurips paper checklist"):
                    checklist_page = checklist_page or pno
    n = len(doc)
    if first_end is None:
        rep(False, f"no References/Appendix/Checklist heading found; {n} pages total, cannot tell where main text ends")
    else:
        p, y = first_end
        ok = p <= limit or (p == limit + 1 and y < 110)
        rep(ok, f"main text ends on page {p} (heading at y={y:.0f}); limit {limit} content pages; total {n} pages")
    rep(checklist_page is not None, "'NeurIPS Paper Checklist' section present"
        + (f" (page {checklist_page})" if checklist_page else ""))
    if checklist_page and last_ref_page:
        rep(checklist_page >= last_ref_page, "checklist comes after the references")
    full = "\n".join(texts)
    for name, pat in SECTIONS.items():
        found = re.search(rf"^\s*(?:\d+(?:\.\d+)*\s+)?(?:{pat})", full, re.I | re.M)
        rep(bool(found), f"section/heading '{name}' found in PDF text", warn=True)
    if re.search(r"TODO", full):
        rep(False, "the literal text 'TODO' appears in the PDF (unanswered checklist item?)")

    if tex:
        src = tex.read_text(errors="replace")
        base = tex.parent
        def inline(s, depth=0):
            def sub(m):
                f = base / (m.group(1) if m.group(1).endswith(".tex") else m.group(1) + ".tex")
                return inline(f.read_text(errors="replace"), depth + 1) if f.exists() and depth < 5 else m.group(0)
            return re.sub(r"\\(?:input|include)\{([^}]+)\}", sub, s)
        full_src = inline(src)
        nocomment = "\n".join(re.sub(r"(?<!\\)%.*", "", l) for l in full_src.splitlines())
        m = re.search(r"\\usepackage(?:\[([^\]]*)\])?\{neurips_2026\}", nocomment)
        rep(bool(m), "\\usepackage{neurips_2026} present")
        if m:
            opts = {o.strip() for o in (m.group(1) or "").split(",") if o.strip()}
            bad = opts & {"final", "preprint", "nonanonymous", "eandd", "position", "creativeai",
                          "education", "sglblindworkshop", "dblblindworkshop"}
            rep(not bad, f"style options {sorted(opts) or 'default'} are the anonymous main-track submission mode"
                + (f" (not allowed: {sorted(bad)})" if bad else ""))
        rep("answerTODO" not in nocomment and "justificationTODO" not in nocomment,
            "no \\answerTODO / \\justificationTODO left in the checklist")
        rep("BEGIN INSTRUCTIONS" not in full_src, "checklist instruction block deleted")
        rep("NeurIPS Paper Checklist" in full_src, "checklist section heading kept in the source")
    print("RESULT:", "FAIL" if fails else "OK")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
