# Checklist guidance for this study (NeurIPS 2026, 16 questions)

Guidance for `paper-repo`; each answer must be made true by the finished delivery, not by this note.
Answers stay `\answerYes/\answerNo/\answerNA` with a 1-2 sentence justification pointing to a section.

1. Claims: Yes only if the abstract states the conditions/limits found (the objective accepts "small", "depends", "unexpected").
2. Limitations: Yes; dataset count, design coverage, model misspecification (BT), perturbation realism.
3. Theory: NA unless the paper states a theorem; if a bound is stated, give assumptions and proof (appendix).
4. Experimental result reproducibility: Yes only if `code/README.md` plus the seeds, data versions/checksums and commands regenerate every reported number (objective R6-R8); otherwise No with the reason.
5. Open access to data and code: Yes if the repo reproduces every number; data are public (not committed, `data/` per objective) with versions + sha256; anonymised code link/zip required for review.
6. Experimental details: Yes; splits, perturbation definitions, BT fitting settings (regularisation, tie handling), seeds.
7. Statistical significance: Yes only if repeats / CIs / tests are reported (objective requires uncertainty).
8. Compute resources: Yes; CPU only, measured wall time from real runs (not the estimates in `resources.md`).
9. Code of ethics: Yes unless something contrary is found.
10. Broader impacts: Yes; leaderboard manipulation discussed carefully (sensitivity analysis only; no deployable attack tooling beyond what the study needs).
11. Safeguards: NA unless a high-risk asset (new dataset/model) is released; the Arena text is not redistributed.
12. Licences for existing assets: Yes; list each dataset with its licence and version (see R13 in `VENUE.md`); state the undeclared licence of the LLM-judge set if used.
13. New assets: NA if only code is released; otherwise document.
14. Crowdsourcing/human subjects: NA (secondary analysis of public data) - say so.
15. IRB: NA - same reason.
16. Declaration of LLM usage: describe the LLM assistance disclosed under R11 (the study's method does not use an LLM as a component unless the LLM-judge data are analysed, which are existing data).
