# Agentic evidence audit packet

- generated_at: `2026-11-07T05:13:58.122288+00:00`
- paper_dir: `work/results/a01/codex/20261107_023211/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261107_040258-paper_evidence_audit_round_3-6ogn3642/workspace`

Use this packet as the default entrypoint. Read raw artifacts only when this packet is insufficient.
The goal is narrow: check whether the paper's visible claims remain consistent with claims_grounding.json, paper_data.json, and the scientific-evidence trail.

## Expected audit focus

- visible claims in `paper.tex` that overstate, contradict, or drift from `claims_grounding.json`
- claims grounded to the wrong source ids, or source ids that do not support the visible wording
- mismatches between visible manuscript text and the resolved/anchored evidence trail
- cases where the evidence trail exists but does not justify the paper's wording or numeric precision
- contradictions between `paper.tex`, `claims_grounding.json`, `paper_data.json`, and `scientific-evidence/verification-report.json`
- every visible claim in Supplementary Information, including tables and figures, under the same grounding standard as the main paper

## Artifact checklist

- `paper.tex` — `present`
- `claims_grounding.json` — `present`
- `paper_data.json` — `present`
- `validation_report.json` — `present`
- `scientific-evidence/verification-report.json` — `present`
- `references_provenance.json` — `present`

## validation report summary

```json
{
  "available": true,
  "evidence_validation": {
    "anchored_references": 132,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 176,
    "resolved_references": 102,
    "total_references": 234
  },
  "ok": true,
  "pdf_path": "work/results/a01/codex/20261107_023211/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 132,
    "dangling_references": 0,
    "manifests_checked": 20,
    "resolved_references": 102,
    "total_references": 234
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "Task investment selects coordinates updated to round10(x+rho(1-x)); positive caps are 1 and 1/2, co-first tolerance is 1e-10, input rounding is 10 decimals.",
      "evidence_locations": [],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "source_evidence/downstream/program/src/program.py:1",
        "source_evidence/downstream/program/src/program.py:260",
        "data/protocol.json"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The rules are arithmetic mean, ordinary median including averaged central values when even, and pairwise Borda with half-credit ties and updated rivals.",
      "evidence_locations": [],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "source_evidence/downstream/program/src/program.py:50",
        "source_evidence/downstream/program/src/program.py:129",
        "source_evidence/downstream/program/src/program.py:193"
      ]
    },
    {
      "citation_keys": [],
      "claim": "HELM MMLU v1.13.0 contributes 57 subject scores and Open LLM contributes six normalized columns, divided by 100, from pinned revision 9c09a7cae43334062a82cb164f2ef255013dafa2; frozen resources record acquisition on 2026-11-07.",
      "evidence_locations": [
        "final.evidence.episodes: original HELM and Open LLM decisions; table dimensions and public provenance are inspectable supplementary resource metadata"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "data/helm.json",
        "data/openllm.json",
        "data/protocol.json",
        "scripts/acquire_scores.py"
      ]
    },
    {
      "citation_keys": [],
      "claim": "There are eight fixed mean-nonwinner rank-spaced targets per score table; three seeds 42011,42013,42017 repeat the same instances; 48 decisions per family, 96 distinct original instances, 288 original records.",
      "evidence_locations": [],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "derived/summary.json",
        "data/protocol.json"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Within any fixed rule and target, increasing rho weakly decreases the minimum budget, including infinity; this does not order different rules. Full-headroom all-task reachability follows structurally from the intervention model.",
      "evidence_locations": [],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "source_evidence/downstream/program/src/program.py:260",
        "source_evidence/downstream/program/src/program.py:193"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 40, 'mean', 1.0): minimum task budget 1; normalized fraction 1/57; independent lower=upper=1; greedy=1; recorded random counts range 1--1.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/0",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/0",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/0"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 40, 'mean', 0.5): minimum task budget 1; normalized fraction 1/57; independent lower=upper=1; greedy=1; recorded random counts range 1--1.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/1",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/1",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/1"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 40, 'median', 1.0): minimum task budget 0; normalized fraction 0/57; independent lower=upper=0; greedy=0; recorded random counts range 0--0.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/2",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/2",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/2"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 40, 'median', 0.5): minimum task budget 0; normalized fraction 0/57; independent lower=upper=0; greedy=0; recorded random counts range 0--0.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/3",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/3",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/3"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 40, 'borda', 1.0): minimum task budget 4; normalized fraction 4/57; independent lower=upper=4; greedy=4; recorded random counts range 15--23.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/4",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/4",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/4"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 40, 'borda', 0.5): minimum task budget 4; normalized fraction 4/57; independent lower=upper=4; greedy=4; recorded random counts range 12--17.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/5",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/5",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/5"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 10, 'mean', 1.0): minimum task budget 9; normalized fraction 9/57; independent lower=upper=9; greedy=9; recorded random counts range 16--23.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/6",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/6",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/6"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 10, 'mean', 0.5): minimum task budget 23; normalized fraction 23/57; independent lower=upper=23; greedy=23; recorded random counts range 38--38.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/7",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/7",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/7"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 10, 'median', 1.0): minimum task budget 12; normalized fraction 12/57; independent lower=upper=12; greedy=12; recorded random counts range 16--18.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/8",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/8",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/8"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 10, 'median', 0.5): minimum task budget 12; normalized fraction 12/57; independent lower=upper=12; greedy=16; recorded random counts range 20--32.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/9",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/9",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/9"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 10, 'borda', 1.0): minimum task budget 34; normalized fraction 34/57; independent lower=upper=34; greedy=34; recorded random counts range 41--47.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/10",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/10",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/10"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 10, 'borda', 0.5): minimum task budget 39; normalized fraction 39/57; independent lower=upper=39; greedy=39; recorded random counts range 46--50.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/11",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/11",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/11"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 37, 'mean', 1.0): minimum task budget 12; normalized fraction 12/57; independent lower=upper=12; greedy=12; recorded random counts range 22--27.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/12",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/12",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/12"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 37, 'mean', 0.5): minimum task budget 36; normalized fraction 36/57; independent lower=upper=36; greedy=36; recorded random counts range 47--49.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/13",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/13",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/13"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 37, 'median', 1.0): minimum task budget 16; normalized fraction 16/57; independent lower=upper=16; greedy=16; recorded random counts range 19--22.",
      "evidence_locations": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/0/solution/cases/0/observations/14",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/1/solution/cases/0/observations/14",
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes/2/solution/cases/0/observations/14"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "tables/budgets.tex",
        "derived/allocations.csv"
      ]
    },
    {
      "citation_keys": [],
      "claim": "('helm', 37, 'medi

[truncated after 14000 chars]
```

## paper_data summary

```json
{
  "available": true,
  "claim_count": 0,
  "downstream_study": {
    "attempt_counts": {
      "scored": 3,
      "total": 3,
      "unscored": 0
    },
    "baseline_program_dir": "work/results/a01/codex/20261107_023211/investigation/.baseline-seed-g14qkd4e/program_0",
    "baseline_score": 0.7239766081871346,
    "baseline_tree_sha256": "3da809dabc5527a111c242e4efcd4621efe41020af5780cf84c4a71d63b1fb63",
    "combined_score": 0.7239766081871346,
    "entrypoint_path": "src/program.py",
    "final_evaluation": {
      "correct": true,
      "outcome": "qualified",
      "status": "completed"
    },
    "investigation_outcome": "completed_no_winner",
    "limitations": [
      "Investigation found no qualifying winner; selection used search evidence only.",
      "Unscored attempts are missing performance evidence, not measured losses.",
      "Search scores and sealed final metrics belong to different evaluation scopes.",
      "An unqualified final outcome may reflect validity or other criteria; do not infer that failure means only an inferior score. Interpret metrics within those limitations."
    ],
    "program_dir": "work/results/a01/codex/20261107_023211/downstream/program",
    "program_tree_sha256": "10c6dac0ab0f2b3f7884ff8316ab5c6ea1e376f8c1ae69ef8868189e5ef2e012",
    "search_score_delta": 0.0,
    "selection_kind": "non_winner_candidate",
    "source_attempt_id": "c01_cap_response_frontiers_attempt_01",
    "source_evidence": {
      "baseline": "source_evidence/downstream/baseline",
      "program": "source_evidence/downstream/program"
    },
    "source_program_dir": "work/results/a01/codex/20261107_023211/investigation/ideas/01_certified_cap_response_frontiers_for_mean_and_median_leaderboards/program_1",
    "source_tree_sha256": "66c3ef2e0cfe1fa4ddcd1629b03dcd8d70e2d2073d5ecfbc557ef2816363e320"
  },
  "final_evaluation": {
    "correct": true,
    "outcome": "qualified",
    "status": "completed"
  },
  "grounding_source_count": 26,
  "paper_profile": "standalone",
  "totals": {
    "attempts": 3,
    "correct_programs": 3,
    "evaluated_programs": 3,
    "ideas": 3
  }
}
```

