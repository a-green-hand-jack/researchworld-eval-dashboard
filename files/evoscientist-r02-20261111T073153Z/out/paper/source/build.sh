# build the paper (run from the paper directory): pdflatex + bibtex
pdflatex -interaction=nonstopmode main.tex > build.log 2>&1
bibtex main > bibtex.log 2>&1
pdflatex -interaction=nonstopmode main.tex >> build.log 2>&1
pdflatex -interaction=nonstopmode main.tex >> build.log 2>&1
