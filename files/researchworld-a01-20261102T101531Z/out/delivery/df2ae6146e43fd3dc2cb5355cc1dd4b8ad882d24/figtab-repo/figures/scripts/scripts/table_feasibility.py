"""Tables (C4, appendix): share feasible [Wilson 95% CI] by rank-under-the-mean bin and rule, per board, for one gain model (--gain-model).
Intervals are clipped to [0, 1]. One file per board: feasibility_<gain>_<board>.tex."""
from common import *

RULES = ["mean", "geomean", "median", "min", "trimmed_mean", "borda", "copeland", "condorcet_winner", "plurality"]
BINS = ["1-2", "3-10", "11-100", "rest"]


def main():
    def extra(p):
        p.add_argument("--gain-model", default="G2_0.5")
    a = args(__doc__, extra)
    df = read(a, "feasibility.csv")
    df = df[(df.gain_model == a.gain_model) & (df.rank_basis == "mean") & (df.field == "all") & (df.normalisation == "normalised")
            & df.rule.isin(RULES) & (df.rule_param.isna() | (df.rule_param == 0.2) | (df.rule == "geomean"))]
    for lb, gr, pop, title in BOARDS:
        d = df[(df.leaderboard == lb) & (df.granularity == gr) & (df.population == pop)]
        bins = [b for b in BINS if b in set(d.rank_bin)]
        rows = []
        for r in RULES:
            row = [RULE_LABEL[r]]
            for b in bins:
                x = d[(d.rule == r) & (d.rank_bin == b)]
                row.append(fmt_ci(x.frac_feasible.iloc[0], max(0, x.ci_lo.iloc[0]), min(1, x.ci_hi.iloc[0]), 2) if len(x) else "--")
            rows.append(row)
        ns = [str(int(d[d.rank_bin == b].n_targets.iloc[0])) for b in bins]
        write_table(a, f"feasibility_{a.gain_model}_{lb}_{gr}", rows, "l" + "l" * len(bins), ["Rule"] + [f"{b} ($n$={n})" for b, n in zip(bins, ns)],
                    f"{title.replace(chr(10), ' ')}; gain {a.gain_model}; share feasible [Wilson 95% CI].")


if __name__ == "__main__":
    main()
