# figtab-repo — figures and tables

Presentation position. Generators live in `figures/src/` (shared style `style.py`); they read the result files of `experiment-repo`
(`results/`, path passed as argument) and write vector PDF + PNG + a provenance `.json` (input SHA-256, cell counts) into `figures/`
and LaTeX tables into `tables/`. `sh figures/src/make_all.sh RESULTS_DIR` regenerates everything; `figures/MANIFEST.md` maps every
output to its command, inputs and the claim it supports; `figures/CAPTIONS.md` and `tables/CAPTIONS.md` hold caption stubs.
Only display statistics are computed here (bin medians with bootstrap-over-targets bands, Wilson intervals). Commitment: issue #2.

Last built against experiment-repo `9f74808` (`core_*.csv` unchanged since `22c9566`).
