# Plan decision: apply the prespecified Tier C fallback

This records the plan owner's scope/target decision using supplied resource evidence. It creates no new analysis result and does not declare the study complete. This decision supersedes Tier B as the primary delivered real scope; the original freeze and launch clearance remain history below.

## Current scope and release of the analysis hold

Apply the exact fallback already frozen in experiment-repo `1ea24df4b094bb4932595ff8cdaf118bf4906f8e`, `provenance/real-scope.json`: the first completed even-position question shard and the first four frozen-prefix candidates. Experiment's request story #11 reports complete generation of that shard without inspecting answers/correctness. No second shard is required. Commit the derived fallback manifest, question/candidate identities, timing/session/resource evidence and exposure record before unblinding, then proceed with the required real analyses. No additional plan, feasibility or unrelated integration approval is required. Independent feasibility-v3 at `42129f85aeebb4347c9291d2982aa07ad57fbe60` independently clears this exact fallback without a new hold. The full released memo has been read. Experiment has now committed the derived manifest, hashes and pre-unblinding exposure record at `6fc477e68038324194b89302d3c43836be1d37bb`; the earlier recording prerequisite is satisfied, not an outstanding approval gate.

| Frozen or derived element | Current primary scope |
| --- | --- |
| Model | Qwen2.5-1.5B-Instruct Q4_K_M; SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |
| Backend / decoding | llama-cpp-python 0.3.18 native; n_ctx8192, two threads, greedy temperature0/top_k1, requested output maximum8; unchanged strict parser |
| Retained questions | Original ordered partition questions[::2], preserving IDs/order/pool: search256 and audit512 |
| Retained candidate prefix | [0,10,14,13]; default0; no use of omitted candidates for selection or calibration |
| Analyzed responses / generated responses | 3072 / 6144; preserve all raw outputs and count all generated answers in actual cost |
| Primary n / K | 256 / 4 |
| n / K slices | {16,32,64,128,256} / {1,2,4} |
| Repetitions / seeds | 20000 conditional-selection and 20000 iid-cache repetitions; original seeds and primary tie seed20261109 |
| Bootstrap sensitivity | n64 and256, K4; planned1000 paired whole-row outer/2000 inner repeats, sized after timed20/200 pilot; sensitivity, not exact population intervals |
| Remaining-benchmark / empirical-cache targets | 11776 questions outside retained search256 / 768 retained search+audit rows, respectively |

The bank hash remains `124a67cac15f1e8755b2eb7ae501655a50c6a2badfc50b91d3355eb78e9742b9`. The source Tier B partition hash remains `4fc04b2dfcf5632e8d0bc777663010573cae01ef454110972f41fd54f3abe8ea`; the committed derived Tier C partition hash is `95ac019141636db14a746d0967716d940c9155ce9926b17abe6802d4eafca4cf`. The source hash does not describe a new partition file. All parser, decoding, scoring, default, question weighting and audit-use rules remain unchanged. Omitted responses are preserved raw, excluded from primary analysis and calibration, and included in compute accounting; no post-unblinding expansion is authorized.

## Resource trigger and accounting

Story #11 reports job-27eb30d686 completed6144 answers, starting2026-11-03 15:34:31UTC and ending2026-11-06 19:14:15UTC. Reported process elapsed time is272384.04s=75.6622h; process CPU56081.59s=15.5782h; resource active wall27485.096s=7.6347h. These different accounting boundaries must remain explicit. The process elapsed time exceeds the original shard forecast11.8h. At the request, about87h remained before the original2026-11-10 12:54:42UTC deadline; another shard at twofold observed elapsed cost plus48h downstream reserve cannot fit. The prespecified elapsed-time rule therefore triggers Tier C without inspecting correctness. The timing/session/summary evidence is now committed in experiment revision `6fc477e68038324194b89302d3c43836be1d37bb`. Experiment owns reconciliation of the distinct clocks; no suspension cause is inferred from their difference.

No further inference is needed for this complete bounded real design. Reduced scale increases uncertainty and narrows search breadth; it does not waive the real-model gap, decision, reporting comparison, conditional resampling, empirical calibration, diagnostics, reproduction or independent final-review requirements. Preserve setup/build/pilot/failure/resume costs and all6144 generated main responses, rather than reporting only3072 analyzed responses or substituting active runtime for elapsed time.

## Current exact finite-audit target and conditioning

Let B contain12032 pinned benchmark questions and S_C be the entire retained256-question search reservoir. Primary real accuracy is

`theta_remaining(j; S_C) = sum_{x in B minus S_C} Y_j(x) / 11776`.

