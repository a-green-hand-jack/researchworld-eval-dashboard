# Feasibility judgement v2 — measured Tier B cleared

Assessed 2026-11-03 by idea-review-repo, against Research objective #1, its frozen requirements, the idea Brief and the settled story plan. This supersedes v1's unresolved inference gate. It is a feasibility decision before main inference, not a finding about benchmark accuracy or approval of a final research release. Source revisions/hashes are in `provenance/feasibility-v2-inputs.json`.

## Decision

**Go for the frozen Tier B study at the selected 1.5B model.** The measured resource gate is now satisfied: K=8 frozen-prefix candidates, 512 search and 1024 disjoint audit questions, 12,288 main responses, and two sequential 6,144-response shards. Experiment-repo's `provenance/real-scope.json`, `real-partition.json` and `docs/real-scope-freeze.md` specify this scope before any main response. The earlier 16-candidate preferred scope and draft reserve rules are superseded, not results.

Proceed under the already settled plan without an additional feasibility hold or an unrelated manuscript/venue dependency. This judgement does not clear Tier A at the selected model, authorize outcome-driven expansion, or certify completed empirical results. Model size is a scope limitation, not a violation of the objective. No smaller model's infeasibility is asserted.

The replies to story-repo #6 and experiment-repo #5 supply what was requested. No reopening is necessary. Story has assigned every objective requirement and the method/theory/manuscript division; the assessment remains this position's independent delivery, with no paper directory assigned to it. The initial commitment can close after this judgement is supplied to the plan and analysis owners. Reassess if resources, exposure, target or scale change materially.

## Measured basis and arithmetic check

Inspected experiment-repo `1ea24df4b094bb4932595ff8cdaf118bf4906f8e` and story-repo `28f6eadbc8eafba9aeda6a14581c383847bcb698`. The former supplies raw pilot records, summary/diagnostics, main-input tokenizer census, freeze manifest, generation/cache/session code and planned analyses. The latter supplies `study/plan.md`, requirement ownership and timing/precision rules. Current venue and paper inputs are also recorded in provenance.

The representative pilot used the pinned Qwen2.5-1.5B-Instruct Q4_K_M SHA recorded in the manifest, native llama-cpp-python 0.3.18, n_ctx=8192, two threads and the main decoding settings. It generated 100 responses on 25 validation questions, with four instruction/format families and category-first/long-validation inputs. The prior context-setting mismatch is resolved.

Measured pilot response mean was 5.9543 wall seconds and 11.8722 process CPU seconds; wall p95 was 8.9022 and maximum 16.5937 seconds. The reported timed segment was 599.58 wall /1191.37 CPU seconds. These are the analysis owner's measurements. The pilot script initializes the model before its timer, so this timed segment must not be called the entire end-to-end setup cost. The main forecast separately allows overhead, and the final accounting must include loading, build/setup, failures and resumes.

Measured peak RSS was 3,372,800 KiB = 3.2166 GiB, leaving about 0.7834 GiB below the 4-GiB job ceiling. This is sufficient headroom for proceeding with the frozen sequential schedule, not proof that no longer prompt or process allocation can exhaust memory. The tokenizer-only main census has no context overflow; its maximum input is 1143 tokens, longer than the pilot maximum 541. The length-based extrapolation and checkpoints remain necessary. Host CPU sharing can change observed throughput.

Pilot usage totals were 20,695 prompt and 196 completion tokens. There were 15 malformed outputs, zero out-of-option letters, seven length endings and one backend-reported completion of nine tokens despite the requested eight-token cap. These are retained diagnostics; no main accuracy was used to modify the bank. A 15% pilot format-failure rate constrains the meaning of this direct-answer system's score and must be reported. It does not justify silently changing the parser after main results. The backend token anomaly is documented; report actual usage rather than clipping recorded counts.

I independently checked raw-record count, distinct questions, mean latency, call-count arithmetic, memory conversion, forecast sum and finite-audit planning SE using `scripts/check_supplied_scope.py`. Copies of the exact supplied inputs and hashes are bundled under `provenance/scope-gate-inputs/`; output is `assessment/scope-gate-check.json`. This verification does not rerun the LLM or repeat experimental analysis.

## Forecast and remaining time

