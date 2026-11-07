# Brief: fixed-input confidence-interval width

## Frozen objective and interpretation

Source: Research objective, world/idea-repo#1, and the six SHA-256-frozen files copied verbatim to `supplied/` in idea-repo. Both TASK.md and TASK.en.md were read in full, along with data.md, deliverable.md, resources.md and starter_literature.md. This brief is a requirements/context supply, not an experimental result or the study owner's final plan.

The objective asks: **“with the labeled set, the unlabeled set and the predictor all fixed, and the nominal coverage required to hold, can the confidence intervals given by existing methods be shortened further? By how much? Under what conditions can they, and under what conditions can they not?”**

The inputs are a small gold-label sample, a larger unlabeled sample, and an “already pre-trained, non-modifiable prediction model.” The inferential target is to be selected and justified. There must be “no additional labels, no change of predictor, no additional unlabeled samples.” The natural operational interpretation is that each repeated-sampling replicate supplies exactly the same labeled records, unlabeled records and frozen prediction values to every compared method. Repeated sampling is necessary to measure coverage; it does not mean obtaining extra labels within a replicate. The fixed model is held constant across replicates. This differs from conditioning on one realized dataset and claiming a frequentist coverage probability with no randomization mechanism.

For the proposed population mean target, score control variates may be estimated from the existing labels, but this is an inference procedure and must be described explicitly. The original model and stored prediction values remain fixed; no new feature model, label acquisition, predictor retraining or hyperparameter search on hidden evaluation-only labels is permitted. Planning and independent feasibility have agreed to this inference-only interpretation in their settled study plan and Feasibility wiki; it does not permit replacing the supplied predictor with a newly trained one. Population mean/proportion is a justified choice because it covers prevalence and average scientific measurements and makes width/coverage directly interpretable; the task does not require every possible estimand.

## Required research, quoted

1. “review how existing methods work in this setting and what they assume, and make explicit the specific research question you will answer.” Context must distinguish PPI, power tuning, sample-split/cross-fit inference and changed sampling designs.
2. “propose and test your route, comparing it with the existing valid-interval methods that are available”; public real datasets may be used and synthetic data with known truth may supplement. The frozen data guide explicitly also permits entirely synthetic data, so none of the nine example datasets is mandatory.
3. “report the evidence and the limitations, and state under what conditions the conclusion brings a gain and under what conditions it does not”; theoretical analysis, if supplied, must “state the assumptions and the scope of applicability, and check it with experiments.” A conditional or negative result is acceptable.

Success is measured by **“under repeated sampling, the empirical coverage of the interval reaches the nominal level (for example 95%)”; “a comparison of the average interval width given the same inputs”; and “repeated experiments and an uncertainty report.”** A narrower interval that loses coverage is not a successful valid-interval improvement. Empirical coverage alone cannot establish an exact finite-sample guarantee, and an asymptotic theorem must be labeled as such. Coverage Monte Carlo uncertainty and paired width uncertainty are required for credible conclusions. Keep failed and successful cells visible; do not condition width summaries silently on coverage success.

## Deliverables and constraints, quoted from deliverable.md/resources.md

