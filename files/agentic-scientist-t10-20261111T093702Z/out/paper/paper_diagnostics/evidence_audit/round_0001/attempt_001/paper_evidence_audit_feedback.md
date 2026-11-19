# Agentic evidence audit feedback

- generated_at: `2026-11-11T12:21:08.662099+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `1`
- audit_json_path: `work/results/t10/claude/20261111_094019/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t10/claude/20261111_094019/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t10/claude/20261111_094019/paper/paper_evidence_audit_raw.txt`

## Summary
Numbers, coverage and qualification wording check out against the artifacts, but the Supplementary sealed-evaluation runtime of 1400 seconds has no support in the evidence trail.

## Findings
- `si-sealed-runtime-unsupported` (Supplementary Information, Search-pool metrics and sealed-evaluation details): The 1400 s elapsed time appears in no artifact. The only cited evidence (paper_data.json final_evaluation.evaluation_evidence.episodes) holds five partition entries with durations of about 265 to 267 s each, which sum to about 1332 s. It has no total elapsed time and no episode count of 680. The 680 figure is derivable from evaluate_final.py constants (REPS_MAIN=100 x 5 families, REPS_CONTROL=30 x 2 bases x 3 control types), but the cited ref does not show it.
  - claim: The sealed evaluation used 680 episodes (500 main and 180 control) and took 1400 seconds of the 5400-second budget.
  - evidence: paper.tex Supplement, Search-pool metrics and sealed-evaluation details paragraph; claims_grounding.json claim 'Sealed evaluation: 680 episodes ... 1400 s elapsed' (source id final.evidence.episodes); paper_data.json final_evaluation.evaluation_evidence.episodes (5 entries, seeds 9101-9105, durations sum 1332.27 s); grep for 1400 finds it only in paper.tex and the grounding claim, not in paper_data.json, analysis/ or source_evidence/.
  - requested_fix: Remove the 1400-second figure, or replace it with the supported 'the five reported partition durations sum to about 1332 s'. Source the 680-episode count (500 main plus 180 control) to the REPS_MAIN and REPS_CONTROL constants in source_evidence/evaluate_final.py. Update the claims_grounding.json entry to match.
