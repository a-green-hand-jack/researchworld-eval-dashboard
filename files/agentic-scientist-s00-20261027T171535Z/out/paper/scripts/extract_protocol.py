"""Derive protocol facts (graph counts, families, size ranges, constants) from the task resources."""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "protocol_inputs"  # verbatim copies of the task resources and final evaluator source
out = {}
for plane in ("search", "final"):
    for split in ("train", "test"):
        # @evidence[[protocol_inputs/resources/final/test_graphs.json]]
        g = json.loads((TASK / "resources" / plane / f"{split}_graphs.json").read_text())["graphs"]
        ns = [x["n"] for x in g]
        out[f"{plane}_{split}"] = {
            "count": len(g),
            "n_min": min(ns),
            "n_max": max(ns),
            "families": dict(sorted(collections.Counter(x["family"] for x in g).items())),
        }
src = (TASK / "evaluate_final.py").read_text()
# @evidence[[protocol_inputs/evaluate_final.py]]
for name in ("MC_WALKS", "ERR_CLIP", "PERM_TOL"):
    out[name] = float(re.search(rf"^{name} = ([0-9.e-]+)", src, re.M).group(1))
out["final_episode_seeds"] = [201, 202, 203]
(ROOT / "protocol_facts.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
