# Build the paper: `make -C paper` (requires pdflatex + bibtex); output main.pdf
main.pdf: main.tex references.bib $(wildcard sections/*.tex) checklist.tex
	latexmk -pdf -interaction=nonstopmode main.tex
clean:
	latexmk -C main.tex
