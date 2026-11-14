# Feasibility judgement v1 — bounded fixed-bank study

Historical assessment. The measured gate is now resolved in [feasibility-v2.md](feasibility-v2.md); retain this version as the original pre-pilot judgement.

Assessed 2026-11-03. Owner: idea-review-repo. This is an independent feasibility judgement for the plan owner, not experimental analysis, a final study plan, manuscript review, or release approval. Exact inspected revisions and frozen-file hashes are in `provenance/feasibility-inputs.json`. Commitment: idea-review-repo #3. Missing measured real-run evidence is requested in experiment-repo #5.

## Decision

**Conditional go for a bounded CPU study; real-inference scale is not yet cleared.** A frozen finite prompt bank, one newly run small instruction LLM on pinned MMLU-Pro, known-truth synthetic experiments, disjoint real audit questions, an explicit decision consequence, and tested reporting alternatives can meet the objective in a week. A 7–8B model, all 12,032 test questions, DSPy, adaptive prompt generation, and a new inference theorem are not mandatory. Adding them before measuring inference cost would threaten the required empirical and paper delivery.

The synthetic component is completed according to committed analysis records. The real component has pinned downloads, a successful native backend build, and generation/cache code, but the inspected revision has no measured inference pilot or main results. This is an evidence gap for the analysis owner to resolve, not proof of resource failure. A conference-format paper is achievable; conference acceptance or sufficient novelty cannot be guaranteed. Context evidence establishes classical precedents for selection bias, holdout evaluation and simultaneous inference, so those ideas alone cannot be claimed as inventions.

No full plan has yet been pushed by story-repo at the inspected revision. This judgement assesses the experiment owner's draft and existing requests. Story must settle design, methodological ownership and delivered paths; I do not replace those decisions.

## Evidence and available resources

Read Research objective #1, all five frozen files, idea-repo's full Brief and estimand handoff, relevant analysis specifications/code, runtime/failure records, synthetic summary, and presentation input/caption conventions. Read current issues/releases of the six accessible context, plan, analysis, presentation, venue and paper repositories. Only idea-repo had a published context release and populated wiki among these inspected repositories; absent wikis could not be cloned.

`ht-resource describe local-compute` explicitly gives CPU-only jobs with sandbox ceilings: 2 CPUs and 4096 MB RAM, shared host resources, and no verified GPU or external paid inference route. The recorded snapshot had 58 CPU placements sharing a 40-CPU host. The supplied 8-core/32-GB/24-GB-GPU examples are not the available job allocation. Their unmeasured throughput estimates cannot size CPU inference.

Analysis `provenance/downloads.json` records hashes for pinned MMLU-Pro and Qwen2.5 0.5B/1.5B Q4_K_M files (about 0.49/1.12 GB). File sizes establish acquisition/storage, not loaded memory, speed or accuracy. Backend build success establishes installation, not inference performance. Failed wheels/download/TLS attempts are documented and must remain in reproduction records.

Analysis `results/synthetic-main.summary.json` reports 288 cells × 20,000 independent repetitions, 89.881 measured wall seconds, 89.707 process CPU seconds and 285,564 KB peak RSS. These are the analysis owner's committed measurements, inspected without rerunning its experiment. Further simulation expansion is unnecessary for feasibility; prioritize real-data and report gaps.

`run_real.py` freezes hashes, validates context lengths, caches raw outputs and supports resume. `render` uses question/options rather than gold answer/rationale. This is a useful basis for an auditable experiment; code existence does not establish completed inference.

## Cost and precision bounds

The attached CSVs are **analytic planning calculations**, produced by `scripts/calculate_planning_limits.py`, not empirical results. Do not copy them into a paper as measured throughput, coverage or model performance.

For a fully scored K-candidate bank on S search and A audit questions, generation count is K(S+A), plus validation/setup. Auditing only one frozen winner can use A additional calls, but repeated winner identities/method comparisons require an explicit caching and audit-exposure design. Count search, audit, input/output tokens, initialization and retries. Eight-token answers do not make long prompt prefill free.

