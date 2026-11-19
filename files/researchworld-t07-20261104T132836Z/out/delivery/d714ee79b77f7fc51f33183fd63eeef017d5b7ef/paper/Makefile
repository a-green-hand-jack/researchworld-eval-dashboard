# Build paper/main.pdf from LaTeX sources (needs TeX Live: latexmk, bibtex).
# Intermediate files go to paper/build/ (ignored by git); the PDF is copied to paper/main.pdf.
all: main.pdf

main.pdf: main.tex checklist.tex refs.bib $(wildcard sections/*.tex) $(wildcard figures/*) $(wildcard tables/*)
	latexmk -pdf -interaction=nonstopmode -outdir=build main.tex
	cp build/main.pdf main.pdf

check: main.pdf
	python3 ../tools/check_venue.py main.pdf main.tex

clean:
	rm -rf build main.pdf