## references provenance summary

```json
{
  "excluded_initial_records": "Off-topic initial metadata hits were not retained. Unavailable-content classics omitted. Incorrect DOI candidate for bribery was discarded after title mismatch; no substantive claim uses it.",
  "references": [
    {
      "citation_key": "Hendrycks2020MMLU",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Hendrycks2020MMLU.opening.txt",
      "id": "ref.exact.Hendrycks2020MMLU",
      "metadata_path": "literature/Hendrycks2020MMLU.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.088113+00:00",
      "source_url": "https://arxiv.org/abs/2009.03300",
      "title": "Measuring Massive Multitask Language Understanding",
      "year": 2020
    },
    {
      "citation_key": "Suzgun2022BBH",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Suzgun2022BBH.opening.txt",
      "id": "ref.exact.Suzgun2022BBH",
      "metadata_path": "literature/Suzgun2022BBH.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.105557+00:00",
      "source_url": "https://arxiv.org/abs/2210.09261",
      "title": "Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them",
      "year": 2022
    },
    {
      "citation_key": "Liang2022HELM",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Liang2022HELM.opening.txt",
      "id": "ref.exact.Liang2022HELM",
      "metadata_path": "literature/Liang2022HELM.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.157804+00:00",
      "source_url": "https://arxiv.org/abs/2211.09110",
      "title": "Holistic Evaluation of Language Models",
      "year": 2022
    },
    {
      "citation_key": "Dehghani2021Lottery",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Dehghani2021Lottery.opening.txt",
      "id": "ref.exact.Dehghani2021Lottery",
      "metadata_path": "literature/Dehghani2021Lottery.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.176534+00:00",
      "source_url": "https://arxiv.org/abs/2107.07002",
      "title": "The Benchmark Lottery",
      "year": 2021
    },
    {
      "citation_key": "Lanctot2023SocialChoice",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Lanctot2023SocialChoice.opening.txt",
      "id": "ref.exact.Lanctot2023SocialChoice",
      "metadata_path": "literature/Lanctot2023SocialChoice.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.196724+00:00",
      "source_url": "https://arxiv.org/abs/2312.03121",
      "title": "Evaluating Agents using Social Choice Theory",
      "year": 2023
    },
    {
      "citation_key": "Singh2025Illusion",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Singh2025Illusion.opening.txt",
      "id": "ref.exact.Singh2025Illusion",
      "metadata_path": "literature/Singh2025Illusion.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.216006+00:00",
      "source_url": "https://arxiv.org/abs/2504.20879",
      "title": "The Leaderboard Illusion",
      "year": 2025
    },
    {
      "citation_key": "Zhou2023Cheater",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Zhou2023Cheater.opening.txt",
      "id": "ref.exact.Zhou2023Cheater",
      "metadata_path": "literature/Zhou2023Cheater.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.233361+00:00",
      "source_url": "https://arxiv.org/abs/2311.01964",
      "title": "Don't Make Your LLM an Evaluation Benchmark Cheater",
      "year": 2023
    },
    {
      "citation_key": "Yang2023Rephrased",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Yang2023Rephrased.opening.txt",
      "id": "ref.exact.Yang2023Rephrased",
      "metadata_path": "literature/Yang2023Rephrased.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.242552+00:00",
      "source_url": "https://arxiv.org/abs/2311.04850",
      "title": "Rethinking Benchmark and Contamination for Language Models with Rephrased Samples",
      "year": 2023
    },
    {
      "citation_key": "Chen2026Strategic",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Chen2026Strategic.opening.txt",
      "id": "ref.exact.Chen2026Strategic",
      "metadata_path": "literature/Chen2026Strategic.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.253834+00:00",
      "source_url": "https://arxiv.org/abs/2603.08371",
      "title": "Leaderboard Incentives: Model Rankings under Strategic Post-Training",
      "year": 2026
    },
    {
      "citation_key": "Dodge2019Reporting",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Dodge2019Reporting.opening.txt",
      "id": "ref.exact.Dodge2019Reporting",
      "metadata_path": "literature/Dodge2019Reporting.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.276065+00:00",
      "source_url": "https://arxiv.org/abs/1909.03004",
      "title": "Show Your Work: Improved Reporting of Experimental Results",
      "year": 2019
    },
    {
      "citation_key": "Gao2023Harness",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Gao2023Harness.abstract.txt",
      "id": "ref.exact.Gao2023Harness",
      "metadata_path": "literature/Gao2023Harness.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.276718+00:00",
      "source_url": "https://doi.org/10.5281/zenodo.5371628",
      "title": "A framework for few-shot language model evaluation",
      "year": 2021
    },
    {
      "citation_key": "Brandt2016Handbook",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Brandt2016Handbook.abstract.txt",
      "id": "ref.exact.Brandt2016Handbook",
      "metadata_path": "literature/Brandt2016Handbook.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.277212+00:00",
      "source_url": "https://doi.org/10.1017/cbo9781107446984",
      "title": "Handbook of Computational Social Choice",
      "year": 2016
    },
    {
      "citation_key": "Gibbard1973Manipulation",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Gibbard1973Manipulation.abstract.txt",
      "id": "ref.exact.Gibbard1973Manipulation",
      "metadata_path": "literature/Gibbard1973Manipulation.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.277774+00:00",
      "source_url": "https://doi.org/10.2307/1914083",
      "title": "Manipulation of Voting Schemes: A General Result",
      "year": 1973
    },
    {
      "citation_key": "Huber1964Robust",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Huber1964Robust.abstract.txt",
      "id": "ref.exact.Huber1964Robust",
      "metadata_path": "literature/Huber1964Robust.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.279438+00:00",
      "source_url": "https://doi.org/10.1214/aoms/1177703732",
      "title": "Robust Estimation of a Location Parameter",
      "year": 1964
    },
    {
      "citation_key": "Hampel1974Influence",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Hampel1974Influence.abstract.txt",
      "id": "ref.exact.Hampel1974Influence",
      "metadata_path": "literature/Hampel1974Influence.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.279890+00:00",
      "source_url": "https://doi.org/10.1080/01621459.1974.10482962",
      "title": "The Influence Curve and Its Role in Robust Estimation",
      "year": 1974
    },
    {
      "citation_key": "Faliszewski2009Bribery",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Faliszewski2009Bribery.abstract.txt",
      "id": "ref.exact.Faliszewski2009Bribery",
      "metadata_path": "literature/Faliszewski2009Bribery.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.280381+00:00",
      "source_url": "https://doi.org/10.1613/jair.2676",
      "title": "How Hard Is Bribery in Elections?",
      "year": 2009
    },
    {
      "citation_key": "Nemhauser1978Submodular",
      "consultation_scope": "opening pages and abstract; no citation links followed",
      "content_path": "literature/Nemhauser1978Submodular.opening.txt",
      "id": "ref.exact.Nemhauser1978Submodular",
      "metadata_path": "literature/Nemhauser1978Submodular.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.292298+00:00",
      "source_url": "https://doi.org/10.1007/bf01588971",
      "title": "An analysis of approximations for maximizing submodular set functions\u2014I",
      "year": 1978
    },
    {
      "citation_key": "Hoeffding1963Bounds",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Hoeffding1963Bounds.abstract.txt",
      "id": "ref.exact.Hoeffding1963Bounds",
      "metadata_path": "literature/Hoeffding1963Bounds.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.292693+00:00",
      "source_url": "https://doi.org/10.1080/01621459.1963.10500830",
      "title": "Probability Inequalities for Sums of Bounded Random Variables",
      "year": 1963
    },
    {
      "citation_key": "Efron1979Bootstrap",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Efron1979Bootstrap.abstract.txt",
      "id": "ref.exact.Efron1979Bootstrap",
      "metadata_path": "literature/Efron1979Bootstrap.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.293074+00:00",
      "source_url": "https://doi.org/10.1214/aos/1176344552",
      "title": "Bootstrap Methods: Another Look at the Jackknife",
      "year": 1979
    },
    {
      "citation_key": "Dwork2001Rank",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Dwork2001Rank.abstract.txt",
      "id": "ref.exact.Dwork2001Rank",
      "metadata_path": "literature/Dwork2001Rank.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.293449+00:00",
      "source_url": "https://doi.org/10.1145/371920.372165",
      "title": "Rank aggregation methods for the Web",
      "year": 2001
    },
    {
      "citation_key": "Rousseeuw1984Median",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Rousseeuw1984Median.abstract.txt",
      "id": "ref.exact.Rousseeuw1984Median",
      "metadata_path": "literature/Rousseeuw1984Median.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.293825+00:00",
      "source_url": "https://doi.org/10.1080/01621459.1984.10477105",
      "title": "Least Median of Squares Regression",
      "year": 1984
    },
    {
      "citation_key": "Bertsimas2004Price",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Bertsimas2004Price.abstract.txt",
      "id": "ref.exact.Bertsimas2004Price",
      "metadata_path": "literature/Bertsimas2004Price.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.294235+00:00",
      "source_url": "https://doi.org/10.1287/opre.1030.0065",
      "title": "The Price of Robustness",
      "year": 2004
    },
    {
      "citation_key": "Bertsimas2011Theory",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/Bertsimas2011Theory.abstract.txt",
      "id": "ref.exact.Bertsimas2011Theory",
      "metadata_path": "literature/Bertsimas2011Theory.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.294662+00:00",
      "source_url": "https://doi.org/10.1137/080734510",
      "title": "Theory and Applications of Robust Optimization",
      "year": 2011
    },
    {
      "citation_key": "BenTal1998Robust",
      "consultation_scope": "substantive abstract supplied by OpenAlex; no full-text claim",
      "content_path": "literature/BenTal1998Robust.abstract.txt",
      "id": "ref.exact.BenTal1998Robust",
      "metadata_path": "literature/BenTal1998Robust.metadata.json",
      "retrieved_at": "2026-11-07T04:45:51.295127+00:00",
      "source_url": "https://doi.org/10.1287/moor.23.4.769",
      "title": "Robust Convex Optimization",
      "year": 1998
    },
    {
      "citation_key": "Demsar2006Comparisons",
      "consultation_scope": "opening pages and abstract",
      "content_path": "literature/Demsar2006Comparisons.opening.txt",
      "id": "ref.exact.Demsar2006Comparisons",
      "retrieved_at": "2026-11-07T04:45:51.302935+00:00",
      "source_url": "https://jmlr.org/papers/v7/demsar06a.html",
      "title": "Statistical Comparisons of Classifiers over Multiple Data Sets",
      "year": 2006
    }
  ],
  "retrieval_policy": "Exact task-allowed identifiers, exact pre-2010 titles to repair mismatched identifiers, and exact foundational DOI endpoints only. No citation-graph traversal or related-content expansion."
}
```

