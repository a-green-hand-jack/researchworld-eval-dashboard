# Agentic evidence audit feedback

- generated_at: `2026-11-11T12:24:35.979205+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `4`
- audit_json_path: `work/results/t10/claude/20261111_094019/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t10/claude/20261111_094019/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t10/claude/20261111_094019/paper/paper_evidence_audit_raw.txt`

## Summary
Reported numbers, coverage statistics, partition composition and search metrics match the artifacts. Four wording problems remain: a theory claim overgeneralised to binary predictors, an unverified plankton-label claim, an untested practitioner recommendation, and a misattributed 3 s deadline.

## Findings
- `binary-predictor-zero-gain-overgeneral` (Introduction (Contributions), Method (headroom), Discussion, Conclusion): Section 3 says two things can shorten a PPI++ interval: letting the weight leave [0,1] when the unclipped optimum exceeds 1, and nonlinearity of E[Y|Yhat]. A two-valued predictor only removes the nonlinearity term. The clip term can still be positive if the unclipped weight exceeds 1, so zero gain for every binary predictor does not follow from the paper's own formula.
  - claim: The gain is zero for any binary-valued predictor / is zero for binary-valued predictors / predicts none for binary-valued predictors
  - evidence: paper.tex Method Eq. for the ceiling and the paragraph on zero-gain conditions (i)-(iii); analysis/headroom_derived.json real.plankton has lambda_unclipped 0.841 (inside [0,1]) and oracle_vs_ppi_pp about 2e-16, so zero is shown only for that pool; real.census_income has lambda_unclipped 1.34 and oracle_linear_vs_ppi_pp 0.0179, showing the clip term is nonzero when the weight exceeds 1.
  - requested_fix: Qualify every statement to say the nonlinearity component is zero for two-valued predictors, and that total gain is zero only when the unclipped optimal weight also lies in [0,1], as for the plankton pool (lambda about 0.84).
- `plankton-label-binary-unsupported` (Results (headroom check), claims_grounding.json claim on plankton): The artifacts establish only that Yhat takes two unique values. No artifact records that the plankton label Y is binary. The cited sources, the plankton log-ratio metric and headroom_derived.json real.plankton, do not support that claim. The zero ceiling needs only a two-valued Yhat.
  - claim: both Y and Yhat are binary in the plankton pool, so E[Y|Yhat] is exactly linear and the ceiling is zero
  - evidence: analysis/headroom_derived.json real.plankton has n_unique_yhat=2 and no field for the number of unique Y values; the cited final.metric.log_ratio_vs_ppi_family_plankton is a width ratio and says nothing about Y; the task data description in paper_prompt.md says nothing about plankton labels being binary.
  - requested_fix: Reword to say the plankton predictor takes only two values, so E[Y|Yhat] is affine and the ceiling is zero. Remove or explicitly qualify the statement that the label is binary, in both paper.tex and claims_grounding.json.
- `practical-reading-untested-recommendation` (Discussion (Practical reading)): This is stated as an attainable benefit, but no unclipped-PPI++ interval was run and its coverage is unknown. The only supporting evidence is a population-level ceiling for a single pool, census income, where 0.0179 of 0.0213 is the unclipped-linear part. The paper elsewhere says the observed gain exceeds the ceiling in four of five families and that the clip-removal experiment was not run.
  - claim: A practitioner who already uses PPI++ ... can obtain most of the predictable gain on a predictor whose optimal weight exceeds one by letting the weight leave [0,1]
  - evidence: paper.tex Limitations (3) and the list of untested experiments (i); Table tab:final unclipped-linear column; analysis/headroom_derived.json oracle_linear_vs_ppi_pp (nonzero only for census_income); no final or search metric exists for an unclipped PPI++ interval.
  - requested_fix: Rephrase as a population-level diagnostic: for census income about 84 percent of the computed ceiling is attributable to the weight clip. State explicitly that attaining it, and its coverage cost, was not tested, and delete the general recommendation to practitioners.
- `si-deadline-misattributed` (Supplementary Information A.1 (settings of the evaluated interval)): The artifacts show the 3 s wall deadline applies to the candidate's estimate RPC. It does not apply to the ppi-python reference or baseline calls, so the sentence misdescribes the evaluator.
  - claim: The reference calls have a 3 s per-estimate deadline.
  - evidence: source_evidence/frozen_winner_estimator.py docstring: Per-call wall deadline: 3 seconds (enforced), on the candidate estimate op; source_evidence/evaluate_final.py RPC_CAP = 3.0, used for candidate RPCs, while compute_baselines calls ppi_py with no deadline.
  - requested_fix: Change to say the evaluated estimator must respond within a 3 s per-estimate deadline enforced by the evaluator, or delete the sentence.
