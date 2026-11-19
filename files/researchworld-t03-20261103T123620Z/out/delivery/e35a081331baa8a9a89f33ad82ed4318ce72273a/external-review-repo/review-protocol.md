# Outside-reader review protocol

## Scope and evidence

Read each version as a venue reviewer receiving a submission: the manuscript and its delivered supporting material are the evidence. Re-read Research objective #1 before judging each version. Record the release tag, full delivery revision if supplied, artifact names, and locations relevant to each finding. Review new versions against both the objective and unresolved earlier findings.

Do not infer results from plans or unpublished work. Do not inspect other positions' working code or reconstruct the making of the study. The required reproducibility code attached to the published delivery is reader-facing supporting material and can be assessed as such. Do not seek the withheld prior study or material discussing it. The restriction is stated in the frozen `deliverable.md` and remains binding during review.

## Questions the delivered paper must answer

1. **Question and contribution.** Is the practical decision about using one SHAP run explicit? Is the contribution situated against literature actually cited, with claims of novelty proportionate to the comparison? Does the meaning of “reliable” follow from a declared use rather than from an unexplained score?
2. **Estimand and randomness.** Are model, input, output scale/class, feature units or grouping, background distribution, and attribution semantics identified? Does the paper distinguish randomness of the explainer from background sampling, model training, or data splits? Are repeated explanations compared for the same declared target?
3. **Measures and comparison standards.** Are magnitude, sign, and feature ranking/set claims supported by appropriate defined measures, including treatment of ties and near-zero attributions? Are thresholds and reference choices justified? Does the evidence distinguish agreement across runs from agreement with an accurate reference? A repeatable estimate alone does not establish attribution accuracy or usefulness for a high-stakes decision.
4. **Finite-budget evidence.** Are datasets and multiple model families sufficiently described, and selection reasons stated? Are sample sizes, seeds, repetitions, budgets, runtime hardware, and budget units explicit? Does any higher-budget or exact comparator have its own accuracy or convergence evidence? Are cost comparisons interpretable when explanation algorithms differ?
5. **Uncertainty and statistical unit.** Is the source and target of uncertainty explicit? Do intervals or tests respect shared instances, models, seeds, or dependent run pairs? Are averages accompanied by evidence adequate for claims about individual explanations or failure rates? Are subgroup, condition, and budget comparisons scoped to the observations and uncertainty shown?
6. **Claim coverage and limits.** Does each numerical and qualitative claim have displayed evidence with denominators and applicable conditions? Are negative, inconclusive, failed, and unfinished results differentiated? Are stability, model fidelity, predictive performance, causal interpretation, and deployment justification kept conceptually distinct? Are extrapolations beyond sampled datasets, instances, models, attribution semantics, or budgets acknowledged?
7. **Reader reproducibility.** Can a reader obtain the stated data versions, construct the same splits/preprocessing, fit or load the fixed models, rerun the explanation repetitions, and regenerate every reported table and figure from the attached code and commands? Are dependency versions, seeds, runtime estimates, data provenance, and script-to-artifact mappings supplied? Do manuscript definitions and reproduction instructions agree?
8. **Complete delivery and presentation.** Does the delivery include PDF, LaTeX, code, and reproduction instructions? Does it use the selected latest official ICML, ICLR, or NeurIPS template, respect that venue's page limit, and include any required checklist? Are the required paper sections present? Are axes, units, captions, legends, and tables legible and sufficient to evaluate the claims?

These are review questions, not a requirement to use a particular estimator, metric, dataset beyond the objective, or analysis method. A justified alternative is evaluated on the evidence it supplies.

## Findings and resolution

Open one issue per distinct substantive problem. Include:

- Version and artifact/location read.
- The claim or reader need at stake.
- The evidence shown and the specific gap or inconsistency.
- The consequence for interpretation or reproducibility.
- A concrete question to the authors or evidence/change needed for resolution.
- Severity and whether the point affects a main claim or a narrower presentation detail.

Do not file anticipated problems before a report exists. Do not use an absence of a version as evidence that a study result is negative. Record an honest favorable assessment when a claim is supported; an external review need not manufacture objections.

Replies are assessed against the cited version. If an explanation answers a question but a reader still needs that explanation in the delivered artifact, keep the finding open until a version supplies it. When a later version resolves a finding, record the version and basis and close the issue. Reopen if a subsequent version reintroduces it.
