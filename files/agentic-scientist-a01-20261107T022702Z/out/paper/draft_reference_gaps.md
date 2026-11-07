# Post-draft citation-gap analysis

**Status:** `no_gaps`

The draft directly cites its relevant comparator literatures and benchmark background, while its allocation claims are grounded in recorded evidence or explicit derivations, so no targeted post-draft retrieval is justified.

## Coverage supporting this decision

- **Introduction** (`paper.tex:20`): MMLU, BIG-Bench Hard, and HELM have direct citations. The median-resistance intuition at `paper.tex:24` is explicitly qualified, not asserted as an established leaderboard guarantee; robust-estimation background is cited in Related Work.
- **Related Work — Evaluation design and incentives** (`paper.tex:39`): benchmark selection, evaluation infrastructure, leaderboard incentives, and strategic post-training each have direct citations. The paragraph distinguishes the present fixed-rival allocation model from strategic equilibrium analysis.
- **Related Work — Social choice and targeted changes** (`paper.tex:42`): social-choice evaluation, rank aggregation, strategic reporting, and election bribery are directly cited. The target-only, capped intervention is distinguished from those models rather than presented as an uncited external comparator family.
- **Related Work — Robustness and contamination** (`paper.tex:45`): robust estimation, influence, and contamination have direct citations. The paragraph disclaims any empirical calibration of the hypothetical headroom response from those studies.
- **Method** (`paper.tex:73`): aggregation rules and comparator policies are explicitly defined; allocation certificates are derived and linked to implementation evidence. These are not unsupported claims of a generic greedy guarantee or optimizer superiority. The supplementary discussion at `paper.tex:260` already cites submodular optimization and robust optimization when explaining their different assumptions.
- **Public Score Tables and Comparison Protocol** (`paper.tex:131`): snapshot dimensions, normalization, target selection, and allocation checks are grounded in frozen resources and evaluation records. The existing **Public snapshots, normalization, and reproduction map** subsection (`paper.tex:388`) supplies acquisition and version context; the draft does not equate these recomputed comparisons with live leaderboard rankings.

## Grounding and exclusions

Reviewed `paper.tex`, `references.bib`, `references_provenance.json`, `claims_grounding.json`, `paper_data.json`, `paper_strategy.json`, and `global_memory_summary.md`. All 25 distinct citation keys used in the manuscript resolve in the bibliography and have provenance entries with existing local consulted-content artifacts. This establishes current coverage, not an exhaustive literature review or a new full-text verification of every reference.

The strategy's earlier warnings about incomplete reference verification describe a pre-draft state; current bibliography, provenance, and claim mappings document subsequent consultation. The global memory summary is qualitative context only. Recorded quantitative findings, original mathematical arguments, and explicitly acknowledged training-response limitations are not retrieval gaps. Seeking additional manipulation variants or training-cost studies would expand positioning rather than repair a visibly unsupported paragraph.

**Missing literatures:** none. **Rewrite targets:** none. **Failure reason:** none.

No references were retrieved. The manuscript, bibliography, and reference-provenance file were not modified.
