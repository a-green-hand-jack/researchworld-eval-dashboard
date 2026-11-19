# Paper Strategy

**Status:** ready for `paper_standalone` using `write-paper-standalone`; strategy only, not a manuscript.

**Provisional title:** Memorization Without Observed Grokking Across MLP Widths

## Central Question and Thesis

**Question.** Within a fixed training horizon, how do hidden width and weight decay affect memorization and observed generalization in modular-arithmetic MLPs, and what can a censored width-lag contrast actually establish?

**Thesis.** Across the tested addition and subtraction conditions, wider fixed-rate MLPs attain sustained memorization earlier or attain it when the narrowest models do not. None attains sustained generalization within 20,000 updates. The reported width-lag contrast consequently reflects fitting and endpoint substitution, not an identified effect on grokking time.

This is a finite-horizon negative-results paper with a metric-identification analysis, not a new scheduling algorithm or a demonstrated neural mechanism. Its strength is a clear separation between what the experiments observe and what their lag statistic cannot establish. It partially answers the original research question; it does not complete the original proposed mechanistic investigation. Readiness means a coherent grounded paper is possible, not that ICLR acceptance or a novelty claim has been established.

## Evidence and Framing Decision

No prior manuscript, resolved edit-context input, `aggregated/`, or `extra_tasks/` directory is present. The JSON status `recentered` describes a fresh shift from the source proposal to the observed scientific setting, not an edit to an existing paper. No inherited title or figure plan exists to preserve.

Three framings were compared:

| Candidate framing | Decision | Grounded reason |
| --- | --- | --- |
| Preserve the proposed capacity-versus-decay-clock explanation | Reject as the thesis | Random-label fitting controls, initial-logit calibration, and the proposed generalization-time equivalence test were not performed. |
| Broaden into an annealing or optimizer-method family | Reject as the thesis | A selected fixed recipe has final evidence, but alternate schedules and the original lower-rate implementation lack matched final-plane comparisons. Search scores cannot establish final superiority or a width mechanism. |
| Recenter on the final width-by-decay factorial and censoring boundary | Select | The final evaluator supplies all condition-level training traces and the event/aggregation definitions needed to explain the negative result and audit the lag contrast. |

The final evidence is independent of the source proposals and recent memory. `downstream_study` is absent; no `study.*` grounding sources are supplied. Do not invent a campaign selection contract, search score differences, or scored/unscored attempt counts. Omit a comparison against the original learning-rate-0.001 implementation because no comparable final-plane result is retained. Missing performance evidence is not a loss.

### Private Qualification and Provenance Audit

The authoritative `final.qualification.status`, `final.qualification.outcome`, and `final.qualification.correct` values are **completed**, **qualified**, and **true**, respectively. Do not replace these with an earlier search acceptance or failure label. Record the completed, accepted evaluation in a reader-facing reproducibility disclosure without calling it evidence of generalization, scientific validity, superiority, or a causal mechanism. If revised authoritative artifacts instead record failed qualification, disclose that failure throughout writing, review, audit, and revision while preserving all limitations; the cause remains unknown without diagnostics.

The local final evaluator and evidence JSON hashes match the final metadata. The available constant-rate implementation specifies learning rate 0.01; its connection to the final evaluation is supported by retained source and campaign records, but an independently reconstructed match to the final program-tree hash has not been established. Keep this distinction explicit in the private audit. The source labels candidate diagnostics as unverified. The scientific observations used here are retained evaluator-generated traces, not candidate-reported measurements; do not extrapolate this into comprehensive integrity or adaptivity certification.

### Actual Evaluated Setting

- Modulus 97; addition and subtraction, not the proposal's alternate modulus or data fraction.
- Concatenated one-hot inputs and a linear–ReLU–linear network with hidden widths 16, 64, and 256; measured parameter counts 4769, 18785, and 74849.
- Full-batch cross-entropy training with AdamW, decay 0 or 1, the fixed constant-rate policy, and a 20,000-update horizon.
- Three initialization seeds: 1009, 2027, 3037. Each seed episode contains twelve condition records; do not call the three episodes three training runs or treat all 36 condition records as independent replications.
- Each operation's deterministic final pool contains 4705 pairs, split into 1411 training and 3294 held-out pairs. Splits are fixed across seeds. This is not 30% training on all 97-squared input pairs.
- Checkpoints every 500 updates. Memorization requires training accuracy at least 0.99 at three consecutive checkpoints; generalization uses held-out accuracy at least 0.95 over the same persistence rule. The event is dated to the first checkpoint of the qualifying triplet.

