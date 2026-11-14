# Agentic evidence audit

- verdict: `fail`
- finding_count: `1`

## Summary
The numbers, per-seed scores, partition counts, hyperparameters, qualified outcome and identity caveats all match the evidence trail. One Supplementary Information statement, the data licences, has no support in any artifact.

## Findings
### 1. si-licence-unsupported-1 — Supplementary Information (Reproducibility, data and licences)
- claim: Data sources are public: MTEB results (CC0-1.0), Open LLM Leaderboard contents (no dataset licence declared on its card), and HELM Lite release v1.13.0 (scenario data under per-scenario licences, not individually verified).
- issue: The paper states specific licence facts for three datasets, but no artifact records any licence information. The SI sentence has no @evidence anchor and no claims_grounding.json entry, so the licence statements are unsupported.
- evidence: paper.tex SI Reproducibility paragraph, which has no @evidence tag on this sentence; claims_grounding.json has no licence claim; source_evidence/manifests/*_final_manifest.json hold only upstream, revision, score_definition, normalization, columns and models, with no licence field; analysis/protocol_facts.json has no licence field; paper_data.json has no licence entry.
- requested_fix: Delete the specific licence assertions (CC0-1.0, no licence declared on the card, per-scenario licences) and say only that the data come from the public upstream sources and pinned revisions listed in Table tab:data. Add that licence terms were not verified in this study.
