"""Table (C6, appendix): ablation grid for C2: median paired difference k_min(rule) - k_min(mean) [CI] per factor level, board and rule.
Bold = claim_holds==1 (CI strictly above 0, i.e. C2 supported in that cell). Rules shown: those named in the plan (median, Borda, Copeland, Condorcet)."""
from common import *

RULES = ["median", "borda", "copeland", "condorcet_winner"]
ORDER = ["gain_model", "granularity", "normalisation", "population", "field", "noise"]


def main():
    a = args(__doc__)
    df = read(a, "ablation.csv")
    df = df[df.metric.str.startswith("C2") & df.rule.isin(RULES)]
    rows = []
    for f in ORDER:
        for (lb, lv), d in df[df.factor == f].groupby(["leaderboard", "level"], sort=False):
            row = [latex_escape(f), latex_escape(lv), "HELM" if lb == "helm_mmlu" else "OLB"]
            for r in RULES:
                x = d[d.rule == r]
                if len(x) == 0 or pd.isna(x.estimate.iloc[0]):
                    row.append("--"); continue
                x = x.iloc[0]
                s = f"{x.estimate:+.1f} [{x.ci_lo:+.1f}, {x.ci_hi:+.1f}]".replace("-", "$-$")
                row.append(f"\\textbf{{{s}}}" if x.claim_holds == 1 else s)
            rows.append(row)
    write_table(a, "ablation_c2", rows, "lllllll", ["Factor", "Level", "Board"] + [RULE_LABEL[r] for r in RULES],
                "k_min(rule) - k_min(mean), median over targets feasible under both [95% bootstrap CI]; bold = CI above 0. Criterion: results/README.md.")


if __name__ == "__main__":
    main()
