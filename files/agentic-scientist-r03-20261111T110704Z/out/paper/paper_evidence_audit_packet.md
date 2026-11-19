# Agentic evidence audit packet

- generated_at: `2026-11-11T13:22:03.479657+00:00`
- paper_dir: `work/results/r03/claude/20261111_111139/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261111_122649-paper_evidence_audit_round_9-ucs9r5za/workspace`

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
    "anchored_references": 35,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 48,
    "resolved_references": 17,
    "total_references": 52
  },
  "ok": true,
  "pdf_path": "work/results/r03/claude/20261111_111139/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 35,
    "dangling_references": 0,
    "manifests_checked": 3,
    "resolved_references": 17,
    "total_references": 52
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "claim": "Pooled over three leaderboards the sealed final nRMSE is 0.562 and skill against column-mean imputation is 0.434.",
      "source_ids": [
        "final.metric.final_nrmse",
        "final.metric.final_score"
      ]
    },
    {
      "claim": "Per-seed pooled skills of the sealed evaluation are 0.433, 0.427 and 0.433 (seeds 201-203), 157.4/160.6/161.0 s per seed.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Per-leaderboard nRMSE: MTEB 0.703, HELM Lite 0.501, Open LLM Leaderboard 0.482.",
      "source_ids": [
        "final.metric.final_nrmse_mteb",
        "final.metric.final_nrmse_helm",
        "final.metric.final_nrmse_oll"
      ]
    },
    {
      "claim": "MTEB nRMSE at k=2,5,10,20 is 0.787, 0.722, 0.664, 0.638; per-added-benchmark reductions about 0.022, 0.012, 0.003 are differences of these values divided by added benchmarks; k=20 is about 7% of 297 columns.",
      "source_ids": [
        "final.metric.final_nrmse_mteb_k2",
        "final.metric.final_nrmse_mteb_k5",
        "final.metric.final_nrmse_mteb_k10",
        "final.metric.final_nrmse_mteb_k20"
      ]
    },
    {
      "claim": "Skill against greedy-forward ridge is 0.099 and against random-k ridge is 0.016; difference 0.083; implied error ratio about 1.09 is indicative only. Selector and imputer are scored jointly, so these margins are not a test of selection alone; the 0.016 margin is small and unresolved.",
      "source_ids": [
        "final.metric.final_skill_vs_greedy_ridge",
        "final.metric.final_skill_vs_random_selection"
      ]
    },
    {
      "claim": "Permuted-control gap is 0.678 nRMSE.",
      "source_ids": [
        "final.metric.final_permuted_control_gap"
      ]
    },
    {
      "claim": "The sealed final evaluation completed with outcome qualified.",
      "source_ids": [
        "final.qualification.outcome",
        "final.qualification.status",
        "final.qualification.correct"
      ]
    },
    {
      "claim": "Sealed evaluation used seeds 201-203 with 14 episodes per seed. The identity of the sealed-evaluated source tree is not established by retained artifacts (presumably the development-selected pair or its latent-skill extension, which have identical development scores); no hash-comparison artifact exists.",
      "source_ids": [
        "final.evidence.episodes",
        "final.qualification.outcome"
      ]
    },
    {
      "claim": "Development-partition scores: simple pair 0.220, proposed pair 0.247 (seed scores 0.243 and 0.251), latent-extended pair 0.247 identical.",
      "source_ids": [
        "result.top_program_01",
        "result.top_program_02",
        "result.top_program_03"
      ]
    },
    {
      "claim": "Development-partition nRMSE (1.067 vs 1.028), skill vs random-k (0.100 vs 0.132) and permuted gap (0.522 vs 0.568) are read from search-split metric files (analysis/search_metrics.json) rather than from the final registry.",
      "source_ids": [
        "result.top_program_01",
        "result.top_program_03"
      ]
    },
    {
      "claim": "Three configurations were scored in total on the development partition.",
      "source_ids": [
        "result.total_evaluated_programs"
      ]
    },
    {
      "claim": "Final aggregate nRMSE of 0.562 is the equal-weight mean of the three leaderboard values; the valid-run flag requires real episodes to beat controls.",
      "source_ids": [
        "final.metric.final_nrmse",
        "final.metric.final_nrmse_mteb",
        "final.metric.final_nrmse_helm",
        "final.metric.final_nrmse_oll"
      ]
    },
    {
      "citation_keys": [
        "Hendrycks2021MMLU",
        "Srivastava2023BIGbench",
        "Liang2023HELM",
        "Muennighoff2023MTEB"
      ],
      "claim": "Benchmark suites: MMLU, BIG-bench, HELM, MTEB.",
      "source_ids": [
        "ref.openalex.W3083410900",
        "ref.openalex.W4281690148",
        "ref.openalex.W4320003957",
        "ref.openalex.W4386576685"
      ]
    },
    {
      "citation_keys": [
        "Polo2024TinyBenchmarks",
        "Vivek2024AnchorPoints",
        "Perlitz2024EfficientBenchmarking",
        "Kipnis2024Metabench",
        "Hofmann2025Fluid"
      ],
      "claim": "Item-level reduction of evaluation cost, adaptive item selection under an item-response model, and sparse benchmark distillation from several benchmarks.",
      "source_ids": [
        "ref.openalex.W4392181972",
        "ref.openalex.W4411630215",
        "ref.openalex.W4401042935",
        "ref.openalex.W4406058560",
        "ref.openalex.W4415087836"
      ]
    },
    {
      "citation_keys": [
        "Perlitz2024BenchBench",
        "Ruan2024ObservationalScaling",
        "Polo2024Sloth"
      ],
      "claim": "Agreement analyses across benchmarks and low-dimensional capability models bear on how related benchmark scores are.",
      "source_ids": [
        "ref.openalex.W4403662613",
        "ref.openalex.W4415798639",
        "ref.openalex.W4405254278"
      ]
    },
    {
      "citation_keys": [
        "Ruan2024ObservationalScaling",
        "Polo2024Sloth",
        "Embretson2000IRT"
      ],
      "claim": "Latent-capability and scaling views of multi-benchmark performance; IRT; latent-factor predictors not run as baselines.",
      "source_ids": [
        "ref.openalex.W4415798639",
        "ref.openalex.W4405254278",
        "ref.openalex.W1648888400"
      ]
    },
    {
      "citation_keys": [
        "Dempster1977EM",
        "Rubin1976Inference",
        "Candes2009MatrixCompletion",
        "Salakhutdinov2007PMF",
        "Chaloner1995BayesianDesign",
        "Nemhauser1978Submodular",
        "Krause2008NearOptimalSensor",
        "Wolpert1992Stacked",
        "Breiman1996Stacked",
        "Hoerl1970Ridge",
        "Lawson1995NNLS"
      ],
      "claim": "EM for Gaussian missing data, missingness assumptions, matrix completion, experimental design and submodular greedy selection, stacking and ridge are standard tools.",
      "source_ids": [
        "ref.openalex.W2049633694",
        "ref.openalex.W2100358124",
        "ref.openalex.W2611328865",
        "ref.openalex.W2137245235",
        "ref.openalex.W2014018052",
        "ref.openalex.W1680189815",
        "ref.openalex.W2131824593",
        "ref.openalex.W28412257",
        "ref.openalex.W2914369697",
        "ref.openalex.W4234698323",
        "ref.openalex.W2075665712"
      ]
    },
    {
      "citation_keys": [
        "Zhou2023IFEval",
        "Suzgun2023BBH",
        "Hendrycks2021MATH",
        "Rein2023GPQA",
        "Sprague2023MuSR",
        "Wang2024MMLUPro"
      ],
      "claim": "Open LLM Leaderboard component benchmarks: IFEval, BBH, MATH, GPQA, MuSR, MMLU-Pro.",
      "source_ids": [
        "ref.openalex.W4388718089",
        "ref.openalex.W4306808908",
        "ref.openalex.W3134642945",
        "ref.openalex.W4388926373",
        "ref.openalex.W4387947619",
        "ref.openalex.W4415796274"
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
  "grounding_source_count": 27,
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
  "campaign_results_dir": "work/results/r03/claude/20261111_111139/investigation",
  "count": 30,
  "generated_at": "2026-11-11T12:27:26.847154+00:00",
  "queries": [
    "An analysis of approximations for maximizing submodular set functions\u2014I",
    "Anchor Points: Benchmarking Models with Much Fewer Examples",
    "Bayesian Experimental Design: A Review",
    "Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models",
    "BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions",
    "Comparing Test Sets with Item Response Theory",
    "Do These LLM Benchmarks Agree? Fixing Benchmark Evaluation with BenchBench",
    "Efficient Benchmarking of Language Models",
    "Exact Matrix Completion via Convex Optimization",
    "Holistic Evaluation of Language Models",
    "Inference and missing data",
    "Item Response Theory for Psychologists",
    "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena",
    "MTEB: Massive Text Embedding Benchmark",
    "Maximum Likelihood from Incomplete Data Via the EM Algorithm",
    "Measuring Massive Multitask Language Understanding",
    "Near-Optimal Sensor Placements in Gaussian Processes: Theory, Efficient Algorithms and Empirical Studies",
    "Near-optimal observation selection using submodular functions",
    "Observational Scaling Laws and the Predictability of Language Model Performance",
    "Probabilistic Matrix Factorization",
    "Ridge Regression: Biased Estimation for Nonorthogonal Problems",
    "Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families",
    "Solving Least Squares Problems",
    "Stacked generalization",
    "Stacked regressions",
    "metabench - A Sparse Benchmark of Reasoning and Knowledge in Large Language Models",
    "tinyBenchmarks: evaluating LLMs with fewer examples"
  ],
  "reference_query_plan": {
    "architectural_shifts": [
      "from pure conditional-variance Gaussian imputation (nRMSE 1.067 in search) to quantile-transformed wrapper-selected NNLS-stacked imputation (nRMSE 1.028)",
      "adding a monotone latent-skill member and A-optimal selector to the stack gave identical search score to the stacked incumbent (no measurable gain)",
      "final sealed evaluation nRMSE 0.562 overall, with MTEB error decreasing as k grows (0.787 at k=2 to 0.638 at k=20)"
    ],
    "benchmarks": [
      "MTEB (embedding models x tasks)",
      "HELM Lite (core scenarios)",
      "Open LLM Leaderboard (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO)"
    ],
    "central_topic": "Choosing a small subset of k benchmarks to run on a new model and imputing its scores on the remaining benchmarks from a historical model-by-benchmark score matrix (MTEB, HELM Lite, Open LLM Leaderboard), evaluated by held-out-model normalized RMSE against random selection, ridge and permuted-control baselines.",
    "comparators": [
      "random benchmark selection",
      "greedy ridge regression on selected benchmarks",
      "permuted-control baseline",
      "low-rank matrix completion / probabilistic matrix factorization",
      "item-response-theory style latent ability models for LLM evaluation",
      "benchmark-sparsification work (metabench, tinyBenchmarks)",
      "observational scaling laws and Sloth skill scaling laws"
    ],
    "core_methods": [
      "greedy conditional-variance (Gaussian/low-rank) benchmark subset selection",
      "EM-estimated Gaussian covariance with conditional-mean imputation of missing scores",
      "wrapper cross-validated forward selection of benchmarks",
      "rank-Gauss (quantile) transform with range clipping",
      "per-target NNLS stacked ensemble of imputers",
      "monotone-link latent-skill model with Huber MAP and Laplace posterior",
      "A-optimal experimental-design selection"
    ],
    "forbidden_query_patterns": [
      "generic 'benchmarking' or 'optimization' phrasing",
      "scientific method / paper-writing phrasing",
      "chronology of campaign cycles, ideas, or attempts",
      "internal terms such as combined_score, rubric, program_1, eligible",
      "queries naming or hinting at the prior published paper on this exact task (do not search for its title, authors, or results)",
      "unsupported claims about generative-LLM benchmark transfer beyond MTEB/HELM Lite/Open LLM Leaderboard"
    ],
    "queries": [
      {
        "category": "core_method",
        "query": "predicting language model benchmark performance from a subset of benchmarks low-rank",
        "rationale": "Central problem: infer a new model's scores on unrun benchmarks from k observed ones using a historical score matrix."
      },
      {
        "category": "core_method",
        "query": "greedy subset selection conditional variance Gaussian process sensor placement submodular",
        "rationale": "Theory-side literature behind greedy conditional-variance selection and its near-optimality guarantees."
      },
      {
        "category": "core_method",
        "query": "EM algorithm multivariate Gaussian missing data covariance estimation conditional mean imputation",
        "rationale": "The incumbent imputer estimates a Gaussian covariance by EM from a partially observed matrix and imputes by conditional mean."
      },
      {
        "category": "baseline_comparator",
        "query": "stacked generalization non-negative least squares ensemble",
        "rationale": "Per-target NNLS stack of imputers is the best-scoring configuration; need the stacking/NNLS-combining reference."
      },
      {
        "category": "baseline_comparator",
        "query": "matrix completion low-rank probabilistic matrix factorization missing entries",
        "rationale": "Expected comparator family for score-matrix imputation with a low-rank/latent structure."
      },
      {
        "category": "baseline_comparator",
        "query": "item response theory efficient evaluation of language models few examples",
        "rationale": "Latent-ability models (monotone-link latent skill) and benchmark-sparsification comparators such as metabench/tinyBenchmarks."
      },
      {
        "category": "result_driven_theme",
        "query": "observational scaling laws low-dimensional capability space language models",
        "rationale": "Supports the low-dimensional latent skill explanation and the starter-list work on cross-benchmark predictability (including Sloth)."
      },
      {
        "category": "architectural_shift",
        "query": "A-optimal Bayesian experimental design active feature selection",
        "rationale": "A-optimal latent selector was added in the third variant and gave no gain; need experimental-design background."
      },
      {
        "category": "result_driven_theme",
        "query": "cross-benchmark agreement of LLM benchmarks correlation of model rankings",
        "rationale": "Variation in predictability across leaderboards and the permuted-control gap relate to benchmark-agreement analysis."
      },
      {
        "category": "benchmark_context",
        "query": "MTEB massive text embedding benchmark leaderboard",
        "rationale": "MTEB is the primary data source and the setting with the highest error across k."
      }
    ],
    "result_driven_themes": [
      "few benchmarks recover the rest only modestly: skill over random selection is small (final 0.016) while gain over greedy ridge is larger (0.099)",
      "prediction difficulty varies by leaderboard (HELM 0.50, Open LLM 0.48, MTEB 0.70)",
      "diminishing returns in k on MTEB",
      "permuted-control gap shows that cross-benchmark structure is real",
      "low-rank / latent-skill structure in model-by-benchmark matrices"
    ],
    "status": "ready"
  },
  "reference_query_plans": [
    {
      "architectural_shifts": [
        "from pure conditional-variance Gaussian imputation (nRMSE 1.067 in search) to quantile-transformed wrapper-selected NNLS-stacked imputation (nRMSE 1.028)",
        "adding a monotone latent-skill member and A-optimal selector to the stack gave identical search score to the stacked incumbent (no measurable gain)",
        "final sealed evaluation nRMSE 0.562 overall, with MTEB error decreasing as k grows (0.787 at k=2 to 0.638 at k=20)"
      ],
      "benchmarks": [
        "MTEB (embedding models x tasks)",
        "HELM Lite (core scenarios)",
        "Open LLM Leaderboard (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO)"
      ],
      "central_topic": "Choosing a small subset of k benchmarks to run on a new model and imputing its scores on the remaining benchmarks from a historical model-by-benchmark score matrix (MTEB, HELM Lite, Open LLM Leaderboard), evaluated by held-out-model normalized RMSE against random selection, ridge and permuted-control baselines.",
      "comparators": [
        "random benchmark selection",
        "greedy ridge regression on selected benchmarks",
        "permuted-control baseline",
        "low-rank matrix completion / probabilistic matrix factorization",
        "item-response-theory style latent ability models for LLM evaluation",
        "benchmark-sparsification work (metabench, tinyBenchmarks)",
        "observational scaling laws and Sloth skill scaling laws"
      ],
      "core_methods": [
        "greedy conditional-variance (Gaussian/low-rank) benchmark subset selection",
        "EM-estimated Gaussian covariance with conditional-mean imputation of missing scores",
        "wrapper cross-validated forward selection of benchmarks",
        "rank-Gauss (quantile) transform with range clipping",
        "per-target NNLS stacked ensemble of imputers",
        "monotone-link latent-skill model with Huber MAP and Laplace posterior",
        "A-optimal experimental-design selection"
      ],
      "forbidden_query_patterns": [
        "generic 'benchmarking' or 'optimization' phrasing",
        "scientific method / paper-writing phrasing",
        "chronology of campaign cycles, ideas, or attempts",
        "internal terms such as combined_score, rubric, program_1, eligible",
        "queries naming or hinting at the prior published paper on this exact task (do not search for its title, authors, or results)",
        "unsupported claims about generative-LLM benchmark transfer beyond MTEB/HELM Lite/Open LLM Leaderboard"
      ],
      "queries": [
        {
          "category": "core_method",
          "query": "predicting language model benchmark performance from a subset of benchmarks low-rank",
          "rationale": "Central problem: infer a new model's scores on unrun benchmarks from k observed ones using a historical score matrix."
        },
        {
          "category": "core_method",
          "query": "greedy subset selection conditional variance Gaussian process sensor placement submodular",
          "rationale": "Theory-side literature behind greedy conditional-variance selection and its near-optimality guarantees."
        },
        {
          "category": "core_method",
          "query": "EM algorithm multivariate Gaussian missing data covariance estimation conditional mean imputation",
          "rationale": "The incumbent imputer estimates a Gaussian covariance by EM from a partially observed matrix and imputes by conditional mean."
        },
        {
          "category": "baseline_comparator",
          "query": "stacked generalization non-negative least squares ensemble",
          "rationale": "Per-target NNLS stack of imputers is the best-scoring configuration; need the stacking/NNLS-combining reference."
        },
        {
          "category": "baseline_comparator",
          "query": "matrix completion low-rank probabilistic matrix factorization missing entries",
          "rationale": "Expected comparator family for score-matrix imputation with a low-rank/latent structure."
        },
        {
          "category": "baseline_comparator",
          "query": "item response theory efficient evaluation of language models few examples",
          "rationale": "Latent-ability models (monotone-link latent skill) and benchmark-sparsification comparators such as metabench/tinyBenchmarks."
        },
        {
          "category": "result_driven_theme",
          "query": "observational scaling laws low-dimensional capability space language models",
          "rationale": "Supports the low-dimensional latent skill explanation and the starter-list work on cross-benchmark predictability (including Sloth)."
        },
        {
          "category": "architectural_shift",
          "query": "A-optimal Bayesian experimental design active feature selection",
          "rationale": "A-optimal latent selector was added in the third variant and gave no gain; need experimental-design background."
        },
        {
          "category": "result_driven_theme",
          "query": "cross-benchmark agreement of LLM benchmarks correlation of model rankings",
          "rationale": "Variation in predictability across leaderboards and the permuted-control gap relate to benchmark-agreement analysis."
        },
        {
          "category": "benchmark_context",
          "query": "MTEB massive text embedding benchmark leaderboard",
          "rationale": "MTEB is the primary data source and the setting with the highest error across k."
        }
      ],
      "result_driven_themes": [
        "few benchmarks recover the rest only modestly: skill over random selection is small (final 0.016) while gain over greedy ridge is larger (0.099)",
        "prediction difficulty varies by leaderboard (HELM 0.50, Open LLM 0.48, MTEB 0.70)",
        "diminishing returns in k on MTEB",
        "permuted-control gap shows that cross-benchmark structure is real",
        "low-rank / latent-skill structure in model-by-benchmark matrices"
      ],
      "status": "ready"

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
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{subcaption}

\newcommand{\nrmse}{\mathrm{nRMSE}}

\title{How Far Do $k$ Benchmarks Go? Cold-Start Benchmark Selection and Score Imputation on Family-Disjoint Held-Out Models}

\begin{document}
\maketitle

\begin{abstract}
Evaluating a new model on every benchmark of a leaderboard is expensive, yet benchmarks may be substantially redundant, so a few runs might carry information about the rest. We study the cold-start version of this problem: given a model$\times$benchmark history with missing cells, commit to $k$ benchmarks before seeing the new model, run only those, and impute the rest. We evaluate a family of selector--imputer pairs built from a rank-Gauss transform, an EM-fitted Gaussian with missing data, cross-validated wrapper selection, and a per-target non-negative stack of imputers; the identity of the exact source tree evaluated in the sealed run is not established by the retained artifacts, and we presume it is the development-selected pair or its latent-skill extension. Evaluation uses held-out models from model families disjoint from the history on three public leaderboards (MTEB, Open LLM Leaderboard, HELM Lite). The evaluated pair attains pooled normalized RMSE 0.562, a mean relative error reduction (skill) of 0.434 against column-mean imputation, and beats permuted-observation controls by a wide margin, but its skill over random-$k$ selection with a ridge imputer is only 0.016. On MTEB the error falls from 0.787 at $k{=}2$ to 0.638 at $k{=}20$ with sharply diminishing returns. Selector and imputer are scored jointly, three seeds do not resample held-out models, and no component ablation was run, so we do not attribute the gain to either part.
\end{abstract}

\section{Introduction}
A full evaluation of a language or embedding model touches dozens to hundreds of benchmarks, each costing compute, time and human effort. Public leaderboards meanwhile accumulate large model$\times$benchmark score matrices, and benchmark suites such as MMLU, BIG-bench, HELM and MTEB \citep{Hendrycks2021MMLU,Srivastava2023BIGbench,Liang2023HELM,Muennighoff2023MTEB} are plausibly overlapping in what they measure: agreement analyses across benchmarks and low-dimensional capability models fitted to public evaluations both bear on how related benchmark scores are \citep{Perlitz2024BenchBench,Ruan2024ObservationalScaling,Polo2024Sloth}. This suggests a budgeted-evaluation protocol: an evaluator holding a historical matrix with $M$ models, $N$ benchmarks and missing cells receives a new model, can afford only $k\ll N$ benchmark runs, and wants to infer the scores on the other $N-k$ benchmarks as accurately as possible. Two decisions then matter: \emph{which} $k$ benchmarks to run, and \emph{how} to turn their scores into predictions. A practitioner also needs to know how large $k$ must be.

Prior work on cheaper evaluation mostly reduces the number of \emph{items} within one benchmark \citep{Polo2024TinyBenchmarks,Vivek2024AnchorPoints,Perlitz2024EfficientBenchmarking}, distills a handful of benchmarks into a sparse one \citep{Kipnis2024Metabench}, or fits low-dimensional capability models across many benchmarks \citep{Ruan2024ObservationalScaling,Polo2024Sloth}. The setting studied here differs in three ways: the selection is committed \emph{before} any score of the new model is seen, the target is the score on every unrun benchmark, and the new model comes from a family that is absent from the history.

\paragraph{Research question and hypotheses.} When only $k$ benchmarks can be run on a new model, how accurately can a history-fitted selector--imputer pair recover its other scores, how does the error fall with $k$, and how much of the gain comes from cross-benchmark structure versus the choice of which $k$ to run? We examine four hypotheses.
\textbf{H1}: observed scores on a selected subset predict the remaining scores better than history-only column means.
\textbf{H2}: the error decreases with $k$ with diminishing returns.
\textbf{H3}: a model-based selector adds accuracy beyond random selection under a comparable imputer.
\textbf{H4}: difficulty differs across leaderboards.

\paragraph{What the evidence supports.} Using a sealed evaluation on family-disjoint held-out models from three leaderboards, H1 and H2 are supported, H4 is observed but confounded by the number of benchmarks per leaderboard, and H3 is not tested by the sealed evaluation, because selector and imputer are scored jointly; the 0.016 skill margin over random-$k$ ridge is small and unresolved. Figure~\ref{fig:overview} summarises the protocol.

\paragraph{Contributions.}
(i) A precise cold-start protocol with committed selection, family-disjoint held-out models, evaluator-owned baselines and negative controls, and a hierarchical aggregation rule (Section~\ref{sec:protocol}).
(ii) A reimplementable selector--imputer design built from standard components: rank-Gauss transform, EM Gaussian, wrapper selection, NNLS stacking (Section~\ref{sec:method}).
(iii) An error-versus-$k$ curve on MTEB and per-leaderboard errors, with skill relative to three baselines and a permutation control (Section~\ref{sec:results}).
(iv) A calibrated account of what the evidence cannot show: no ablation, no theory check, joint scoring of selector and imputer, and seed variation that does not reflect held-out sampling (Section~\ref{sec:limits}).

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/protocol_overview.png}
\caption{Cold-start protocol. A history matrix with missing cells is given to the method; it commits to $k$ benchmark indices; only the new model's scores on those $k$ benchmarks are revealed; the method predicts all other benchmarks; error is measured in units of history column standard deviations and compared with column-mean, random-$k$ ridge and greedy-forward ridge baselines and with permuted-observation controls.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\paragraph{Benchmark suites and their overlap.} Multi-task suites aggregate many sub-benchmarks \citep{Hendrycks2021MMLU,Srivastava2023BIGbench,Liang2023HELM,Muennighoff2023MTEB}. Agreement analyses across benchmarks \citep{Perlitz2024BenchBench} bear on how related benchmark scores are; here the target, the held-out split and the aggregation are defined explicitly.

\paragraph{Cheaper evaluation within or across benchmarks.} tinyBenchmarks, anchor points and efficient-benchmarking studies shrink the number of items of a single benchmark while preserving its score or ranking \citep{Polo2024TinyBenchmarks,Vivek2024AnchorPoints,Perlitz2024EfficientBenchmarking}. metabench distills a sparse benchmark from several benchmarks \citep{Kipnis2024Metabench}. Fluid benchmarking goes further by choosing items adaptively under an item-response model of latent ability \citep{Hofmann2025Fluid}. These works reduce or adapt item counts within a benchmark or a fixed suite; here the unit of selection is a whole benchmark, the choice is committed before any score of the new model is seen, and the target is every benchmark not run.

\paragraph{Latent-capability and scaling views.} Observational scaling laws and skill scaling laws explain multi-benchmark performance through a few latent capability factors estimated from public evaluations \citep{Ruan2024ObservationalScaling,Polo2024Sloth}, and item response theory has long modelled responses through latent ability \citep{Embretson2000IRT}. These latent-factor predictors are the closest benchmark-level relatives of the present setting; we did not run them as baselines, so how they compare under our protocol is left open. Our imputer uses a Gaussian dependence structure rather than an explicit latent-factor law, and we evaluate on family-disjoint models rather than within-family extrapolation.

\paragraph{Missing data, matrix completion and design.} Gaussian models with missing entries are fitted by EM \citep{Dempster1977EM} under missingness assumptions discussed by \citet{Rubin1976Inference}. Low-rank and probabilistic matrix completion \citep{Candes2009MatrixCompletion,Salakhutdinov2007PMF} are the standard alternatives for filling score matrices. Selecting observations to minimise posterior uncertainty is an experimental-design problem \citep{Chaloner1995BayesianDesign}; for Gaussian processes, greedy selection of informative variables has near-optimality guarantees when the objective is submodular \citep{Nemhauser1978Submodular,Krause2008NearOptimalSensor}. Stacked generalization combines predictors with weights fitted on held-out predictions \citep{Wolpert1992Stacked,Breiman1996Stacked}, and ridge regression \citep{Hoerl1970Ridge} is the linear baseline used by the evaluator.

\section{Method}\label{sec:method}

\subsection{Problem setup and success criterion}\label{sec:setup}
Let $X\in\mathbb{R}^{M\times N}$ be a history matrix with observation mask $O\in\{0,1\}^{M\times N}$; benchmark $j$ has history mean $m_j$ and standard deviation $\sigma_j$ computed over its observed cells. A new model $i$ has scores $y_{ij}$ on a subset $\mathcal{O}_i$ of benchmarks (not every model was run on every benchmark). A method must (a) output a set $S$ of $k$ benchmark indices \emph{before} seeing any new-model score (non-adaptive selection), and (b) given $y_{iS}$ (only the entries in $\mathcal{O}_i\cap S$), output predictions $\hat y_{ij}$ for all $j$. Scoring uses the cells $\mathcal{C}_i=\mathcal{O}_i\setminus S$. For one evaluation episode with $T$ held-out models,
\begin{equation}
\nrmse=\sqrt{\frac1T\sum_{i=1}^{T}\frac{1}{|\mathcal{C}_i|}\sum_{j\in\mathcal{C}_i}\Big(\frac{\hat y_{ij}-y_{ij}}{\sigma_j}\Big)^2},
\end{equation}
so every held-out model has equal weight and every benchmark is on the scale of its history spread. A baseline $b$ yields the skill
\begin{equation}
\mathrm{skill}_b = \mathrm{clip}\big(1-\nrmse/\nrmse_b,\,-1,\,1\big),
\end{equation}
the relative error reduction against that baseline, which is $0$ at parity and negative when worse.

\subsection{Design rationale}\label{sec:rationale}
If benchmark scores are jointly Gaussian with covariance $\Sigma$ and benchmarks in $S$ are observed, the conditional mean $\mathbb{E}[y_U\mid y_S]$ ($U$ the unrun benchmarks) minimises mean squared error, and the expected squared error summed over $U$ equals $\operatorname{tr}\Sigma_{U\mid S}$. Choosing $S$ greedily to reduce this trace (an A-optimal design) is therefore a principled selector \emph{under the Gaussian model}. Concretely, for a row-vector of scores $y\sim\mathcal{N}(\mu,\Sigma)$ and observation noise $\lambda\ge 0$, the posterior covariance after observing benchmark $j$ is $R'=R-R_{\cdot j}R_{j\cdot}/(R_{jj}+\lambda)$ with $R$ initialised at $\Sigma$, and the resulting drop of the summed variance over the remaining benchmarks is $\sum_{i\in U,\,i\neq j}R_{ij}^2/(R_{jj}+\lambda)$. A benchmark scores highly if it is strongly correlated with many others and itself has substantial variance, so redundant benchmarks are avoided once one of them has been chosen, because the update deflates their shared variance. The classical near-optimality guarantees for greedy selection \citep{Nemhauser1978Submodular,Krause2008NearOptimalSensor} apply to submodular objectives; we do not claim that the trace criterion with noise and missing data satisfies the required conditions here. We state the Gaussian argument only as motivation: we did not check it against a controlled experiment, and real score matrices are bounded, skewed and sparsely observed, which can make the trace criterion misaligned with realised held-out error. Three design choices address this misalignment:
(1) a per-benchmark rank-Gauss transform makes marginals closer to normal, with predictions mapped back through the stored history quantiles and clipped to the observed history range;
(2) a wrapper selector scores candidate benchmarks directly by cross-validated held-out-model error, instead of the model-based trace alone;
(3) a per-target non-negative-least-squares stack \citep{Lawson1995NNLS,Breiman1996Stacked} lets each target benchmark weight several imputers (Gaussian conditional means, ridge, nearest-neighbour models, column median), with a median-shrinkage fallback when the stack does not beat the median in cross-validation.
All tuning uses history models only.

\subsection{Compared approaches}\label{sec:variants}
\textbf{Proposed pair.} The selector--imputer pair of Section~\ref{sec:impl}, selected on the development partition as the best-scoring configuration. The sealed evaluation presumably ran this pair or its latent-skill extension (below), which have identical development scores; no artifact records which source tree was evaluated, so this identity is not established. Statements about the ``evaluated pair'' therefore refer to this selector--imputer family. \textbf{Variant under search.} A simpler pair: z-scored columns, EM Gaussian, covariance-trace greedy selection with a coverage weighting, and the ridge-regularised Gaussian conditional mean, with shrinkage, factor rank and ridge strength tuned by history cross-validation. A third pair adds a monotone-link latent-skill member to the stack and a latent A-optimal selector candidate. The proposed pair and the simpler pair differ in several components at once (transform, selector candidates, stack, clipping), so their comparison (Table~\ref{tab:search}) is a comparison of configurations, not an ablation. \textbf{Evaluator baselines.} (a) \emph{Column mean}: predict each benchmark's history mean. (b) \emph{Random-$k$ ridge}: five random $k$-subsets (seeded from the dataset, $k$ and draw index), ridge imputer fitted on a rank-5 SVD-completed history (40 completion iterations), ridge strength chosen by leave-one-out over four values; the mean $\nrmse$ over draws is the baseline. (c) \emph{Greedy-forward ridge}: forward selection (up to 20 benchmarks) minimising leave-one-out ridge error on the remaining benchmarks of the completed history, with the same ridge imputer. Both ridge baselines share their imputer, so they probe selection with the imputer fixed; the proposed pair changes both selector and imputer.

\subsection{Selector and imputer}\label{sec:impl}
The constants and routines below are read from the proposed-pair source copy; the identity of the sealed-evaluated source tree is not established (presumably this pair or its latent-skill extension, Section~\ref{sec:variants}).

\paragraph{Representation and EM.} Two representations of the history are built: z-scoring (clipped at $\pm8$) and an empirical rank-Gauss map $\Phi^{-1}\big((r-\tfrac12)/n\big)$ per benchmark (average ranks; benchmarks with fewer than eight observations or four distinct values fall back to z-scores). For each, EM fits $\mathcal{N}(\mu,\Sigma)$ with missing entries, applying diagonal shrinkage $\Sigma\leftarrow(1-\epsilon)\Sigma+\epsilon\,\mathrm{diag}(\Sigma)$ ($\epsilon=0.02$) in each M-step (at most 60 iterations, tolerance $10^{-4}$, 25-s budget).

\paragraph{Selection.} Candidate subsets come from (i) covariance-trace greedy A-optimal selection: with $R$ the current posterior covariance, add $j$ maximising $\sum_{i\in U,i\ne j}R_{ij}^2/(R_{jj}+\lambda)$, then update $R\leftarrow R-R_{\cdot j}R_{j\cdot}/(R_{jj}+\lambda)$; and (ii) a greedy forward \emph{wrapper} that adds the benchmark minimising five-fold held-out-model squared error of the conditional-Gaussian predictor, with all candidates scored by batched matrix products and an optional coverage weighting (benchmarks missing for many history models are less informative). For each representation and candidate rule, the subset with the lowest history cross-validation error in raw benchmark units is chosen (up to 250 candidates per step).

\paragraph{Imputation.} For a new model, the Gaussian conditional mean $\mu+\Sigma_{\cdot S}(\Sigma_{SS}+\lambda I)^{-1}(y_S-\mu_S)$ conditions only on the selected benchmarks that model actually has. Shrinkage, factor rank and $\lambda$ are tuned by five-fold history cross-validation. The stack uses, per target benchmark, non-negative weights over six base predictors (three Gaussian conditional means at shrinkage 0, 0.15 and 0.3, ridge on the selected benchmarks, and kNN with 5 and 15 neighbours) plus an implicit column-median term, fitted on out-of-fold history predictions and regularised toward a pooled weight vector; a regularisation strength is chosen from six values by cross-validation. Outputs are mapped back to raw units, clipped to the history range, and replaced by the observed value for selected benchmarks; a model with no selected score receives the column median.

\paragraph{Cost and applicability.} All components are CPU-only NumPy. Fitting plus selection for one $(\text{dataset},k)$ episode is dominated by EM and cross-validation; the sealed evaluation of 14 episodes per seed took about 157--161 seconds per seed. The method presumes a history matrix with enough coverage per benchmark and a new model whose scores are exchangeable with history models after transformation, which family-disjoint evaluation tests but does not guarantee. In the proposed-pair source copy, which is not verified as the sealed-evaluated tree, wall-clock guards skip optional selector candidates after 70 s, fall back to a smaller tuning grid after 150 s, and skip stacking (leaving the Gaussian-only model) after 210 s; the timing above is a property of the sealed run and may not transfer to that copy.

\subsection{Experimental protocol}\label{sec:protocol}
\paragraph{Data.} Sealed evaluation uses three public leaderboards at pinned revisions: MTEB results (297 benchmark columns; 124 history and 37 held-out models), the Open LLM Leaderboard table (six benchmarks, namely IFEval \citep{Zhou2023IFEval}, BBH \citep{Suzgun2023BBH}, MATH Level~5 \citep{Hendrycks2021MATH}, GPQA \citep{Rein2023GPQA}, MuSR \citep{Sprague2023MuSR} and MMLU-Pro \citep{Wang2024MMLUPro}; 3371 history and 300 held-out models, the held-out set capped at 300), and HELM Lite v1.13.0 core scenarios (ten scenarios; 66 history and 25 held-out models). Models are grouped by normalised name, family key and content hash (union-find); groups, never single models, are assigned to history or held-out, so no family or duplicated record appears on both sides. Held-out groups are drawn in hash order until at least a quarter of rows are held out. A separate MTEB partition with disjoint groups was used for model development (Section~\ref{sec:search}).

\paragraph{Episodes.} Each seed runs 14 episodes: MTEB at $k\in\{2,5,10,20\}$; Open LLM Leaderboard at $k\in\{1,2,3\}$; HELM Lite at $k\in\{2,3,5\}$; plus evaluator-owned controls. In a \emph{permuted} control, held-out models' observed values on the selected benchmarks are cyclically reassigned to other held-out models (MTEB $k{=}10$, Open LLM $k{=}2$, HELM $k{=}3$); in a \emph{constant} control the observations are replaced by column means (MTEB $k{=}10$). Controls separate genuine cross-model information from the imputer's marginal prior. The seeds (201, 202, 203) reach only the candidate's random state; the held-out sets, baselines and controls are fixed by hashing.

\paragraph{Why this protocol answers the question.} Four design decisions tie the measurement to the research question. (i) Family-disjoint held-out models make the new model genuinely new: if siblings of a held-out model were in the history, a nearest-neighbour effect could masquerade as cross-benchmark structure. (ii) Committing to $S$ before any new-model score is observed matches the budgeted setting in which the evaluator cannot adapt the run list, and it prevents the selector from peeking at the targets. (iii) Equal weight per held-out model, and errors in units of each benchmark's history spread, stop benchmarks with large numeric ranges or models with many observed cells from dominating the metric. (iv) Evaluator-owned baselines and permutation controls keep the comparison objects outside the control of the method: the method cannot tune its own competitors. The remaining weakness is that the held-out set is fixed, which we return to in Section~\ref{sec:limits}.

\paragraph{Aggregation.} Within a leaderboard, values are averaged over seeds, then over its $k$ grid with equal weights; the pooled metric averages the three leaderboards with weight $1/3$ each. The permuted-control gap is the control $\nrmse$ minus the matched real-episode $\nrmse$, averaged over seeds and then over leaderboards. A run counts as valid only if all episodes complete with finite predictions, real episodes beat their controls, and pooled skill against column mean and random-$k$ ridge is positive. The sealed evaluation finished with outcome \emph{qualified}. This statement concerns the evaluated setting; no further qualification diagnostics were retained.

\section{Results}\label{sec:results}

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/main_results.pdf}
\caption{Sealed evaluation on family-disjoint held-out models. (a) MTEB $\nrmse$ against budget $k$ (mean over three seeds). (b) $\nrmse$ per leaderboard (OLL: Open LLM Leaderboard) and pooled over the three. (c) Skill against column-mean, greedy-forward ridge and random-$k$ ridge baselines, pooled over leaderboards. No error bars: the retained metrics are seed means, and the three seeds share the same held-out models.}
\label{fig:main}
\end{figure}

\subsection{Main results}
Pooled over the three leaderboards, the evaluated pair reaches $\nrmse=0.562$ and a skill of 0.434 against column-mean imputation, that is, a mean relative error reduction of 43.4\% (Table~\ref{tab:final}). 
The three per-seed pooled skills are 0.433, 0.427 and 0.433, so the stochasticity of the method's own cross-validation folds moves the headline by less than 0.006. 
This supports H1 in the evaluated setting. Because all three seeds use identical held-out models, this spread does not measure how the result would change with different held-out models, and we report no confidence interval for the pooled values.

\begin{table}[t]
\centering
\caption{Sealed final metrics of the evaluated selector--imputer pair (mean over seeds 201--203; hierarchy described in Section~\ref{sec:protocol}). Lower $\nrmse$ is better; skill is relative error reduction against the named baseline.}
\label{tab:final}
\small
\begin{tabular}{lcl}
\toprule
Metric & Value & Meaning\\
\midrule
Pooled $\nrmse$ & 0.562 & mean over 3 leaderboards\\
\quad MTEB / HELM / Open LLM & 0.703 / 0.501 / 0.482 & per leaderboard\\
\quad MTEB $k{=}2/5/10/20$ & 0.787/0.722/0.664/0.638 & error vs.\ budget\\
Skill vs.\ column mean & 0.434 & H1\\
Skill vs.\ greedy-forward ridge & 0.099 & selector+imputer jointly\\
Skill vs.\ random-$k$ ridge & 0.016 & selector+imputer jointly\\
Permuted-control gap (nRMSE) & 0.678 & control minus real\\
\bottomrule
\end{tabular}

\end{table}

\subsection{Error against the budget $k$}
On MTEB, $\nrmse$ falls monotonically from 0.787 at $k{=}2$ to 0.722 at $k{=}5$, 0.664 at $k{=}10$ and 0.638 at $k{=}20$ (Figure~\ref{fig:main}a). 
The mean reduction per additional benchmark shrinks from about 0.022 between $k{=}2$ and $5$, to 0.012 between 5 and 10, to 0.003 between 10 and 20 (differences of the four tabulated means divided by the number of added benchmarks). This supports the diminishing-returns part of H2 on MTEB, with four budgets and no uncertainty estimate for each point. Even at $k{=}20$, i.e.\ about 7\% of the 297 columns, the typical per-cell error is still about 0.64 history standard deviations. We cannot say what $k$ is ``enough'': that depends on an error tolerance we did not define, and the curve has no baseline at each $k$ (the retained metrics report baseline skill only pooled over budgets). The curve is measured for one leaderboard; the Open LLM Leaderboard and HELM Lite grids ($k\le3$ of 6 and $k\le5$ of 10) were not retained as per-$k$ curves.

\subsection{Baselines and controls}
\paragraph{Control.} The permuted-observation control raises $\nrmse$ by 0.678 on average over the matched real episodes (Table~\ref{tab:final}). 
Hence the predictions depend on the new model's own scores on the selected benchmarks rather than on a marginal prior alone. The gap is an absolute $\nrmse$ difference and should be read against the pooled error of 0.562.

\paragraph{Selection versus imputation.} Skill against random-$k$ ridge is only 0.016: at the pooled level the proposed pair has a mean relative error 1.6\% lower than five random subsets imputed by a ridge model on a completed history. Skill against greedy-forward ridge is 0.099. 
Both figures mix selector and imputer, so neither isolates ``which $k$''. The two baselines share an imputer and differ only in selection; since skill against greedy ridge exceeds skill against random-$k$ ridge by 0.083, the averaged skills suggest, but cannot confirm because per-baseline errors were not retained, that the greedy-forward ridge baseline was no better than the random-$k$ ridge baseline. This indicative inference is the only retained evidence about selection alone, and it does not establish that a leave-one-out greedy selector is worse than random subsets under a fixed ridge imputer. For H3 the grounded conclusion is therefore modest. The pair's accuracy over a ridge imputer does not separate into a selector effect and an imputer effect, and the small margin over random-$k$ suggests that on these leaderboards most of the achievable gain over column means is available with a reasonable imputer and an arbitrary subset.

\subsection{Difficulty across leaderboards}
$\nrmse$ is 0.703 on MTEB, 0.501 on HELM Lite and 0.482 on the Open LLM Leaderboard (Figure~\ref{fig:main}b), so H4 holds in the sense that error differs. It is not a clean difficulty ranking: the leaderboards differ in the number of benchmarks (297, 10, 6), history size (124, 66, 3371 models), $k$ grids, and what $k$ means as a fraction of the columns. MTEB lists embedding models over many task types, which is also a different object from generative language models; none of the three results transfers to the others. 

\subsection{Reading the metrics: sensitivity and failure analysis}
\paragraph{Skill is a mean of ratios.} Each skill value is computed per episode and then averaged along the hierarchy of Section~\ref{sec:protocol}, and is clipped to $[-1,1]$. It is therefore not equal to one minus the ratio of pooled errors. If it were, the two ridge-baseline skills would imply that the greedy-forward baseline has an error about $(1-0.016)/(1-0.099)\approx 1.09$ times that of the random-$k$ baseline. We read this only as indicative of the sign and rough size of the effect. 
\paragraph{Where the pair could fail.} Three mechanisms can degrade the predictions without being visible in the pooled numbers: (a) benchmarks with few history observations fall back to z-scores or to coarse medians, and the clipped outputs cannot extrapolate beyond the history range, so a new model that outperforms every history model on a benchmark is necessarily under-predicted on that benchmark; (b) selected benchmarks that a new model has not been run on contribute nothing, and the pair then falls back to a prior that conditions on fewer scores (a model with none of the selected scores receives column medians); (c) the wall-clock guards switch off the stack or optional candidates on slow hardware. We did not construct stress tests for (a)--(c), so we cannot report how often or by how much they matter.
\paragraph{What a different outcome would have looked like.} A permuted-control gap near zero would have meant that the predictions were driven by the marginal prior; a negative skill against column means would have refuted H1; a flat MTEB curve would have refuted H2. The first two did not occur and the third is contradicted by the monotone curve, so the study could have refuted them. By contrast, H3 and H4 are not tested sharply: the sealed metrics do not isolate selection, and the leaderboards are not matched in size.

\subsection{Configuration comparison on the model-development partition}\label{sec:search}
During development, three configurations were scored on a separate MTEB partition (disjoint groups, 280 columns, 131 history and 32 held-out models) with two seeds and $k\in\{2,5,10,20\}$. Table~\ref{tab:search} keeps these numbers apart from the sealed ones; $\nrmse$ values are not comparable across the two partitions.


\begin{table}[t]
\centering
\caption{Development-partition comparison (MTEB, two seeds). Score is the mean skill against column mean. The seed columns give the two per-seed scores.}
\label{tab:search}
\small
\begin{tabular}{lccccc}
\toprule
Configuration & Score & Seeds 11/12 & $\nrmse$ & vs.\ random-$k$ & Perm.\ gap\\
\midrule
Simple pair (trace + cond.\ mean) & 0.220 & 0.220 / 0.220 & 1.067 & 0.100 & 0.522\\
Proposed pair (wrapper + stack) & 0.247 & 0.243 / 0.251 & 1.028 & 0.132 & 0.568\\
Proposed + latent-skill member & 0.247 & 0.243 / 0.251 & 1.028 & 0.132 & 0.568\\
\bottomrule
\end{tabular}
\end{table}

The proposed pair scores 0.247 against 0.220 for the simple pair, with non-overlapping per-seed ranges (0.243--0.251 vs.

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}

\subsection{Evaluation protocol details}
Table~\ref{tab:data} lists the data partitions used by the sealed evaluation, taken from the evaluator's dataset manifests. 
Group counts are numbers of family groups after union-find merging. The model-development partition (MTEB, 280 columns, 131 history models, 32 held-out models, revision identical to the sealed MTEB revision) uses a disjoint set of groups. 

\begin{table}[h]
\centering
\caption{Sealed evaluation partitions.}
\label{tab:data}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lcccccc}
\toprule
Leaderboard & Revision & Cols. & History & Held-out & Groups (h/o) & $k$ grid\\
\midrule
MTEB results & 6dabbcc & 297 & 124 & 37 & 92 / 25 & 2, 5, 10, 20\\
Open LLM Leaderboard & 9c09a7c & 6 & 3371 & 300 & 2314 / 266 & 1, 2, 3\\
HELM Lite & v1.13.0 & 10 & 66 & 25 & 16 / 7 & 2, 3, 5\\
\bottomrule
\end{tabular}
\end{table}

\noindent Score definitions: MTEB uses each task's main score averaged over the entries of the first available split (test, validation, dev, train), taken from the model revision directory with the most task files; Open LLM Leaderboard uses raw scores of IFEval, BBH, MATH Level 5, GPQA, MUSR and MMLU-PRO, dropping rows with a missing score; HELM Lite uses the ten scenario columns of the core-scenarios table, excluding the mean-win-rate column. Held-out MTEB and HELM Lite models may lack some scores; those cells are not scored. Per-seed pooled scores of the sealed evaluation were 0.4330 (seed 201), 0.4273 (202) and 0.4328 (203), taking 157.4, 160.6 and 161.0 seconds for 14 episodes each. 

\subsection{Method specification and hyperparameters}
Table~\ref{tab:hyper} collects the constants of the pair described in Section~\ref{sec:impl}; they are read from the entry-point source of the proposed-pair source copy (\texttt{src/program.py}: the EM, greedy-selection, wrapper-selection, stacking and prediction routines). This copy is not verified to be the exact tree evaluated in the sealed run (see below), so the constants describe the proposed pair, not a confirmed record of the sealed configuration. 

\begin{table}[h]
\centering
\caption{Constants of the proposed pair, read from its source copy (not verified as the exact sealed-evaluated tree).}
\label{tab:hyper}
\small
\begin{tabular}{lp{0.5\textwidth}}
\toprule
Component & Setting\\
\midrule
EM & shrinkage 0.02, $\le 60$ iterations, tol.\ $10^{-4}$, jitter $10^{-4}$, 25-s budget\\
Cross-validation & 5 folds over history models\\
Covariance shrinkage grid & 0, 0.05, 0.15, 0.3\\
Factor-rank grid & 2, 4, 6, 10, full\\
Ridge $\lambda$ grid (Gaussian conditional mean) & 0.003, 0.03, 0.1, 0.3\\
Selection candidates & 4 trace-greedy settings, 2 wrapper settings (coverage exponent 0 or 1)\\
Wrapper & $\lambda=0.1$, shrinkage 0.05, $\le 250$ candidates per step\\
Stack base predictors & Gaussian conditional means (shrink 0, 0.15, 0.3), ridge ($\lambda=5$), kNN (5, 15)\\
Stack regularisation grid & 0, 0.05, 0.25, 1, 5, $10^{5}$\\
Clipping & z-scores at $\pm 8$; outputs to the history range\\
Wall-clock guards & skip optional candidates 70 s; smaller tuning grid 150 s; skip stacking 210 s\\
\bottomrule
\end{tabular}
\end{table}

\noindent The latent-skill extension (third row of Table~\ref{tab:search}) adds a low-rank model $T_{ij}\approx g_j(u_i\cdot v_j+b_j)$ with a monotone piecewise-linear link $g_j$ per benchmark, Huber-likelihood MAP inference of a new model's latent vector with a Laplace covariance, an additional stack member retained only if cross-validation improves, and a latent A-optimal selector candidate. Its metrics equal those of the proposed pair (Table~\ref{tab:search}); the extension took roughly 331--334 seconds per search seed against 141--142 seconds for the proposed pair. 
The longer run time indicates that the extra code ran, but its influence on outputs is not established. The final-evaluation record lists a hash of the evaluated source tree; no hash-comparison artifact is available, so the identity of the evaluated tree is not established, and the tie above means the retained scores cannot discriminate the two. The main text describes the shared stack, and the extension is described here because the sealed run may have used it. The simple pair used 95--97 seconds per search seed. 

\subsection{Extra evidence tables}
\begin{table}[h]
\centering
\caption{Development-partition per-seed scores and durations (seconds, two seeds each).}
\label{tab:seeds}
\small
\begin{tabular}{lcccc}
\toprule
Configuration & Score (seed 11) & Score (seed 12) & Time (seed 11) & Time (seed 12)\\
\midrule
Simple pair & 0.2201 & 0.2197 & 95.4 & 97.3\\
Proposed pair & 0.2429 & 0.2506 & 140.9 & 142.2\\
Proposed + latent member & 0.2429 & 0.2506 & 331.2 & 334.3\\
\bottomrule
\end{tabular}

\end{table}

\subsection{Unperformed analyses}
The following were not run and are not claimed: component ablations (the ablation directory of the run is missing); empirical verification of the trace objective as expected error; bootstrap or model-resampling intervals; per-leaderboard $k$ curves for Open LLM Leaderboard and HELM Lite as retained metrics; baseline $\nrmse$ values per budget; additional leaderboards such as LiveBench, BigCodeBench or AlpacaEval, which the task description lists as optional.

\subsection{Reproducibility and data sources}
Entry point: a single Python file exposing a \texttt{handle} request function (operations \texttt{reset}, \texttt{load\_history}, \texttt{select}, \texttt{predict}); dependencies are NumPy only; behaviour is deterministic given the seed except for the wall-clock guards. Figures and tables in this paper come from \texttt{scripts/build\_figures.py} (Figure~\ref{fig:main}), \texttt{scripts/extract\_protocol\_facts.py} (Table~\ref{tab:data}), \texttt{scripts/extract\_search\_metrics.py} (Tables~\ref{tab:search} and~\ref{tab:seeds}); the sealed metrics are read from the evaluation registry. The data come from the public upstream sources and pinned revisions listed in Table~\ref{tab:data}; licence terms of these sources were not verified in this study. Literature retrieval used only titles from the starter literature and standard methodology references; no material from the excluded publication was knowingly accessed.

\subsection{LLM Usage}
Large language models were used for research hypothesis generation, for implementing and running the compared configurations, and for drafting and editing this manuscript. The selector--imputer designs, code, experiments and the text were produced by an automated LLM-driven research workflow, with evaluator-owned scoring that the workflow could not modify. All reported numbers were read from evaluator outputs and checked against the evidence registry; the human role was limited to specifying the task and evaluation setting. References were retrieved from bibliographic databases and checked against their records.
```