Method provenance: hash-matched `task/evaluate_final.py`, `task/resources/final/benchmark.json`, `task/requirements.txt`, and the retained constant-rate source. Scientific observations and deterministic summaries are grounded in `final.evidence.episodes`; named metrics use `final.metric.*`. Do not manufacture additional source identifiers for unregistered code files.

## Scientific Explanation and Its Testability

Use a deliberately limited accounting explanation: finite-horizon width differences in fitting can generate apparent lag differences even when no generalization time is observed. The stored event table tests the fitting part; the evaluator's exact formula tests the accounting part. This is a retrospective interpretation, not a preregistered mechanism test.

The evidence gives 30 memorization events among 36 condition records and no sustained generalization event. Widths 64 and 256 memorize at checkpoint 500 in every condition. Width 16 without decay memorizes at checkpoint 1000 or 1500; width 16 with positive decay never meets the threshold. Checkpoint ties do not imply equal continuous-time dynamics.

Let T be the training horizon, M the sustained memorization checkpoint, and G the sustained generalization checkpoint. The reported lag is T if M is absent; otherwise it is max(0, (G if observed else T) − M). When G is absent but M exists, this is the observed remaining follow-up after fitting, not an observed delay to generalization. When M is absent, a post-memorization delay is not even defined: T is a scoring convention.

Under positive decay, width 16 receives T, whereas width 256 receives T−500. Their difference is therefore exactly 500 for every seed. The supplied interval [500, 500] reflects identical values of this capped statistic, not precise knowledge of latent grokking times. The reported decay interaction, 1083.3333333333335 updates, has the same limitation. Explain these facts in the body, not only the supplement.

An observed generalization event or failure to reproduce this formula would defeat the present account of these stored contrasts. A causal explanation of why the networks do not generalize would require new interventions, which are out of scope here. The original claim about near-invariant true generalization times across width remains untested.

## Included Method Groups

1. **Fixed-rate width family without weight decay — baseline.** The within-evaluation reference, not the original lower-rate source program.
2. **Matched width family with unit decay — ablation.** The evaluated regularization contrast at the same widths, operations, seeds, and horizon; no claim of scale-matched initialization.
3. **Nonlearning prediction references — supporting.** Initial network, training-label mode, exact-pair lookup with mode fallback, and label-deranged-input predictions. Disjoint held-out pairs make the lookup and mode references identical. Derangement uses held-out labels to construct a diagnostic permutation and is not a deployable learned comparator or a random-label training experiment.

Do not include proposal-only width grids, independent random-label networks, calibration procedures, mechanistic circuits, or a sequence of discarded scheduling branches as required methods.

## Results Organization

Both operations are condition-specific evidence for one thesis. Organize by scientific comparison, not by experiment order:

1. **Width and Decay Effects on Fitting.** A twelve-row main event table shows each operation/decay/width condition, all three memorization times or non-attainment, and observed generalization count. Preserve the six narrow positive-decay fitting failures.
2. **Held-Out Outcomes.** Compare final-five-checkpoint training and held-out accuracy across width. Show the individual seed observations; contextualize held-out results using the available reference predictors. The stored per-record score is the final-five-checkpoint held-out mean, not an event-attainment rate.
3. **What the Capped Lag Measures.** Give the exact formula, the supplied contrast and degenerate interval, and the decay interaction with their identification caveats. These are comparisons over width, not learning-curve progression.

If reporting the aggregate control gap, define it as the equally weighted late-window accuracy difference against four stored references, two of which coincide. Do not imply four independent controls. Avoid pooled significance tests, unsupported generalization-rate confidence intervals, or imputation of unobserved events as actual event times. Only three initialization seeds vary; neither dataset split nor operation supplies independent seed replication.

