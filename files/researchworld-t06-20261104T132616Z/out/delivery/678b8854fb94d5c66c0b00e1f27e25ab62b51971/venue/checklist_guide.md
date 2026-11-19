# NeurIPS 2026 checklist: what each answer must rest on in this study

Owner of the filled checklist: the report position (`paper-repo`); this guide says what is true/known for the venue and
what evidence each answer needs. Fill `checklist.tex` (copy from `venue/neurips2026/`), keep the question text and
guidelines as shipped, replace each `\answerTODO{}` and `\justificationTODO{}`. An answer is only Yes if the pointed-to
section exists in the final paper.

| # | Question (short) | Expected answer / evidence needed |
|---|---|---|
| 1 | Claims match contributions/scope | Yes only if every claim in abstract/intro is backed by a result and states its scope (datasets, evaluation designs, perturbation type). |
| 2 | Limitations discussed | Yes; section "Discussion & limitations" (objective requires applicable conditions and limits). |
| 3 | Theory: assumptions + proofs | NA unless a derivation (e.g. influence/approximation formula) is claimed; then Yes with proof in appendix. |
| 4 | Reproducibility information | Yes: datasets with commits/sha256 (see `data.md` of the objective), BT fitting settings, perturbation definitions, seeds, k, B. |
| 5 | Open access to data and code | Yes for public data (versions) and code; the PDF must stay anonymous (anonymized repo/zip, no author URLs). Raw data not shipped, acquisition script is. |
| 6 | Training/test details | Mostly NA/Yes: no training; fitting details (solver, regularisation, tolerance, ties handling, splits/bootstrap) stated. |
| 7 | Error bars / significance | Yes: CIs from bootstrap/multiple seeds for every headline number; define what the interval covers. |
| 8 | Compute resources | Yes: CPU model/cores, RAM, wall time per experiment (measured, from logs, not estimated). |
| 9 | NeurIPS Code of Ethics | Yes after reading https://neurips.cc/public/EthicsGuidelines. |
| 10 | Societal impact | Discuss both: leaderboards used for selection; manipulability findings could be misused (vote manipulation) vs. help auditing. |
| 11 | Safeguards for high-risk release | NA unless attack code/perturbation tooling that could game a live leaderboard is released; then say what is withheld/limited (only offline, on frozen data). |
| 12 | Assets credited, licenses | Yes: cite every dataset/code used, state license from `data.md`; undeclared licenses (judge set) stated as undeclared; WebDev Arena click-through license, if used. |
| 13 | New assets documented | Yes if derived tables/code are released (README of the reproduction notes), else NA. |
| 14 | Crowdsourcing instructions | NA (only existing public votes reanalysed; no new participants). |
| 15 | IRB / participant risk | NA (existing public data; note that Arena text content is not redistributed). |
| 16 | LLM usage | Core method uses no LLM (NA/No) unless an LLM judge dataset is part of the study; LLM *assistance* in writing/coding is described in a separate disclosure paragraph in the paper (objective requires disclosure). |

Position of the checklist in the PDF: after references and appendix; it does not count toward 9 pages.
