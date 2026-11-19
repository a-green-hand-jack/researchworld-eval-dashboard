# figtab-repo — figures and tables

Presentation position. Generators are in `figures/src/` (shared style `style.py`); they read the result files of `experiment-repo`
(`results/`, path passed as argument) and write vector PDF + PNG + a JSON sidecar (arguments, input SHA-256, plotted counts) into
`figures/`, and LaTeX tables into `tables/`.

`figures/MANIFEST.md` — output -> command -> input files -> claim supported. `figures/CAPTIONS.md`, `tables/CAPTIONS.md` — caption stubs.
Commitment: issue #2. Nothing is computed beyond display statistics (bin medians with bootstrap-over-targets CIs, Wilson intervals).
