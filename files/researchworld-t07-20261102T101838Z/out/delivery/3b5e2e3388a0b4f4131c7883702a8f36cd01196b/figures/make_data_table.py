"""Table 'data': models x items, accuracy spread and degenerate items per benchmark.
Reads the pinned .jbl score matrices (benchmark-prediction commit 55faff49...).
Usage: python3 -I make_data_table.py <dir with *.jbl> <out dir>"""
import sys, pathlib
import joblib, numpy as np, pandas as pd

BENCH = [("ifeval", "IFEval"), ("bbh", "BBH"), ("gpqa", "GPQA"), ("musr", "MuSR"), ("openllm_math", "MATH Lvl5"),
         ("mmlu_pro", "MMLU-Pro"), ("arc_challenge", "ARC-C"), ("mmlu", "HELM MMLU"), ("gsm", "HELM GSM8K"),
         ("math", "HELM MATH"), ("med_qa", "HELM MedQA"), ("legalbench", "HELM LegalBench"),
         ("commonsense", "HELM Commonsense")]

src, out = map(pathlib.Path, sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
rows = []
for key, name in BENCH:
    M = np.asarray(joblib.load(src / f"{key}.jbl")).astype(float)
    n_raw = M.shape
    M = M[~np.isnan(M).all(1)][:, ~np.isnan(M).all(0)]
    acc = np.nanmean(M, 1)
    p = np.nanmean(M, 0)
    rows.append(dict(benchmark=name, key=key, raw_models=n_raw[0], raw_items=n_raw[1],
                     models=M.shape[0], items=M.shape[1], nan_frac=float(np.isnan(M).mean()),
                     acc_min=acc.min(), acc_median=np.median(acc), acc_max=acc.max(),
                     mean_item_acc=p.mean(), frac_items_const=float(((p == 0) | (p == 1)).mean())))
df = pd.DataFrame(rows)
df.to_csv(out / "data_summary.csv", index=False)

tex = [r"\begin{tabular}{lrrccc}", r"\toprule",
       r"Benchmark & Models & Items & Model acc.\ min / med / max & Items solved by all or none \\", r"\midrule"]
tex = [r"\begin{tabular}{lrrcr}", r"\toprule",
       r"Benchmark & Models & Items & Model accuracy (min / median / max) & Constant items \\", r"\midrule"]
for r in rows:
    tex.append(f"{r['benchmark']} & {r['models']} & {r['items']} & "
               f"{100*r['acc_min']:.1f} / {100*r['acc_median']:.1f} / {100*r['acc_max']:.1f} & "
               f"{100*r['frac_items_const']:.1f}\\% \\\\")
    if r["key"] == "arc_challenge":
        tex.append(r"\midrule")
tex += [r"\bottomrule", r"\end{tabular}"]
(out / "tab_data.tex").write_text("\n".join(tex) + "\n")
print(df.to_string())
