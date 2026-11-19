# Agentic evidence audit packet

- generated_at: `2026-11-13T19:24:17.833207+00:00`
- paper_dir: `work/results/t07/codex/20261113_154315/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261113_180124-paper_evidence_audit_round_2-584s_del/workspace`

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
    "anchored_references": 113,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 163,
    "resolved_references": 81,
    "total_references": 194
  },
  "ok": true,
  "pdf_path": "work/results/t07/codex/20261113_154315/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 113,
    "dangling_references": 0,
    "manifests_checked": 18,
    "resolved_references": 81,
    "total_references": 194
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "The final evaluation completed but did not qualify; no conditional reaggregation changes this status.",
      "source_ids": [
        "final.qualification.status",
        "final.qualification.outcome",
        "final.qualification.correct"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The final evidence covers ten fixed benchmark cases, four Leaderboard-derived and six HELM-derived, with seeds 5003, 7001 and 9001 and budgets 8, 16 and 32.",
      "evidence_refs": [
        "@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]",
        "@evidence[[source_evidence/final_data_manifest.json]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Primary and all reference predictions are absent for Commonsense at seeds 5003 and 9001. Constant, copy, permuted and selected-item-mean structural checks fail there, while fitted uniform selection is available. The underlying exception is not identified by these records.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/audit]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Common-support comparisons use 28 of 30 case-seed pairs, with Commonsense supported only at seed 7001. All other cases have three supported seeds.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/common_support]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Reported primary aggregate MAE is 0.08801465854359276 and RMSE 0.09789336720441476, including missing-output defaults.",
      "evidence_refs": [
        "@evidence[[source_evidence/evaluate_final.py#L870-L873]]",
        "@evidence[[source_evidence/evaluate_final.py#L1005-L1042]]"
      ],
      "source_ids": [
        "final.metric.mae",
        "final.metric.rmse",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Spearman1904",
        "Kendall1938"
      ],
      "claim": "Reported primary Spearman is 0.7328732236748521 and Kendall tau-b 0.5943160224743321; these include missing-record defaults.",
      "source_ids": [
        "final.metric.spearman",
        "final.metric.kendall_tau_b"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Reported fitted-uniform MAE 0.044910877034389785, selected-mean MAE 0.10836174574059959, uniform-mean MAE 0.1335974367939037, IRT MAE 0.1186668212839868, anchor MAE 0.22047382735923254, and source-mean MAE 0.1643825693696333 have different missing-output exposure and do not form a measured-only superiority ranking.",
      "source_ids": [
        "final.metric.no_diversity_mae",
        "final.metric.no_calibration_mae",
        "final.metric.uniform_mae",
        "final.metric.irt_mae",
        "final.metric.anchor_mae",
        "final.metric.source_mean_mae",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Structural-control failure summary is 0.041666666666666664, missing-evaluation fraction is 0.011049723756906077, and checked replay maximum discrepancy is zero. The first two are evaluator-defined summaries, not rates over independent target models or case-seed pairs.",
      "evidence_refs": [
        "@evidence[[source_evidence/evaluate_final.py#L1070-L1076]]"
      ],
      "source_ids": [
        "final.metric.control_failure_rate",
        "final.metric.missing_episode_rate",
        "final.metric.reset_max_abs_error"
      ]
    },
    {
      "citation_keys": [
        "Efron1979"
      ],
      "claim": "The stored primary-minus-anchor contrast is -0.0769036132600842 with endpoints [-1,1]; these are fallback endpoints because pairing is incomplete, not an informative confidence interval. Its missing-record convention differs from separately penalized marginal MAEs.",
      "evidence_refs": [
        "@evidence[[source_evidence/evaluate_final.py#L1034-L1068]]"
      ],
      "source_ids": [
        "final.metric.delta_anchor_mae",
        "final.metric.delta_anchor_ci_low",
        "final.metric.delta_anchor_ci_high",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Available-pair primary MAE is lower than fitted-uniform MAE in nine cases; MedQA is the exception at 0.0574 versus 0.0530. This is descriptive and includes singleton-support Commonsense.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/case_mae]]",
        "@evidence[[build_paper_artifacts.py]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Conditional BBH primary and fitted-uniform MAEs are 0.0308 and 0.0570, and MATH MAEs are 0.0603 and 0.0624. MuSR anchor error is heterogeneous relative to the other cases.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/case_mae]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Under equal-source/equal-case and within-case available-seed normalization, primary MAEs at budgets 8/16/32 are 0.0438507255604756, 0.03333117402076665 and 0.027776433747489636.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/budget_mae/0]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "On identical common support, fitted-uniform MAEs at budgets 8/16/32 are 0.05983060181043318, 0.04388863282142454 and 0.03283671741622329.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/budget_mae/1]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Selected-item mean MAEs at budgets 8/16/32 are 0.13207754853140033, 0.10495817584576625 and 0.08507833899220836; uniform-mean MAEs are 0.10821494499086409, 0.08229789663800609 and 0.05556974653061864. Uniform raw means have lower MAE at every displayed budget, whereas fitted selection reverses the conditional ordering.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/budget_mae]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Conditional primary Spearman correlations at budgets 8/16/32 are 0.7787133623969075, 0.8485275353348883 and 0.8858252382784845. Selected-mean correlations are 0.7805746798716318, 0.8461155247695583 and 0.8818752839767907. Reconstruction changes absolute-score error much more than ranking in this retained evidence, without isolating a particular reconstruction component.",
      "evidence_refs": [
        "@evidence[[derived_results.json#/budget_spearman]]",
        "@evidence[[derived_results.json#/budget_mae]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "All numerical cells of supplementary case and budget tables and both quantitative figures are deterministic transformations of recorded final target means and predictions on their declared common support. Seed dots are descriptive, with overlapping model populations, and are not confidence intervals.",
      "evidence_refs": [
        "@evidence[[derived_results.json]]",
        "@evidence[[build_paper_artifacts.py]]",
        "@evidence[[tables/case_mae.tex]]",
        "@evidence[[tables/budget_metrics.tex]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The supplementary seed table retains every primary case-seed record, recorded target/group counts, and budget-averaged MAE/RMSE/Spearman/Kendall. Missing rows remain missing. The exhaustive CSV separates each budget, condition and reference with availability/structural status, using the evaluator's zero rank-correlation convention for exactly constant vectors.",
      "evidence_refs": [
        "@evidence[[tables/primary_seed_metrics.tex]]",
        "@evidence[[complete_metrics.csv]]",
        "@evidence[[build_paper_artifacts.py]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The remaining reported diagnostic MAEs are 0.22204546910278564 for constant observations, 0.15448451324975213 for copied observations, 0.1005045540030643 for permuted observations and 0.02807015578570595 for the single checked replay; they are not ordinary independent target-accuracy estimates.",
      "source_ids": [
        "final.metric.constant_mae",
        "final.metric.copy_mae",
        "final.metric.permuted_mae",
        "final.metric.reset_mae"
      ]
    },
    {
      "citation_keys": [
        "Elfving1952",
        "Kiefer1960"
      ],
      "claim": "The evaluated source-only selector uses equal total group weights, empirical score covariance, diagonal nugget 0.1 max(mu(1-mu),0.05), and greedy squared conditional covariance divided by conditional item variance floored at 1e-12. It uses low-rank updates and no target-adaptive acquisition.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L52-L91]]"
      ],
      "grounding_note": "Registry id identifies the delivered configuration only; readable code is substantive support, not the metric value or hash.",
      "source_ids": [
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [
        "Hoerl1970"
      ],
      "claim": "The linear branch fits row-unweighted centered ridge regression with an intercept and shrinkage. Per-budget strength grid is 0.1/1/10 and shrinkage grid 0/0.5/1, selected by group-weighted source-held-out squared error.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L94-L100]]",
        "@evidence[[source_evidence/selected_method.py#L201-L270]]"
      ],
      "source_ids": [
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [
        "Andersen1970"
      ],
      "claim": "The source profile branch fixes smoothed-logit abilities, initializes difficulties from clipped group-weighted item means, and uses eight bounded Newton updates with difficulty penalty 0.01. It is not joint or conditional maximum-likelihood Rasch estimation.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L103-L115]]"
      ],
      "source_ids": [
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Profiles interpolate Rasch probabilities with binary source responses and clip at 1e-6. Each source contributes five ability-offset particles with offsets h*(-2,-1,0,1,2) and prior proportions (1,4,6,4,1)/16; total mass is equal per source group.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L118-L155]]"
      ],
      "source_ids": [
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Posterior normalization uses log-sum-exp and adds the exact observed total to the expected unqueried total. Every prefix recomputes from the original prior; the posterior is not a calibrated empirical uncertainty interval.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L158-L191]]",
        "@evidence[[source_evidence/selected_method.py#L336-L365]]"
      ],
      "source_ids": [
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [
        "Varma2006",
        "Arlot2010",
        "Stone1974"
      ],
      "claim": "At most three group-disjoint source folds choose residual weight 0/0.5/0.75, offset scale 0/0.5 and blend 0/0.5/1, by group-balanced MAE across budgets, with simpler tie-breaking. One-group fallback is ridge strength one, shrinkage one and zero profile blend. No final fitted blend logs or independent final component ablations are available.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L201-L287]]"
      ],
      "source_ids": [
        "result.top_program_01",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The uniform fitted control changes acquisition and refits/tunes reconstruction. The selected-mean control returns the raw mean on the primary order. The uniform mean uses the same prescribed seeded uniform order as the fitted uniform control. These compare configured procedures or whole reconstruction, not isolated particle or selector effects.",
      "evidence_refs": [
        "@evidence[[source_evidence/selected_method.py#L57-L62]]",
        "@evidence[[source_evidence/selected_method.py#L327-L365]]",
        "@evidence[[source_evidence/evaluate_final.py#L774-L793]]",
        "@evidence[[source_evidence/evaluate_final.py#L924-L944]]"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [
        "Roberts2017",
        "BenDavid2010"
      ],
      "claim": "The evaluator uses seed-hashed approximately 70/30 model-group splits and equal source-domain, within-domain case, seed and budget weights. Metadata grouping is conservative and cannot prove full training-lineage separation.",
      "evidence_refs": [
        "@evidence[[source_evidence/evaluate_final.py#L685-L708]]",
        "@evidence[[source_evidence/evaluate_final.py#L1005-L1018]]",
        "@evidence[[source_evidence/final_data_manifest.json]]"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Vivek2024"
      ],
      "claim": "The anchor reference clusters centered normalized response vectors using one initialization and at most 30 iterations; scores are repres

[truncated after 14000 chars]
```

## paper_data summary

```json
{
  "available": true,
  "claim_count": 0,
  "downstream_study": null,
  "final_evaluation": {
    "correct": false,
    "limitations": [
      "Final evaluation completed but did not qualify; search success does not establish final qualification.",
      "Non-qualification may reflect performance, uncertainty, validity, adaptivity, or other criteria; report only causes supported by evaluator evidence.",
      "Retained metrics do not independently establish claims whose qualification or validity checks failed. Missing gate diagnostics remain unknown."
    ],
    "outcome": "not_qualified",
    "status": "completed"
  },
  "grounding_source_count": 34,
  "paper_profile": "standalone",
  "totals": {
    "attempts": 3,
    "correct_programs": 1,
    "evaluated_programs": 3,
    "ideas": 3
  }
}
```

## references provenance summary

```json
{
  "campaign_results_dir": "work/results/t07/codex/20261113_154315/investigation",
  "count": 27,
  "generated_at": "2026-11-13T18:27:39.477580+00:00",
  "queries": [
    "Exact DOI: 10.48550/arXiv.2309.08638",
    "Exact DOI: 10.48550/arXiv.2402.14992",
    "Exact DOI: 10.48550/arXiv.2407.12844",
    "Exact DOI: 10.48550/arXiv.2409.03563",
    "Exact DOI: 10.48550/arXiv.2410.05952",
    "Exact DOI: 10.48550/arXiv.2211.09110",
    "Exact DOI: 10.48550/arXiv.2406.01574",
    "Exact DOI: 10.1080/00401706.1970.10488634",
    "Exact DOI: 10.1214/aoms/1177729442",
    "Exact DOI: 10.4153/CJM-1960-030-4",
    "Exact DOI: 10.1111/j.2517-6161.1970.tb00842.x",
    "Exact DOI: 10.1111/j.2517-6161.1977.tb01600.x",
    "Exact DOI: 10.1007/978-0-387-84858-7",
    "Exact DOI: 10.1007/978-0-387-45528-0",
    "Exact DOI: 10.1214/aos/1176344552",
    "Exact DOI: 10.1093/biomet/63.3.581",
    "Exact DOI: 10.1002/9781119013563",
    "Exact DOI: 10.1111/ecog.02881",
    "Exact DOI: 10.1186/1471-2105-7-91",
    "Exact DOI: 10.1214/09-SS054",
    "Exact DOI: 10.1111/j.2517-6161.1974.tb00994.x",
    "Exact DOI: 10.1093/biomet/30.1-2.81",
    "Exact DOI: 10.2307/1412159",
    "Exact DOI: 10.1007/s10994-009-5152-4",
    "Exact DOI: 10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2",
    "Exact authoritative source: ERIC ED458219, Rasch/2PL and item-information foundations",
    "Exact permitted collection source: Hugging Face Open LLM Leaderboard Space"
  ],
  "reference_query_plan": {},
  "reference_query_plans": [],
  "references": [
    {
      "abstract": "Modern language models often exhibit powerful but brittle behavior, leading to the development of larger and more diverse benchmarks to reliably assess their behavior.Here, we suggest that model performance can be benchmarked and elucidated with much smaller evaluation sets.We first show that in six popular language classification benchmarks, model confidence in the correct class on many pairs of points is strongly correlated across models.We build upon this phenomenon to propose Anchor Point Selection, a technique to select small subsets of datasets that capture model behavior across the entire dataset.Anchor points reliably rank models: across 87 diverse language model-prompt pairs, evaluating models using 1-30 anchor points outperforms uniform sampling and other baselines at accurately ranking models.Moreover, just a dozen anchor points can be used to estimate model per-class predictions on all other points in a dataset with low error, sufficient for gauging where the model is likely to fail.Lastly, we present Anchor Point Maps for visualizing these insights and facilitating comparisons of the performance of different models on various regions within the dataset distribution.",
      "citation_key": "Vivek2024",
      "consulted_scope": "OpenAlex title, metadata and abstract where available; no citation links traversed",
      "doi": "10.48550/arXiv.2309.08638",
      "id": "ref.openalex.W4411630215",
      "paper_id": "https://openalex.org/W4411630215",
      "query": "Exact DOI: 10.48550/arXiv.2309.08638",
      "retrieved_at": "2026-11-13T18:27:33.577497+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2309.08638",
      "title": "Anchor Points: Benchmarking Models with Much Fewer Examples",
      "venue": "Conference of the European Chapter of the Association for Computational Linguistics",
      "year": 2024
    },
    {
      "abstract": "The versatility of large language models (LLMs) led to the creation of diverse benchmarks that thoroughly test a variety of language models' abilities. These benchmarks consist of tens of thousands of examples making evaluation of LLMs very expensive. In this paper, we investigate strategies to reduce the number of evaluations needed to assess the performance of an LLM on several key benchmarks. For example, we show that to accurately estimate the performance of an LLM on MMLU, a popular multiple-choice QA benchmark consisting of 14K examples, it is sufficient to evaluate this LLM on 100 curated examples. We release evaluation tools and tiny versions of popular benchmarks: Open LLM Leaderboard, MMLU, HELM, and AlpacaEval 2.0. Our empirical analysis demonstrates that these tools and tiny benchmarks are sufficient to reliably and efficiently reproduce the original evaluation results.",
      "citation_key": "Polo2024",
      "consulted_scope": "OpenAlex title, metadata and abstract where available; no citation links traversed",
      "doi": "10.48550/arXiv.2402.14992",
      "id": "ref.openalex.W4392181972",
      "paper_id": "https://openalex.org/W4392181972",
      "query": "Exact DOI: 10.48550/arXiv.2402.14992",
      "retrieved_at": "2026-11-13T18:27:33.383236+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2402.14992",
      "title": "tinyBenchmarks: evaluating LLMs with fewer examples",
      "venue": "arXiv (Cornell University)",
      "year": 2024
    },
    {
      "abstract": "Large Language Models (LLMs) vary in their abilities on a range of tasks. Initiatives such as the Open LLM Leaderboard aim to quantify these differences with several large benchmarks (sets of test items to which an LLM can respond either correctly or incorrectly). However, high correlations within and between benchmark scores suggest that (1) there exists a small set of common underlying abilities that these benchmarks measure, and (2) items tap into redundant information and the benchmarks may thus be considerably compressed. We use data from n > 5000 LLMs to identify the most informative items of six benchmarks, ARC, GSM8K, HellaSwag, MMLU, TruthfulQA and WinoGrande (with d = 28,632 items in total). From them we distill a sparse benchmark, metabench, that has less than 3% of the original size of all six benchmarks combined. This new sparse benchmark goes beyond point scores by yielding estimators of the underlying benchmark-specific abilities. We show that these estimators (1) can be used to reconstruct each original individual benchmark score with, on average, 1.24% root mean square error (RMSE), (2) reconstruct the original total score with 0.58% RMSE, and (3) have a single underlying common factor whose Spearman correlation with the total score is r = 0.94.",
      "citation_key": "Kipnis2025",
      "consulted_scope": "OpenAlex title, metadata and abstract where available; no citation links traversed",
      "doi": "10.48550/arXiv.2407.12844",
      "id": "ref.openalex.W4406058560",
      "paper_id": "https://openalex.org/W4406058560",
      "query": "Exact DOI: 10.48550/arXiv.2407.12844",
      "retrieved_at": "2026-11-13T18:27:33.762496+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2407.12844",
      "title": "metabench -- A Sparse Benchmark of Reasoning and Knowledge in Large Language Models",
      "venue": "arXiv (Cornell University)",
      "year": 2024
    },
    {
      "abstract": "Predicting the performance of LLMs on individual task instances is essential to ensure their reliability in high-stakes applications. To do so, a possibility is to evaluate the considered LLM on a set of task instances and train an assessor to predict its performance based on features of the instances. However, this approach requires evaluating each new LLM on a sufficiently large set of task instances to train an assessor specific to it. In this work, we leverage the evaluation results of previously tested LLMs to reduce the number of evaluations required to predict the performance of a new LLM. In practice, we propose to test the new LLM on a small set of reference instances and train a generic assessor which predicts the performance of the LLM on an instance based on the performance of the former on the reference set and features of the instance of interest. We conduct empirical studies on HELM-Lite and KindsOfReasoning, a collection of existing reasoning datasets that we introduce, where we evaluate all instruction-fine-tuned OpenAI models until the January 2024 version of GPT4. When predicting performance on instances with the same distribution as those used to train the generic assessor, we find this achieves performance comparable to the LLM-specific assessors trained on the full set of instances. Additionally, we find that randomly selecting the reference instances performs as well as some advanced selection methods we tested. For out of distribution, however, no clear winner emerges and the overall performance is worse, suggesting that the inherent predictability of LLMs is low.",
      "citation_key": "Pacchiardi2024",
      "consulted_scope": "OpenAlex title, metadata and abstract where available; no citation links traversed",
      "doi": "10.48550/arXiv.2409.03563",
      "id": "ref.openalex.W4403556531",
      "paper_id": "https://openalex.org/W4403556531",
      "query": "Exact DOI: 10.48550/arXiv.2409.03563",
      "retrieved_at": "2026-11-13T18:27:33.628072+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2409.03563",
      "title": "100 instances is all you need: predicting the success of a new LLM on unseen data by testing on a few instances",
      "venue": "arXiv (Cornell University)",
      "year": 2024
    },
    {
      "abstract": "As large language models (LLMs) become increasingly versatile, numerous large scale benchmarks have been developed to thoroughly assess their capabilities. These benchmarks typically consist of diverse datasets and prompts to evaluate different aspects of LLM performance. However, comprehensive evaluations on hundreds or thousands of prompts incur tremendous costs in terms of computation, money, and time. In this work, we investigate strategies to improve evaluation efficiency by selecting a subset of examples from each benchmark using a learned policy. Our approach models the dependencies across test examples, allowing accurate prediction of the evaluation outcomes for the remaining examples based on the outcomes of the selected ones. Consequently, we only need to acquire the actual evaluation outcomes for the selected subset. We rigorously explore various subset selection policies and introduce a novel RL-based policy that leverages the captured dependencies. Empirical results demonstrate that our approach significantly reduces the number of evaluation prompts required while maintaining accurate performance estimates compared to previous methods.",
      "citation_key": "Li2025",
      "consulted_scope": "OpenAlex title, metadata and abstract where available; no citation links traversed",
      "doi": "10.48550/arXiv.2410.05952",
      "id": "ref.openalex.W4403344243",
      "paper_id": "https://openalex.org/W4403344243",
      "query": "Exact DOI: 10.48550/arXiv.2410.05952",
      "retrieved_at": "2026-11-13T18:27:34.649008+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2410.05952",
      "title": "Active Evaluation Acquisition for Efficient LLM Benchmarking",
      "venue": "arXiv (Cornell University)",
      "year": 2024
    },
    {
      "abstract": "Language models (LMs) are becoming the foundation for almost all major language technologies, but their capabilities, limitations, and risks are not well understood. We present Holistic Evaluation of Language Models (HELM) to improve the transparency of language models. First, we taxonomize the vast space of potential scenarios (i.e. use cases) and metrics (i.e. desiderata) that are of interest for LMs. Then we select a broad subset based on coverage and feasibility, noting what's missing or underrepresented (e.g. question answering for neglected English dialects, metrics for trustworthiness). Second, we adopt a multi-metric approach: We measure 7 metrics (accuracy, calibration, robustness, fairness, bias, toxicity, and efficiency) for each of 16 core scenarios when possible (87.5% of the time). This ensures metrics beyond accuracy don't fall to the wayside, and that trade-offs are clearly exposed. We also perform 7 targeted evaluations, based on 26 targeted scenarios, to analyze specific aspects (e.g. reasoning, disinformation). Third, we conduct a large-scale evaluation of 30 prominent language models (spanning open, limited-access, and closed models) on all 42 scenarios, 21 of which were not previously used in mainstream LM evaluation. Prior to HELM, models on average were evaluated on just 17.9% of the core HELM scenarios, with some prominent models not sharing a single scenario in common. We improve this to 96.0%: now all 30 models have been densely benchmarked on the same core scenarios and metrics under standardized conditions. Our evaluation surfaces 25 top-level findings. For full transparency, we release all raw model prompts and completions publicly for further analysis, as well as a general modular toolkit. We intend for HELM to be a living benchmark for the community, continuously updated with new scenarios, metrics, and models.",
      "citation_key": "Liang2023",
      "consulted_scope": "OpenAlex title, metadata and abstract where available; no citation links traversed",
      "doi": "10.48550/arXiv.2211.09110",
      "id": "ref.openalex.W4320003957",
      "paper_id": "https://openalex.org/W4320003957",
      "query": "Exact DOI: 10.48550/arXiv.2211.09110",
      "retrieved_at": "2026-11-13T18:27:34.917766+00:00",
      "source_url": "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2211.09110",
      "title": "Holistic Evaluation of Language Models",
      "venue": "arXiv (Cornell University)",
      "year": 2022
    },
    {
      "abstract": "In the age of large-scale language models, benchmarks like the Massive Multitask Language Understanding (MMLU) have been pivotal in pushing the boundaries of what AI can achieve in langua

[truncated after 14000 chars]
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


\usepackage{paper,times}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,booktabs,graphicx,subcaption}
\usepackage{hyperref,url}
\title{Score-Targeted Item Selection for LLM Benchmark Prediction:\\Accuracy and Evaluation Limits}
\author{}
\newcommand{\clip}{\operatorname{clip}_{[0,1]}}
\newcommand{\sigmoid}{\operatorname{sigmoid}}
\begin{document}
\maketitle

\begin{abstract}
Predicting a language model's benchmark score from a few responses can reduce evaluation cost, but prediction accuracy and evaluation completeness are different requirements. We study a source-only estimator that selects items by their conditional covariance with the full score and combines ridge prediction with an optional Rasch-residual profile mixture. A frozen evaluation covers ten fixed benchmark cases, three grouped model splits, and budgets of 8, 16, and 32 items. On common available support, the estimator's mean absolute error decreases from 0.0439 to 0.0278 across these budgets; its Spearman correlation increases from 0.7787 to 0.8858. These are conditional descriptions, not qualified overall results. The evaluation completed but failed qualification: primary and reference predictions are missing for two Commonsense splits, and matched structural checks fail. The reported aggregate MAE of 0.0880 includes missing-output penalties. We separate measured prediction errors, scoring defaults, and unresolved diagnostics, establishing an evidence-bounded assessment rather than an overall selection-advantage claim.
\end{abstract}




\section{Introduction}
Full-benchmark evaluation repeatedly measures the same item universe across language models, checkpoints, or inference settings. Historical item-level responses may therefore contain useful information about which questions distinguish model behavior. The practical question is whether a new model can answer a small, fixed subset while a source-trained estimator reconstructs its full score and preserves model rankings. This setting differs from accelerating generation: the savings come from querying fewer items, not from changing the evaluated language model.

Existing benchmark-compression methods exploit response similarity, latent ability, or predictive dependencies \citep{Vivek2024,Polo2024,Kipnis2025,Pacchiardi2024,Li2025}. A complementary design objective is to select questions directly for the scalar score of interest. An item can distinguish source response patterns without being especially informative about their average. Conversely, correlated items can remain useful if their residual variation predicts that average. This motivates conditioning on already selected items and greedily targeting the remaining covariance with the full source score.

We study this design together with a source-trained reconstruction family. A linear ridge predictor provides a simple fallback; a group-balanced mixture of Rasch-shrunk source profiles offers nonlinear response-pattern matching. Both use the same nested item prefixes, and their combination is selected using source-group holdouts. The scientific hypothesis is that source response structure can improve score reconstruction at a fixed query budget. The available evaluation does not isolate a benefit from the profile component, nor does it establish a generally advantageous selector.

The decisive evidence boundary is evaluation integrity. The frozen assessment completed but did not qualify. Missing primary predictions coincide with missing reference predictions in part of the Commonsense evidence; matched structural checks also fail there. The retained predictions can describe accuracy on available pairs, but cannot supply the missing outcomes or restore qualification. Treating penalty-scored aggregate errors as ordinary prediction errors would obscure this distinction.



Our contributions are consequently bounded: a precise description of a score-targeted, source-only reconstruction method; a common-support comparison across fixed benchmarks and item budgets; and an explicit account of how incomplete records restrict the interpretation of those comparisons. We report the unsuccessful qualification alongside the conditional results rather than selecting whichever summary gives the most favorable ordering. The resulting study addresses what these measurements establish, and what remains unmeasured.

\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{figures/method_and_evidence_overview.png}
\caption{Source-only item design and score reconstruction, with an explicit evidence boundary. Source responses determine a fixed nested item order, ridge fitting, and an optional residual-profile mixture. Target responses update prediction only. Measured prediction error is distinguished from missing records and failed checks; the latter cannot be repaired by conditioning on available predictions.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\paragraph{Few-item language-model evaluation.}
Anchor Points selects a small set of representative examples from cross-model response structure \citep{Vivek2024}. tinyBenchmarks studies efficient score estimation with curated subsets, and metabench uses latent abilities to compress reasoning and knowledge evaluation \citep{Polo2024,Kipnis2025}. Reference-instance assessors predict model performance on other instances \citep{Pacchiardi2024}; learned evaluation-acquisition policies model dependencies between test outcomes \citep{Li2025}. Our fixed source-only order is not target-adaptive acquisition. The local anchor and IRT references below are explicitly defined implementations, not certified reproductions of these published systems.

\paragraph{Design and reconstruction.}
Choosing observations for a scalar target relates to optimal allocation in regression \citep{Elfving1952}, whereas information criteria for a whole parameter vector address a different objective \citep{Kiefer1960}. Our empirical covariance rule is a regularized linear-prediction heuristic, not an optimal-design theorem for shifted binary responses. Ridge regression supplies a stabilized linear estimator \citep{Hoerl1970}; standard statistical-learning and probabilistic-modeling texts provide broader background \citep{Hastie2009,Bishop2006}. The profile model is a finite mixture, but it does not fit mixture weights by expectation maximization \citep{Dempster1977}. Likewise, its fixed-ability difficulty fitting should not be confused with conditional maximum-likelihood estimation \citep{Andersen1970}.

\paragraph{Assessment under dependence and missingness.}
Cross-validation distinguishes choosing a predictor from assessing it \citep{Stone1974,Arlot2010}; evaluating a configuration on the same validation evidence used to tune it can be optimistic \citep{Varma2006}. Grouped validation addresses dependence, but the blocking scheme determines which extrapolation question is tested \citep{Roberts2017}. Domain-shift theory further motivates caution about transferring source accuracy to new response distributions \citep{BenDavid2010}. Missing-data inference requires assumptions about the missingness process \citep{Rubin1976,Little2019}; we make no such assumptions here. HELM motivates multi-metric evaluation \citep{Liang2023}, and distinct benchmark constructions, such as MMLU-Pro, should not be conflated with the fixed MMLU case studied here \citep{Wang2024}. These distinctions motivate reporting error, ranking, and evidence availability separately.

\section{Method}
\subsection{Problem Setup and Design Rationale}
Let $X\in\{0,1\}^{S\times N}$ contain complete item responses of source models, and let $y\in\{0,1\}^{N}$ denote a target model's responses. Its reference score is $s(y)=N^{-1}\sum_{j=1}^{N}y_j$. Only $y_Q$ is observable to the estimator, for a subset $Q$ of size $b\ll N$. Source rows have supplied group labels $g(i)$; target identities, target groups, and full target scores are unavailable during fitting and prediction. The goal is a bounded estimate $\hat s_b(y_Q)$ with small absolute and squared score error and accurate target-model ordering.

The studied budgets are $b\in\{8,16,32\}$. A single source-only order gives nested prefixes $Q_b$, with no repeated items. This is not a claim that these budgets suffice for every benchmark. The rationale is to combine task-directed acquisition with conservative reconstruction: selection targets the full-score functional, while a tuned linear fallback limits reliance on an overly specific source-profile model. Equal total source-group mass reduces the influence of densely represented groups in selection and profile priors, without asserting that groups perfectly recover training ancestry.



\subsection{Score-Targeted Fixed Prefixes}
For $G$ source groups with sizes $n_g$, define $w_i=(G n_{g(i)})^{-1}$, source item means $\mu_j=\sum_i w_iX_{ij}$, and full source scores $t_i=N^{-1}\sum_jX_{ij}$. With $\bar t=\sum_iw_it_i$, form
\begin{equation}
 Z_{ij}=\sqrt{w_i}(X_{ij}-\mu_j),\qquad
 u_i=\sqrt{w_i}(t_i-\bar t),\quad
 C=Z^\top Z+D,\quad c=Z^\top u,
\end{equation}
where $D_{jj}=0.1\max\{\mu_j(1-\mu_j),0.05\}$. For the selected prefix $Q$, residual covariance and variance are
\begin{equation}
 c_{j\mid Q}=c_j-C_{jQ}C_{QQ}^{-1}c_Q,\qquad
 v_{j\mid Q}=C_{jj}-C_{jQ}C_{QQ}^{-1}C_{Qj}.
\end{equation}
The next item maximizes $c_{j\mid Q}^{\,2}/\max(v_{j\mid Q},10^{-12})$ among unselected items. This is the reduction in residual variance for a linear scalar-score predictor under the empirical covariance model. It is neither an information guarantee for the true target distribution nor a causal statement about particular questions.


The implementation updates residual quantities through a low-rank pivoted factorization instead of materializing the dense item covariance. Selection is rebuilt using only training groups inside every source-validation fold. The final fit repeats it on all supplied source rows. Crucially, observing target answers never changes the item order or its hyperparameters.

\subsection{Linear and Residual-Profile Reconstruction}
The linear branch regresses source full scores on the selected binary responses. Centering features at their unweighted source mean $\bar x_Q$ and scores at $\bar t_{\rm row}$ gives
\begin{equation}
 \beta_b=(X_{Q,c}^{\top}X_{Q,c}+\lambda I)^{-1}X_{Q,c}^{\top}(t-\bar t_{\rm row}),\qquad
 \hat s^{\rm lin}_b=\clip\!\left[\bar t_{\rm row}+\gamma(y_Q-\bar x_Q)^\top\beta_b\right].
\end{equation}
The ridge fit itself is row-unweighted; group balancing is used for selecting configurations, not silently substituted into this regression. Per-budget $\lambda\in\{0.1,1,10\}$ and $\gamma\in\{0,0.5,1\}$ minimize source-held-out group-weighted squared error.




The nonlinear branch retains source response profiles while smoothing them with a Rasch response model, a logistic ability--difficulty family \citep[Chap.~2]{Baker2001}. Our custom fit fixes source abilities at $\theta_i=\operatorname{logit}[(\sum_jX_{ij}+0.5)/(N+1)]$. Item difficulties $d_j$ are fitted by group-weighted Bernoulli likelihood with a quadratic penalty. Write $r_{ij}=\sigmoid(\theta_i-d_j)$ and
\begin{equation}
 p_{ij}=\operatorname{clip}_{[\epsilon,1-\epsilon]}
       [(1-\rho)r_{ij}+\rho X_{ij}],\qquad
 p_{i\ell j}=\sigmoid[\operatorname{logit}(p_{ij})+a_\ell].
\end{equation}
The offsets are $a_\ell=h(-2,-1,0,1,2)_\ell$ with prior proportions $(1,4,6,4,1)/16$. Each source group's total prior mass is equal; within a group it is divided equally across source rows. Thus this is a mixture of source-derived response profiles and ability offsets, not a new language-model architecture.


For observed responses, a particle $k=(i,\ell)$ receives posterior mass
\begin{equation}
 \omega_k(y_Q)\ \propto\ \pi_k\prod_{j\in Q}p_{kj}^{y_j}(1-p_{kj})^{1-y_j},\qquad
 \hat s^{\rm prof}_b=\frac{\sum_{j\in Q}y_j+\sum_k\omega_k\sum_{j\notin Q}p_{kj}}{N}.
\label{eq:profile}
\end{equation}
The observed contribution is exact; only unqueried responses are reconstructed. Log-sum-exp normalization stabilizes the calculation. Every request uses the original prior and the complete current prefix, so cumulative responses are not counted twice. This model-based posterior is not an empirically calibrated uncertainty interval.


The output is $(1-\alpha)\hat s^{\rm lin}_b+\alpha\hat s^{\rm prof}_b$. Source tuning considers $\rho\in\{0,0.5,0.75\}$, $h\in\{0,0.5\}$, and $\alpha\in\{0,0.5,1\}$, using at most three group-disjoint folds. It selects one profile/blend configuration across budgets by equal-group held-out MAE. Ties favor smaller blend weight, offset scale, then residual weight. A zero blend is an explicit linear fallback. The final evidence does not record which blend was used in each fit, so it cannot demonstrate a nonzero profile contribution.


\subsection{What a Fixed Prefix Can Identify}
The reconstruction problem has an information constraint independent of the chosen statistical model. If two target models have identical queried responses, the interface supplies no information that could distinguish them, so the estimator returns the same value. In particular, neither target identities nor target group memberships are additional inputs to prediction. The source-trained mappings and particle priors are also identical for these rows. A fixed prefix therefore cannot distinguish targets that agree on observed items but differ elsewhere. We do not measure the prevalence of such pairs in the final evidence: the available score records do not supply the queried response patterns needed for that analysis. This source-inspectable property explains why score covariance is a design rationale rather than a target-level guarantee. Undocumented target response patterns may remain indistinguishable even when source-held-out prediction looks accurate.


The two reconstruction branches make different assumptions about this unresolved information. The linear branch extends source score relationships through a regularized affine map. The profile branch assigns probability to source-shaped patterns with ability offsets, then averages their unobserved totals. The convex fallback prevents source tuning from requiring the profile branch, but does not protect against shifts absent from every validation group. Neither branch acquires new target information beyond the prescribed prefix. Increasing the number of particles or retuning the blend therefore cannot by itself resolve identical-prefix ambiguity. Conversely, replacing the item order may change which targets become indistinguishable, but its effect cannot be assigned to acquisition alone when the reconstruction is also refitted. This motivates keeping the procedure-level and matched-order comparisons separate in the results.

\section{Evaluation Protocol and Evidence Availability}
\subsection{Fixed Benchmarks and Grouped Model Holdouts}

The final assessment contains four Open LLM Leaderboard-derived cases (BBH, GPQA, MuSR, and OpenLLM Math) and six HELM-derived cases (Commonsense, GSM, LegalBench, MATH, MedQA, and MMLU). The upstream collections are documented by \citet{OpenLLMLeaderboard} and \citet{Liang2023}, respectively; our case identities and filtering come from the supplied data manifest. We retain these staged case names rather than asserting identity with every similarly named public benchmark. Each case uses a fixed binary item universe. The question is prediction for held-out models on that universe, not generalization to newly sampled questions or unseen benchmark distributions.



Seeds 5003, 7001, and 9001 define model-group splits. The evaluator orders groups by a seed-dependent hash, assigns approximately 70\% of groups to the source side, and withholds the rest as targets. Group construction uses available provenance and conservative family/provider information. It is a metadata heuristic, not a proof of disjoint pretraining or complete ancestry separation. The estimator sees only opaque source-group labels. Source tuning is internal to a fit; final targets are not used to select its settings. Repeated seeds reuse model populations and are not independent populations.




\subsection{Comparators and Control Semantics}
The \emph{fitted uniform-selection control} replaces the score-targeted order with a seeded uniform nested order, rebuilding selection and tuning in each fold. It keeps the reconstruction family, not necessarily the fitted predictor: hyperparameters can change. The \emph{selected-item mean} retains the primary order and returns the raw observed mean, removing reconstruction as a whole rather than an affine calibration layer. The \emph{uniform sample mean} averages responses on the same seeded uniform order used by the fitted uniform control, permitting a second matched-order reconstruction comparison.




The anchor reference clusters centered, normalized item response vectors and estimates scores from representatives weighted by assigned cluster sizes. The IRT reference fits a penalized two-parameter logistic response model, chooses items by fitted information near zero ability, and infers target ability from queried responses; the response family and item-information definition follow standard IRT terminology \citep[Chaps.~2,6]{Baker2001}. These references use the same query budgets, but they are local comparators, not official reproductions of Anchor Points or tinyBenchmarks. A source-mean reference predicts the average source score without target responses. Extended fitting details are in the supplement.


\subsection{Three Distinct Reporting Objects}
We distinguish (i) the evaluator's reported aggregate, (ii) prediction errors computed on common available records, and (iii) qualification and structural diagnostics. In the reported aggregate, the two data sources receive equal mass, cases are equally weighted within source, and seeds and budgets are equally weighted. Missing predictions receive worst-case defaults: MAE and RMSE are set to one, and rank correlations to minus one. Absent baseline records similarly receive MAE one. These defaults are operational penalties, not measured model predictions.



For conditional comparisons, all displayed methods must have predictions for a case--seed pair. We average budgets and targets within that pair and show its seed-level values. Pooled conditional summaries retain equal data-source and case weights, but normalize seed weights over available seeds \emph{within each case}. The same availability intersection is used for error and ranking in the budget view. Commonsense therefore contributes only its available split, rather than being silently omitted or assigned a synthetic loss. This changes the estimand; it does not estimate missing performance. We show descriptive seed dispersion, not confidence bars. Spearman and Kendall correlations describe ordering \citep{Spearman1904,Kendall1938}; neither establishes score calibration.


\section{Results}
\subsection{Completed Evaluation, Failed Qualification}
The final evaluation completed and failed qualification. Table~\ref{tab:aggregate} preserves its scored summaries. Primary MAE is 0.0880 and RMSE is 0.0979; reported Spearman and Kendall correlations are 0.7329 and 0.5943. These summaries include defaults for missing primary records. Their ordering against the fitted uniform-selection MAE of 0.0449 cannot be interpreted as a measured overall selection disadvantage.



\begin{table}[t]
\centering
\caption{Reported final aggregates, \emph{including evaluator defaults}. Errors are score fractions. Missing primary and baseline records receive error one; fitted controls have different availability. These columns are not a measured-only superiority ranking.}
\label{tab:aggregate}
\begin{tabular}{lr@{\qquad}lr}
\toprule
Prediction rule & MAE & Primary diagnostic & Value\\
\midrule
Score-targeted reconstruction & 0.0880 & RMSE & 0.0979\\
Uniform selection + fitting & 0.0449 & Spearman & 0.7329\\
Selected-item mean & 0.1084 & Kendall $\tau_b$ & 0.5943\\
Uniform sample mean & 0.1336 & Structural-control failure summary & 0.0417\\
IRT reference & 0.1187 & Missing-evaluation fraction & 0.0110\\
Anchor reference & 0.2205 & Checked replay discrepancy & 0.0000\\
Source-mean reference & 0.1644 & Qualification & Failed\\
\bottomrule
\end{tabular}
\end{table}


The failure evidence is localized but consequential (Table~\ref{tab:audit}). Primary predictions and all reference predictions are absent for Commonsense at seeds 5003 and 9001. Constant, copied, permuted, and selected-item-mean conditions have recorded predictions there but fail structural checks. The fitted uniform control is available there. The retained record does not identify the underlying exception or root defect, so missing outputs should not be described as an accuracy failure, and the failed checks should not be attributed to a particular implementation error without additional evidence.


\begin{table}[t]
\centering
\caption{Availability and integrity audit of the final evidence. The two affected Commonsense splits are not counted as measured prediction losses in our conditional figures.}
\label{tab:audit}
\begin{tabular}{p{.30\linewidth}p{.60\linewidth}}
\toprule
Evidence & Recorded finding\\
\midrule
Commonsense, seeds 5003/9001 & Primary and reference predictions absent; matched constant, copy, permutation, and selected-mean structural checks fail.\\
Common comparison support & 28 of 30 case--seed pairs; Commonsense uses seed 7001 only.\\
Paired primary--anchor contrast & $-0.0769$ with stored endpoints $[-1,1]$; endpoints are fallback values, not an informative interval.\\
Reset replay & Maximum absolute discrepancy $0$ for the checked replay; not a certificate for other conditions.\\
\bottomrule
\end{tabular}
\end{table}




The paired primary--anchor contrast has a separate missing-record convention. It is not obtained by subtracting the separately penalized aggregate MAEs. Its stored interval endpoints remain the evaluator's initialized fallback because complete pairing is unavailable. We therefore report no significance claim. Bootstrap methodology \citep{Efron1979} does not turn unexecuted or unsupported resampling into an uncertainty estimate.

\subsection{Conditional Comparison Across Fixed Cases}
Figure~\ref{fig:cases} compares only common available predictions. The primary estimator has lower descriptive MAE than the fitted uniform control in nine cases; MedQA is the exception (0.0574 versus 0.0530). This count includes Commonsense with only one supported seed. BBH gives 0.0308 versus 0.0570, while the corresponding values on MATH are 0.0603 and 0.0624. Thus the observed differences vary substantially across cases. The anchor reference's especially large MuSR error also illustrates why a single pooled comparator should not substitute for the case-level view.


\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{figures/available_pair_method_comparison.pdf}
\caption{Available-pair MAE, averaged equally over query budgets, separated by data source. Small dots show supported seeds; vertical marks show their descriptive mean. Parentheses give supported seed counts; the asterisk marks missing Commonsense records at seeds 5003 and 9001. All four methods use identical case--seed support. Missing-output penalties are not plotted as measured errors. These conditional results do not restore failed qualification.}
\label{fig:cases}
\end{figure}


The conditional comparison differs from the reported aggregate ordering because it changes both the available support and the handling of missing records. Neither view should replace the other: the reported aggregate reflects the evaluator's failure policy, while the conditional view describes retained predictions. The latter is compatible with useful prediction accuracy on observed cases and simultaneously insufficient evidence for a qualified overall result. It does not establish that missingness is benign or that the omitted outcomes would follow the same pattern.

\subsection{Item Budget, Reconstruction, and Ranking}
On the stated common-support aggregation, primary MAE is 0.0439, 0.0333, and 0.0278 at the three budgets; fitted uniform-selection MAE is 0.0598, 0.0439, and 0.0328. Figure~\ref{fig:budgets} separates absolute-score prediction from model ranking. Selected-item raw means have much larger MAE (0.1321, 0.1050, and 0.0851), but Spearman correlations of 0.7806, 0.8461, and 0.8819 are close to the primary values of 0.7787, 0.8485, and 0.8858. Reconstruction therefore changes absolute-score error much more than rank correlation in this retained evidence. This is a descriptive matched-order contrast, not an attribution to any one reconstruction component.



\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{figures/budget_accuracy_and_ranking.pdf}
\caption{Conditional error and ranking at each budget. Large dots use equal data-source and case weights, with available seeds normalized within each case. Small dots are descriptive seed summaries normalized over cases available for that seed; they are not independent replicates of the pooled estimator. Both panels and all methods use the same available case--seed intersection. No confidence interval or qualified overall comparison is implied.}
\label{fig:budgets}
\end{figure}


Uniform sample means have lower MAE than selected-item raw means at every displayed budget, whereas fitted selection reverses that ordering on common support. Selection and reconstruction must therefore be assessed jointly. This observation does not identify which selector would be preferable with a fixed independently chosen predictor: the fitted uniform control retunes, and no final fixed-predictor selector-only contrast is available. Similarly, residual-zero and blend-zero settings in source tuning do not constitute independently evaluated final ablations.


\section{Discussion and Limitations}
\paragraph{Accuracy is conditional on an evidence mask.}
The main empirical lesson is not simply that one method has a smaller error. A failure policy and an availability-conditioned comparison answer different questions. Worst-case defaults appropriately penalize a non-completing evaluation, but do not reveal how an absent prediction would have scored. Removing those defaults cannot certify completion. Because the missingness mechanism is unknown, we neither impute outcomes nor extrapolate the observed Commonsense split to its missing splits. This distinction remains necessary even when the remaining comparisons look favorable.

\paragraph{What the method comparison identifies.}
The selected-item-mean condition supports a contrast between fitted reconstruction and no reconstruction on the primary prefixes. It does not isolate Rasch smoothing, residual profiles, group balancing, or their interaction. The fitted uniform control changes acquisition and allows downstream retuning, so it compares two configured procedures. Source-validation tuning establishes how settings are selected, not independent evidence that a component improves final performance. Sequentially developed configurations are likewise not controlled component interventions. Missing or unavailable ablations remain missing evidence.

\paragraph{Scope of generalization and uncertainty.}
These are fixed binary benchmarks and metadata-grouped target models, not samples from a defined population of future tasks. Conservative grouping can merge unrelated models or miss undocumented ancestry. The source-trained covariance and profile assumptions can fail under response shifts. Reusing targets across seeds further prevents reading seed dispersion as an independent-sample confidence interval. We retain the evaluator's uninformative paired interval and refrain from replacing it with an unvalidated narrow interval. The checked replay discrepancy only addresses that replay, not arbitrary execution paths or the failed structural conditions.

\paragraph{Scores are not all of evaluation.}
Full-score MAE does not measure item-level probability calibration. A Bernoulli probability score such as the classical Brier criterion \citep{Brier1950} concerns a different prediction object from our reconstructed benchmark average. Likewise, ranking can be approximately preserved even when scores are systematically shifted. No measured deployment cost, CPU speedup over full language-model evaluation, architecture-specific effect, or reliable stopping criterion is established here. The available response matrices avoid new language-model inference, but do not quantify end-to-end operational savings.

\section{Conclusion}
Score-targeted fixed prefixes and source-trained reconstruction provide a concrete approach to few-item benchmark prediction. The retained evaluation supports heterogeneous conditional accuracy comparisons and shows that fitted reconstruction can change score error more than rank ordering on the same selected responses. However, the final assessment completed without qualification: missing primary and reference predictions and failed matched structural checks are essential parts of the result, not peripheral implementation notes.

The reported penalty-scored aggregate and the available-pair reaggregation must therefore remain separate. Neither demonstrates overall superiority, and neithe

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}
\subsection{Inspectable Implementation and Reproducibility}
The accompanying source snapshots are readable evidence, not merely hashes identifying an unavailable implementation. \texttt{source\_evidence/selected\_method.py} contains the evaluated estimator; \texttt{source\_evidence/evaluate\_final.py} contains the evaluator and local references. The entrypoint manifest and method description are preserved alongside them. Table~\ref{tab:locations} gives relevant locations. The estimator is a finite JSON request handler: reset, source transfer, source fitting, prefix observation, and release. It receives binary matrices and opaque source-group labels, not benchmark names or target identities. Predictions are bounded finite scores. Identical observed rows follow the same prediction calculation; reset and release clear learned state.



\begin{table}[h]
\centering\small
\caption{Readable source locations for implementation and protocol claims. Locations refer to the supplied snapshots.}
\label{tab:locations}
\begin{tabular}{ll}
\toprule
Mechanism & File and lines\\
\midrule
Group weighting and score-targeted selection & \texttt{selected\_method.py}, 52--91\\
Ridge and difficulty fitting & \texttt{selected\_method.py}, 94--115\\
Profiles, priors, posterior score & \texttt{selected\_method.py}, 118--191\\
Source-only tuning and final fitting & \texttt{selected\_method.py}, 194--287\\
Model-group split and local references & \texttt{evaluate\_final.py}, 685--771\\
Scored aggregate and paired fallback & \texttt{evaluate\_final.py}, 1005--1076\\
\bottomrule
\end{tabular}
\end{table}

\paragraph{Rebuilding the paper, not rerunning the evaluation.}
The command \texttt{python build\_paper\_artifacts.py} reads only the frozen evidence registry and regenerates \texttt{derived\_results.json}, both quantitative figures, their PDF/PNG exports, and the numerical supplementary tables. Adjacent provenance sidecars identify the inputs. It does not execute the estimator, refit references, query language models, or rerun the sealed assessment. The overview is rendered separately; the rebuild script never overwrites an existing overview. The exact local writing environment and validation commands are documented in \texttt{REPRODUCIBILITY.md}. The original end-to-end environment and a verified full-evaluation runtime are not established by this artifact-only reconstruction; no estimated runtime is presented as a measurement.


\paragraph{Data version and limits of reconstruction.}
The task identifies the pinned binary response-matrix snapshot \texttt{55faff496947789f94e6b5908c77cbc3e84f81ad}. The actual evaluated objects are the staged, filtered matrices described in \texttt{source\_evidence/final\_data\_manifest.json}, not a new download from a moving leaderboard. Its group rule combines recorded base-model relations, aliases/details identities, broad family metadata, and provider fallback. Metadata cannot prove complete lineage separation. Reproducing the evaluation from upstream data requires the staged column alignment and grouping resources as well as the estimator; the frozen predictions alone are sufficient only for the paper's descriptive reaggregation. The original upstream code repository was not accessed during writing under the task's literature restriction.


\subsection{Extended Estimation Details}
Difficulty initialization uses the group-weighted mean ability minus the logit item mean. Item means are clipped to $[10^{-4},1-10^{-4}]$ for this initialization. Eight Newton updates use group-weighted Bernoulli residuals with difficulty penalty $0.01$ and clip each update to $[-2,2]$. Abilities remain fixed; this is not joint maximum-likelihood Rasch fitting. Profile probabilities are clipped with $\epsilon=10^{-6}$ before applying offsets. Chunked particle summaries avoid retaining the full particle-by-item array during source tuning; a nonzero final blend stores the fitted particle probabilities. A zero blend bypasses that branch at prediction time.


The source folds rebuild the selected order, Rasch probabilities, profiles, and priors on each fold's training groups. Linear configurations are chosen separately for each budget using equal-group squared error. The profile/blend grid uses MAE averaged over budgets, then rows within groups, then groups. It shares the validation folds with linear tuning, so this score is not an untouched outer-fold performance estimate. If only one source group is supplied, grouped tuning is unavailable and the code uses ridge strength one, shrinkage one, and a zero profile blend. This fallback is a code-defined behavior, not evidence that the final evaluator used a single-group fit.


Equation~\ref{eq:profile} explicitly separates known and predicted items. In the batch path, the expected unqueried total is computed as each particle's full expected total minus its queried expected total. The single-row path sums over an explicit unqueried mask. Both implement the same algebra. This source inspection supports an implementation description, not an empirical guarantee that every execution path passed the evaluator's controls. The final diagnostic failures remain in force.

\subsection{Local Reference Implementations}
The anchor reference centers each item's source response vector, normalizes its length, and applies $k$-means with $k=b$, one initialization, and at most 30 iterations. Representatives are distinct nearest response vectors. Every item is reassigned to its nearest representative and representative weights are the fractions assigned. Target score prediction is the weighted average of queried responses. This reference need not match the preprocessing, optimization, or benchmark regime of published Anchor Points.


The IRT reference models logits as $\theta_i\exp(\eta_j)-d_j$. Its objective is summed Bernoulli negative log likelihood plus penalties $0.5\|\theta\|^2+0.05\|\eta\|^2+0.005\|d\|^2$. L-BFGS-B uses bounded parameters and at most 40 iterations. Item order is the decreasing fitted information $a_j^2 p_j(1-p_j)$ at zero ability, where $a_j=\exp(\eta_j)$ \citep[Chap.~6]{Baker2001}. Target abilities use up to 30 regularized Newton updates on queried responses; the reference score averages fitted response probabilities over the entire item universe. Finite-objective checks do not prove solver optimality. No exact reproduction of a published IRT benchmark-compression package is claimed.


\subsection{Available-Pair Numerical Results}
Table~\ref{tab:cases_si} retains exact case-level descriptive means to more precision than the main text. All methods within a row use the same supported seeds and give equal weight to each budget and target within a seed. The table is not an extrapolation to absent records. In particular, the Commonsense row is a single split, and cannot quantify its between-seed stability.
\begin{table}[h]
\centering
\caption{Conditional MAE on common available support. $n$ counts supported seeds.}
\label{tab:cases_si}
\begin{tabular}{lrrrrr}
\toprule
Case & $n$ & Score design & Uniform + fit & Anchor & IRT\\
\midrule


BBH & 3 & 0.0308 & 0.0570 & 0.1551 & 0.0507 \\
GPQA & 3 & 0.0128 & 0.0197 & 0.0694 & 0.0530 \\
MuSR & 3 & 0.0198 & 0.0266 & 0.4441 & 0.0515 \\
OL-Math & 3 & 0.0123 & 0.0221 & 0.0242 & 0.0132 \\
Commonsense & 1 & 0.0455 & 0.0605 & 0.0818 & 0.1157 \\
GSM & 3 & 0.0517 & 0.0590 & 0.1027 & 0.1275 \\
LegalBench & 3 & 0.0440 & 0.0599 & 0.2031 & 0.0738 \\
MATH & 3 & 0.0603 & 0.0624 & 0.0838 & 0.1083 \\
MedQA & 3 & 0.0574 & 0.0530 & 0.2492 & 0.0845 \\
MMLU & 3 & 0.0474 & 0.0634 & 0.2738 & 0.0721 \\

\bottomrule
\end{tabular}
\end{table}


\begin{table}[h]
\centering
\caption{Conditional budget summaries. Cases receive equal weight within source domain, domains equal weight, and available seeds equal weight within case. Raw selected means and reconstructed scores use the same primary prefixes.}
\label{tab:budget_si}
\begin{tabular}{rlrr}
\toprule
Items & Method & MAE & Spearman\\
\midrule


8 & Score design & 0.0439 & 0.7787 \\
8 & Uniform + fit & 0.0598 & 0.5892 \\
8 & Selected mean & 0.1321 & 0.7806 \\
8 & Uniform mean & 0.1082 & 0.5303 \\
16 & Score design & 0.0333 & 0.8485 \\
16 & Uniform + fit & 0.0439 & 0.7278 \\
16 & Selected mean & 0.1050 & 0.8461 \\
16 & Uniform mean & 0.0823 & 0.6015 \\
32 & Score design & 0.0278 & 0.8858 \\
32 & Uniform + fit & 0.0328 & 0.7995 \\
32 & Selected mean & 0.0851 & 0.8819 \\
32 & Uniform mean & 0.0556 & 0.6908 \\

\bottomrule
\end{tabular}
\end{table}



\subsection{Seed-Level Records and Exhaustive Numerical Ledger}
Table~\ref{tab:seed_si} gives the recorded primary metrics for every case--seed pair, averaged equally over budgets. The target count and number of recorded target-group labels vary with the split. A missing primary record stays missing in this table rather than inheriting its evaluator penalty. This table retains the affected rows explicitly, while the main aggregate table preserves the separately scored defaults.


\begin{table}[p]
\centering\small
\setlength{\tabcolsep}{3pt}
\caption{All primary case--seed records. $T$ counts targets and $H$ their recorded groups. Errors and correlations average the three budgets. Missing outputs are not measured errors; available rows do not repair failed overall qualification.}
\label{tab:seed_si}
\begin{tabular}{lrrrrrrr}
\toprule
Case & Seed & $T$ & $H$ & MAE & RMSE & Spearman & Kendall\\
\midrule


BBH & 5003 & 54 & 10 & 0.0281 & 0.0349 & 0.8109 & 0.6488 \\
BBH & 7001 & 65 & 10 & 0.0311 & 0.0395 & 0.8239 & 0.6577 \\
BBH & 9001 & 243 & 10 & 0.0331 & 0.0432 & 0.9250 & 0.7658 \\
GPQA & 5003 & 54 & 10 & 0.0110 & 0.0149 & 0.6439 & 0.4973 \\
GPQA & 7001 & 64 & 10 & 0.0123 & 0.0155 & 0.7122 & 0.5326 \\
GPQA & 9001 & 243 & 10 & 0.0152 & 0.0203 & 0.8333 & 0.6467 \\
MuSR & 5003 & 54 & 10 & 0.0182 & 0.0234 & 0.7836 & 0.6100 \\
MuSR & 7001 & 65 & 10 & 0.0209 & 0.0272 & 0.6419 & 0.4624 \\
MuSR & 9001 & 244 & 10 & 0.0203 & 0.0255 & 0.7730 & 0.5790 \\
OL-Math & 5003 & 54 & 10 & 0.0078 & 0.0122 & 0.7274 & 0.6130 \\
OL-Math & 7001 & 65 & 10 & 0.0129 & 0.0208 & 0.7905 & 0.6874 \\
OL-Math & 9001 & 244 & 10 & 0.0161 & 0.0243 & 0.9037 & 0.7588 \\
Commonsense & 5003 & 14 & 5 & \multicolumn{4}{c}{Missing; not a measured loss} \\
Commonsense & 7001 & 20 & 5 & 0.0455 & 0.0737 & 0.8867 & 0.7742 \\
Commonsense & 9001 & 37 & 5 & \multicolumn{4}{c}{Missing; not a measured loss} \\
GSM & 5003 & 14 & 5 & 0.0500 & 0.0611 & 0.9288 & 0.7763 \\
GSM & 7001 & 20 & 5 & 0.0442 & 0.0552 & 0.9424 & 0.8403 \\
GSM & 9001 & 37 & 5 & 0.0608 & 0.0731 & 0.9336 & 0.8052 \\
LegalBench & 5003 & 14 & 5 & 0.0394 & 0.0524 & 0.7651 & 0.6237 \\
LegalBench & 7001 & 20 & 5 & 0.0431 & 0.0518 & 0.8429 & 0.6652 \\
LegalBench & 9001 & 35 & 5 & 0.0496 & 0.0625 & 0.7919 & 0.6375 \\
MATH & 5003 & 14 & 5 & 0.0650 & 0.0762 & 0.9782 & 0.9098 \\
MATH & 7001 & 20 & 5 & 0.0580 & 0.0683 & 0.9414 & 0.8517 \\
MATH & 9001 & 37 & 5 & 0.0580 & 0.0827 & 0.9340 & 0.8079 \\
MedQA & 5003 & 14 & 5 & 0.0666 & 0.0798 & 0.8548 & 0.6726 \\
MedQA & 7001 & 20 & 5 & 0.0571 & 0.0752 & 0.8665 & 0.7133 \\
MedQA & 9001 & 37 & 5 & 0.0485 & 0.0623 & 0.9262 & 0.7864 \\
MMLU & 5003 & 14 & 5 & 0.0570 & 0.0775 & 0.9560 & 0.8618 \\
MMLU & 7001 & 20 & 5 & 0.0437 & 0.0619 & 0.9129 & 0.7678 \\
MMLU & 9001 & 37 & 5 & 0.0413 & 0.0577 & 0.8682 & 0.7126 \\

\bottomrule
\end{tabular}
\end{table}

An exhaustive machine-readable table, \texttt{complete\_metrics.csv}, additionally retains every recorded condition and reference, separated by case, seed, and budget. It includes primary, both fitted/raw-mean controls, matched constant/copied/permuted observations, replay where recorded, and anchor/IRT/uniform/source-mean references. Missing prediction metrics are blank, not penalty values; availability and structural-failure fields remain separate. As in the evaluator, a constant truth or prediction vector receives rank correlation zero by convention. Scores for a condition with a failed structural check describe its recorded output only, not validated performance. The table and its provenance sidecar are generated by the same transformation script as the figures.



For completeness, the remaining reported diagnostic MAEs are 0.2220 for constant observations, 0.1545 for copied observations, 0.1005 for permuted observations, and 0.0281 for replay. These evaluator summaries have their original weighting and scope; they are not new controlled accuracy estimates. In particular, replay covers the checked repeated case rather than the full benchmark collection, and matched corrupted observations are not ordinary target responses.





\subsection{Availability Masks and Statistical Interpretation}
There are 30 planned case--seed pairs, of which 28 enter the common-support comparisons. For the budget plots, each available pair supplies all three budgets and all four displayed methods. The per-case normalization deliberately preserves the intended relative mass of the two data sources. It does not make the missing splits exchangeable with the retained split. A globally normalized available-pair average would be a different statistic; neither is an estimate of the complete evaluation without a missingness assumption.


The seed dots in the budget figure separately renormalize the original case weights over cases available for each seed. Consequently their average need not equal the large pooled dot, whose normalization is within each case. They convey descriptive variation under overlapping model-group partitions and should not be used as independent replicates for a significance test. No new bootstrap or inferential procedure is introduced by the paper's plotting code. All qualification facts remain those of the frozen evaluator.

Structural checks use matched constant, copied, and permuted observations to test dependence on legal observations, together with reset replay. Their aggregate failure summary is not an ordinary proportion of independent failed target models. Likewise, the missing-evaluation fraction counts scheduled evaluation units, including conditions and replay, not case--seed pairs. The two missing primary pairs and their baseline omissions are therefore reported explicitly rather than inferred from that fraction.
```
