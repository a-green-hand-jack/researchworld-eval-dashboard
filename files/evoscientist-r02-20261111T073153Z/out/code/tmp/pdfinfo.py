import fitz, sys
d = fitz.open("paper/main.pdf")
print("pages", len(d))
for i, p in enumerate(d):
    t = p.get_text()
    heads = [l for l in t.split("\n") if l.strip().startswith(("Impact Statement","References","A. Proofs","1. Introduction","6. Results","7. Discussion","Checklist"))]
    print(i + 1, len(t), heads[:3])
if len(sys.argv) > 1:
    for i in map(int, sys.argv[1:]):
        d[i - 1].get_pixmap(dpi=80).save(f"tmp/page{i}.png")
