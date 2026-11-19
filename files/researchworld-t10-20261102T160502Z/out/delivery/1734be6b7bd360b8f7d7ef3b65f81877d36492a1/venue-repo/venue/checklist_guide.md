# What each NeurIPS 2026 checklist item needs from this study

Fixed wording and macros are in `template/checklist.tex` (do not edit questions). `paper-repo` writes the final
answers once results exist; an answer must not be `Yes` unless the evidence in the right column is in the delivery.
Prefilled answers before the evidence exists are forbidden (R7).

| # | Item | What this study must show for `Yes` | Supplied by |
|---|---|---|---|
| 1 | Claims | Abstract/intro claim exactly what the tables show, incl. null/conditional outcomes; scope = mean/prevalence target, fixed (labeled, unlabeled, predictor), the datasets used | paper-repo; claim→evidence map from story-repo `PLAN.md` §4 |
| 2 | Limitations | A "Limitations" section: finite-population sampling convention, mean estimand only, covariates unused, shift cases, small-n | paper-repo |
| 3 | Theory | Efficiency-floor derivation with assumptions (iid, finite variance, CLT regime), proof or sketch in appendix; scope of validity | experiment-repo (derivation), paper-repo |
| 4 | Data and code | Code + runnable commands + data fetch steps; datasets public; seeds | experiment-repo, paper-repo README |
| 5 | Experimental details | n/N grids, replicates, sampling convention, estimator definitions, calibrator class and its tuning on development seeds only | experiment-repo |
| 6 | Statistical significance | Coverage with Wilson CIs, paired width ratios with CIs, number of replicates, how errors were computed | experiment-repo, figtab-repo |
| 7 | Compute resources | CPU type/count, run times, total CPU hours (record from real jobs) | experiment-repo |
| 8 | Code of ethics | Statement; no human subjects, public data | paper-repo |
| 9 | Broader impacts | Short note: mis-covered intervals in downstream science; consequence of silent under-coverage | paper-repo |
| 10 | Safeguards | `NA` (no high-risk release) with justification | paper-repo |
| 11 | Licences of assets | `ppi-python` MIT; data files: no stated licence (R13), original sources named; UCI CC BY 4.0 if used; folktables MIT / PUMS public | paper-repo, from `data.md` |
| 12 | New assets | The code release (and any generated synthetic data) documented; licence is the owner's choice, none declared by venue | paper-repo |
| 13 | Crowdsourcing/human subjects | `NA` | paper-repo |
| 14 | IRB | `NA` | paper-repo |
| 15 | LLM usage | `NA` if no LLM is a component of the core method (writing/editing/formatting-only use needs no declaration per the template text); otherwise describe it | paper-repo |
