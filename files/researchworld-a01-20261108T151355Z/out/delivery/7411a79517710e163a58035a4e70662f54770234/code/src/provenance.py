"""results/MANIFEST.csv: every result/summary file with rows, SHA-256, producing job (run_all.sh JOB) and the input files it was computed from.
results/summary/runtimes.csv: per-job wall seconds and scheduler-measured CPU seconds, from a saved `ht-resource status local-compute` JSON (arg 1, optional).
Usage: python3 src/provenance.py [status.json]"""
import sys, json, hashlib, pathlib, re, pandas as pd
R = pathlib.Path(__file__).resolve().parents[1]; res = R / "results"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
MAN = json.load(open(R / "data/processed/manifest.json"))
inputs = {"helm": ["data/processed/helm_mmlu57.csv"], "ollb": ["data/processed/ollb6.csv"]}
JOB = [(r"ollb_ord100_(.+)", r"ollb_ord100_\1 (run_extra.sh)"), (r"ollb_hstar_ord100_(.+)", r"ollb_hstar100_\1 (run_extra.sh)"), (r"(helm|ollb)_eps(1e0)", r"\1_eps1 (run_extra.sh)"),
       (r"(helm|ollb)_eps2e0", r"\1_eps2 (run_extra2.sh)"), (r"(helm|ollb)_eps8e0", r"\1_eps8 (run_extra2.sh)"), (r"(helm|ollb)_emp_restricted", r"\1_emp_restricted (run_extra2.sh)"),
       (r"helm_tasksub_gain10_eps(.+)", r"helm_tasksub_eps\1 (run_extra.sh)"), (r"convex_cost", "convex_cost (run_extra2.sh)"),
       (r"(helm|ollb)_noise_gain10_t30", r"\1_noise30 (run_robust30.sh)"), (r"helm_taskboot_gain10_t30", "helm_taskboot30 (run_robust30.sh)"),
       (r"ollb_hstar_ord_(condorcet|plurality)", r"ollb_hstar_\1 (run_robust30.sh)"),
       (r"pairs_composition|emp_caps_restricted|base_model_metadata", "src/emp_pairs_composition.py"), (r"empirical_gains|emp_caps$", "src/emp_caps.py"), (r"sample_weights", "src/sample_weights.py"),
       (r"helm_main", "helm_main"), (r"ollb_score", "ollb_score"), (r"ollb_ord_(.+)", r"ollb_ord_\1"), (r"ollb_trim_(.+)", r"ollb_trim_\1"), (r"helm_trim", "helm_trim"),
       (r"ollb_nomerge", "ollb_nomerge"), (r"ollb_raw", "ollb_raw"), (r"ollb_top500", "ollb_top500"), (r"(helm|ollb)_noise", r"\1_noise"),
       (r"helm_taskboot", "helm_taskboot"), (r"helm_tasksub", "helm_tasksub"), (r"(helm|ollb)_flip", r"\1_flip"), (r"(helm|ollb)_spillover", r"\1_spill"),
       (r"(helm|ollb)_eps", r"\1_eps"), (r"(helm|ollb)_hstar(_ord)?", r"\1_hstar\2"), (r"theory_checks", "src/theory_checks.py (not in run_all.sh)")]
rows = []
for f in [x for x in sorted(res.glob("*.csv")) if x.stem != "MANIFEST"] + sorted((res / "summary").glob("*.csv")):
    stem = f.stem; SUMJOB = {"margin_robust": "src/margin_robust.py", "cluster_bootstrap_ollb": "src/cluster_bootstrap.py", "cluster_sizes_ollb": "src/cluster_bootstrap.py", "convex_cost": "src/convex_cost.py",
                             "c8_restricted_pairs": "src/emp_pairs_composition.py", "peak_memory": "src/peak_memory.py", "cpu_total": "src/provenance.py", "runtimes": "src/provenance.py"}
    job = SUMJOB.get(stem, "src/analyze.py") if f.parent.name == "summary" else next((re.sub(p + ".*", t, stem) for p, t in JOB if re.match(p, stem)), "?")
    ds = "helm" if stem.startswith("helm") else "ollb"
    if f.parent.name == "summary": ins = "results/*.csv (see src/analyze.py)"
    else: ins = ";".join(f"{i}={sha(R / i)[:16]}" for i in inputs[ds]) + (";data/processed/ollb_noise.json" if "noise" in stem else "")
    rows.append(dict(file=str(f.relative_to(R)), rows=len(pd.read_csv(f)), sha256=sha(f), job=job, inputs_sha256_prefix=ins))
