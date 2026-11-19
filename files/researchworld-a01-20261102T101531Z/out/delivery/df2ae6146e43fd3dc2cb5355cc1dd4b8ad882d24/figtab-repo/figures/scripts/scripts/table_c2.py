"""Tables (C2/C3, appendix): paired median difference k_min(rule) - k_min(mean) [95% bootstrap CI] (n pairs), per board, rows = contrast, columns = gain model.
Positive = the rule needs more tasks than the mean. Bold = CI strictly above 0 (C2 supported in that cell). One file per board: c2_<board>.tex."""
from common import *

GAINS = ["G1", "G1_add10", "G1_add20", "G2_0.25", "G2_0.5", "ceil"]


def main():
    a = args(__doc__)
    df = read(a, "paired_stats.csv")
    df = df[(df.metric == "k_min") & (df.estimate_type == "median_diff(other-mean)") & (df.rank_stratum == "all_attackers") & (df.cost == "linear")
            & (df.normalisation == "normalised") & (df.field == "all")]
    for lb, gr, pop, title in BOARDS:
        d = df[(df.leaderboard == lb) & (df.granularity == gr) & (df.population == pop)]
        rows = []
        for c in d.contrast.drop_duplicates():
            row = [latex_escape(c.replace("mean vs ", "").replace(":", " "))]
            for g in GAINS:
                x = d[(d.contrast == c) & (d.gain_model == g)]
                if len(x) == 0 or pd.isna(x.estimate.iloc[0]):
                    row.append("--"); continue
                x = x.iloc[0]
                s = f"{x.estimate:+.1f} [{x.ci_lo:+.1f}, {x.ci_hi:+.1f}] ({int(x.n_pairs)})".replace("-", "$-$")
                row.append(f"\\textbf{{{s}}}" if x.ci_lo > 0 else s)
            rows.append(row)
        write_table(a, f"c2_{lb}_{gr}", rows, "l" + "l" * len(GAINS), ["Rule"] + [latex_escape(g) for g in GAINS],
                    f"{title.replace(chr(10), ' ')}: median paired difference in k_min vs the mean rule [95% bootstrap CI over targets] (pairs); bold = CI above 0.")


if __name__ == "__main__":
    main()