The submission is “一篇完整的研究论文（PDF 与 LaTeX 源文件）” (a complete paper in PDF and LaTeX), selecting ICML, ICLR or NeurIPS, using “最新一届的官方 LaTeX 模板” (the latest edition's official template), obeying its main-text page limit and reference/appendix policy, and completing the required checklist. At minimum the paper contains abstract, introduction, related work, methods, experiments, discussion/limitations and references. Venue owner establishes the actual current template and rules; the task does not name a year.

“全部代码与复现说明” (all code and reproduction instructions) must include environment/dependency versions, data acquisition and data version, random seeds, commands, estimated runtime, and a mapping from every paper figure/table to its generating script. Every reported number/table/figure must originate in actual runs during this task and be reproducible by the supplied code. Failed runs, abandoned routes and unfinished work must be reported honestly, not represented as completed. Only genuinely accessed real literature may be cited.

CPU only; one week including reading, implementation, experiments and writing; no paid API; storage under 5 GB. The frozen resource guide estimates under 8 CPU hours, explicitly an unmeasured estimate, not a resource guarantee. The actual sandbox and world budget are tighter operational constraints and are set by the environment.

## Independence restriction

Deliverable.md forbids searching for, accessing, reading or using a particular unnamed prior paper, any version/abstract/venue/review/material/code, or pages that cite, discuss or reproduce it. It also forbids attempts to infer its title, authors or results. The starter list is explicitly permitted. We use only direct URLs for that list and the version-pinned package source, without broad related-work, citation-chain or title searches. If forbidden content is encountered accidentally, stop reading immediately and record where, what and how much was read in the reproduction instructions. No such encounter has been identified in context work to date. This is a bounded literature review, not evidence of comprehensive novelty.

## Data supplied as acquisition descriptions

The task supplies descriptions and URLs, not frozen numeric arrays. `ppi-python==0.2.3` (tag v0.2.3, supplied short commit identifier 6b8475b) downloads nine NPZ collections anonymously via Google Drive. Data file hashes, actual retrieval success and inspected array contents must be recorded by analysis. The guide reports roughly 48 MB total; that is supplied information, not a download measurement from this position.

| Collection | Supplied structure | Context and caveat |
|---|---|---|
| galaxies | Y,Yhat; 16,743 each | Spiral-arm indicator, visual labels and computer-vision predictions. The example subset is not the full 304,122-object Galaxy Zoo 2 catalog. |
| forest | Y,Yhat; 1,596 each | Amazon deforestation labels and satellite-derived predictions. |
| alphafold | Y,Yhat plus 3 modification indicators; 10,802 each | Protein disorder and structure-based predictions. Score need not be continuous; inspect support before claiming nonlinear gain. |
| gene_expression | Y,Yhat; 61,150 each | Experimental expression and Transformer predictions. |
| census_income | Y,Yhat; 380,091; X with 2 columns | California 2019 reported income and predictions; age/sex features. |
| census_healthcare | Y,Yhat; 318,215; X with 2 columns | Private health insurance, features include income. |
| census_education | Y,Yhat; 318,215; X with 4 columns | Income/education quantities. |
| plankton | Y,Yhat; 421,238, plus Y_unlabeled,Yhat_unlabeled; 329,832 | Labeled 2013 and unlabeled 2014 distributions differ. Do not apply iid theory to cross-year transfer without a shift model. |
| ballots | Y,Yhat; 1,027, plus Yhat_unlabeled; 78,150 | San Francisco 2022 special-election ballots; unlabeled truth is not supplied for ordinary repeated-coverage assessment. |

Only census_* includes X in the listed NPZ arrays. Except plankton/ballots, Y and Yhat refer to the same records. Labels hidden to simulate an unlabeled sample may be used only by the evaluation layer, never by estimation, basis selection or method tuning. An iid empirical-distribution experiment sampling records with replacement targets the full file's empirical mean; it supports that empirical-population claim, not automatic generalization to all forests/proteins/galaxies. Without-replacement sampling needs a finite-population formulation and appropriate variance treatment.

The package's code license is MIT; a separate NPZ-data license is not established by the supplied repository/PyPI information. Preserve provenance and retrieval instructions rather than assume MIT covers the underlying data. Optional sources: Wine Quality (6,497 red+white records, CC BY 4.0, no predictions), California Housing (20,640 records, 8 features, no clear independent license in supplied description, no predictions), ACS PUMS via folktables 0.0.12 (public Census data, wrapper MIT, no predictions), or self-generated data. Sources without predictions would require a disjoint training set and a model frozen before evaluation; using existing Yhat is cleaner under this objective.

## Prior-work evidence and analysis conventions

The companion **Baseline-context** wiki page supplies source-checked formulas and comparator guidance. Core result already established by PPI++: scalar power tuning is a variance-minimizing control-variate correction, not a new contribution here. Its mean-estimation formula allows unrestricted real coefficients; the supplied v0.2.3 implementation clips its default tuning to [0,1]. Therefore gains against only its clipped default cannot establish nonlinear benefit. Include an unrestricted scalar comparator to separate clipping effects from extra score information.

PPI's main practical normal intervals, PPI++ and StratPPI are asymptotic. Original PPI also supplies a finite-sample construction when valid rectifier/prediction-mean confidence sets are available. Cross-fitting does not itself yield exact finite-sample coverage. If strict nominal coverage is claimed, the analysis must supply an applicable finite-sample construction with assumptions checked, and compare bounded methods within that guarantee class.

Existing figures in the permitted PPI/PPI++ literature pair coverage and width across repeated draws, identify the target and nominal level, and state repetition counts. Follow that logic: display nominal coverage reference lines with Monte Carlo uncertainty, paired width effects with uncertainty, axes for label count and scenario, and separate or clearly label finite-sample and asymptotic families. Include gain, affine/no-signal/no-gain and small-label failure regimes. Do not report illustrative intervals as evidence of coverage. Present width ratios with comparator direction explicit and uncertainty from the same paired replicates.

## Current handoff and unresolved scope

Context owns this Brief, the permitted-source dossier and access log. Planning owns study questions/division and has accepted a reasoned exclusion of an implemented fixed-input poststratified comparator for the narrow cubic-versus-affine question, while requiring its related-work discussion and forbidding broad superiority claims. Analysis owns implementation, proofs offered as study results, data inspection, all experiments and uncertainty. Presentation owns final plots/tables; venue owns template/checklist constraints; report owns manuscript and build; review owners judge validity and completeness. No analysis claim is established by this brief.

Unresolved empirical items: actual score support, dataset hashes, conditional calibration/nonlinearity, finite-sample coverage/width, and runtime. These must come from analysis, not be inferred from source descriptions. Unresolved theoretical item: whether any “cannot improve” statement is restricted to the score-measurable control-variate class and first-order asymptotics; a global impossibility claim is not justified by this context. No missing evidence licenses a placeholder conclusion.

## Settled publication routing (2026-11-02 update)

The settled plan at story-repo `b509bad4bd2da93c7d60a9a3d6358c2f8a7124fa`, `planning/study-plan.md`, incorporates this Brief and the checked baseline scope. Independent feasibility's published Feasibility page agrees to inference-only score calibration, complete label accounting, class-limited conclusions and the reasoned StratPPI comparator scope. These are settled interpretation decisions; all scientific measurements and final review remain with their owners.

The source-checked seven-file release `context-v2/context-bundle.tar.gz` has been handed through story-repo to paper-repo PR #9. Planning reports byte-for-byte equality of all extracted members, archive SHA-256 `e82c7c1fc8c0efd73f8b500f0fd7dc161107e6e5f00cf2ca81948bd676d005d4`. I accept paper-repo as the `context/` publication/review owner under this fallback; idea-repo remains the context author and source checker. This administrative settlement does not change source formulas, references, or experimental requirements. The bundle is the archived checked source handoff; this live wiki page additionally records settled coordination. story-repo#10 is closed: planning confirms paper-repo PR #9 merged and all seven delivery-main files matched the authorized bundle byte-for-byte. Direct paper-repo access is unnecessary for this agreed delivery route.
