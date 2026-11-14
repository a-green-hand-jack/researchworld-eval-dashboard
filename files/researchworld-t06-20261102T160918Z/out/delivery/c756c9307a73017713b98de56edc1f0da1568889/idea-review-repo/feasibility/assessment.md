# Feasibility assessment: pairwise leaderboard stability

## Decision

**Proceed with the bounded empirical study and manuscript integration.** The available CPU implementation, pinned public data, completed perturbation runs, uncertainty calculations and modeling controls can answer the objective as a descriptive comparison of fixed leaderboard snapshots. No additional dataset, GPU, paid judge, exact combinatorial solver or broad experiment expansion is needed for that objective.

This assessment begins after the empirical runs were completed. It is an independent judgement before further integration/expansion costs, not an ex-ante approval or preregistration of those runs. It does not approve a final manuscript that has not yet been assembled, guarantee conference acceptance, or substitute for independent final review.

The feasible research question is: how do successful, fully refitted leading-pair outcome-reversal attacks and random perturbations vary across these observed regularized Bradley–Terry rankings, and how do their effects relate to baseline gap uncertainty and whole-ranking changes? The MT common-cell comparison can additionally describe label-source differences on a shared observed schedule. The data do not identify a causal effect of crowdsourcing, expertise, model judging or sports design in general.

## Inputs and basis of judgement

The standard is idea-review-repo#1 and all five frozen files under `/initial-state/inputs/0/`, especially the two-real-design requirement, CPU/week constraint, paper/reproduction deliverables, and source-access prohibition. I read the actual method implementation (`scripts/bt.py`, `datasets.py`, `run_study.py`, `matched_fixedpair.py`), analysis notes, primary audits and uncertainty summaries, matched fixed-pair outputs, provenance and reproducibility instructions. This was a feasibility inspection, not an independent rerun of all fits. Analysis supplies its recorded method checks and reconstructable witnesses; final review must still check their use in the delivery.

Inspected empirical revision: `36eb7c0b781382017a3983c1e57b85306933582d` of world/experiment-repo, also published as `analysis-v1`. Important source paths are `notes/{methods,data_audit,pilot,results_handoff,run_log}.md`, `results/provenance.json`, `results/{primary,robustness,matched,matched_bootstrap}/audits.csv`, `results/summary/primary/uncertainty.csv`, and `results/summary/matched_fixedpair/difference.json`.

The context Brief at world/idea-repo `context/brief.md` (revision `acb49911b146ca88535b888fe04fd43a728bd322`) and settled study plan/requirement map at world/story-repo `planning/{study_plan,requirements}.md` (revision `2d0f3bf2ed00ed2a064e1d6d022dba3ccb20d63c`) have now been read. They match the frozen objective and this scope boundary. Story explicitly routes feasibility through release/wiki/issues, with no final artifact path; paper owns incorporating the bounds.

## Resources: measured costs versus estimates

Four pinned raw inputs total 203,736,944 bytes (about 204 MB decimal), from the actual provenance manifest. Arena has 57,477 rows/64 models; MT human and GPT-4 have 3,355 and 2,400 rows/six models; NBA uses ten separate 2006–2015 regular seasons of 990–1,230 unique games/30 teams. These are materially smaller than the optional 140k text-rich Arena release. Raw inputs remain outside version control; column-selective parsing and aggregated pair-count fitting avoid carrying dialogue text into every fit.

Recorded per-dataset elapsed wall times sum as follows. These sums come from archived audit CSVs; they are not measured total process time, CPU-hours, download/build time, or a forecast for another host.

| Executed batch | Audit records | Sum of recorded elapsed seconds |
| --- | ---: | ---: |
| Primary | 13 | 99.36 |
| Modeling/annotation robustness | 10 | 33.09 |
| Matched human-label selections | 200 | 5.30 |
| Paired matched question resamples | 1,000 | 34.00 |

Primary settings are 500 random-reversal replicates, 50 endpoint-only replicates and 500 cluster bootstraps per ranking, with exact refits at seven budget levels and representative single-edit checks. Runs used one BLAS thread and ordinary CPU numerical libraries. Home-adjusted NBA and fixed-pair follow-up results exist, but their audit files do not supply comparable elapsed fields; no timing is invented for them. Peak RAM and total end-to-end reproduction time have not been independently measured here. The observed data sizes and completed small-dimensional fits support computational feasibility under the actual 2-CPU/4-GB sandbox as well as the task's reference CPU setup; they do not establish an unmeasured peak-memory bound.

Planning estimate: reserve remaining work primarily for manuscript/figure integration, official-template compliance, a clean reproduction and independent correction, rather than spending the week on new datasets. This is a prioritization judgement, not a measured schedule. Reproduction/build timings should be recorded by their owners when run; no universal runtime guarantee follows from the table.

## Evidence and scope risks

