#!/usr/bin/env python3
"""Check a built paper PDF against the NeurIPS 2026 main-track format rules.

Usage: python3 -I tools/check_pdf.py paper.pdf

Reports: total pages, the page on which the reference list starts (main text
must end on or before page 9, i.e. the content pages are those before the
"References" heading page, counting that page's content above the heading),
presence of the "NeurIPS Paper Checklist" heading, leftover [TODO] answers,
and whether the author block is anonymous. Exit status 1 on a failed check.
"""
import re
import sys
import pymupdf as fitz  # PyMuPDF

MAX_CONTENT_PAGES = 9


def main(path):
    doc = fitz.open(path)
    texts = [p.get_text() for p in doc]
    ok = True
    print(f"pages total: {len(doc)}")
    ref = next((i for i, t in enumerate(texts) if re.search(r"^\s*(References|Bibliography)\s*$", t, re.M)), None)
    chk = next((i for i, t in enumerate(texts) if "NeurIPS Paper Checklist" in t), None)
    if ref is None:
        print("FAIL: no 'References' heading found"); ok = False
    else:
        # main text ends on the page holding the heading; it fits if that page <= 9
        print(f"references start on page {ref + 1} (limit: main text on pages 1-{MAX_CONTENT_PAGES}; "
              "a reference list starting on page 10 is allowed only if page 9 is full of content)")
        if ref + 1 > MAX_CONTENT_PAGES + 1:
            print("FAIL: main text runs past page 9"); ok = False
        elif ref + 1 == MAX_CONTENT_PAGES + 1:
            print("WARN: references begin on page 10; confirm no content (incl. ack/limitations) sits there")
    if chk is None:
        print("FAIL: checklist heading not found (papers without it are desk rejected)"); ok = False
    else:
        print(f"checklist starts on page {chk + 1}")
        if ref is not None and chk < ref:
            print("FAIL: checklist precedes references"); ok = False
    if any("[TODO]" in t for t in texts):
        print("FAIL: unanswered [TODO] in checklist/text"); ok = False
    first = texts[0] if texts else ""
    if re.search(r"Anonymous Author", first):
        print("author block: anonymous (submission mode)")
    else:
        print("WARN: author block not 'Anonymous Author(s)' -- fine only for preprint/final option")
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
