# Schedule-only recovery feasibility — conditional assessment

2026-11-06. Assessed in response to idea-review-repo#4. **CPU and storage support completing the unchanged120 mandatory controls. The proposed schedule is conditionally feasible, with little serial slack; final schedule authorization requires the report and presentation owners' concrete12-hour integration readiness and a fresh launch-time resource check.** This assessment is usable immediately; it is not authorization to assume those missing answers. Story-repo owns the final schedule. Optional180k remains excluded.

## Inputs and scope

Re-read Research objective#1: one week includes experiments, paper and code; actual evidence, statistical uncertainty, failure conditions, complete conference-format PDF/LaTeX and reproduction remain required. The nominal48-hour writing reserve was a planning buffer, not a frozen objective requirement. Reducing it to12h can be legitimate when material work proceeds in parallel, but must be supported by actual remaining work, not assumed from compute affordability.

Read story-repo `cc533b2dbe25bf24d8ca7cc2cb550024ae1a9430`, `notes/proposed-schedule-recovery.md`, story-repo#10, and the requests paper-repo#15 / figtab-repo#7. Those two requests had no owner readiness answers at this check. Read newly accessible experiment-repo `8d03738bba4b43df94daa7dd6a8ba9e6640e8a79`: `results/resource-checkpoints/before-follow-on.json` and `code/scripts/monitor_resources.py`; also checked both anomaly-containing raw curves. The checkpoint is now pushed, despite the earlier request describing it as not yet accessible. The failed original time gate remains intact. No training, rebenchmarking or scientific reanalysis was performed by this position; primary scientific summaries do not decide this schedule.

## Arithmetic checked

`recovery-cost-audit.json` records an independent calculation from the204 checkpoint entries:60 main and24 frozen completed,120 controls unstarted, no other recorded statuses; actual production loop CPU20,583.014248682s and measured preproduction540.826764397s; remaining9.459425200CPU h. This verifies inventory arithmetic, not every raw run's scientific validity. The checkpoint calls CPU a recorded lower bound and excludes unmeasured tooling; do not report it as exact total project compute.

The apparent47.1s discrepancy is resolved directly by the monitor: it adds four7.850837637s interpreter startup allowances WITH the remaining50% reserve. Thus:

`(20583.014248682 + 540.826764397 + 1.5*(9.459425200*3600 + 4*7.850837637))/3600 = 20.069956144 CPU h`.

That leaves23.930043856h under the44 CPU-hour planning cap. The logical result archive is87,881,268 bytes, and remaining reserved outputs376,241,580 bytes, totaling464,122,848 bytes. Checkpoint workspace sizes are also reported, but shared host capacity and extra delivery/build copies still need monitoring. These resource margins are adequate for this attempt; they do not buy elapsed time lost to interruptions.

The original experiment deadline, November6 at12:39:10.373Z, is already missed. The proposed experiment cutoff, November8 at00:39:10.373Z, leaves12h until the unchanged report/analysis/figure target at12:39:10.373Z, then48h until the absolute November10 deadline. The week must never restart. A schedule amendment must preserve the failed old gate as history rather than edit it into a pass.

## Two distinct wall-time scenarios

The literal historical maximum wall/CPU factor is452.968283947, giving6433.156h of reserved serial remaining work. Preserve this scenario and its failed gate. It cannot support the requested schedule.

Raw adjacent-evaluation checks confirm very large gaps in only the two named completed runs:

| Run | Adjacent updates | Elapsed seconds | CPU seconds |
|---|---|---:|---:|
|frozen_w512_b06|17800 to17900|143235.0567|0.5923|
|frozen_w512_b07|22100 to22200|143234.8632|0.5028|

This establishes a separation between elapsed and CPU accounting. It does not establish the cause, prove a specific suspension mechanism, or guarantee no recurrence. Preserve timestamps and all elapsed-cost disclosures; do not rewrite either learning clock or timing fields. Scientific update-based outcomes and recorded CPU efficiency remain distinct from interrupted wall efficiency.

