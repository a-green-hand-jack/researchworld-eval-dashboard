# Agentic evidence audit

- verdict: `fail`
- finding_count: `2`

## Summary
All numeric results, source-code descriptions and citations match the evidence trail, but two narrative claims go beyond what the grounded evidence supports.

## Findings
### 1. threats-gain-attribution-1 — Discussion and Limitations (Threats to validity)
- claim: The library includes the exact case-6 sigmoid and saturating and count-based shapes close to the grid's other forms, so any gain over linear regression partly reflects a match between the library and the grid.
- issue: This asserts as fact a causal attribution of the 0.180-to-0.126 gain to library-grid matching. The manuscript says elsewhere that it cannot attribute the gain to any mapping or to the gate. No ablation was run, per-case baseline values are unavailable, and per-case gate decisions are unverified.
- evidence: paper.tex Limitations items (4) and (6) and the Case 6 paragraph in Results; paper_data.json ablation_studies is empty and evidence_sources.ablations status is missing; final_evaluation.evaluation_evidence.candidate_diagnostics_trust is unverified; claims_grounding.json has no claim supporting attribution of the gain.
- requested_fix: Reword to a hedged possibility, for example "the gain over linear regression may partly reflect the library containing shapes close to the grid's mechanisms; this was not tested". Keep the statement that no ablation or per-case gate logging exists.

### 2. design-after-search-percase-1 — Method (Frozen BIC-gated exposure library) and Limitations (1)
- claim: It was written after inspecting model-selection results ... the library was designed after seeing model-selection per-case errors
- issue: No claims_grounding.json entry or paper_data.json source records that the library author saw per-case model-selection errors. The same paper says per-case values for the model-selection plane are not part of the verified evidence and are not used. The grounded trace only shows that the three classes were scored sequentially (steps 1, 2, 3) and that only plane means are registered.
- evidence: paper_data.json improvement_trace (step_index 1-3, combined_score only) and grounding_sources result.improvement_001 to result.improvement_003 (plane-mean values only); claims_grounding.json has no claim covering this statement; paper.tex Model-selection paragraph says per-case values for this plane are not part of the verified evidence.
- requested_fix: Narrow both statements to what is grounded, for example "the library was developed after the two earlier estimator classes had been scored on the model-selection seeds". Drop the "per-case errors" wording, or add a grounded source for it.
