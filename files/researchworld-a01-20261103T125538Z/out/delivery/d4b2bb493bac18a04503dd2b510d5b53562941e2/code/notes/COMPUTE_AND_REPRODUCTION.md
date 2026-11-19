# Compute configuration and full-reproduction estimate

This note answers paper-repo's manuscript/checklist request (experiment-repo#3). Configuration and timing evidence are separate from planning estimates. No full experiment was repeated for this request.

## Allocation, environment and memory

The analysis worker and each tracked local-compute job were limited to **2 logical CPUs and 4 GiB memory, with no GPU**. These are ceilings on a shared host, not exclusive reservations. The current worker probe confirms CPU quota `200000 100000` (two CPUs), affinity count2, and cgroup memory limit4,294,967,296bytes. Its currently visible host CPU model is Intel Xeon Gold6230 at2.10GHz; per-job CPU model strings were not separately logged during the historical runs. The probe's UTC and exact fields are in `results/compute_configuration.json`. Do not describe the host's total memory/CPU count as the allocation to these jobs.

All tracked numerical jobs set `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1`; no separate HiGHS thread option was set. Python3.11.2, NumPy2.4.6, SciPy1.17.1, pandas3.0.6 and PyArrow26.0.0 are recorded in `results/environment.json` and pinned in `requirements.txt`. The two leaderboard bundles were independent parallel jobs; subset/random diagnostics were separate jobs. No model training or inference was performed.

**Peak memory was not measured.** No per-job peak RSS or cgroup peak-memory series was recorded. All jobs succeeded within their4GiB limit, but the limit is not a peak-usage measurement and must not be reported as such. CPU-hours consumed and process-level utilization were likewise not instrumented; wall-clock timing and allocation bounds are what this study can report. Reading the present worker's cumulative peak would not recover the past jobs' peaks, so no such substitution is made.

## Measured components

| Completed component | Recorded wall time | Scope |
|---|---:|---|
| HELM12-target/four-rule pilot |0.203s|Inner script; excludes resource/interpreter startup.|
| Open LLM12-target/four-rule pilot |0.106s|Inner script; excludes resource/interpreter startup.|
| HELM full primary +11 additional main configurations |12.82s|Bundle, including child interpreter startup.|
| Open LLM full12 configurations +4 alternate-matrix primary runs |359.13s|Bundle, including child interpreter startup.|
|200 paired45-of-57 HELM subject-subset draws |149.30s|Measured computation loop.|
|HELM random task-order baseline |1.04s|Inner script,2,000 orders per target.|
|Open LLM random task-order baseline |14.03s|Inner script, exact subset enumeration.|
|Relocated independent optimizer test suite |2.635s|Recorded unittest execution in the delivered layout.|

Pilot rows, per-target timings and bundle child runtimes are under `results/`; resource start/end records and retained completion lines are in `results/resource_runs.json`. Resource lifecycle time includes startup/teardown and is different from the inner-script and bundle times above. The five main bundle/subset/random timings sum to536.32s, about8.94min **as a sum of component measurements**, not as a measured serial end-to-end reproduction. Adding the two pilots and the example relocated test execution gives about8.99min. Concurrent runs and shared-host contention mean this is not the elapsed duration of the original research session.

Acquisition, preparation/checksums, item-weighted-mean sensitivity, normalization audit, summary generation, output validation, copying/hashing and package installation completed successfully, but isolated component timings for them were not recorded. The raw acquisition manifest lists122 files totaling37,800,558bytes (about36.05MiB); this is a measured input size, not a download-time estimate. No peak-memory or untimed-step number is invented.

## Labeled planning estimate for a new reproduction

Follow `README.md` after `cd code` in the paper delivery. On a comparable2-CPU/4GiB worker:

- **Dependencies already installed and public files reachable:** allow **20minutes** for the full scientific reproduction commands, including cold score downloads, parsing/audits, tests, all exact attacks, baseline/subset/weight checks and final summaries/validation. This is a conservative planning estimate, not a measured end-to-end runtime. It allows roughly twice the known summed compute time plus several minutes for the untimed small steps and network/startup overhead.
- **Completely new environment:** allow **30–60minutes** including installation of the pinned CPU Python dependencies and cold HTTPS downloads. Package resolution, network service latency and shared-host contention can exceed that allowance; it is not a guaranteed bound.
- The optional pilots can be regenerated with the commands used in `results/resource_runs.json`/the run-sizing note, but are not required to regenerate any reported empirical result. If rerunning them, retain the same12-target pilot setting and both boards.

These estimates cover the analysis package only. Publication figure rendering and LaTeX/PDF build are separate components owned and timed by presentation/report. The package contains no data-generation or model-training expense hidden outside these commands. Report measured component times, allocated resources, missing peak memory and the planning estimate with their respective labels.
