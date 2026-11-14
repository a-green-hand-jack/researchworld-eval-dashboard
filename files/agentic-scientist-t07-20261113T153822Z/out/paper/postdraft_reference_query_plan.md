# Post-Draft Reference Query Plan

**Status:** ready  
**Scope:** Three focused query specifications for the two medium-priority gaps in `draft_reference_gaps.md` and `draft_reference_gaps.json`. Query 3 is conditional. A later retrieval pass should add approximately two to three unique sources, not refresh the bibliography. No references were retrieved in this stage.

## Central Topic

Evidence-bounded prediction of LLM full binary benchmark scores and rankings from fixed 8-, 16-, or 32-item prefixes using source-only score-covariance selection and ridge/Rasch-residual reconstruction. Only upstream Open LLM Leaderboard collection context and direct Rasch/2PL foundations need incremental citation support.

## Grounding and Existing Coverage

The gap memo and JSON were read first and drive every query below. The manuscript, all 25 existing bibliography entries and their stored provenance, the original query-plan schema, and the global memory summary were checked locally. Global memory supplies qualitative context only, not numerical evidence.

- **Core methods:** Fixed source-only prefixes, grouped tuning, and ridge prediction already have adequate methodological context. The Rasch introduction at `paper.tex:86` needs direct model-family support; its fixed-ability, group-weighted penalized fit and optional profile blend remain custom, artifact-grounded details.
- **Comparators:** The local 2PL comparator at `paper.tex:130` and its information formula at `paper.tex:293` need foundational support. Anchor Points, tinyBenchmarks, metabench, reference-instance prediction, and active evaluation acquisition already have direct citations; do not expand their coverage.
- **Benchmarks:** One collection reference is missing for the four Open LLM Leaderboard-derived cases named at `paper.tex:115`. For the six HELM-derived cases in that paragraph, reuse `Liang2023` without retrieval. `Wang2024` addresses MMLU-Pro and is not provenance for staged MMLU.
- **Architectural shifts:** None are requested or justified.
- **Result-driven boundaries:** Missing predictions, failed qualification, structural diagnostics, and retained-support results remain artifact-grounded. Citations cannot repair those outcomes, isolate a profile contribution, establish selector superiority, or calibrate target uncertainty.

The original plan already included a Leaderboard collection query, but no dedicated collection source is present in the resulting bibliography or provenance. Reopening that specific unresolved gap is warranted; rerunning successful comparator searches is not. The stored abstract for `Andersen1970` concerns conditional maximum-likelihood estimation, explicitly distinguished from this implementation, rather than directly supporting both response-model families.

## Queries

### 1. Upstream Leaderboard Collection Context

- **Query:** `Open LLM Leaderboard benchmark collection documentation BBH GPQA MuSR OpenLLM Math`
- **Category:** `benchmark_context`
- **Gap / location:** `evaluation-leaderboard-context`; Evaluation Protocol and Evidence Availability / Fixed Benchmarks and Grouped Model Holdouts, opening paragraph, `paper.tex:115`.
- **Anchor:** “four Open LLM Leaderboard-derived cases (BBH, GPQA, MuSR, and OpenLLM Math)”
- **Rationale:** Seek one authoritative collection source documenting the upstream benchmark composition, closing the unresolved collection citation gap. Do not use it to substantiate staged counts, filtering, exact snapshot identity, or equivalence with public benchmark versions. Reuse existing HELM support instead of searching again; do not substitute MMLU-Pro provenance for staged MMLU.
- **Completion condition:** One verified collection source supports the named upstream context. Preserve staged case names and the manuscript's explicit non-equivalence warning; do not commission separate searches for every benchmark.

### 2. Rasch Response-Model Foundations

- **Query:** `Rasch logistic item-response model ability item difficulty foundational reference`
- **Category:** `core_method`
- **Gap / location:** `method-rasch-irt-foundations`; Method / Linear and Residual-Profile Reconstruction, `paper.tex:86`.
- **Anchor:** “The nonlinear branch retains source response profiles while smoothing them with a Rasch model.”
- **Rationale:** Seek an authoritative foundation for logistic ability-minus-difficulty responses. Prefer a source also covering 2PL discrimination and item information so it can support the later comparator paragraph. Existing `Andersen1970` supports a distinction about conditional estimation, not this full response-family framing. Broad statistical texts and already-cited LLM compression methods do not directly close the identified gap.
- **Completion condition:** One verified source supports the Rasch model family. Keep the fixed-ability penalized fitting description explicit; do not portray it as standard joint estimation or cite foundations as evidence of a measured profile benefit.

### 3. Conditional 2PL and Item-Information Complement

- **Query:** `two-parameter logistic item-response model discrimination Fisher item information authoritative reference`
- **Category:** `baseline_comparator`
- **Gap / location:** Same `method-rasch-irt-foundations` target; Evaluation Protocol and Evidence Availability / Comparators and Control Semantics, `paper.tex:130`, and Supplementary Information / Local Reference Implementations, `paper.tex:293`.
- **Anchor:** “The IRT reference fits a penalized two-parameter logistic response model, chooses items by fitted information near zero ability, and infers target ability from queried responses.”
- **Rationale:** Seek at most one complementary authoritative source for variable discrimination and Fisher item information `a^2 p(1-p)`, verifying consistency with the draft's `theta*a-d` parameterization. This is foundational support for the already-written local comparator, not a new comparator-family search or certification of an official reproduction.
- **Execution / completion condition:** Run only if the source from Query 2 does not cover the required 2PL distinction and information expression. Otherwise reuse that source and skip this query. Retain all local-fit, optimizer, and non-reproduction disclaimers.

## Exclusions and Stop Rule

- Do not broaden into a bibliography rebalance, generic benchmark-compression search, citation-graph traversal, related-paper recommendations, or searches for all ten benchmarks. Do not repeat HELM or successful comparator retrieval directions.
- Retain the original plan's prohibition on identifying or accessing the task-prohibited unnamed paper or its authors, title, findings, mirrors, summaries, reviews, presentations, repositories, or discussions. No such identification is needed for these gaps.
- Do not equate an upstream collection with staged item universes, filtering, counts, snapshot identity, or public benchmark versions; do not conflate staged MMLU with MMLU-Pro.
- Do not add latent-class/residual-mixture literatures, new acquisition methods, deployment speedups, new benchmark populations, target-adaptive policies, calibrated stopping rules, or architecture-transfer claims.
- Do not use foundations to certify optimizer correctness, comparator reproduction, target-calibrated uncertainty, profile-component benefit, selector superiority, or the cause of failed qualification.
- Stop later retrieval after one suitable collection source and one suitable IRT source, adding a second IRT source only if necessary: approximately two to three unique sources total. An unresolved source should remain an explicit gap rather than trigger a broader search.

This stage writes a plan only. The manuscript, bibliography, reference provenance, original plan, and draft-gap artifacts remain unchanged.
