# Agentic evidence audit feedback

- generated_at: `2026-11-11T14:52:11.755435+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `2`
- audit_json_path: `work/results/t02/claude/20261111_085902/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t02/claude/20261111_085902/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t02/claude/20261111_085902/paper/paper_evidence_audit_raw.txt`

## Summary
Every number in the paper matches the evaluator records and the derived arithmetic, but the three-way decision rule is attributed to the evaluator and called pre-declared without any retained support, and several grounding entries cite source ids that cannot support their claims.

## Findings
- `decision-rule-provenance-1` (Introduction (Contributions), Method (Test statistic and decision rule), Abstract): The retained evaluator source and workload manifests contain no supported/refuted/inconclusive logic. The evaluator only emits the eight metrics and a correct flag. The verdict is computed by the authors' own scripts/derive_resolution.py. The only trace of the rule is a "task contract" mention in paper_strategy.json and paper_strategy.md, which is not an inspectable source for the rule's wording or for when it was declared. The claims_grounding.json entry for the rule cites only the CI endpoints, which support applying the rule but not its content, origin or timing.
  - claim: The paper describes the supported/refuted/inconclusive rule as "the three-way decision rule that the sealed evaluation uses", "declared in advance" and "declared before the final evaluation".
  - evidence: source_evidence/evaluator/evaluate_final.py (aggregate_plane and METRIC_NAMES, no verdict); source_evidence/workload/final_manifest.json (no rule); scripts/derive_resolution.py lines 40-47 (author-side verdict); claims_grounding.json claim[3]; paper_strategy.json narrative_rationale.
  - requested_fix: Say that the verdict is obtained by applying the stated interval rule to the evaluator's reported interval. Remove "the sealed evaluation uses" and the unsupported claim about when it was declared, or attribute the rule to the task protocol and note that its text is not retained in the evidence artifacts.
- `grounding-source-mismatch-1` (Method, Supplementary Information (workloads, parameter counts, compute), Resolution of the design): claims_grounding.json grounds these claims to final.qualification.status (the string "completed") or final.evidence.episodes (four seed records with score, duration and seed). Neither id contains the claimed content, so the refs resolve but do not support the visible claims. The true sources are only named in free-text claim prose and @evidence comments.
  - claim: Workload settings, parameter counts and multipliers, 22 episodes, 1,804 RPC calls, 11,764 s elapsed, the 1.107 and 0.922 slope bounds, and the 35 seed multisets.
  - evidence: claims_grounding.json claims[14]-[17] and the bounds and multiset claims; paper_data.json grounding_sources for final.qualification.status (value "completed") and final.evidence.episodes (episodes list only); source_evidence/workload/final_manifest.json, source_evidence/frozen_model/program.py, source_evidence/final/final_manifest.json compute_usage, derived/resolution.json.
  - requested_fix: Re-point these claims to the files that actually contain the values: the workload manifest, frozen_model/program.py, final_manifest.json compute_usage and derived/resolution.json. Label the bounds and combinatorial counts as derived arithmetic from the protocol constants rather than as supported by the qualification or episode ids.
