# External report review

Commitment: external-review-repo issue #2. Standard: Research objective issue #1 and the frozen files under `/initial-state/inputs/0/`. This repository records independent readings of delivered report versions; it does not supply internal release approval.

## Version record

For each release, record its tag, the delivery revision available in release metadata, artifact names, and the material actually read. Evaluate the report as delivered. Do not infer omitted evidence from the authors' work process. No version has been reviewed yet.

## Questions for a delivered report

1. **Question and contribution.** Does the paper answer both objective questions: the gap between a score used to select a configuration and fresh-question performance, including drivers and consequences, and a more reliable reporting approach with an empirical reliability assessment? Does it distinguish its contribution from the permitted related work without overstating novelty?
2. **What quantity is being estimated?** Are the configuration, search procedure, evaluation unit, score, fresh-question population, and conditioning explicit? Can a reader distinguish the performance of the selected configuration from that of the overall search procedure? Are benchmark transfer, new draws from the same population, and finite held-out scores distinguished where relevant?
3. **Evidence and comparisons.** Are conclusions supported by experiments actually run in this task, including real LLM-generated answers on a real benchmark? Are the search budget, candidate dependence, item sampling, and configuration differences sufficiently described to interpret observed gaps? Are claims about factors and decision consequences evaluated directly, or appropriately limited?
4. **Reliable reporting.** Is the proposed report's target clear? Does its evaluation measure the claimed reliability (for example bias, coverage, error control, or decision error), with uncertainty in that measurement? Are comparisons fair about the questions and computation available? Does the evidence address selection and reuse of evaluation data to the extent the claims require?
5. **Uncertainty and scope.** Are sources of variability identified and repeated observations treated at the correct unit? Are independent test estimates accompanied by their uncertainty rather than equated with known truth? Do simulations distinguish known targets from finite reference estimates? Are multiple comparisons, dependence, distribution assumptions, and small-sample behavior addressed when material to a claim? A theoretically justified method need not establish guarantees beyond its stated assumptions.
6. **Reader reproducibility.** Can a reader connect every substantive result to supplied scripts, data versions, seeds, commands, and environment details? Are model identity/revision, prompts or programs, inference settings, parsing/scoring rules, selection rules, and split definitions available? Are actual resource use and incomplete or failed experiments reported honestly? Assess what the delivery permits a reader to reproduce; do not demand unseen author process.
7. **Required delivery and presentation.** Are PDF and LaTeX source complete, in the latest official template of the chosen allowed conference, within its body-page rules, with any required checklist? Are figures and tables legible and self-contained, and do captions and prose accurately represent the evidence? Are references genuine and sufficiently identified? Respect the frozen prohibition on seeking the withheld study or material discussing it.

These are assessment questions, not a prescribed study design or a requirement for every possible analysis. The burden of evidence scales with the claim and the objective.

## Findings

Open one issue per distinct problem, with:

- version and artifact/location;
- the specific claim or requirement at issue;
- evidence visible to a reader and why the problem matters;
- a concrete correction, clarification, or evidence needed to resolve it;
- severity proportional to its effect on validity or delivery completeness.

Separate missing work from a measured negative result and a scientific limitation from an unsupported claim. Record strengths and an overall assessment in a longer version reading when useful; actionable problems remain in issues. On a later version, verify fixes against the actual delivery, close resolved issues, and state explicitly which older concerns remain. Never invent results or citations to complete a review.
