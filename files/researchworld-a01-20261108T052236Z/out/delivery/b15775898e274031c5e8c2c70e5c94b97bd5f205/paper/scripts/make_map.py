"""Write paper/floats/tab_map.tex: which script makes each figure and table, from which result files."""
import csv, json, pathlib
root = pathlib.Path(__file__).resolve().parents[2]
man = json.load(open(root / "presentation/manifest.json"))
scripts = {r["file"]: r["script"] for r in csv.DictReader(open(root / "analysis/results/MANIFEST.csv"))}
where = {"cost_by_rank": "Fig.~\\ref{fig:rank}", "cap_map": "Fig.~\\ref{fig:capmap}", "scaling_and_noise": "Fig.~\\ref{fig:noise}",
         "main_summary": "Tab.~\\ref{tab:summary}", "counterexamples": "Tab.~\\ref{tab:counter}", "theory_validation": "Tab.~\\ref{tab:theory}",
         "cap_map_ollb": "Fig.~\\ref{fig:capmap-ollb}", "cap_map_ollb_sample": "Fig.~\\ref{fig:capmap-sample}", "cap_map_helm": "Fig.~\\ref{fig:capmap-helm}",
         "replay_ollb": "Fig.~\\ref{fig:replay-ollb}", "replay_helm": "Fig.~\\ref{fig:replay-helm}",
         "task_scaling_ceil": "Fig.~\\ref{fig:taskscale}", "task_scaling_gain10": "Fig.~\\ref{fig:taskscale-gain10}",
         "costs_full_ollb": "Tab.~\\ref{tab:costs-ollb}", "costs_full_ollb_sample": "Tab.~\\ref{tab:costs-sample}", "costs_full_helm": "Tab.~\\ref{tab:costs-helm}",
         "ordinal_comparison": "Tab.~\\ref{tab:ordinal}", "order_statistics": "Tab.~\\ref{tab:order}", "power_means_ollb": "Tab.~\\ref{tab:pow-ollb}",
         "power_means_helm": "Tab.~\\ref{tab:pow-helm}", "mean_leader_ollb": "Tab.~\\ref{tab:leader-ollb}", "mean_leader_helm": "Tab.~\\ref{tab:leader-helm}",
         "robust_slices": "Tab.~\\ref{tab:slices}", "robust_offsets": "Tab.~\\ref{tab:offsets}", "robust_eps": "Tab.~\\ref{tab:eps}",
         "robust_reoptimized_costs": "Tab.~\\ref{tab:reopt}", "robust_weights": "Tab.~\\ref{tab:weights}",
         "gstar_curves": "Fig.~\\ref{fig:gstar}", "gstar_matched": "Fig.~\\ref{fig:gstar-matched}", "replay_extra_raise": "Fig.~\\ref{fig:replay-extra}",
         "cluster_uncertainty": "Fig.~\\ref{fig:cluster}", "normalised_rule_costs": "Fig.~\\ref{fig:normalised}"}
where.update({n: "Tab.~\\ref{tab:%s}" % n.replace("_", "-") for n in
              ["gstar_thresholds", "gstar_gain_anchor", "replay_extended", "replay_seed_sensitivity", "reoptimised_seed_sensitivity", "cluster_headline",
               "cluster_family_sensitivity", "cluster_strata_costs", "cluster_strata_feasibility", "cluster_sizes", "normalised_cost_ratios",
               "rank_matched_ratios", "minimum_zero_diagnostic", "ordinal_seed_ceil", "ordinal_seed_gain10"]})
extra = {"cap_rule_summary.csv": "claims.py", "c2_order_statistics.csv": "claims.py", "c4_ordinal_vs_mean.csv": "claims.py",
         "condorcet_existence.csv": "condorcet_exist.py", "theory_validation_summary.json": "theory_validate.py",
         "robust_slices.csv": "slice_summary.py", "robust_eps.csv": "robust_summary.py", "robust_offsets.csv": "robust_summary.py",
         "robust_weights.csv": "robust_summary.py", "robust_nsweep.csv": "robust_summary.py", "robust_noise_taskboot_per_target.csv": "robust_summary.py",
         "ollb_ceil.csv": "run_replay.py", "ollb_gain10.csv": "run_replay.py", "helm_ceil.csv": "run_replay.py", "helm_gain10.csv": "run_replay.py"}
scripts.update(extra)
scripts.update({k.split("/")[-1]: v.split("/")[-1] for k, v in json.load(open(root / "presentation/SOURCE_SCRIPTS.json"))["producers"].items()})
esc = lambda s: s.replace("_", "\\_\\allowbreak ")
rows = []
for a in man["artifacts"]:
    ins = [i["path"].split("/")[-1] for i in a["inputs"]]
    sc = sorted({scripts.get(i, "?") for i in ins if i in scripts})
    rows.append((where[a["name"]], a["name"], ins, sc))
rows.sort(key=lambda r: ("Fig" not in r[0], r[0]))
cap = ("Script-to-output map. Figures and tables made by \\texttt{presentation/render.py} (display summaries only) are listed with the result files in \\texttt{analysis/results/} they are made from, each followed by the analysis script that wrote it (\\texttt{MANIFEST.csv}); where an asset has more than three result files the list is cut (\\ldots) and the exact list is in \\texttt{presentation/manifest.json}. "
       "The two tables written by the report are listed last: their numbers come from the claim tables via \\texttt{paper/scripts/make\\_numbers.py}.")
report = [("Tab.~\\ref{tab:claims}", "claims", ["cap_rule_summary.csv", "c2_order_statistics.csv", "c4_ordinal_vs_mean.csv", "replay2_summary.csv"], "typeset in paper/sections/experiments.tex; values via paper/scripts/make_numbers.py"),
          ("Tab.~\\ref{tab:map}", "script map", ["presentation/manifest.json", "MANIFEST.csv"], "paper/scripts/make_map.py")]
out = ["\\Needspace{10\\baselineskip}", "\\begingroup", "\\captionof{table}{" + cap + "}\\label{tab:map}", "\\fontsize{8}{9.5}\\selectfont",
       "\\begin{longtable}{@{}p{0.55in} p{1.55in} p{3.0in}@{}}", "\\toprule", "Where & Asset & Result files (analysis script) \\\\", "\\midrule", "\\endfirsthead",
       "\\toprule", "Where & Asset & Result files (analysis script) \\\\", "\\midrule", "\\endhead", "\\bottomrule", "\\endlastfoot"]
for w, n, ins, sc in rows:
    shown = ins[:3]
    cell = ", ".join("%s (%s)" % (esc(f), esc(scripts.get(f, "?"))) for f in shown) + (", \\ldots" if len(ins) > 3 else "")
    out.append("%s & \\texttt{%s} & \\texttt{%s} \\\\" % (w, esc(n), cell.replace("\\_\\allowbreak ", "\\_\\allowbreak ")))
for w, n, ins, how in report:
    cell = ", ".join(esc(f) for f in ins) + "; " + esc(how)
    out.append("%s & \\texttt{%s} & \\texttt{%s} \\\\" % (w, esc(n), cell))
out += ["\\end{longtable}", "\\addtocounter{table}{-1}", "\\endgroup", ""]
(root / "paper/floats/tab_map.tex").write_text("\n".join(out))
