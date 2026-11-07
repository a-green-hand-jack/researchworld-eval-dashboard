TEX=pdflatex
all: main.pdf
main.pdf: main.tex appendix.tex checklist_filled.tex references.bib $(wildcard tables/*.tex) $(wildcard figures/*.pdf)
	$(TEX) -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	$(TEX) -interaction=nonstopmode -halt-on-error main.tex
	$(TEX) -interaction=nonstopmode -halt-on-error main.tex
	cp main.pdf ../paper.pdf
clean:
	rm -f main.aux main.bbl main.blg main.log main.out main.toc
.PHONY: all clean
