# figtab-repo — figures and tables

Presentation position. Generators are in `figures/src/` (shared style `style.py`); they read result files of `experiment-repo` (path passed as argument) and write vector PDF + PNG + a `.json` sidecar (arguments, input SHA-256, plotted counts) into `figures/` and LaTeX tables into `tables/`.
The output -> command -> input -> claim table is `figures/MANIFEST.md`; caption stubs (to paste verbatim) are `figures/CAPTIONS.md` and `tables/CAPTIONS.md`; table inputs are hashed in `tables/MANIFEST.json`.
Commitment: issue #2.
