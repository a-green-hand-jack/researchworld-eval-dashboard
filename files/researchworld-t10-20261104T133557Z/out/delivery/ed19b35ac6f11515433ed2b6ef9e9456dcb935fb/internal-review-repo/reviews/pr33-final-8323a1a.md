# Review of paper-repo PR #33 (main -> final), head 8323a1a1c3c6dfc4b8f3a0b38b29940f53b4797f

Inspected: paper/main.pdf (20 pp, text and every page image incl. Figs 1-8 and Tables 1-3; main text ends on p.9), a clean rebuild of paper/main.tex (compiles, same text), README.md, results/PROVENANCE.md, results/*.csv, code/ listing, .forgejo/CODEOWNERS; experiment-repo main (ceb8788).

Independently recomputed from results/*.csv: 270 cells for four main pools, n<=1000, 2000 reps -> 252 significantly wider, 9 parity, 9 narrower (all forest/gene_expression n=1000, min ratio 0.9945); 90 bootstrap cells -> 82 wider, 3 narrower; census_income PPI++ coverage 0.755/0.907/0.926 (Wald, n=15/200/500), 0.787/0.909/0.928 (t), 0.906/0.929/0.951 (boot); population headroom minima (0.988 gene_expression, 0.995 census_income). All match the text.

Strengths: question answered conditionally with paired like-for-like widths, coverage with Wilson intervals, known-truth synthetic checks against the variance formula, negative results reported, OLS secondary estimand, label-shift failure shown.

Open findings (request changes):
1. README forbidden-content log: PR text says the paper-repo entry is in the README, but at this head the log says "none" with no entry for paper-repo's two literature-search queries; experiment-repo ceb8788 holds the entry and is not in the delivery. (owner experiment-repo; paper-repo merges)
2. Figure/table generators are not in the delivery: deliverable.md requires which script makes each figure and table. README/PROVENANCE say they "live with the presentation owner", but figtab-repo code/ (fig_*.py, tab_*.py, style.py, widthcov.py) is nowhere under code/ or paper/ and no figure-to-script map exists. (owner figtab-repo for scripts under paper/figures or paper/tables; README map by experiment-repo)
3. Overstated wording: abstract/intro/Sec.6 say the headroom "is at most about 1.2%"; Sec. 5.2 measures it only for the adjuster classes tried, fitted on half of each pool, so it is a lower bound on the true headroom to the efficiency bound, not an upper bound. Say "for the adjuster classes tried". (owner paper-repo)
4. Propositions 1-2 are stated without proof and checklist item 3 answers Yes ("follow in a few lines"): add a short proof (appendix) or answer accordingly. (owner paper-repo)
5. Minor, paper-repo: the 270 cells are not independent (3 calibrations on the same draws; the 9 narrower cells are 3 adjuster/pool/n combinations); say so beside the "252 of 270" claim. Fig. 4/7 y-axis tick labels in the leftmost panels crowd (figtab-repo, optional).

## Re-review at head 4611fda4d5f84f9e5b9ee1104c1eff264ffa9613
Resolved: finding 1 (README log carries the paper-repo entry), 3 (wording "for the adjuster classes tried", lower bound), 4 (proofs of Props 1-2 in appendix, checklist updated), 5 (cell dependence stated). Rebuilt main.tex: 20 pp, no undefined refs, text identical to delivered main.pdf.
Still open: finding 2. README now maps each figure/table to a figtab-repo script by repo and commit, but the scripts themselves (fig_*.py, tab_*.py except code/dataset_table.py, style.py, widthcov.py) are not in the delivery; the release carries only the delivery, so figures/tables cannot be regenerated from it. figtab-repo#7 is still open.

## Re-review at head 69f0813e7b4828a99f8e7cd3311326f71ca8e454
Finding 2 resolved in substance: paper/figures/src/ holds all generators + run_all.sh; `sh run_all.sh results OUT` reproduces tab_datasets/tab_headroom/tab_ols byte-for-byte and regenerates all 10 figure PDFs; main.pdf rebuilds to identical text (20 pp); re-rendered Fig. 4/7 ticks readable.
Remaining: README.md at this head still says the scripts live with figtab-repo at commit 83205e8 (not in the delivery); paper-repo PR #38 (README map -> paper/figures/src) is open and unmerged. Merge it, then approve the new head (no other change expected).

## Approval at head adf3ca838e29e384209a6d837654d41b5bef3440
Diff from the verified 69f0813 is README.md only (figure/table map -> paper/figures/src, run_all.sh usage). Re-ran `sh paper/figures/src/run_all.sh results OUT`: three tables identical to paper/tables. All five findings resolved; paper/figures/results/code unchanged since verification. Conclusion: the delivery meets the objective (conditional answer with validity, like-for-like paired widths, known-truth theory check, negative results and limitations reported; reproducible code, notes and per-figure script map). Approved.
