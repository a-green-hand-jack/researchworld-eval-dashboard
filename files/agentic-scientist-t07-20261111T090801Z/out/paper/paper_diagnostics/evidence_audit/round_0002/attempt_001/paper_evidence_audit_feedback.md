# Agentic evidence audit feedback

- generated_at: `2026-11-11T10:53:34.177731+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `2`
- audit_json_path: `work/results/t07/claude/20261111_091120/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t07/claude/20261111_091120/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t07/claude/20261111_091120/paper/paper_evidence_audit_raw.txt`

## Summary
Numbers, tables, and the qualification, development, and held-out caveats match the evidence trail, but two wordings go beyond it: "every error metric" and "passes both negative controls".

## Findings
- `every-error-metric-overclaim` (Introduction (Answer paragraph)): The retained outputs give baseline comparisons only for MAE (random mean, anchor points, IRT-style) and for utility against the best baseline. Baseline RMSE, Spearman and Kendall are not retained, and the paper's own Uncertainty paragraph says baseline-specific Spearman values are not part of the retained outputs. The claim therefore covers metrics that were never compared.
  - claim: the point estimates favour the stacked configuration on every error metric
  - evidence: paper_data.json final_evaluation.metrics holds only delta_mae_vs_*, delta_score_vs_* and CI fields as baseline contrasts; claims_grounding.json claims 5-8 ground only MAE and utility gains; paper.tex Experimental Protocol (Uncertainty) and Results sections state that baseline Spearman is not retained.
  - requested_fix: Replace "on every error metric" with "on MAE against all three baselines and on utility against the best baseline", and state that baseline RMSE, Spearman and Kendall were not retained.
- `passes-controls-gate-wording` (Abstract; Discussion (What the evidence supports); Conclusion): "Passes" implies a pass/fail criterion with a threshold. The evaluator only requires the control episodes to be complete and valid, and no control threshold is evidenced. The paper itself says candidate diagnostics are unverified, no gate-level diagnostics exist, and it will not state which criteria underlie the qualified label. The grounded evidence is only the control deltas (permuted Spearman drop 1.157 and MAE rise 0.156; constant MAE rise 0.094), measured on one episode on MMLU-Pro with seed 9101.
  - claim: it also passes both negative controls (single episodes); passes both negative controls
  - evidence: claims_grounding.json claim[12] cites only the control_* metric deltas; source_evidence/evaluate_final.py lines ~1241-1255 and ~1272 (controls_ok is completeness/validity only, with no performance threshold); paper_data.json final_evaluation.evaluation_evidence.candidate_diagnostics_trust=unverified; paper.tex Experimental Protocol (Controls and qualification).
  - requested_fix: Reword to "predictions degrade as expected under both negative controls (single episodes: permuted MAE +0.156, Spearman -1.157; constant MAE +0.094)". Drop "passes", or state explicitly that no pass/fail criterion for the controls is evidenced.