For the actual Tier B subset, the supplied validation timing fit adjusts the mean input from 206.95 to 237.718 tokens and forecasts 6.9115 seconds/response. This is an extrapolation, not measured main throughput. For 12,288 responses it gives 23.5914 hours nominal generation, 47.1828 with the stipulated factor-of-two contingency, plus 48 hours downstream reserve and 2 hours overhead: **97.1828 hours total**.

The scope records the week conservatively from objective creation, 2026-11-03 12:54:42 UTC, to 2026-11-10 12:54:42 UTC. At its freeze, 166.4748 hours remained, leaving 69.2920 hours after that forecast. My check during this activation still found more than 166 hours remaining. Thus this is a forecast against the remaining original week, not a reset deadline. Each sequential shard has about 23.6 hours of generation at the contingency rate, comfortably below the 72-hour job cap.

The fit is based on 100 dependent validation timings, covers only some combinations of the bank, and extrapolates to longer main inputs. The contingency is a planning margin, not a probabilistic runtime guarantee. Nevertheless the reserve/margin and bounded shards support this resource decision. Tier A at this selected model exceeds a full week under the same rule; there is no need to spend further time proving that a smaller alternative could support Tier A.

At throughput-only checkpoints, compare remaining conservative cost with the deadline minus reserve. Retain the frozen rule: preserve caches and request a recorded scope revision if the gate fails. The predefined Tier C fallback uses the first even-position question shard and first four frozen-prefix candidates, with all extra calls accounted for. Never select completed rows, stop, or expand according to accuracy. Report actual cumulative runtime/calls/tokens after the jobs finish.

## Precision and claim limits

The selected configuration's fresh-item target is micro accuracy on the 11,520 pinned-benchmark questions outside the entire 512-item search pool. The 1024 audit items are sampled uniformly without replacement. For this target, the worst-case finite-population planning SE is 1.4915 percentage points and the approximate normal 95% half-width 2.9233 points. These are calculations, not observed error bars or population coverage measurements. Paired superiority precision depends on wins/losses and can be materially worse.

The supplied exact hypergeometric inversion addresses the finite audit design. Paired wins/losses intervals use marginal hypergeometric inversion plus a union bound; they retain pairing and can be conservative. This inspection checks that there is an appropriate implementable route, not a replacement for the analysis owner's validity checks or independent final review. The selected prompt must remain frozen by search labels, and audit labels must not feed parser, bank, budget or model changes.

Keep conditional 20,000-repeat selection resampling, empirical-cache calibration and genuine disjoint-audit checking separate. The cache's exact mean is known for its declared empirical distribution; the audit's underlying finite target is estimated. Monte Carlo precision cannot erase question-pool uncertainty. Noisy audit sign/claim disagreement is not measured population false-claim error. A real gap below audit resolution or an unresolved superiority decision remains a valid result; main inference and analysis must still be completed.

The planned n={16,32,64,128,256,512}, K={1,2,4,8}, default/tie seeds and reporting/decision comparisons are frozen. Whole rows preserve candidate pairing. The paired-row sensitivity bootstrap has a timed-analysis pilot rule; keep it bounded and preserve the exact finite-audit interval separately. Report width, selected quality and resource costs with calibration, rather than treating broad valid intervals as automatically useful or corrected intervals as debiased point scores.

## Settled ownership and completion limits

Story's plan covers the complete objective and assigns experiment the methods/derivation validity, numerical analysis, real inference, diagnostics and reproduction; paper the final exposition/full manuscript/build; figtab the figures/tables/generators; venue official assets/rules; and story plan/CODEOWNERS. Context and feasibility supply their material without taking another owner's final paths. The CODEOWNERS transfer remains the appropriate delivery mechanism, not a reason to stall independently authorized inference.

Venue has now supplied verified ICLR 2027 official assets and requirements, including its nine-page main-text rule and mandatory AI-use statement. Paper has working manuscript material but no complete reviewed delivery at the inspected revision. The original integration gaps have concrete owners/routes; those outputs remain necessary. Neither this gate clearance nor a successful pilot completes the required real experiment, paper, code or final version review. Retain v1's scientific scope limits: fixed-bank search, one small quantized model, strict direct-letter protocol, pinned finite benchmark and permitted-source evidence. General adaptive optimizers, arbitrary fresh natural-language questions and stronger models are outside demonstrated scope.

No new literature search or prohibited-material access occurred in this reassessment. Re-read objective and relevant frozen deliverable requirements before this delivery. No main performance result is asserted or manufactured.