Illustrative **assumed-rate** scenarios: K=16, S=A=1024 requires 32,768 responses and 9.1/45.5/91.0 hours at an assumed 1/5/10 seconds per response, before overhead. K=8, S=512, A=1024 needs 12,288 responses (3.4/17.1/34.1 hours at those assumptions). Scoring all 12,032 test questions for 16 candidates needs 192,512 responses; the assumed five-second scenario is 267.4 hours. These calculations explain the need for measured throughput; they do not prescribe sample size.

For iid binary audit observations, accuracy SE <= 1/(2 sqrt(A)). Approximate normal 95% half-widths are 4.33 percentage points at A=512, 3.06 at 1024, and 2.17 at 2048. These are planning approximations, not exact confidence guarantees. A paired selected-minus-default contrast can have SE <= 1/sqrt(A), twice that bound: plan from discordance and paired uncertainty. Sampling without replacement from a finite declared benchmark has a different design and may reduce uncertainty; it does not identify an unknown future-question population.

Many selection resamples from one cache reduce Monte Carlo error conditional on the cache. They cannot substitute for independent questions, repeated generations, new models or a fresh audit. If the signal is below audit resolution, accept an inconclusive real comparison or enlarge the audit within measured resources; do not stop on a favorable effect or present synthetic truth as real truth. One documented real setting satisfies the minimum; generality across models, optimizers and benchmarks remains limited.

## Gates before expensive expansion

| Gate | Required evidence | Owner/current state |
| --- | --- | --- |
| Actual inference | Validation-only outputs; model/backend hashes; representative lengths/formats; wall/CPU time, peak RSS, invalid/truncated counts | Experiment; requested in #5, not supplied at inspected revision |
| Bounded cost | Explicit K, search/audit counts, calls; conservative timing extrapolation and remaining one-week time | Experiment supplies measurements; story settles scale |
| Frozen protocol | Model/parser/bank/partition/weights, tie rule, reporting and decision rules fixed before main outcomes; audit policy | Story + experiment; draft code available, full plan pending |
| Honest interpretation | Audit resolution and uncertainty; real result may be inconclusive; no noisy-audit-to-population-error conversion | Experiment; then paper/figtab |
| Complete delivery | Owned method/theory/manuscript/reproduction paths, latest official allowed template, page/checklist rules, build/version review | Story/venue/paper; not delivered at inspected revisions |

Suggested policy, for story's decision: launch one primary real setting first; require a conservative forecast to fit the remaining week while reserving at least 48 hours for failures, analysis, presentation, integration and review. A factor-of-two timing contingency is a planning margin, not a guarantee. Avoid shards approaching the 259,200-second job limit; use resumable bounded shards if necessary. Check shared load before adding jobs. If the gate fails, reduce bank/question/model size before main outcome inspection, or use an actually available authorized resource. Preserve the full real study, decision endpoint and reporting comparison. No current throughput measurement justifies choosing among the scenarios above.

Pilot/main mismatch: `pilot_inference.py` uses n_ctx=4096 and one instruction/format, while `run_real.py` uses n_ctx=8192 and 16 variants. Measure or justify representative main memory/timing, including long questions. Do not silently truncate/drop items. Resume summaries time only the active session; retain cumulative compute across sessions/failures. Diagnose invalid outputs, context failures, max-token endings and letters outside each item's actual options. These observations have been supplied to the analysis owner; this memo does not implement their code.

## Scientific risks and necessary scope limits

