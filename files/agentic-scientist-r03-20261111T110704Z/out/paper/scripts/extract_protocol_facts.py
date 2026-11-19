"""Derive dataset sizes and evaluation-plan facts from the evaluator manifests / evaluator source.
Reads only source_evidence/ (manifests + evaluate_final.py); writes analysis/protocol_facts.json."""
import json, re, collections, pathlib
# @evidence[[source_evidence/evaluator/evaluate_final.py]]
root = pathlib.Path("source_evidence/manifests")
out = {"final": {}, "search": {}}
for fam, stem in (("mteb", "mteb_final"), ("oll", "oll_final"), ("helm", "helm_final")):
    m = json.load(open(root / (stem + "_manifest.json")))  # @evidence[[source_evidence/manifests/mteb_final_manifest.json]]
    roles = collections.Counter(x["role"] for x in m["models"])
    out["final"][fam] = {"revision": m["revision"], "n_columns": len(m["columns"]),
                         "n_history_models": roles[0], "n_heldout_models": roles[1],
                         "n_family_groups_history": len({x["group"] for x in m["models"] if x["role"] == 0}),
                         "n_family_groups_heldout": len({x["group"] for x in m["models"] if x["role"] == 1})}
m = json.load(open("source_evidence/manifests/mteb_search_manifest.json"))
roles = collections.Counter(x["role"] for x in m["models"])
out["search"]["mteb"] = {"revision": m["revision"], "n_columns": len(m["columns"]),
                         "n_history_models": roles[0], "n_heldout_models": roles[1]}
src = open("source_evidence/evaluator/evaluate_final.py").read()
out["final_seeds"] = [int(x) for x in re.search(r"FINAL_SEEDS = \(([^)]*)\)", src).group(1).split(",")]
out["baseline_draws"] = int(re.search(r"BASELINE_DRAWS = (\d+)", src).group(1))
out["completion_rank"] = int(re.search(r"COMPLETION_RANK = (\d+)", src).group(1))
out["completion_iters"] = int(re.search(r"COMPLETION_ITERS = (\d+)", src).group(1))
cases = re.findall(r'\("(real|perm|const)", "(\w+)", (\d+)\)', src.split("def build_plan")[1].split("def load_datasets")[0])
out["plan"] = [{"case": c, "family": f, "k": int(k)} for c, f, k in cases if True][-14:]
json.dump(out, open("analysis/protocol_facts.json", "w"), indent=1)
print(json.dumps(out, indent=1))
