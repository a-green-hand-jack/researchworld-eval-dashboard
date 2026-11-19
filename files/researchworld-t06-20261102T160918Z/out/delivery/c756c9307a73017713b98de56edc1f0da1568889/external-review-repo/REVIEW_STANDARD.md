# External review standard

This position reviews the report and artifacts delivered in each release of
`world/result`. The controlling requirements are Research objective #1 and its
frozen inputs under `/initial-state/inputs/0/`. This is a review protocol, not a
review of a report that has not yet been released.

## Review record

For each available version, record its release tag, delivery revision where
provided, artifact names, and the report sections, figures or tables supporting
an observation. Read the report as delivered, not the other positions' development
history. Separate a demonstrated error, missing evidence, ambiguous description,
and a suggested extension. Each unresolved substantive problem gets its own
issue, with the version, evidence, effect on acceptance or claim, and a concrete
resolution criterion. Reassess issues against subsequent released revisions and
close those resolved. A lack of a first release is not a scientific criticism.

## Questions the submission must answer

1. **Question and contribution.** Is ranking stability defined operationally?
   Does the contribution matter and is its relationship to the literature clear?
   Judge novelty from the report's supported positioning, without searching for
   or accessing the study that the objective withholds.
2. **Data and scope.** Do the results use real public data from at least two
   distinct evaluation designs? Are snapshots, inclusion rules, participant
   definitions, repeated observations and ties explained? Do the conclusions
   distinguish differences between datasets from causal effects of evaluation
   design? Two datasets alone do not identify such a causal effect.
3. **Estimand and fitting.** Are the ranking population, target comparison,
   model, objective, identifiability convention, regularization, tie treatment
   and fitting diagnostics specified sufficiently to interpret the result?
   Are isolated participants, disconnected comparison graphs, separation and
   close or tied baseline scores handled or bounded where relevant?
4. **Perturbation and budget.** What exactly can be changed: labels, deletions,
   additions, weights or comparison identities? What information does a targeted
   strategy use? Is cost defined at a meaningful observational unit and normalized
   transparently across datasets? Are random and targeted changes compared at
   commensurate costs where the claims require them? Label heuristic outcomes as
   achieved perturbations rather than certified minimal budgets unless justified.
5. **Evidence for each claim.** Trace every major abstract and discussion claim
   to a displayed measurement. Are rank displacement, order reversal, winner
   stability or top-k metrics appropriate to that claim? Does a global rank metric
   conceal the local instability being discussed? Are baselines and controls
   adequate for the claimed contribution? If an approximation selects edits,
   does the delivered evidence establish what exact refitting achieves?
6. **Uncertainty and interpretation.** Are seeds, repeated runs and uncertainty
   summaries supplied where needed? Does the text distinguish variation in the
   edit search, random perturbations and sampling uncertainty in the observations?
   Is the resampling unit defensible for shared prompts, judges or repeated games?
   Are differences in sample size, participant count, graph structure and baseline
   margins considered before generalizing across evaluation designs? A negative
   result is acceptable when supported and appropriately scoped.
7. **Reproduction.** Can a reader obtain the stated data versions and reproduce
   the reported results using the delivered code? Check dependency versions,
   checksums, preprocessing, seeds, commands, expected CPU/runtime requirements,
   and the mapping from every table and figure to generating scripts and outputs.
   Inspect artifacts within access and undertake bounded checks where useful;
   do not substitute a new analysis for evidence absent from the report. Distinguish
   failures actually observed from details merely missing from the instructions.
8. **Presentation and compliance.** Is the PDF legible, self-contained and
   consistent with its source and artifacts? Are definitions, denominators,
   uncertainty, captions and numerical precision clear? Does it contain all
   required sections, official current chosen-conference template, page-limit
   compliance and applicable checklist? Are citations checkable and limitations,
   unfinished work, failed runs and LLM assistance disclosed as required?

## Ownership and access

The outputs of this role are review issues in its own repository and, when
useful, a longer reading in its wiki. The paper and internal-review positions
watch these issues. External review does not approve the release, produce another
position's deliverables, or infer validity from the development process. Issues
must state what a reader needs to assess the delivered claim, rather than mandate
an unnecessary implementation or prescribe a favorable result.
