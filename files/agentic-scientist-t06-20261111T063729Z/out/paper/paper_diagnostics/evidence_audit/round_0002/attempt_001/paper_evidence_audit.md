# Agentic evidence audit

- verdict: `fail`
- finding_count: `4`

## Summary
Most numbers match the evaluator evidence and the grounded claims. Several visible claims go beyond it: B2's construction is stated as fact, development per-case equality is unsupported, related-work characterisations exceed title-level evidence, and a runtime claim rests on the wrong procedure.

## Findings
### 1. b2-construction-overclaim — Abstract; Introduction (What we find iii, Contributions 3); Results 5.4; Conclusion
- claim: a static first-order influence ranking with refit bisection reaches every one of these budgets; a one-shot influence ranking with refit bisection already attains every budget; the budgets can be viewed as properties of that simple procedure's output
- issue: Only the evaluator-recorded B2 budgets equal the studied budgets. The paper itself says (Sec. 3.5) the evaluator source is not staged and that reading B2 as static influence ranking plus bisection is an interpretation, not a verified fact. The abstract, introduction, results and conclusion nonetheless state this construction as fact. The inference that re-linearisation, leverage correction and polish added nothing also depends on that unverified reading.
- evidence: claims_grounding.json last claim ('construction details are not claimed') and claim 11 (B2 budgets equal the studied ones, recorded outcomes only); paper.tex Sec. 'Comparators and validity controls' (interpretation caveat); paper_data.json final_evaluation episodes record only B2_k and B2_score values.
- requested_fix: Reword every main-text statement to say that the evaluator's recorded influence-only reference (B2) matched the studied configuration's budgets in all six held-out cases. Say explicitly that B2's construction is unverified, and drop or qualify the conclusion that the static ranking alone suffices or that the extra search components contributed nothing.

### 2. dev-equality-unsupported — Results 5.4 (The studied configuration equals influence-only removal)
- claim: The same holds on development tables (Section dev).
- issue: The development evidence has only aggregate totals. The studied configuration scores 0.4993, and the logged influence-only reference is also 0.4993. No development per-case budgets are recorded, so per-case equality of budgets cannot be claimed. Section 5.6 also says these breakdowns are log-quoted and not in the registry.
- evidence: claims_grounding.json claim on search-stage evaluator output (aggregate values only, 'no registry entry beyond the 0.4993 total'); paper_data.json all_programs (only combined_score and per-episode scores); paper.tex Sec. 5.6 and Supplement 'Development tables: additional detail'.
- requested_fix: Delete the sentence, or narrow it to say that on the development tables the aggregate score of the studied configuration equals the logged aggregate influence-only reference score of 0.4993. State that no per-case development budgets are recorded.

### 3. relwork-beyond-title-level — Related Work (Data-dropping robustness; Manipulation of crowd-vote leaderboards)
- claim: Broderick et al. 'show it on published applied analyses'; 'Unlike an approximation-only metric, we accept a removal set only after an exact refit'; the vote-rigging work 'allows an actor to add votes'
- issue: The reference records hold only titles and years, and claims_grounding.json grounds these citations at title or one-sentence level. Broderick is grounded only as 'a finite-sample robustness metric for when dropping a little data changes conclusions'. The vote-rigging paper is grounded only as studying vote-rigging strategies and their effect on rankings. Applied-analysis demonstrations, the 'approximation-only' characterisation and the add-votes setting are not supported. This also conflicts with the LLM Usage statement that related work is described only at the level of the cited titles.
- evidence: references_provenance.json entries for Broderick2020AnAF and 2501.17858 (title, year, venue only); claims_grounding.json claims for ref.s2.f4c5a3ee... and ref.openalex.W4406975857.
- requested_fix: Remove the three unsupported descriptors. Describe Broderick et al. only as proposing a finite-sample robustness metric for when dropping a little data changes conclusions. Describe the vote-rigging paper only as studying vote-rigging strategies against Chatbot Arena and their effect on rankings, without stating what manipulations its setting allows.

### 4. runtime-claim-misattributed — Discussion (Implications for practice); Supplement (Data provenance and reproduction)
- claim: A one-shot influence ranking plus bisection over exact refits certifies small reversal budgets on tables of this size in seconds on a CPU.
- issue: The only timing evidence is 4.45 s and 4.51 s per held-out episode for the full studied configuration. That configuration includes re-linearisation and polish, and the episodes cover all six cases. No timing exists for a one-shot influence ranking with bisection. The hardware is not recorded in the evidence, so 'on a CPU' is unsupported. This also depends on the unverified B2 construction.
- evidence: paper_data.json final_evaluation episodes duration_seconds 4.452 and 4.508; claims_grounding.json claim 6 (durations for the studied configuration only); the paper says B2's construction is not verified.
- requested_fix: Say that the studied configuration's recorded held-out evaluation episodes took about 4.5 s each, and remove the 'one-shot ranking plus bisection' attribution and the 'on a CPU' wording.
