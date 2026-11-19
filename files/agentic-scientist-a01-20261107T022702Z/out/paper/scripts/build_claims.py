import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    paper = json.loads((ROOT / "paper_data.json").read_text())
    records = json.loads((ROOT / "derived/original_records.json").read_text())
    references = json.loads((ROOT / "references_provenance.json").read_text())["references"]
    claims = []

    def add(claim, source_ids=None, locations=None, artifacts=None, citations=None):
        claims.append({"claim": claim, "source_ids": source_ids or ["final.evidence.episodes"],
                       "citation_keys": citations or [], "evidence_locations": locations or [],
                       "supporting_artifacts": artifacts or []})

    add("Task investment selects coordinates updated to round10(x+rho(1-x)); positive caps are 1 and 1/2, co-first tolerance is 1e-10, input rounding is 10 decimals.",
        artifacts=["source_evidence/downstream/program/src/program.py:1", "source_evidence/downstream/program/src/program.py:260", "data/protocol.json"])
    add("The rules are arithmetic mean, ordinary median including averaged central values when even, and pairwise Borda with half-credit ties and updated rivals.",
        artifacts=["source_evidence/downstream/program/src/program.py:50", "source_evidence/downstream/program/src/program.py:129", "source_evidence/downstream/program/src/program.py:193"])
    add("HELM MMLU v1.13.0 contributes 57 subject scores and Open LLM contributes six normalized columns, divided by 100, from pinned revision 9c09a7cae43334062a82cb164f2ef255013dafa2; frozen resources record acquisition on 2026-11-07.",
        artifacts=["data/helm.json", "data/openllm.json", "data/protocol.json", "scripts/acquire_scores.py"],
        locations=["final.evidence.episodes: original HELM and Open LLM decisions; table dimensions and public provenance are inspectable supplementary resource metadata"])
    add("There are eight fixed mean-nonwinner rank-spaced targets per score table; three seeds 42011,42013,42017 repeat the same instances; 48 decisions per family, 96 distinct original instances, 288 original records.",
        artifacts=["derived/summary.json", "data/protocol.json"])
    add("Within any fixed rule and target, increasing rho weakly decreases the minimum budget, including infinity; this does not order different rules. Full-headroom all-task reachability follows structurally from the intervention model.",
        artifacts=["source_evidence/downstream/program/src/program.py:260", "source_evidence/downstream/program/src/program.py:193"])
    for record in records:
        if record["seed"] != records[0]["seed"]:
            continue
        key = (record["family"], record["target"], record["rule"], record["fraction"])
        related = [other for other in records if (other["family"], other["target"], other["rule"], other["fraction"]) == key]
        if record["budget"] is None:
            text = f"{key}: promotion is unattainable, independently certified; no finite budget or zero-cost intervention is inferred."
        else:
            random_counts = [len(other["baselines"]["random"]["tasks"]) for other in related]
            text = (f"{key}: minimum task budget {record['budget']}; normalized fraction {record['budget']}/{record['dimension']}; "
                    f"independent lower=upper={record['budget']}; greedy={len(record['baselines']['greedy']['tasks'])}; "
                    f"recorded random counts range {min(random_counts)}--{max(random_counts)}.")
        add(text, locations=["paper_data.json#" + other["pointer"] for other in related], artifacts=["tables/budgets.tex", "derived/allocations.csv"])
    add("HELM row 10 reverses mean/median ordering from 9/12 at full cap to 23/12 at half cap. Open LLM row 1609 reverses from 2/3 to 4/3. These are instance counterexamples, not population rates.",
        artifacts=["derived/original_records.json", "figures/paired_mean_median_budgets.pdf"])
    add("All eight original targets per family are reachable under all rules at full cap. At half cap HELM reachability is 5/5/4 and Open LLM is 7/6/3 for mean/median/Borda.",
        artifacts=["derived/summary.json", "figures/cap_conditioned_reachability.pdf"])
    add("Every original reference interval closes, all finite selected cardinalities match reference minima, and selected subsets repeat identically across three seeds.",
        artifacts=["scripts/build_results.py", "derived/summary.json"])
    add("Matched greedy equals the finite minimum for original mean and Borda decisions. HELM row28 median at half cap has optimum21 versus greedy52. No component attribution follows.",
        artifacts=["derived/summary.json", "derived/original_records.json"])
    add("Permutation, constant and zero-update controls each have 48 validated decisions per family and seed with no case failure; one first-seed replay is recorded as successful and the remaining replay payloads are absent.",
        locations=["/final_evaluation/evaluation_evidence/episodes/0/solution/replay"], artifacts=["derived/summary.json"])
    add("Mean sorted gains, odd-median threshold counting, even-median endpoint counting and rival-aware Borda integer gap constraints describe the inspectable supplied selected source; its tree-digest scope is not equated to the final manifest. Borda search has 20000-node limit, 0.9 work allowance and verified incumbent fallback. Exhaustive scalar verification is used when d<=6.",
        artifacts=["source_evidence/downstream/program/src/program.py:63", "source_evidence/downstream/program/src/program.py:73", "source_evidence/downstream/program/src/program.py:82", "source_evidence/downstream/program/src/program.py:93", "source_evidence/downstream/program/src/program.py:160", "source_evidence/downstream/program/src/program.py:193", "source_evidence/downstream/program/src/program.py:268"])
    add("Independent references use exhaustive six-task subsets, exact scalar HELM checks, and time-limited SciPy binary Borda optimization; random and greedy are matched score-space selection policies, not training algorithms.",
        artifacts=["data/protocol.json", "source_evidence/evaluation.py", "source_evidence/downstream/baseline/src/program.py"])
    add("Development selection had three scored configurations, zero unscored configurations, and zero aggregate difference from the original baseline; no matched final original-baseline delta is available.",
        source_ids=["study.attempts.total", "study.attempts.scored", "study.attempts.unscored", "study.search_score", "study.baseline_score", "study.search_score_delta", "study.investigation_outcome", "study.selection_kind"])
    add("The independent frozen final assessment is completed and qualified; this does not establish generalization, novelty or superiority.",
        source_ids=["final.qualification.status", "final.qualification.outcome", "final.qualification.correct"])
    add("No ablation supports internal component superiority; training-response calibration, strict-margin sensitivity and composition resampling are unavailable. Task budgets are not observed training cost.",
        artifacts=["source_evidence/downstream/program/src/METHOD.md", "data/protocol.json"])
    for reference in references:
        add("Background citation consulted within documented scope: " + reference["title"],
            source_ids=[reference["id"]], artifacts=[reference["content_path"]], citations=[reference["citation_key"]])
    known = set(paper["grounding_sources"]) | {reference["id"] for reference in references}
    assert all(set(claim["source_ids"]) <= known for claim in claims)
    (ROOT / "claims_grounding.json").write_text(json.dumps({"claims": claims}, indent=2))
    print("Claims:", len(claims))


if __name__ == "__main__":
    main()
