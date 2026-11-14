"""Table (baselines): smallest budget k at which at least half of the attackers rank first, per rule and strategy (from baselines_budget_needed.csv),
with the share of attackers that reach rank 1 within the evaluated budgets. inf = fewer than half reach it."""
from common import *


def main():
    a = args(__doc__)
    df = read(a, "baselines_budget_needed.csv")
    df = df[df.budget_type == "k"]
    rows = []
    for (lb, rule), d in df.groupby(["leaderboard", "rule"], sort=False):
        row = ["HELM" if lb == "helm_mmlu" else "OLB headline", latex_escape(rule)]
        for s in ["optimal", "greedy_headroom", "random"]:
            x = d[d.strategy == s]
            row.append("--" if len(x) == 0 else f"{x.median_budget_needed.iloc[0]:g} ({100 * x.frac_reached.iloc[0]:.0f}\\%)")
        rows.append(row)
    write_table(a, "baselines", rows, "llrrr", ["Board", "Rule", "Optimal", "Greedy", "Random"],
                "Median budget k needed (share of attackers that reach rank 1 within the evaluated budget), gain model G1; inf = median attacker does not reach rank 1.")


if __name__ == "__main__":
    main()
