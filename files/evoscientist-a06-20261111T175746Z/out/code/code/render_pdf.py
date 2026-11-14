import sys, pypdfium2 as pdfium
pdf = pdfium.PdfDocument("paper/main.pdf")
print("pages", len(pdf))
for i in [int(x) for x in sys.argv[1:]]:
    pdf[i].render(scale=1.3).to_pil().save(f"results/page{i+1}.png")
