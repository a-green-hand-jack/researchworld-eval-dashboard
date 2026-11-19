# paper-repo

Delivery root. `paper/` holds the LaTeX source (NeurIPS 2026 main-track template from `venue-repo`); the built `paper.pdf` at the root is rebuilt with each merge once results exist. Code, results, figures, tables and `REPRODUCE.md` are delivered by their owners (see `.forgejo/CODEOWNERS`).

Status: complete draft. `paper.pdf` (25 pages: 9 main, references, NeurIPS checklist, appendix) is built from `paper/` at the commit that precedes the one adding the PDF. Every number in the text comes from `results/tables/*.csv` (see `results/CLAIMS_MAP.md`); figures and tables are the renders of `figures/` and `tables/`. Covered since the first draft: flip probability against the true gap, the plug-in version of Proposition 2 (removes the mean bias, not the error or the ranking), CV+/jackknife+ against split, one misspecified mean. Not done, and stated as such in the paper: a real compositional dataset, volume ratios at K=10, other misspecifications and other CV+ noise models.
