# figtab-repo — figures and tables

Presentation position. Generators in `figures/src/` read result files of `experiment-repo` (the `results/` directory is passed as argument) and write
vector PDF + PNG + a JSON sidecar (arguments, input SHA-256, plotted cell values) into `figures/` and LaTeX tables into `tables/`.
`sh figures/src/run_all.sh RESULTS_DIR` regenerates everything. Output -> command -> input -> claim: `figures/MANIFEST.md`; caption stubs: `figures/CAPTIONS.md`, `tables/CAPTIONS.md`.
Delivered into `paper-repo` by pull request on `figures/` and `tables/`. Commitment: issue #2.
