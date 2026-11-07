# Reference Query Plan

**Status: ready.** Nine queries; planning only. No references have been retrieved or verified in this stage.

## Central topic

Reliability of accuracy reports after selecting from a frozen LLM prompt bank: selection-data reuse versus independent split reporting, with synthetic population truth kept distinct from finite real-data audit comparisons.

## Grounding and scope

- `paper_data.json` reports no scored search candidates and no winning search variant. Its separate `final_evaluation` is completed and contains five seeded episodes, each with cases S64K1, S64K16, S256K1, S256K16, R64K1, R64K16, R256K1, and R256K16. These final records, not older memory or proposal titles, establish the measured neighborhood.
- `source_evidence/downstream/program/src/program.py` preserves a frozen bank of 16 instruction/format variants, seeded random half-selection/half-report allocation, uniform reporting weights, and deterministic tie order. Its interface describes maximum-accuracy selection, 95% Wilson reporting intervals, synthetic known truth, and fresh real-data audit comparisons. The preserved policy is not the proposed quarter-split or stratum-balanced policy.
- The recorded pooled report MSE is 0.0033498776393466522, versus 0.005354862639043066 for same-winner reuse, 0.003172102647821109 for honest half-split, and 0.002705803510381116 for full-budget naive reporting. These descriptive aggregates motivate a bias–variance discussion, not uniform dominance or significance claims. Full-budget selection can choose a different winner; the comparators are not interchangeable estimands.
- The final record also reports signed optimism, report bias, decision reversals, interval width, and coverage. The pooled coverage value, 0.95166015625, mixes evaluation contexts and does not establish population coverage for the real benchmark. Real-case details contain `audit_size=512` and `paired_subject_bootstrap_interval`; the resampling implementation and interval contrast require verification before interpretation.
- Final evidence labels candidate diagnostics `unverified`. Treat these as evaluator-recorded observations, not independently reproduced inference or audited raw model outputs. Search-stage timeouts are missing observations, not measured scientific losses. Keep search and final evaluation scopes separate.
- MMLU-Pro is the task-specified dataset context. The provided final real-case records do not independently identify the dataset revision, model, or complete inference provenance. Do not infer a model family, architecture comparison, or full-benchmark evaluation from the task specification alone.
- `figures/` contains no figures; no existing `references.bib` or `references_provenance.json` is present. There are no prior retrieval queries to recycle or correct.

## Method and comparator families

Core methods are fixed-bank prompt selection, randomized protected reporting, Wilson intervals, known-truth synthetic evaluation, finite real-data audits, and recorded paired subject-bootstrap diagnostics. Measured comparators are fixed/random prompts, full-sample winner reporting, same-winner reuse, and honest half-split reporting. Best-arm identification, post-selection inference, adaptive data analysis, and reliable leaderboards are conceptual related-work comparators only; none should be described as an implemented algorithm or measured baseline unless the artifacts actually show it.

**Architectural shifts: none supported.** Instruction/format variation is not an architecture or representation transition. No architectural-shift query is warranted.

## Queries

1. **Core method:** `sample splitting model selection independent test error bias variance`
   - Grounds the actual half-split policy and its reporting-bias/variance tradeoff. Restrict later retrieval to foundational original statistical methodology rather than broad recent LLM discovery.
2. **Baseline comparator:** `"Valid post-selection inference" Berk Brown Buja Zhang Zhao`
   - Permitted starter work for inference after choosing a winner; regression-specific guarantees are context, not implemented prompt-selection certificates.
3. **Baseline comparator:** `"Preserving Statistical Validity in Adaptive Data Analysis" Dwork`
   - Permitted starter work contrasting adaptive reuse protection with a frozen bank and a single protected report. No differential-privacy implementation is implied.
4. **Baseline comparator:** `"The Ladder: A Reliable Leaderboard for Machine Learning Competitions" Blum Hardt`
   - Permitted starter work on reliable reporting under repeated reuse; contrast its setting with one-shot splitting, without claiming a Ladder experiment.
5. **Baseline comparator:** `"Efficient Prompt Optimization Through the Lens of Best Arm Identification" Shi`
   - Permitted starter work distinguishing prompt-selection quality from estimation quality, matching finite-arm selection and fixed/random controls. Its adaptive allocation algorithm was not run.
6. **Core method:** `"Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design" Sclar`
   - Permitted starter work for the instruction/format bank and K=1/16 comparisons, without asserting an architecture change or measured sensitivity beyond the available records.
7. **Benchmark context:** `"MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark" Wang`
   - Permitted original benchmark paper for the task-specified multiple-choice setting; dataset revision and actual model provenance remain separate verification requirements.
8. **Result-driven theme:** `Wilson score interval binomial proportion coverage`
   - Foundational interval methodology for recorded coverage/width; distinguish synthetic population targets from noisy real audit estimates.
9. **Result-driven theme:** `paired bootstrap accuracy difference dependent observations`
   - Foundational paired/dependence-aware inference relevant to the recorded subject-bootstrap intervals. Verify pairing, resampling unit, and contrast; do not relabel this as a bias-correction method or selection certificate.

## Retrieval boundaries and rejected alternatives

Later retrieval must resolve the six named queries to the explicitly permitted starter originals, not substitute loosely related discoveries. The other three queries are limited to foundational original statistical methodology. All reference targets must be public by 2025. Prefer original fixed-version documents and minimal identity metadata; do not browse citation graphs, cited-by lists, related-paper recommendations, review/aggregation pages, or social discussions. Title matches are retrieval targets, not claims that those papers have already been read.

Do not try to identify the prohibited paper. Do not access it or any mirror, preprint, abstract, venue/review page, supplementary media, blog, repository, or page citing, discussing, or reproducing it. No search blacklist of guessed titles/authors is appropriate. If prohibited material is accidentally encountered, stop reading immediately and record the location, what was encountered, and how much was read in the reproduction record. These query restrictions reduce exposure risk; they do not guarantee every search result is permissible.

Avoid broad discovery queries restating the central LLM tuning/benchmark-bias question. Also reject generic optimization, benchmarking, scientific-method, and paper-writing searches: they add little grounding and increase irrelevant or prohibited exposure. Exclude chronology-shaped queries entirely.

Do not prioritize DSPy/MIPRO, economics-specific winner inference, high-dimensional multiplier-bootstrap certificates, adaptive prompt-generation pipelines, quarter-split superiority, or stratified-reporting gains. The actual retained source and final results do not establish those implementations or improvements. Likewise, do not invent neural-model comparisons or transfer stories. Fixed-bank reporting and its explicit measured comparators are more relevant than literature attached only to untested idea titles.

## Handoff

This is a coherent literature neighborhood despite unsuccessful search attempts because independent final records and preserved source identify a concrete reporting study. The plan is ready for constrained retrieval, not a declaration that a complete paper, novel method, population-valid real-data coverage claim, or reproducible real-LLM provenance has been established. No reference, paper, or claims-grounding artifacts are written in this stage.
