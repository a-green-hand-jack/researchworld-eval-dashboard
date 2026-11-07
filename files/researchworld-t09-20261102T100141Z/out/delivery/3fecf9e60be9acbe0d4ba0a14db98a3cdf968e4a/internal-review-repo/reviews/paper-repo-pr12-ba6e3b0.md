# Review record: paper-repo PR #12 (into `final`), head ba6e3b01572b — approved

Inspected at the head, from a clone of paper-repo.

- Format: `venue/check_format.py paper.pdf paper/main.tex` PASS (29 pages, main text ends on p. 9, checklist last). Independent pdflatex/bibtex rebuild: 0 undefined references; text identical to shipped `paper.pdf`.
- Numbers: `paper/scripts/make_numbers.py` regenerates `paper/numbers.tex` byte-identically. The new `Rd*` macros match `results/realdraws_summary.csv` / `realdraws_perdraw.csv` (ego-Facebook M1 Bernoulli(0.5) OLS(z,f): mean 0.43, range 0.27–0.65, DM 0.50; Stanford3 0.12, 0.09–0.16; wins out of 32 draw×mechanism pairs: Stanford3 32 / 31 / 15 (p=0.5, 0.1, cluster), ego-Facebook 21 / 1 / 10).
- Reproducibility: `check_cell.py MAIN 'er|M1|bern0.5'` re-run at this head: 4000 rows, 0 differ (IDENTICAL). `MAIN_realdraws` is defined in `experiments.py`, in the README experiment table, the run command and the MANIFEST (24 cells, 8 draws × 60 assignments).
- Figures: `figures/paper_numbers.py` map now keyed to paper figure numbers (Fig. 1–23, Tables 1–4) with the include widths the paper uses (finding A resolved). Opened Fig. 1 / Table 1 and the pages with Figs. 2, 3, 4, 5 in the built PDF: axes, legends and tick labels are legible at print size, none blank or unlabelled (finding H resolved).
- Claims: the real-graph statements in Sec. 4.4 now rest on 8 independent baseline draws, disclose that ego-Facebook depends on the baseline draw and that cluster randomisation is 15/32 (Stanford3) and 10/32 (ego-Facebook); the discussion states the one-graph limitation; the not-completed ridge/GBM full-grid run (MAINML) is disclosed as not completed.

Earlier findings B, C, D (paper and experiment side), E, F, G, A, H: all resolved. 

Non-blocking remarks (no action required for approval): "Stanford3 favours regression robustly" is a Bernoulli-design statement (cluster design is 15/32, reported in the same sentence); the 32-pair counts mix 4 mechanisms × 8 draws and are descriptive, not a test.

Conclusion: the version meets the objective and the commitment standard (#2). Approved.
