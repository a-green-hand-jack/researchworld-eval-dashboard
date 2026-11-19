# Grounded Reference Query Plan

**Status: ready.** Eight targeted queries; planning only. No external source was retrieved or read, and the listed papers remain candidates for later verification rather than already consulted references.

## Central topic

Finite-budget memorization without observed delayed generalization in width-scaled one-hot ReLU MLPs on modular addition and subtraction, comparing AdamW decay arms and shared constant versus exponential learning-rate schedules.

## Grounding and scope

- Primary evidence: `paper_data.json`, especially `final_evaluation.metrics`, `final_evaluation.evaluation_evidence.episodes`, and the evaluated configurations in `all_programs`. Local implementation context: `task/evaluate.py`, `task/resources/search/benchmark.json`, `task/resources/final/benchmark.json`, and the configuration files under `results/ideas/`. `task/task.md` supplies the allowed starter titles and identifiers. Memory summaries are qualitative context only and do not override these artifacts.
- Actual data: modular addition and subtraction modulo 97, with 9409 possible ordered pairs per operation. Hash partitioning separates search and final subsets. Each final operation contains 1411 training and 3294 heldout pairs. This is a task-local synthetic split, not a named public benchmark.
- Actual model: concatenated one-hot pairs (194 features), one ReLU hidden layer with width 16, 64 or 256, and 97 output logits; 4769, 18785 or 74849 parameters. Full-batch AdamW uses decay 0 or 1. Candidate recipes share initial learning rate 0.01 and constant or exponential scheduling, with schedule factors 1, 0.5 and 0.1 respectively. These schedule factors are not the AdamW weight-decay coefficients.
- Final recorded observations: three seeds (1009, 2027, 3037), two operations, two decay arms and three widths give 36 cases. Thirty have sustained training-accuracy crossings; none has a sustained heldout-accuracy crossing within 20000 updates. Crossings require three consecutive checkpoints at train accuracy at least 0.99 or heldout accuracy at least 0.95, sampled every 500 updates. Non-observation is finite-horizon censoring, not evidence of impossibility.
- The recorded width-lag contrast cannot identify a generalization-time shift when all generalization times are censored. Negative recorded control gaps also preclude treating successful training fit as learned heldout arithmetic. Controls are constant, copy, deranged prediction alignment and initialization; there is no separately trained randomized-label control.
- The constant-rate recipe has the highest recorded search aggregate among the three recipes. That ordering does not establish statistical significance, a scheduling mechanism or improved grokking. Learning-rate changes also alter cumulative AdamW shrinkage. The evidence bundle labels candidate diagnostics `unverified`; planning uses the recorded traces without claiming independent scientific validation.
- **Architectural shifts: none.** Width scaling occurs inside one fixed representation and architecture family. No Transformer/MLP transition, learned-representation comparison, Fourier analysis, circuit extraction or lazy-to-rich diagnostic was performed.
- No figures, existing BibTeX or reference provenance were present. There are no inherited retrieval queries to reuse or correct.

## Query set

Every query below is an exact title plus identifier already supplied in `task/task.md`; none is an open-ended topical discovery search.

1. **Benchmark context** — `"Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets" 2201.02177`  
   Grounds delayed generalization and the small algorithmic/modular-arithmetic setting. Contrast with finite-horizon non-observation here; do not assume identical models or splits.
2. **Core method** — `"Decoupled Weight Decay Regularization" 1711.05101`  
   Grounds AdamW and the learning-rate/shrinkage coupling needed to interpret constant versus annealed schedules across zero/positive decay arms.
3. **Result-driven theme** — `"Omnigrok: Grokking Beyond Algorithmic Data" 2210.01117`  
   Positions the recorded weight-norm and loss traces against a norm/landscape account without asserting a tested norm mechanism.
4. **Baseline comparator** — `"Explaining Grokking Through Circuit Efficiency" 2309.02390`  
   Covers an expected alternative explanation for fitting versus generalization; no circuit measurements were made here.
5. **Baseline comparator** — `"Grokking as the Transition from Lazy to Rich Training Dynamics" 2310.06110`  
   Supplies a two-layer-network dynamics comparator. Preserve the regression-versus-classification distinction and the absence of transition diagnostics.
6. **Baseline comparator** — `"Unifying Grokking and Double Descent" 2303.06173`  
   Positions grokking relative to interpolation-related generalization; censored timing is not evidence of either a generalization transition or double descent.
7. **Baseline comparator** — `"Deep Double Descent: Where Bigger Models and More Data Hurt" 1912.02292`  
   Separately anchors model-size and training-duration comparisons. The three-width sweep does not establish an interpolation threshold or a double-descent curve.
8. **Result-driven theme** — `"Understanding Deep Learning Requires Rethinking Generalization" 1611.03530`  
   Contextualizes training fit without heldout generalization and explicit regularization. Its random-label/image experiments are not experiments conducted here.

## Retrieval boundaries and rejected alternatives

For the later retrieval stage, restrict lookup to these eight explicitly allowed starter identities, preferably by exact identifier. Verify returned identity before reading source content. Do not expand citation graphs, cited-by lists, recommendations, surveys, related-paper feeds or broad web results. Even allowed sources can contain links to disallowed material: do not follow them or inspect citation/discussion material that would expose the prohibited work. If prohibited content is encountered incidentally, stop reading immediately and record what, where and how much was seen in the reproduction documentation. Do not try to infer the prohibited identity to implement this boundary. No external encounter occurred in this stage.

Reject broad combinations of grokking with model size, width, capacity or scaling because they risk retrieving the expressly prohibited prior work. Reject generic optimization, benchmarking, scientific-method and paper-writing searches because they do not locate a specific scientific comparator. AdamW supplies the narrow optimization reference actually needed; no separate broad schedule survey is justified by the result.

Reject architecture-transition and Transformer/Fourier-circuit searches because only a fixed one-hot ReLU family was evaluated. The allowed mechanistic Transformer starter is not selected: circuit efficiency already covers the needed conceptual comparator without suggesting a Transformer analysis was performed. Reject language-model memorization papers because no language model or information-content memorization estimator was used. Reject claims of observed grokking, representation emergence, lazy-to-rich transition or double descent.

Do not promote the unexecuted p=31 proposal, widths 16/32/64/128, initial-logit calibration, randomized-label fitting, or paired bootstrap equivalence tests into completed methods. Those differ from the actual recorded modulo-97 experiments. These exclusions keep the eight-query plan focused on the measured fitting/generalization distinction and the implemented optimizer, rather than campaign chronology or an unsupported mechanism.

## Handoff

The JSON mirrors this memo with an empty architectural-shifts list and no failure reason. Later retrieval must verify and read the allowed primary sources before any citation is used; this stage supplies no BibTeX, provenance, paper text or claims-grounding file.
