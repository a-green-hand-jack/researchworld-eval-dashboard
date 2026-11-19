# Agentic evidence audit

- verdict: `fail`
- finding_count: `3`

## Summary
Headline numbers, derived quantities, figures and implementation constants match the evidence trail, but three visible statements go beyond what the retained evidence supports.

## Findings
### 1. slice-axis-advantage-1 — Discussion and Limitations (Threats to validity)
- claim: so part of its advantage on the slice axis reflects a match between method and metric by design
- issue: The sentence asserts that the procedure has an advantage on the slice axis. The paper itself says per-axis baseline values are not retained and that the composite margin does not show dominance on each axis, so no slice-axis advantage over any baseline is measured. The implied attribution to method-metric alignment is also not tested.
- evidence: paper.tex Discussion (What the evidence supports says per-axis baseline values are not retained; What it does not support (ii) says only the best baseline score is retained); claims_grounding.json has no per-axis baseline claim; paper_data.json final_evaluation.metrics holds only aggregate best_baseline_score and margin; the evaluator's classwise baseline calibrates per label for every K.
- requested_fix: Rewrite to a conditional statement, for example: for K<=10 the evaluator slices coincide with the procedure's Mondrian groups, so slice-axis results may partly reflect this alignment; no per-axis baseline comparison is retained, so any slice-axis advantage is unmeasured.

### 2. h2-sealed-gap-1 — Method (Design rationale and hypotheses)
- claim: H2 is addressed by the development comparison V1 versus V2 and by the sealed shift-case gap
- issue: The sealed shift-case gap (0.0536) is a single absolute value for the weighted procedure. No sealed unweighted counterpart or baseline shift gap is retained, so it cannot address whether the weighting reduced shift under-coverage. Only the development V1 versus V2 comparison (0.0613 to 0.0201, three seeds) bears on H2. The sealed gap is in fact larger than the development value.
- evidence: paper_data.json final_evaluation.metrics.shift_coverage_gap=0.0536 with no sealed V1 or baseline shift metric; derived/derived_stats.json variants V1 and V2 shift_coverage_gap; claims_grounding.json claim on development versus final shift gap says cause not isolated.
- requested_fix: Say H2 is supported only descriptively by the development V1 versus V2 comparison on three seeds. State that the sealed shift gap is reported as a residual and does not test H2.

### 3. conditional-impossibility-1 — Related Work (Conditional validity)
- claim: Exact conditional coverage is impossible in general without further structure, which has motivated relaxations that target class-, group- or feature-conditional guarantees (Gibbs2023, Bairaktari2025)
- issue: The impossibility statement and its motivational link to the cited works have no claims_grounding.json entry and no retained evidence. The grounding describes these references by title and venue only. The titles ('Conformal prediction with conditional guarantees', 'Kandinsky Conformal Prediction: Beyond Class- and Covariate-Conditional Coverage') do not establish the claim, and the paper says elsewhere that such descriptions rest on titles and venues alone.
- evidence: claims_grounding.json related-work claim for Gibbs2023ConformalPW and Bairaktari2025KandinskyCP is limited to 'titles and venues'; references_provenance.json holds only title, venue and year for both; no source id supports an impossibility result.
- requested_fix: Remove the impossibility sentence, or state it as general background without attributing it to these citations. Describe the cited works only as addressing conditional-coverage guarantees, as their titles indicate.
