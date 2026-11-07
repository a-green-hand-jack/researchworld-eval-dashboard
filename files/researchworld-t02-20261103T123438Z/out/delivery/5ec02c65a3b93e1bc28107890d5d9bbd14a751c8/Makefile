.PHONY: paper audit inventory clean

# Keep the official style unchanged and use TeX's normal paths (trailing colon).
export TEXINPUTS := $(CURDIR)/venue/official:

paper:
	@test -f venue/official/neurips_2026.sty || { echo 'Missing venue-owner template delivery: venue/official/neurips_2026.sty'; exit 1; }
	@test -f manuscript/main.tex || { echo 'Missing integrated manuscript: manuscript/main.tex'; exit 1; }
	mkdir -p build/latex
	latexmk -pdf -cd -interaction=nonstopmode -halt-on-error -outdir=$(CURDIR)/build/latex $(CURDIR)/manuscript/main.tex
	cp build/latex/main.pdf paper.pdf

# Technical document checks; independent scientific review remains necessary.
audit:
	python3 build/audit_pdf.py --pdf paper.pdf --output build/pdf-audit.json
	python3 build/audit_checklist.py --checklist manuscript/checklist.tex --output build/checklist-audit.json

inventory: paper
	python3 build/inventory_document.py

clean:
	@if test -f manuscript/main.tex; then latexmk -C -cd -outdir=$(CURDIR)/build/latex $(CURDIR)/manuscript/main.tex; fi
