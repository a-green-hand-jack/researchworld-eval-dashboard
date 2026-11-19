# Build paper.pdf at the repository root: make -C paper
# The official ICLR 2027 style files live in ../venue/iclr2027 (copied unchanged from the organisers' zip).
export TEXINPUTS := ../venue/iclr2027:../figures/out:
export BIBINPUTS := ../venue/iclr2027:.:
export BSTINPUTS := ../venue/iclr2027:
all:
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	cp main.pdf ../paper.pdf
clean:
	latexmk -C main.tex
