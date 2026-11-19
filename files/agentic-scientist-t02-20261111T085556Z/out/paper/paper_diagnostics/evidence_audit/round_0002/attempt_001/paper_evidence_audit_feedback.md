# Agentic evidence audit feedback

- generated_at: `2026-11-11T14:49:07.233068+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `3`
- audit_json_path: `work/results/t02/claude/20261111_085902/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t02/claude/20261111_085902/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t02/claude/20261111_085902/paper/paper_evidence_audit_raw.txt`

## Summary
The numbers and qualification handling match the final evaluation record, but the abstract overclaims calibration and an unsupported literature gap, and the development-plane wording is looser than the data.

## Findings
- `abstract-calibrated-overclaim` (Abstract): Nothing in the evidence supports "calibrated". The Method section says the plain percentile interval from four clusters (at most 35 distinct resamples) makes no claim of nominal coverage and may not be nominal, and that the interval is only a coarse summary. Qualification (qualified, completed, correct=true) supports validity of the measurement, not calibration of the interval.
  - claim: The evaluation itself was valid, so the result is a calibrated non-answer rather than a failure
  - evidence: paper.tex Method "Caveat on few clusters" and "A coarse bootstrap" paragraphs; claims_grounding.json claim[0] (qualification is integrity of measurement only) and claim[14] (35 multisets); paper_data.json final_evaluation.metrics have no coverage or calibration diagnostic.
  - requested_fix: Replace "calibrated non-answer" with a plain statement such as "a valid but inconclusive measurement", and keep the existing note that the interval's coverage is not guaranteed.
- `novelty-gap-ungrounded` (Abstract and Related Work): The cited sources cover grokking accounts, double descent, and memorization, but no claim or source in claims_grounding.json supports a statement about how much the delay-versus-width dependence has been measured. The abstract states this unhedged, while Related Work hedges it as a non-exhaustive reading. The retrieval plan also flagged a possible prior width-and-grokking-delay paper that was excluded. Memorization capacity is likewise listed as an account of grokking in the abstract without a citation for that role.
  - claim: its dependence on model size has received little systematic measurement (Abstract); none of them has ... measured delay against width under a fixed protocol (Related Work)
  - evidence: claims_grounding.json claims[21]-[32] only ground what each cited paper says; references_provenance.json reference_query_plan forbidden_query_patterns note a possible prior paper on width and grokking delay; paper.tex Abstract sentence 1 versus Related Work "Grokking and its explanations".
  - requested_fix: Delete the "little systematic measurement" claim from the abstract, or qualify it as "to our non-exhaustive reading", matching Related Work. Do not present memorization capacity as a cited account of grokking.
- `dev-plane-wording-1` (Results (Validity checks and development-plane context) and Supplementary Information (Development-plane comparison)): Only the 0.801 seed is just above the V1 mean of 0.798. The other V3 seed (0.899) is about 0.10 above it. The configuration-mean difference V1 to V2 is 0.0308, which rounds to 0.031, not the 0.030 printed. The main text says the differences are "of the same size" as the seed spreads, but the seed spreads (0.051, 0.043, 0.098) are 1.7 to 4.5 times the mean differences (0.031, 0.022). The grounding entry cites only result.improvement_001 to 003, which carry scores only. The censoring counts, final accuracies, controls, and per-seed scores come from source_evidence/search_variants and derived/resolution.json.
  - claim: per-seed scores of V3 (0.801, 0.899) ... lie just above the V1 mean (0.798); differences between them are of the same size as the spread between the two seeds
  - evidence: derived/resolution.json search.variants (seed_scores V1 0.772/0.823, V2 0.807/0.850, V3 0.801/0.899; scores 0.79769, 0.82847, 0.85015); paper_data.json grounding_sources result.improvement_001 to 003 (score values only); paper.tex SI section sec:si-dev and the Results development-plane paragraph; claims_grounding.json claim[18].
  - requested_fix: Rewrite to say the lower V3 seed (0.801) lies just above the V1 mean while the higher seed (0.899) lies above the V2 mean. State the first mean difference as 0.031. Change "same size" to "no larger than the seed-to-seed spreads". Add the search_variants and derived/resolution.json evidence refs to the grounding entry for the censoring, accuracy, and control values.