## Required Figures and Readability

The inspected ICLR template uses `paper.sty`: **one 5.5-inch text column and a 9-inch text height**. A full-width figure is one text-column wide; do not assume a two-column conference format. All three required figures use the full text width. A nominal half-width figure would be only 2.75 inches wide and is inappropriate for these panel/annotation densities. Heights below are design budgets, not measured results.

| Figure | Scientific content and generator | Budget and placement |
| --- | --- | --- |
| `study_overview` | One early design-and-inference overview using `generate-concept-figure`: the evaluated factorial, the two distinct event definitions, and the finite-horizon inference boundary. No fabricated curves or causal mechanisms. | Full width, page 1 or 2; 2 compartments, at most 2 across; at most 6 categories and 3 series per compartment; minimum 9-point rendered labels; graphic height about 1.7–2.0 inches plus caption. |
| `width_decay_outcomes` | Matplotlib seed dotplots. Columns: addition/subtraction. Rows: late-window training/held-out accuracy. Width on the horizontal axis, decay in two fixed colors, three seed markers and condition mean. | Full width; 4 panels in 2-by-2 layout; 3 width categories and 2 series per panel; minimum 8.5-point labels; graphic height about 3.1–3.5 inches plus caption. Match scales within rows; use separate row scales so held-out values remain visible. |
| `censoring_audit` | Matplotlib direct comparison of capped lag by width. One panel per decay condition; operation-specific neutral shapes/patterns and individual seeds. Explicitly mark missing memorization and state that generalization is unobserved throughout. | Full width; 2 panels in one row; 3 categories and 2 series per panel; minimum 9-point labels; graphic height about 2.0–2.3 inches plus caption. A labeled focused vertical range is acceptable; an apparent event at the cap is not. |

Use one overview workflow only; orchestration, not this strategy stage, owns its execution. Keep Figure 2's decay colors semantically stable; Figure 3 can distinguish operations with neutral shapes rather than reassign those colors. No trajectory figure is required: direct outcomes and event tables support the thesis without a run diary or compressed learning curves.

**Export contract.** Quantitative plots must have editable/reproducible plotting source, vector PDF, and 300-DPI PNG. Reference PDF from LaTeX whenever present. Require at least 2400 pixels for full-width raster output or 1200 for partial/column-width raster-only output. For a 5.5-inch final graphic, render the source canvas large enough to meet the PNG pixel budget with proportionally scaled typography, rather than upscaling a saved image. Preserve editable draw.io and any PDF export for the overview; use raster only if no PDF exists and meet the full-width pixel budget.

## Body Layout and Scientific Value

Target about **8.5 body pages**, excluding references and supplement, without margin or font changes. An eight-page body must finish at least 75% full under `VENUE.md`.

| Component | Approximate body-page allocation, figures included |
| --- | --- |
| Abstract, Introduction, and early overview | 1.5 |
| Related Work | 0.75 |
| Experimental Design and Event Definitions | 1.75 |
| Results, both quantitative figures, and event table | 3.0 |
| Discussion and Limitations | 1.25 |
| Conclusion | 0.25 |

Use the space for a precise fitting-versus-generalization question, exact event definitions, paired-seed evidence, readable comparisons, reference-predictor interpretation, the capped-lag derivation, and limits of identification. Do not fill pages with implementation history, repeated zero-event panels, literature padding, or unexecuted experiments. If the grounded material cannot fill the venue budget substantively, surface that conflict rather than disguise it.

The template scaffold contains a named author and final-copy command; these are incompatible with anonymous review. The later writer must use anonymous review mode, omit author identities/affiliations/acknowledgements/funding and identifying links, preserve the required orchestrator watermark, and check ICLR 2026 submission compliance. The old style-file header alone does not establish latest-template provenance. Do not invent a venue checklist.

## Supplementary Information After References

Keep the decisive negative evidence and capped-lag limitation in the main paper. After the references, use the prescribed clear-page/appendix/Supplementary Information structure for:

