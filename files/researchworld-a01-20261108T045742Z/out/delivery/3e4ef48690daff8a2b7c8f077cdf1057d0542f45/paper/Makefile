# Build paper/main.pdf with the unmodified ICLR 2027 style files from ../venue/iclr2027.
# Run `make -C paper`, then copy to ../paper.pdf (make install).
export TEXINPUTS := ../venue/iclr2027:$(TEXINPUTS)
export BSTINPUTS := ../venue/iclr2027:$(BSTINPUTS)
export BIBINPUTS := .:$(BIBINPUTS)
.PHONY: all install check clean
all: main.pdf
main.pdf: main.tex refs.bib $(wildcard sections/*.tex)
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
install: main.pdf
	cp main.pdf ../paper.pdf
check: main.pdf
	python3 -I ../venue/check_format.py main.pdf main.tex
clean:
	latexmk -C
