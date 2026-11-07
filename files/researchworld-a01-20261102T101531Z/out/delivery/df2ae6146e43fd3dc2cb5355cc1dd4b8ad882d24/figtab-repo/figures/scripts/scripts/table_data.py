"""Table: data sources from results/data_manifest.json: snapshot, size (models x tasks), score unit, exclusions."""
import json
from common import *


def main():
    a = args(__doc__)
    m = json.load(open(os.path.join(a.results, "data_manifest.json")))["sources"]
    h, o1, o2 = m["helm_mmlu"], m["open_llm_leaderboard_v2_headline"], m["open_llm_leaderboard_v2_subtask"]
    ex = o1["exclusions"]
    rows = [
        ["HELM MMLU", "release v1.13.0", f"{h['models_after_exclusions']} (of {h['models_before_exclusions']})", h["tasks"], "exact match, 100--1534 items/subject",
         "none (all models complete)"],
        ["Open LLM Lb. v2, headline (\\texttt{contents})", "\\texttt{" + o1["snapshot_sha"][:7] + "}", f"{o1['models_main_population']:,} (of {o1['rows_total']:,})", o1["tasks"],
         "normalised task scores", f"{ex['flagged']} flagged, {ex['duplicate_fullname_after_flag_removal']} duplicate names"],
        ["Open LLM Lb. v2, sub-task (\\texttt{results})", "\\texttt{" + o2["snapshot_sha"][:7] + "}", f"{o2['models_used']} (selected subset)", o2["tasks"], "sub-task accuracy",
         "subset: top 300 by Average + 400 random"],
    ]
    write_table(a, "data", rows, "llrrll", ["Board", "Snapshot", "Models", "Tasks", "Score", "Exclusions / selection"],
                "Snapshot ids and file checksums: results/data_manifest.json.")


if __name__ == "__main__":
    main()
