# Review of paper-repo PR #9, round 3 (interim version into `release`)
Head inspected: 29ef145187cd003c024c87625c59f7defdc73543.

Checked at this head:
- N1 fixed: Table 2 is populated (B1 4.60/4.54 at n=50, P3 DR 3.40/3.43, P3 EB 3.04/3.80, Spearman 0.85/0.64 ...), values equal my recomputation from results/predictions/tier1.parquet; make_tables.py now fails on a missing cell; no stray dashes remain in the PDF text outside the intended ones.
- paper/paper.pdf and ../paper.pdf rebuilt from the sources at this head with build.sh: text identical to the delivered PDF.
- N2 fixed (checklist item 1 now states the correction finding), N3 fixed (Table 5 caption per split), N4: checklist guideline text removed (19 pages), appendix run-in headings now have text. Remaining WARN: one Type 3 font in the PDF (`pdffonts`: a single unnamed Type 3 font, the same warning the unmodified template gives); main text 9/9 pages by the checker.
- All round-1 findings F1-F10 were verified resolved in round 2. All four figures, Tables 1-11 open and readable.
- Honest scope: further analyses on 4-7 benchmarks with 20 repetitions and the organisation hold-out (not a capability/family-by-size shift) are disclosed in the abstract-level limitations; forbidden-content disclosure present; no placeholder numbers.

Open, not blocking this interim version (for `final`):
- code/bpx/__pycache__/*.pyc are tracked (experiment-repo path): remove, add .gitignore.
- Planned analyses still not run: family/size/date hold-out, re-implementation fidelity (original benchpred package not run; Active Evaluation Acquisition, metabench GAM absent): they stay stated limitations unless an attempt is made.
- Further analyses use subsets of benchmarks; extending them to all 13, if budget allows, would strengthen Sec. 5.5.

Conclusion: the interim version is supported by its evidence and honest about its scope. Approve.