1. **Exact Data and Training Specification.** Deterministic data construction and final-pool counts; actual one-hot representation and network parameterization; optimizer settings; seed and checkpoint definitions. Source registry anchor: `final.evidence.episodes`, supplemented by the inspected final evaluator, resource JSON, and dependency file.
2. **Complete Condition-Level Observations.** All 36 records with events or non-attainment, capped lag, late-window accuracies, and completion. Sources: `final.evidence.episodes`, `final.metric.completion_fraction`, `final.metric.delayed_fraction`.
3. **Reference Predictors and Available Diagnostics.** Separate stored reference accuracies and the duplicate-control explanation; descriptive endpoint loss/norm tables only. Sources: `final.evidence.episodes`, `final.metric.control_gap`. No new mechanism test is implied by these diagnostics.
4. **Capped-Lag Calculation and Reproduction Map.** Exact event/aggregation pseudocode, three-seed paired contrast and Student-t interval construction, and artifact-to-script/table/figure mapping. Sources: `final.evidence.episodes`, `final.metric.restricted_mean_lag`, `final.metric.width_lag_contrast`, `final.metric.width_lag_ci_low`, `final.metric.width_lag_ci_high`, `final.metric.decay_interaction`. Document `numpy==2.1.3` and `torch==2.5.1+cpu`, and distinguish training from replotting stored results. The evaluator requires an RPC execution context; do not invent a working standalone command or undocumented hardware/runtime claim.
5. **LLM Usage.** A separate section discloses artifact-supported roles in idea proposal, bounded policy implementation, reference-query planning, framing, and writing, while distinguishing evaluator-owned training/measurements. Do not claim undocumented human review or model identities. Anchor to the final evidence and named local implementation/query-plan provenance; do not present an episode as sole proof of writing roles.

Any subsequently supplied authoritative appendix-ranked analyses belong here by default. Do not guess their ranking, promote or discard them to satisfy page counts, or retroactively alter this strategy on that basis.

## Limits, Reference Safety, and Writing Guardrails

The empirical scope is one modulus, two related operations, one representation/architecture, three widths and three initialization seeds, a fixed split per operation, two decay values, one selected learning-rate recipe, and a finite horizon. Initialization scale is not matched across widths. There are no independently trained random-label controls, circuit measurements, or true generalization-time observations. Late threshold excursions without enough following checkpoints cannot meet the sustained-event rule. Non-attainment does not imply that grokking never occurs, and low accuracy alone does not identify the cause.

Reference files contain retrieved metadata, including off-target entries; metadata retrieval is not proof of consultation. Only exact starter-literature identities verified against both bibliography and provenance may be used, and substantive claims require actually consulting the approved sources. Never identify a paper by a query-string match, expand citation graphs, or conduct broad width-grokking searches. This strategy made no external lookup and inspected local reference metadata only. Stop and log any identifiable prohibited encounter; do not infer the forbidden paper's identity. No novelty claim may depend on pretending that an unrestricted literature review was performed.

**Forbidden headings:** Campaign Progression; Search Timeline; Milestones; First Successful Run; Phase 1 / Phase 2; Experiment A / Experiment B; Winning Configuration; Successive Improvements; Capacity-versus-Decay-Clock Mechanism Confirmed.

**Forbidden public phrasing:** “we then tried,” “first valid result,” “subsequent improvements,” “next-best,” “later variants,” “search winner proves,” pipeline-native metric/acceptance labels listed in the JSON contract, “larger models grok faster,” “grokking never occurs,” “the confidence interval proves faster generalization,” claims of random-label control experiments, and “state of the art.” Internal field names and paths appear above only as private audit or source-routing instructions, not recommended manuscript language.

Prefer explicit reader-facing names: memorization attainment, generalization attainment, late-window held-out accuracy, and administratively capped lag. Keep the two sustained thresholds distinct. A completed accepted evaluation is compatible with a scientifically negative observation; publication eligibility cannot upgrade that observation into evidence for a neural mechanism.

## Stage Boundary

Write only the strategy artifacts and append-only memory records in this stage. Do not draft `paper.tex`, create `claims_grounding.json`, render figures, launch new experiments, or run final-paper validation. Validate the strategy's JSON structure, registered source IDs, figure budgets, and consistency with existing evidence only.
