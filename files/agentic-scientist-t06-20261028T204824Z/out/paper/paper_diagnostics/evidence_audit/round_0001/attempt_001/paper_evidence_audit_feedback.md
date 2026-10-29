# Agentic evidence audit feedback

- generated_at: `2026-10-28T21:48:22.794928+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `3`
- audit_json_path: `work/results/t06/claude/20261028_204856/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t06/claude/20261028_204856/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t06/claude/20261028_204856/paper/paper_evidence_audit_raw.txt`

## Summary
All reported metrics, selection context and qualification facts match the evidence, but a few visible claims go beyond the grounded artifacts: design sizes and model counts, the permuted-control generalization, and the description of one cited work.

## Findings
- `design-size-ungrounded-1` (Evaluation designs (Table 1) and Candidate explanations): No claims_grounding.json claim, paper_data.json grounding source or source_evidence file gives row counts or competitor counts. The task contract and evaluate_final.py record no per-design sizes or competitor counts, and the "six models" figure appears only in the agent-written reference_query_plan rationale. The paper's own Table 1 caption says no row counts are used, and its text says gaps and row counts per design are not available. Stating "the largest dataset" and an exact model count contradicts that and is not artifact-backed.
  - claim: Table 1 lists crowd votes as "Many chatbots; the largest dataset" and both MT-Bench designs as "Six models", and the number-of-competitors bullet says "MT-Bench data involve six models, whereas the crowd and sports data involve more competitors."
  - evidence: paper.tex Table 1 rows and caption, and the Candidate explanations bullet on competitors; claims_grounding.json has no claim for these; task_contract.json final data roles list no sizes; "six models" appears only in reference_query_plan.json and references_provenance.json query rationale.
  - requested_fix: Delete "the largest dataset" and the exact "Six models" figures from Table 1 and the competitors bullet, or qualify them as unverified context not drawn from the evaluation artifacts. For example, say the designs differ in size and competitor count in ways not measured here.
- `perm-control-overreach-1` (Results, Validity checks and run-to-run behaviour): The grounded fact is only that final.metric.perm_control_abs_gap equals 0.0. By evaluate_final.py this is the mean absolute score difference over one control episode per case (CONTROL_SEED 201) against the primary seed-201 score, using one permutation of each of 12 cases. That supports "no difference was observed on these control runs", not a general statement that the scores are independent of row order or labels.
  - claim: The permuted-input control gap is 0.0, "so ... the measured scores do not depend on row order or competitor labels."
  - evidence: paper_data.json grounding_sources final.metric.perm_control_abs_gap (value 0.0); claims_grounding.json claim "Valid proposal rate 1.0 and permuted-input control gap 0.0"; source_evidence/task/evaluate_final.py lines ~293-295 and ~951-957; paper.tex Section 5.4.
  - requested_fix: Reword to say that on the single permuted control run per case the proposer's scores matched the unpermuted scores (mean absolute gap 0.0). Remove the general claim that scores do not depend on row order or competitor labels.
- `related-work-yang-description-1` (Related Work (Data poisoning and label-flip attacks)): The only provenance for this reference is a title, "Efficient Preference Poisoning Attack on Offline RLHF", with no abstract or text. The detailed technical description (log-linear DPO, parameter-independent gradient shift, sparse approximation) is not supported by any inspectable artifact. Seetharaman2021Influence is also cited as the subject of poisoning research, but its retrieved title is a defense paper.
  - claim: Yang2026Preference studies "label-flip attacks on log-linear direct preference optimisation, observing that flipping one preference label shifts the gradient independently of the parameters, which turns the choice of flips into a sparse-approximation problem."
  - evidence: references_provenance.json entries ref.openalex.W7160306608 (title only) and ref.openalex.W4287201019 (title "Influence Based Defense Against Data Poisoning Attacks in Online Learning"); claims_grounding.json related-work claim is labelled "qualitative positioning" only.
  - requested_fix: Limit the Yang2026Preference sentence to what the retrieved title supports (a preference-poisoning attack on offline RLHF). Remove the unverified mechanism details, and describe Seetharaman2021Influence as a defense against poisoning in online learning.
