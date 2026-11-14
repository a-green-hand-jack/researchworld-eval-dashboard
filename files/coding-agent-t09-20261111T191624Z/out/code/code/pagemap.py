import sys
from pypdf import PdfReader
r = PdfReader(sys.argv[1])
for i, p in enumerate(r.pages, 1):
    t = p.extract_text() or ""
    heads = [l for l in t.split("\n") if l[:2].strip().isdigit() and len(l) < 80][:4]
    print(i, len(t), "References" in t[:300] or "NeurIPS Paper Checklist" in t[:200], t[:60].replace("\n", " | "))
