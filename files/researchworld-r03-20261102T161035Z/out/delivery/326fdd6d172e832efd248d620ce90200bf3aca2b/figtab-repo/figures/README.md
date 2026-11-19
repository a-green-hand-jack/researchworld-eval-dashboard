# figures/ and tables/ (owner: figtab-repo)
Delivered: `figures/fig*.pdf` (vector), `tables/tab_*.tex` (booktabs fragments, `\input` them), `tables/*.csv` (the numbers behind them), `figures/CAPTIONS.md` (what each item shows, caveats, suggested captions), `figures/preview/*.png` (raster previews only).
Generator: `figures/src/make_figs.py` (everything). Inputs and their provenance: `figures/inputs/` (`PROVENANCE.md`).
Basis: experiment-repo's common-target-set protocol (fixed targets across selectors and k; full-information reference). Figure width 5.5 in (ICLR text width), fonts 6.5-7.5 pt, one colour and marker per method across all figures.
Items: Fig. 1 data and spectrum; Fig. 2 main curves; Fig. 3 selector comparison; Fig. 4 inference methods; Fig. 5 distribution shift; Fig. 6 missing data and training size; Fig. 7 synthetic theory; Fig. 8 a+b/k fits on real curves; Tables data, main, k-needed. About five fit in the 9-page body (suggested: 1 or 2, 3, 4, 5, 8); the rest go to the appendix.
Open item: none known; the k-needed numbers for held-out organisations are poorly identified (see CAPTIONS.md).
