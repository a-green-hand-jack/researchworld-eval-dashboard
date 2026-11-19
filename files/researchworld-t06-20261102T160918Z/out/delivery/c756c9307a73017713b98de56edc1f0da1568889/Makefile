.PHONY: paper clean
paper:
	mkdir -p build
	TEXINPUTS=.:venue//: BIBINPUTS=.:venue//: BSTINPUTS=.:venue//: latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build paper.tex
	cp build/paper.pdf paper.pdf
clean:
	latexmk -C -outdir=build paper.tex
