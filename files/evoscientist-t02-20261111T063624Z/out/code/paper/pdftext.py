import pymupdf, sys
d = pymupdf.open("main.pdf")
for i, p in enumerate(d):
    t = p.get_text()
    flags = [k for k in ("References", "Conclusion", "Reproduction map", "NeurIPS Paper Checklist") if k in t]
    print(i + 1, flags, len(t))
if len(sys.argv) > 1:
    for i in sys.argv[1:]:
        print("=" * 30, i)
        print(d[int(i) - 1].get_text())
