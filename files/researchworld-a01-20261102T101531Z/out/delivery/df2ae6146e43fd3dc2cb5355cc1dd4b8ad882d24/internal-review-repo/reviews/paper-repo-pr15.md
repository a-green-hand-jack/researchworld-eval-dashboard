# Review record: paper-repo PR #15 (into `final`), head acd3ed3339e194ce647233bb7cd1e043e8e7f28b

Judged against #1 (objective), #2 (my standard), `deliverable.md`, `data.md`. Commit status `hutian/delivery` = success.

## Inspected
- `paper/main.pdf` (10 pages: main text 8 pages incl. references start, appendix 2; ICLR 2027 style, anonymous). Rebuilt from `paper/main.tex` with pdflatex+bibtex: text identical to the delivered PDF, no undefined references.
- All 4 main-text figures, Table 1-6 and appendix opened as rendered pages: figures are labelled, legible, legends/axes present, and agree with the text (Fig. 1 vs Table 4/5, Fig. 2 vs C4 numbers, Fig. 3 vs `subsample_curves_summary.csv` values 2.3 -> 15, 0.465 -> 0.263, Fig. 4 vs C3).
- Numbers traced to `results/`: Table 2 vs `headline.csv` (HELM, OLB headline, OLB sub-task, mean/median/minimum cells), "median cheaper for 75 of 78 targets" vs `paired_stats.csv`, C3 monotone shares vs `power_mean_monotonicity.csv` (9%/15%, 98%/29%, 15%/37%), Table 3 vs `verification.csv` (3,900 real + 6,000 small, all match).
- Reproduction (own clone, job + sandbox): `code/fetch_data.sh` (9.5 min) fetched the snapshots; `15_manifest.py` regenerated `results/data_manifest.json` byte-identically (checksums of every used file match). `test_real.py`: 80 checked, 0 bad. `14_verification.py` reproduces `verification.csv` byte-identically. `09_per_target.py helm` and `olb_headline` reproduce all 77,760 rows: `k_min` and `feasible` identical in every row; `G_min` identical except the frontier upper bounds that `11_collect.py` fills in afterwards (expected).
- References: Faliszewski et al. 2009, Dominguez-Olmedo et al. 2024 checked to exist; the others are the starter list. Independence: no forbidden source used; one incidental title/abstract snippet is logged in Appendix B.

## Conclusion
Supported. The question (investment = breadth k and depth G, by rule, on two public boards) is answered with exact solvers, uncertainty, robustness and baselines; claims are conditional and negative results (C3, C5) are reported; limitations are candid; reproduction notes exist and the key results re-run.

## Minor findings (not blocking; none changes a claim)
1. `results/subsample_raw_helm.csv` (and derived `subsample_curves*.csv` G columns for the median) predate the median G_min fix: rerunning `12_subsample.py helm` gives identical `k_min` but different median `G_min` in 138 rows. The paper only uses k_min from these, but the committed file does not match the code.
2. Table 3 says "10 rules" while `verification.csv` has 15 rule specifications (9 families + 6 power means), and Sec. 3 says "400 random small instances" whereas Table 3/C1 count 6,000 checks (15 x 400); say "15 rule specifications x 400 instances".
3. C3 calls the HELM median curve "U-shaped"; Fig. 4 shows a jump from the minimum to p=-2 and then a plateau.
4. C6 "nearly identical" across populations: median differences change from -1 (normalised) to 0 (raw, official providers) on a six-task board; fine as read with limitation (ii), but "nearly" should carry the one-task scale.
5. Appendix Tables 4-5 are set very small (`\tiny` + resizebox); legible only by zoom.
