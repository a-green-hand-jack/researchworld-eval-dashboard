# Draft Reference Gap Analysis

**Status:** ready

One medium-priority benchmark-source citation gap remains for the primary Open LLM six-task panel; the existing related-work and results coverage does not justify broader retrieval.

## Review Basis

Reviewed `paper.tex`, the 25 entries in `references.bib` and `references_provenance.json`, the 57 claim mappings in `claims_grounding.json`, the grounding-source and final-evaluation records in `paper_data.json`, `paper_strategy.json`, and `global_memory_summary.md`. The memory summary supplies qualitative context only. Existing reference provenance limits substantive reading to canonical metadata and abstracts; this memo does not infer stronger support from those records.

## Target: method-open-llm-panel-source

- **Section:** Method, opening paragraph of “Public score panels and experimental protocol” (`paper.tex:97`).
- **Priority:** medium.
- **Citation intent:** benchmark_context.
- **Anchor:** “the pinned Open LLM contents snapshot with six raw-score coordinates”.
- **Missing literature:** Official Open LLM leaderboard six-task suite and raw-score documentation.
- **Reason:** The paragraph names a primary score-panel source without directly citing its official leaderboard or suite documentation. Related Work cites IFEval, BBH, MATH, GPQA, MuSR, and MMLU-Pro individually, but those sources do not attribute their assembly into this leaderboard panel. No corresponding suite-level source appears among the existing bibliography or provenance entries. The supplementary revision hashes and local acquisition manifest already ground the actual inputs; this is a reader-facing source-attribution gap, not a missing-data or unsupported-results problem.
- **Focused search topic:** Official Open LLM leaderboard documentation for the six-task suite IFEval, BBH, MATH level 5, GPQA, MuSR, and MMLU-Pro, including raw-score fields.
- **Minimal later change:** Add one verified canonical official source at this paragraph. If available documentation describes a different leaderboard generation or standardized rather than raw scores, do not treat it as support for the pinned panel. Retain the recorded revisions and normalization details as the authority for the actual analyzed inputs. No method or results rewrite is needed.

## Areas Not Flagged

- Related Work directly cites the benchmark families, social-choice aggregation, robust estimation, leakage and contamination, validity, and uncertainty literature it discusses. No uncited named comparator family there warrants an additional retrieval target.
- Introduction motivation can use the existing benchmark-composition, social-choice, and contamination references if local citation placement is desired; this does not require new references. The discussion of median and mean behavior is explained by the paper's own definitions rather than asserted as an external finding.
- Exact enumeration, sorted-headroom optimality, monotonicity, and feasible-support bounds are explained and tied to implementation evidence. The paper disclaims optimizer novelty; adding generic optimization citations would not close a demonstrated gap.
- Quantitative results, cohort definitions, and certificate scope are grounded in the recorded evaluation and claim mappings, not candidates for bibliographic repair. Real training costs and response calibration remain explicit limitations, not invitations to expand the story.

## Retrieval Boundary

This memo requests only the single source-attribution lookup above, not a citation-count increase or a broader literature pass. Any later lookup must respect the recorded strategy's prohibited-study and no-citation-graph-expansion restrictions. No reference retrieval was performed, and `paper.tex`, `references.bib`, and `references_provenance.json` were not modified.
