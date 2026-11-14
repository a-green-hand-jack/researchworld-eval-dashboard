# Agentic evidence audit feedback

- generated_at: `2026-11-11T10:22:54.673477+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `1`
- audit_json_path: `work/results/r02/claude/20261111_085834/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/r02/claude/20261111_085834/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/r02/claude/20261111_085834/paper/paper_evidence_audit_raw.txt`

## Summary
The results, qualification facts, development numbers and derived quantities match the evidence trail; one implementation-specific description of negative control C3 misstates the evaluator's pass rule.

## Findings
- `c3-control-rule-1` (Method (Baselines, negative controls and validity conditions)): The evaluator's C3 check is one-sided. It requires only cov >= target - tol and mean_size >= target*K - 1, so over-coverage up to full sets passes. The word near implies a two-sided closeness requirement that the source does not impose, and it clashes with the paper's own point that one-sided metrics do not penalise over-coverage.
  - claim: (C3) uniform probability inputs, where coverage must be near target and mean set size at least (1-alpha)K-1.
  - evidence: source_evidence/evaluator/evaluate.py control_verdicts (the else branch: passed = o["cov"] >= o["target"] - o["tol"] and o["mean_size"] >= o["target"]*o["K"] - 1.0); paper.tex Method, negative-controls paragraph.
  - requested_fix: Reword C3 to say that coverage must be at least the target minus a tolerance, and that mean set size must be at least (1-alpha)K-1. Remove the near-target wording and state that over-coverage is not penalised by this check.
