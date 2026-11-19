# External review record

The research objective is `world/external-review-repo#1`. Commitment: issue #2.
The review unit is a version published as a release of `world/result`, including
its report and reproduction material. No version existed at the initial check
on 2026-11-03. This is a review standard, not a review of future work.

## Questions for the released report

- Is the research question meaningful and the contribution distinguished from
  the prior work actually cited and read? Respect the task's excluded-material
  restriction; do not seek to identify the prohibited paper.
- Are the score matrix, task and model inclusion, score direction and scales,
  missing observations, aggregation rules, ties, and target selection explicit?
  Does “first” mean a sole winner or a shared maximum?
- Is investment defined operationally, with a clear intervention space,
  feasible score bounds, costs, and assumptions about other tasks and models?
  Does the paper distinguish an assumed score change from demonstrated
  effects or costs of incorporating task data into training?
- Can a reader check the investment minimum or bound claimed, including
  optimality, infeasibility, numerical tolerance, and special cases? Are
  comparisons across rules made on a justified common basis?
- Do public, identified data snapshots support the generalizations made?
  Are controls and sensitivity analyses appropriate to the claims, including
  attainable score gains, costs, ceilings, model pools, and ties where relevant?
- Is uncertainty reported and interpreted for its actual source? Distinguish
  deterministic results on a fixed matrix from sampling or evaluation noise;
  do not require stochastic repetitions of an exact deterministic calculation.
- Do tables, plots, and prose agree? Are effect sizes, denominators, exceptions,
  and failure conditions visible, including any reversals of rule comparisons?
- Can the delivered code recreate the evidence using documented versions,
  hashes, dependencies, seeds where applicable, commands, expected runtime,
  and a figure/table-to-script mapping? Are uncompleted runs disclosed?
- Does the complete PDF and LaTeX delivery meet the selected current official
  conference template, main-text page limit, required sections and checklist?

## Recording findings

Each substantive problem gets its own issue in this repository. State the
release tag and exact revision, the relevant report location or artifact,
what the evidence does and does not establish, why it matters, and a concrete
resolution criterion. Review the delivered work, not its development process.
Subsequent versions must be checked against outstanding findings; close an
issue once the delivered evidence resolves it. Do not treat a promised analysis
or a disclosed omission as completed evidence. Do not invent a finding when
no report has been released.
