"""Parse the Open LLM Leaderboard `results` snapshot (one JSON per evaluation) into a flat table of
leaf-task scores (raw accuracy in [0,1]) and stderrs, plus group-level scores and evaluation metadata.
usage: prep_ollb_results.py RESULTS_DIR OUT_DIR"""
import sys, os, json, glob
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
BBH = [f"leaderboard_bbh_{s}" for s in """boolean_expressions causal_judgement date_understanding disambiguation_qa formal_fallacies geometric_shapes
hyperbaton logical_deduction_five_objects logical_deduction_seven_objects logical_deduction_three_objects movie_recommendation navigate
object_counting penguins_in_a_table reasoning_about_colored_objects ruin_names salient_translation_error_detection snarks sports_understanding
temporal_sequences tracking_shuffled_objects_five_objects tracking_shuffled_objects_seven_objects tracking_shuffled_objects_three_objects web_of_lies""".split()]
GPQA = ["leaderboard_gpqa_diamond", "leaderboard_gpqa_extended", "leaderboard_gpqa_main"]
MATH = [f"leaderboard_math_{s}_hard" for s in "algebra counting_and_prob geometry intermediate_algebra num_theory prealgebra precalculus".split()]
MUSR = ["leaderboard_musr_murder_mysteries", "leaderboard_musr_object_placements", "leaderboard_musr_team_allocation"]
METRIC = {**{t: "acc_norm,none" for t in BBH + GPQA + MUSR}, **{t: "exact_match,none" for t in MATH}, "leaderboard_mmlu_pro": "acc,none"}
GROUP = {"BBH": ("leaderboard_bbh", "acc_norm,none", BBH), "GPQA": ("leaderboard_gpqa", "acc_norm,none", GPQA),
         "MATH": ("leaderboard_math_hard", "exact_match,none", MATH), "MUSR": ("leaderboard_musr", "acc_norm,none", MUSR)}
rec, bad = [], []
for f in sorted(glob.glob(os.path.join(src, "*/*/results_*.json"))):
    try:
        d = json.load(open(f)); R = d["results"]
        row = dict(file=os.path.relpath(f, src), model_name=d.get("model_name"), model_sha=d["config"].get("model_sha"),
                   dtype=d["config"].get("model_dtype"), date=d.get("date"))
        for t, m in METRIC.items():
            row[t] = R[t][m]; row[t + "__se"] = R[t].get(m.replace(",none", "_stderr,none"))
            ns = d.get("n-samples", {}).get(t, {}); row[t + "__n"] = ns.get("effective")
        for k in ("prompt_level_strict_acc,none", "inst_level_strict_acc,none"):
            row["leaderboard_ifeval__" + k.split(",")[0]] = R["leaderboard_ifeval"][k]
        row["leaderboard_ifeval"] = 0.5 * (R["leaderboard_ifeval"]["prompt_level_strict_acc,none"] + R["leaderboard_ifeval"]["inst_level_strict_acc,none"])
        row["leaderboard_ifeval__se"] = R["leaderboard_ifeval"].get("prompt_level_strict_acc_stderr,none")
        for g, (gk, gm, _) in GROUP.items():
            row["group_" + g] = R[gk][gm]
        rec.append(row)
    except Exception as e:
        bad.append((f, repr(e)))
df = pd.DataFrame(rec)
print(len(df), "parsed;", len(bad), "failed")
for b in bad[:5]: print(b)
df.to_parquet(os.path.join(out, "ollb_results_leaf.parquet"))
pd.DataFrame(bad, columns=["file", "error"]).to_csv(os.path.join(out, "ollb_results_unparsed.csv"), index=False)
