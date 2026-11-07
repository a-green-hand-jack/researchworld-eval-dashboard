# Research and access log

All work is independent within this task. No topic search engine, literature search, citation graph, related-paper service, or paper aggregator was used. Only the six supplied starter-paper PDF URLs, a classical empirical-Bernstein paper (arXiv:0907.3740), the version-pinned PPI repository files, artifact download URLs, and official conference/template/ethics URLs were fetched. No forbidden-work encounter has been identified; no attempt was made to identify that work. PDF extraction locally includes the allowed documents; bibliography lists were not followed.

## Decisions made before full experiments

- Target: population mean E[Y]; IID labeled pairs and independent IID unlabeled scores; fixed external score. Score transformations use no new features or model training. Learned coefficients belong to the inference procedure.
- Main: eight synthetic laws, three provided score/label artifacts, n=200/800, N=10n, 5000 paired repetitions. Seeds are stable SHA256-derived integers. Real data are IID draws with replacement from each empirical distribution; their full-label means are evaluation truth only.
- Main methods: classical Wald, original PPI, unconstrained scalar PPI++, clipped scalar PPI++, degree-three multivariate control variates, five-fold degree-one and degree-three controls, four finite-sample empirical-Bernstein methods (label-only, raw score, 20%-pilot degree-one/degree-three bounded controls).
- Fixed Legendre basis degree three, five folds, 20% pilot, 95% intervals. No per-cell tuning or selection of significant results. CF1 isolates nonlinear gains from changes to coefficient estimation.
- Additional planned checks: degree stress test (1,2,3,7,15 at n=50,200,800), N/n sensitivity (.25,1,4,40 at n=800), finite-sample large-n check. All planned checks and any failures are reported.

## Preliminary / abandoned work

- System `python` alias was absent; switched to a local Python 3.11 virtual environment. Initial package-free download attempts failed because `requests` was not installed; no results lost.
- Two guessed conference-page URLs and a guessed 2026 style ZIP URL returned 404. The official NeurIPS 2026 CFP linked the correct current style archive, which was downloaded and used unchanged.
- A 30-repetition smoke run (results/smoke) checked I/O for eight laws and forest. Its results are not used as scientific evidence or merged with the 5000-repetition results.
- The smoke run included a fixed five-helper Bonferroni EB menu. It was dropped from the main comparison: its selection penalty and its unmatched toy transformations made it a less direct test of learned score controls. The implementation and smoke outputs are retained. Finite-sample learned controls instead use an independent 20% pilot.
- Smoke results prompted adding the degree-one cross-fit control, so any difference from PPI++ is not mistaken for evidence of nonlinear information. This happened before the full run.

## Reading notes

- PPI: general rectifier principle, mean estimator, distribution/independence assumptions, asymptotic and bounded finite-sample variants.
- PPI++: Sections 2, 3, 6 and mean power-tuning formula; its AIPW connection and efficiency inequality already establish much of the general conceptual basis. This project does not claim to invent control variates or nuisance calibration.
- Cross-PPI: Sections 1--3, training-on-label issue and cross-fitting; our original predictor is frozen and our nuisance fit is only low-dimensional on the score.
- Active inference: Sections 1--2; acquiring different labels is excluded here.
- StratPPI: Sections 1--3; designed strata allocations cannot be retrospectively applied to a fixed IID label set; fixed-bin poststratification is a related score-control construction.
- DML: introductory orthogonalization/cross-fitting argument; we use elementary fixed-dimensional expansions, not its causal assumptions.
- Maurer--Pontil (2009): Theorem 4, Corollary 5; symmetric bound derived by applying Theorem 4 to Z and 1-Z with half of the failure probability per tail.
- Official NeurIPS 2026 formatting instructions: 9 body pages; references, optional appendices and checklist excluded. Official checklist questions/guidelines preserved.

## Completed-run amendments and processing fixes

- Main, degree, ratio, and finite-sample suites were all completed: 49 conditions and 233,000 repetitions. Finite-sample additional n values were 3,200 and 12,800 (3,000 repetitions each); all other reported cells used 5,000 repetitions.
- After the first main run, added Hoeffding label-only and exact equal-tailed binomial intervals for known binary laws/artifacts. These are stronger finite-sample baselines than EB in many binary cases. The original random draws were regenerated from the same seeds, without recomputing or changing other endpoints. The current driver includes these baselines directly. No result was removed because the new baseline performed better.
- Per-cell `cpu_seconds` in the original main metadata is cumulative CPU time within that worker, not per-task time. It is not summed in the paper. Later suites use the corrected per-task counter. Per-cell and suite wall-time measurements were unaffected.
- Initial summary generation stopped because CV3 appears in both the main and independent degree-ablation suites. Added explicit suite filtering; no numerical output changed. A full output audit subsequently checks regenerated inputs/endpoints and all stored coverage/width values.

## Final document verification

- Summary-generation code had a Python string-escaping syntax error while creating LaTeX number macros. Corrected it and regenerated every output; no raw experimental result was altered.
- Increased printed precision for Monte Carlo errors that initially rounded to zero; tiny floating-point variance in mathematically constant widths is shown as zero rather than artificial scientific precision.
- Scoped appendix table font sizes locally, added longtable captions and repeated headings, and removed all overfull boxes. Inspected rendered pages of the PDF. Official style remains byte-identical.
- Final automated audits: all 49 conditions, 233,000 repetitions, 551 method summaries; all raw endpoints/widths/coverage internally consistent; all first-draw endpoints regenerated from recorded seeds; official 16-question checklist complete and original questions/guidelines preserved; seven main-text pages within the nine-page cap; no undefined references or overfull boxes.

- Document-audit parsing initially encountered non-UTF8 bytes in the TeX log; used replacement decoding for that log and reran the audit successfully. PDF text and numerical outputs were unaffected.
