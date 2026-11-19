# figtab: figures and tables of the paper

Generators and their outputs. `figstyle.py` fixes the ICML 2027 widths (3.25 in / 6.75 in) and the 7 pt minimum type size;
`common.py` loads `../results/` and holds the two-level cluster bootstrap (seeds, then instances) and Clopper–Pearson intervals.
`provenance.md` maps every item to its script, inputs and claim. `make_all.sh` rebuilds all, and fails on a Type 3 font.
`--pilot` uses `*_test` / `pilot` result files and writes to the git-ignored `_pilot/`: layout tests only, never delivered.

State: Tier-1 results are final in `../results/`; Fig 1(a, c), Fig 3, Fig 4, Tables 1-2 and the appendix items are built on them.
Fig 1(b) (d-curve, d<=20 complete; d>20 Arrhythmia not drawn) and Fig 2 (yardstick, German MLP/GBDT missing) are built on inputs STATUS.md still calls preliminary, flagged in `provenance.md`. `figA_c5_split` reads `c5_split_R20.csv`.
`captions.md` has caption text per item, with what each caption's numbers are read from.
