"""C6: data audit table.  Output: tables/data_audit.tex  (from results/data_audit.csv; accuracy columns are x100)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "figures", "src"))
import common as C

if __name__ == "__main__":
    a = C.load("data_audit.csv").set_index("bench")
    L = ["\\begin{tabular}{llrrrrrrr}", "\\toprule",
         "Benchmark & Suite & Models & (dedup.) & Items & \\multicolumn{3}{c}{Model accuracy (\\%)} & const. items \\\\",
         " & & raw & & & min & median & max & \\\\", "\\midrule"]
    for b in C.benches(a.reset_index()):
        r = a.loc[b]
        L.append(f"{C.bl(b).replace('_', ' ')} & {'OLL' if r.suite == 'openllm' else 'HELM'} & {r.n_models_raw} & {r.n_models_dedup} & {r.n_items} & "
                 f"{100 * r.acc_min:.1f} & {100 * r.acc_median:.1f} & {100 * r.acc_max:.1f} & {r.n_const_items} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    os.makedirs(C.OUT_TAB, exist_ok=True)
    p = os.path.join(C.OUT_TAB, "data_audit.tex"); open(p, "w").write("\n".join(L) + "\n"); print("wrote", p)
