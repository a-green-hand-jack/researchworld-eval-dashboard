# Agentic evidence audit feedback

- generated_at: `2026-11-11T08:44:17.929927+00:00`
- ok: `False`
- verdict: `fail`
- finding_count: `3`
- audit_json_path: `work/results/t03/claude/20261111_071336/paper/paper_evidence_audit.json`
- audit_markdown_path: `work/results/t03/claude/20261111_071336/paper/paper_evidence_audit.md`
- raw_output_path: `work/results/t03/claude/20261111_071336/paper/paper_evidence_audit_raw.txt`

## Summary
All numbers and derived quantities match the sealed metrics, derived_metrics.json and the source files, and the qualified outcome is reported correctly. Three wording claims go beyond what the evidence trail supports.

## Findings
- `control-attribution-chiefly-budget` (Results, How much is instance-specific?): The text assigns most of the permutation-retained 0.0216 gain to budget and prior, but no budget-only constant, prior-only variant or per-cell breakdown was evaluated. The paper itself says the control cannot separate budget calibration from dataset or family calibration and that the prior-alone comparison was not run, so "chiefly" is an unsupported attribution.
  - claim: The retained part is knowledge the diagnostic holds about the episode: chiefly the budget, through the prior, and any dataset- or family-level shifts in its simulated values.
  - evidence: paper.tex Results section on the permuted control, versus paper.tex Discussion (What the control tells us) and the Results sentence that the control does not separate budget from dataset or family calibration; paper_data.json ablation_studies is empty; claims_grounding.json only supports the 0.0216 (61%) / 0.0137 (39%) split via combined_score, skill_vs_always_reliable and control_permuted_score.
  - requested_fix: Replace "chiefly the budget, through the prior" with a hedged statement such as "episode-level information that may include budget through the prior and dataset- or family-level shifts; the evidence does not apportion it". Make the later "consistent with knowing the budget" sentence match.
- `held-out-datasets-wording` (Abstract / Introduction / Experimental protocol): One of the three final datasets, German Credit half B (485 rows), is the other hash-parity half of the German Credit data whose half A (515 rows) was a search-plane dataset used to select the configuration. It is disjoint by record hash only, not a separate dataset, and the abstract and introduction do not say so. This could be read as three independent datasets.
  - claim: On three held-out tabular datasets ... held out from the selection of the diagnostic.
  - evidence: source_evidence/final_resources_manifest.json (german_B, UCI 144, partition rule hash%2==1) and source_evidence/search_resources_manifest.json (german_A, UCI 144, hash%2==0); paper.tex Supplementary Table tab:data; paper.tex Statistical limits says only "disjoint ... by record hash".
  - requested_fix: In the abstract and introduction, qualify the wording, e.g. "three datasets disjoint by record hash from the search data, one of which is the complementary half of a search-plane German Credit split". Note that the German Credit result is not from an independent source dataset.
- `constants-untuned-abstract` (Abstract / Supplementary Table tab:consts): The abstract's "hand-set and untuned" does not mention that the budget-prior constants 0.84 and 0.96 were taken from aggregate label means of earlier search-plane evaluations. The prior is data-derived from evaluator outputs, and the paper's own limitations say search scores informed it. "Untuned" overstates how independent the constants are of search-plane label statistics. The supplementary table caption has the same gap.
  - claim: constants are hand-set and untuned; Constants of the frozen self-diagnostic. None was fitted to instance labels.
  - evidence: source_evidence/selected_config_NOTES.md ("Prior values 0.84 / 0.96: aggregate label means by budget seen in earlier evaluation metrics"); source_evidence/selected_config_program.py lines 35-46 comment; paper.tex Method (provenance paragraph) and Statistical limits; paper_data.json final_evaluation.metrics mean_label_low_budget and mean_label_high_budget.
  - requested_fix: Reword the abstract to "weights and shrinkage constants are hand-set and untuned, and the budget prior was taken from earlier search-plane aggregate label means". Amend the Table tab:consts caption to say the prior values come from aggregate search-plane label means.
