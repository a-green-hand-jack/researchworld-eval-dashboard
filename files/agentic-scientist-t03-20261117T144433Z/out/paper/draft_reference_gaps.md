# Draft Reference Gap Analysis

**Status:** `no_gaps`

The draft directly supports its relevant literature comparisons and scoped methodological positioning with existing references, so no targeted post-draft retrieval is justified.

## Grounded review

Reviewed `paper.tex`, `references.bib`, `references_provenance.json`, `claims_grounding.json`, relevant scope and metrics in `paper_data.json`, `paper_strategy.json`, and the qualitative context in `global_memory_summary.md`. All 25 distinct manuscript citation keys resolve to existing bibliography and provenance entries. The decision rests on paragraph-level coverage, not bibliography size.

- **Related Work — “Attribution targets and disagreement.”** The paragraph directly cites the conditional/interventional distinction (`Chen2020`), background sensitivity (`Yuan2022`), between-method disagreement (`Krishna2022`), and predictive multiplicity (`Marx2020`). It explicitly distinguishes these settings from fixed-game repetition.
- **Related Work — “Sampling and uncertainty.”** Sampling approximation (`Castro2009`, `Maleki2013`, `Mitchell2022`), regression-estimator bias/variance and uncertainty (`Covert2021`), and leverage-score sampling (`Musco2024`) receive direct citations. The paragraph does not claim a new estimator or transfer those methods' guarantees to the studied dependent designs.
- **Related Work — “What stability measures capture.”** Chance-corrected feature-selection stability (`Nogueira2018`), ranking displacement (`Diaconis1977`), and top-weighted ranking comparison (`Webber2010`) are already cited where introduced.
- **Introduction and Method.** Foundational attribution positioning cites `Shapley1953` and `Lundberg2017`; datasets and model families have direct references. The sampling configuration and package-comparator settings are source-grounded implementation descriptions, not unsupported superiority or benchmark-standard claims. Bootstrap methodology is cited, with explicit limits on inference.

## Exclusions and decision

The retained quantitative findings are grounded in the supplied data and claims ledger; their uncertainty and provenance limitations are not missing-literature problems. The distinction between agreement, efficiency, and vector fidelity is also justified directly from the metric definitions. More local reuse of existing citations, if desired, would not require retrieval.

Broader estimator tournaments, neural-model comparisons, causal attribution, and deployment certification would expand the paper's stated scope rather than repair a paragraph-specific citation gap. No missing literature areas or rewrite targets are recommended, and there is no analysis failure. No references were retrieved; the manuscript, bibliography, and reference provenance were left unchanged.
