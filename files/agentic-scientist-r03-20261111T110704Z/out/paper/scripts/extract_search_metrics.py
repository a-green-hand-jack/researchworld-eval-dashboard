"""Collect search-split metrics of the three scored configurations into analysis/search_metrics.json."""
import json
# @evidence[[source_evidence/metrics_cfg01.json]] @evidence[[source_evidence/evalevidence_cfg01.json]]
rows = {}
for n in ("01", "02", "03"):
    m = json.load(open(f"source_evidence/metrics_cfg{n}.json"))
    ev = json.load(open(f"source_evidence/evalevidence_cfg{n}.json"))
    rows[n] = {"metrics": m,
               "seed_scores": {str(e["seed"]): e["score"] for e in ev["episodes"]},
               "seed_durations_s": {str(e["seed"]): e["duration_seconds"] for e in ev["episodes"]}}
json.dump(rows, open("analysis/search_metrics.json", "w"), indent=1)
print(json.dumps(rows, indent=1))
