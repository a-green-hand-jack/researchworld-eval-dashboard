# Agentic evidence audit feedback

- generated_at: `2026-11-11T08:37:06.721825+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `3`
- audit_json_path: `work/results/t06/claude/20261111_064241/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t06/claude/20261111_064241/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t06/claude/20261111_064241/paper/paper_evidence_audit_raw.txt`

## Summary
The numbers match the recorded evidence, and the no-winner, qualification and scope caveats are handled correctly. Three wording and figure issues still assert things the evidence does not record: B3's construction, the non-vacuity threshold, and the "additional search machinery" framing.

## Findings
- `controls-nonvacuity-threshold-1` (Results/Controls (Figure 3 caption and figure image)): The evidence records only a boolean nonvacuous=true and the spread ratios (0.088, 0.160). It records no threshold. The manuscript says this itself ("The evidence does not state the thresholds or construction details behind the non-vacuity indicator ... we make no claim about them"). The caption and plot assert a specific evaluator limit that no artifact supports.
  - claim: Figure 3b caption: "with the evaluator's non-vacuity limit of 0.5"; the plotted dashed line is labelled "evaluator limit 0.5".
  - evidence: derived/final_stats.json permutation_controls (F5, F6 contain only bt_std_ratio, expected_moved_fraction, moved_fraction, nonvacuous); paper_data.json only contains 'nonvacuous' flags; scripts/build_figures.py line 91-92 hard-codes the 0.5 line; claims_grounding.json claim on controls lists no threshold; paper.tex Section 3.4 (method_comp) final sentences.
  - requested_fix: Remove the 0.5 line and the phrase 'evaluator's non-vacuity limit of 0.5' from Figure 3b and its caption. Report only the recorded spread ratios and the evaluator's non-vacuous flag.
- `b3-construction-claim-1` (Problem Setup and Method, 3.4 Comparators and validity controls): The same paragraph says the evaluator source is not staged and B1-B3 construction is not verified. This sentence nonetheless states what B3 is (hand-built, no gradient). The evidence trail records only B3's budgets and scores.
  - claim: "B3 is described by the evaluator only as an opponent-targeted removal, and we treat it as a hand-built comparator that needs no gradient."
  - evidence: claims_grounding.json claim 'Evaluator source for comparators B1-B3 and the controls is not staged; only recorded outcomes ... are reported and construction details are not claimed'; derived/final_stats.json holds only b3_k, b3_percent and b3_score; paper.tex Section 3.4.
  - requested_fix: Delete the clause 'we treat it as a hand-built comparator that needs no gradient'. Keep only that B3 is recorded by the evaluator as an opponent-targeted removal, with its recorded budgets.
- `search-machinery-overreach-1` (Abstract; Introduction (What we find iii, Contributions 3)): This wording presents the B2 reference as the studied configuration minus its extra steps. The body says B2's construction is unverified, that B2 is not asserted to equal step (a), and that no conclusion about the re-linearisation, leverage correction or polish may be drawn. The abstract and introduction therefore overreach the grounded claim, which is only that the recorded budgets coincide with the evaluator's influence-only reference.
  - claim: Abstract: "these data show no measured gain from the additional search machinery"; Introduction (iii): "the held-out data show no measured improvement from the additional search machinery."
  - evidence: paper.tex Sections 3.4 and 4.4 ('we do not conclude ... that the re-linearisation, leverage correction and polish contributed nothing'); claims_grounding.json claim 'B2's construction is unverified and no conclusion depends on it'; claims_grounding.json claim 'B2 is not asserted to equal any step of the studied configuration'.
  - requested_fix: Rephrase both places to say the studied configuration's recorded budgets equal the evaluator's recorded influence-only reference budgets in all six held-out cases, so no measured reduction relative to that reference is observed. Drop the reference to the 'additional search machinery'.
