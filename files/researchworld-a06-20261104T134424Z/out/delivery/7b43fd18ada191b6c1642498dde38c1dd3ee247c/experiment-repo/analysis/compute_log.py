"""Compute log. usage: ht-resource status local-compute | python3 compute_log.py MATRIX.npz OUT.json
Job times are 'ran' seconds as measured by the resource (world running time; CPU rate per job in cpu_rate)."""
import sys, json, platform, numpy as np
import scipy, pandas, sklearn, torch, transformers
st = json.load(sys.stdin); d = np.load(sys.argv[1])
jobs = [dict(note=t["note"], ref=t["ref"], state=t["state"], ran_s=t["ran"], cpu_rate=t.get("cpu_rate"), cpus_per_job=2, memory_mb=t.get("memory_mb")) for t in st["tracked"] + st.get("ended", [])]
# the resource lists only its last 10 ended jobs: keep earlier records of the same file for jobs that dropped off; for a job recorded
# while still running, ran_s is the last value observed before it ended (a lower bound on its final running time)
import os
if os.path.exists(sys.argv[2]):
    seen = {j["ref"] for j in jobs}
    for j in json.load(open(sys.argv[2]))["all_jobs"]:
        if j["ref"] not in seen:
            j = dict(j); j["record"] = "carried over from the previous compute_log.json" + ("; last value observed while running (lower bound)" if j["state"] == "running" else ""); jobs.append(j)
score = [j for j in jobs if j["note"].startswith("pool cfg")]
Y = d["Y"]
log = dict(
  python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, pandas=pandas.__version__, sklearn=sklearn.__version__, torch=torch.__version__, transformers=transformers.__version__,
  model="Qwen/Qwen2.5-0.5B-Instruct (fp32, CPU)", mmlu_pro_revision="b189ec765aa7ed75c8acfea42df31fdae71f97be",
  seeds=dict(config_demo_sets=12345, question_subset=2024, synthetic_plan_grid="100+cell index", synthetic_pool=7, replay_real=5, hybrid_study=11, ranking_study=21),
  matrix=dict(configs_complete=int(Y.shape[0]), config_indices=d["cfg_idx"].tolist(), items=int(Y.shape[1]), forward_passes_scored=int(Y.shape[0] * Y.shape[1]),
              cells_planned=60 * 2000, acc_min=float(Y.mean(1).min()), acc_max=float(Y.mean(1).max())),
  scoring_jobs=dict(n_jobs=len(score), total_ran_cpu_hours_upper_bound=sum(j["ran_s"] for j in score) * 2 / 3600, jobs=score),
  all_jobs=jobs,
  note="cpu-hours upper bound = ran seconds x 2 CPUs per job; the host was shared (containers_per_cpu 3-4), so effective CPU use was lower. Scoring forward passes include partially finished configurations beyond 'forward_passes_scored' (not counted).")
if len(sys.argv) > 3:   # OUTDIR of the scoring jobs: wall-clock of each chunk (final elapsed line of its log, which includes time the container was frozen) and the time its last file was written
    import glob, re, datetime
    wc = {}
    for f in sorted(glob.glob(sys.argv[3] + "/pool_*.log")):
        txt = open(f, errors="ignore").read().replace("\r", "\n"); el = re.findall(r"elapsed (\d+)s", txt); dn = re.findall(r"^done ([0-9.]+)", txt, re.M)
        wc[os.path.basename(f)[:-4]] = dict(last_progress_elapsed_s=int(el[-1]) if el else None, done_elapsed_s=float(dn[-1]) if dn else None,
                                          npy_written_utc=datetime.datetime.fromtimestamp(os.path.getmtime(f[:-4] + ".npy"), datetime.timezone.utc).isoformat(timespec="seconds"))
    log["scoring_wall_clock"] = dict(note="all ten scoring jobs were started 2026-11-04 14:17-14:19 UTC (job 48:54 was resumed after an out-of-memory kill); elapsed values are wall-clock seconds in the job and include time the container was frozen, so they exceed the world running time `ran_s` recorded by the resource (the final ran_s of the finished scoring jobs fell outside the resource's list of ended jobs; the values in scoring_jobs are the last ones observed while the jobs ran, i.e. lower bounds)", chunks=wc)
json.dump(log, open(sys.argv[2], "w"), indent=1)
