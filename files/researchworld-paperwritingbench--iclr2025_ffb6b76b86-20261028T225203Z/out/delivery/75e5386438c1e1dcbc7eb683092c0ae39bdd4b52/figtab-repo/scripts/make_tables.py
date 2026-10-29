"""Generate the LaTeX tables of the paper from the CSVs transcribed from the experimental log.

Usage: python3 scripts/make_tables.py   (writes exhibits/tables.tex)

Conventions (ICLR): caption above the table, booktabs rules, "--" where the log has N/A,
best score per benchmark (over every cell of that benchmark) in bold.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NA = "--"


def read(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def best(rows, cols):
    vals = [float(r[c]) for r in rows for c in cols if r[c]]
    return max(vals)


def cell(v, top):
    if not v:
        return NA
    return r"\textbf{%s}" % v if float(v) == top else v


def general_table():
    rows = read("general_lm.csv")
    benches = [("mmlu", "MMLU"), ("piqa", "PIQA"), ("nq", "NQ"),
               ("triviaqa", "TriviaQA"), ("gsm8k", "GSM8K")]
    tops = {b: best(rows, [f"{b}_token", f"{b}_byte"]) for b, _ in benches}
    out = [r"\begin{table}[t]",
           r"\caption{Accuracy (\%) of general-purpose LMs with token-level and byte-level"
           r" predictions on knowledge and reasoning benchmarks. Byte-level predictions are"
           r" obtained from the same models without retraining. Voting and the byte-level"
           r" ensemble combine the two best-performing models on each benchmark and are reported in"
           r" the byte-level columns; token-level entries are not applicable (--)."
           r" Voting was not reported for NQ, TriviaQA and GSM8K. Bold: best score per benchmark.}",
           r"\label{tab:general}",
           r"\begin{center}",
           r"\small",
           r"\setlength{\tabcolsep}{4.5pt}",
           r"\begin{tabular}{l" + "cc" * len(benches) + "}",
           r"\toprule",
           " & " + " & ".join(r"\multicolumn{2}{c}{%s}" % n for _, n in benches) + r" \\",
           " ".join(r"\cmidrule(lr){%d-%d}" % (2 + 2 * i, 3 + 2 * i) for i in range(len(benches))),
           "Model & " + " & ".join(["Token & Byte"] * len(benches)) + r" \\",
           r"\midrule"]
    for r in rows:
        if r["model"].startswith("Voting"):
            out.append(r"\midrule")
        name = r["model"].replace("(Ours)", "(ours)")
        cells = []
        for b, _ in benches:
            cells += [cell(r[f"{b}_token"], tops[b]), cell(r[f"{b}_byte"], tops[b])]
        out.append(name + " & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}", r"\end{table}"]
    return "\n".join(out)


def code_and_beam_table():
    rows = read("code_lm.csv")
    benches = [("humaneval", "HumanEval"), ("mbpp", "MBPP")]
    tops = {b: best(rows, [f"{b}_token", f"{b}_byte"]) for b, _ in benches}
    beam = read("beam_ablation.csv")
    out = [r"\begin{table}[t]",
           r"\begin{minipage}[t]{0.60\linewidth}",
           r"\caption{Pass@1 (\%) of code LMs with token-level and byte-level predictions."
           r" The byte-level ensemble combines the two best-performing models on each benchmark"
           r" (--: not applicable). Bold: best score per benchmark.}",
           r"\label{tab:code}",
           r"\begin{center}",
           r"\small",
           r"\setlength{\tabcolsep}{4.5pt}",
           r"\begin{tabular}{lcccc}",
           r"\toprule",
           " & " + " & ".join(r"\multicolumn{2}{c}{%s}" % n for _, n in benches) + r" \\",
           r"\cmidrule(lr){2-3} \cmidrule(lr){4-5}",
           r"Model & Token & Byte & Token & Byte \\",
           r"\midrule"]
    for r in rows:
        if r["model"].startswith("Top-2"):
            out.append(r"\midrule")
        name = r["model"].replace("(Ours)", "(ours)")
        cells = []
        for b, _ in benches:
            cells += [cell(r[f"{b}_token"], tops[b]), cell(r[f"{b}_byte"], tops[b])]
        out.append(name + " & " + " & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}", r"\end{minipage}\hfill",
            r"\begin{minipage}[t]{0.36\linewidth}",
            r"\caption{Effect of beam width on the byte-level FIM pass rate (\%) on HumanEval."
            r" Width 1 matches the byte-level greedy results of Figure~\ref{fig:fim}.}",
            r"\label{tab:beam}",
            r"\begin{center}",
            r"\small",
            r"\begin{tabular}{ccc}",
            r"\toprule",
            r"Beam width & PSM & SPM \\",
            r"\midrule"]
    tp, ts = max(float(r["psm"]) for r in beam), max(float(r["spm"]) for r in beam)
    for r in beam:
        out.append(f"{r['beam_width']} & {cell(r['psm'], tp)} & {cell(r['spm'], ts)} " + r"\\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}", r"\end{minipage}",
            r"\end{table}"]
    return "\n".join(out)


def fim_table_fallback():
    rows = read("fim_humaneval_random_span.csv")
    cols = ["psm_greedy", "psm_at10", "spm_greedy", "spm_at10"]
    tops = {c: best(rows, [c]) for c in cols}
    out = [r"\begin{table}[t]",
           r"\caption{Pass rates (\%) on HumanEval Random Span infilling with CodeLlama-7b under"
           r" the PSM and SPM prompt templates. Token healing and alignment are fixes for prompts"
           r" ending mid-token and are evaluated in SPM mode only (--). Bold: best per column.}",
           r"\label{tab:fim}",
           r"\begin{center}",
           r"\small",
           r"\begin{tabular}{lcccc}",
           r"\toprule",
           r" & \multicolumn{2}{c}{PSM} & \multicolumn{2}{c}{SPM} \\",
           r"\cmidrule(lr){2-3} \cmidrule(lr){4-5}",
           r"Method & Greedy & @10 & Greedy & @10 \\",
           r"\midrule"]
    for r in rows:
        if r["method"].startswith("Byte"):
            out.append(r"\midrule")
        name = r["method"].replace("Token-level + Healing", r"\quad + token healing") \
                          .replace("Token-level + Alignment", r"\quad + token alignment") \
                          .replace("(Ours)", "(ours)")
        out.append(name + " & " + " & ".join(cell(r[c], tops[c]) for c in cols) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}", r"\end{table}"]
    return "\n".join(out)


HEADER = ("% Generated by scripts/make_tables.py from data/*.csv (transcribed from the\n"
          "% experimental log). Do not edit numbers by hand; requires \\usepackage{booktabs}.\n")

if __name__ == "__main__":
    (ROOT / "exhibits" / "tables.tex").write_text(
        HEADER + "\n% --- Table: general LMs (log Table 2) ---\n" + general_table()
        + "\n\n% --- Tables: code LMs (log Table 3) and beam ablation (log Table 4) ---\n"
        + code_and_beam_table() + "\n")
    (ROOT / "exhibits" / "table_fim_fallback.tex").write_text(
        HEADER + "% Optional: log Table 1 is already printed inside figures/figure_6.png;"
        " use only if Figure 6 is not used.\n" + fim_table_fallback() + "\n")
    print("wrote exhibits/tables.tex and exhibits/table_fim_fallback.tex")
