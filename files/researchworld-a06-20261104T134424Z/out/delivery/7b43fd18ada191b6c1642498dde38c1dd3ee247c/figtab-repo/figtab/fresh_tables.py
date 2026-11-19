"""Equal-item-budget comparison of reporting protocols (external review #6), as LaTeX fragments (tabular + one-line note), from results/fresh_protocol_*.csv.
Each row is scored against its OWN truth mu_ship: the true accuracy of the configuration that protocol shipped (the search saw different data).
t7_fresh_protocol: synthetic reference cell (tau .01, K 16, rho .5, m .3, best-of-K), total item budgets 200 and 400.
t8_fresh_real: real-LLM replay at the largest K in fresh_protocol_real.csv, budget 200 (disjoint truth). K is read from the file."""
from tables import pm, write, tabular, LAB
from style import *

INS = ["naive", "boot_oob", "boot_opt", "simul", "crossfit", "hybrid", "split"]
LAB7 = {"naive": "naive", "boot_oob": "bootstrap out-of-bag", "boot_opt": "bootstrap optimism", "simul": "simultaneous bound", "crossfit": "5-fold cross-fit", "hybrid": "hybrid (proj.+cond.)", "split": "held-out split 50/50"}
HEAD = "protocol & items & true acc. (\\%) & bias (pp) & RMSE (pp) & coverage & width (pp)"

def row(lab, r):
    return " & ".join([lab, str(int(r["items"])), f"{100 * r.mu_ship:.2f}", pm(r.bias, r.bias_se), f"{100 * r.rmse:.2f}", f"${r.cover:.3f} \\pm {r.cover_se:.3f}$", f"{100 * r.width:.1f}"])

def block(g, budget, pairs):
    g = g[g["items"] == budget]; rows = []
    for e in INS:
        rows.append(row(LAB7[e], g[(g.protocol == "insample") & (g.est_name == e)].iloc[0]))
    for nt in pairs:
        r = g[(g.protocol == "fresh") & (g.n_tune == nt)].iloc[0]
        rows.append(row(f"fresh set {int(r.n_tune)}/{int(r.m_fresh)}", r))
    return rows

def main():
    s = pd.read_csv(os.path.join(RESULTS, "fresh_protocol_summary.csv"))
    s = s[(s.tau == 0.01) & (s.K == 16) & (s.rho == 0.5) & (s.m == 0.3)]
    rows = block(s, 200, [50, 100]) + ["\\midrule"] + block(s, 400, [100, 200])
    reps = int(s.reps.min())
    note = (f"Reference cell ($\\tau$=.01, $K$=16, $\\rho$=.5, mean accuracy .3, best-of-$K$), {reps} repetitions; the budget (items) is the total number of questions consumed: "
            "methods above the fresh-set rows tune and report on the same items (in-sample), a fresh-set row ``$n_{\\rm tune}/m$'' tunes on $n_{\\rm tune}$ items and reports the winner on $m$ new items (Wilson interval). "
            "Each row is scored against its own truth, the true accuracy of the configuration that protocol shipped (third column; it differs across protocols because the search saw different data). "
            "Bias and coverage are mean $\\pm$ Monte Carlo s.e.; coverage is of the nominal 95\\% interval; the held-out split tunes on one half of the items and reports on the other.")
    write("t7_fresh_protocol", tabular("lrrrrrr", rows, HEAD), note)

    r = pd.read_csv(os.path.join(RESULTS, "fresh_protocol_real.csv")); K = int(r.K.max()); r = r[r.K == K]
    rows = block(r, 200, [50, 100])
    note = (f"Real-LLM replay on MMLU-Pro (Qwen2.5-0.5B-Instruct), best-of-$K$ with $K$={K} configurations (largest $K$ in the file), total budget 200 questions, {int(r.reps.min())} repetitions. "
            "Questions are drawn without replacement from the 2000-question pool; each row is scored against the accuracy of the configuration it shipped on the pool questions that protocol did not use (third column, true accuracy of the shipped configuration). "
            "Columns as in the synthetic table.")
    write("t8_fresh_real", tabular("lrrrrrr", rows, HEAD), note)

if __name__ == "__main__":
    main()
