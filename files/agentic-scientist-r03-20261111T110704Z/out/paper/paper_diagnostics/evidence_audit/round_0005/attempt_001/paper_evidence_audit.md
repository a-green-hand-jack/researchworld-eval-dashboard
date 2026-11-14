# Agentic evidence audit

- verdict: `fail`
- finding_count: `4`

## Summary
Every number, count, and the qualified final outcome match claims_grounding.json, paper_data.json, and the evaluator source. Four wording overclaims remain: two in Discussion, one in Results and Conclusion, and one in Related Work.

## Findings
### 1. perm-control-erases-overclaim — Discussion and Limitations (What is and is not shown)
- claim: the improvement is not an artefact of the imputer's marginals since permuting the observations erases it
- issue: The retained evidence supports only an average nRMSE gap of 0.678 between permuted-control and matched real episodes, which cover three of the 14 episodes per seed. No control nRMSE, control skill against column mean, or comparison of controls with the column-mean baseline was retained, so the evidence does not show that the control removes the whole improvement.
- evidence: paper_data.json final_evaluation.metrics.final_permuted_control_gap=0.6775 (the only control metric); claims_grounding.json claim[5] states only "Permuted-control gap is 0.678 nRMSE"; paper.tex Results paragraph "Control" already says the gap is an absolute difference to be read against 0.562
- requested_fix: Replace "erases it" with "raises nRMSE by 0.678 on average over the three matched real episodes, so the predictions use the new model's own scores". Do not say the control removes the gain over column means.

### 2. unavoidable-residual-overclaim — Discussion and Limitations (Practical reading)
- claim: an unavoidable residual of about 0.64 history standard deviations remains on MTEB at k=20
- issue: 0.638 is the measured nRMSE of one selector-imputer pair at k=20 on 37 held-out MTEB models. Nothing in the evidence shows it is an irreducible floor, and the paper itself says no ablation, resampling interval, or alternative imputer comparison was run.
- evidence: claims_grounding.json claim[3] supports only the nRMSE values at k=2, 5, 10, 20; paper_data.json final.metric.final_nrmse_mteb_k20=0.6377; paper.tex Limitations "Unperformed analyses" and "Uncertainty" paragraphs
- requested_fix: Change "unavoidable residual" to "a residual error of about 0.64 history standard deviations for the evaluated pair on MTEB at k=20, with no claim about a lower bound".

### 3. greedy-vs-random-inference-too-strong — Results (Selection versus imputation) and Conclusion
- claim: the greedy-forward baseline had larger error on average than the random-k baseline ... under a fixed ridge imputer, a leave-one-out greedy selector did not beat random subsets; Conclusion: a leave-one-out greedy selector can fail to beat random subsets
- issue: The paper derives this only from the difference between two clipped, hierarchically averaged skills (0.099 vs 0.016). Skill is a mean of per-episode ratios, and the paper says it does not equal one minus a ratio of pooled errors. The per-baseline nRMSE values were not retained. claims_grounding.json grounds only an "indicative only" error ratio of about 1.09. The flat statements are firmer than that grounding.
- evidence: claims_grounding.json claim[4] ("implied error ratio about 1.09 is indicative only"); paper.tex Results "Selection versus imputation" ("per-baseline errors were not retained") and "Skill is a mean of ratios" paragraph; evaluate_final.py computes skill as clip(1-cand/b) per episode, then averages
- requested_fix: Reword each statement as indicative only. For example, say "the averaged skills suggest, but per-baseline errors were not retained to confirm, that the greedy-forward ridge baseline was no better than random-k ridge". Remove the unqualified "did not beat random subsets".

### 4. related-work-unsupported-details — Related Work (Cheaper evaluation within or across benchmarks) and Introduction
- claim: metabench distills six benchmarks into a sparse one using the responses of thousands of models and checks recovery of the original scores; Introduction: agreement analyses across dozens of benchmarks
- issue: references_provenance.json retains only the titles and metadata of these references, and claims_grounding.json grounds them at the level of "sparse benchmark distillation" and "agreement depends on methodological choices". The specifics (six benchmarks, thousands of models, recovery check, dozens of benchmarks) have no retained source text, so they are unsupported by the evidence trail.
- evidence: references_provenance.json entries for Kipnis2024Metabench (title "metabench - A Sparse Benchmark of Reasoning and Knowledge in Large Language Models") and Perlitz2024BenchBench contain no abstract or snippet; claims_grounding.json claims for the item-level and agreement citations
- requested_fix: Cut the quantitative and procedural details to what the titles and grounded claims support. For example, say "metabench distills a sparse benchmark from several benchmarks" and "agreement analyses across benchmarks".
