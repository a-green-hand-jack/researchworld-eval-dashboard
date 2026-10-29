# Agentic evidence audit

- verdict: `fail`
- finding_count: `2`

## Summary
The numbers, controls, comparators, qualified final outcome and unscored-attempt handling all match the evidence, but two visible claims go beyond it: the SI says the agent wrote the evaluated finder, and the paper states as fact what the episode timings include.

## Findings
### 1. finder-provenance-1 — Supplementary Information, LLM usage (paper.tex line 379); also Contributions (i) and Reproducibility record, Artifacts paragraph (line 374)
- claim: An autonomous LLM-based research agent ... implemented the perturbation finder and the refined configurations
- issue: The evidence shows the evaluated finder is the seeded starter baseline, not code the agent wrote. The text also says the three refined configurations were implemented, but they have no inspectable source and were never scored, so this cannot be checked.
- evidence: paper_data.json downstream_study.selection_kind=baseline, source_attempt_id=bootstrap, source_program_dir=.baseline-seed-dewjjlsp/program_0, program_tree_sha256 equal to baseline_tree_sha256 (1a860d79...); source_evidence/downstream/program/src/program.py line 1 reads Starter perturbation finder and line 44 reads This starter: one-step influence (AMIP-style) ranking; program.py is byte-identical to source_evidence/downstream/baseline/src/program.py; claims_grounding.json study.attempts.scored=0 of total=3; paper.tex line 360 itself says no source for the refined configurations is among the artifacts
- requested_fix: In LLM usage, state that the evaluated finder is the provided starter/baseline configuration seeded before the search, and drop the claim that the agent implemented it. Say the three refined configurations were designed but have no inspectable source and were not scored. In the Artifacts paragraph, add that the finder is the baseline starter configuration.

### 2. episode-duration-scope-1 — Discussion and Limitations, What the evidence supports (paper.tex line 253); SI Per-case verified sizes (line 290); SI Software and compute (line 371)
- claim: This covers data transfer, the search, and the evaluator's verification refit, and it is possible because each refit acts on p x p sufficient statistics / the evaluator's comparator runs add to this
- issue: The evaluation record gives only one duration_seconds value per seed and does not say what that time includes or excludes. The breakdown comes from the harness, which cannot be inspected, yet the paper states it as fact without the stated-protocol label it uses for other harness details. It then credits the speed to the p x p refit, which was not measured.
- evidence: paper_data.json final_evaluation.evaluation_evidence.episodes[*].duration_seconds holds only scalar values (15.99, 15.55, 16.33); claims_grounding.json supports only the claim Recorded episode time per seed over all 17 cases was 15.99 s, 15.55 s and 16.33 s; paper.tex line 102 says harness internals are not among the artifacts; no grounding source or source_evidence file defines the timing scope
- requested_fix: Report only the recorded per-seed episode times. Either remove the statements about what the time covers (data transfer, search, verification refit, comparator runs excluded) or label them as the harness's stated protocol, which could not be inspected. Rephrase the p x p sufficient-statistics explanation as a plausible reason, not a measured one.
