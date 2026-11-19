# Draft Reference Gaps

**Status:** ready

Two paragraph-specific gaps justify a small retrieval pass for Open LLM Leaderboard benchmark context and direct Rasch/IRT foundations. Existing related-work coverage needs no expansion. Both targets are medium priority; neither requires changing the paper's evidence-bounded thesis.

## Grounded Review

Reviewed `paper.tex`, all 25 entries in `references.bib` and their existing provenance, the 30 claims in `claims_grounding.json`, the structure and final-evaluation evidence in `paper_data.json`, `paper_strategy.json`, and `global_memory_summary.md`. All manuscript citation keys resolve, and every existing bibliography entry is cited. Global memory was used only as qualitative context, not numerical evidence. No references were retrieved.

## 1. Benchmark Collection Context

- **Target ID:** `evaluation-leaderboard-context`
- **Section:** Evaluation Protocol and Evidence Availability
- **Paragraph:** Fixed Benchmarks and Grouped Model Holdouts, opening paragraph.
- **Priority / intent:** medium / benchmark_context
- **Anchor:** “four Open LLM Leaderboard-derived cases (BBH, GPQA, MuSR, and OpenLLM Math)”
- **Gap:** The paragraph identifies a named upstream collection without a direct collection reference; no dedicated Leaderboard source appears in the bibliography. HELM is already represented by `Liang2023`, which can be reused here without new retrieval. `Wang2024` concerns MMLU-Pro and must not be repurposed as provenance for the staged MMLU case.
- **Focused search topic:** Open LLM Leaderboard benchmark collection documentation covering BBH, GPQA, MuSR, and OpenLLM Math.
- **Bounded intervention:** Add one authoritative collection citation. Retain the staged names and the explicit warning against assuming public-benchmark identity. Case counts, fixed item universes, snapshot identity, and filtering remain supported by the supplied artifacts, not by this citation. Do not commission separate searches for all ten benchmarks.

## 2. Named Item-Response Model Foundations

- **Target ID:** `method-rasch-irt-foundations`
- **Section:** Method
- **Paragraph:** Linear and Residual-Profile Reconstruction, introduction of Rasch smoothing.
- **Priority / intent:** medium / background
- **Anchor:** “The nonlinear branch retains source response profiles while smoothing them with a Rasch model.”
- **Gap:** The named response family lacks a direct foundational citation. `Andersen1970` is cited in Related Work for an estimation procedure explicitly not used here, and its stored abstract addresses conditional estimation. Broad statistical texts and the already cited LLM compression methods do not directly anchor the Rasch/2PL distinction in these paragraphs. The local IRT comparator in Evaluation Protocol and Evidence Availability also introduces two-parameter logistic responses and fitted item information without a direct foundation citation.
- **Focused search topics:** Rasch logistic ability–difficulty model foundations; two-parameter logistic discrimination and Fisher item information.
- **Bounded intervention:** Retrieve one authoritative source covering both families, or at most two complementary sources. Cite the Rasch introduction and reuse the relevant source at the local IRT comparator if supported. Preserve the fixed-ability, penalized custom-fit description and the disclaimer that local references are not official reproductions. No claim of profile-component benefit or target-calibrated uncertainty should be added.

## Coverage That Does Not Justify Retrieval

- Related Work directly cites Anchor Points, tinyBenchmarks, metabench, reference-instance prediction, and active evaluation acquisition. There is no missing comparator-family paragraph to expand.
- Scalar-target design, ridge regression, validation dependence, domain shift, missingness, ranking statistics, and bootstrap background already have relevant citations. The selector is explicitly a heuristic, not an unsupported optimality theorem.
- Numerical accuracy, availability masks, failed qualification, structural diagnostics, and local implementation details are grounded in the supplied evidence. More citations cannot repair missing predictions, isolate a profile contribution, or establish overall superiority.
- Do not add literature on deployment speedups, new benchmark populations, target-adaptive policies, or calibrated stopping rules: those would expand rather than support the existing story.

## Handoff

Retrieve approximately two to three sources total across these two targets, preferring reuse when one IRT source covers both model families. This memo does not prescribe new paper sections or a broad rewrite. The manuscript, bibliography, and reference provenance remain unchanged.
