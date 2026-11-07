# Agentic evidence audit packet

- generated_at: `2026-11-07T07:07:47.894551+00:00`
- paper_dir: `work/results/r03/codex/20261107_045228/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261107_062605-paper_evidence_audit-jeaaq75p/workspace`

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
    "anchored_references": 62,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 76,
    "resolved_references": 36,
    "total_references": 98
  },
  "ok": false,
  "pdf_path": null
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [
    {
      "messages": [
        "generated_by.script_path does not exist."
      ],
      "raw_reference": "<generated_by.script_path>",
      "subject_path": "paper.pdf.prov.json",
      "target": ".codex/skills/validate-paper/scripts/validate_compile_inputs.py"
    }
  ],
  "summary": {
    "anchored_references": 62,
    "dangling_references": 1,
    "manifests_checked": 11,
    "resolved_references": 35,
    "total_references": 98
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "The final evaluation completed and qualified; qualification is not proof of broad generalization.",
      "source_ids": [
        "final.qualification.status",
        "final.qualification.outcome",
        "final.qualification.correct"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The retained original reference has zero measured search score change; three alternative evaluations are unscored and do not establish measured losses or failure causes.",
      "source_ids": [
        "study.selection_kind",
        "study.investigation_outcome",
        "study.search_score_delta",
        "study.attempts.total",
        "study.attempts.scored",
        "study.attempts.unscored"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The pooled studied score is 0.9527636891 and equivalent normalized MAE is 0.0472363109; rounded values in the abstract, results, and pooled table are 0.9528 and 0.0472.",
      "source_ids": [
        "final.metric.combined_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Random-query low-rank pooled score is 0.9364101694, equivalent MAE 0.0635898306; the studied-minus-random difference is 0.0163535197.",
      "source_ids": [
        "final.metric.combined_score",
        "final.metric.random_lowrank_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The supplied pooled paired family-clustered interval against random-query factors is [0.0148071678, 0.0184780194], not an interval against ridge or for subgroups.",
      "source_ids": [
        "final.metric.paired_gain_ci_low",
        "final.metric.paired_gain_ci_high"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Information-selected ridge scores 0.9482262260 (MAE 0.0517737740), with descriptive studied-minus-ridge difference 0.0045374631 and no supplied paired significance interval.",
      "source_ids": [
        "final.metric.selected_ridge_score",
        "final.metric.combined_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Medoid ridge scores 0.9327472830 (MAE 0.0672527170), mean offset 0.9206056682 (MAE 0.0793943318), and historical means 0.9068768878 (MAE 0.0931231122).",
      "source_ids": [
        "final.metric.medoid_ridge_score",
        "final.metric.copy_score",
        "final.metric.constant_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The studied method has the highest pooled observed score among the six evaluated policies, without statistical superiority being established against all comparators.",
      "source_ids": [
        "final.metric.combined_score",
        "final.metric.random_lowrank_score",
        "final.metric.selected_ridge_score",
        "final.metric.medoid_ridge_score",
        "final.metric.copy_score",
        "final.metric.constant_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Three final seeds are 1009, 1013, 1019; replay is excluded from primary means and figures.",
      "evidence_refs": [
        "paper_data.json#final_evaluation.evaluation_evidence.episodes",
        "source_evidence/evaluation/plan.json#aggregation"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Figure 2, supplementary Table 2, and derived_results.json retain each of the twelve primary source/split/seed cells and six policies, using control=false and replay=false.",
      "evidence_refs": [
        "build_paper_artifacts.py",
        "derived_results.json"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The studied policy has higher observed scores than random-query factors in all twelve retained primary cells and the highest three-seed mean in each of four source/split conditions.",
      "evidence_refs": [
        "derived_results.json#conditions"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Studied condition means are 0.9496/0.9442 for MTEB model/family splits and 0.9591/0.9582 for Open LLM model/family splits, rounded from saved observations.",
      "evidence_refs": [
        "derived_results.json#conditions"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Pooled source scores are 0.9468974985 for MTEB and 0.9586298797 for Open LLM; they do not constitute controlled source-difficulty comparisons.",
      "source_ids": [
        "final.metric.mteb_score",
        "final.metric.open_llm_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Open LLM family split at seed 1019 gives studied score 0.9531041725 versus information-selected ridge 0.9533160600, a retained local reversal.",
      "evidence_refs": [
        "paper_data.json#final_evaluation.evaluation_evidence.episodes[2].solution.cases"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Pooled independently deranged-history score is 0.9233917542 and actual-minus-control gap is 0.0293719349.",
      "source_ids": [
        "final.metric.permuted_score",
        "final.metric.corruption_gap",
        "final.metric.combined_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Every retained source/split/seed pair has a lower observed studied-policy score under historical-column derangement, as shown in Figure 3 and supplementary Table 3; the contrast changes learning, querying, and target composition jointly.",
      "evidence_refs": [
        "source_evidence/evaluation/evaluate_final.py#permute_training",
        "tables/controls.tex"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.corruption_gap"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The final required cases completed and reset replay passed; these are interface/execution controls, not comprehensive validity guarantees.",
      "source_ids": [
        "final.metric.failed_episode_fraction",
        "final.metric.control_failure_fraction",
        "final.metric.reset_replay_ok",
        "final.qualification.status"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Supplementary Figure 4 shows only the studied-policy measured checkpoint arrays, increasing in each retained actual trajectory; no baseline checkpoint comparison, fixed-panel curve, or universally sufficient budget is inferred.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Recorded seed durations are 24.0816306723, 22.8890082091, 23.0760153015 seconds, excluding independent acquisition; no measured inference-cost, end-to-end storage, or speed advantage is asserted.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Hoerl",
        "Koren",
        "Jain"
      ],
      "claim": "The inspectable retained source implements masked alternating ridge factors, fixed observed column means, and SVD initialization; lambda=0.1, candidate ranks 1/2/4/8, seeded 10% cell validation, at most four validation sweeps and eight refit sweeps capped by requested steps.",
      "evidence_refs": [
        "source_evidence/downstream/program/src/program.py#L45-L83"
      ],
      "source_ids": [
        "study.selection_kind"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Equations 1 and 3 describe clipped remaining-target 1-MAE and context-independent ridge latent prediction; availability is known and historical missing cells are masked, not observed zeros.",
      "evidence_refs": [
        "source_evidence/evaluation/evaluate_final.py#curve_score",
        "source_evidence/downstream/program/src/program.py#L110-L142"
      ],
      "source_ids": [
        "study.selection_kind",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Chaloner",
        "Cohn"
      ],
      "claim": "The retained-source acquisition in Equation 4 uses a unit-noise quadratic trace-reduction proxy, includes the queried coordinate, and ignores purchased score values. Equation 5 is a fixed-target matrix identity, not an MAE optimality theorem.",
      "evidence_refs": [
        "source_evidence/downstream/program/src/program.py#L114-L127"
      ],
      "source_ids": [
        "study.selection_kind"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Random LF uses matching reference factor fit/prediction construction; the ridge comparators use zero-filled centered covariance and penalties 0.01/0.1/1 chosen with every-fifth-row historical validation; means and mean-offset policies use random legal queries.",
      "evidence_refs": [
        "source_evidence/evaluation/evaluate_final.py#reference_fit,predict_factors,run_baseline"
      ],
      "source_ids": [
        "study.selection_kind",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The readable retained and original reference files match, but exact byte-level identity to the separately hashed final snapshot is not independently certified; mechanism interpretation is conditional on supplied-source association.",
      "evidence_refs": [
        "source_evidence/downstream/program/src/program.py",
        "source_evidence/downstream/baseline/src/program.py"
      ],
      "source_ids": [
        "study.selection_kind",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "MTEB"
      ],
      "claim": "The evaluated source regimes are separately fitted MTEB embedding-model scores and Open LLM six raw generative benchmark columns; no learned cross-source transfer is asserted.",
      "evidence_refs": [
        "source_evidence/evaluation/audit.json#sources,extraction",
        "source_evidence/evaluation/evaluate_final.py#build_case"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "MTEB"
      ],
      "claim": "Pinned MTEB revision is 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383; pinned Open LLM revision is 9c09a7cae43334062a82cb164f2ef255013dafa2. MTEB extraction uses natural-bound original test scores and default/English task/revision/subset columns; Open LLM uses raw scores. The latter dataset license is undeclared.",
      "evidence_refs": [
        "source_evidence/evaluation/audit.json#sources,extraction"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The inspected final protocol uses model and heuristic name-family disjoint groups, approximately 70% historical groups, twenty-observation MTEB column support, and coverage filters; family labels are not authoritative lineage.",
      "evidence_refs": [
        "source_evidence/evaluation/evaluate_final.py#split_components,require_disjoint_rows,build_case",
        "source_evidence/evaluation/audit.json#extraction"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "MTEB checkpoints are 1/2/4/8, Open LLM checkpoints 1/2/3. Target, row, checkpoint, seed, split, source weighting is nested and equal at each level; control/replay have zero primary weight.",
      "evidence_refs": [
        "source_evidence/evaluation/plan.json#aggregation,production"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Efron",
        "Owen"
      ],
      "claim": "The supplied interval uses 200 paired family-clustered bootstrap draws with RNG24681357 and 2.5/97.5 percentile endpoints, shared family multiplicities across paired policies, cases and seeds within source. It is preserved, not reconstructed from seed means.",
      "evidence_refs": [
        "source_evidence/evaluation/plan.json#uncertainty"
      ],
      "source_ids": [
        "final.metric.paired_gain_ci_low",
        "final.metric.paired_gain_ci_high",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Documented evaluation versions are CPython3.12.15, NumPy1.26.4, SciPy1.12.0, PyArrow16.1.0, with CPU operation, isolation and broker requirements; this is not a newly measured cross-platform reproduction.",
      "evidence_refs": [
        "source_evidence/evaluation/plan.json#runtime",
        "source_evidence/evaluation/requirements.txt",
        "source_evidence/evaluation/evaluate_final.py#RPC"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "No fixed untouched target panel, response-adaptive selector, controlled nonlinear superiority, universal budget sufficiency, or family-held-out tuning is supported. Diagnostic descriptions remain unverified.",
      "evidence_refs": [
        "source_evidence/downstream/program/src/program.py",
        "source_evidence/evaluation/plan.json#limitations"
      ],
      "source_ids": [
        "study.attempts.unscored",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "MMLU",
        "MTEB",
        "HELM",
        "Tiny",
        "Metabench",
        "BenchBench"
      ],
      "claim": "MMLU, MTEB and HELM motivate heterogeneous evaluation coverage; item-level compression in tinyBenchmarks and metabench differs from buying aggregated benchmark scores; BenchBench motivates care about agreement methodology.",
      "source_ids": [
        "ref.allowed.MMLU",
        "ref.allowed.MTEB",
        "ref.allowed.HELM",
        "ref.allowed.Tiny",
        "ref.allowed.Metabench",
        "ref.allowed.BenchBench"
      ]
    },
    {
      "citation_keys": [
        "Ob

[truncated after 14000 chars]
```

## paper_data summary

```json
{
  "available": true,
  "claim_count": 0,
  "downstream_study": {
    "attempt_counts": {
      "scored": 0,
      "total": 3,
      "unscored": 3
    },
    "baseline_program_dir": "work/results/r03/codex/20261107_045228/investigation/.baseline-seed-6ewnjfck/program_0",
    "baseline_score": 0.9527030000575736,
    "baseline_tree_sha256": "33fc15401729399a8a88a6f041ce38f1279d47925bd6d123e805fb82ff752560",
    "combined_score": 0.9527030000575736,
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
    "program_dir": "work/results/r03/codex/20261107_045228/downstream/program",
    "program_tree_sha256": "33fc15401729399a8a88a6f041ce38f1279d47925bd6d123e805fb82ff752560",
    "search_score_delta": 0.0,
    "selection_kind": "baseline",
    "source_attempt_id": "bootstrap",
    "source_evidence": {
      "baseline": "source_evidence/downstream/baseline",
      "program": "source_evidence/downstream/program"
    },
    "source_program_dir": "work/results/r03/codex/20261107_045228/investigation/.baseline-seed-6ewnjfck/program_0",
    "source_tree_sha256": "33fc15401729399a8a88a6f041ce38f1279d47925bd6d123e805fb82ff752560"
  },
  "final_evaluation": {
    "correct": true,
    "outcome": "qualified",
    "status": "completed"
  },
  "grounding_source_count": 35,
  "paper_profile": "standalone",
  "totals": {
    "attempts": 3,
    "correct_programs": 0,
    "evaluated_programs": 0,
    "ideas": 3
  }
}
```

## references provenance summary

```json
{
  "count": 25,
  "generated_at": "2026-11-07T06:45:47.420116+00:00",
  "queries": [
    "ARXIV:2210.07316",
    "ARXIV:2009.03300",
    "ARXIV:2211.09110",
    "ARXIV:2402.14992",
    "ARXIV:2407.12844",
    "ARXIV:2407.13696",
    "ARXIV:2405.10938",
    "ARXIV:2412.06540",
    "DOI:10.1109/MC.2009.263",
    "DOI:10.1109/ICDM.2008.22",
    "DOI:10.1007/s10208-009-9045-5",
    "DOI:10.1109/TIT.2010.2044061",
    "DOI:10.1109/TIT.2010.2046205",
    "TITLE:Spectral Regularization Algorithms for Learning Large Incomplete Matrices",
    "TITLE:Probabilistic Matrix Factorization",
    "ARXIV:1212.0467",
    "DOI:10.1145/1390156.1390267",
    "DOI:10.1214/aos/1176344552",
    "DOI:10.1093/biomet/63.3.581",
    "DOI:10.1037/1082-989X.7.2.147",
    "DOI:10.1214/12-AOAS547",
    "DOI:10.1080/00401706.1970.10488634",
    "DOI:10.1214/ss/1177009939",
    "DOI:10.1613/jair.295",
    "DOI:10.1111/j.2517-6161.1977.tb01600.x"
  ],
  "references": [
    {
      "citation_key": "MTEB",
      "content_path": "literature/MTEB.txt",
      "id": "ref.allowed.MTEB",
      "paper_id": "ARXIV:2210.07316",
      "query": "ARXIV:2210.07316",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2210.07316",
      "title": "MTEB: Massive Text Embedding Benchmark",
      "year": 2022
    },
    {
      "citation_key": "MMLU",
      "content_path": "literature/MMLU.txt",
      "id": "ref.allowed.MMLU",
      "paper_id": "ARXIV:2009.03300",
      "query": "ARXIV:2009.03300",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2009.03300",
      "title": "Measuring Massive Multitask Language Understanding",
      "year": 2020
    },
    {
      "citation_key": "HELM",
      "content_path": "literature/HELM.txt",
      "id": "ref.allowed.HELM",
      "paper_id": "ARXIV:2211.09110",
      "query": "ARXIV:2211.09110",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2211.09110",
      "title": "Holistic Evaluation of Language Models",
      "year": 2022
    },
    {
      "citation_key": "Tiny",
      "content_path": "literature/Tiny.txt",
      "id": "ref.allowed.Tiny",
      "paper_id": "ARXIV:2402.14992",
      "query": "ARXIV:2402.14992",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2402.14992",
      "title": "tinyBenchmarks: evaluating LLMs with fewer examples",
      "year": 2024
    },
    {
      "citation_key": "Metabench",
      "content_path": "literature/Metabench.txt",
      "id": "ref.allowed.Metabench",
      "paper_id": "ARXIV:2407.12844",
      "query": "ARXIV:2407.12844",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2407.12844",
      "title": "metabench -- A Sparse Benchmark of Reasoning and Knowledge in Large Language Models",
      "year": 2024
    },
    {
      "citation_key": "BenchBench",
      "content_path": "literature/BenchBench.txt",
      "id": "ref.allowed.BenchBench",
      "paper_id": "ARXIV:2407.13696",
      "query": "ARXIV:2407.13696",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://export.arxiv.org/api/query?id_list=2407.13696",
      "title": "Do These LLM Benchmarks Agree? Fixing Benchmark Evaluation with BenchBench",
      "year": 2024
    },
    {
      "citation_key": "Observational",
      "content_path": "literature/Observational.txt",
      "id": "ref.allowed.Observational",
      "paper_id": "ARXIV:2405.10938",
      "query": "ARXIV:2405.10938",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://export.arxiv.org/api/query?id_list=2405.10938",
      "title": "Observational Scaling Laws and the Predictability of Language Model Performance",
      "year": 2024
    },
    {
      "citation_key": "Sloth",
      "content_path": "literature/Sloth.txt",
      "id": "ref.allowed.Sloth",
      "paper_id": "ARXIV:2412.06540",
      "query": "ARXIV:2412.06540",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2412.06540",
      "title": "Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families",
      "year": 2024
    },
    {
      "citation_key": "Koren",
      "content_path": "literature/Koren.txt",
      "id": "ref.allowed.Koren",
      "paper_id": "DOI:10.1109/MC.2009.263",
      "query": "DOI:10.1109/MC.2009.263",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1109/MC.2009.263",
      "title": "Matrix Factorization Techniques for Recommender Systems",
      "year": 2009
    },
    {
      "citation_key": "Hu",
      "content_path": "literature/Hu.txt",
      "id": "ref.allowed.Hu",
      "paper_id": "DOI:10.1109/ICDM.2008.22",
      "query": "DOI:10.1109/ICDM.2008.22",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1109/ICDM.2008.22",
      "title": "Collaborative Filtering for Implicit Feedback Datasets",
      "year": 2008
    },
    {
      "citation_key": "CandesRecht",
      "content_path": "literature/CandesRecht.txt",
      "id": "ref.allowed.CandesRecht",
      "paper_id": "DOI:10.1007/s10208-009-9045-5",
      "query": "DOI:10.1007/s10208-009-9045-5",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1007/s10208-009-9045-5",
      "title": "Exact Matrix Completion via Convex Optimization",
      "year": 2009
    },
    {
      "citation_key": "CandesTao",
      "content_path": "literature/CandesTao.txt",
      "id": "ref.allowed.CandesTao",
      "paper_id": "DOI:10.1109/TIT.2010.2044061",
      "query": "DOI:10.1109/TIT.2010.2044061",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1109/TIT.2010.2044061",
      "title": "The Power of Convex Relaxation: Near-Optimal Matrix Completion",
      "year": 2010
    },
    {
      "citation_key": "Keshavan",
      "content_path": "literature/Keshavan.txt",
      "id": "ref.allowed.Keshavan",
      "paper_id": "DOI:10.1109/TIT.2010.2046205",
      "query": "DOI:10.1109/TIT.2010.2046205",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1109/TIT.2010.2046205",
      "title": "Matrix Completion From a Few Entries",
      "year": 2010
    },
    {
      "citation_key": "Mazumder",
      "content_path": "literature/Mazumder.txt",
      "id": "ref.allowed.Mazumder",
      "paper_id": "c1f4f6222167e95bdf07a1358960a0a3ab2320a4",
      "query": "c1f4f6222167e95bdf07a1358960a0a3ab2320a4",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/search/match?query=Spectral+Regularization+Algorithms+for+Learning+Large+Incomplete+Matrices&fields=title%2CpaperId%2Cauthors%2Cyear%2Cabstract%2CcitationStyles",
      "title": "Spectral Regularization Algorithms for Learning Large Incomplete Matrices",
      "year": 2010
    },
    {
      "citation_key": "PMF",
      "content_path": "literature/PMF.txt",
      "id": "ref.allowed.PMF",
      "paper_id": "e19971e7d100386b9b4cf4ea1a0782b62fe036e5",
      "query": "e19971e7d100386b9b4cf4ea1a0782b62fe036e5",
      "read_scope": "full PDF",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/search/match?query=Probabilistic+Matrix+Factorization&fields=title%2CpaperId%2Cauthors%2Cyear%2Cabstract%2CcitationStyles",
      "title": "Probabilistic Matrix Factorization",
      "year": 2007
    },
    {
      "citation_key": "Jain",
      "content_path": "literature/Jain.txt",
      "id": "ref.allowed.Jain",
      "paper_id": "ARXIV:1212.0467",
      "query": "ARXIV:1212.0467",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://export.arxiv.org/api/query?id_list=1212.0467",
      "title": "Low-rank Matrix Completion using Alternating Minimization",
      "year": 2012
    },
    {
      "citation_key": "BayesianMF",
      "content_path": "literature/BayesianMF.txt",
      "id": "ref.allowed.BayesianMF",
      "paper_id": "DOI:10.1145/1390156.1390267",
      "query": "DOI:10.1145/1390156.1390267",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1145/1390156.1390267",
      "title": "Bayesian probabilistic matrix factorization using Markov chain Monte Carlo",
      "year": 2008
    },
    {
      "citation_key": "Efron",
      "content_path": "literature/Efron.txt",
      "id": "ref.allowed.Efron",
      "paper_id": "DOI:10.1214/aos/1176344552",
      "query": "DOI:10.1214/aos/1176344552",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1214/aos/1176344552",
      "title": "Bootstrap Methods: Another Look at the Jackknife",
      "year": 1979
    },
    {
      "citation_key": "Rubin",
      "content_path": "literature/Rubin.txt",
      "id": "ref.allowed.Rubin",
      "paper_id": "DOI:10.1093/biomet/63.3.581",
      "query": "DOI:10.1093/biomet/63.3.581",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1093/biomet/63.3.581",
      "title": "Inference and Missing Data",
      "year": 1976
    },
    {
      "citation_key": "Schafer",
      "content_path": "literature/Schafer.txt",
      "id": "ref.allowed.Schafer",
      "paper_id": "DOI:10.1037/1082-989X.7.2.147",
      "query": "DOI:10.1037/1082-989X.7.2.147",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1037/1082-989X.7.2.147",
      "title": "Missing data: Our view of the state of the art.",
      "year": 2002
    },
    {
      "citation_key": "Owen",
      "content_path": "literature/Owen.txt",
      "id": "ref.allowed.Owen",
      "paper_id": "DOI:10.1214/12-AOAS547",
      "query": "DOI:10.1214/12-AOAS547",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1214/12-AOAS547",
      "title": "Bootstrapping data arrays of arbitrary order",
      "year": 2012
    },
    {
      "citation_key": "Hoerl",
      "content_path": "literature/Hoerl.txt",
      "id": "ref.allowed.Hoerl",
      "paper_id": "DOI:10.1080/00401706.1970.10488634",
      "query": "DOI:10.1080/00401706.1970.10488634",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1080/00401706.1970.10488634",
      "title": "Ridge Regression: Biased Estimation for Nonorthogonal Problems",
      "year": 1970
    },
    {
      "citation_key": "Chaloner",
      "content_path": "literature/Chaloner.txt",
      "id": "ref.allowed.Chaloner",
      "paper_id": "DOI:10.1214/ss/1177009939",
      "query": "DOI:10.1214/ss/1177009939",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1214/ss/1177009939",
      "title": "Bayesian Experimental Design: A Review",
      "year": 1995
    },
    {
      "citation_key": "Cohn",
      "content_path": "literature/Cohn.txt",
      "id": "ref.allowed.Cohn",
      "paper_id": "DOI:10.1613/jair.295",
      "query": "DOI:10.1613/jair.295",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1613/jair.295",
      "title": "Active Learning with Statistical Models",
      "year": 1996
    },
    {
      "citation_key": "Dempster",
      "content_path": "literature/Dempster.txt",
      "id": "ref.allowed.Dempster",
      "paper_id": "DOI:10.1111/j.2517-6161.1977.tb01600.x",
      "query": "DOI:10.1111/j.2517-6161.1977.tb01600.x",
      "read_scope": "abstract",
      "retrieved_at": "2026-11-07T06:45:47.420116+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.1111/j.2517-6161.1977.tb01600.x",
      "title": "Maximum Likelihood from Incomplete Data Via the EM Algorithm",
      "year": 1977
    }
  ],
  "restriction_policy": "Exact permitted starter IDs and foundational method DOIs only; no citation graphs or broad benchmark searches."
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
\usepackage{amsmath,amssymb,booktabs,graphicx,subcaption}
\usepackage{hyperref,url}
\title{Variance-Guided Benchmark Selection for\newline Incomplete Model Score Matrices}
\author{}

\begin{document}
\maketitle

\begin{abstract}
Historical leaderboard scores offer a way to reduce model evaluation costs: measure a small subset of benchmarks and predict the rest. No improvement beyond the original reference was established; we characterize its variance-guided masked low-rank policy. Historical scores determine benchmark factors; purchased scores determine a new model's latent representation; a conditional variance proxy determines which benchmark to purchase. The selector depends on availability and previous query identities, not observed score values. On separately fitted MTEB embedding-model and Open LLM generative-model matrices, using model-disjoint and heuristic name-family-disjoint splits, the pooled normalized prediction score is $0.9528$, versus $0.9364$ for random-query low-rank reconstruction. The supplied paired family-clustered interval for this difference is $[0.0148,0.0185]$. Independently deranging historical columns reduces the studied score to $0.9234$, consistent with useful cross-benchmark correspondence. However, information-selected covariance ridge is competitive, and different query policies leave different evaluation targets. The evidence therefore supports a conditional comparison of complete evaluation policies, not fixed-target superiority, response-adaptive acquisition, or a universal sufficient benchmark budget.


\end{abstract}

\section{Introduction}
Evaluating a new language model across a broad benchmark suite is costly even when each individual benchmark is inexpensive. Public leaderboards contain a different resource: repeated measurements of historical models on overlapping tasks. If these measurements share structure, a small number of newly purchased benchmark scores may help estimate the unmeasured scores. The practical question is not just whether benchmarks correlate, but whether an explicit selection-and-prediction policy uses a limited evaluation budget more effectively than simpler alternatives.

We consider an incomplete matrix whose rows are models and columns are benchmark measurements. A new row comes with an availability mask indicating which measurements could be obtained. The policy purchases a bounded number of entries and predicts the available entries that remain unpurchased. This formulation separates historical missingness from the new model's query budget. It also exposes a subtle evaluation issue: selecting a benchmark removes that benchmark from the scored remainder. Two selection policies may therefore be evaluated on different target sets even when they start from the same model and availability mask.

Our central hypothesis is deliberately limited: \emph{a variance-guided query rule coupled to masked low-rank reconstruction provides a useful operational policy when historical cross-benchmark correspondence is informative}. The method is an inspectable combination of regularized matrix factorization and prediction-oriented design, rather than a new architecture. We compare it with a matched factor predictor using random queries, two covariance-ridge policies, historical benchmark means, and an observation-using mean-offset predictor. The matrices are fitted independently; transferring a protocol across embedding and generative models is not transferring learned factors between them.

The final evaluation supports this hypothesis within the measured regime. The studied policy has the highest pooled score among the six evaluated policies, with a positive paired uncertainty interval against random-query factor reconstruction. Destroying historical row correspondence across columns lowers its score. Neither result identifies a universally optimal selector: covariance ridge nearly matches the pooled result and slightly exceeds it in one retained source/split/seed cell. Moreover, the variance proxy optimizes a working squared-error quantity, whereas the measured loss is absolute error on a changing remainder.



The contributions are threefold. First, we specify a reproducible, CPU-only policy connecting incomplete historical scores to budgeted reconstruction. Second, we provide a direct comparison across two distinct public leaderboard sources, with row-level and name-family-level separation and paired uncertainty for the closest selector comparison. Third, we use a historical-correspondence control and explicitly separate what these measurements establish from what requires fixed-target, family-aware, or score-adaptive experiments. The contribution is this bounded empirical characterization, not evidence that unmeasured alternatives underperform.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/concept_overview.png}
\caption{Budgeted reconstruction from historical benchmark scores. Each source is fitted separately. Masked historical measurements yield benchmark factors; a variance proxy chooses an available benchmark; purchased scores determine a latent representation used to predict the unpurchased remainder. The query rule does not condition on purchased values. The evaluated remainder changes with the query policy.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\paragraph{Evaluation breadth and compression.}
MMLU, MTEB, and HELM illustrate the breadth and heterogeneity of model evaluation \citep{MMLU,MTEB,HELM}. Their roles differ: MTEB evaluates embeddings, whereas the other settings concern language-model capabilities more broadly. Reducing evaluation within a benchmark, as in tinyBenchmarks \citep{Tiny}, is distinct from purchasing complete benchmark scores. Metabench uses sparse item-level measurements to estimate underlying benchmark abilities \citep{Metabench}; our observational unit is instead an already aggregated model--benchmark score. BenchBench emphasizes that agreement conclusions depend on evaluation choices \citep{BenchBench}. We accordingly state the precise prediction target rather than treating correlation or a high aggregate score as sufficient validation.

\paragraph{Latent structure and experimental design.}
Observational scaling laws and Sloth motivate low-dimensional descriptions of multi-benchmark performance \citep{Observational,Sloth}. We do not fit compute scaling laws or recover interpretable skills. Our factors are regularized predictive coordinates, following the broader matrix-factorization tradition \citep{Koren,PMF,BayesianMF}. Masked numerical ratings should not be confused with implicit positive/negative feedback \citep{Hu}. Matrix completion has both convex and alternating-minimization approaches \citep{CandesRecht,CandesTao,Keshavan,Mazumder,Jain}; their recovery guarantees require assumptions not verified for these selectively observed leaderboards. Ridge regularization stabilizes the conditional solves \citep{Hoerl}. The acquisition rule is a prediction-oriented design heuristic, related to Bayesian design and statistical active learning \citep{Chaloner,Cohn}, not a theorem of absolute-error optimality.

\paragraph{Missingness and uncertainty.}
Classical missing-data work distinguishes the observed-data model from assumptions about the observation process \citep{Rubin,Schafer}. Optimizing a masked loss does not establish that missing leaderboard entries are ignorable, nor is our alternating ridge fit a fitted model of that process or an EM analysis \citep{Dempster}. Bootstrap inference also depends on the resampling unit \citep{Efron}. Work on dependent data arrays cautions against treating all cells as independent \citep{Owen}. Here the supplied interval resamples heuristic families in a paired fashion; it does not quantify every source of distributional or implementation uncertainty.

\section{Method}
\label{sec:method}
\subsection{Problem and success criterion}
Let $X\in[0,1]^{M\times N}$ be historical scores, with observed-entry mask $W$. For a held-out model, let $A$ denote the available benchmark indices, $Q_k\subset A$ the purchased indices after budget $k$, and $x_j$ the measured score at index $j$. The predictor receives only $X,W,A$, and purchased values. It outputs $\hat x_j$ for the remaining targets $R_k=A\setminus Q_k$. For one held-out row, the reported normalized prediction score is
\begin{equation}
 S_k=1-\frac{1}{|R_k|}\sum_{j\in R_k}
 \left|\operatorname{clip}_{[0,1]}(\hat x_j)-x_j\right|.
 \label{eq:score}
\end{equation}

Higher is better. This is not classification accuracy, explained variance, or a fraction of recovered benchmarks. Each benchmark purchase has equal nominal cost; the objective does not incorporate measured benchmark runtimes. Missing historical cells contribute no observations, even though the transport representation stores zeros in those positions. The new model's availability mask is supplied before selection, which is more information than an evaluator may have in a prospective deployment.

\subsection{Masked factors and conditional prediction}
For benchmark $j$, compute the historical observed mean $\mu_j$. With latent row coordinates $u_i\in\mathbb R^r$ and benchmark factors $v_j\in\mathbb R^r$, the fitted objective is
\begin{equation}
 \min_{U,V}\sum_{i,j:W_{ij}=1}(X_{ij}-\mu_j-u_i^\top v_j)^2
       +\lambda\left(\|U\|_F^2+\|V\|_F^2\right).
 \label{eq:fit}
\end{equation}
The means remain fixed during alternating ridge updates. Initialization uses the leading right singular vectors of the zero-filled, mean-centered matrix, scaled by square roots of their singular values. Zero filling is an initialization device, not a claim that missing measurements equal a benchmark mean in the fitted loss.

The regularization coefficient is $\lambda=0.1$. Rank is chosen from $\{1,2,4,8\}$ by absolute error on a deterministic seeded holdout of approximately $10\%$ of observed historical cells. Infeasible ranks are skipped. Each rank uses at most four alternating sweeps for validation; the chosen rank is refitted on all historical observations for at most eight sweeps, capped by the requested fitting allowance. This is historical-cell validation, not nested validation on held-out model families. The saved results do not report selected ranks, so we do not attribute performance to a particular latent dimensionality.


For a new model and purchased set $Q$, stack the corresponding factor rows into $V_Q$. Prediction uses
\begin{equation}
 C_Q=(V_Q^\top V_Q+\lambda I)^{-1},\qquad
 \hat u_Q=C_QV_Q^\top(x_Q-\mu_Q),\qquad
 \hat x_j=\operatorname{clip}_{[0,1]}(\mu_j+v_j^\top\hat u_Q).
 \label{eq:predict}
\end{equation}
Each new model has an independent conditional state. Observations from one held-out row do not update another row's latent representation or refit the historical benchmark factors.


\subsection{Variance-guided benchmark acquisition}
Let $T=A\setminus Q$ be the currently available, unpurchased indices. For each legal next query $a\in T$, the implemented proxy is
\begin{equation}
 g(a\mid Q,A)=\frac{\sum_{j\in T}(v_j^\top C_Qv_a)^2}
                         {1+v_a^\top C_Qv_a},\qquad
 a^*=\arg\max_{a\in T}g(a\mid Q,A).
 \label{eq:acq}
\end{equation}

The index order resolves ties. Under a unit-noise linear working model, adding $v_a$ changes the inverse information matrix by
\begin{equation}
 C_{Q\cup\{a\}}=C_Q-
 \frac{C_Qv_av_a^\top C_Q}{1+v_a^\top C_Qv_a}.
 \label{eq:rankone}
\end{equation}
Consequently, $g$ is the reduction in $\operatorname{tr}(V_TC_QV_T^\top)$ \emph{on the current fixed set $T$} from this update. This identity explains the implementation; it is not a calibrated posterior uncertainty estimate or a guarantee about the measured absolute error.

Crucially, the sum includes the queried coordinate $a$. The measured remainder after purchasing $a$ excludes it. Thus the implemented criterion is not pure off-diagonal transfer, and the identity does not establish optimal design for Equation~\ref{eq:score}. In addition, $C_Q$ depends on purchased indices, not purchased score values. Query sequences can differ between availability masks, but two new models with the same mask follow the same sequence under the same fitted factors. Predictions are response-conditioned; selection is not response-adaptive.

\subsection{Compared policies and computational scope}
The closest comparison, \textbf{Random LF}, uses the same masked factor-fitting and conditional prediction construction with uniformly random legal queries. \textbf{Variance LF} denotes the studied selector. The two ridge comparators estimate a benchmark covariance from mean-centered historical scores with missing residuals filled by zero. Their predictor is
\begin{equation}
 \hat x=\mu+\Sigma_{:,Q}(\Sigma_{Q,Q}+\alpha I)^{-1}(x_Q-\mu_Q),
 \label{eq:ridge}
\end{equation}
followed by clipping. \textbf{Info ridge} chooses queries by a conditional-covariance reduction criterion; \textbf{Medoid ridge} orders benchmarks by the sum of absolute imputed historical correlations, skipping unavailable indices. Their penalty is chosen from $\{0.01,0.1,1\}$ on every-fifth historical-row validation using a single observed predictor coordinate. They therefore differ from the factor policy in representation, tuning, and potentially query sets; they are not matched-query reconstruction ablations.


\textbf{Means} predicts $\mu$ regardless of observed values. \textbf{Mean offset} adds the average purchased residual $|Q|^{-1}\sum_{a\in Q}(x_a-\mu_a)$ to each benchmark mean. Both use random legal queries. Even the observation-invariant comparator is scored on its own purchased-set remainder, rather than on an identical untouched panel shared by all policies.

The factor state stores benchmark loadings and a small latent solve instead of a full benchmark covariance. Nevertheless, the inspected code initializes with a dense singular-value decomposition and forms dense products for acquisition. The factor dimension is small, but this implementation is not a sparse-matrix scalability demonstration. We report no measured memory advantage or speedup over ridge. All evaluated methods operate on CPU; no new language-model inference is performed.

\section{Experimental Protocol}
\subsection{Public score sources and split construction}
We use two real sources separately. MTEB supplies embedding-model task measurements; Open LLM supplies generative-model scores on IFEval, BBH, MATH Lvl 5, GPQA, MUSR, and MMLU-PRO. They are different application regimes, not two subsets of an aligned model roster. The pinned source revisions and extraction rules appear in Supplementary Information. No cross-source entity matching or pooled factor fit is used.



MTEB extraction uses original test \texttt{main\_score} values in their natural unit interval, default/English subsets, and distinct task/revision/subset columns. Open LLM uses raw benchmark columns rather than aggregate or leaderboard-normalized scores. Nonfinite or out-of-bound source values are omitted. No normalization is fitted on held-out scores. Duplicate raw documents and complete score examples are linked before partitioning; normalized identities and aliases are also checked for overlap.

Within each source, the protocol evaluates model-disjoint and heuristic name-family-disjoint splits. Connected identity/content groups are assigned to history or test by seeded group shuffling, with approximately $70\%$ of groups assigned to history. Family separation adds a conservative name-based linkage. This is stronger than independently splitting rows that may share aliases, but it is not authoritative model genealogy. MTEB columns require at least twenty historical observations, and test rows require enough available values for the full query budget plus a nonempty remainder. Filtering therefore conditions the evaluated population on coverage.


\subsection{Budget, weighting, and uncertainty}
The retained final measurements use seeds $1009$, $1013$, and $1019$. MTEB is scored at budgets $k\in\{1,2,4,8\}$; Open LLM at $k\in\{1,2,3\}$. Budgets are checkpointed along one query sequence, not independently optimized policies for each $k$. Within a held-out row, target errors have equal weight; rows, checkpoints, seeds, splits within a source, and the two sources are averaged in that order with equal weight at each level. This prevents the larger source or denser target rows from dominating the pooled result.



The supplied uncertainty interval compares Variance LF with Random LF using $200$ paired family-clustered bootstrap draws and percentile endpoints $2.5$ and $97.5$. Family multiplicities are shared across paired methods, cases, and seeds within each source, preserving the frozen aggregation weights. It is a pooled interval, not an interval for every subgroup or for another comparator. The stored episode summaries do not contain row-level residuals; the paper preserves the supplied interval rather than reconstructing it from three seed averages. Seed markers in figures are descriptive variation, not confidence limits.



\subsection{Historical-correspondence and state controls}
Each source/split/seed condition is paired with a fit on independently deranged historical columns. The control preserves column marginals and missingness while disrupting historical cross-column row correspondence. Test scores remain unchanged. This tests sensitivity to the alignment available in historical scores, not an isolated acquisition component. A reset replay checks the initial actual condition for repeated legal queries and clipped predictions. Controls and replay have zero primary aggregation weight; replay is not another independent seed. The protocol retains original denominators for failures rather than silently dropping incomplete cases.


The retained method is the unchanged original reference implementation: the preceding selection process produced no measured search improvement, and its three alternative evaluations returned no usable scores, establishing neither comparative losses nor their failure causes. Independently, the final evaluation completed and met its recorded qualification criteria; this does not certify generalization beyond the stated protocol, as detailed in the supplement.




\section{Results}
\subsection{Direct comparison of complete policies}
Table~\ref{tab:pooled} reports the pooled scores and their equivalent absolute errors. Variance LF scores $0.9528$, compared with $0.9364$ for Random LF, an observed difference of $0.01635$. The supplied paired interval is $[0.01481,0.01848]$. Within the frozen population and weighting, this supports a positive operational contrast for variance-guided versus random queries with the matched factor construction. It does not compare prediction errors on identical target panels.


\begin{table}[t]
\centering
\input{tables/pooled}
\caption{Pooled prediction scores and normalized MAE. LF denotes masked low-rank reconstruction. All methods receive the same source/split/seed and budget protocol, but their purchased indices and scored remainders can differ. Only Variance LF versus Random LF has a supplied paired uncertainty interval.}
\label{tab:pooled}
\end{table}

Historical means already score $0.9069$, illustrating why a high absolute score alone is insufficient evidence of useful querying. Adding a model-level offset raises the score to $0.9206$. Medoid ridge reaches $0.9327$, while information-selected ridge reaches $0.9482$. Thus an informative covariance-based policy captures much of the observed predictability without the studied factor representation. Its pooled difference from Variance LF is $0.00454$; there is no supplied paired interval establishing statistical superiority against this stronger comparator.


\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/main_comparison.pdf}
\caption{Direct comparisons under (a) MTEB model separation, (b) MTEB name-family separation, (c) Open LLM model separation, and (d) Open LLM name-family separation. Small dots show the three final seeds; diamonds show their means. Horizontal positions share the same explicitly restricted score axis. No dots are uncertainty intervals. Variance LF has the highest mean in each panel; the individual-seed reversal against Info ridge remains visible in panel (d).}
\label{fig:main}

\end{figure}

\subsection{Source, split, and seed heterogeneity}
Figure~\ref{fig:main} retains all source/split conditions instead of displaying only the pooled ranking. Mean Variance LF scores are $0.9496$ and $0.9442$ on MTEB's model and name-family splits, and $0.9591$ and $0.9582$ on Open LLM's corresponding splits. The pooled source scores are $0.9469$ for MTEB and $0.9586$ for Open LLM. These are not controlled source-difficulty comparisons: the benchmark collections, availability patterns, and budget ranges differ.




The matched random-query factor baseline has lower observed scores in every retained source/split/seed cell. However, universal dominance across all comparators is not observed. On Open LLM's name-family split at seed $1019$, Variance LF scores $0.953104$, whereas Info ridge scores $0.953316$. Rounding these to fewer digits can hide the reversal. This small counterexample is important because the pooled ordering alone could suggest that the factor representation is always preferable. The evidence supports neither that conclusion nor isolated attribution to factorization rather than query selection.


The supplementary checkpoint curves show increasing observed scores with larger budgets along each retained trajectory. They cannot determine a universally sufficient $k$: there is no externally specified acceptable error threshold, no uncertainty interval by budget, and fewer available targets remain at later checkpoints. Nor do the summaries contain baseline checkpoint curves from which to infer budget-specific advantages over ridge. The central comparison is the prespecified average over checkpoint budgets.


\subsection{Sensitivity to historical correspondence}
Figure~\ref{fig:control} pairs the actual and deranged-history measurements. The pooled studied score falls from $0.9528$ to $0.9234$, an actual-minus-control gap of $0.02937$. Every retained source/split/seed pair has a lower observed score under the control. Useful historical structure therefore survives the source extraction and splitting procedures sufficiently to affect the measured policy. Benchmark marginals alone are not enough to reproduce its actual-history result.




\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/historical_dependence_control.pdf}
\caption{Historical-correspondence control by source. Each line joins aligned and independently column-deranged histories for one retained seed and split; it does not depict temporal change. Color and marker distinguish split definitions. The control changes the learned representation and potentially the query set, so the score gap is not an acquisition-only effect.}
\label{fig:control}
\end{figure}

This is a dependence check, not proof that the low-rank model is true. The control perturbs factor learning, selection, and prediction jointly, and could also alter which targets remain. It cannot identify the best latent rank, verify that missingness is ignorable, or certify absence of benchmark contamination. All required final cases completed, and the reset replay passed; these facts support execution consistency within the tested interface, not comprehensive scientific validity.



\section{Discussion and Limitations}
\paragraph{What the comparison identifies.}
The evidence is strongest for a policy-level statement: for these public score matrices, splits, and checkpoint weights, variance-guided factor reconstruction improves the observed remaining-target objective over its random-query counterpart. This is a useful decision problem when the evaluator cares precisely about whichever available benchmarks were not purchased. It is a weaker basis for a statement about reconstructing a prespecified panel, because the policy controls the scored target composition as well as the information collected. A fixed untouched panel, shared query sets for predictor ablations, and a selector-only comparison on that panel would separate these effects; none is reported here.

\paragraph{What the mechanism does not establish.}
The acquisition formula uses a conditional quadratic proxy with a unit-noise working interpretation. No empirical calibration of that uncertainty is available. The optimized proxy includes a coordinate that subsequently leaves the target set, and the final score uses absolute rather than squared loss. These mismatches do not invalidate the observed contrast, but they prevent interpreting it as validation of an optimality theorem. Likewise, availability-conditioned sequential choices should not be described as learning which question to ask from a new model's answers: the implemented choice ignores those answers.

\paragraph{Scope of the data distribution.}
Historical scores are selectively observed. Coverage filtering and the supplied availability mask restrict the population to models with enough measured benchmarks, potentially excluding the hardest prospective cases. Name-derived family labels can miss cross-namespace relationships and do not guarantee separation of pretraining data, fine-tuning lineages, or shared evaluation contamination. Historical-cell rank selection also does not measure sensitivity to tuning on entirely unseen families. The final splits and derangement control constrain some interpretations, but they do not justify arbitrary out-of-distribution or future-model generalization. Implementation interpretation uses the inspectable retained source; an independently verifiable byte-identical final snapshot is unavailable, as detailed in the supplement.

\paragraph{Uncertainty, costs, and practical use.}
The supplied bootstrap interval concerns one pooled matched-factor contrast under heuristic family clustering. It is not evidence of significance against all baselines; subgroup differences and the ridge comparison remain descriptive. The experiment purchases benchmark scores retrospectively from a frozen table and assumes equal query costs. It therefore demonstrates prediction under a score budget, not measured savings in inference time, energy, or monetary cost. A practical evaluator should select its own error tolerance, retain direct measurement of safety-critical or poorly represented benchmarks, and test a fixed target panel before relying on inferred scores for model release decisions.

\paragraph{What averaging hides.}
Equal row weights give sparse and dense held-out models the same contribution after their target errors are averaged. Equal source weights likewise prevent the larger generative-model table from overwhelming the embedding-model setting. These are explicit priorities of the evaluation, not invariances of the underlying inference problem. A different deployment population, benchmark weighting, or cost model can change the policy ranking. Moreover, a small average absolute error can coexist with large errors on a particular capability. The retained summaries contain neither per-benchmark residual distributions nor tail-error intervals, so they do not support certifying individual benchmark predictions, identifying which tasks can safely be skipped, or converting the pooled score into a deployment-specific reliability threshold. Reporting the source/split views and the local ridge reversal is therefore necessary, but not a substitute for task-level validation when choosing an actual evaluation panel.

\section{Conclusion}
Historical leaderboard measurements can support budgeted reconstruction without fitting a large predictor or running new language-model inference. In the evaluated setting, a regularized masked factor model coupled to variance-guided queries yields a higher pooled remaining-target score than the same factor construction with random queries. The historical-column control further shows that useful correspondence across benchmarks contributes to the measured result. These observations hold across the separately fitted embedding-model and generative-model sources and their two split definitions, rather than establishing transfer of a common representation.

The most important qualification is the target itself. Query policies remove different coordinates from evaluation, and the strongest covariance comparator is competitive, including a retained local reversal. The measurements therefore do not establish fixed-target superiority, score-adaptive selection, calibrated uncertainty, or a universal number of sufficient benchmarks. The appropriate conclusion is narrower: variance-guided masked reconstruction is a useful operational policy in the observed regime, with clear reasons to require shared-target evaluation, stronger family definitions, and explicit deployment costs before making broader claims.

\clearpage
\bibliography{references}
\bibliographystyle{paper}

\clearpage
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}
\subsection{Inspectable implementation and analytic identity}
The retained evaluated implementation is supplied at
\path{source_evidence/downstream/program/src/program.py}; the original reference is at
\path{source_evidence/downstream/baseline/src/program.py}.
Their readable source contents match. The entrypoint contract is in the adjacent \texttt{program\_spec.toml} files. Factor fitting is at lines 45--62, rank selection at lines 65--83, acquisition at lines 114--127, and conditional prediction at lines 134--142. Comparison implementations are inspectable in \path{source_evidence/evaluation/evaluate_final.py}, especially \texttt{reference\_fit}, \texttt{run\_baseline}, and \texttt{curve\_score}. These files, rather than source hashes alone, support the implementation description. The final manifest and the selection registry record different tree digests; no separate final source snapshot is supplied. We therefore do not certify byte-level identity of the final snapshot from hashes or method-family alignment alone. Implementation-level interpretation is conditional on the supplied retained-source association; final measurements and qualification are read independently from evaluator evidence.




For completeness, set $H_Q=V_Q^\top V_Q+\lambda I$. Since $\lambda>0$, $H_Q$ is invertible. Multiplying $H_Q+v_av_a^\top$ by the right side of Equation~\ref{eq:rankone} gives the identity matrix: the added rank-one terms cancel after division by $1+v_a^\top C_Qv_a$. Multiplying the covariance difference on the left by $V_T$ and on the right by $V_T^\top$ and taking a trace gives
\[
 \operatorname{tr}\!\left[V_T(C_Q-C_{Q\cup\{a\}})V_T^\top\right]
 =\frac{\|V_TC_Qv_a\|_2^2}{1+v_a^\top C_Qv_a}.
\]
This matches the source acquisition calculation. It assumes the same target matrix on both sides and therefore is not a derivation of the actual change in remaining-target MAE. The factor estimates and regularization are treated as fixed; uncertainty about the fitted factors is not integrated out as in a fully Bayesian factor model.


\subsection{Pinned acquisition, extraction, and reproducibility}
The MTEB score archive is pinned to revision
\texttt{6dabbcc68c28ea5f180c\allowbreak e7df79347b3ca9cc6383}
of \url{https://github.com/embeddings-benchmark/results}.
The Open LLM contents table is pinned to
\texttt{9c09a7cae43334062a82\allowbreak cb164f2ef255013dafa2}
at \url{https://huggingface.co/datasets/open-llm-leaderboard/contents}.
The acquisition audit, extracted private research pool, and final protocol are supplied in \path{source_evidence/evaluation/audit.json}, \path{task/resources/final/pool.json.gz}, and \path{source_evidence/evaluation/plan.json}. Reacquisition should verify the archive/table hashes recorded in the audit and reapply the documented extraction rather than substitute a current leaderboard. The audit attributes CC0-1.0 to the MTEB results according to the task data specification; it also notes the absence of a standalone license file in the pinned archive. The Open LLM dataset license is undeclared. Public access is not permission to redistribute that table; reproduction should reacquire it rather than assume redistribution rights.


Repeated MTEB model/column measurements use the deterministic lexicographically first revision. Exact duplicate raw documents retain only the archive-first owner and other copies become missing before splitting. Full score-example hashes are computed before downstream preprocessing. The family heuristic combines namespace and a lowercased model stem before punctuation/digits; Open LLM uses the base-model metadata when available. Such deterministic bookkeeping is reproducible but cannot recover unrecorded lineage.

The documented evaluation environment is CPython 3.12.15 on Linux x86\_64, NumPy 1.26.4, SciPy 1.12.0, and PyArrow 16.1.0. The benchmark evaluator requires native Landlock and seccomp isolation and a broker; a portable invocation on an unsupported kernel is not an equivalent reproduction. The exact entrypoint command is
\begin{samepage}
\begin{verbatim}
python task/evaluate_final.py \
  --program_path \
  source_evidence/downstream/program/src/program.py \
  --results_dir /tmp/reproduced-final
\end{verbatim}
\end{samepage}
The command is documented for independent reproduction on a supported isolated host, not rerun during manuscript preparation; production used the broker-mediated interface. Seeds are fixed by the evaluator to $1009,1013,1019$. The retained seed records report approximately $24.08$, $22.89$, and $23.08$ seconds respectively, excluding independent source acquisition. These are machine-dependent durations, not a runtime guarantee. No end-to-end acquisition/storage or benchmark-inference runtime was measured for this paper.




All manuscript tables and quantitative figures are generated by \path{build_paper_artifacts.py} directly from \path{paper_data.json}; this only summarizes saved measurements. The conceptual overview is prepared separately from the manuscript specification. \path{README.md} gives figure/table mappings and build commands. Derived artifacts have adjacent provenance sidecars and the manuscript has inline evidence links in LaTeX comments.

\subsection{Complete retained seed comparisons}
Table~\ref{tab:seeds} gives each primary source/split/seed comparison. The pooled weighting averages target errors within rows before averaging rows and checkpoints, then gives equal weight to seeds, the two split cases per source, and the two sources. The reset replay is omitted here and from primary aggregates. Table~\ref{tab:controls} retains all actual/control pairs for the studied policy; control scores are not mixed into the primary leaderboard.

\begin{table}[h]
\centering\footnotesize

\begin{tabular}{llrrrrrr}\toprule Source & Split/seed & Var LF & Rand LF & Info R & Med R & Offset & Means \\ \midrule
MTEB & M/1009 & 0.9528 & 0.9412 & 0.9500 & 0.9369 & 0.9340 & 0.9147 \\
MTEB & M/1013 & 0.9470 & 0.9326 & 0.9410 & 0.9316 & 0.9262 & 0.8996 \\
MTEB & M/1019 & 0.9490 & 0.9373 & 0.9439 & 0.9318 & 0.9277 & 0.9132 \\
\addlinespace
MTEB & F/1009 & 0.9488 & 0.9376 & 0.9443 & 0.9345 & 0.9199 & 0.9042 \\
MTEB & F/1013 & 0.9369 & 0.9211 & 0.9283 & 0.9158 & 0.9178 & 0.8810 \\
MTEB & F/1019 & 0.9469 & 0.9384 & 0.9457 & 0.9378 & 0.9323 & 0.9170 \\
\addlinespace
Open LLM & M/1009 & 0.9595 & 0.9375 & 0.9535 & 0.9331 & 0.9133 & 0.9063 \\
Open LLM & M/1013 & 0.9582 & 0.9370 & 0.9529 & 0.9321 & 0.9143 & 0.9055 \\
Open LLM & M/1019 & 0.9597 & 0.9376 & 0.9540 & 0.9336 & 0.9156 & 0.9075 \\
\addlinespace
Open LLM & F/1009 & 0.9619 & 0.9422 & 0.9579 & 0.9364 & 0.9182 & 0.9228 \\
Open LLM & F/1013 & 0.9594 & 0.9387 & 0.9539 & 0.9359 & 0.9168 & 0.9081 \\
Open LLM & F/1019 & 0.9531 & 0.9358 & 0.9533 & 0.9334 & 0.9111 & 0.9027 \\
\addlinespace
\bottomrule\end{tabular}
\caption{All retained primary scores. M/F denotes model/name-family split; LF denotes low-rank reconstruction; R denotes ridge. Values are averages over the source-specific budget checkpoints, not single-budget scores.}
\label{tab:seeds}
\end{table}

\begin{table}[h]
\centering\small

\begin{tabular}{llrr}\toprule Source & Split/seed & Aligned & Deranged \\ \midrule
MTEB & M/1009 & 0.9528 & 0.9212 \\
MTEB & M/1013 & 0.9470 & 0.9065 \\
MTEB & M/1019 & 0.9490 & 0.9168 \\
MTEB & F/1009 & 0.9488 & 0.9094 \\
MTEB & F/1013 & 0.9369 & 0.8923 \\
MTEB & F/1019 & 0.9469 & 0.9209 \\
Open LLM & M/1009 & 0.9595 & 0.9338 \\
Open LLM & M/1013 & 0.9582 & 0.9338 \\
Open LLM & M/1019 & 0.9597 & 0.9351 \\
Open LLM & F/1009 & 0.9619 & 0.9452 \\
Open LLM & F/1013 & 0.9594 & 0.9349 \\
Open LLM & F/1019 & 0.9531 & 0.9307 \\
\bottomrule\end{tabular}
\caption{Historical-correspondence control for Variance LF. Each row is a paired source/split/seed comparison. M/F follows Table~\ref{tab:seeds}.}
\label{tab:controls}
\end{table}

\subsection{Budget-conditioned measurements}
Figure~\ref{fig:budget} displays only the measured studied-policy checkpoint curves. The retained records provide comparison-policy averages but not their checkpoint arrays. Consequently, this figure makes no budget-specific comparative claim. Later checkpoints remove more benchmarks from the target set, which is another reason not to read the curves as a fixed-panel learning curve or as evidence that a particular budget is sufficient.

\begin{figure}[h]
\centering
\includegraphics[width=\textwidth]{figures/budget_sensitivity.pdf}
\caption{Recorded checkpoint scores for Variance LF. Each line is one split and seed; all measured trajectories are shown. The Open LLM and MTEB budget grids differ. These are budget-conditioned remaining-target scores, not measurements of comparison policies or a fixed evaluation panel.}
\label{fig:budget}

\end{figure}

\subsection{Uncertainty and evaluation provenance}
The supplied bootstrap uses evaluator RNG seed $24681357$. Family multiplicities are drawn per source and shared over paired Variance LF/Random LF observations, cases, and seeds. Equal case, seed, and source weights are preserved. Zero sampled mass for a case/seed contributes zero rather than changing its aggregation weight; incomplete required actual measurements would trigger a conservative interval. These are the documented resampling semantics, not a new analysis from unavailable row residuals. The family labels are heuristic, so the interval is conditional on that clustering choice.


The final evidence independently records completion and qualification. This is distinct from retaining the original reference after a selection procedure with zero measured score change and three unscored alternative evaluations. Missing scores are missing performance evidence, not measured losses. Their recorded exits do not identify statistical failure, protocol invalidity, or adaptivity defects as the cause. No alternative-method performance table, successful nonlinear comparison, fixed-target ablation, or family-held-out hyperparameter tuning is inferred from these records. Candidate-generated diagnostic descriptions were not trusted as verified measurements.




\subsection{Research transparency}
This observational study analyzes public model-level scores and does not collect new human-subject data. The main risks are misleading inferred model capabilities and overconfident deployment decisions, especially under selective missingness or lineage shift. Inferred scores should not replace direct evaluation of high-stakes properties. No claim of a universal ranking, proprietary-data access, or a measured environmental benefit is made. Negative and countervailing observations, including the local ridge reversal and lack of scored alternative-method evidence, are retained.

Literature access was restricted to explicitly permitted starter records and exact foundational-method identifiers/titles. No citation graph expansion or broad search for the prohibited related work was performed. Retrieved metadata and abstracts were checked for relevance; mismatched records and an unrelated abstract were rejected rather than cited. The active citation provenance records the content actually consulted. No prohibited-material encounter was identified during this writing step.

\subsection{LLM Usage}
LLM-based agents assisted with research proposals, source implementation, framing, literature-metadata checking, and manuscript preparation. The exploratory alternative implementations did not yield usable comparative scores; the evaluated method remained the supplied reference. For this manuscript, an LLM inspected saved source and evaluator evidence, selected the bounded empirical thesis, generated static plotting/table code, drafted and revised the text, and ran grounding and LaTeX checks. It did not rerun the final experiments or create new performance measurements. Literature claims were limited to consulted allowed abstracts and the explicitly retrieved factorization paper. No human review, human-conducted experiment, or independent external replication is implied.
```