| Risk | Evidence or mechanism | Required bound or correction |
| --- | --- | --- |
| Confusing a found attack with a minimum | Influence ordering and binary search inspect only one family of prefixes; prefix monotonicity is not certified | State successful-edit **upper bounds**; retain exact witnesses/refit margins. Failure within the 5% search cap does not certify robustness. No optimality solver is required for this bounded claim. |
| Ranking instability is conflated with attack novelty or harm | Arena's initial leading gap and all ten NBA leading gaps have bootstrap percentile ranges spanning zero | Present baseline uncertainty alongside edit counts; distinguish pair reversal, any winner change and global Kendall disagreement. Small costs may reflect unresolved ordering. |
| Cross-design attribution exceeds identification | Entrants, sample sizes, gaps, coverage, tie rates, dependence and eras differ | Compare snapshots descriptively. Use the 1,814-cell matched MT control for schedule/sample-count comparability, while retaining its label/gap/annotator limitations. It does not establish an inherent advantage of model judging. |
| Edit units are silently equated | Only distinct decisive labels are reversed; ties are fixed. A reversal changes a full win to a full loss | Define the intervention and report integer k, k/N, N and decisive counts. Do not equate this cost with deleting rows, injecting votes, independent bit noise or actual attacker access. Same fraction measures changed observed records, not equal inferential information. |
| Model conventions dominate headline counts | Arena found counts change with ridge strength; dropping ties changes its fitted leader | Specify summed-loss ridge penalty and half-win ties, retain sensitivity results and changed pair identities. A fixed lambda has different relative strength as sample size changes. Do not advertise an invariant “two edits” property. |
| Conditional bootstrap is overstated | Arena lacks user clusters; MT questions share annotators; NBA dates do not capture all temporal drift; pair selected from data | Call percentile ranges conditional/descriptive, without simultaneous or post-selection coverage guarantees. Separate data resampling from random-edit Monte Carlo error. Additional inaccessible metadata cannot be supplied by computation. |
| Matched comparison changes its estimand | Bootstrap runner-up identities can change; fixed-reference follow-up was added after inspecting this | Report reselected and fixed-reference statistics separately; disclose post-hoc status and zero-edit already-reversed replicates. A bootstrap percentile range for a heuristic is not an interval for optimal attack cost. |
| Nominal budgets conceal saturation | Targeted candidates can be fewer than requested k; integer rounding differs by N | Use actual_k and at-most-k language in curves/captions; deterministic influence results receive no Monte Carlo interval. |
| Static sports model is overgeneralized | Separate seasons and home-effect control address some pooling/home issues, not changing strengths | Retain within-season drift limitation. NBA rankings here are fitted BT rankings of observed results, not a validation of published Elo ratings or ground-truth team quality. |
| Main-conference positioning is unsupported | Existing BT/influence ingredients are conventional; this role has not established novelty | Context owner must supply actually read permitted prior-work positioning. Frame evidence-driven scope honestly; neither a new estimator nor guaranteed venue-level novelty follows from completed computation. |

## Remaining delivery gates and ownership

The empirical requirement of at least two different real evaluation designs is met in scope by Arena human preference and NBA competition, with human/model-judge MT comparisons adding a further design contrast. The task permits a chosen perturbation method and metrics; it does not require every edit type, all listed datasets, certified minima or causal attribution. Omitting these extensions does not waive a required evaluation item.

The remaining required work is owned elsewhere and must stay open until delivered: story settles the plan and CODEOWNERS; context supplies the Brief and permitted related-work positioning; experiment imports code/results and checks manuscript numerical claims; figtab supplies measured figures/tables and script mappings; venue supplies the latest official permitted template/rules/checklist; paper assembles a complete source/PDF/reproduction project, fills evidence-dependent checklist answers, and discloses AI assistance; independent reviewers judge the assembled version. A successful feasibility assessment does not replace any of those deliverables.

Before release, verify that all reported numbers/figures trace to executed outputs, raw data are excluded, pinned fetching and the documented command order work in the delivered layout, each figure/table has a generator, source restrictions and any accidental encounter are documented, and final PDF/page limits/checklist pass independent review. These are objective requirements, not permission requests. Any new costly work should first identify a claim that the existing analysis cannot support; otherwise prioritize closing these delivery gates.

## Context-informed contribution check

Context supplied in idea-review-repo#4 its actually read permitted-source account: starter Huang et al. already studies influence-guided BT deletion sensitivity on Arena/MT, while starter Min et al. addresses new-vote injection. I have read the Brief and that account, not independently read those papers; bibliographic accuracy and source-grounded comparisons remain context's responsibility. Given that supply, neither a first leaderboard-sensitivity audit nor a new influence technique is a feasible claim. Changing deletion to reversal alone does not demonstrate a substantial methodological advance.

The existing evidence can support a complete empirical paper whose contribution is the specified outcome-reversal audit, observed relation to unresolved baseline gaps, modeling-convention sensitivity, random/endpoint comparisons, sports-season heterogeneity and matched-label-source controls. It supports the particular observed contrasts, not a universal gap law, an optimal attack, or a causal design hierarchy. The extension's significance and adequacy for the selected conference's main-track novelty bar remain review judgements; feasibility is not an acceptance prediction. The paper must make the overlap and difference explicit rather than treating completed experiments as proof of novelty.

No mandatory empirical gap is identified for the settled descriptive questions. If the intended claim expands to comparative superiority over deletion/injection methods, it would require new like-for-like executed baselines with aligned fits/ties/denominators; the present study does not supply them. The bounded plan makes no such claim, so that expansion is unnecessary. Remaining evidence work is faithful integration, reproducibility validation and independent review of the assembled paper, with context completing its permitted-source dossier.

## Closed-handoff reconciliation

The owner responses closing world/story-repo#3 and world/idea-repo#3 have been checked. The subsequent story planning revision inspected here is `4885509675c1bd22a52eec0cb8e4dbc87426cf3b`; its changes explicitly adopt the feasibility limits and retain assembled-report validation as open. No scope expansion, missing owner or additional empirical requirement is introduced by these answers. They resolve both requested inputs.

Context additionally clarifies that this regularized empirical-schedule BT audit does not recreate the official Arena weighting/interval pipeline. The paper must describe its fitted snapshot ranking and avoid claiming to reproduce or overturn an official published ranking under its full methodology. The distinction does not prevent the chosen fixed-model sensitivity question from meeting the objective. Final application of these bounds has now been checked at the revision supplied in world/paper-repo#6; see `delivery-check.md` for the exact revision, inspected evidence and closure.
