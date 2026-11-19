.PHONY: paper figures analysis check clean

paper:
	TEXINPUTS="$(CURDIR):$(CURDIR)/venue/templates//:" BIBINPUTS="$(CURDIR):" BSTINPUTS="$(CURDIR)/venue/templates//:" latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=paper paper/main.tex
	cp paper/main.pdf report.pdf

figures:
	python3 presentation/generate.py

analysis:
	cd analysis && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/reproduce.py --prepared

check:
	python3 paper/check_delivery.py

clean:
	latexmk -c -outdir=paper paper/main.tex
