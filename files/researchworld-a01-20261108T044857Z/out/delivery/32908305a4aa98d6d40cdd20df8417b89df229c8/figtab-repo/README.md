# figtab-repo — figures and tables

Presentation position. Generators in `figures/src/` read the result files of `experiment-repo` (the `results/` directory, passed as the first argument)
and write vector PDF + PNG + a `.json` sidecar (arguments, SHA-256 of every input, plotted cell counts) into `figures/`, LaTeX tables into `tables/`.
`figures/MANIFEST.md` maps each output to its command, inputs and claim; `figures/CAPTIONS.md` and `tables/CAPTIONS.md` hold the caption stubs.
Shared style (Okabe-Ito colour per rule, fonts, rank bins with bootstrap CI over targets): `figures/src/style.py`. Commitment: issue #2.