A prospective scenario using the maximum per-run factor of the other82 completed runs is reasonable for a monitored attempt: factor1.860141103 applied to remaining CPU, startup allowances and50% reserve gives **26.418137880 serial elapsed hours**. This is a conditional planning scenario, not a bound or statistically calibrated runtime interval. Exclusion is tied to the identified raw timing anomalies, not model outcomes. No twofold speedup is assumed.

At the audit time November6 at21:04:11.414Z,27.583h remained, leaving only1.165h margin. The serial scenario's latest launch is approximately **November6 at22:14:05Z**. This is derived from the current quote; it is not a new fixed deadline or permission to launch after prerequisites fail. Recalculate at actual authorization. If that time passes, this serial affordability argument no longer fits the proposed cutoff. A measured concurrent remaining-work/makespan quote might still fit, but must use actual lane allocation/rates, startup and contingency rather than dividing by two or assuming unavailable throughput.

## Required gates and monitoring

1. **Integration readiness before final schedule authorization.** Story-repo must obtain paper-repo#15 and figtab-repo#7 owner decisions describing actual remaining tasks, available primary inputs, concrete12h final-integration plan and any required change. The owners must be able to work on the completed primary material now: accessible actual analysis/curves, scope/limitations and correct P3 fit-gate interpretation; no placeholders or outcome claims from missing controls. Context/template/bibliography/checklist/build/manifests and generating scripts can progress independently. Without those concrete decisions, feasibility of the whole delivery is not established, even though training fits CPU/storage. Please supply the decisions to idea-review-repo#4 for the completed gate check.
2. **Launch-time fit.** Capture actual UTC and fresh resource/job availability; checkpoint currently has `resource_snapshot:null`. Recompute all remaining CPU/storage and elapsed forecasts, preserve both literal anomaly and explicit prospective scenarios. The selected defensible scenario must fit the proposed experiment cutoff with contingency. Retain at most two one-thread jobs and immutable scientific source/configs. A missed serial latest-start requires a new measured scheduling quote or revised decision, not implicit speedup. Document final story authorization and revised target separately from the failed old checkpoint.
3. **Monitor at the first follow-on completion wake and every scheduled completion wake thereafter.** Reconcile attempted/completed/failed counts, cumulative known CPU (including attempts/startup/tooling separately), actual archive/workspace and fresh rates for all remaining families/widths. Keep at least50% contingency on remaining quoted work; use slower observed rates if they exceed the current quote. For a prospective wall factor, record the selected population/rationale and retain any newly observed gaps separately. Do not mechanically replace the anomalous literal maximum or silently ignore new stalls. Preserve logs and source provenance.
4. **Explicit revise/stop-new-work gate.** If the full remaining mandatory work plus contingency cannot fit the experiment cutoff,44 CPU-hours, available storage or the owner's12h integration plan, stop launching additional configs pending explicit schedule/recovery decision. Preserve validated checkpoints and every unfinished requirement. At the experiment cutoff, any uncompleted controls are unfinished research, not censored completed runs or a valid final204-run result. Do not keep silently extending into the48h review reserve or restart the week. Exact checkpoint recovery may be used under the validated rules; a resource cutoff is never outcome-based seed selection.
5. **Final artifact gate.** By November8 at12:39:10.373Z the full actual registered evidence, figures/tables/manifests, code/reproduction and complete built report must be reviewable to retain the48h reserve as planned. The final period must accommodate independent review, fixes, build and reproduction, not be assumed to rescue unfinished routine assembly. If this target is threatened, raise a concrete gap immediately. The absolute November10 deadline and independent approval standard remain unchanged. Optional extension is excluded throughout.

These are planning conditions for finishing required work; they neither reduce scientific scope nor manufacture a negative result. Parallel preparation is necessary for the12h window and should proceed now under each owner's function. Owner readiness answers are missing material, not implied by silence; no waiting or duplicate benchmark is required from this position while those requests are pending.

## Judgement status

The resource and anomaly questions are answered with pushed, checked evidence. The remaining missing gate is the actual report/presentation schedule assessment and fresh launch-time fit. Keep request#4 and recovery commitment#5 open for those inputs; the final schedule remains unauthorised by this conditional assessment alone. An unchanged acceptable readiness answer and timely launch need a gate check, not another study redesign. No new external literature/prohibited material was accessed; this assessment is arithmetic and authorized internal-source review only.
