import json
from pathlib import Path

import numpy as np

from build_results import ROOT, sidecar


def borda_totals(matrix):
    totals = np.zeros(len(matrix), dtype=np.int64)
    for column in matrix.T:
        _, inverse, counts = np.unique(column, return_inverse=True, return_counts=True)
        below = np.cumsum(counts) - counts
        totals += 2 * below[inverse] + counts[inverse] - 1
    return totals / (2 * (len(matrix) - 1) * matrix.shape[1])


def main():
    # @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]
    records = json.loads((ROOT / "derived/original_records.json").read_text())
    matrices = {}
    for family in ["helm", "openllm"]:
        resource = json.loads((ROOT / "data" / (family + ".json")).read_text())
        matrices[family] = np.round(np.asarray([row["scores"] for row in resource["rows"]]), 10)
    checked = 0
    for record in records:
        matrix = matrices[record["family"]].copy()
        target = record["target"]
        original = matrix[target].copy()
        endpoints = np.round(original + record["fraction"] * (1 - original), 10)
        selected = record["allocation"]["tasks"]
        if record["allocation"]["status"] == "unattainable":
            selected = list(range(matrix.shape[1]))
        matrix[target, selected] = endpoints[selected]
        if record["rule"] == "mean":
            aggregates = matrix.mean(axis=1)
        elif record["rule"] == "median":
            aggregates = np.median(matrix, axis=1)
        else:
            aggregates = borda_totals(matrix)
        gap = aggregates[target] - np.delete(aggregates, target).max()
        if record["allocation"]["status"] == "unattainable":
            assert gap < -1e-10, record["pointer"]
        else:
            assert gap >= -1e-10, record["pointer"]
        checked += 1
    path = ROOT / "derived/witness_verification.json"
    path.write_text(json.dumps({"checked_original_records": checked,
                                "scope": "Arithmetic verification of recorded witnesses and all-task unattainability; no solver or evaluator rerun.",
                                "passed": True}, indent=2))
    sidecar(path, sources=["@evidence[[derived/original_records.json]]",
                           "@evidence[[data/helm.json]]",
                           "@evidence[[data/openllm.json]]"], kind="derived")
    print("Verified recorded witnesses and cap infeasibility:", checked)


if __name__ == "__main__":
    main()
