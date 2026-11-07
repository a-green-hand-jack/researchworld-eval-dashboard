# Objective coverage and acceptance checks

Authority: Research objective issue #1 and all five frozen input files. This map records responsibilities; it does not narrow those requirements or assert that uninspected outputs passed.

| Objective requirement | Delivering owner | Acceptance evidence |
| --- | --- | --- |
| Operational research questions and metrics | story | `planning/study_plan.md`: fixed-pair sensitivity, targeting, cross-snapshot contrasts, convention dependence |
| At least two real evaluation designs | experiment | Pinned crowd/human/model-judge/sports input audit and executed results under `analysis/`; distinctions in paper |
| Define small changes and cross-dataset comparison | story + experiment + paper | Distinct decisive-label reversals, fixed schedule/ties, counts plus k/N including ties, decisive denominator context, descriptive comparison caveats |
| Implement and execute methods with actual evidence | experiment | CPU run manifests, numerical checks, exact-refit witnesses, generated result files and scripts |
| Appropriate baselines, controls and uncertainty | experiment | Random/endpoint/influence curves, separate Monte Carlo and cluster uncertainty, matched MT, convention/home controls; post-hoc follow-up labeled |
| Supported conclusions, applicable conditions, limitations | paper | Every quantitative claim mapped to executed results; local/global distinction; upper bounds only; no causal design hierarchy or minimum certificates |
| Novelty and positioning versus related work | idea supplies; paper reports | Verified permitted literature dossier and checked citations, conditional empirical contribution without unsupported priority claim |
| Complete research paper | paper | PDF and LaTeX with abstract, introduction, related work, methods, experiments, discussion/limitations and bibliography |
| Latest official ICML/ICLR/NeurIPS template, page limit, required checklist | venue supplies; paper completes | Official current-year source/provenance and page rules under `venue/`; actual compiled PDF checked; manuscript-dependent checklist answered truthfully |
| Complete code/environment reproduction | experiment | Pinned dependency versions, CPU requirements, data URLs/revisions/hashes, seeds, commands, measured/estimated runtime distinguished, witness verification, failures/abandoned/uncompleted runs accounted for |
| Every figure/table generated from actual runs | figtab supplies; paper integrates | `presentation/` generator and input/output mapping; rendered `figures/` and `tables/`; artifact-wide README links and runnable paths |
| Public data CPU-only within resource/time constraints | experiment | Provenance and run logs; no paid API/GPU requirement for reproduction; raw data excluded from repository/artifact |
| Only real consulted citations; no invented numbers | idea + experiment + figtab + paper in their outputs | Verified source notes and generated numerical inputs; no placeholders passed off as measurements |
| Avoid withheld study and derivative material | all positions | Restricted-source workflow, no title/author/result inference or broad search targeting that study; accidental encounter log if applicable |
| Disclose LLM assistance and incomplete work honestly | paper with owner records | Accurate assistance statement, failure/omission accounting and completed checklist |
| Final deliverable independently reviewed | paper proposes; internal-review approves | Exact version commit approved, system delivery/contract checks pass, merge to release/final publishes world result |

Context Brief and independent feasibility judgement have now been read and reconciled in the study plan. Their bounded-scope judgement supports proceeding, without asserting final manuscript acceptance. Verified source dossiers continue feeding the manuscript under context ownership. Venue has verified the official NeurIPS 2026 format (nine content pages and 16 completed checklist questions); all declared artifact paths are covered by the settled CODEOWNERS. The actual compiled PDF and checklist still require checking before a version is proposed.
