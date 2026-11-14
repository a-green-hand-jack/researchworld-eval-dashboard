# Build the paper with the ICLR 2027 style files delivered by venue-repo (../venue/iclr2027).
# usage: make   (writes main.pdf)
export TEXINPUTS := ../venue/iclr2027//:$(TEXINPUTS)
export BSTINPUTS := ../venue/iclr2027//:$(BSTINPUTS)
main.pdf: main.tex refs.bib sections/*.tex ../tables/*.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
clean:
	latexmk -C
