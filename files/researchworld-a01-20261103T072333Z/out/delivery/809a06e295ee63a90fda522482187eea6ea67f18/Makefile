.PHONY: paper clean
paper:
	TEXINPUTS=.:venue/official//: latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex

clean:
	latexmk -c paper.tex
