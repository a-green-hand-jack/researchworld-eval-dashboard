"""Write results/MANIFEST.md and results/MANIFEST.json: SHA-256, size, rows and the one-line convention of every result file, the processed input
data, and the seeds / bootstrap sizes used. Usage: python3 src/manifest.py  (run after the experiments and src/analyze.py)"""
import hashlib, json, pathlib, subprocess, re
import pandas as pd
root = pathlib.Path(__file__).resolve().parents[1]; R = root / "results"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
VOLATILE = {"ollb_powmeans_weighted.csv": ["cpu_s"], "censoring_and_cpu.csv": ["cpu_s"]}
sha_nv = lambda p, cols: hashlib.sha256(pd.read_csv(p).drop(columns=cols).to_csv(index=False).encode()).hexdigest()
CORE = ("One row per target x cap x rule; L1 = total points raised, K = tasks touched, Linf = largest single-task jump (minimised separately); "
        "INF = proven infeasible under the cap (feasible=0), NaN = solver time-out (censored=1, *_lb/*_ub bounds); eps=1e-3 margin unless the file says otherwise; "
        "rank_mean = rank of the target under the plain mean (1 = best).")
CONV = [
 (r"ollb_score_(.*)\.csv", "OLLB (4496 models, 6 tasks, normalised scores), all targets, score rules trimmed1/mean/geomean/harmonic/median/min, cap=\\1. " + CORE),
 (r"ollb_ordinal_(borda|condorcet)_(.*)\.csv", "OLLB, ordinal rule \\1, cap=\\2, rank-stratified target sample (ranks 2-21 + 150 log-uniform in rank, seed 0; 136 targets); population rates need stratum weights (analysis/pooled_feasibility.csv). " + CORE),
 (r"ollb_plurality_sample\.csv", "OLLB, plurality, 8 caps, same rank-stratified sample as the other ordinal rules. " + CORE),
 (r"ollb_plurality_top500\.csv", "OLLB, plurality, 4 caps, the 500 best models as targets. " + CORE),
 (r"ollb_powmeans_weighted\.csv", "OLLB, all targets: p-mean continuum (pow-5, -1 harmonic, 0 geomean, 1 mean, min) and weighted means (Dirichlet(1) weights wdir0-19 with seed 1000+k, inverse-std weights). NOT IN GIT (131 MB): release asset ollb_powmeans_weighted.csv.gz of experiment-repo release results-large-v1; sha256 is of the uncompressed CSV. " + CORE),
 (r"(ollb_raw|ollb_nomerge|ollb_top500)_variants\.csv", "Data-slice sensitivity (raw=lm-eval raw accuracies; nomerge=merged models removed; top500=best 500 only), ceil and gain10, sample of 60 targets seed 0. " + CORE),
 (r"ollb_(eps0\.1|notie)\.csv", "Tie/eps sensitivity on OLLB gain10, Borda & plurality, rank sample: eps0.1 = margin 0.1 point; notie = ties count as loss. " + CORE),
 (r"ollb_(noise|taskboot)_gain10\.csv", "OLLB robustness: per-replicate rows (see run_robust.py header), cap gain10, seed 0, R=100 replicates.  noise = rankings recomputed from evaluation-noise-perturbed scores; taskboot = task-bootstrap."),
 (r"ollb_capcomp_score_(.*)\.csv", "OLLB, all targets, rules mean/median/min, cap=\\1 (cap-composition runs for request #6.1: emp95_nochat / emp95_nochatname / emp95_chat calibrate the empirical gain cap on subsets of the 540 declared pairs, empfrac95[_nochat] = 95th percentile of the share of remaining headroom closed, head0.25 = a quarter of the remaining headroom; src/mti/data.py make_cap). " + CORE),
 (r"ollb_capcomp_plurality_(.*)\.csv", "OLLB, plurality, cap=\\1 (see ollb_capcomp_score), same rank-stratified target sample as the other ordinal rules. " + CORE),
 (r"ollb_dup_(first|latest|worst)\.csv", "OLLB duplicate-name rule `\\1` (data/processed/ollb6_dup_\\1.csv.gz, src/build_dup_variants.py), all targets, mean/median/min at ceil and emp95 (request #6.3a). " + CORE),
 (r"helm_main\.csv", "HELM MMLU v1.13.0 (57 subjects, all complete models), all targets; caps ceil,front0,front2,gain5,gain10,gain20; rules mean,geomean,harmonic,pow-5,median,min,borda,condorcet,plurality. " + CORE),
 (r"helm_trimmed\.csv", "HELM trimmed mean (t=1) via exact MILP, all caps. " + CORE),
 (r"helm_eps0\.1\.csv|helm_notie\.csv", "HELM tie/eps sensitivity (eps=0.1 or ties as loss). " + CORE),
 (r"helm_powmeans_weighted\.csv", "HELM p-mean continuum and weighted means. " + CORE),
 (r"helm_(noise|taskboot)_gain10\.csv", "HELM robustness replicates, cap gain10, seed 0, R=100."),
 (r"helm_tasksub_ceil\.csv", "HELM task-subset scaling: random subsets of n subjects (R=50 draws per n, seed 0), cap ceil."),
 (r"theory_pairs\.csv", "Closed-form prediction (pred_*) vs solver output (solver_*) for mean, min and (HELM) median, per instance; abs_err_L1, feasible_agrees, K_agrees."),
]
AN = {
 "summary_groups": "per dataset x design x cap x rule x rank group (analyze.py): n targets, censored, infeasible count/rate (Wilson CI), median L1/K/Linf over all targets (infeasible = +inf) and over feasible targets only, with B=1000 percentile bootstrap CIs over targets.",
 "pooled_feasibility": "feasible share per dataset x design x cap x rule pooled over rank groups, Wilson CI; weighted=1 = stratum-weighted estimate for the sampled ordinal rules.",
 "rank_dependence": "C4: Spearman rho and log10-rank slope of L1 and K versus the target's mean rank, feasible targets only, bootstrap CI for the slope.",
 "rule_comparison_vs_mean": "C2: paired per-target log10 ratio of each rule's L1 to the mean's (both feasible), bootstrap CI, paired Wilcoxon p with Holm correction.",
 "ordering_stability": "C2: Kendall tau between rule orderings (by median L1) in two dataset|cap cells within a rank group.",
 "targeted_vs_uniform": "C5: L1 / (n x Linf) per rule (targeted cost over the cost of a uniform improvement of the largest single jump), median and bootstrap CI.",
 "censoring_and_cpu": "solver time-outs (censored count/share) and measured CPU seconds per dataset x design x cap x rule (HiGHS CPU, summed over targets).",
 "weighted_means": "20 Dirichlet(1) weight draws (seed 1000+k): min/median/max over draws of the group median L1/K and infeasible share, plus inverse-std weights (winvstd_*).",
 "robust_noise_taskboot_targets": "C6: per target (10 best models after the first) x rule: median and 2.5-97.5% replicate interval of L1/K under evaluation-noise (noise) or task-bootstrap resampling (R=100, seed 0); p_already_first, p_infeasible.",
 "robust_noise_taskboot_rule_order": "C6: mean rank of each rule (by median L1) over replicate draws with its 2.5-97.5% interval.",
 "robust_tasksub": "C6: HELM task-subset scaling: random subsets of n subjects (R=50, seed 0) by n x rule x target rank in subset: L1/K medians with replicate intervals, p_infeasible, gap_own_med.",
 "robust_tasksub_slopes": "C6: log-log slope of median L1 versus n per rule and target rank in the subset.",
 "robust_variants": "C6: data-slice sensitivity (raw / nomerge / top500) per cap x rule: feasible share, median L1/K over feasible targets, bootstrap CI.",
 "robust_variants_ordering": "C6: Kendall tau of each slice's rule ordering against the main OLLB ordering.",
 "robust_eps_ties": "C6: paired eps=0.1 and ties-as-loss runs versus the main eps=1e-3 runs: changed feasibility, changed K, L1 ratio with bootstrap CI.",
}
AN.update({
 "cap_composition_pairs": "request #6.1a: per subset of the declared (fine-tune, base) pairs (all, chat, nochat, domain, nochatname) and OLLB task: pair count, emp95, emp99, mean/median gain, 95th percentile of the share of headroom closed, share of pairs gaining more than 10 points.",
 "cap_composition_types": "request #6.1a: the 540 pairs by Type of the fine-tune and Type of its base model, and counts by chat-like model name.",
 "cap_composition_feasible": "request #6.1b/c: feasible share (all targets; plurality stratum-weighted) and median L1 among feasible targets by rule x cap x rank group, for ceil / emp95 / emp99 and the cap-composition caps.",
 "rank_dependence_fits": "request #6.2: power / linear / log fits of L1 against rank at cap ceil per dataset x design x rule, on group medians and on target-level values: coefficients, rmse_log10, rmse_L1, R2 on the L1 scale, preferred form by each criterion.",
 "rank_monotonicity": "request #6.2: are the group medians of L1 at ceil monotone in rank? Group medians, decreases, and whether each decrease lies within the bootstrap intervals.",
 "duplicate_rule_sensitivity": "request #6.3a: OLLB group medians of L1 and infeasible share under duplicate-name rules best (delivered) / first / latest / worst, with change against best.",
 "duplicate_rule_leaders": "request #6.3a: leader and runner-up under mean / median / min for each duplicate-name rule.",
 "ollb_item_counts_check": "request #6.3b: items per OLLB task summed from n-samples of one results JSON for each of 60 randomly sampled models (HF results snapshot aa81ecc3; network needed to regenerate).",
 "helm_subject_sizes": "request #6.4a: items per HELM MMLU subject (checked identical across models), item size in points and binomial SE.",
 "score_cap_defence": "request #6.4b: share of targets that can reach first when every model's task scores are clipped (at leader + h or at a per-task percentile), for mean/median/min on OLLB and HELM, with ceil or gain10 attack cap.",
 "score_cap_defence_groups": "request #6.4b: the same by rank group.",
})
CONV.append((r"theory_checks\.txt", "PASS/FAIL summary of the closed-form versus solver checks (src/theory_checks.py)."))
CONV.append((r"instances/(.*)\.csv\.gz", "gzip -9 (mtime 0) copy of results/\\1.csv, made by src/pack_instances.py pack; `make unpack` restores the CSV, whose own SHA-256 is listed above."))
CONV.append((r"analysis/(.*)\.csv", None))
def conv(rel):
    for pat, c in CONV:
        m = re.fullmatch(pat, rel)
        if m and c is None: return AN.get(m.group(1), "derived by src/analyze.py / src/analyze_robust.py")
        if m: return re.sub(r"\\(\d)", lambda k: m.group(int(k.group(1))), c) if "\\" in c else c
    return ""