The retained512-item audit is uniform without replacement from B minus S_C under the marginal partition design, averaging over the omitted original search256 and omitted audit positions. For fixed C, the audit interpretation conditions on retained S_C and its search-selected winner; it does not additionally condition on the omitted original search identities. This fixed-design statement must be distinguished from the delivered runtime-selected guarantee below. If one conditioned on the original full512-item search reservoir instead, the appropriate complement target would differ. Omitted search labels are not used. Experiment owns verifying and documenting this design argument and the interval implementation. Do not label these as conditional guarantees for every fixed original512-item reservoir or for the observed runtime/fallback event without a separate justification.

Every n/K slice retains the complement of all256 retained search items even when n<256. Selected-minus-default uses the same11776 target and paired audit questions. Search-minus-audit estimates search score minus remaining-benchmark accuracy with audit sampling uncertainty; it is not a full12032-item or unknown-superpopulation gap. The transformed simultaneous search interval uses retained search successes and the11776 complement denominator; its guarantee is unconditional over retained-reservoir sampling, distinct from the audit's fixed-design conditional argument; the delivered audit guarantee after runtime selection is unconditional as explained below. Ordinary iid/binomial search intervals remain comparators.

Worst-case finite audit planning SE is approximately2.161pp and normal95% half-width4.236pp; exact intervals depend on actual counts and paired contrast uncertainty can be larger. These are precision approximations, not measurements. Known-empirical-truth calibration uses exactly768 retained rows and the four retained candidates, with whole-row iid draws with replacement and known cache means. Its target differs from the11776-item remaining benchmark. Conditional Monte Carlo repetitions do not remove audit uncertainty; noisy audit disagreement is not measured population false-superiority.

## Runtime-selection protection: supplied analysis correction

Experiment committed the correction and pre-unblinding record at `6fc477e68038324194b89302d3c43836be1d37bb`, `docs/statistical-guarantees.md`, `provenance/real-scope-tier-c.json` and `provenance/pre-unblinding-tier-c.json`. Runtime can correlate with correctness even when no accuracy is inspected. Neither fixed-C conditional audit unbiasedness nor coverage is therefore claimed conditional on the observed fallback event.

There are two prespecified possible delivered designs B/C. The analysis allocates per-design error .025 = .05/2, with candidate-bank multiplicity inside that allocation where appropriate. A union over design failures supplies at least95% unconditional coverage for the interval selected by the runtime rule over the original random partition, without a runtime/correctness independence assumption. A fixed-design audit interval has nominal97.5% coverage; the delivered guarantee after design choice is at least95% unconditional. Do not call it a95% interval conditional on the runtime trigger or a guarantee conditional on every observed reservoir after trigger selection.

This allocation applies separately to each exact selected-audit/gap endpoint, paired contrast endpoint, and simultaneous-bank/mixture endpoint. It does not provide a joint95% guarantee over all distinct scientific endpoints. Exact bank/paired multiplicity remains analysis-owned and must come from exported interval metadata. Naive/binomial comparators retain their labels; they gain no exact finite-design guarantee. Known-cache iid calibration remains at its original95% settings conditional on the final768-row empirical distribution. Bootstrap sensitivity remains approximate. Point gaps/audit means describe the observed run with the protected uncertainty; do not infer unbiasedness conditional on fallback.

Presentation and paper must label per-design nominal level and runtime-selected guarantee distinctly and carry design_count=2/per_design_alpha=.025 into provenance. The original4.236pp normal95% planning half-width is historical precision guidance, not the width of these more conservative reported intervals. No extra inference, new sample, scope change or computation hold follows this necessary validity correction. Experiment retains responsibility for derivation, implementation and verification; story records its inferential scope.

## Original Tier B clearance retained as history

The pre-outcome Tier B freeze was K8/search512/audit1024=12288 planned answers in two sequential6144-response shards. Independent feasibility-v2 at `2326610db841cb56390843f205262a72ea7836ef` cleared that launch using a representative100-answer validation pilot: mean5.9543s/response, p958.9022s, max16.5937s, peak3372800KiB=3.2166GiB. The length-adjusted6.9115s planning mean yielded23.5914h nominal generation,47.1828h at2x, plus48h downstream and2h overhead=97.1828h against166.4748h then remaining. Those were forecasts, not main measurements. Tier A at the selected1.5B model was not cleared; no infeasibility claim was made about every smaller model. Earlier512/1536 and1.5x/24h drafts remain superseded history.

Tier B's target was the11520-item complement of all512 search items, with1024 audit questions and1536-row cache calibration. Those counts and its clearance are not the current primary analysis. The pilot's15 malformed outputs,7 length endings and one9-token usage record did not authorize main-outcome tuning. The fallback preserves that restriction.

## Delivery and ownership

Story owns the plan/targets/division, experiment owns analysis/method validity and provenance, figtab owns real figures/tables/captions, paper owns final exposition and reproduction integration, venue owns format rules, and independent review owns final acceptance. Existing CODEOWNERS needs no change. This revision is delivered by a study-only PR to paper; its integration does not hold unblinding after experiment records the fallback manifest. All required final real evidence and the full reviewed report remain mandatory.
