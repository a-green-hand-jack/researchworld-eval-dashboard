# Reference query plan

**Status: ready.** Eight citation-oriented queries, restricted to explicitly user-authorized starter works. No references have been retrieved, externally verified, or read in this stage; these are retrieval targets, not citation-ready sources.

## Scientific scope and grounding

The paper's defensible neighborhood is **width, initialization, and AdamW decay in finite-horizon grokking on modulo-97 addition**, not a demonstrated universal relationship between size and delayed generalization.

Grounding comes from `paper_data.json`, particularly `best_correct`, `all_programs[*].evaluation_evidence`, and `final_evaluation`, checked against the local trainer definition in `task/evaluate_final.py` and data-pool metadata in `task/resources/{search,final}/dataset.json`. The older `global_memory_summary.md` supplies planning context only: its lack of width-resolved observations does not override the trajectories now present. `figures/` is empty; neither `references.bib` nor `references_provenance.json` exists, so there are no prior retrieval queries to reuse or correct.

- **Task/data:** ordered pairs with label `(a+b) mod 97`. The full input universe has 9409 pairs, but the actual search and final pools contain 4704 and 4705 disjoint pairs, respectively; each uses a seeded 60% training split. Do not describe the experiment as training on the full universe or as a multi-task benchmark.
- **Architecture:** two separate learned input embedding tables, summed with a hidden bias, followed by GELU and a linear 97-class output. Hidden widths are 32, 128, and 256; parameter count is `292 * width + 97`. Width changes capacity within one architecture. **Architectural shifts: none**, hence the JSON array is empty and no architecture-shift query is warranted. Representation transitions were not measured.
- **Methods/controls:** AdamW; common learning-rate, decay, and initialization settings; paired seed/split width comparisons; fixed-reference, zero-decay, and initial-global-norm controls. The latter rescales each width's initial global norm to the width-128 target. It is not a frozen-feature intervention. Recorded controls are not evidence that the proposed random-label experiment was run.
- **Event analysis:** checkpointed fit/generalization events and right censoring. The trainer uses three consecutive checkpoints at training accuracy at least 0.99 and evaluation accuracy at least 0.95, and labels a fitted/generalized event with delay at least 1000 updates as grokking. Recorded normalized restricted delay is not automatically a survival-analysis estimator or evidence of decay-clock collapse.

## Result-driven priorities and limits

The strongest successful search configuration is learning rate 0.003, decay 1.0, and initialization multiplier 0.5. Its reported mean terminal accuracy is 0.47786043216436414, versus 0.43313850513637975 for multiplier 1.0 at the same learning rate and decay. This makes initialization and norm explanations high-priority literature, but the aggregate difference alone does not establish significance, width mediation, or grokking. All three search configurations report zero grokking incidence at the 6000-update horizon. The configuration that doubles learning rate and halves decay, preserving their nominal product, did not qualify; its scientific failure cause is not established.

The final evaluation uses the selected reduced-initialization configuration at 24000 updates on different seeds and a different data pool. It **did not qualify**, and only five of nine planned width-seed records are present. Available width-128 records for seeds 60613 and 70717 report fit/generalization steps of 300/17600 and 200/19200, respectively. All three available width-32 records remain right-censored. All width-256 records and the remaining width-128 record are missing, not observed non-events. These observations motivate finite-horizon, capacity, and regularization comparators, but do not establish a complete size-response curve, causal horizon effect, norm mediation, or a general size law. Final-versus-search comparisons confound horizon, seeds, and data pool.

## Queries

Each quoted title and arXiv identifier below is copied from the user-authorized starter list. Categories and rationales mirror the JSON.

1. **Benchmark context:** `"Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets" 2201.02177` — Ground modular-arithmetic grokking and the distinction between fitting and delayed generalization; contextualize finite-horizon non-events without calling them permanent failures.
2. **Core method:** `"Decoupled Weight Decay Regularization" 1711.05101` — Ground the actual AdamW optimizer, zero-decay comparison, and the distinction between nominal shrinkage and effective regularization.
3. **Result-driven theme:** `"Omnigrok: Grokking Beyond Algorithmic Data" 2210.01117` — Position reduced initialization, measured norm trajectories, and matched-initial-norm controls against norm/loss-landscape explanations; do not claim cross-domain experiments or causal mediation.
4. **Baseline comparator:** `"Grokking as the Transition from Lazy to Rich Training Dynamics" 2310.06110` — Compare theoretical width/initialization explanations while explicitly distinguishing its stated two-layer regression setting from this classification network. No training-regime transition was measured.
5. **Baseline comparator:** `"Explaining Grokking Through Circuit Efficiency" 2309.02390` — Cover the task's explicit competing efficiency explanation without claiming circuit identification from norm and accuracy curves.
6. **Baseline comparator:** `"Progress Measures for Grokking via Mechanistic Interpretability" 2301.05217` — Supply the modular-addition mechanistic comparator; its Transformer is related work, not an architecture trained or transitioned to in this run.
7. **Baseline comparator:** `"Unifying Grokking and Double Descent" 2303.06173` — Position grokking specifically within the capacity/generalization literature; no observed double-descent curve is asserted.
8. **Result-driven theme:** `"Deep Double Descent: Where Bigger Models and More Data Hurt" 1912.02292` — Separately anchor model-size versus training-duration dependence, which matters for interpreting differing horizons and missing widest-model outcomes; this is not another generic grokking search.

Expected comparator families are norm/loss-landscape accounts, lazy-to-rich dynamics, circuit efficiency, modular-addition mechanistic progress measures, and grokking/double descent. They are alternatives for positioning, not mechanisms validated by this run. The last two queries have different roles: a grokking-specific conceptual connection versus the original model-size/training-duration comparator.

## Safe downstream execution

**Do not execute retrieval in this stage.** For the later stage, use the eight arXiv identifiers as a closed allowlist and resolve only the original permitted works directly. The title strings are precise citation selectors, not permission to issue broad web searches. An automated retriever unable to restrict resolution to those identifiers must stop rather than fall back to open-ended search. Do not traverse references, citing papers, related-paper recommendations, aggregator pages, commentary, or repositories. Bibliographic retrieval alone does not meet the requirement to read a work before citing it; later review must remain confined to the allowed originals.

Do not attempt to identify the prohibited unnamed study. If prohibited material is encountered incidentally, stop reading immediately and record the location and extent of exposure for the reproducibility record. No such external encounter occurred here; only local task artifacts were inspected.

## Rejected query families

- Broad combinations of grokking with width/model-size scaling are relevant in principle but unsafe under the explicit exclusion; the exact allowed works provide a bounded alternative without guessing the excluded study.
- Generic optimization, benchmarking, methodology, or paper-writing queries add no scientific precision to the measured width/initialization/decay comparisons.
- Language-model memorization and general language-model scaling are outside this synthetic modular-addition experiment, despite their presence in the starter list.
- Random-label memorization, frozen-feature/NTK interventions, Fourier circuits, and architecture-transfer searches would promote proposed or unmeasured methods into actual experiments.
- Survival-analysis, uncertainty-method, or decay-clock-collapse searches are not added merely because the artifacts contain censoring and bootstrap summaries; no corresponding estimator innovation or validated collapse is established.
- Queries asserting a monotonic width law, permanent failure to grok, causal norm mediation, accepted final results, or measured failures for missing records are unsupported.

## Handoff

The JSON and this memo constitute a ready literature-scoping plan, not a completed bibliography or an accepted scientific conclusion. Preserve non-qualification, missing observations, censoring, and cross-stage confounding in downstream writing. No bibliography, provenance, LaTeX paper, or claims-grounding file is created at this stage.
