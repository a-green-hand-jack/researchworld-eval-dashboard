"""Real-LLM tables as LaTeX fragments (booktabs tabulars; caption and \\begin{table} are the manuscript's), all generated from results/*.csv and
results/compute_log.json.  K is the largest K in real_summary.csv, so the tables follow the files as more configurations complete.
E6 -> t5_real_methods: nine reporting methods in the real setting (best-of-K, disjoint truth), n = 50 and 200.
E7 -> t6_setup_compute: setup and compute record of the real-LLM matrix."""
import json
from tables import pm, write, tabular, LAB
from style import *

ORDER9 = ["naive", "split", "crossfit", "boot_opt", "boot_oob", "boot_632", "simul", "cond", "hybrid"]
LAB9 = dict(LAB, hybrid="hybrid (proj.+cond.)")

# Interim: real_summary.csv predates the change of the hybrid point estimate (hybrid median) in analysis/lib.py, so bias and RMSE of these
# rows are not reproduced by the delivered code. Set to () when the K=21 real_summary.csv (written with the new code) replaces it.
STALE_POINT = ()

def t5(ns=(50, 200)):
    d = pd.read_csv(os.path.join(RESULTS, "real_summary.csv")); d = d[(d.truth_arm == "disjoint") & (d.proc == "argmax")]
    K = int(d.K.max()); rows = []
    for k, n in enumerate(n for n in ns if n in set(d.n)):
        if k: rows.append("\\midrule")
        g = d[(d.K == K) & (d.n == n)].set_index("est_name")
        for i, e in enumerate(ORDER9):
            r = g.loc[e]
            stale = e in STALE_POINT
            rows.append(" & ".join([str(n) if i == 0 else "", LAB9[e], "--" if stale else pm(r.bias, r.bias_se), "--" if stale else f"{100 * r.rmse:.2f}", f"${r.cover:.3f} \\pm {r.cover_se:.3f}$", f"{100 * r.width:.1f}"]))
    reps = int(d[d.K == K].reps.min())
    note = (f"Real-LLM replay on MMLU-Pro with Qwen2.5-0.5B-Instruct: best-of-$K$ over the $K$={K} configurations, tuning set of $n$ questions drawn without replacement from the 2000-question pool; "
            f"{reps} repetitions per row. Truth = accuracy of the selected configuration on the pool questions outside the tuning set (finite-pool truth). "
            "Bias and coverage are mean $\\pm$ Monte Carlo s.e.; coverage is of the nominal 95\\% interval."
            + (" Bias and RMSE of the conditional and hybrid rows were computed with an earlier point estimate and are not shown; they are regenerated with the K=21 replay." if STALE_POINT
               else " The bias and RMSE of the conditional method are dominated by the heavy tail of its estimate (reported as measured)."))
    write("t5_real_methods", tabular("rlrrrr", rows, "$n$ & method & bias (pp) & RMSE (pp) & coverage & width (pp)"), note)

def t6():
    j = json.load(open(os.path.join(RESULTS, "compute_log.json"))); m = j["matrix"]
    s = pd.read_csv(os.path.join(RESULTS, "matrix_spread.csv")).iloc[0]; jobs = j["scoring_jobs"]["jobs"]
    ch = j["scoring_wall_clock"]["chunks"]; res = ch["pool_48-54"]["done_elapsed_s"] / 3600
    full = [v["done_elapsed_s"] / 3600 for k, v in ch.items() if k != "pool_48-54"]
    jobs_txt = (f"{len(ch)} scoring jobs of 6 configurations each, all finished; wall-clock {min(full):.1f}--{max(full):.1f} h per job"
                f" ({res:.1f} h for the job resumed after an out-of-memory stop)")
    rep = [x for x in j.get("all_jobs", []) if x["note"].startswith(("real replay", "fresh-set protocols real")) and f"K={m['configs_complete']}" in x["note"]]
    rep_txt = "; ".join("%s %.0f min" % (x["note"].replace(" (v2 hybrid)", ""), x["ran_s"] / 60) for x in rep)
    cell = lambda a, b: f"{a} & {b}"
    rows = [
        cell("model", "Qwen2.5-0.5B-Instruct, fp32, CPU; option-letter log-probabilities"),
        cell("benchmark", f"MMLU-Pro test, revision \\texttt{{{j['mmlu_pro_revision'][:12]}}}, {m['items']} questions (seed {j['seeds']['question_subset']})"),
        cell("configurations", f"{m['configs_complete']} complete of 60 planned (instruction wording $\\times$ demo set $\\times$ layout)"),
        cell("forward passes", f"{m['forward_passes_scored']:,} scored of {m['cells_planned']:,} planned"),
        cell("accuracy across configs", f"mean {100 * s.acc_mean:.1f}\\%, range {100 * s.min_acc:.1f}--{100 * s.max_acc:.1f}\\%, sd {100 * s.sd_acc_across_configs:.2f} pp"),
        cell("item correlation", f"mean pairwise correlation of item correctness across configs {s.mean_pairwise_item_corr:.2f}"),
        cell("scoring jobs", jobs_txt),
        cell("replay jobs", rep_txt),
        cell("seeds", f"configs/demos {j['seeds']['config_demo_sets']}, questions {j['seeds']['question_subset']}, replay {j['seeds']['replay_real']}"),
        cell("packages", f"Python {j['python']}, numpy {j['numpy']}, scipy {j['scipy']}, pandas {j['pandas']}, scikit-learn {j['sklearn']}, torch {j['torch']}, transformers {j['transformers']}"),
    ]
    note = (f"Setup and compute record of the real-LLM matrix, from the compute log and the matrix summary; all {m['configs_complete']} planned configurations are scored. "
            "Scoring wall-clock is elapsed time in the job on a shared host and includes time the container was frozen, so it exceeds the CPU time used. "
            "Replay times are the logged running times.")
    write("t6_setup_compute", tabular("lp{0.64\\linewidth}", rows, "item & value"), note)

if __name__ == "__main__":
    t5(); t6()
