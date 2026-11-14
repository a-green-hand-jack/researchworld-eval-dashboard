# Agentic evidence audit packet

- generated_at: `2026-11-11T08:53:34.534375+00:00`
- paper_dir: `work/results/t03/claude/20261111_071336/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261111_080655-paper_evidence_audit_round_5-8jygc_qr/workspace`

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
    "anchored_references": 36,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 48,
    "resolved_references": 24,
    "total_references": 60
  },
  "ok": true,
  "pdf_path": "work/results/t03/claude/20261111_071336/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 36,
    "dangling_references": 0,
    "manifests_checked": 6,
    "resolved_references": 24,
    "total_references": 60
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "Mean top-3 Jaccard agreement between an assessed Kernel SHAP run and eight reruns is 0.8065 at budget 4d and 0.9315 at 16d (abstract 0.807/0.932), averaged over three held-out datasets, three model families, two seeds and 20 instances per cell.",
      "source_ids": [
        "final.metric.mean_label_low_budget",
        "final.metric.mean_label_high_budget"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The difference between mean agreement at 16d and 4d is 0.125 (derived).",
      "source_ids": [
        "final.metric.mean_label_low_budget",
        "final.metric.mean_label_high_budget"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Share of assessed-rerun pairs with non-identical top-3 sets lies between 19.3% and 38.7% at 4d and between 6.8% and 13.7% at 16d (derived from mean labels via Jaccard values 0,0.2,0.5,1).",
      "source_ids": [
        "final.metric.mean_label_low_budget",
        "final.metric.mean_label_high_budget"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The diagnostic's score (1-MSE) in the sealed final evaluation is 0.9838, i.e. MSE 0.0162 and RMSE 0.127 (derived).",
      "source_ids": [
        "final.metric.combined_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Skill (MSE reduction) over always-reliable is 0.0353 with one-sided 2.5th-percentile bootstrap lower bound 0.0171.",
      "source_ids": [
        "final.metric.skill_vs_always_reliable",
        "final.metric.skill_vs_always_reliable_ci_low"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Skill over constant 0.5 is 0.1543 with lower bound 0.1245.",
      "source_ids": [
        "final.metric.skill_vs_constant_half",
        "final.metric.skill_vs_constant_half_ci_low"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Skill over the split-half-gap heuristic is 0.0122 with lower bound 0.0081.",
      "source_ids": [
        "final.metric.skill_vs_gap_heuristic",
        "final.metric.skill_vs_gap_heuristic_ci_low"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The pairing-permuted control scores 0.9701; the diagnostic exceeds it by 0.0137 (derived) with lower bound 0.0101.",
      "source_ids": [
        "final.metric.combined_score",
        "final.metric.control_permuted_score",
        "final.metric.combined_minus_control_ci_low"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Relative MSE reductions by the diagnostic are 68.5% vs always-reliable, 90.5% vs constant 0.5, 42.9% vs split-half gap and 45.9% vs permuted control; comparator MSEs 0.0515, 0.1705, 0.0284, 0.0299 and RMSEs 0.227, 0.413, 0.169, 0.173 (derived).",
      "source_ids": [
        "final.metric.combined_score",
        "final.metric.skill_vs_always_reliable",
        "final.metric.skill_vs_constant_half",
        "final.metric.skill_vs_gap_heuristic",
        "final.metric.control_permuted_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Of the 0.0353 MSE reduction over always-reliable, 0.0216 (61%) is retained under within-episode permutation and 0.0137 (39%) is instance-specific (derived).",
      "source_ids": [
        "final.metric.combined_score",
        "final.metric.skill_vs_always_reliable",
        "final.metric.control_permuted_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Mean within-episode Spearman correlation between predicted and actual reproducibility is 0.5809 (episodes with a constant vector count as zero by evaluator convention).",
      "source_ids": [
        "final.metric.spearman_r_hat_vs_label"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Per-seed final scores are 0.9850 (seed 9001) and 0.9826 (seed 9002), a difference of 0.0025; per-seed sweeps took 53.3 s and 53.8 s.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The sealed final evaluation completed with recorded outcome qualified and validity flag true; candidate diagnostics trust is unverified; the four lower bounds (three skills and diagnostic-minus-control) are all positive.",
      "source_ids": [
        "final.qualification.outcome",
        "final.qualification.status",
        "final.qualification.correct",
        "final.metric.skill_vs_always_reliable_ci_low",
        "final.metric.skill_vs_constant_half_ci_low",
        "final.metric.skill_vs_gap_heuristic_ci_low",
        "final.metric.combined_minus_control_ci_low"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The mean label deficit 1-y averaged over the two budgets is 0.131 (derived).",
      "source_ids": [
        "final.metric.mean_label_low_budget",
        "final.metric.mean_label_high_budget"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The budget prior constants 0.84 and 0.96 exceed the final label means by 0.0335 at 4d and 0.0285 at 16d (derived; constants read from selected configuration source).",
      "source_ids": [
        "final.metric.mean_label_low_budget",
        "final.metric.mean_label_high_budget"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The selected configuration scored 0.9854 on the search plane (per seed 0.9840 and 0.9869), a development proxy used for selection among three configurations.",
      "source_ids": [
        "result.best_correct_score",
        "result.improvement_003"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Search-plane scores of the three configurations are 0.9760 (A: 0.9740/0.9779), 0.9837 (B: 0.9824/0.9849) and 0.9854 (C: 0.9840/0.9869); all three completed and none was unscored.",
      "source_ids": [
        "result.improvement_001",
        "result.improvement_002",
        "result.improvement_003",
        "result.total_attempts",
        "result.total_evaluated_programs"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Protocol facts (36 episodes, 720 labeled instances, 8 reruns, 20 derangements, 200 bootstrap replicates, seeds 9001/9002, budgets 4d/16d, d=10/10/20) are read from source files, not from the sealed metrics: source_evidence/evaluator_final.py (line 42 seeds; lines 66-72 full-protocol constants; lines 761-812 kernel_coalitions; lines 861-872 derangements) and source_evidence/task_contract.json. The only sealed-evidence record that corroborates part of this is the per-seed episode record (two seeds).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Diagnostic constants (8 folds, 4 partitions, 1000 antithetic draws, simulator weights 0.5/0.2/0.3, shrinkage 0.6/0.4, prior 0.84/0.96, margin 0.02, scale 3) are read from the source file of the selected configuration (source_evidence/selected_config_program.py: constants lines 35-46, weights lines 55-63), whose program directory is recorded under result.improvement_003. They are not sealed metrics; the configuration's notes state the constants were hand-set and untuned and that no code was executed when writing it.",
      "source_ids": [
        "result.improvement_003"
      ]
    },
    {
      "citation_keys": [
        "Lundberg2017Unified"
      ],
      "claim": "Kernel SHAP casts Shapley estimation as weighted regression over sampled coalitions.",
      "source_ids": [
        "ref.openalex.W2618851150"
      ]
    },
    {
      "citation_keys": [
        "Covert2020Improving",
        "Mitchell2021Sampling",
        "Musco2024Provably",
        "Jethani2021FastSHAP",
        "Gupte2025Understanding"
      ],
      "claim": "Kernel SHAP variance reduction and alternative estimators: paired sampling and regression refinements, permutation sampling, leverage-score sampling, amortized estimators, and an empirical comparison on tabular data.",
      "source_ids": [
        "ref.s2.3dd57363da3201f920c7e0b17a29e59ef44da724",
        "ref.openalex.W3157730516",
        "ref.openalex.W4403853934",
        "ref.openalex.W3179224442",
        "ref.s2.3fc7625f169756de672bc60b97d322ede2b3e0cb"
      ]
    },
    {
      "citation_keys": [
        "Sundararajan2019many",
        "Chen2020True",
        "Frye2020Shapley",
        "Kumar2020Problems",
        "Covert2020Explaining",
        "Gosiewska2019Do"
      ],
      "claim": "Value-function choice changes what a Shapley attribution means; additive attributions can misrepresent interactions.",
      "source_ids": [
        "ref.openalex.W2969551072",
        "ref.openalex.W3037688018",
        "ref.openalex.W3092722451",
        "ref.openalex.W3007549203",
        "ref.openalex.W3107600318",
        "ref.openalex.W2990298540"
      ]
    },
    {
      "citation_keys": [
        "Ribeiro2016Why",
        "AlvarezMelis2018Robustness",
        "Krishna2022Disagreement",
        "Yuan2022empirical"
      ],
      "claim": "Local explanations vary under perturbation and across methods; background size affects SHAP stability for deep models.",
      "source_ids": [
        "ref.openalex.W2951501516",
        "ref.openalex.W2809283485",
        "ref.s2.e0f12956ccfc1ed005b54cb876d9173c4a18dc75",
        "ref.openalex.W4224936048"
      ]
    },
    {
      "citation_keys": [
        "Marx2019Predictive",
        "Nogueira2017Stability",
        "Webber2010similarity",
        "Williamson2020Efficient"
      ],
      "claim": "Predictive multiplicity, feature-selection stability with chance correction, rank-biased overlap and population-level Shapley importance inference are related measurement notions.",
      "source_ids": [
        "ref.openalex.W2972763980",
        "ref.s2.456f688d742ad3c086a9372c4e35251094904210",
        "ref.s2.b82756edb00e92f7314f1a3e036bf292664ad3a5",
        "ref.openalex.W3035927733"
      ]
    },
    {
      "citation_keys": [
        "Ding2021Retiring",
        "Pedregosa2012Scikit",
        "Gorishniy2021Revisiting",
        "Lundberg2018Consistent",
        "DoshiVelez2017Towards"
      ],
      "claim": "Datasets, models and context: folktables ACS income, scikit-learn model families, deep tabular architectures, tree-versus-neural comparisons, tree-specific Shapley algorithms and rigorous interpretability evaluation.",
      "source_ids": [
        "ref.openalex.W3190248325",
        "ref.openalex.W2101234009",
        "ref.openalex.W3174082502",
        "ref.openalex.W2787070805",
        "ref.openalex.W2594475271"
      ]
    },
    {
      "citation_keys": [
        "Bhatt2020Explainable",
        "Lundberg2017Unified"
      ],
      "claim": "Practitioner studies report feature attributions as a widely deployed form of explanation.",
      "source_ids": [
        "ref.openalex.W2973193541",
        "ref.openalex.W2618851150"
      ]
    },
    {
      "citation_keys": [
        "Visani2021Statistical",
        "Slack2020Reliable"
      ],
      "claim": "Prior work on sampled local explainers quantifies repeat-run stability of LIME (stability indices) and models uncertainty of LIME and Kernel SHAP explanations with Bayesian local regressions.",
      "source_ids": [
        "ref.openalex.W3003730808",
        "ref.openalex.W3177950445"
      ]
    },
    {
      "citation_keys": [
        "Kott2001Using",
        "Efron1973Stein"
      ],
      "claim": "The diagnostic's jackknife covariance follows the delete-a-group jackknife, and its shrinkage toward a prior is described as empirical-Bayes-style in the sense of Stein-type estimators.",
      "source_ids": [
        "ref.openalex.W2470309683",
        "ref.openalex.W2072857774"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The budget-prior constants 0.84 and 0.96 are hand-set. The configuration's notes (source_evidence/selected_config_NOTES.md, 'Provenance of constants') describe them as aggregate label means by budget seen in earlier evaluation metrics; those means are not retained in the evidence, so the origin is unverified. They are not the sealed-final label means (0.8065 and 0.9315).",
      "source_ids": [
        "result.improvement_003"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The German Credit final dataset is the complementary hash-parity half of the search-plane German Credit split, per source_evidence/final_resources_manifest.json and search_resources_manifest.json (read from those manifests, not from sealed metrics).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    }
  ]
}
```

## paper_data summary

```json
{
  "available": true,
  "claim_count": 0,
  "downstream_study": null,
  "final_evaluation": {
    "correct": true,
    "outcome": "qualified",
    "status": "completed"
  },
  "grounding_source_count": 28,
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
  "campaign_results_dir": "work/results/t03/claude/20261111_071336/investigation",
  "count": 30,
  "generated_at": "2026-11-11T08:07:41.278553+00:00",
  "queries": [
    "Improving KernelSHAP: practical Shapley value estimation using linear regression",
    "Shapley value estimation sampling error bounds approximation guarantees",
    "uncertainty quantification confidence intervals for Shapley value estimates feature attribution",
    "stability of post-hoc explanations LIME SHAP repeated runs random sampling instability",
    "top-k feature attribution agreement metrics rank-biased overlap Jaccard rank correlation explanations",
    "delete-a-group jackknife variance estimation",
    "empirical Bayes shrinkage noisy variance estimates",
    "interventional versus observational conditional expectation Shapley values background data choice",
    "Statlog German Credit Pima Indians Diabetes tabular classification benchmark datasets"
  ],
  "reference_query_plan": {
    "architectural_shifts": [
      "Shift from single-run SHAP point attribution to attribution plus per-instance reliability estimate (r_hat)",
      "Shift from naive diagonal jackknife (cycle 1, 0.976) to covariance-aware CRN/antithetic simulation (0.984) to partition ensemble with budget prior (0.985; sealed final ~0.984)"
    ],
    "benchmarks": [
      "Pima Indians Diabetes (OpenML 37)",
      "Statlog German Credit (UCI)",
      "Model families: logistic regression and other common tabular classifiers owned by the evaluator"
    ],
    "central_topic": "Whether a single run of a budget-limited stochastic Kernel SHAP explainer gives a reliable top-k feature attribution for a trained tabular model, and whether per-instance reliability can be predicted from that one run (within-run variance diagnostics) rather than from repeated runs.",
    "comparators": [
      "Improved/variance-reduced Kernel SHAP and regression-based Shapley estimators",
      "Sampling-based Shapley approximation with error guarantees (leverage score sampling)",
      "Explanation disagreement and instability literature (LIME/SHAP)",
      "Feature-selection stability and ranking-similarity measures (Nogueira; rank-biased overlap)",
      "Background-data and expectation-choice effects on SHAP (Yuan; Chen et al.)",
      "Uncertainty quantification for Shapley estimates"
    ],
    "core_methods": [
      "Kernel SHAP with paired, kernel-weighted coalition sampling at a fixed budget (4d and 16d coalitions)",
      "Repeat-run reliability label: mean top-k Jaccard overlap between a reference run and independent reruns",
      "Single-run self-diagnostic r_hat: delete-one-group jackknife of the regression estimator with covariance-aware rerun simulation",
      "Budget-aware empirical-Bayes shrinkage and partition-ensembled jackknife (best variant)",
      "Calibration of simulated rerun stability and comparison with a gap heuristic and constant baselines"
    ],
    "forbidden_query_patterns": [
      "generic 'optimization' or 'benchmarking' queries",
      "scientific method / paper-writing phrasing",
      "chronology of cycles, ideas or search history",
      "deep tabular architectures (FT-Transformer, ResNet) as a main topic: the run evaluates none beyond starter context",
      "queries naming or aiming at a specific prior paper on repeat-run SHAP reliability (access prohibited)",
      "generic 'explainable AI survey' queries"
    ],
    "queries": [
      {
        "category": "core_method",
        "query": "Improving KernelSHAP: practical Shapley value estimation using linear regression",
        "rationale": "Kernel SHAP sampling, paired sampling and variance reduction are the stochastic estimator whose rerun noise is studied."
      },
      {
        "category": "baseline_comparator",
        "query": "Shapley value estimation sampling error bounds approximation guarantees",
        "rationale": "Theory of estimator error under limited coalition budget (leverage-score sampling and related) frames why reruns differ."
      },
      {
        "category": "core_method",
        "query": "uncertainty quantification confidence intervals for Shapley value estimates feature attribution",
        "rationale": "The self-diagnostic quantifies within-run uncertainty of attributions; closest prior work on SHAP error bars."
      },
      {
        "category": "baseline_comparator",
        "query": "stability of post-hoc explanations LIME SHAP repeated runs random sampling instability",
        "rationale": "Direct comparator literature on rerun and perturbation instability of sampled explainers."
      },
      {
        "category": "core_method",
        "query": "top-k feature attribution agreement metrics rank-biased overlap Jaccard rank correlation explanations",
        "rationale": "Reliability label is top-k Jaccard; need justification and comparison with rank-aware similarity measures."
      },
      {
        "category": "architectural_shift",
        "query": "delete-a-group jackknife variance estimation",
        "rationale": "Delete-one-group jackknife of the Kernel SHAP regression is the mechanism behind the single-run diagnostic."
      },
      {
        "category": "architectural_shift",
        "query": "empirical Bayes shrinkage noisy variance estimates",
        "rationale": "Best variant shrinks the simulated stability estimate toward a budget-level prior."
      },
      {
        "category": "result_driven_theme",
        "query": "interventional versus observational conditional expectation Shapley values background data choice",
        "rationale": "Clarifies that the study targets the reliability of the estimator, not the choice of value function; background resampling is a noise source."
      },
      {
        "category": "benchmark_context",
        "query": "Statlog German Credit Pima Indians Diabetes tabular classification benchmark datasets",
        "rationale": "Dataset provenance for the two evaluation datasets; keep only to find dataset citations."
      }
    ],
    "result_driven_themes": [
      "Reliability is budget dependent: mean top-k stability label 0.84 at low budget vs 0.96 at high budget in search; 0.81 vs 0.93 in sealed final",
      "Within-run estimates only modestly rank-correlate with realized stability (Spearman ~0.54) and beat trivial/gap heuristics by small margins (~0.01), with a permuted control close behind",
      "Conditional claim: single runs sufficient at high budget, unreliable for a minority at low budget, detectable only partially from one run"
    ],
    "status": "ready"
  },
  "reference_query_plans": [
    {
      "architectural_shifts": [
        "Shift from single-run SHAP point attribution to attribution plus per-instance reliability estimate (r_hat)",
        "Shift from naive diagonal jackknife (cycle 1, 0.976) to covariance-aware CRN/antithetic simulation (0.984) to partition ensemble with budget prior (0.985; sealed final ~0.984)"
      ],
      "benchmarks": [
        "Pima Indians Diabetes (OpenML 37)",
        "Statlog German Credit (UCI)",
        "Model families: logistic regression and other common tabular classifiers owned by the evaluator"
      ],
      "central_topic": "Whether a single run of a budget-limited stochastic Kernel SHAP explainer gives a reliable top-k feature attribution for a trained tabular model, and whether per-instance reliability can be predicted from that one run (within-run variance diagnostics) rather than from repeated runs.",
      "comparators": [
        "Improved/variance-reduced Kernel SHAP and regression-based Shapley estimators",
        "Sampling-based Shapley approximation with error guarantees (leverage score sampling)",
        "Explanation disagreement and instability literature (LIME/SHAP)",
        "Feature-selection stability and ranking-similarity measures (Nogueira; rank-biased overlap)",
        "Background-data and expectation-choice effects on SHAP (Yuan; Chen et al.)",
        "Uncertainty quantification for Shapley estimates"
      ],
      "core_methods": [
        "Kernel SHAP with paired, kernel-weighted coalition sampling at a fixed budget (4d and 16d coalitions)",
        "Repeat-run reliability label: mean top-k Jaccard overlap between a reference run and independent reruns",
        "Single-run self-diagnostic r_hat: delete-one-group jackknife of the regression estimator with covariance-aware rerun simulation",
        "Budget-aware empirical-Bayes shrinkage and partition-ensembled jackknife (best variant)",
        "Calibration of simulated rerun stability and comparison with a gap heuristic and constant baselines"
      ],
      "forbidden_query_patterns": [
        "generic 'optimization' or 'benchmarking' queries",
        "scientific method / paper-writing phrasing",
        "chronology of cycles, ideas or search history",
        "deep tabular architectures (FT-Transformer, ResNet) as a main topic: the run evaluates none beyond starter context",
        "queries naming or aiming at a specific prior paper on repeat-run SHAP reliability (access prohibited)",
        "generic 'explainable AI survey' queries"
      ],
      "queries": [
        {
          "category": "core_method",
          "query": "Improving KernelSHAP: practical Shapley value estimation using linear regression",
          "rationale": "Kernel SHAP sampling, paired sampling and variance reduction are the stochastic estimator whose rerun noise is studied."
        },
        {
          "category": "baseline_comparator",
          "query": "Shapley value estimation sampling error bounds approximation guarantees",
          "rationale": "Theory of estimator error under limited coalition budget (leverage-score sampling and related) frames why reruns differ."
        },
        {
          "category": "core_method",
          "query": "uncertainty quantification confidence intervals for Shapley value estimates feature attribution",
          "rationale": "The self-diagnostic quantifies within-run uncertainty of attributions; closest prior work on SHAP error bars."
        },
        {
          "category": "baseline_comparator",
          "query": "stability of post-hoc explanations LIME SHAP repeated runs random sampling instability",
          "rationale": "Direct comparator literature on rerun and perturbation instability of sampled explainers."
        },
        {
          "category": "core_method",
          "query": "top-k feature attribution agreement metrics rank-biased overlap Jaccard rank correlation explanations",
          "rationale": "Reliability label is top-k Jaccard; need justification and comparison with rank-aware similarity measures."
        },
        {
          "category": "architectural_shift",
          "query": "delete-a-group jackknife variance estimation",
          "rationale": "Delete-one-group jackknife of the Kernel SHAP regression is the mechanism behind the single-run diagnostic."
        },
        {
          "category": "architectural_shift",
          "query": "empirical Bayes shrinkage noisy variance estimates",
          "rationale": "Best variant shrinks the simulated stability estimate toward a budget-level prior."
        },
        {
          "category": "result_driven_theme",
          "query": "interventional versus observational conditional expectation Shapley values background data choice",
          "rationale": "Clarifies that the study targets the reliability of the estimator, not the choice of value function; background resampling is a noise source."
        },
        {
          "category": "benchmark_context",
          "query": "Statlog German Credit Pima Indians Diabetes tabular classification benchmark datasets",
          "rationale": "Dataset provenance for the two evaluation datasets; keep only to find dataset citations."
        }
      ],
      "result_driven_themes": [
        "Reliability is budget dependent: mean top-k stability label 0.84 at low budget vs 0.96 at high budget in search; 0.81 vs 0.93 in sealed final",
        "Within-run estimates only modestly rank-correlate with realized stability (Spearman ~0.54) and beat trivial/gap heuristics by small margins (~0.01), with a permuted control close behind",
        "Conditional claim: single runs sufficient at high budget, unreliable for a minority at low budget, detectable only partially from one run"
      ],
      "status": "ready"
    },
    {
      "architectural_shifts": [
        "Shift from single-run SHAP point attribution to attribution plus per-instance reliability estimate (r_hat)",
        "Shift from naive diagonal jackknife (cycle 1, 0.976) to covariance-aware CRN/antithetic simulation (0.984) to partition ensemble with budget prior (0.985; sealed final ~0.984)"
      ],
      "benchmarks": [
        "Pima Indians Diabetes (OpenML 37)",
        "Statlog German Credit (UCI)",
        "Model families: logistic regression and other common tabular classifiers owned by the evaluator"
      ],
      "central_topic": "Whether a single run of a budget-limited stochastic Kernel SHAP explainer gives a reliable top-k feature attribution for a trained tabular model, and whether per-instance reliability can be predicted from that one run (within-run variance diagnostics) rather than from repeated runs.",
      "comparators": [
        "Improved/variance-reduced Kernel SHAP and regression-based Shapley estimators",
        "Sampling-based Shapley approximation with error guarantees (leverage score sampling)",
        "Explanation disagreement and instability literature (LIME/SHAP)",
        "Feature-selection stability and ranking-similarity measures (Nogueira; rank-biased overlap)",
        "Background-data and expectation-choice effects on SHAP (Yuan; Chen et al.)",
        "Uncertainty quantification for Shapley estimates"
      ],
      "core_

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

\usepackage{hyperref}
\usepackage{url}
\usepackage{graphicx}
\usepackage{subcaption}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{array}

\newcommand{\rhat}{\hat r}
\newcommand{\topk}{\mathrm{T}_3}
\newcommand{\jac}{\mathrm{J}}

\title{How Reliable Is One Kernel SHAP Run? Budget-Conditional Top-3 Reproducibility and a Single-Run Self-Diagnostic}

\begin{document}
\maketitle

\begin{abstract}
Explanations of tabular predictions are often produced by one run of a stochastic Shapley estimator, and the resulting top features are then reported as the reason for the prediction. We ask when the top-3 features of one budget-limited Kernel SHAP run would be reproduced by independent reruns. We define reproducibility as the mean top-3 Jaccard agreement between the assessed run and eight reruns, and we study coalition budgets of $4d$ and $16d$ for $d$ features. On three tabular datasets that are disjoint by record hash from the search data (one is the complementary half of a German Credit split used in the search, so it is not an independent source dataset) and three model families, mean agreement is 0.807 at $4d$ and 0.932 at $16d$, so single-run reliability depends on the budget. We then test whether the assessed run's own coalition data can predict its reproducibility, using a jackknife-based rerun simulation shrunk toward a budget prior. In the sealed evaluation, which qualified, the predictor lowers squared error against always-reliable, constant-0.5 and split-half-gap baselines, with positive one-sided bootstrap lower bounds, and beats a pairing-permuted control by 0.0137. The permuted control keeps about 61\% of the gain over always-reliable, per-instance rank correlation is 0.58, and the weights and shrinkage constants are hand-set and untuned. The budget-prior values are hand-set too: the configuration's notes describe them as aggregate label means from earlier evaluation metrics, but those means are not retained in the evidence, so their origin cannot be checked. The results are limited to Kernel SHAP, three datasets and two budgets.

\end{abstract}

\section{Introduction}
Shapley-value attributions \citep{Lundberg2017Unified} are used to explain individual predictions of tabular models in credit, medical and similar settings, and practitioner studies report feature attributions as a widely deployed form of explanation \citep{Bhatt2020Explainable}. For models without a tractable exact algorithm, they are usually estimated by a stochastic procedure under a fixed budget of model evaluations. Two runs of the same estimator on the same trained model and the same instance therefore return different attribution vectors, and the features that appear in a short list of reasons can change from run to run. A common practice, which we take as the case of interest, is to run the explainer once and report what it returns. Whether that practice is adequate, and under which conditions, is rarely stated as a checkable claim.

We study a deliberately narrow version of this question. The explainer is Kernel SHAP with an interventional value function and a 32-row background, run with a budget of $B=4d$ or $B=16d$ coalitions for a model with $d$ features. The decision-relevant object is the top-3 feature set by absolute attribution. We call a single run \emph{reproducible} to the degree that independent reruns, which differ only in their coalition sampling, return the same top-3 set. This definition ignores background resampling, model retraining and the choice between explainers; those sources of disagreement are outside our scope and we do not measure them.

The study has two parts. First, we measure how reproducible single runs are at the two budgets, on three tabular datasets and three model families. The datasets are disjoint by record hash from the search data used to select the diagnostic; one of them (German Credit) is the complementary half of a search-plane split, so that result does not come from an independent source dataset. Second, we ask whether reproducibility can be \emph{predicted for a given run from that run alone}. A practitioner holds one run, not eight. A self-diagnostic that reads the run's coalition masks, weights and evaluated coalition values and returns a reproducibility estimate $\rhat\in[0,1]$ would let the practitioner flag instances whose top-3 set should not be trusted. We evaluate such a diagnostic against three baselines and against a control that keeps all episode-level information but destroys instance-level pairing.

\paragraph{Contributions.}
\begin{itemize}
\item An operational, rerun-based reproducibility label for single-run top-3 attribution, together with a squared-error evaluation protocol that includes trivial baselines, a split-half-gap heuristic and a pairing-permuted control (Section~\ref{sec:method}).
\item A measurement of budget dependence. Across the final datasets and model families, mean top-3 Jaccard agreement is 0.807 at $4d$ and 0.932 at $16d$ (Section~\ref{sec:results}).
\item A single-run diagnostic that combines a delete-one-group jackknife of the run's own regression with Monte-Carlo propagation to the top-3 set and shrinkage toward a budget prior. It beats every baseline and the permuted control with positive lower bounds, but the margin over the control is small in absolute terms (0.0137), and most of its gain over the always-reliable baseline survives permutation.
\item An explicit account of what is not established: no ablation of the diagnostic's components, no per-dataset or per-family breakdown in the retained evidence, only two budgets, and constants set by hand (Section~\ref{sec:limits}).
\end{itemize}

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/protocol_overview.png}
\caption{Protocol overview. A trained model and an explained instance yield one assessed Kernel SHAP run at budget $4d$ or $16d$. Eight independent reruns define the reproducibility label (mean top-3 Jaccard with the assessed run). The self-diagnostic sees only the assessed run and returns $\rhat$, which is scored by squared error against the label and compared with three baselines and a pairing-permuted control.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\paragraph{Shapley estimation.}
Kernel SHAP casts Shapley estimation as a weighted regression over sampled coalitions \citep{Lundberg2017Unified}. Later work reduces its variance through paired sampling and regression refinements \citep{Covert2020Improving}, permutation sampling \citep{Mitchell2021Sampling}, leverage-score sampling with error guarantees \citep{Musco2024Provably}, and amortized estimators \citep{Jethani2021FastSHAP}. \citet{Gupte2025Understanding} compare Shapley approximations empirically on tabular data. These papers make the estimator more accurate or give accuracy guarantees at a chosen budget. We take the budget as given and ask what a user holding one run can say about the reproducibility of its top-3 set, which is a statement about the run rather than about the estimator's average error. The closest work on sampled local explainers asks the per-explanation version of this question for LIME: \citet{Visani2021Statistical} define stability indices from repeated runs, and \citet{Slack2020Reliable} model the uncertainty of LIME and Kernel SHAP explanations with Bayesian local regressions. Both ask for more runs or a posterior over them. We instead ask whether the top-3 set returned by one run at a fixed budget will be reproduced by a rerun, using only that run's own coalition data and an evaluator that does reruns to supply the label.

\paragraph{What a Shapley value means.}
The value function defines what is being attributed: interventional or conditional expectations answer different questions \citep{Sundararajan2019many,Chen2020True,Frye2020Shapley,Kumar2020Problems,Covert2020Explaining}, and additive attributions can misrepresent models with interactions \citep{Gosiewska2019Do}. We fix an interventional value function with a 32-row background and treat the resulting attribution, not its causal or data-faithful interpretation, as the object whose run-to-run stability is measured.

\paragraph{Instability and disagreement of explanations.}
Local explanations are known to vary under perturbation and between methods \citep{Ribeiro2016Why,AlvarezMelis2018Robustness,Krishna2022Disagreement}, and \citet{Yuan2022empirical} study how background size affects SHAP stability for deep models. Our label isolates a different and narrower source of variation, namely the coalition sampling of a single estimator with everything else fixed. This is analogous in spirit to predictive multiplicity, which asks how much predictions vary across equally good alternatives \citep{Marx2019Predictive}, except that the alternatives here are reruns of an estimator.

\paragraph{Stability and similarity measures.}
Feature-selection stability is commonly measured by average pairwise similarity of selected sets, with corrections for chance agreement \citep{Nogueira2017Stability}, and rank-based comparisons of incomplete lists use measures such as rank-biased overlap \citep{Webber2010similarity}. We use the plain Jaccard index on top-3 sets because three reasons is a natural unit for a decision explanation. We do not apply a chance correction, which matters when datasets with $d=10$ and $d=20$ are averaged (Section~\ref{sec:limits}). Uncertainty quantification for Shapley-based importance has been developed at the population level \citep{Williamson2020Efficient}; we address the per-instance, per-run level.

\paragraph{Tabular data and models.}
Our final datasets include an ACS income task from the folktables toolkit \citep{Ding2021Retiring}. Our model families are logistic regression, random forest and a small MLP implemented in scikit-learn \citep{Pedregosa2012Scikit}. Deep tabular architectures \citep{Gorishniy2021Revisiting} are not part of this study, and exact tree-specific Shapley algorithms \citep{Lundberg2018Consistent} are not used. Our framing of reproducibility as a measurable property with explicit scope follows the call for rigorous evaluation of interpretability \citep{DoshiVelez2017Towards}.

\section{Method}\label{sec:method}
\subsection{Problem setup}
Let $f$ be a trained binary classifier and $f_1(x)$ its predicted probability of the positive class. Raw features are grouped so that a categorical feature, after one-hot encoding, forms one group; there are $d$ groups. For an explained instance $x$ and a background set of $m=32$ training rows, the interventional value of a coalition $S\subseteq[d]$ is
\begin{equation}
v(S)=\frac1m\sum_{b=1}^{m} f_1\big(x_S,\,b_{\bar S}\big),
\end{equation}
with anchors $v_0=v(\emptyset)$ and $v_1=v([d])=f_1(x)$. A Kernel SHAP \emph{run} draws $B$ coalitions with masks $z_i\in\{0,1\}^d$ and weights $w_i$ (summing to one), evaluates $v_i=v(S_i)$, and returns
\begin{equation}
\phi=\arg\min_{\phi}\ \sum_{i=1}^{B} w_i\big(v_i-v_0-z_i^{\top}\phi\big)^2\quad\text{s.t.}\quad \mathbf 1^{\top}\phi=v_1-v_0 .
\end{equation}
The coalition set follows the Kernel SHAP size distribution with complement pairs placed adjacently. Size classes are enumerated exhaustively when the budget affords it and the remainder is sampled in complement pairs; the weights of sampled coalitions are uniform over the remaining mass. The budget is $B=c\,d$ with $c\in\{4,16\}$, which gives $B\in\{40,160\}$ for $d=10$ and $B\in\{80,320\}$ for $d=20$ (evaluator source: \texttt{source\_evidence/evaluator\_final.py}, \texttt{kernel\_coalitions}, lines 761--812).

Let $\topk(\phi)$ be the indices of the three largest $|\phi_j|$, and let $\jac(A,B)=|A\cap B|/|A\cup B|$. For two top-3 sets with overlap $c\in\{0,1,2,3\}$ the Jaccard index is $c/(6-c)$, that is $0$, $0.2$, $0.5$ or $1$.

\paragraph{Reproducibility label.}
For an assessed run $\phi^{(0)}$ and $R=8$ reruns $\phi^{(1)},\dots,\phi^{(R)}$ that use fresh coalition draws but the same model, instance, background and budget,
\begin{equation}
y=\frac1R\sum_{r=1}^{R}\jac\big(\topk(\phi^{(0)}),\,\topk(\phi^{(r)})\big)\in[0,1].
\end{equation}
The label is conditional on the particular assessed run, so it can in principle be predicted from that run's data. It measures coalition-sampling noise only. Because it uses $R=8$ reruns it is itself a noisy estimate of the conditional expectation, and we cannot quantify that noise from the retained evidence.

\paragraph{Diagnostic task.}
The diagnostic receives, for each of up to 20 explained instances of a trained model, the assessed run's masks, weights, evaluated values and anchors, plus $d$, $B$, $k=3$ and the model-family name. It returns $\rhat\in[0,1]$ per instance. It never sees labels, reruns, model internals or dataset names.

\subsection{Design rationale}
Kernel SHAP is a weighted regression, so run-to-run variation of $\phi$ is sampling variation of regression coefficients. The top-3 set changes between runs when this variation is large relative to the gap between the third and fourth largest $|\phi_j|$. A single run contains information about its own sampling variation: deleting random subsets of its coalition pairs and re-solving the regression shows how sensitive $\phi$ is to the particular coalitions drawn. Propagating that sensitivity to the top-3 set by simulation gives an estimate of the expected overlap with a rerun, which is what the label measures. Two weaknesses motivate the remaining components. The jackknife is computed from only $B/2$ coalition pairs and is itself noisy, particularly at $4d$; and its spread need not match the rerun spread. We therefore shrink the simulated value toward a budget-specific prior. We hypothesized that this would reduce error most where the label is high and nearly constant (large budget) and that instance-specific information would matter most near ties between the third and fourth feature. We did not run component ablations, so these are design motivations and not tested mechanisms.

\subsection{Compared predictors}
\paragraph{Self-diagnostic (frozen selected configuration).}
For each instance, with $F=8$ folds and $P=4$ independent random partitions:
\begin{enumerate}
\item Assign complement pairs of coalitions at random to folds, drop one fold at a time, and re-solve the regression to obtain leave-fold-out solutions $\phi^{(-f)}$. Folds that leave no more than $d$ rows are skipped. Define centered, scaled deviations $\Delta_f=\sqrt{(F'-1)/F'}\,(\phi^{(-f)}-\bar\phi^{(-\cdot)})$ over the $F'$ valid folds, so that $\sum_f\Delta_f\Delta_f^{\top}$ is the delete-one-group jackknife covariance (the delete-a-group jackknife of survey sampling, \citealp{Kott2001Using}).
\item Simulate reruns with 1000 common-random-number draws (500 antithetic pairs, seeded by the episode seed). The diagonal simulator uses $\phi+\mu\,\sigma\odot\zeta$ with $\sigma_j=(\sum_f\Delta_{fj}^2)^{1/2}$ and $\zeta\sim\mathcal N(0,I_d)$. The full-covariance simulator uses $\phi+\sum_f\zeta_f\Delta_f$, which preserves the efficiency constraint. Each simulated top-3 set is compared with the observed one by Jaccard index and averaged. This gives $s_{d,1}$ (diagonal, $\mu=1$), $s_{d,0.7}$ (diagonal, $\mu=0.7$) and $s_{f,1}$ (full covariance, $\mu=1$).
\item Compute the margin $z_{\mathrm{m}}$, the gap between the third and fourth largest $|\phi_j|$ divided by the jackknife standard error of that gap, averaged over partitions along with the three simulated values.
\item Combine: $s=0.5\,s_{d,1}+0.2\,s_{d,0.7}+0.3\,s_{f,1}$ and
\begin{equation}
\rhat=\mathrm{clip}_{[0.02,1]}\Big(0.6\,s+0.4\,\pi(B/d)+0.02\tanh\big(z_{\mathrm m}/3\big)\Big),
\end{equation}
where the prior $\pi$ is linear in $\log_2(B/d)$ between $0.84$ at $B=4d$ and $0.96$ at $B=16d$.
\end{enumerate}
On any numerical failure the output falls back to $\pi(B/d)$. The source is in \texttt{source\_evidence/selected\_config\_program.py} (constants at lines 35--46; functions \texttt{\_jackknife\_cov}, \texttt{\_sim\_jaccard}, \texttt{\_margin\_z}, \texttt{\_empirical\_bayes} and \texttt{\_diagnose\_one}). The final record stores only a tree hash of the evaluated sources, so the above describes the source file of the configuration designated as selected in the search record, not a hash-verified copy.

Provenance of the constants matters for interpretation. The weights $0.5/0.2/0.3$, $0.6$, $0.02$, the fold count and the partition count are hand-set and were not tuned on instance labels. The values $0.84$ and $0.96$ are hand-set constants (\texttt{selected\_config\_program.py}, lines 41--45); the configuration's notes describe them as aggregate label means by budget seen in earlier evaluation metrics (\texttt{selected\_config\_NOTES.md}, ``Provenance of constants''), but no such means are retained in the evidence available to us, so we can neither verify the values nor their origin. The shrinkage weight is therefore a fixed constant, not an estimated empirical-Bayes weight; we use the term \emph{empirical-Bayes-style} only for the structure of shrinking an unreliable per-unit estimate toward a prior derived from other data, as in Stein-type estimators \citep{Efron1973Stein}.

\paragraph{Baselines and control.}
All are scored with the same per-instance squared error $(\rhat_i-y_i)^2$. \emph{Always reliable} outputs $\rhat=1$. \emph{Constant 0.5} outputs $0.5$. The \emph{split-half gap} heuristic is computed by the evaluator from the assessed run alone: it solves the regression separately on the two halves of the complement-pair blocks, sets $se_j=|\phi^A_j-\phi^B_j|/2$, forms $z=(|\phi|_{(3)}-|\phi|_{(4)})/\sqrt{se_{(3)}^2+se_{(4)}^2}$, and outputs $0.5+0.5\tanh z$. The \emph{pairing-permuted control} scores the diagnostic's own outputs against labels after permuting them among the 20 instances of an episode with each of 20 fixed derangements and averaging. It therefore keeps everything the diagnostic knows about the episode, such as its budget, model and dataset level, and removes only the instance-level pairing between $\rhat$ and $y$. The diagnostic exceeds this control only if its instance-specific variation is informative.

\subsection{Experimental protocol}
The evaluation was run once under a sealed protocol, with the selected configuration frozen beforehand. Datasets are the ACS income task (California, 2018, 1-year person records via folktables; $d=10$; 20{,}000 sampled rows), Give Me Some Credit (OpenML 46929; $d=10$; 20{,}000 sampled rows) and the second half of a hash-based split of Statlog German Credit ($d=20$; 485 rows). Models are scikit-learn logistic regression, a 100-tree random forest and a one-hidden-layer MLP with 64 units, trained on a 70\% split with train-only median imputation and standardization. For each dataset, family, budget in $\{4d,16d\}$ and seed in $\{9001,9002\}$ there is one episode of 20 explained test instances, with nine runs per instance (one assessed, eight reruns). That gives 36 episodes and 720 labeled instances. The protocol constants in this paragraph (instances, reruns, derangements, bootstrap replicates, seeds) are read from \texttt{source\_evidence/evaluator\_final.py} (line 42 for the seeds, lines 66--72 for the full-protocol values; lines 861--872 for the derangements) and \texttt{task\_contract.json}, not from the sealed metrics. Scores aggregate with equal weight over instances, then seeds within a dataset--family--budget cell, then cells within a dataset, then datasets. The headline quantity is $\text{score}=1-\text{MSE}$ of the diagnostic. A \emph{skill} is the MSE of a comparator minus the MSE of the diagnostic. The evaluator reports one-sided 2.5th-percentile lower bounds from 200 hierarchical bootstrap replicates that resample cells, seeds and instances within each of the three fixed datasets. These datasets were disjoint, by normalized record hash, from the two search-plane datasets (a hash-based split of German Credit and Pima Diabetes) used to choose the configuration (\texttt{final\_resources\_manifest.json}, \texttt{search\_resources\_manifest.json}). The evaluator's pre-declared assessment treats the diagnostic as informative only if the three skill lower bounds are positive and its score exceeds the permuted control by a positive lower bound (\texttt{task\_contract.json}, \texttt{protocol.promotion\_rule}).

\section{Results}\label{sec:results}
All numbers in this section come from the sealed final evaluation unless stated otherwise. The evaluation completed and its recorded outcome is \emph{qualified}. The pre-declared assessment rule from the protocol is met by the reported lower bounds, all four of which are positive. This is a statement about the diagnostic's measured skill in this regime, and not a validity, superiority or generality claim about Kernel SHAP reliability.

\subsection{Single-run reproducibility depends on the budget}
Mean top-3 Jaccard agreement is 0.8065 at $B=4d$ and 0.9315 at $B=16d$ (Figure~\ref{fig:main}b). 
The difference is 0.125. Since a one-feature swap gives Jaccard 0.5 and larger disagreements give at most 0.2, the loss $1-\bar y$ bounds the share of assessed--rerun pairs with non-identical top-3 sets. That share is at least $1-\bar y$ and at most $2(1-\bar y)$: between 19.3\% and 38.7\% at $4d$, and between 6.8\% and 13.7\% at $16d$ (derived; \texttt{analysis/derived\_metrics.json}). 
Even at $16d$, then, a noticeable minority of rerun pairs disagree on the identity of the top three features, and at $4d$ a substantial minority do. These are averages over datasets, model families, seeds and instances. The retained final evidence contains only per-seed aggregate scores, not per-cell labels, so we cannot say which datasets, families or instances drive them.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/main_comparison.pdf}
\caption{Sealed final evaluation. (a) Reduction in mean squared error of the single-run diagnostic relative to each baseline and to the pairing-permuted control, with the evaluator's one-sided 2.5th-percentile bootstrap lower bound (diamonds). (b) Mean top-3 Jaccard agreement between an assessed run and eight reruns at the two budgets, averaged over three final datasets, three model families, two seeds and 20 instances per cell.}
\label{fig:main}
\end{figure}

\subsection{The diagnostic against baselines and a control}
The diagnostic reaches a score of 0.9838 (MSE 0.0162, RMSE 0.127; derived). 
Table~\ref{tab:main} gives the comparison. Its MSE is lower than that of always-reliable by 0.0353, of constant 0.5 by 0.1543, and of the split-half-gap heuristic by 0.0122. The lower bounds of these three skills are 0.0171, 0.1245 and 0.0081, all positive. 
Relative to each comparator's MSE, the reductions are 68.5\%, 90.5\% and 42.9\% (derived). The \emph{always-reliable} baseline is the practitioner's default of trusting every run; the mean label deficit $1-y$, averaged over the two budgets, is only 0.131 (derived), so the room for improvement by prediction is small in absolute terms, and the split-half-gap heuristic already captures part of it.

\begin{table}[t]
\centering
\caption{Sealed final evaluation of the frozen self-diagnostic. Scores are $1-\text{MSE}$ against the rerun-agreement label; skills are MSE reductions. Lower bounds are the evaluator's one-sided 2.5th percentiles over 200 bootstrap replicates; no upper bounds were recorded. Columns marked $\dagger$ are derived from the reported values (\texttt{analysis/derived\_metrics.json}).}
\label{tab:main}
\small
\begin{tabular}{lccc}
\toprule
Quantity & Estimate & Lower bound & MSE$^\dagger$ / share$^\dagger$ \\
\midrule
Diagnostic score & 0.9838 & -- & 0.0162 \\
Skill vs.\ always reliable & 0.0353 & 0.0171 & 0.0515 \\
Skill vs.\ constant 0.5 & 0.1543 & 0.1245 & 0.1705 \\
Skill vs.\ split-half gap & 0.0122 & 0.0081 & 0.0284 \\
Permuted-control score & 0.9701 & -- & 0.0299 \\
Diagnostic $-$ control score & 0.0137$^\dagger$ & 0.0101 & 45.9\% of control MSE \\
Spearman $\rho(\rhat,y)$ & 0.5809 & -- & -- \\
Mean label at $4d$ / $16d$ & 0.8065 / 0.9315 & -- & -- \\
Score, seed 9001 / 9002 & 0.9850 / 0.9826 & -- & -- \\
\bottomrule
\end{tabular}
\end{table}


\subsection{How much is instance-specific?}
The pairing-permuted control scores 0.9701 against 0.9838 for the diagnostic, a difference of 0.0137 with lower bound 0.0101. 
In relative terms this is a 45.9\% reduction in MSE, but in absolute terms it is small, and Figure~\ref{fig:accounting}b shows why this matters for interpretation. Of the 0.0353 reduction over always-reliable, 0.0216 (61\%) is retained when the diagnostic's outputs are permuted within episodes, and 0.0137 (39\%) is lost. The retained part is episode-level information that may include the budget (through the prior) and dataset- or family-level shifts in the simulated values; the evidence does not apportion it. The lost part is the instance-specific information. Both parts are measured, and the lower bound for the instance-specific part is positive, which implies that labels vary across instances in a way that a single run can partly anticipate. The control does not separate budget calibration from dataset- or family-level calibration; the evidence has no breakdown that would allow this.

Rank resolution is moderate. The mean within-episode Spearman correlation between $\rhat$ and $y$ is 0.5809. 
 The evaluator assigns zero to episodes in which either vector is constant, which can happen when all 20 labels are 1.0; this convention may lower the average. A rank correlation of 0.58 means that $\rhat$ orders instances better than chance but not sharply: a threshold on $\rhat$ would misclassify many instances near the threshold. We did not evaluate any thresholded flagging rule, calibration curve or selective-prediction metric, so we make no claim about how well $\rhat$ would work as an abstention signal.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/error_accounting.pdf}
\caption{Error accounting derived from the sealed metrics. (a) Root-mean-squared error of each predictor against the rerun-agreement label. (b) Decomposition of the diagnostic's MSE reduction relative to always-reliable into the part that survives instance-level permutation and the instance-specific part.}
\label{fig:accounting}
\end{figure}

\subsection{Consistency across seeds and search-plane checks}
Per-seed scores are 0.9850 for seed 9001 and 0.9826 for seed 9002, a difference of 0.0025. With two seeds this gives no variance estimate, and the bootstrap lower bounds are the only recorded uncertainty. 
On the search plane (German Credit half A and Pima Diabetes), the selected configuration scored 0.9854, against 0.9838 on the sealed final data; this search score is a development proxy, was used for selection among three configurations, and is not an independent estimate. The prior constants 0.84 and 0.96 exceed the final label means by 0.0335 at $4d$ and 0.0285 at $16d$ (derived), so the prior was somewhat optimistic on the final data, and the diagnostic still qualified. 
 How much of the final score depends on this prior is unknown, because no variant without the prior was evaluated.

\section{Discussion and Limitations}\label{sec:limits}
\paragraph{What the evidence supports.}
Within the evaluated regime (Kernel SHAP, 32-row interventional background, $k=3$, budgets $4d$ and $16d$, three datasets, three model families), the answer to ``is one run enough?'' is conditional. The mean agreement is 0.81 at the smaller budget and 0.93 at the larger one, and a run-internal diagnostic can predict agreement with lower error than the baselines. We do not claim that SHAP is reliable or unreliable in general, nor that any specific agreement level is sufficient for a particular use. Sufficiency depends on the cost of a top-3 flip in the application, which the label does not encode.

\paragraph{What the control tells us.}
The margin over the permuted control is positive and its lower bound is positive, but 61\% of the diagnostic's gain over always-reliable survives permutation. Most of the measured benefit is therefore episode-level rather than instance-specific; it may reflect the budget, dataset- or family-level calibration, or both, and the evidence does not apportion it. The instance-specific contribution is real in the sense of the bootstrap, but small in absolute MSE. A fair comparison would also include a budget-conditional constant, which is the prior alone and was not evaluated; without it, we cannot say how much the simulation adds to the prior.

\paragraph{No component attribution.}
The diagnostic combines a partition ensemble, three simulators, a prior and a margin term. There are no ablations, so the results support the claim that the assembled configuration beats the baselines and the control in this regime, and not that any component is responsible. Three configurations were scored on the search plane (Supplementary Table~\ref{tab:search}); their per-seed ranges overlap for the two best, and we draw no mechanistic conclusion from the differences.

\paragraph{Scope of the label.}
The label captures only coalition-sampling noise. Background resampling \citep{Yuan2022empirical}, retraining noise and disagreement between explainers \citep{Krishna2022Disagreement} are not measured and woul

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}

\subsection{Evaluation protocol details}
Table~\ref{tab:data} lists the datasets, and the remaining protocol constants follow. All values are read from the evaluator source and manifests in \texttt{source\_evidence/}.
\begin{table}[h]
\centering
\caption{Datasets. Rows are after the evaluator's de-duplication and sampling. $d$ is the number of feature groups; budgets are $4d$ and $16d$.}
\label{tab:data}
\small
\begin{tabular}{llrrl}
\toprule
Plane & Dataset & Rows & $d$ & Source \\
\midrule
Search & German Credit, half A & 515 & -- & UCI Statlog, hash-parity split \\
Search & Pima Diabetes & 768 & -- & OpenML 37, v1 \\
Final & ACS income (CA, 2018) & 20{,}000 & 10 & folktables 0.0.12, ACSIncome \\
Final & Give Me Some Credit & 20{,}000 & 10 & OpenML 46929, v1 \\
Final & German Credit, half B & 485 & 20 & UCI Statlog, hash-parity split \\
\bottomrule
\end{tabular}
\end{table}
The ACS sample is the 20{,}000 rows with the smallest record hash after removing 5{,}711 duplicates from 195{,}665 records, and the Give Me Some Credit sample is selected the same way after removing 609 duplicates from 150{,}000 records. German Credit has no duplicates, and its two halves are assigned by the parity of the record hash. Per-seed sweeps (18 cells each) took 53.3\,s and 53.8\,s on CPU. 
The evaluator environment is pinned to numpy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1 and scipy 1.18.1, with 8 CPU cores, 16\,GB of memory and a 4500\,s wall-clock limit for the final plane (\texttt{task\_contract.json}). Final seeds are 9001 and 9002 and search seeds are 101 and 102. Each episode explains 20 test instances, uses 8 reruns, and the control uses 20 deterministic derangements.

\subsection{Derived quantities}
Table~\ref{tab:derived} lists every quantity derived from the sealed metrics. With score $=1-\text{MSE}$, the MSE of a comparator is one minus the diagnostic score plus its skill, and the permuted-control MSE is one minus the control score. All values are produced by \texttt{analysis/derive\_metrics.py} from \texttt{paper\_data.json}.
\begin{table}[h]
\centering
\caption{Derived error quantities. Reductions are relative to each comparator's MSE.}
\label{tab:derived}
\small
\begin{tabular}{lccc}
\toprule
Predictor & MSE & RMSE & MSE reduction by diagnostic \\
\midrule
Diagnostic & 0.0162 & 0.127 & -- \\
Split-half gap & 0.0284 & 0.169 & 42.9\% \\
Permuted control & 0.0299 & 0.173 & 45.9\% \\
Always reliable & 0.0515 & 0.227 & 68.5\% \\
Constant 0.5 & 0.1705 & 0.413 & 90.5\% \\
\bottomrule
\end{tabular}
\end{table}
The bounds on non-identical top-3 sets follow from the Jaccard values $\{0,0.2,0.5,1\}$ for overlaps $\{0,1,2,3\}$: a pair with non-identical sets loses between 0.5 and 1 of the maximal agreement, so a mean loss $D$ implies a non-identical share $q$ with $D\le q\le 2D$. The gain over always-reliable splits into $0.0216$ retained under permutation (the always-reliable MSE minus the control MSE) and $0.0137$ instance-specific.

\subsection{Selected configuration constants}
\begin{table}[h]
\centering
\caption{Constants of the frozen self-diagnostic. None was fitted to instance labels; the budget-prior values 0.84 and 0.96 are hand-set; the configuration's notes call them aggregate label means from earlier evaluation metrics, which are not retained in the evidence. Values are read from \texttt{selected\_config\_program.py} (constants at lines 35--46, simulator weights at lines 55--63), not from the sealed metrics.}
\label{tab:consts}
\small
\begin{tabular}{lll}
\toprule
Constant & Value & Role \\
\midrule
Folds / partitions & 8 / 4 & delete-one-group jackknife, averaged \\
Draws & 1000 (500 antithetic) & common random numbers per episode \\
Simulator weights ($s_{d,1}$, $s_{d,0.7}$, $s_{f,1}$) & 0.5, 0.2, 0.3 & convex combination \\
Prior at $B=4d$ / $16d$ & 0.84 / 0.96 & hand-set; origin per notes only \\
Prior weight & 0.4 & shrinkage toward prior \\
Margin term & 0.02, scale 3 & soft gate, $\tanh(z_{\mathrm m}/3)$ \\
Output clip & $[0.02,1]$ & numerical safety \\
\bottomrule
\end{tabular}
\end{table}
The notes accompanying the configuration state that it was written without executing any code, so no local calibration or cross-validation exists for it and none is claimed. Its search-plane score was obtained only from the evaluator.

\subsection{Search-plane scores of the three configurations}
Three configurations were scored on the search plane; all three completed successfully and none was unscored. The search label is evaluator-defined, so it is the same quantity as in the final evaluation, but the datasets differ, and these scores are development proxies. Table~\ref{tab:search} lists them. Configuration~A is a single-partition jackknife with full covariance and a $\sqrt2$ inflation of the simulated spread and 400 draws. Configuration~B replaces this with common-random-number draws, diagonal and full-covariance simulators and a fixed convex combination. Configuration~C, the selection, adds the partition ensemble, the budget prior and the margin term (\texttt{searchplane\_config\_A\_program.py}, \texttt{searchplane\_config\_B\_program.py}, \texttt{selected\_config\_program.py}). Because several changes were made at once and no ablation was run, no change is credited with a score difference. The per-seed ranges of B and C overlap, and A is lower than both on each of the two seeds.
\begin{table}[h]
\centering
\caption{Search-plane scores ($1-\text{MSE}$) by seed. Search seeds are 101 and 102.}
\label{tab:search}
\small
\begin{tabular}{lccc}
\toprule
Configuration & Seed 101 & Seed 102 & Mean \\
\midrule
A (inflated full-covariance jackknife) & 0.9740 & 0.9779 & 0.9760 \\
B (common-random-number combination) & 0.9824 & 0.9849 & 0.9837 \\
C (selected: B + partitions, prior, margin) & 0.9840 & 0.9869 & 0.9854 \\
\bottomrule
\end{tabular}
\end{table}


\subsection{Reproducibility statement}
The evaluator source, task contract, manifests and the source of the selected configuration are in \texttt{source\_evidence/}. The scripts \texttt{analysis/derive\_metrics.py} and \texttt{analysis/build\_figures.py} regenerate Table~\ref{tab:derived} and Figures~\ref{fig:main} and~\ref{fig:accounting} from \texttt{paper\_data.json}. Figure~\ref{fig:overview} is a schematic with no quantitative content. We did not re-run the sealed evaluation, and per-cell labels and per-instance outputs from it are not part of the retained evidence.

\subsection{LLM usage}
Large language models were used in this work in two roles. First, an LLM-based research agent proposed and implemented the candidate diagnostics, and the sealed evaluator, not the agent, scored them. Second, an LLM drafted this manuscript from the recorded evaluator outputs and source files, and generated the analysis and figure scripts. Every number in the paper was checked against the recorded evaluator outputs or computed from them by the included scripts. No LLM output was used as a source of experimental results. References were retrieved from bibliographic databases; our descriptions of cited works rely on their public titles and on the model's prior knowledge, and the papers were not re-read in full while writing.
```
