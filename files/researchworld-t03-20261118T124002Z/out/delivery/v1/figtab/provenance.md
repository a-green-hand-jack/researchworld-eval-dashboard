# Provenance of delivered figures and tables

Regenerate everything: `sh make_all.sh` (reads `../results/`, or `$FIGTAB_RESULTS`; ~10 min on 2 CPUs on a loaded host, dominated by the cluster bootstraps).
Each item has a `.json` beside it with the input files and the figtab commit that produced it (some also carry the numbers drawn). Placed width is the width the
generator draws at: include with no scaling (`\includegraphics{...}` without `width=`/`scale=`). Text in every PDF is >= 7 pt at that width
(checked with PyMuPDF; sub- and superscripts are drawn at full size) and no PDF has a Type 3 font (`make_all.sh` fails if one appears).

| item | claim (story id) | placed | script | inputs | state of the inputs |
|---|---|---|---|---|---|
| `fig1_tail.pdf` | C1 tail + d: (a) per-instance r_3 ECDF at the default, exact and eps=0.10-tolerant; (b) reliable fraction vs d; (c) r_3 vs z, true and plug-in | `figure*` 6.75 in | `fig1_tail.py` | `tidy_*_R20.csv`, `plugz_*_R20.npz` | (a), (c) final (Tier 1); **(b) uses the d=8,12 subsets (all cells present now), which STATUS.md still calls preliminary**; Arrhythmia margin-scale cells not drawn |
| `fig2_yardstick.pdf` | C3: rerun vs background vs retrain disagreement, shares of instances | `figure` 3.25 in | `fig2_yardstick.py` | `yardstick_R20.csv` | **partial**: ACS LR/MLP/GBDT and German LR (4 of 6 cells, 30 instances, seed 0); German MLP/GBDT still running. Rebuild before use |
| `fig2_yardstick_perm.pdf` | appendix: same for Permutation | `figure` | `fig2_yardstick.py --perm` | same | same |
| `fig3_certificates.pdf` | C4: (a, b) P(exact \| certified) vs nominal, k=3, 5; (c) certified share vs the oracle | `figure*` 6.75 in | `fig3_certificates.py` | `certificate_coverage.csv`, `oracle_tightness.csv` | final (Tier 1); (c) is the stratified R~200 subset, s0 cells |
| `figA_calibration_k135.pdf` | appendix: calibration for k=1,3,5 | `figure*` | `fig3_certificates.py --appendix` | `certificate_coverage.csv` | final |
| `figA_c5_split.pdf` | appendix, C5: what the unreliable instances of the shipped default are made of (truncation bias / bias under both / noise split at gap vs SD) | `figure` | `figA_c5_split.py` | `c5_split_R20.csv` | final for the six main groups; the file is on experiment-repo's `main`, not yet on `dev` |
| `figA_ecdf_x16.pdf` | appendix, C1: the x16 half of the old Fig 1(a): exact r_3 ECDF at x1 and x16 | `figure` | `figA_ecdf_x16.py` | `tidy_*_R20.csv` | final |
| `fig4_budget.pdf` | C2/S4: reliable fraction vs budget, per explainer, shipped defaults marked | `figure` 3.25 in | `fig4_budget.py` | `tidy_*_R20.csv` | final |
| `figA_budget_by_model.pdf` | appendix version of Fig 4, one panel per dataset x model | `figure*` | `fig4_budget.py --by-model` | same | final |
| `figA_bstar.pdf` | appendix, C2: predicted vs empirical B*(x), Covert-Lee, k=3, delta=0.1 | `figure` | `figA_bstar.py` | `instances_R20.csv` | final (Tier 1 cells; the d-curve subsets are left out) |
| `tab1_reliable_fraction.tex` | C1 + C5: per dataset x model x explainer, F_3 and eps-tolerant F_3, mean r_3 (exact and eps-tolerant), Nogueira, bias share | `table*`, `\small` | `tab1_reliable_fraction.py` | `tidy_*_R20.csv` | final |
| `tab2_certificates.tex` | C4: price of certification: certificate, oracle, cost at equal reliability (range over the 6 cells, k=3, delta=0.1) | `table*`, `\small` | `tab2_certificates.py` | `certificate_coverage.csv`, `oracle_tightness.csv`, `cost_at_equal_reliability.csv` | final; the oracle block is from the stratified subset (30 instances per s0 cell), not a population rate |
| `tabA_certificates.tex` | appendix, C4: the per-cell values behind Table 2 (one row per dataset x model x rule) | appendix table | `tabA_certificates.py` | `certificate_coverage.csv`, `cost_at_equal_reliability.csv` | final |

Tables are tabular bodies only (no `table*`, caption or font size; Table 1 sets its own `\tabcolsep` in a group to fit 6.75 in): the paper places them and sets `\small`. Both were checked to fit 6.75 in at `\small` in the ICML 2027 style.
`captions.md` holds the caption text of each item and what each caption's numbers are read from.

Not built, and why:
- C5 three-way split (truncation bias / selection instability / sampling variance): `bias_variance_R20.csv` has only the bias share, which Table 1 carries; a by-d figure of it was drawn and dropped (the d=8,12 cells have 0-14 unreliable instances, so the intervals are uninformative). The three-way split needs a result file from `experiment-repo` (asked in `experiment-repo`#4).
- E7 (global-importance control), `cells_not_run.csv` marking, k/eps/delta sensitivity: result files exist for E7 (`e7_controls.csv`); no item is built yet because no main-text claim carries it; it is one sentence of text.

**Do not copy numbers from a figure into text; read them from the `.json` or the result files.** Items marked partial/preliminary above are rebuilt by `make_all.sh` once `results/STATUS.md` declares them final.
