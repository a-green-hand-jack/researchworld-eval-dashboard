# Post-draft Reference Query Plan

**Status:** ready  
**Scope:** one medium-priority benchmark-source attribution query; no retrieval performed.

## Central Topic and Grounding

The manuscript studies conditional minimum task-support investment for a fixed target model to become strictly first under mean, median, and trimmed-mean aggregation with bounded score uplifts. This incremental plan concerns only attribution of its primary Open LLM six-task raw-score panel.

Read `draft_reference_gaps.md` and `draft_reference_gaps.json` first, then checked the draft, existing bibliography and provenance, global memory summary, and original query-plan structure. Both gap artifacts identify only `method-open-llm-panel-source`. One query, rather than the default three to six, respects their explicit single-lookup boundary. No full literature refresh or bibliography rebalancing is justified.

Existing component citations are `IFEval`, `BBH`, `MATH`, `GPQA`, `MuSR`, and `MMLUPro`. The 25 bibliography/provenance entries contain no suite-level official Open LLM source. Provenance records report canonical metadata and abstract reading only; this plan does not infer deeper source support. Existing related-work citations cover social choice, robust estimation, benchmark composition, contamination, validity, and uncertainty. No new comparator or method-family search is requested. There are no architectural-shift or result-driven retrieval targets.

## Query 1: Primary Panel Attribution

- **Category:** `benchmark_context`.
- **Priority and target:** medium; `method-open-llm-panel-source`.
- **Location:** `paper.tex:97`, Method, opening paragraph of “Public score panels and experimental protocol”.
- **Anchor:** “the pinned Open LLM contents snapshot with six raw-score coordinates”.
- **Query:** `"Open LLM Leaderboard" IFEval BBH "MATH" "GPQA" "MuSR" "MMLU-Pro" raw scores official documentation`

**Rationale:** Constituent benchmark papers explain individual tasks but do not attribute their assembly into the leaderboard panel. A single canonical official suite or primary dataset documentation source should establish the six-task composition and raw-score field semantics compatible with contents snapshot `9c09a7cae43334062a82cb164f2ef255013dafa2`, acquired on 2026-11-17. This is a reader-facing source-attribution gap, not missing empirical evidence.

**Acceptance and stopping rule:** Later verification must distinguish leaderboard generations and raw versus standardized scores. A source describing a different generation or only standardized scores is not support for the pinned raw panel. Recorded revisions, acquisition records, and supplementary normalization details remain authoritative for the actual analyzed inputs. Add at most one verified compatible source at this paragraph; no method or results rewrite is needed. If no compatible official source is verified, leave the gap explicitly unresolved rather than substitute a near-match or broaden retrieval.

## Boundaries and Deferred Work

- This stage plans only: it retrieves no references and changes neither `paper.tex`, `references.bib`, nor `references_provenance.json`.
- Preserve prohibited-study restrictions: no discovery by title, authors, results, paraphrased question, or broad strategic-leaderboard/benchmark-cheating searches. Do not search run-local proposal names as established methods.
- No citation-graph expansion, cited-by searches, recommendations, reference-list mining, surveys, discussions, mirrors, code repositories, or social posts that could expose the prohibited study. Limit later lookup to canonical official suite or primary dataset documentation.
- Do not repeat component-benchmark searches, substitute an unpinned latest leaderboard, use standardized-only descriptions, detour into Arena, or conflate the six-task contents panel with the separate 24-subtask BBH sensitivity panel. HELM MMLU v1.13.0 and BBH results snapshot `aa81ecc38fdc5708254b833923368970efdf5ef5` are context, not new targets.
- No generic optimization, robustness, social-choice, contamination, validity, uncertainty, architecture, prompting, or training-cost literature refresh. Do not introduce claims of universal robustness, transfer, or candidate superiority.
- Stop after the single attribution target is resolved or found unsupported; do not expand for citation count, bibliography balance, or methods/results rewriting.

The companion JSON retains the field structure of `reference_query_plan.json`; its sole prospective query mirrors this memo.
