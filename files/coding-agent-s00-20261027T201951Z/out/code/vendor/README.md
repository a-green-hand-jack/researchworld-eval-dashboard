# Official template provenance

Source: https://github.com/ICLR/Master-Template

Archive: https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2026.zip

The official ICLR 2026 archive is included as downloaded. Extracted `.sty` and `.bst` files are unmodified. The manuscript uses `iclr2026_conference.sty` with its standard layout. In `paper.tex`, after `\maketitle`, the running header is changed to state that this is an empirical report rather than a conference submission; no acceptance or submission is claimed.

Build with `TEXINPUTS="$PWD/vendor:" pdflatex paper.tex` from the project root. The trailing colon retains the system TeX search path.