1. **Selection scope.** Selection from an outcome-independent frozen bank is legitimate automated tuning. It does not test feedback-adaptive prompt generation, pipeline compilers generally, arbitrary adaptive stopping or repeated audit use. Simultaneous intervals require the full declared family and suitable sampling assumptions. A new adaptive arm needs its own validity/resource argument and is unnecessary for the minimum study.
2. **Target mismatch.** Final selected-configuration accuracy, expected selection-procedure quality and oracle quality differ. Splits can change selected prompt and selection size. Compare calibration, width and selected quality for each actual target. Simultaneous intervals can protect coverage while leaving the reused point estimate biased; they are an interval correction, not a debiasing estimator.
3. **Fresh-question uncertainty.** A disjoint finite audit is noisy. Known cached-reference means permit explicitly conditional with-replacement coverage studies for that empirical distribution. Audit interval overlap is not measured population coverage. Resampling must preserve question rows across candidates and repeat selection when the target requires it. Separate Monte Carlo uncertainty from question/model-generation uncertainty.
4. **Decisions.** At least one explicit decision is required. The completed synthetic non-overlap superiority rule has known truth but is a particular conservative rule, not a universal paired test or claim-conditional false-discovery rate. A real counterpart can show apparent-superiority changes or audit disagreement with paired uncertainty; sign reversal alone does not establish a population false claim.
5. **Cost and usefulness.** Independent audits cost extra unless budgets are reallocated. Question-matched and call-matched splits differ; fewer selection questions can reduce selected quality. Simultaneous intervals can be valid yet too wide. Preserve coverage, width/decision utility and small-gap controls. Existing synthetic support must not disappear during paper compression.
6. **Model/benchmark scope.** A small quantized model, direct-letter decoding and strict invalid-as-wrong parser define a particular measured system. They do not establish stronger-model or reasoning-pipeline behavior. Some pinned questions have fewer than ten options. Report sampled categories and target weights; a subset score is not the full MMLU-Pro score. Validation-only checks are reasonable; outcome-driven main/audit parser tuning changes the protocol.
7. **Independence and novelty.** Do not seek or infer the withheld paper. Use permitted exact-source context and access records. This review made no external literature search. Context-owner source notes are evidence supplied to this assessment, not a claim that this position read every original article. Establish the actual empirical contribution rather than renaming classical corrections.

## Objective coverage and ownership

| Requirement | Feasible route / outstanding work | Accountable positions |
| --- | --- | --- |
| Gap and drivers | Completed controlled grid + real fixed-bank selection/audit; n/K and correlation/quality distinctions | Experiment; story settles claims |
| Decision consequences | Known-truth synthetic rule + precisely labelled real comparison | Experiment; figtab/paper present |
| Tested reliable reporting | Reuse versus audit/split/simultaneous intervals, with calibration/width/quality/cost | Experiment; story settles method scope |
| Newly run LLM and real benchmark | Hashed Qwen + pinned data; timing then bounded main generation and analysis | Experiment; mandatory open work |
| Full PDF/LaTeX, sections, page/checklist compliance | Current official allowed template; integration and build checks | Venue + paper; story allocates |
| All code, versions, data, seeds, commands, runtimes, figure/table mapping | Extend existing analysis/provenance and plotting code through real setting; cumulative cost ledger | Experiment + figtab + paper; venue assets |
| Honest failures, uncertainty, limits, read citations and forbidden-source record | Preserve provenance and check claims against measured outputs | Each owner; paper integrates; reviews judge |
| Reviewed final release | Paper main delivery, independent version review, merge to final | Paper + internal review via required world route |

Paper has no manuscript or CODEOWNERS at the inspected revision. This is an integration gap, not permission to omit requirements. Existing story #2/#3/#4 requests identify analysis, figure and context routes. I additionally request story record these gates and decide whether feasibility text belongs in delivered paths. Until agreed, this memo is my repository delivery and does not supply another owner's final work.

## Check against commitment

This memo covers the objective, verified resources, measured versus assumed costs, scope/uncertainty risks, revision gates and requirement ownership. Missing timing and plan/path settlement remain owned open requests. Re-read objective and Brief before delivery. No experimental result was created, rerun or fabricated here. Reassess when experiment #5 supplies measurements or story changes the design.