files = sorted(p for p in list(R.glob("*.csv")) + list(R.glob("analysis/*.csv")) + list(R.glob("*.txt")) + list(R.glob("instances/*.csv.gz")))
data = sorted((root / "data" / "processed").glob("*"))
ent = []
for p in files + data:
    rel = str(p.relative_to(root if p in data else R)); e = dict(file=("" if p in data else "results/") + rel, sha256=sha(p), bytes=p.stat().st_size)
    if p.name in VOLATILE:   # measured CPU seconds change from run to run; the rest of the file is deterministic
        e["volatile_columns"] = VOLATILE[p.name]; e["sha256_without_volatile"] = sha_nv(p, VOLATILE[p.name])
    if p.suffix == ".csv": e["rows"] = sum(1 for _ in open(p, "rb")) - 1
    e["convention"] = conv(rel) if p not in data else "processed input matrix/metadata built by src/build_data.py"
    ent.append(e)
hdr = dict(seeds="all drivers --seed 0 (rank sample, MC draws); weighted means seed 1000+k", bootstrap="B=1000 percentile bootstrap over targets, seed 0 (analyze.py --B 1000 --seed 0)")
json.dump(dict(header=hdr, files=ent), open(R / "MANIFEST.json", "w"), indent=1)
with open(R / "MANIFEST.md", "w") as f:
    f.write("# Result manifest\n\n" + "\n".join(f"- {k}: {v}" for k, v in hdr.items()) + "\n\n| file | rows | sha256 | convention |\n|---|---|---|---|\n")
    for e in ent: f.write(f"| {e['file']} | {e.get('rows','')} | `{e['sha256']}`{(' (without column ' + ', '.join(e['volatile_columns']) + ': `' + e['sha256_without_volatile'] + '`)') if 'volatile_columns' in e else ''} | {e['convention']} |\n")
print(len(ent), "files")
