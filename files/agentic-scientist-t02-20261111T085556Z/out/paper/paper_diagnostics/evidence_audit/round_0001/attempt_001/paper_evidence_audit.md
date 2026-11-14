# Agentic evidence audit

- verdict: `fail`
- finding_count: `3`

## Summary
The main-text numbers, the qualification disclosure and the derived resolution quantities match the evaluator metrics and derived/resolution.json. The development-plane supplement has one false comparison and one unsupported causal inference, and a few implementation and process statements cannot be inspected in the artifacts.

## Findings
### 1. si-dev-span-false — Supplementary Information, Development-plane comparison (and the claims_grounding.json development claim)
- claim: per-seed scores of V3 (0.801, 0.899) spanning the other two means, so no ordering of the configurations is supported
- issue: The V3 per-seed range [0.801, 0.899] contains the V2 mean (0.828) but not the V1 mean (0.798), because 0.801 is above 0.798. The claim that it spans both other means is false, and the unqualified claim that no ordering is supported rests on it.
- evidence: source_evidence/search_variants/variant1_metrics.json (score 0.7977); derived/resolution.json search.variants[2].seed_scores (101: 0.8012, 102: 0.8991); figures/search_variants_descriptive.png panel (a), where the V3 seed-101 dot sits above the V1 mean bar; claims_grounding.json claim on development-plane configurations.
- requested_fix: Replace the sentence with a supportable one, for example: V3 per-seed scores (0.801, 0.899) span the V2 mean (0.828) and lie just above the V1 mean (0.798). With two seeds per configuration, seed-to-seed spread (0.051, 0.043, 0.098) is as large as or larger than the differences between configuration means (0.030, 0.022). Correct the matching claims_grounding.json text.

### 2. censoring-threshold-inference — Supplementary Information (Development-plane comparison) and Discussion (Threshold and time-grid sensitivity)
- claim: All six V2 runs are censored although their mean final held-out accuracy is 0.944, illustrating that the 0.99 threshold, not failure to learn, can produce censoring; runs that end below 0.99 held-out accuracy are censored however close they come to it
- issue: The evidence gives only a six-run mean of final held-out accuracy. It does not say which threshold (training or held-out) was missed, in which runs, or whether any run ended near 0.99. Censoring is defined as never reaching 0.99 at any checkpoint, not as ending below it. The paper itself states that censoring merges not-fitting and not-generalizing and that the artifacts cannot separate them. The causal attribution to the threshold is therefore unsupported.
- evidence: source_evidence/search_variants/variant2_metrics.json (final_val_acc_mean 0.944, censored_fraction 1.0, no per-run fit or generalization steps); paper.tex Censoring paragraph and Scope section; source_evidence/evaluator/evaluate.py delay_gap (censored if fit or gen is None).
- requested_fix: Qualify the sentence. Say only that all six V2 runs were censored while their mean final held-out accuracy was 0.944, and that the retained records do not show whether censoring came from a missed training threshold or a missed held-out threshold, or how close individual runs came to 0.99. Remove the claim that the threshold, not failure to learn, produced the censoring.

### 3. uninspectable-process-claims — Discussion (What would resolve it, item iv), Supplementary Information (Analyses not performed, Reproducibility)
- claim: a sweep script for the exponent exists but was not executed; the sealed evaluation was run once
- issue: No sweep script appears in source_evidence/, scripts/ or any other readable artifact. The only support is the agent's internal strategy notes. Nothing in the evaluator records or manifests shows how many times the sealed evaluation was run. The paper cites no inspectable source for either statement.
- evidence: Directory listings of source_evidence/ and scripts/ (only derive_resolution.py, build_figures.py, write_prov.py, and the evaluator and model sources); source_evidence/final/final_manifest.json (a single started_at and completed_at pair, no run-count field); the only mention of the sweep script is in paper_strategy.md and memory.md.
- requested_fix: Remove, or qualify as not verifiable from the retained artifacts, the statements that a sweep script exists and that the sealed evaluation was run once. Keep the point that no exponent sweep or matched ablation has results.