## manuscript source excerpt

```tex
\documentclass{article}

\usepackage{xcolor}
\usepackage{xfp}
\usepackage{draftwatermark}
\newlength{\watermarkTextWidth}
\AddToHook{begindocument/end}{
  \SetWatermarkText{\normalfont Generated by The Agentic Scientist}
  \SetWatermarkFontSize{10pt}
  \SetWatermarkLightness{0.85}
  \settowidth{\watermarkTextWidth}{\normalfont\fontsize{10pt}{12pt}\selectfont Generated by The Agentic Scientist}
  \edef\watermarkScale{\fpeval{0.8 * sqrt(\paperwidth**2 + \paperheight**2) / \watermarkTextWidth}}
  \edef\watermarkAngle{\fpeval{atand(\paperheight/\paperwidth)}}
  \SetWatermarkScale{\watermarkScale}
  \SetWatermarkAngle{\watermarkAngle}
}


\usepackage{iclr2026_conference,times}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,booktabs,graphicx,longtable,subcaption}
\usepackage{hyperref,url}
\title{Cap-Dependent Task Budgets for Leaderboard Promotion}
\newcommand{\budget}{B}
\newcommand{\tol}{\varepsilon}
\begin{document}
\maketitle

\begin{abstract}
Multitask leaderboards aggregate heterogeneous scores, creating incentives to improve selected benchmark tasks rather than broad capability. How much targeted investment is needed to reach the top, and does the answer depend on the aggregation rule? We study a static score-space model: investment selects tasks, each selected score receives a bounded fraction of its remaining headroom, and competitors remain fixed. We compare arithmetic mean, ordinary median, and pairwise Borda aggregation on public HELM MMLU and Open LLM score snapshots. Independently checked allocation bounds reveal cap-dependent reversals: for one HELM target, mean versus median budgets change from 9 versus 12 tasks at full headroom to 23 versus 12 at half headroom; an Open LLM target exhibits the same qualitative reversal. Some promotions become unattainable under the smaller cap. These results reject a cap-independent resistance ordering on the evaluated instances. They quantify conditional score-space vulnerability, not the training data, compute, or money needed to realize such changes.


\end{abstract}

\section{Introduction}
Public multitask benchmarks compress a model's performance profile into a leaderboard position. MMLU and BIG-Bench Hard exemplify evaluations with heterogeneous component tasks, while HELM emphasizes transparency and breadth of evaluation \citep{Hendrycks2020MMLU,Suzgun2022BBH,Liang2022HELM}. Once adoption and recognition depend on position, a developer may have an incentive to concentrate resources on a subset of benchmark tasks. A leaderboard's aggregation rule determines which score changes are rewarded. Evaluating that incentive requires specifying both the allowed changes and the meaning of investment.

We ask a deliberately conditional question: on a fixed public score table, what is the smallest task subset whose improvement would make a target model co-first? Investment is the number of selected tasks, not the amount of training data. Each selected coordinate receives a stipulated fraction of its remaining score headroom; every unselected coordinate and every competitor's coordinate stays fixed. This model separates a leaderboard's response to score changes from the unresolved question of how reliably training can produce those changes. It is an analysis of a possible response envelope, not evidence that a developer can realize the envelope.

A common intuition is that the median should resist concentrated improvements because isolated extreme scores need not affect its value. That intuition does not settle the relative cost of reaching the top. A mean rewards every increment, whereas a median depends on crossing order-statistic thresholds. Reducing the permitted increment can change which threshold crossings remain available without proportionally changing the median's task budget. Conversely, a low starting median can require many changes even when a mean responds cheaply. The relevant object is therefore a budget conditioned jointly on the target, aggregation rule, and response cap.

Our study makes three concrete contributions. It defines a common bounded intervention model for mean, median, and Borda; expresses scalar allocation through sorting or threshold certificates and Borda through rival-aware integer constraints; and reports paired budgets, unattainability, and matched comparator results on frozen public score tables. The central finding is not a universally preferable aggregation rule. The same-target mean--median ordering reverses when the cap changes in both evaluated settings. Reference bounds and explicit failure states make that conclusion auditable without interpreting a timeout as impossibility.

The study is intentionally narrower than a strategic training equilibrium. Competitors do not react, task costs are uniform, and no model is trained. These restrictions preserve an interpretable comparison but preclude claims about real resource expenditure, general capability, or a population-wide frequency of reversal. The full target panel, including targets already co-first under a different rule, is retained rather than filtering to favorable examples.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/score_space_overview.png}
\caption{The score-space intervention model. A fixed public score table and target define the comparison. Selecting tasks raises only the target's selected coordinates to a specified headroom cap. Mean, ordinary median, and rival-aware Borda yield a minimum task budget or certified unattainability. The cap describes a hypothetical response, not a measured training effect.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\paragraph{Evaluation design and incentives.}
The benchmark lottery shows that task selection can alter comparative conclusions \citep{Dehghani2021Lottery}. Here the task set stays fixed while the aggregation rule and permitted response change. HELM's multidimensional evaluation and the language-model evaluation harness motivate explicit task definitions and reproducible score processing \citep{Liang2022HELM,Gao2023Harness}; our computations use released scores rather than rerunning either evaluation system. Analyses of leaderboard incentives and selective evaluation provide complementary reasons not to equate rank with general capability \citep{Singh2025Illusion}. Strategic post-training has also been modeled as an interaction between a benchmark designer and competing developers \citep{Chen2026Strategic}. We instead hold rivals fixed and measure discrete promotion budgets, without estimating an equilibrium or latent quality.

\paragraph{Social choice and targeted changes.}
Treating tasks as voters connects model evaluation with social choice \citep{Lanctot2023SocialChoice,Brandt2016Handbook}; aggregating rankings is also a classical information-retrieval problem \citep{Dwork2001Rank}. Strategic preference reporting \citep{Gibbard1973Manipulation} and election bribery \citep{Faliszewski2009Bribery} establish useful distinctions between aggregation and manipulation. Our intervention changes only a target's numerical task coordinates, according to a fixed response cap. It cannot arbitrarily rewrite rankings or remove competitors. In particular, a Borda calculation must update rivals as the target overtakes them, rather than compare against frozen Borda totals.

\paragraph{Robustness and contamination.}
Classical robust estimation distinguishes local influence from resistance under a specified contamination model \citep{Huber1964Robust,Hampel1974Influence,Rousseeuw1984Median}. These distinctions caution against importing a slogan about median robustness into an adaptive, bounded, top-rank objective. Our coordinates are heterogeneous tasks, not independent observations of a common location parameter. Benchmark leakage and rephrased contamination can affect measured model performance \citep{Zhou2023Cheater,Yang2023Rephrased}, but those findings do not calibrate our headroom response. We neither identify contaminated models nor infer that task-specific data necessarily produces the score increments analyzed here. The contribution is an instance-level comparison under stated assumptions, not a claim of first priority over all work on strategic evaluation.

\section{Method}
\subsection{Problem setup and intervention model}
Let $X\in[0,1]^{n\times d}$ contain higher-is-better task scores, with target row $t$ and original target vector $x=X_t$. For a selected task set $S\subseteq\{1,\ldots,d\}$ and cap $\rho$, define
\begin{equation}
 u_j(\rho)=\operatorname{round}_{10}\!\left(x_j+\rho(1-x_j)\right),\qquad
 y_j(S,\rho)=\begin{cases}u_j(\rho),&j\in S,\\x_j,&j\notin S.\end{cases}
 \label{eq:response}
\end{equation}
The evaluated positive caps are $\rho=1$ and $\rho=1/2$. Input scores and endpoints are rounded to ten decimal places. A separate no-update control uses zero response. Task selection is the decision variable; the cap is an externally specified condition, not a fitted learning curve. Figure~\ref{fig:overview} summarizes this distinction.



Write $A_r(i;X)$ for row $i$'s aggregate under rule $r$, and $X^{t\leftarrow y}$ for the modified table. Promotion means co-first within tolerance $\tol=10^{-10}$:
\begin{equation}
 A_r(t;X^{t\leftarrow y})\geq \max_{i\ne t} A_r(i;X^{t\leftarrow y})-\tol.
 \label{eq:success}
\end{equation}
We minimize the uniform investment
\begin{equation}
 \budget_r(t,\rho)=\min_S\{|S|:\text{Equation~\eqref{eq:success} holds}\},
 \qquad b_r(t,\rho)=\budget_r(t,\rho)/d.
 \label{eq:objective}
\end{equation}
If no subset succeeds, $\budget_r=\infty$. An empty successful subset has budget zero; an empty response reporting unattainability does not. Co-first is weaker than strict victory, and the results do not address arbitrary tie-breaking policies.


\subsection{Design rationale and compared approaches}
We compare arithmetic mean, ordinary median, and pairwise Borda on identical targets and endpoints. The even median averages the two central order statistics. Borda awards one point for a task-level pairwise win and half a point for a tie, then averages across opponents and tasks:
\begin{equation}
 A_{\mathrm{B}}(i;X)=\frac{1}{d(n-1)}\sum_{j=1}^{d}\sum_{h\ne i}
 \left[\mathbf{1}\{X_{ij}>X_{hj}\}+\tfrac12\mathbf{1}\{X_{ij}=X_{hj}\}\right].
 \label{eq:borda}
\end{equation}
Changing the target can lower a rival's Borda total even though the rival's underlying task scores are unchanged.


The hypothesis is conditional: the ordering of task budgets need not survive a change in cap. This follows mechanistically from distinct sufficient statistics. Mean uses total added score mass; median uses central threshold crossings; Borda uses pairwise crossings against the whole competitor population. None of these mechanisms implies the same ranking of investment costs on every target vector.

There is nevertheless a simple within-rule restriction. Holding the table and target fixed, a larger cap weakly expands the set of successful subsets. Thus, with infinity ordered above finite budgets,
\begin{equation}
 \rho_1\leq\rho_2\quad\Longrightarrow\quad
 \budget_r(t,\rho_1)\geq\budget_r(t,\rho_2).
 \label{eq:monotone}
\end{equation}
This implication follows from the same target--rival monotonicity used by the endpoint test. It does not order different rules: their budgets may increase by different amounts when the cap shrinks. Observing a reversal between rules therefore does not contradict monotonicity of either rule's own budget. This separation distinguishes the proposed comparison from an assertion that a smaller permitted improvement can make promotion cheaper.



Allocation methods are compared with no intervention, marginal greedy selection, and a seeded random task order evaluated by successive prefixes. Marginal greedy chooses the task producing the largest current improvement in the target's gap to its strongest rival, with deterministic task-order ties. A random order is drawn for each decision, not optimized over many orders. These are selection policies under the same response model, not alternative training procedures. The original development comparator uses exhaustive allocation on small tables and greedy allocation otherwise; its selection score does not supply a matched final population comparison.




\subsection{Scalar allocation certificates}
For mean and median, competitors' aggregates stay fixed. Let $c_r=\max_{i\ne t}A_r(i;X)$. Raising selected coordinates to their endpoints cannot reduce any studied aggregate or worsen any target--rival gap. Thus the all-task endpoint vector certifies reachability: if it cannot win, no subset can. Conversely, because selected tasks have unit cost and no penalty for a larger allowed response, endpoint updates suffice for the stated optimization problem.

For the mean, let $g_j=u_j-x_j$, and sort gains decreasingly as $g_{(1)}\geq\cdots\geq g_{(d)}$. The minimum finite budget is the smallest $k$ satisfying
\begin{equation}
 \sum_{\ell=1}^{k} g_{(\ell)}\geq d\bigl(c_{\mathrm{mean}}-\tol-\bar{x}\bigr).
 \label{eq:mean}
\end{equation}
No other $k$ tasks can supply more gain, giving a cardinality certificate rather than just a successful witness.


For odd $d=2m+1$, median success requires at least $m+1$ coordinates at or above $c_{\mathrm{median}}-\tol$. Count those already above that threshold, then count coordinates whose endpoint crosses it. The required number of crossings gives the minimum if enough are available. For even $d=2m$, success depends on the sum of the two central values, not a single threshold. The solver enumerates candidate lower central endpoints and the smallest compatible upper endpoint. It checks the nested requirements of at least $m+1$ values above the lower endpoint and at least $m$ above the upper endpoint, sharing upgrades where possible. Final aggregate checks protect the numerical boundary. The small even-dimensional setting also uses exhaustive subset verification. Appendix~\ref{sec:scalar} gives the counting construction.




\subsection{Rival-aware Borda allocation}
Use twice-credit integer totals $T_i=2d(n-1)A_{\mathrm{B}}(i;X)$. Let $\delta_{ij}\in\{0,1,2\}$ be the increase in the target's twice-credit against rival $i$ on task $j$, and $G_j=\sum_{i\ne t}\delta_{ij}$. Selecting task $j$ increases the target's total by $G_j$ and decreases rival $i$'s total by $\delta_{ij}$. With binary task indicators $z_j$, the necessary and sufficient constraints are
\begin{equation}
 \sum_j (G_j+\delta_{ij})z_j\geq D_i,
 \quad D_i=\left\lceil T_i-T_t-2d(n-1)\tol\right\rceil,
 \quad i\ne t.
 \label{eq:cover}
\end{equation}
Only initially positive deficits constrain the solution, since all gap improvements are nonnegative. This formulation accounts for changing rival totals explicitly.


The supplied selected source builds a feasible gain-ordered prefix, deletes unnecessary tasks, and searches smaller cardinalities using individual-rival bounds and suffix pruning. Search is bounded by a deadline and a node limit; on interruption it returns a verified incumbent, not an optimality assertion. In the recorded original instances, independent reference bounds close and match every finite returned cardinality. That observed agreement is stronger than a feasible-witness check, but it does not establish exactness for arbitrary larger instances or superiority of a particular search component. No controlled component ablation is available.



\section{Public Score Tables and Comparison Protocol}
\paragraph{Snapshots and preprocessing.}
The study uses HELM's MMLU release v1.13.0 and the pinned Open LLM contents snapshot, acquired on 7 November 2026. HELM contributes 57 subject scores; Open LLM contributes six normalized leaderboard columns: IFEval, BBH, MATH Lvl 5, GPQA, MuSR, and MMLU-PRO. Open LLM scores are divided by 100; its additional raw columns are not treated as independent tasks. The comparison recomputes all three aggregation rules from these component scores. It is not a claim about the live ordering displayed by either website.





Score content and known model aliases are clustered before a deterministic content-based split separates development from final analysis. Exact duplicates are collapsed; normalization is applied after assignment. The frozen final competitor tables, not just the selected targets, determine every comparison. Known alias matching reduces exact overlap but cannot establish unseen-model-family independence because lineage information is incomplete. Appendix~\ref{sec:repro} specifies versions, hashes, and the acquisition code.

\paragraph{Targets and matched comparisons.}
Each final score table has eight fixed targets, selected at rank-spaced positions among nonwinners under its original arithmetic mean. Target selection is not repeated separately for each rule. Consequently, a target can already be co-first under median or Borda. We retain such zero-budget cases. Each target is assessed under every rule at both positive caps, keeping all other inputs fixed. Target labels are frozen row indices, not model-family categories.



The records contain three seeded executions, with seeds 42011, 42013, and 42017, of the same target instances. There are 48 distinct target--rule--cap decisions per score table. Independent validation recomputes aggregate success and checks the reference bounds. The reference uses exhaustive subsets for the six-task table, sorting or threshold counting for scalar rules on HELM, and a time-limited binary optimization reference for HELM Borda. We report a finite optimum only where a valid witness and matching lower and upper bounds are recorded; unresolved optimization would remain a bound interval. Independently certified unattainability is kept separate from missing or failed computation.



\paragraph{Checks and uncertainty.}
Task permutations, constant-score tables, and zero-update controls test implementation behavior and are excluded from the empirical target denominator. A recorded reset replay checks a repeated status/effort signature. Repeated seeds do not resample tasks or models. We therefore report deterministic paired differences and observed repeatability, not confidence intervals for an unspecified population. The random comparator's range reflects only its recorded orders. No statistical test is used to turn these fixed-panel counterexamples into a universal rule ranking.

\section{Results: Cap-Dependent Promotion Budgets}
\subsection{Within-target reversals}
Table~\ref{tab:budgets} reports every original target. Figure~\ref{fig:paired} places the mean and median budgets on common normalized axes. Points above the diagonal require more tasks under median; points below it require more under mean. The shaded rails retain unattainable cases rather than assigning them an artificial large finite budget. Multiplicities are explicit, and seeded repeats are not plotted as independent targets.

For HELM target 10, the mean/median budgets are 9/12 tasks at full headroom and 23/12 at half headroom. For Open LLM target 1609, they are 2/3 and 4/3, respectively. Thus the direction of the same-target comparison reverses in both score tables. These examples refute a cap-independent ordering on these instances; they do not estimate how frequently such reversals occur among future models.



The reversal is interpretable without attributing it to training. Smaller increments reduce the total gain available to the mean, requiring additional coordinates. The median can retain its task count when the necessary endpoint threshold crossings remain possible. HELM targets 37, 18, and 28 exhibit unchanged median counts across the two caps while their mean counts increase. This is a property of their observed score geometry under the stipulated response, not a claim that median is insensitive to cap changes in general. HELM target 40 already has median budget zero at both caps despite being a mean-selected nonwinner.


\begin{table}[t]
\centering\small
\caption{Minimum selected-task counts on all original targets. $\infty$ means unattainable under the stated cap. Every finite count matches a closed independent reference bound in each recorded seeded execution. Task counts are within-snapshot investments, not calibrated training costs.}
\label{tab:budgets}
\input{tables/budgets.tex}
\end{table}

\begin{figure}[t]
\centering
\begin{subfigure}{\textwidth}
\centering\includegraphics[width=\textwidth]{figures/paired_mean_median_budgets.pdf}
\end{subfigure}
\caption{Paired minimum task fractions for identical targets. Top: HELM; bottom: Open LLM. Left: full headroom; right: half headroom. NA rails indicate certified unattainability, not missing values or an additional numeric range. Annotated row indices identify targets that reverse their mean--median ordering. Labels $\times k$ denote coincident target points. All finite points have matching independent lower and upper cardinality bounds.}
\label{fig:paired}

\end{figure}

\subsection{Reachability and Borda}
At full headroom, all eight targets in each table are reachable under all three rules. This is expected structurally: selecting every coordinate sets the target to the scale maximum. The informative full-headroom quantity is therefore the minimum task budget, not reachability alone. At half headroom, HELM has five reachable targets under mean, five under median, and four under Borda; Open LLM has seven, six, and three. Figure~\ref{fig:reachability} uses the same target denominator throughout. An all-task cap that fails the rank condition certifies these unattainable cases. Such a result is a limit of the intervention model, not evidence of an unsuccessful training run or a solver timeout.


Borda can require a large selected subset because improving a task matters through the rival crossings it enables. For Open LLM target 1566, full-headroom Borda requires all six tasks, but half-headroom Borda is unattainable; mean and median remain reachable with four tasks at half headroom. HELM target 28 is also unreachable under half-headroom Borda while mean and median remain reachable. These are comparisons between precisely defined rule-and-cap configurations. They do not isolate a causal benefit of ordinal aggregation, since the aggregation objective itself changes.


\begin{figure}[t]
\centering
\begin{subfigure}{\textwidth}
\centering\includegraphics[width=\textwidth]{figures/cap_conditioned_reachability.pdf}
\end{subfigure}
\caption{Reachable original targets out of eight, by aggregation rule and response cap. The denominator excludes seeded repeats and synthetic controls. Reachability means co-first under the cap, not general model improvement. All full-headroom cases are reachable; half-headroom failures differ by rule and score table.}
\label{fig:reachability}

\end{figure}

\subsection{Allocation checks and comparator interpretation}
Across the original decisions, all recorded reference intervals close. Every finite selected cardinality equals its reference minimum, and every reported unattainable decision agrees with the independent reference. The selected task subsets are identical across the three seeds, not merely equal in size. These observations support the precision of the reported finite-instance comparisons, not a claim about unrestricted solver completeness.


Marginal greedy matches the minimum on the recorded feasible mean and Borda decisions. It can miss median budgets because immediate marginal changes do not necessarily reward the threshold crossings needed for eventual promotion. For HELM target 28 at half headroom, the certified median minimum is 21 tasks, compared with 52 for the recorded greedy policy. This gap concerns a selection policy on that instance; no ablation identifies which internal solver component accounts for it. Nor is it a general advantage over the original development comparator: the frozen selection had no aggregate development-score improvement over that comparator. Matched random-order costs and all selected subsets are supplied in the supplement and machine-readable records.




\section{Discussion and Limitations}
\paragraph{What the investment measures.}
A task count measures concentration of intervention support. It does not measure examples, tokens, training steps, compute, or money. The response in Equation~\eqref{eq:response} is hypothetical and favorable: all selected improvements are jointly available, improvements do not spill into unselected tasks, and no forgetting occurs. Real training can violate every condition. A smaller task budget can therefore coexist with a larger real training cost. The empirical conclusions apply only to the stated score response, uniform task costs, and fixed competitors.

\paragraph{Why rule robustness is conditional.}
Median robustness in a location-estimation problem does not by itself determine the cost of overtaking a particular competitor. Here the objective is relative rank, and the target's starting position matters. Borda additionally depends on the whole competitor population; mean and median depend on their respective strongest rival aggregate. A change in the competitor set or task composition could change the comparisons. The analysis holds those objects fixed, rather than selecting a favorable population for each rule. Normalizing by task count enables a visual comparison but does not make selecting a subject equivalent in practical effort to selecting an entire benchmark.

\paragraph{Coverage and uncertainty.}
The paired design identifies cap sensitivity on the observed instances, not how common the phenomenon is beyond them. Targets are mean-rank stratified rather than a random model sample. The two score snapshots share an evaluation ecosystem and can include related model lineages. Hash and alias separation does not establish independence of model development or broad transfer. Only two positive caps were evaluated; the figures are discrete comparisons, not continuous response frontiers. No composition resampling, strict-victory sensitivity, heterogeneous-cost study, or empirical training-response calibration is available. These omissions constrain generalization but do not invalidate the displayed within-target counterexamples.


\paragraph{Computation and scientific scope.}
A feasible witness alone would not certify a minimum; a time limit alone would not certify impossibility. We preserve both distinctions. Bound closure happens to support exact cardinalities on the recorded original instances, although Borda search is bounded in the implementation. The separate final assessment is completed and qualified; that status neither establishes novelty nor enlarges the scope of the scientific conclusions. The development comparison has no positive aggregate difference, and no component ablation supports a claim of optimizer superiority. Public availability of score files also does not settle their redistribution rights; the reproduction instructions preserve upstream provenance and describe reacquisition rather than assuming a code or model license covers score data.




\section{Conclusion}
Targeted leaderboard promotion has no meaningful task budget until both the aggregation rule and the allowed score response are specified. Under a bounded headroom model on two frozen public score tables, paired minimum budgets reverse their mean--median ordering for some targets when the cap is reduced. Reachability also changes by rule, including cases where using every task is insufficient. The evidence supports these finite-instance, conditional conclusions rather than a universal ranking of aggregation rules.

The practical implication is methodological: report the target score vector, response assumptions, competitor population, success criterion, and allocation bounds together. A single aggregate vulnerability score hides distinctions between inexpensive promotion, already being co-first, and promotion that is impossible under the cap. Extending this analysis to real resource allocation requires evidence linking training investments to joint score changes and their side effects. Until such calibration is available, task-count budgets are interpretable counterfactual diagnostics, not estimates of the cost of producing a better model.

\clearpage
\bibliography{references}
\bibliographystyle{iclr2026_conference}
\clearpage
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}

\subsection{Endpoint reduction and scalar certificates}\label{sec:scalar}
For each rule, increasing only a target coordinate weakly improves every target--rival gap. For mean and median this follows from coordinatewise monotonicity with unchanged rival aggregates. For Borda, the target gains pairwise credit while any overtaken rival loses the corresponding credit. Consequently, if the all-task endpoint vector is unsuccessful, every subset is unsuccessful. If a selected task could instead receive any intermediate increase below its endpoint at the same unit cost, replacing it by its endpoint cannot destroy success. This endpoint reduction does not apply when improvements incur magnitude-dependent costs, adversely affect other coordinates, or provoke responding rivals.

For mean, the largest-gain prefix maximizes added score over subsets of a fixed size, proving Equation~\eqref{eq:mean}. For odd median, put $h=c_{\mathrm{median}}-\tol$, $a=\#\{j:x_j\geq h\}$, and $p=\#\{j:x_j<h\leq u_j\}$. With $d=2m+1$, the finite minimum is $k=\max(0,m+1-a)$ if $k\leq p$, and is otherwise unattainable. This is a threshold count, not a local derivative of the median.



For the even median, let $d=2m$ and let $\mathcal{E}=\{x_j,u_j:j=1,\ldots,d\}$ be the set of endpoints. Enumerate $\ell\in\mathcal{E}$ and choose the smallest $h\in\mathcal{E}$ with $h\geq\ell$ and $(\ell+h)/2\geq c_{\mathrm{median}}-\tol$. At least $m+1$ coordinates must be at least $\ell$, and at least $m$ must be at least $h$. Set
\[
 a_\ell=\max(0,m+1-\#\{x_j\geq\ell\}),\qquad
 a_h=\max(0,m-\#\{x_j\geq h\}).
\]
Partition available upgrades into shared crossings $x_j<\ell,\ u_j\geq h$, lower-only crossings $x_j<\ell\leq u_j<h$, and upper-only crossings $\ell\leq x_j<h\leq u_j$. Shared crossings cover both deficits; the other two types cover one each. If either deficit exceeds its total available crossings, discard the endpoint pair. Otherwise use shared crossings up to the larger deficit and fill remaining deficits from their dedicated types. Checking the resulting median and taking the smallest cardinality over endpoints yields the implemented construction. For a fixed lower endpoint, increasing the upper threshold only shrinks feasible choices, so the smallest compatible upper endpoint suffices. On the six-task table, exhaustive verification also checks scalar cardinalities. These are explanations of the inspected implementation, not additional experimental findings.



\subsection{Borda constraints and bounded search}
Equation~\eqref{eq:cover} follows by subtracting the updated rival total $T_i-\sum_j\delta_{ij}z_j$ from the updated target total $T_t+\sum_jG_jz_j$. Integer ceiling converts the aggregate tolerance to a gap constraint. Every coefficient is nonnegative, so initially nonthreatening rivals stay nonthreatening. Full-cap failure of any constraint certifies unattainability. A feasible subset is always checked against the complete active-rival constraints, not just the reduced search system.

Let $D=\max_iD_i$ and let $U$ be the current feasible cardinality. For a subset with at most $U$ tasks, the rival-specific contribution is bounded by $2U$. Satisfying the largest deficit therefore requires common gain at least $D-2U$. Rivals with deficit at most that value can safely be omitted during improvement search. Zero-common-gain tasks do not help. Independent-rival sorted coefficient sums give lower cardinality bounds. Branch search prunes a node if the largest remaining coefficients for any rival cannot cover its residual deficit within the remaining task slots. Its node limit is 20,000; the solver uses 90\% of the supplied work allowance and divides remaining time among pending Borda decisions. These are source settings, not measured speedups.




There is no assertion of a generic greedy approximation guarantee: guarantees for submodular maximization require specific objective and constraint assumptions \citep{Nemhauser1978Submodular}. Nor is this a robust optimization problem that optimizes against a calibrated uncertainty set. Robust optimization provides a different treatment of uncertain coefficients and conservatism \citep{BenTal1998Robust,Bertsimas2004Price,Bertsimas2011Theory}. Our response cap is fixed for each conditional comparison. It is not a distributional estimate, a worst-case set learned from interventions, or a guarantee about actual score changes.

\subsection{Complete allocation and comparator tables}
Tables below contain all original target--rule--cap combinations. Selected minima and their task subsets repeat across the recorded seeds. Greedy counts are unchanged across these seeds; random-prefix counts can differ, so their range is shown rather than treating the best order as the policy. Normalized counts are rounded for display only. The CSV retains full task indices, exact source pointers, seed-level comparator counts, and the recorded reference bounds. For unattainability, the underlying reference uses an out-of-range cardinality sentinel; the tables display $\infty$ instead of that sentinel. No sentinel is interpreted as measured investment.

\begingroup\small
\begin{longtable}{llrrr rr r rr}
\caption{Complete original decisions for HELM MMLU. $B$ is the selected minimum; $L=U$ is the independent reference bound when finite. $G$ is marginal greedy; $R$ is the range across the recorded seeded random orders. $\infty$ denotes independently certified unattainability, not zero investment.}\\
\toprule
Target & Rule & $\rho$ & $B$ & $B/d$ & $L$ & $U$ & $G$ & \multicolumn{2}{c}{$R$ (min--max)} \\
\midrule\endfirsthead
\toprule Target & Rule & $\rho$ & $B$ & $B/d$ & $L$ & $U$ & $G$ & \multicolumn{2}{c}{$R$ (min--max)} \\ \midrule\endhead
40 & Mean & 1.0 & 1 & 0.018 & 1 & 1 & 1 & 1 & 1 \\
40 & Mean & 0.5 & 1 & 0.018 & 1 & 1 & 1 & 1 & 1 \\
40 & Median & 1.0 & 0 & 0.000 & 0 & 0 & 0 & 0 & 0 \\
40 & Median & 0.5 & 0 & 0.000 & 0 & 0 & 0 & 0 & 0 \\
40 & Borda & 1.0 & 4 & 0.070 & 4 & 4 & 4 & 15 & 23 \\
40 & Borda & 0.5 & 4 & 0.070 & 4 & 4 & 4 & 12 & 17 \\
10 & Mean & 1.0 & 9 & 0.158 & 9 & 9 & 9 & 16 & 23 \\
10 & Mean & 0.5 & 23 & 0.404 & 23 & 23 & 23 & 38 & 38 \\
10 & Median & 1.0 & 12 & 0.211 & 12 & 12 & 12 & 16 & 18 \\
10 & Median & 0.5 & 12 & 0.211 & 12 & 12 & 16 & 20 & 32 \\
10 & Borda & 1.0 & 34 & 0.596 & 34 & 34 & 34 & 41 & 47 \\
10 & Borda & 0.5 & 39 & 0.684 & 39 & 39 & 39 & 46 & 50 \\
37 & Mean & 1.0 & 12 & 0.211 & 12 & 12 & 12 & 22 & 27 \\
37 & Mean & 0.5 & 36 & 0.632 & 36 & 36 & 36 & 47 & 49 \\
37 & Median & 1.0 & 16 & 0.281 & 16 & 16 & 16 & 19 & 22 \\
37 & Median & 0.5 & 16 & 0.281 & 16 & 16 & 22 & 47 & 50 \\
37 & Borda & 1.0 & 41 & 0.719 & 41 & 41 & 41 & 46 & 48 \\
37 & Borda & 0.5 & 50 & 0.877 & 50 & 50 & 50 & 53 & 54 \\
18 & Mean & 1.0 & 13 & 0.228 & 13 & 13 & 13 & 23 & 25 \\
18 & Mean & 0.5 & 40 & 0.702 & 40 & 40 & 40 & 50 & 51 \\
18 & Median & 1.0 & 18 & 0.316 & 18 & 18 & 18 & 20 & 25 \\
18 & Median & 0.5 & 18 & 0.316 & 18 & 18 & 29 & 39 & 42 \\
18 & Borda & 1.0 & 41 & 0.719 & 41 & 41 & 41 & 47 & 49 \\
18 & Borda & 0.5 & 52 & 0.912 & 52 & 52 & 52 & 55 & 55 \\
28 & Mean & 1.0 & 16 & 0.281 & 16 & 16 & 16 & 24 & 31 \\
28 & Mean & 0.5 & 49 & 0.860 & 49 & 49 & 49 & 54 & 55 \\
28 & Median & 1.0 & 21 & 0.368 & 21 & 21 & 21 & 24 & 25 \\
28 & Median & 0.5 & 21 & 0.368 & 21 & 21 & 52 & 54 & 57 \\
28 & Borda & 1.0 & 46 & 0.807 & 46 & 46 & 46 & 50 & 51 \\
28 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
16 & Mean & 1.0 & 21 & 0.368 & 21 & 21 & 21 & 29 & 32 \\
16 & Mean & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
16 & Median & 1.0 & 24 & 0.421 & 24 & 24 & 24 & 25 & 28 \\
16 & Median & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
16 & Borda & 1.0 & 50 & 0.877 & 50 & 50 & 50 & 52 & 52 \\
16 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
26 & Mean & 1.0 & 25 & 0.439 & 25 & 25 & 25 & 34 & 39 \\
26 & Mean & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
26 & Median & 1.0 & 29 & 0.509 & 29 & 29 & 29 & 29 & 29 \\
26 & Median & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
26 & Borda & 1.0 & 51 & 0.895 & 51 & 51 & 51 & 53 & 53 \\
26 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
20 & Mean & 1.0 & 46 & 0.807 & 46 & 46 & 46 & 47 & 47 \\
20 & Mean & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
20 & Median & 1.0 & 29 & 0.509 & 29 & 29 & 29 & 29 & 29 \\
20 & Median & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
20 & Borda & 1.0 & 53 & 0.930 & 53 & 53 & 53 & 53 & 54 \\
20 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
\bottomrule\end{longtable}

\begin{longtable}{llrrr rr r rr}
\caption{Complete original decisions for Open LLM. $B$ is the selected minimum; $L=U$ is the independent reference bound when finite. $G$ is marginal greedy; $R$ is the range across the recorded seeded random orders. $\infty$ denotes independently certified unattainability, not zero investment.}\\
\toprule
Target & Rule & $\rho$ & $B$ & $B/d$ & $L$ & $U$ & $G$ & \multicolumn{2}{c}{$R$ (min--max)} \\
\midrule\endfirsthead
\toprule Target & Rule & $\rho$ & $B$ & $B/d$ & $L$ & $U$ & $G$ & \multicolumn{2}{c}{$R$ (min--max)} \\ \midrule\endhead
803 & Mean & 1.0 & 1 & 0.167 & 1 & 1 & 1 & 1 & 1 \\
803 & Mean & 0.5 & 1 & 0.167 & 1 & 1 & 1 & 1 & 1 \\
803 & Median & 1.0 & 1 & 0.167 & 1 & 1 & 1 & 1 & 3 \\
803 & Median & 0.5 & 1 & 0.167 & 1 & 1 & 1 & 1 & 3 \\
803 & Borda & 1.0 & 1 & 0.167 & 1 & 1 & 1 & 1 & 4 \\
803 & Borda & 0.5 & 1 & 0.167 & 1 & 1 & 1 & 1 & 4 \\
1188 & Mean & 1.0 & 2 & 0.333 & 2 & 2 & 2 & 2 & 2 \\
1188 & Mean & 0.5 & 3 & 0.500 & 3 & 3 & 3 & 3 & 4 \\
1188 & Median & 1.0 & 2 & 0.333 & 2 & 2 & 2 & 2 & 3 \\
1188 & Median & 0.5 & 3 & 0.500 & 3 & 3 & 3 & 3 & 4 \\
1188 & Borda & 1.0 & 5 & 0.833 & 5 & 5 & 5 & 5 & 6 \\
1188 & Borda & 0.5 & 5 & 0.833 & 5 & 5 & 5 & 5 & 6 \\
1609 & Mean & 1.0 & 2 & 0.333 & 2 & 2 & 2 & 2 & 3 \\
1609 & Mean & 0.5 & 4 & 0.667 & 4 & 4 & 4 & 4 & 5 \\
1609 & Median & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 3 \\
1609 & Median & 0.5 & 3 & 0.500 & 3 & 3 & 3 & 4 & 4 \\
1609 & Borda & 1.0 & 5 & 0.833 & 5 & 5 & 5 & 5 & 6 \\
1609 & Borda & 0.5 & 5 & 0.833 & 5 & 5 & 5 & 5 & 6 \\
1566 & Mean & 1.0 & 2 & 0.333 & 2 & 2 & 2 & 2 & 3 \\
1566 & Mean & 0.5 & 4 & 0.667 & 4 & 4 & 4 & 4 & 5 \\
1566 & Median & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 3 \\
1566 & Median & 0.5 & 4 & 0.667 & 4 & 4 & 4 & 4 & 5 \\
1566 & Borda & 1.0 & 6 & 1.000 & 6 & 6 & 6 & 6 & 6 \\
1566 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
1101 & Mean & 1.0 & 2 & 0.333 & 2 & 2 & 2 & 2 & 3 \\
1101 & Mean & 0.5 & 5 & 0.833 & 5 & 5 & 5 & 5 & 5 \\
1101 & Median & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 3 \\
1101 & Median & 0.5 & 4 & 0.667 & 4 & 4 & 4 & 4 & 5 \\
1101 & Borda & 1.0 & 6 & 1.000 & 6 & 6 & 6 & 6 & 6 \\
1101 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
365 & Mean & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 3 \\
365 & Mean & 0.5 & 5 & 0.833 & 5 & 5 & 5 & 6 & 6 \\
365 & Median & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 3 \\
365 & Median & 0.5 & 4 & 0.667 & 4 & 4 & 5 & 4 & 6 \\
365 & Borda & 1.0 & 6 & 1.000 & 6 & 6 & 6 & 6 & 6 \\
365 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
1331 & Mean & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 3 \\
1331 & Mean & 0.5 & 6 & 1.000 & 6 & 6 & 6 & 6 & 6 \\
1331 & Median & 1.0 & 3 & 0.500 & 3 & 3 & 3 & 3 & 4 \\
1331 & Median & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
1331 & Borda & 1.0 & 6 & 1.000 & 6 & 6 & 6 & 6 & 6 \\
1331 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
1870 & Mean & 1.0 & 4 & 0.667 & 4 & 4 & 4 & 4 & 4 \\
1870 & Mean & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
1870 & Median & 1.0 & 4 & 0.667 & 4 & 4 & 4 & 4 & 4 \\
1870 & Median & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
1870 & Borda & 1.0 & 6 & 1.000 & 6 & 6 & 6 & 6 & 6 \\
1870 & Borda & 0.5 & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ & $\infty$ \\
\bottomrule\end{longtable}

\endgroup

\subsection{Controls, replay, and interpretation of uncertainty}
Each permutation, constant-score, and zero-update case contains 48 decisions per score table per seed, with all decisions marked independently validated and no recorded case failure. Permutation rotates task columns while preserving task identities consistently. Constant-score controls check empty-set co-first behavior. Zero-update controls distinguish an existing co-first target from one that cannot be promoted without changing scores. These synthetic checks are not additional public-data findings or additional target samples. There is one recorded reset replay for the first seed: it reports no failure and a matching status/cardinality signature for the replayed decisions. The other two episode records have no replay payload; no additional replay is inferred.



The three executions repeat a fixed panel, yielding 288 original decision records but only 96 unique target--rule--cap instances. Identical outputs across seeds establish observed repeatability of the allocation, not population uncertainty. The nonrandom target selection and shared competitor tables do not justify treating those records as independent draws for a confidence interval. Classical concentration inequalities and bootstrap inference require a defensible sampling object \citep{Hoeffding1963Bounds,Efron1979Bootstrap}; comparative statistical testing likewise depends on the comparison design \citep{Demsar2006Comparisons}. We therefore make no significance claim. Reporting the fixed panel, retained failures, and random-order ranges is more informative here than an unjustified error bar, consistent with explicit reporting of computational comparisons \citep{Dodge2019Reporting}.


\subsection{Public snapshots, normalization, and reproduction map}\label{sec:repro}
The Open LLM contents revision is
\begin{center}\small\texttt{9c09a7cae43334062a82cb164f2ef255013dafa2}.\end{center}
The HELM source is the public bucket's MMLU release v1.13.0. The accompanying frozen resources retain upstream URLs, upstream byte checksums, original source-row indices, and known aliases. The acquisition code canonicalizes Unicode/whitespace and raw score content before split assignment. Raw content and known alias clusters are disjoint across the recorded split; unknown lineage is not covered by that check. HELM is already on a unit scale; Open LLM uses the published normalized columns divided by 100, without treating raw columns as additional tasks. This choice makes the response cap relative to the published task scale. A different nonlinear score calibration would define a different intervention problem.




\paragraph{Reproduction entry points.}
\path{scripts/build_results.py} reads the immutable evidence registry and frozen resource dimensions. It generates Table~\ref{tab:budgets}, both quantitative figures, the complete supplementary tables, \path{derived/allocations.csv}, and \path{derived/summary.json}. It does not rerun the evaluator. \path{scripts/reproduce_allocations.py} independently checks recorded selected subsets against the score tables without changing any measured result. \path{scripts/acquire_scores.py} preserves the supplied upstream acquisition procedure for reacquiring score snapshots into a separate destination. The complete commands, dependencies, checksums, and generation map are in \path{REPRODUCIBILITY.md}. The conceptual overview is a separate deterministic rendering step owned by the document pipeline, not a measured plot.

\paragraph{Readable implementation evidence.}
The supplied selected entry point is specified in
\path{source_evidence/downstream/program/program_spec.toml}.
In \path{source_evidence/downstream/program/src/program.py}, the rank totals begin at line 50, mean allocation at line 73, odd median at line 82, even median at line 93, scalar validation at line 129, Borda search at line 160, and rival-aware Borda allocation at line 193. The response cap is formed at line 260; request validation and deadline allocation begin at line 268. The original comparator entry point and source are retained in the adjacent baseline directory; its allocation routine begins at line 59. Source hashes identify these files but are not used as substitutes for inspecting the implementation.
The retained entry-point file is byte-identical to the downstream selected source. The final manifest records a separate tree digest; different digest scopes are not equated to a file-identity proof. Detailed settings above describe the inspectable selected source, while numerical conclusions rest on the independent recorded allocations and bounds. The retained evaluator source is byte-identical to the evaluator digest in the final manifest.



\paragraph{Provenance and licenses.}
Local resource hashes, upstream source-file hashes, and transferred-array hashes identify different objects and are not interchangeable. The checksum manifest records each scope explicitly. Public access is not an explicit score-data redistribution license; neither the evaluation code license nor a model license automatically covers these tables. Reacquisition with attribution is documented, and public redistribution should be reviewed separately. Literature consultation used exact task-allowed identifiers and exact foundational identifiers, without following related-paper recommendations or citation graphs. Only consulted content supports citations; off-topic initial metadata matches were discarded. No prohibited work was intentionally retrieved or identified, and no claim depends on inferring its identity.

\subsection{Selection scope and independent final assessment}
The frozen configuration had no positive difference from the original baseline on the aggregate development selection score. The selection record contains three scored configurations and no unscored configuration; it does not establish a qualifying development improvement. The separate frozen final evaluation is completed and qualified, with independently checked original decisions and controls as described above. These statements use the selection record for development facts and the independent final assessment for qualification facts. There is no matched final original-baseline delta, and the weighted final evaluation score is not subtracted from the development score. Neither assessment status nor publication suitability changes the scope of the measured score-space conclusions.





\subsection{LLM Usage}
LLM assistance was used for research framing, solver-code development, reference-query planning, manuscript strategy, source inspection, extraction and plotting code, and drafting and revising this manuscript. The recorded evaluations supply the numerical evidence; this writing step does not replace those results with model-generated measurements. LLM-assisted scripts extract the existing records, generate the displayed tables and plots, and check evidence links and LaTeX consistency. No model training or new evaluation is reported as part of manuscript preparation. Claims about model capability, practical training cost, and unmeasured solver improvements are deliberately excluded. The retained logs document these roles; no unrecorded human verification or additional experiment is implied.
```