pd.DataFrame(rows).to_csv(res / "MANIFEST.csv", index=False); print(len(rows), "files")
ROLE = sys.argv[2] if len(sys.argv) > 2 else ""      # optional: keep only the scheduler jobs of this role
if len(sys.argv) > 1:
    st = json.load(open(sys.argv[1])); jobs = {}
    for j in st.get("ended", []) + st.get("tracked", []): jobs[j["ref"]] = j
    out = [dict(job=j["note"], ref=j["ref"], state=j["state"], exit=str(j.get("output", ""))[:12], wall_s=round(j["ran"]) if "ran" in j else None, cpu_s=round(j["spend"]) if "spend" in j else None) for j in jobs.values() if not ROLE or j.get("role") == ROLE]
    sched = pd.DataFrame(out)
    logs = []   # wall seconds of the last "<cap> <rule> done Ns" line of each job log (covers jobs that have dropped out of the scheduler's recent list)
    for f in sorted((R / "logs").glob("*.log")):
        m = re.findall(r"done (\d+)s", f.read_text(errors="ignore")); logs.append(dict(job=f.stem, log_last_done_wall_s=int(m[-1]) if m else None))
    new = pd.DataFrame(logs).merge(sched, on="job", how="outer").set_index("job")
    rt = res / "summary/runtimes.csv"      # the scheduler lists only recent jobs: keep the rows of earlier snapshots, newer values win
    if rt.exists():
        old = pd.read_csv(rt).set_index("job"); old.loc[(old.state == "running") & ~old.index.isin(sched.job if len(sched) else []), "state"] = "ended after an earlier snapshot (final state not recorded)"
        new = new.combine_first(old)
    # jobs that ended between snapshots and are no longer in the scheduler's recent list: wall seconds of the job's own last progress line (as quoted in the scheduler's end notice), cpu not metered per job
    END_NOTICE = {"helm_noise30": ("job-ae2b2f50d0", 4715, "wall = last 'draw 90' line; the final draws ran after it"), "helm_taskboot30": ("job-84c0672ba8", 1923, "wall = last 'draw 90' line; the final draws ran after it"),
                  "ollb_hstar_cond": ("job-60b10b8c5f", 4716, "wall = 'condorcet done' line"), "ollb_hstar100_borda": ("job-bce135f965", 2106, "wall = 'borda done' line"),
                  "ollb_hstar100_condorcet": ("job-0d82d1e9da", 2073, "wall = 'condorcet done' line")}
    for k, (ref, w, note) in END_NOTICE.items():
        new.loc[k, ["ref", "state", "wall_s", "cpu_s"]] = [ref, "ended (" + note + ")", w, float("nan")]
    new.sort_index().reset_index().to_csv(rt, index=False); print(len(out), "scheduler jobs,", len(logs), "logs")
    # total CPU-seconds of every job the scheduler metered for this world (`used.spend` of `ht-resource status local-compute`; includes jobs whose per-job row is missing above)
    u = st.get("used", {}); pd.DataFrame([dict(total_cpu_s=round(u.get("spend", float("nan"))), total_cpu_h=round(u.get("spend", float("nan")) / 3600, 2), jobs_running_at_snapshot=u.get("tracked"),
                                               jobs_listed_with_wall_time=int(sched.wall_s.notna().sum()))]).to_csv(res / "summary/cpu_total.csv", index=False)
