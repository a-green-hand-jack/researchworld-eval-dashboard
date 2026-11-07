# Research and run log

All work took place on 2026-11-02 UTC in `/work`. This is a record of decisions and preliminary work, not a preregistration. No experiments were selected for statistical significance, and no claim of an exhaustive literature review is made.

## Environment and acquisition

- The directory was initially empty. The shell has `python3`, not `python`; two initial environment/download probes using `python` failed immediately with command-not-found. They did not execute an experiment. A local Python 3.11.2 virtual environment was then created.
- Exact public Arena, two MT-Bench, and NBA snapshots were downloaded successfully. SHA-256 checks passed for all four files. No optional large dataset or account was needed.
- Two guessed official NeurIPS template endpoints returned 404. The official 2026 call linked the correct formatting ZIP, which was then acquired. The style file is unmodified, with main-track anonymous mode and a nine-page main-text limit.
- The latest PDF renderer pulled unnecessary layout dependencies. It was replaced with PyMuPDF 1.26.6; no layout inference, OCR, remote models, or GPU were run. This affected inspection tooling only.

## Initial question and preliminary fits

Before inspecting fitted rankings, the study chose fixed-schedule decisive-outcome reversal, random-noise comparison, leader-support normalization, full Arena and MT-Bench panels, and the final six seasons (2010–2015) in the supplied NBA file. The aim was a descriptive cross-design audit, not to optimize an actual online manipulation strategy. All model names and eligible records are retained.

The first diagnostic main fits found static leading-pair reversal paths of 2 Arena records, 46 MT-human records, 61 MT-GPT4 records, and 1–8 NBA games. Matched MT-Bench keys initially appeared to overlap less when compared in their raw A/B orientation; canonicalizing unordered pairs correctly yields 1,814 common question/turn/pair units. The actual matched control uses that canonical intersection throughout; no result from the raw-orientation diagnostic was used as evidence.

Close Arena scores motivated separating point-order reversal from a frozen uncertainty-scale reversal. The latter is a constructed gap below minus twice the original bootstrap gap SD; it is explicitly not a post-edit confidence interval or a significance test. Both endpoints are retained. The original-data bootstrap fixes the queried pair rather than reselecting a different pair per resample.

## Implemented methods and controls

The initial method combined a static influence path with exact refitting of every integer prefix, plus a conservative logistic-curvature no-crossing certificate. It included adaptive influence, incident-only access, deletion, random reversals, question-cluster/record/game bootstrap, matched human-choice repetitions, ridge changes, tie dropping, and a home-covariate NBA control.

A complete initial main experiment, before adding the direct-transfer bound, ran successfully in **91.6261374950409 seconds**. It used 500 bootstrap replicates, 500 random permutations, and 100 matched human selections. No fit failed. Four numerical tests passed at that stage. Its measured outcomes were preserved conceptually in the subsequent expanded run, with unchanged data, seed, stochastic streams and endpoints; the final CSVs supersede these preliminary files.

Inspection showed that leading-pair constructions often selected only direct wins. This led to a maximum-principle derivation: for an item-only ridge BT Hessian, the inverse-Hessian contrast has its extrema at the queried items at every parameter value. Integrating this inequality gives a global direct-transfer relaxation, not merely a local influence approximation. A fifth exhaustive synthetic test was added to check the resulting domination inequality. The general curvature bound was retained as a weaker comparison, rather than omitted because it was sometimes vacuous.

A second expanded main run took **95.11941695213318 seconds**, adding direct bounds and capacities without changing experimental seeds or outcomes. Its all-rival winner audit took **9.228683233261108 seconds**. The winner audit found that NBA-2015 can lose its original leader to Houston in seven constructed edits, before the eight-edit runner-up path; the distinction is reported. After improving numerical-gradient guards and the result consistency checks, the full final `make reproduce` run regenerated the published artifact. Its authoritative timings and checks are `results/run.json`, `results/winner_run.json`, `results/audit.json`, `results/verification.json`, and `results/pdf_check.json`.

## Unexpected or qualifying results retained

- Arena's top pair is unresolved under original-data resampling. Its tiny point-order threshold is not described as overturning a clearly established gap.
- Arena's threshold changes under regularization, and dropping ties already reverses its original queried order. These outcomes appear in the modeling-control table rather than being discarded.
- All full MT-Bench random-flip simulations retain the original winner even at the largest tested random budget; zero observed events are reported with a nonzero Monte Carlo upper limit, not as proof of zero risk.
- Adaptive and static leading-pair constructions have identical counts in these panels. No algorithmic superiority of adaptive selection is claimed.
- Direct capacity is insufficient in several NBA seasons. Certified lower/upper intervals remain intervals; exact optima are not invented. Upper/lower equality sometimes proves exactness even when the simple capacity test fails.
- Global-budget and leader-support scales give different apparent cross-design comparisons. Overlapping lower/upper intervals are acknowledged; an upper-bound ordering is not called a proven ordering of optimal robustness.
- Matching MT schedules preserves the observed expert/GPT-4 difference, but is not a causal comparison or a validity test of judge quality.

## Approaches not pursued

- No broad literature search was attempted, to preserve the independent-research restriction. Novelty priority is consequently qualified.
- Large optional Arena datasets, WebDev, and third-party model judges were unnecessary and not downloaded; this is not a failed acquisition or an unreported experiment.
- Integer/global combinatorial optimization after direct capacity is exhausted was not implemented. All unresolved intervals are labeled. No purported exhaustive NBA search was run.
- Live vote collection, model identity inference, new-vote attacks, actor/annotator corruption, temporal bootstrap, robust-estimator defenses, and causal intervention comparisons were not run and are not claimed complete.
- Uniform random deletion and arbitrary tie corruption were not run. Deletion is a targeted alternative-operation baseline only. The paper specifies this scope.

## Verification and release

Five synthetic/numerical checks pass; all synthetic fixtures are excluded from empirical claims. Stored main and winner edit witnesses are independently reconstructed and refitted, and bounds, counts, endpoints, and original scores are checked. PDF checks verify the page limit, all 16 official checklist answers, unchanged official style, and no unresolved citations/references or overfull boxes. Rendered pages were inspected for figure/table readability, and plot sizing was increased before the final build.

The artifact is packaged without raw datasets, downloaded literature, virtual environments, or LaTeX intermediate files. All raw data remain under `data/raw/`; exact sources and checksums are supplied for reacquisition. No result, plot, or table is fabricated or based on an unrun experiment. No known prohibited material was encountered; see `access_log.md` for the exact access boundary.
