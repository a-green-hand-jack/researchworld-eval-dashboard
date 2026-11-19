import pymupdf, sys
d = pymupdf.open("main.pdf")
print(len(d), "pages")
for i in [int(x) for x in sys.argv[1:]]:
    d[i].get_pixmap(dpi=80).save(f"page{i}.png")
