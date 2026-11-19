"""Headline tables (absolute answer): median k_min (bootstrap CI), median G_min and share feasible, per board, rule, gain model and rank stratum
of the target (rank under the mean rule: 2-10, 11-100, rest). Source: results/per_target.csv (linear cost, normalised scores, full field).
Median k_min / G_min are over the feasible targets only (read them with the feasible share beside them). CI: percentile bootstrap over the feasible
targets (B=2000, --seed) where at least 10 are feasible; a median over fewer than 5 feasible targets is shown in parentheses.
G_min: infimum with strictness ignored; a dagger marks a cell where any G_min is an upper bound
(G_min_kind = upper_bound_frontier); -- = G_min not computed for every feasible target of the cell (median with an even number of tasks, ordinal rules off G1), or no feasible target.
Outputs: headline_main.tex (one gain model, --main-gain), headline_<gain>.tex per gain model, headline_full.tex (all of them, stacked)."""
from common import *

RULES = ["mean", "median", "trimmed_mean", "min", "borda", "copeland", "plurality", "condorcet_winner"]
STRATA = [("2-10", 1, 10), ("11-100", 10, 100), ("rest", 100, 10 ** 9)]
FULL_GAINS = ["G1", "G1_add10", "G2_0.5", "ceil"]
BNAME = {("helm_mmlu", "headline"): "HELM MMLU (57 subjects, 79 models)",
         ("openllm_v2", "headline"): "Open LLM Lb. v2, headline (6 tasks)",
         ("openllm_v2", "subtask"): "Open LLM Lb. v2, sub-tasks (39 tasks)"}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def num(x):
    s = f"{x:.1f}" if abs(x - round(x)) > 1e-9 else f"{int(round(x))}"
    return s


def cell(x, rng, B, ci_feas):
    n = len(x)
    f = x.feasible.eq(1)
    nf = int(f.sum())
    share = f.mean()
    kv = x.k_min[f].to_numpy(float)
    if nf == 0:
        k = "--"
    else:
        med = np.median(kv)
        if nf >= 10:
            lo, hi = boot_ci(kv, np.median, rng, B)
            k = f"{num(med)} [{num(lo)}, {num(hi)}]"
        else:
            k = f"({num(med)})" if nf < 5 else num(med)
    g = x[f & x.G_min.notna()]
    if len(g) < nf or nf == 0:     # shown only when G_min exists for every feasible target of the cell (no selected subset)
        G = "--"
    else:
        G = num(np.median(g.G_min)) + ("$^\\dagger$" if (g.G_min_kind == "upper_bound_frontier").any() else "")
    if ci_feas:
        lo, hi = wilson(int(f.sum()), n)
        fs = f"{share:.2f} [{lo:.2f}, {hi:.2f}]"
    else:
        fs = f"{share:.2f}"
    return [k, G, fs]


def build(d, gain, a, ci_feas):
    """One tabular for one gain model; returns (tex-lines body rows, colspec, header rows)."""
    rng = np.random.default_rng(a.seed)
    rows = []
    for (lb, gr), title in BNAME.items():
        b = d[(d.leaderboard == lb) & (d.granularity == gr) & (d.gain_model == gain)]
        ns = []
        for lab, lo, hi in STRATA:
            t = b[(b.rule == "mean") & (b.rank_mean > lo) & (b.rank_mean <= hi)]
            ns.append(len(t))
        ntxt = ", ".join(f"{lab}: {n}" for (lab, _, _), n in zip(STRATA, ns) if n)
        rows.append(("sec", f"{title}; targets per stratum: {ntxt}"))
        for r in RULES:
            row = [RULE_LABEL[r]]
            for (lab, lo, hi), n in zip(STRATA, ns):
                if n == 0:
                    row += [""] * 3
                    continue
                x = b[(b.rule == r) & (b.rank_mean > lo) & (b.rank_mean <= hi)]
                row += cell(x, rng, a.boot, ci_feas)
            rows.append(("row", row))
    return rows


def tabular(rows):
    lines = [r"\begin{tabular}{l" + "rrr" * 3 + "}", r"\toprule",
             "Rule & " + " & ".join(r"\multicolumn{3}{c}{rank " + s[0].replace("-", "--") + "}" for s in STRATA) + r" \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}",
             " & " + " & ".join(["$k_{\\min}$", "$G_{\\min}$", "feasible"] * 3) + r" \\", r"\midrule"]
    first = True
    for kind, v in rows:
        if kind == "sec":
            if not first:
                lines.append(r"\midrule")
            lines.append(r"\multicolumn{10}{l}{\textit{" + latex_escape(v) + r"}} \\")
            first = False
        else:
            lines.append(" & ".join(map(str, v)) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


def main():
    def extra(p):
        p.add_argument("--main-gain", default="G1_add10")
        p.add_argument("--boot", type=int, default=2000)
    a = args(__doc__, extra)
    d = read(a, "per_target.csv")
    d = d[(d.cost == "linear") & (d.normalisation == "normalised") & (d.field == "all") & d.rule.isin(RULES)
          & (d.rule_param.isna() | (d.rule == "trimmed_mean") & (d.rule_param == 0.2))]
    if "rank_mean" not in d:     # per_target.csv before analysis delivery 2: rank under the mean from the mean-rule rows
        key = ["leaderboard", "granularity", "population", "target_id"]
        rm = d[d.rule == "mean"].groupby(key).init_rank.first().rename("rank_mean").reset_index()
        d = d.merge(rm, on=key)
    w = lambda name, s: open(os.path.join(a.tables_out, name), "w").write(s)
    note = (__doc__.split("Outputs:")[0]).strip()
    full = []
    for g in sorted(set(FULL_GAINS) | {a.main_gain}):
        rows = build(d, g, a, ci_feas=True)
        tex = tabular(rows)
        w(f"headline_{g}.tex", tex)
        if g in FULL_GAINS:
            full.append(f"\\noindent\\textbf{{Gain model {latex_escape(g)}}} ({latex_escape(GAIN_LABEL[g])})\\par\\smallskip\n"
                        f"\\resizebox{{\\linewidth}}{{!}}{{\\input{{../tables/headline_{g}.tex}}}}\\par\\bigskip\n")
        if g == a.main_gain:
            w("headline_main.tex", tabular(build(d, g, a, ci_feas=False)))
    w("headline_full.tex", "".join(full))
    for n in ["headline_main", "headline_full"] + [f"headline_{g}" for g in FULL_GAINS]:
        with open(os.path.join(a.tables_out, n + ".settings.txt"), "w") as f:
            f.write(f"main gain model {a.main_gain}; " + note + "\n")


if __name__ == "__main__":
    main()
