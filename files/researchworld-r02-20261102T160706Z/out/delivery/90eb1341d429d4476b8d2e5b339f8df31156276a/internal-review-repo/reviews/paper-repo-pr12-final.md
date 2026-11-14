# Review record: paper-repo#12 (main -> final), head 50dfe99f04a6d10e717911e1c22bdfe5f4855a3a

Checked against the commitment in `internal-review-repo`#2, the objective, `idea-repo` Brief/Conventions and `venue-repo`'s VENUE.md. Status `hutian/delivery`: success.

## Inspected
- `paper.pdf` (22 pp; identical bytes to `paper/main.pdf`); main text ends on p. 9 (NeurIPS 2026 limit: 9), references p. 10, appendix, filled NeurIPS checklist (all 16 items answered with justification). Clean LaTeX rebuild of `paper/main.tex` (out-of-tree) gives 22 pp.
- All main-text figures (Fig 1-4) and Table 1 opened as rendered; Fig 2 and Fig 3 also at vector resolution; appendix pages (Figs 5-9, Tables 2-7, reproduction notes, checklist) paged through. Labelled axes, legends, null bands present; no blank or placeholder exhibit.
- Numbers re-derived from the committed CSVs: paired geometric-mean pool_frac ratios of Sec 4.3 (Aitchison/L2 2.45/1.98/1.45 for Dirichlet K=3/5/10, 0.90 rounded K=10; Dirichlet-NLL 0.82/0.67/0.62; KL 0.88/0.80/0.70; Hellinger 0.93/0.87/0.75; L_inf 1.19/1.44; normalised KL 0.57/0.32), the null-simulation values (ymax_gap 0.034 sd 0.013; wsc 0.90 sd 0.03; or_gap 0.016 sd 0.005), Beta-law KS counts (3 of 24 below 0.05), the CIFAR-10H ranges (coverage 0.900-0.906, mass 0.103-0.118, normalised 0.32-0.56, worst confidence bin 0.63-0.75). All match.
- Reproducibility: `scripts/aggregate.py` run on the committed raw CSVs reproduces every `results/*_summary.csv` byte for byte (git clean); `run_e1.py --reps 2` reproduces reps 0-1 of the committed `main_dirichlet_D5_h1_linear.csv` exactly (cov10, or_gap, pool_frac, wsc, difference 0.0). REPRODUCE.md gives versions, data sources/revisions/licence status, seeds, commands, runtimes, exhibit->script map, deviations and failed runs, and the (empty) forbidden-material statement. I did not re-run the multi-hour grids.
- Theory: Prop 1 (Beta(k, n+1-k)), Prop 2 (vertex labels: TV = 1-p_j, Hellinger^2 = 2-2sqrt(p_j), KL = -log p_j) and the Hellinger flat-coverage statement of the delta method are correct as derived; the Aitchison failure is reported rather than hidden.
- Citations spot-checked: Principato et al. arXiv:2411.13479 exists with the stated title.

## Conclusion
Supported: the claims are conditional, scoped to the tested designs, with CIs over 100 replicates, a null calibration of the binned metrics, an oracle conditional-coverage measure, negative results (Aitchison theory failure, Mondrian at n=30, CV+ limited) and limitations stated. Novelty is honestly modest (no new guarantee claimed). Approved.

## Non-blocking observations (not acted on by me; for a later round if one exists)
1. Fig 3 (five rows x four columns) has very small tick/axis text at page size; legible only when zoomed. A larger layout or fewer rows in the main text would help.
2. Sec 4.3 says mean coverage "0.896-0.909"; the committed means reach 0.9099 (`results/README.md` says 0.910).
3. The venue rule that critical evidence be in the main text: the n_cal sweep (Fig 7), eps sensitivity (Fig 6), delta-method (Fig 8), shift (Fig 9) and CIFAR-10H (Table 6) are shown only in the appendix, with their numbers quoted in the text.
4. Single regression function per configuration (disclosed in Sec 5): the intervals do not cover variation over it. The CIFAR-10H worst-bin coverage is compared with a null computed at n_test=2000, a conservative comparison.
