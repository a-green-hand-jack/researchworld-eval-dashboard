"""Table (C1): solver vs closed form / brute force. Rows: instance type x board x rule family; columns: checks, matches, maximum absolute deviation.
`real`: mean-rule closed form and independent reference rule on every target; `small_exhaustive`: solver vs brute force on 400 random small instances per rule.
Failures are shown as match < checks, never dropped."""
from common import *


def main():
    a = args(__doc__)
    df = read(a, "verification.csv")
    rows = []
    for (it, lb), d in df.groupby(["instance_type", "leaderboard"], sort=False):
        if it == "real":
            n, k, dev = len(d), int(d.match.sum()), d.abs_diff.max()
            rules = "mean (closed form + reference rule)" if set(d.rule) == {"mean"} else ", ".join(sorted(set(d.rule)))
        else:
            n, k, dev = int(d.n_instances.sum()), int(d.n_match.sum()), d.max_excess.max()
            rules = f"{d.rule.nunique()} rules, brute force"
        rows.append([latex_escape(it), latex_escape(lb), latex_escape(rules), n, k, f"{dev:.2g}"])
    write_table(a, "verification", rows, "lllrrr", ["Instances", "Board", "Check", "Checks", "Match", "Max dev."],
                "Match = solver value equals reference value; real instances compare k_min and G_min.")


if __name__ == "__main__":
    main()
