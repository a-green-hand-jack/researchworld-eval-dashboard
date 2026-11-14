all: main.pdf

main.pdf: main.tex references.bib checklist.tex vendor/neurips_2026.sty $(wildcard generated/*.tex) $(wildcard ../figures/*.pdf)
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -c main.tex

.PHONY: all clean
