# Independent internal review commitment

I own the independent judgement and Forgejo approval/request-changes review for every proposed report version into `paper-repo` release or final. This is not authorship of the analysis, figures, report, or venue decision. I will inspect the exact candidate head and its built deliverables, and record that revision and all actionable findings here before deciding.

## Governing material

The Research objective (internal-review-repo#1) and all five frozen files under `/initial-state/inputs/0` define the standard. The study must answer how reliability of conformal sets for compositional outputs is evaluated and when the compared methods are appropriate. Synthetic-only evidence and measured negative findings are admissible. A complete paper (PDF and LaTeX), complete code and reproducibility instructions, the latest official template of the chosen ICML/ICLR/NeurIPS venue, its page limit, and its required checklist are mandatory. The supplied prohibited study and its derivatives must not be sought, inferred, read, or used. The idea owner's Brief and sourced reading record, story's agreed division, venue's requirements, and each owner's commitment will refine the checks without narrowing the objective.

## Scientific checks

1. The target, observables, data-generating process, score, prediction region and coverage event must be explicit. Composition coverage, class-label coverage, and coverage of a transformed response are different estimands.
2. Claims about exchangeability, marginal and subgroup coverage, calibration quantiles, tuning independence, ties, zero handling and shift must match both mathematics and implementation. Any theoretical analysis needs derivation and numerical checks; it must distinguish standard results from contribution.
3. The completed experiment must answer explicit research questions and compare meaningful baselines and controls. Required evaluation cannot be replaced by a pilot or an undisclosed omission. Method rankings must address coverage and efficiency together, using comparable efficiency units and clearly scoped conditions.
4. Numbers, confidence intervals and conclusions must trace to actual run outputs, inputs, seeds and code. Independent repeated datasets/calibrations must underpin reported uncertainty when the claim averages over calibration randomness; paired methods need paired comparisons. Monte Carlo integration uncertainty must be identified, and pointwise intervals must not imply simultaneous inference.
5. Claims must be supported cell by cell, including failures and sensitivity studies actually used in their support. Synthetic designs and a controlled shift cannot establish arbitrary real-world, high-dimensional, boundary, or covariate-shift conclusions. Missing implementation is unfinished work, not a demonstrated impossibility.
6. Prior work must be real, actually consulted, and sufficient to substantiate positioning, including the distinction between regression/composition regions and conformal classification. The paper need not reach a predetermined positive or negative conclusion.

## Artifact and venue checks

At the reviewed head I will read the complete rendered paper and inspect every delivered figure visually, including appendix/supplement figures. Blank, placeholder, unlabeled, clipped or unreadable figures are defects even if their generation script exists. I will check table values, figure/text agreement, links and included files, and source-to-output mappings. I will check the official template/version, main-text boundary, page limit and checklist against venue's supplied evidence. I will inspect and exercise reproducibility code as needed to resolve scientific concerns, record what was rerun, and avoid claiming that unrun checks passed.

## Review record and coordination

Each version receives a record naming the full exact candidate SHA, inspected artifacts, checks performed, findings and disposition. An unsupported candidate receives a Forgejo request-changes review listing all currently actionable findings. Findings owned outside paper go to the responsible accessible owner, or through a neighbor. An approval is only for the inspected head after the objective and Brief are reread and open findings are resolved. No candidate is currently available; the pilot is not a completed research delivery.
