import sys, fitz
d = fitz.open(sys.argv[1]); print(len(d), 'pages')
for i in map(int, sys.argv[3:]):
    d[i - 1].get_pixmap(dpi=70).save(f'{sys.argv[2]}_{i}.png')
