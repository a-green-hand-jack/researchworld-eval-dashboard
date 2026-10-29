# Agentic evidence audit feedback

- generated_at: `2026-10-27T17:52:52.636787+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `3`
- audit_json_path: `/home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper/paper_evidence_audit.json`
- audit_markdown_path: `/home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper/paper_evidence_audit.md`
- raw_output_path: `/home/user/orca/projects/researchworld-eval/.project/runs/agentic-scientist-s00-20261027T171535Z/work/results/s00/claude/20261027_171558/paper/paper_evidence_audit_raw.txt`

## Summary
The numeric results and qualification statements match the evidence, but the overview figure is only a placeholder image, one Supplementary detail about the unscored alternative has no artifact support, and one Discussion claim about label noise has no per-graph support.

## Findings
- `overview-figure-placeholder` (Introduction (Figure 1 overview)): The rendered figures/overview_pipeline.png contains only the text "overview_pipeline (placeholder)" and shows none of the pipeline stages, so the caption describes content the figure does not display. The generator failed and figure_manifest.json has source_ids empty for this figure.
  - claim: Overview of the study. A connected graph is reduced to five relabeling-invariant statistics; a ridge model predicts log cover time, which is compared with a Monte Carlo label; the bound, constant and shuffled controls are scored through the same pipeline
  - evidence: Image figures/overview_pipeline.png; figure_manifest.json entry overview_pipeline (fallback_reason "generate-concept-figure exited non-zero (rc=1)", source_ids []); validation_report.json error "Missing required figure from strategy: overview_pipeline".
  - requested_fix: Remove the overview figure, or replace it with a rendered diagram that actually shows the described pipeline. Do not describe a pipeline diagram that is not present.
- `si-alternative-ridge-residual` (Supplementary Information, Selection context): The artifacts identify the alternative only by the title "Resistance-calibrated Matthews predictor for small-graph cover time". "With a ridge residual" appears nowhere in paper_data.json, claims_grounding.json or the source evidence. source_evidence/ contains only the baseline and studied program, with no source for the alternative, so this implementation detail is unsupported.
  - claim: The selection procedure considered one alternative candidate, a resistance-calibrated Matthews-style predictor with a ridge residual, and it produced no score
  - evidence: paper_data.json idea_titles (single title); claims_grounding.json claim on selection context lists only counts and scores, with no description of the alternative; source_evidence/downstream/{baseline,program} are identical, with no alternative program.
  - requested_fix: Reduce the description to the grounded title, "a resistance-calibrated Matthews-style predictor", and drop "with a ridge residual". Keep the statement that it was unscored.
- `discussion-noise-slowest-families` (Discussion and Limitations, Evaluation scope and label noise): This states as fact that label noise is non-negligible for specific families. The retained evidence has only a median relative SE of 0.029, with no per-graph or per-family SEs and no maximum, as the Results section itself says. The claim also conflicts with the paper's statement that label noise explains only a minor part of the error.
  - claim: The labels use about 300 walks per graph, so the noise floor is not negligible for the slowest families
  - evidence: paper_data.json final_evaluation.metrics.mc_rel_se_median = 0.0287 is the only noise statistic; claims_grounding.json has no per-family or per-graph noise claim; paper.tex Monte Carlo uncertainty section says per-graph values were not retained.
  - requested_fix: Rephrase as an explicit unmeasured possibility, for example "per-graph standard errors were not retained, so noise on the slowest-covering graphs cannot be assessed". Remove the assertion that the noise floor is non-negligible for the slowest families.
