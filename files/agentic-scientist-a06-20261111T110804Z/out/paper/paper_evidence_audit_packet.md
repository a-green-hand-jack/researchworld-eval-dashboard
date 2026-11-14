# Agentic evidence audit packet

- generated_at: `2026-11-11T15:07:34.421362+00:00`
- paper_dir: `work/results/a06/claude/20261111_111240/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261111_142659-paper_evidence_audit_round_4-yy032bkg/workspace`

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
    "anchored_references": 50,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 120,
    "resolved_references": 90,
    "total_references": 140
  },
  "ok": true,
  "pdf_path": "work/results/a06/claude/20261111_111240/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 50,
    "dangling_references": 0,
    "manifests_checked": 13,
    "resolved_references": 90,
    "total_references": 140
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "claim": "Sealed final evaluation: mean 90%-level interval score of EB-IRT is 0.1449 (primary cases P1-P6, 0.4 synthetic/0.6 real).",
      "source_ids": [
        "final.metric.mean_interval_score",
        "final.metric.combined_score"
      ]
    },
    {
      "claim": "Baseline interval scores in the sealed evaluation: naive Wilson 0.2202, Bonferroni-Wilson 0.1974, resampling 0.2461.",
      "source_ids": [
        "final.metric.naive_baseline_score",
        "final.metric.bonferroni_baseline_score",
        "final.metric.resample_baseline_score"
      ]
    },
    {
      "claim": "EB-IRT aggregate coverage 0.929, mean width 0.129, RMSE 0.0348, signed bias 0.0121.",
      "source_ids": [
        "final.metric.coverage",
        "final.metric.mean_width",
        "final.metric.rmse",
        "final.metric.signed_bias"
      ]
    },
    {
      "claim": "Naive aggregate signed bias is 0.0366, i.e. the naive estimate exceeds fresh-question accuracy by about 0.037; EB-IRT removes about two thirds (0.0121).",
      "source_ids": [
        "final.metric.naive_signed_bias",
        "final.metric.signed_bias"
      ]
    },
    {
      "claim": "Evaluator qualification outcome is 'qualified' with status 'completed'; all replications completed (fraction 1.0).",
      "source_ids": [
        "final.qualification.outcome",
        "final.qualification.status",
        "final.qualification.correct",
        "final.metric.completed_replication_fraction"
      ]
    },
    {
      "claim": "Null-control absolute bias 0.0173 and constant-world error 0; null-control coverage averaged over N1 and N2 is 0.929 (N1 0.971, N2 0.887).",
      "source_ids": [
        "final.metric.null_control_abs_bias",
        "final.metric.constant_control_error",
        "final.metric.null_control_coverage",
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Seed-level spread over eight seeds: EB-IRT interval score sd 0.0040, naive 0.0234, Bonferroni 0.0036, resampling 0.0251; EB-IRT lower than each baseline in all eight seeds with paired differences 0.075, 0.053, 0.101.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Replay-derived (not evaluator-recorded) baseline diagnostics: naive Wilson coverage 0.713 (sd 0.048) and width 0.109; Bonferroni-Wilson coverage 0.962, width 0.190; resampling coverage 0.748, width 0.104 (aggregate over P1-P6). The evaluator records only baseline interval scores and the naive bias; the replay reproduced those recorded values exactly (max abs difference 0), and the other replayed quantities are unchecked against any record.",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.naive_baseline_score"
      ]
    },
    {
      "claim": "Naive bias on real exhaustive cases falls with N: 0.051 (N=60), 0.022 (N=200), 0.009 (N=600).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Final-pool configuration accuracies range from 0.107 to 0.166 (task manifest); naive optimism at N=60 (0.051) is of the same order as the spread of configuration pool accuracies (0.107 to 0.166); no inference about reported advantage over alternatives.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Naive bias in null worlds: 0.067 in N1 vs 0.049 in P1; 0.034 in N2 vs 0.022 in P3.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Searcher effect on naive bias: P2 0.054, P4 0.025 vs P1 0.049, P3 0.022; matched paired differences +0.004 (sd 0.012) and +0.003 (sd 0.008); aggregated naive bias 0.036 for both searchers.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Per-case EB-IRT vs naive interval scores: P1 0.150 vs 0.264, P2 0.155 vs 0.300, P5 0.192 vs 0.303; reductions of 37-48%; coverage 0.96, 0.96, 0.98.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "P4: EB-IRT 0.156 vs naive 0.161 and Bonferroni 0.165; wins in six of eight seeds; bias 0.031 vs 0.025; coverage 0.89 (slightly below nominal, within about one standard error over eight seeds; seed sd about 0.03). P6: all Wilson-style reporters 0.096; coverage 0.83 (seed sd 0.05), clearly below nominal.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Exhaustive-search restricted aggregate: EB-IRT 0.1406, resampling 0.1405, naive 0.2166; halving cases: resampling 0.3916 vs EB-IRT 0.1556.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Resampling is slightly better than EB-IRT in P3 (0.109 vs 0.116), P5 (0.174 vs 0.192) and N2 (0.102 vs 0.111); EB-IRT better in 2, 1 and 1 of 8 seeds.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Replay-derived (resampling bias and coverage are not evaluator-recorded; replay reproduced the recorded baseline interval scores and naive bias exactly): resampling over-corrects under halving with bias -0.067 (P2) and -0.031 (P4), and coverage 0.44 and 0.61; aggregate resampling bias -0.0209.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "EB-IRT signed bias positive in five of six primary cases (0.009-0.031) and -0.002 (sd 0.010) in P1.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Interval widths at N=60/200/600: EB-IRT 0.187/0.101/0.065, naive 0.167/0.088/0.050, Bonferroni-Wilson 0.284/0.153/0.088.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Controls: N1 EB-IRT coverage 0.971, interval score 0.128 vs naive 0.354 (naive coverage 0.47); N2 EB-IRT coverage 0.887, score 0.111 vs naive 0.218 and resampling 0.102; Z1 interval [0,0.02], score 0.020 vs naive 0.026 and Bonferroni 0.059.",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.constant_control_error"
      ]
    },
    {
      "claim": "Width factor kappa ranges from 1.43 to 1.63 across the evaluated cases (computed from the reporter's own function).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Development-setting variants (4 seeds): EB-IRT interval score 0.1480, coverage 0.915, width 0.124; config-by-subject variant 0.1519, coverage 0.893; bootstrap pivot variant 0.1562, coverage 0.77, width 0.085; baselines 0.2321 (naive), 0.1961 (Bonferroni), 0.2732 (resampling).",
      "source_ids": [
        "result.top_program_01",
        "result.top_program_02",
        "result.top_program_03",
        "result.total_evaluated_programs"
      ]
    },
    {
      "claim": "Three reporter variants were evaluated once each in the development setting; all three were scored.",
      "source_ids": [
        "result.total_attempts",
        "result.total_evaluated_programs",
        "result.total_correct_programs"
      ]
    },
    {
      "claim": "Evaluator-recorded wall-clock time averaged 6.2 s per seed (250 episodes, reporter calls plus scoring), about 50 s over the eight sealed seeds; 2000 episodes in total.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Gneiting2007Scoring"
      ],
      "claim": "Interval score is a proper scoring rule minimized by the 5% and 95% predictive quantiles.",
      "source_ids": [
        "final.metric.mean_interval_score"
      ]
    },
    {
      "citation_keys": [
        "Dwork2014PreservingSV",
        "Dwork2015GeneralizationIA",
        "Dwork2015TheRH",
        "Feldman2017CalibratingNT",
        "Hardt2014Hard",
        "Blum2015Ladder",
        "Berk2013ValidPSI",
        "Andrews2024InferenceOnWinners",
        "Chernozhukov2013Gaussian",
        "Efron1973Stein",
        "Efron2011Tweedie",
        "Efron1997Bootstrap632",
        "Recht2019ImageNet",
        "Khattab2023DSPy",
        "OpsahlOng2024MIPRO",
        "Shi2024PromptBAI",
        "Jamieson2016SuccessiveHalving",
        "Sclar2023Quantifying",
        "Polo2024EfficientMultiPrompt",
        "Miller2024ErrorBars",
        "Wilson1927Probable",
        "Wang2024MMLUPro",
        "Qwen2024Qwen25",
        "Cawley2010Overfitting",
        "Feldman2019MultipleClasses",
        "Zhou2022APE",
        "Yang2023OPRO",
        "Bock1981MML",
        "MartinezPlumed2019IRTinAI"
      ],
      "claim": "Related work: adaptive data analysis, reusable holdout, Ladder, post-selection inference, inference on winners, empirical Bayes, bootstrap optimism, prompt search and LLM evaluation (qualitative).",
      "source_ids": [
        "final.qualification.status"
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
  "campaign_results_dir": "work/results/a06/claude/20261111_111240/investigation",
  "count": 30,
  "generated_at": "2026-11-11T14:27:34.157126+00:00",
  "queries": [
    "winner's curse selection bias reported score after selecting best configuration among many",
    "adaptive data analysis statistical validity reuse of holdout",
    "Ladder mechanism reliable leaderboard adaptive submissions",
    "inference on winners selected parameter confidence intervals",
    "valid post-selection inference confidence intervals",
    "empirical Bayes shrinkage for selected maximum item response theory LLM benchmark evaluation",
    "item response theory efficient LLM evaluation question difficulty",
    "prompt optimization best arm identification successive halving limited evaluation budget",
    "automatic prompt and pipeline optimization DSPy MIPRO few-shot instruction search",
    "multi-prompt evaluation performance distribution across prompt templates sensitivity"
  ],
  "reference_query_plan": {
    "architectural_shifts": [
      "from per-config binomial/Wilson score to hierarchical latent-difficulty IRT posterior using all logged (question, config, outcome) triples",
      "from 1-D difficulty to config-by-subject interaction (did not beat the simpler variant)",
      "from analytic posterior to parametric-bootstrap pivot calibration (under-covered: 0.77)"
    ],
    "benchmarks": [
      "MMLU-Pro (replayed outcomes, 24 configs, subject codes)",
      "synthetic latent-difficulty worlds (varying N questions, K configs; equal-config null worlds)"
    ],
    "central_topic": "Quantifying and correcting the winner's-curse bias of reporting the best searched LLM prompt/pipeline configuration's score on the same benchmark questions used to select it, via searcher-agnostic debiased interval reporting evaluated on synthetic worlds and replayed MMLU-Pro outcomes.",
    "comparators": [
      "adaptive data analysis / holdout reuse",
      "Ladder leaderboard mechanism",
      "inference on winners and post-selection inference",
      "best-arm-identification / successive-halving prompt selection",
      "DSPy/MIPRO auto-tuners",
      "efficient multi-prompt evaluation and prompt-format sensitivity"
    ],
    "core_methods": [
      "empirical-Bayes hierarchical logistic item-response (latent difficulty) posterior-quantile interval",
      "parametric-bootstrap pivot calibration of the EB-IRT interval",
      "config-by-subject interaction random effects",
      "naive Wilson interval, Bonferroni and question-resampling reporting baselines"
    ],
    "forbidden_query_patterns": [
      "generic 'hyperparameter optimization' or 'AutoML survey' queries",
      "generic 'benchmarking LLMs' or 'scientific method' queries",
      "queries naming campaign order, cycles, attempts or search history",
      "any attempt to locate the withheld published paper on this exact research question, its title, authors, mirrors, or papers citing/discussing it",
      "queries on LLM-agent paper-writing or research automation"
    ],
    "queries": [
      {
        "category": "core_method",
        "query": "winner's curse selection bias reported score after selecting best configuration among many",
        "rationale": "Central problem: the best-of-K searched config scored on the same questions is upward biased (naive signed bias +0.037 in the run)."
      },
      {
        "category": "baseline_comparator",
        "query": "adaptive data analysis statistical validity reuse of holdout",
        "rationale": "Adaptive reuse of one question set for selection and scoring; grounds the validity argument (Dwork et al. line)."
      },
      {
        "category": "baseline_comparator",
        "query": "Ladder mechanism reliable leaderboard adaptive submissions",
        "rationale": "Reporting-mechanism comparator for repeated adaptive evaluation on a shared test set."
      },
      {
        "category": "baseline_comparator",
        "query": "inference on winners selected parameter confidence intervals",
        "rationale": "Econometric post-selection inference for selected best candidates; the run's Bonferroni/resample baselines belong to this neighborhood."
      },
      {
        "category": "baseline_comparator",
        "query": "valid post-selection inference confidence intervals",
        "rationale": "Classical post-selection inference literature; context for simultaneous/Bonferroni-style intervals compared against."
      },
      {
        "category": "core_method",
        "query": "empirical Bayes shrinkage for selected maximum item response theory LLM benchmark evaluation",
        "rationale": "Run's best method is an empirical-Bayes hierarchical logistic IRT posterior interval (a_config - b_question, Laplace draws, quantile intervals); needs IRT and shrinkage references."
      },
      {
        "category": "architectural_shift",
        "query": "item response theory efficient LLM evaluation question difficulty",
        "rationale": "Representation shift from per-config binomial/Wilson score to latent-difficulty IRT model of (question, config) outcomes; IRT for LLM benchmarks."
      },
      {
        "category": "benchmark_context",
        "query": "prompt optimization best arm identification successive halving limited evaluation budget",
        "rationale": "Searchers in the evaluation (exhaustive and successive halving, sparse outcome logs) are the prompt-selection setting; selection via observed outcomes is ignorable for the likelihood."
      },
      {
        "category": "benchmark_context",
        "query": "automatic prompt and pipeline optimization DSPy MIPRO few-shot instruction search",
        "rationale": "Auto-tuning tools whose reported best-config scores motivate the problem."
      },
      {
        "category": "result_driven_theme",
        "query": "multi-prompt evaluation performance distribution across prompt templates sensitivity",
        "rationale": "Config-to-config variability across prompts/formats determines tau and the size of selection bias; Polo/Sclar neighborhood."
      }
    ],
    "result_driven_themes": [
      "naive reporting is upward biased (signed bias ~0.037) and under-covers; EB-IRT cuts bias to ~0.014 and interval score from -0.232 to -0.148 at ~0.915 coverage",
      "Bonferroni is valid but wide (-0.196); resampling worst (-0.273)",
      "bootstrap pivot calibration under-covers (0.77) and interaction model did not improve on the simple EB-IRT",
      "selection is ignorable for likelihood under searchers that use only observed outcomes"
    ],
    "status": "ready"
  },
  "reference_query_plans": [
    {
      "architectural_shifts": [
        "from per-config binomial/Wilson score to hierarchical latent-difficulty IRT posterior using all logged (question, config, outcome) triples",
        "from 1-D difficulty to config-by-subject interaction (did not beat the simpler variant)",
        "from analytic posterior to parametric-bootstrap pivot calibration (under-covered: 0.77)"
      ],
      "benchmarks": [
        "MMLU-Pro (replayed outcomes, 24 configs, subject codes)",
        "synthetic latent-difficulty worlds (varying N questions, K configs; equal-config null worlds)"
      ],
      "central_topic": "Quantifying and correcting the winner's-curse bias of reporting the best searched LLM prompt/pipeline configuration's score on the same benchmark questions used to select it, via searcher-agnostic debiased interval reporting evaluated on synthetic worlds and replayed MMLU-Pro outcomes.",
      "comparators": [
        "adaptive data analysis / holdout reuse",
        "Ladder leaderboard mechanism",
        "inference on winners and post-selection inference",
        "best-arm-identification / successive-halving prompt selection",
        "DSPy/MIPRO auto-tuners",
        "efficient multi-prompt evaluation and prompt-format sensitivity"
      ],
      "core_methods": [
        "empirical-Bayes hierarchical logistic item-response (latent difficulty) posterior-quantile interval",
        "parametric-bootstrap pivot calibration of the EB-IRT interval",
        "config-by-subject interaction random effects",
        "naive Wilson interval, Bonferroni and question-resampling reporting baselines"
      ],
      "forbidden_query_patterns": [
        "generic 'hyperparameter optimization' or 'AutoML survey' queries",
        "generic 'benchmarking LLMs' or 'scientific method' queries",
        "queries naming campaign order, cycles, attempts or search history",
        "any attempt to locate the withheld published paper on this exact research question, its title, authors, mirrors, or papers citing/discussing it",
        "queries on LLM-agent paper-writing or research automation"
      ],
      "queries": [
        {
          "category": "core_method",
          "query": "winner's curse selection bias reported score after selecting best configuration among many",
          "rationale": "Central problem: the best-of-K searched config scored on the same questions is upward biased (naive signed bias +0.037 in the run)."
        },
        {
          "category": "baseline_comparator",
          "query": "adaptive data analysis statistical validity reuse of holdout",
          "rationale": "Adaptive reuse of one question set for selection and scoring; grounds the validity argument (Dwork et al. line)."
        },
        {
          "category": "baseline_comparator",
          "query": "Ladder mechanism reliable leaderboard adaptive submissions",
          "rationale": "Reporting-mechanism comparator for repeated adaptive evaluation on a shared test set."
        },
        {
          "category": "baseline_comparator",
          "query": "inference on winners selected parameter confidence intervals",
          "rationale": "Econometric post-selection inference for selected best candidates; the run's Bonferroni/resample baselines belong to this neighborhood."
        },
        {
          "category": "baseline_comparator",
          "query": "valid post-selection inference confidence intervals",
          "rationale": "Classical post-selection inference literature; context for simultaneous/Bonferroni-style intervals compared against."
        },
        {
          "category": "core_method",
          "query": "empirical Bayes shrinkage for selected maximum item response theory LLM benchmark evaluation",
          "rationale": "Run's best method is an empirical-Bayes hierarchical logistic IRT posterior interval (a_config - b_question, Laplace draws, quantile intervals); needs IRT and shrinkage references."
        },
        {
          "category": "architectural_shift",
          "query": "item response theory efficient LLM evaluation question difficulty",
          "rationale": "Representation shift from per-config binomial/Wilson score to latent-difficulty IRT model of (question, config) outcomes; IRT for LLM benchmarks."
        },
        {
          "category": "benchmark_context",
          "query": "prompt optimization best arm identification successive halving limited evaluation budget",
          "rationale": "Searchers in the evaluation (exhaustive and successive halving, sparse outcome logs) are the prompt-selection setting; selection via observed outcomes is ignorable for the likelihood."
        },
        {
          "category": "benchmark_context",
          "query": "automatic prompt and pipeline optimization DSPy MIPRO few-shot instruction search",
          "rationale": "Auto-tuning tools whose reported best-config scores motivate the problem."
        },
        {
          "category": "result_driven_theme",
          "query": "multi-prompt evaluation performance distribution across prompt templates sensitivity",
          "rationale": "Config-to-config variability across prompts/formats determines tau and the size of selection bias; Polo/Sclar neighborhood."
        }
      ],
      "result_driven_themes": [
        "naive reporting is upward biased (signed bias ~0.037) and under-covers; EB-IRT cuts bias to ~0.014 and interval score from -0.232 to -0.148 at ~0.915 coverage",
        "Bonferroni is valid but wide (-0.196); resampling worst (-0.273)",
        "bootstrap pivot calibration under-covers (0.77) and interaction model did not improve on the simple EB-IRT",
        "selection is ignorable for likelihood under searchers that use only observed outcomes"
      ],
      "status": "ready"
    },
    {
      "architectural_shifts": [
        "from per-config binomial/Wilson score to hierarchical latent-difficulty IRT posterior using all logged (question, config, outcome) triples",
        "from 1-D difficulty to config-by-subject interaction (did not beat the simpler variant)",
        "from analytic posterior to parametric-bootstrap pivot calibration (under-covered: 0.77)"
      ],
      "benchmarks": [
        "MMLU-Pro (replayed outcomes, 24 configs, subject codes)",
        "synthetic latent-difficulty worlds (varying N questions, K configs; equal-config null worlds)"
      ],
      "central_topic": "Quantifying and correcting the winner's-curse bias of reporting the best searched LLM prompt/pipeline configuration's score on the same benchmark questions used to select it, via searcher-agnostic debiased interval reporting evaluated on synthetic worlds and replayed MMLU-Pro outcomes.",
      "comparators": [
        "adaptive data analysis / holdout reuse",
        "Ladder leaderboard mechanism",
        "inference on winners and post-selection inference",
        "best-arm-identification / successive-halving prompt selection",
        "DSPy/MIPRO auto-tuners",
        "efficient multi-prompt evaluation and prompt-format sensitivity"
      ],
      "core_methods": [
        "empirical-Bayes hierarchical logistic item-response (latent difficulty) posterio

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

\newcommand{\IS}{\mathrm{IS}}
\newcommand{\theHat}{\hat\theta}

\title{Reporting Scores After Prompt Search: A Selection-Aware Posterior Interval from a Hierarchical Latent-Difficulty Model}
\iclrfinalcopy
\author{The Agentic Scientist}

\begin{document}
\maketitle

\begin{abstract}
Automatic prompt and pipeline search reuses one benchmark sample both to choose a configuration and to score it, so the reported score can overstate accuracy on fresh questions.
We measure this optimism in controlled worlds with known truth---synthetic latent-difficulty worlds and cached outcomes of Qwen2.5-0.5B-Instruct on MMLU-Pro under 24 prompt configurations, searched exhaustively or by successive halving---and test a searcher-agnostic remedy.
The naive best-of-search score overstates fresh-question accuracy by 0.037 on average (about 0.05 at 60 benchmark questions), and its nominal 90\% Wilson interval contains the fresh accuracy in only 71\% of replications.
The remedy fits an empirical-Bayes hierarchical logistic latent-difficulty model to the full search log and reports posterior quantiles.
In a sealed evaluation over eight seeds it lowers the mean 90\%-level interval score to 0.145, against 0.220 (naive), 0.197 (Bonferroni-widened Wilson) and 0.246 (question resampling), with coverage 0.929; the evaluator's qualification outcome is ``qualified''.
The gain is regime-dependent: the reporter only ties the naive interval under halving on real outcomes and at 600 questions, and ties resampling under exhaustive search; in those two real-outcome cases its coverage is 0.89 (halving, within seed noise of nominal) and 0.83 (600 questions, clearly below nominal).
The evidence covers one small model, one benchmark and a hand-set width calibration, and does not test effects on ranking decisions.
\end{abstract}












\section{Introduction}
Prompt and pipeline optimizers such as DSPy and MIPRO search over instructions, demonstrations and multi-call structures on a benchmark sample \citep{Khattab2023DSPy,OpsahlOng2024MIPRO}, LLM-driven optimizers propose and rank candidate prompts by their score on a task sample \citep{Zhou2022APE,Yang2023OPRO}, and in practice the best configuration is often reported with the score it attained on the very sample used to select it. Configuration search is also cast as best-arm identification under a fixed evaluation budget \citep{Shi2024PromptBAI}. The reported number is the maximum, over many candidates, of noisy estimates, and the candidate that attains it was chosen \emph{because} its estimate was high. It is therefore a biased estimate of that candidate's accuracy on new questions, and the usual interval around it ignores the selection. This is the selection bias long documented for model selection, where the score used to pick among many candidates is an optimistic performance estimate \citep{Cawley2010Overfitting}. Whether comparisons and decisions built on such numbers are trustworthy depends on how large the gap is and on what controls it.

We ask two questions. \textbf{(Q1)} For a system whose configuration is chosen on a finite question set, how far is the reported score from its accuracy on fresh questions, what governs the gap, and does it threaten conclusions drawn from reported scores? \textbf{(Q2)} Can a better reporting rule be designed, and how should its reliability be tested?

Our answer to Q2 is a post-hoc \emph{reporter} that never touches the search: it receives only the evaluation log of (question, configuration, outcome) triples, the selected configuration and basic metadata, and returns a point estimate and a 90\% interval for the selected configuration's fresh-question accuracy. The reporter fits a hierarchical logistic latent-difficulty model with empirical-Bayes variance components (EB-IRT). Because both searchers we study choose using only observed outcomes, selection is ignorable for the likelihood, so one fitting routine serves exhaustive search and successive halving. Shrinkage of configuration effects addresses the winner's curse directly; the interval is formed from posterior quantiles, which are the optimal report under the interval score \citep{Gneiting2007Scoring}.

We test reliability with an evaluator that owns the data-generating worlds, the searchers and the truth, so that coverage and interval score are measured against known fresh-question accuracy. Worlds are synthetic latent-difficulty worlds and cached real outcomes of Qwen2.5-0.5B-Instruct \citep{Qwen2024Qwen25} on MMLU-Pro \citep{Wang2024MMLUPro} under 24 prompt configurations, plus three negative controls.

\textbf{Contributions.} (i) A quantification of the optimism of best-of-search reporting and of the coverage of its Wilson interval across question budget, world and searcher (Section~\ref{sec:gap}). (ii) A searcher-agnostic EB-IRT reporter with a reimplementable specification (Section~\ref{sec:method}). (iii) A controlled evaluation protocol with known truth, null and constant-world controls, and seed-level uncertainty, applied to four reporters in a sealed final run (Sections~\ref{sec:protocol}--\ref{sec:controls}). (iv) A candid map of where the reporter fails to improve on simpler reporters: real-outcome halving, large question budgets, and exhaustive search where question resampling is as good.

\textbf{Scope.} The worlds, searchers, baseline reporters and scoring were supplied as a fixed evaluation harness, and the real-outcome tensors were produced beforehand by the task authors; this study ran neither LLM inference nor a DSPy/MIPRO search. Claims are conditional on one 0.5B model, one benchmark, one 24-configuration prompt family and two searchers. We do not test whether the optimism changes the \emph{ranking} of systems (Section~\ref{sec:limits}).

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/overview_schematic.png}
\caption{Reporting after search. A benchmark sample of $N$ questions is used to search $K$ configurations; the search log and the selected configuration are passed to a reporter, which returns a point estimate and a 90\% interval for the selected configuration's accuracy on fresh questions. We compare the naive Wilson interval, a Bonferroni-widened interval, a question-resampling optimism correction, and the EB-IRT posterior interval, all scored against known truth.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\textbf{Adaptive data analysis.} Reusing a holdout set across adaptively chosen analyses invalidates standard inference. \citet{Dwork2014PreservingSV,Dwork2015GeneralizationIA} showed that differential-privacy-style noise preserves validity, \citet{Dwork2015TheRH} gave the reusable holdout, \citet{Feldman2017CalibratingNT} calibrated the noise to variance, and \citet{Hardt2014Hard} showed that preventing false discovery in fully interactive analysis is computationally hard. The Ladder \citep{Blum2015Ladder} reports leaderboard scores of repeated submissions through a thresholded mechanism. These methods change \emph{what is released} to the analyst. Our reporter instead leaves the search untouched and corrects the report afterwards from the log; it does not provide their worst-case guarantees, and we do not study adaptive reporting across several released scores.

\textbf{Inference after selection.} Post-selection inference constructs valid intervals for selected targets \citep{Berk2013ValidPSI}; \citet{Andrews2024InferenceOnWinners} study inference on the best-performing unit, the direct statistical analogue of a best-of-search score; and \citet{Chernozhukov2013Gaussian} give Gaussian approximations for maxima that underlie bootstrap critical values. Empirical-Bayes shrinkage \citep{Efron1973Stein} and its connection to selection bias \citep{Efron2011Tweedie} motivate our use of a hierarchical model. The bootstrap optimism correction \citep{Efron1997Bootstrap632} motivates the question-resampling baseline. In machine learning, the optimism of a score used to choose among candidates is a documented source of selection bias in model selection \citep{Cawley2010Overfitting}, and benchmark overfitting under repeated reuse has been probed empirically, on image classification by collecting a fresh test set \citep{Recht2019ImageNet} and by studying how the number of classes affects overfitting from test-set reuse \citep{Feldman2019MultipleClasses}. We study the same optimism for searched LLM configurations, with ground truth supplied by the evaluator.

\textbf{Prompt search and LLM evaluation.} DSPy \citep{Khattab2023DSPy} and MIPRO \citep{OpsahlOng2024MIPRO} automate prompt and pipeline optimization, LLM-driven optimizers generate and select instructions by their score on task examples \citep{Zhou2022APE,Yang2023OPRO}, best-arm formulations bound evaluation cost \citep{Shi2024PromptBAI}, successive halving \citep{Jamieson2016SuccessiveHalving} is a standard budget allocator, performance is sensitive to prompt formatting \citep{Sclar2023Quantifying}, multi-prompt evaluation can be made sample-efficient \citep{Polo2024EfficientMultiPrompt}, item response theory has been used to analyse machine-learning classifiers at the instance level \citep{MartinezPlumed2019IRTinAI}, and error bars on benchmark scores have been advocated \citep{Miller2024ErrorBars}. None of these works supplies a post-search score with selection-aware uncertainty. We use the Wilson interval \citep{Wilson1927Probable} for the baselines.

\section{Method}\label{sec:method}
\subsection{Problem setup and success criterion}
A system is searched over $K$ configurations on $N$ benchmark questions. A searcher produces a log $\mathcal L=\{(q_i,k_i,y_i)\}$ of question indices, configuration indices and binary outcomes, and selects $\hat k$ as a function of $\mathcal L$ only. The target is the selected configuration's accuracy $\theta_{\hat k}$ on fresh questions, which the evaluator knows. A reporter receives $\mathcal L$, $\hat k$, $N$, $K$, the searcher tag and an anonymous subject code per question, and returns $(\hat\theta,\ell,u)$ with $0\le \ell\le\hat\theta\le u\le 1$. We score the interval with the interval score at level $1-\alpha=0.90$,
\begin{equation}
\IS_\alpha(\ell,u;\theta)=(u-\ell)+\tfrac{2}{\alpha}\,(\ell-\theta)_+ + \tfrac{2}{\alpha}\,(\theta-u)_+ ,
\end{equation}
which is a proper scoring rule minimized in expectation by the $\alpha/2$ and $1-\alpha/2$ predictive quantiles \citep{Gneiting2007Scoring}. A missed replication costs $20$ per unit of miss distance, so over-narrow intervals are penalized heavily. We also report coverage, mean width, signed bias of $\hat\theta$ and RMSE. A reporter that fails on a replication receives the worst-case score $20$.

\subsection{Design rationale}
The naive reporter returns the selected configuration's observed accuracy $\hat p_{\hat k}$ with a Wilson interval. Two effects make it unreliable. First, $\hat p_{\hat k}$ is the maximum of noisy estimates, so $\mathbb E[\hat p_{\hat k}-\theta_{\hat k}]>0$ (winner's curse); the effect grows when true differences between configurations are small relative to sampling noise, as in a null world. Second, the Wilson interval treats $\hat p_{\hat k}$ as a fixed-configuration estimate and ignores selection, so it is too short for its nominal level. We expect an estimator that pools information across configurations and questions to shrink the winner's estimate toward the bulk, and a posterior over $\theta_{\hat k}$ to give an interval whose length reflects how little the log says about the selected configuration.

\subsection{EB-IRT reporter}


\textbf{Model.} With $\sigma$ the logistic function, each logged outcome follows
\begin{equation}
y_{qk}\sim\mathrm{Bernoulli}\big(\sigma(a_k-b_q)\big),\quad a_k\sim\mathcal N(0,\tau^2),\quad b_q\sim\mathcal N(m_{s(q)},s^2),
\end{equation}
This is a Rasch-type item response model with hierarchical priors, whose item parameters are classically estimated by marginal maximum likelihood with EM \citep{Bock1981MML}; our fit below instead alternates Newton sweeps over configuration and question parameters with Laplace-corrected variance updates. Here $a_k$ is a configuration effect, $b_q$ a question difficulty and $m_{s}$ the mean difficulty of subject $s$ (the question's subject code; synthetic worlds have a single code). Subject means are shrunk toward the global mean with five pseudo-questions. The fresh-question accuracy of configuration $k$ is $\theta_k=\mathbb E_b[\sigma(a_k-b)]$, where $b$ is drawn from the mixture of subjects weighted by the observed subject frequencies.

\textbf{Empirical-Bayes fit.} Using only the sparse triples, we alternate damped Newton sweeps for $(a,b)$ with variance updates $\tau^2\leftarrow\frac1K\big(\sum_k\hat a_k^2+\sum_k S_k^{-1}\big)$ and $s^2\leftarrow\frac1N\big(\sum_q(\hat b_q-m_{s(q)})^2+\sum_q H_q^{-1}\big)$, where $S_k$ is the Schur-complement posterior precision of $a_k$ after integrating out difficulties and $H_q$ the diagonal Hessian for $b_q$. These Laplace corrections stop $\tau^2$ from collapsing or inflating. Fitting uses bincount-based vector operations, so exhaustive and halving logs share one code path; the fit stops after at most 30 sweeps or a 1.5\,s wall-clock budget.

\textbf{Ignorability.} Exhaustive search and successive halving choose which entries to observe and which configuration to select using only previously observed outcomes. The likelihood of the log is therefore unaffected by the design, and a likelihood-based posterior is valid under either searcher without a searcher-specific correction, provided the model is adequately specified. This is a motivation, not a proof for the real-outcome worlds, whose subject-by-configuration structure a one-dimensional difficulty model only approximates.

\textbf{Posterior interval.} We draw 400 samples of $(a_{\hat k},\text{level shift},\log s)$ from Laplace approximations, integrate over fresh difficulties with 21 Gauss--Hermite nodes and each subject, and obtain draws of $\theta_{\hat k}$. The estimate is their mean $\hat\theta$; with $q_{0.05},q_{0.95}$ the posterior quantiles, the reported interval is
\begin{equation}
\ell=\hat\theta-\kappa\,(\hat\theta-q_{0.05})_+,\qquad u=\hat\theta+\kappa\,(q_{0.95}-\hat\theta)_+ ,
\end{equation}
with a width factor $\kappa(N,K)=\kappa_0\,\big(1+0.25\min(1,\sqrt{50/N})\big)\big(1+0.03\log_2(K/2)\big)$, where $\kappa_0=1.20$ when the log carries subject codes (real outcomes) and $1.12$ otherwise. The constants are fixed in the source; they are design priors that widen the interval to compensate for ignored hyperparameter uncertainty and misspecification, not values fitted to the final worlds. Over the cases studied $\kappa$ ranges from 1.43 to 1.63 (Table~\ref{tab:kappa} in the Supplement), so intervals are roughly 40--60\% wider than raw posterior quantiles. Because $\kappa$ acts only around $\hat\theta$, bias comparisons with the naive estimate reflect the posterior mean alone, whereas interval width and coverage reflect the posterior and $\kappa$ jointly; we did not evaluate $\kappa=1$.

\textbf{Degenerate worlds.} If every outcome is zero the reporter returns estimate $0$ and upper bound $\min(3/n_{\hat k},0.02)$; if $\hat k$ was never observed it returns the pooled mean $\pm0.25$; any exception falls back to a widened Wilson interval.

\subsection{Compared reporters}\label{sec:baselines}
All baselines are computed by the evaluator from the same log. \emph{Naive Wilson}: observed accuracy of $\hat k$ with a 90\% Wilson interval. \emph{Bonferroni-Wilson}: the same estimate with the Wilson critical value taken at level $1-\alpha/(2K)$. \emph{Resampling}: 100 random half-splits; on each, the best configuration on one half is re-scored on the other, the mean score gap $g$ is rescaled to $\hat p_{\hat k}-g/\sqrt2$, and a Wilson interval is placed around it.

\subsection{Experimental protocol}\label{sec:protocol}




\textbf{Worlds.} \emph{Synthetic} worlds draw a base accuracy uniformly from $[0.25,0.75]$ and per-configuration accuracies with spread $0.03$; outcomes follow a Gaussian copula with latent correlation $0.5$ across configurations, and the truth is the selected configuration's accuracy. \emph{Real} worlds use a cached $1500\times24$ binary tensor of Qwen2.5-0.5B-Instruct answers on MMLU-Pro (24 prompt configurations: four instruction wordings $\times$ three demonstration settings $\times$ two answer-prefix formats; revisions in the Supplement). Each replication samples $N$ questions without replacement, permutes configuration labels, searches, and takes as truth the selected configuration's accuracy on the remaining pool questions. \emph{Controls}: N1 is a synthetic world with identical configurations; N2 is the real pool with each question's configuration columns reassigned by a random derangement to break configuration effects; Z1 is an all-zero world with $K=8$. In any null world no configuration is better, so a reporter should neither invent signal nor lose coverage.

\textbf{Cases and searchers.} Table~\ref{tab:cases} lists the cases. \emph{Exhaustive} search evaluates every configuration on every question and selects the highest total; \emph{successive halving} works with a nominal budget of $N\!\cdot\!K$ evaluations over $\lceil\log_2K\rceil$ rounds, discarding the lower half of the survivors each round, so configurations eliminated early are observed on few questions and the log is sparse. Each case has $R=30$ replications ($R=10$ for Z1).

\textbf{Aggregation and uncertainty.} Per-case values average replications; the primary aggregate averages P1--P2 (synthetic, weight 0.4) and P3--P6 (real, weight 0.6) within family. The sealed evaluation uses eight seeds (9101--9108), each running all nine cases. We report mean $\pm$ standard deviation of seed-level values and, for reporter differences, paired seed-level differences. The evaluator records interval score, bias, coverage and width for the EB-IRT reporter, but only the interval scores of the three baselines and the bias of the naive reporter. All other baseline quantities (baseline coverage and width, and the bias of the Bonferroni and resampling reporters) are replay-derived: we replayed the evaluator's own deterministic world, search and baseline code, which reproduced the recorded baseline interval scores and the recorded naive bias exactly (maximum absolute difference 0). The replay-derived values are not checked against any evaluator record. Per-case records carry an unverified diagnostics label from the evaluator, so we treat aggregate metrics as authoritative and per-case values as supporting. The reporter was frozen before the sealed evaluation, and the evaluation completed all replications (completed fraction 1.0).

\section{Results}\label{sec:results}
\subsection{Optimism of best-of-search reporting}\label{sec:gap}





Averaged over P1--P6 the naive estimate exceeds the fresh-question accuracy by $0.0366\pm0.0029$ (Table~\ref{tab:aggregate}). Its nominal 90\% Wilson interval contains the truth in $0.713\pm0.048$ of replications, and in no primary case does it reach 0.82 (Table~\ref{tab:cases}). The Bonferroni-widened interval fixes coverage ($0.962$) but spends width: $0.190$ against $0.129$ for EB-IRT.

\emph{Question budget.} On the three real exhaustive cases ($K=24$) the naive bias falls monotonically with $N$: $0.051$ at $N=60$ (P5), $0.022$ at $N=200$ (P3), $0.009$ at $N=600$ (P6) (Figure~\ref{fig:biascov}a). The optimism at $N=60$ is of the same order as the spread of the 24 configurations' pool accuracies ($0.107$ to $0.166$ in the final pool); we did not measure how the optimism relates to true between-configuration differences.

\emph{World.} Optimism is larger when configurations do not truly differ: in the synthetic null N1 the naive bias is $0.067$ against $0.049$ in P1 (same $N$, $K$, searcher), and in the permuted real null N2 it is $0.034$ against $0.022$ in P3. This is the winner's-curse pattern expected when selection is among near-equals; we did not test it causally.

\emph{Searcher and $K$.} Under halving the naive bias is $0.054$ (P2) and $0.025$ (P4), versus $0.049$ (P1) and $0.022$ (P3) under exhaustive search in matched worlds. The matched paired differences ($+0.004\pm0.012$ and $+0.003\pm0.008$ across seeds) are small relative to seed spread; aggregated over searcher-specific cases the naive bias is $0.036$ under both. We cannot separate the effect of $K$ because it is confounded with the world (32 synthetic, 24 real, 8 constant).

\subsection{Main comparison: sealed final evaluation}




\begin{table}[t]
\centering
\caption{Sealed final evaluation, primary cases P1--P6 (0.4 synthetic / 0.6 real), mean $\pm$ standard deviation over eight seeds. The interval score is at level 0.90 (lower is better); coverage should be near 0.90. Bonferroni-Wilson shares the naive point estimate. Baseline coverage, width and the resampling bias are replay-derived from the evaluator's code, not evaluator-recorded (Section~\ref{sec:protocol}).}
\label{tab:aggregate}
\small









\begin{tabular}{lcccc}
\toprule
Reporter & Interval score $\downarrow$ & Coverage & Mean width & Signed bias \\
\midrule
Naive Wilson & 0.2202$\pm$0.0234 & 0.713$\pm$0.048 & 0.109 & 0.0366$\pm$0.0029 \\
Bonferroni-Wilson & 0.1974$\pm$0.0036 & 0.962$\pm$0.012 & 0.190 & 0.0366$\pm$0.0029 \\
Resampling & 0.2461$\pm$0.0251 & 0.748$\pm$0.020 & 0.104 & $-$0.0209$\pm$0.0030 \\
\textbf{EB-IRT (ours)} & 0.1449$\pm$0.0040 & 0.929$\pm$0.008 & 0.129 & 0.0121$\pm$0.0027 \\
\bottomrule
\end{tabular}
\end{table}

EB-IRT attains a mean interval score of $0.1449$ against $0.2202$ (naive), $0.1974$ (Bonferroni-Wilson) and $0.2461$ (resampling) (Table~\ref{tab:aggregate}), with coverage $0.929$ and RMSE $0.0348$. Its score is lower than each baseline's in all eight seeds; paired seed-level differences are $0.075\pm0.021$ (naive), $0.053\pm0.004$ (Bonferroni) and $0.101\pm0.023$ (resampling). Its aggregate bias, $0.0121\pm0.0027$, removes about two thirds of the naive optimism. The evaluator's qualification outcome for this run is ``qualified'' with status ``completed''. Gate diagnostics beyond that outcome are not available to us, and the outcome does not by itself establish validity beyond the studied worlds.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/per_case_interval_score.pdf}
\caption{Mean interval score per case (lower is better) for four reporters; bars show mean over eight seeds, whiskers one standard deviation across seeds. (a) Synthetic worlds including the null N1. (b) Real outcomes including the permuted null N2. The resampling bar for P2 is clipped (value 0.59).}
\label{fig:perCase}
\end{figure}

\begin{table}[t]
\centering
\caption{Per-case interval score (mean over eight seeds; best per row in bold) and coverage of the naive and EB-IRT intervals. ``exh.'' exhaustive search, ``halv.'' successive halving. Seed standard deviations are in the Supplement.}
\label{tab:cases}
\small
\setlength{\tabcolsep}{4pt}



\begin{tabular}{llrrcccccc}
\toprule
Case & World, search & $N$ & $K$ & Naive & Bonf. & Resamp. & EB-IRT & Cov.\ naive & Cov.\ EB-IRT \\
\midrule
P1 & synthetic, exh. & 150 & 32 & 0.264 & 0.224 & 0.164 & \textbf{0.150} & 0.65 & 0.96 \\
P2 & synthetic, halv. & 150 & 32 & 0.300 & 0.225 & 0.592 & \textbf{0.155} & 0.61 & 0.96 \\
P3 & real, exh. & 200 & 24 & 0.155 & 0.161 & \textbf{0.109} & 0.116 & 0.81 & 0.94 \\
P4 & real, halv. & 200 & 24 & 0.161 & 0.165 & 0.258 & \textbf{0.156} & 0.77 & 0.89 \\
P5 & real, exh. & 60 & 24 & 0.303 & 0.295 & \textbf{0.174} & 0.192 & 0.71 & 0.98 \\
P6 & real, exh. & 600 & 24 & 0.096 & 0.096 & \textbf{0.092} & 0.096 & 0.78 & 0.83 \\
\midrule
N1 & synth.\ null, exh. & 150 & 32 & 0.354 & 0.231 & 0.140 & \textbf{0.128} & 0.47 & 0.97 \\
N2 & real null, exh. & 200 & 24 & 0.218 & 0.168 & \textbf{0.102} & 0.111 & 0.62 & 0.89 \\
Z1 & all-zero, exh. & 100 & 8 & 0.026 & 0.059 & 0.026 & \textbf{0.020} & 1.00 & 1.00 \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Where the gain is large, and where it is not}



Figure~\ref{fig:perCase} and Table~\ref{tab:cases} show a heterogeneous picture, which the aggregate hides.

\emph{Large gains.} On synthetic worlds and at small $N$ EB-IRT lowers the naive interval score by 37--48\% (P1: $0.150$ vs $0.264$; P2: $0.155$ vs $0.300$; P5: $0.192$ vs $0.303$) with coverage at or above nominal. It also beats Bonferroni-Wilson by $0.07$--$0.10$ in P1, P2 and P5 in every seed.

\emph{No gain over naive.} In real-outcome halving (P4) the three Wilson-style scores are close ($0.156$ vs naive $0.161$, Bonferroni $0.165$); the paired advantage over naive is $0.005$ and EB-IRT wins in six of eight seeds. Its point estimate is \emph{more} biased than the naive one there ($0.031$ vs $0.025$) and its coverage is $0.89$, slightly below nominal but within seed noise (seed s.d.\ $0.03$ over eight seeds). At $N=600$ (P6) all Wilson-style reporters score $0.096$ and the naive bias is already small ($0.009$ vs $0.011$ for EB-IRT).

\emph{Resampling is as good under exhaustive search.} Restricting the aggregate to exhaustive-search cases (P1 and P3, P5, P6, same weights) gives interval scores of $0.1406$ for EB-IRT and $0.1405$ for resampling, against $0.2166$ for naive: a tie. In the real exhaustive cases P3, P5 and N2 resampling is slightly better ($0.109$, $0.174$, $0.102$ vs $0.116$, $0.192$, $0.111$), and EB-IRT is the better of the two in only 2, 1 and 1 of eight seeds respectively. The aggregate advantage over resampling therefore comes from halving: on halving cases resampling scores $0.3916$ against $0.1556$, because it over-corrects the sparse log (replay-derived bias $-0.067$ in P2 and $-0.031$ in P4; replay-derived coverage $0.44$ and $0.61$). EB-IRT is the more robust reporter across searchers, not uniformly the more accurate.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/bias_and_coverage.pdf}
\caption{Diagnostics for the primary cases (mean over eight seeds, whiskers one standard deviation across seeds). (a) Signed bias of the point estimate for the naive and EB-IRT reporters. (b) Empirical coverage of the 90\% intervals; dashed line marks the nominal level. Naive coverage is replayed from the evaluator's code.}
\label{fig:biascov}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=0.7\textwidth]{figures/width_vs_n.pdf}
\caption{Mean interval width on the real exhaustive cases ($K=24$) as the number of benchmark questions grows (mean over eight seeds). EB-IRT is wider than the naive interval by a factor of 1.1--1.3 at each $N$ and much narrower than Bonferroni-Wilson. Naive and Bonferroni widths are replayed from the evaluator's code.}
\label{fig:width}
\end{figure}

\emph{Residual bias and miscalibrated width.} EB-IRT's signed bias is positive in five of six primary cases (range $0.009$--$0.031$) and slightly negative only in P1 ($-0.002\pm0.010$) (Figure~\ref{fig:biascov}a); shrinkage removes most, not all, of the winner's curse. Coverage varies from $0.98$ (P5) and $0.96$ (P1, P2) down to $0.89$ (P4) and $0.83$ (P6) (Figure~\ref{fig:biascov}b). Interval width shrinks with $N$ for all reporters (Figure~\ref{fig:width}): EB-IRT is $0.187$, $0.101$ and $0.065$ wide at $N=60$, $200$, $600$, against $0.167$, $0.088$ and $0.050$ for the naive interval and $0.284$, $0.153$ and $0.088$ for Bonferroni-Wilson. The aggregate coverage of $0.929$ is thus an average of over- and under-coverage rather than evidence of calibration in each regime: the fixed width factor over-widens the synthetic and small-$N$ cases and under-widens the largest-$N$ real case. At $N=600$ the target itself is measured on the remaining 900 pool questions, a finite-sample noise that no reporter here models and that matters most where intervals are narrowest; we did not test how much of the P6 shortfall it explains.

\subsection{Negative controls}\label{sec:controls}





In the synthetic null N1 EB-IRT has coverage $0.971$ and interval score $0.128$ against $0.354$ for naive, whose coverage is $0.47$. In the permuted real null N2 EB-IRT has coverage $0.887$ and interval score $0.111$ (naive $0.218$, resampling $0.102$). In both nulls its bias is $0.017$: shrinkage does not reduce the estimate fully to the common mean, and the controls average $0.0173$ in absolute bias. In the constant-zero world Z1 the reporter returns exactly zero with interval $[0,0.02]$ (absolute estimate error $0$, interval score $0.020$ against $0.026$ naive and $0.059$ Bonferroni). The reporter therefore does not manufacture signal in null worlds, but its null coverage in the real world sits at the same $0.89$ as in P4.

\subsection{Reporter variants considered during development}

Two alternative designs were evaluated in the development setting (four seeds, cases P1--P4 with controls) alongside EB-IRT: a parametric-bootstrap pivot calibration of the interval, and an extension with configuration-by-subject random effects. Table~\ref{tab:variants} shows that narrower intervals do not pay: the bootstrap variant has the smallest width ($0.085$) but coverage $0.77$ and a higher interval score ($0.1562$) than EB-IRT ($0.1480$), and t

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}
\subsection{Estimator details and hyperparameters}
The reporter is a single Python module with NumPy only. Fixed constants: at most 30 EB sweeps (three damped Newton steps for $a$ and for $b$ per sweep, steps clipped to $\pm1$) with a 1.5\,s wall-clock guard; $\tau^2\in[10^{-4},4]$, $s^2\in[10^{-2},25]$; initial $\tau^2=0.25$, $s^2=1$; five pseudo-questions for subject means; 400 posterior draws; 21 Gauss--Hermite nodes; level-shift draws with standard deviation $s/\sqrt N$ and $\log s$ perturbations with standard deviation $1/\sqrt{2N}$. The prior variance of $a_{\hat k}$ is floored at $0.3$ times the median inverse Schur precision so that near-equal configurations still receive an interval reflecting sampling noise. The world is treated as ``real'' when any subject code is nonzero. Table~\ref{tab:kappa} gives the resulting $\kappa$. The reporter's draws are seeded from the evaluator's reset call. Source: the reporter's module, function \texttt{\_kappa} and \texttt{\_fit\_irt}.


\begin{table}[h]
\centering
\caption{Width factor $\kappa$ applied around the estimate in each evaluation case (computed from the reporter's own function). It is not used in Z1, where the all-zero rule applies.}
\label{tab:kappa}
\small

\begin{tabular}{lcccc}
\toprule
Case & $N$ & $K$ & Searcher & $\kappa$ \\
\midrule
P1 & 150 & 32 & exhaustive & 1.435 \\
P2 & 150 & 32 & halving & 1.435 \\
P3 & 200 & 24 & exhaustive & 1.495 \\
P4 & 200 & 24 & halving & 1.495 \\
P5 & 60 & 24 & exhaustive & 1.632 \\
P6 & 600 & 24 & exhaustive & 1.425 \\
N1 & 150 & 32 & exhaustive & 1.435 \\
N2 & 200 & 24 & exhaustive & 1.495 \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Evaluation protocol and provenance}
The sealed evaluation runs seeds 9101--9108; each seed runs P1--P6, N1, N2 (30 replications each) and Z1 (10), so $8\times250=2000$ reporter calls. The development setting runs seeds 101--104 with cases P1--P4, N1, N2, Z1. Real worlds: MMLU-Pro revision \texttt{b189ec76\ldots} (MIT licence), Qwen2.5-0.5B-Instruct revision \texttt{7ae55760\ldots} (Apache-2.0), float32 CPU, one deterministic forward pass, prediction by argmax over the ten option-letter logits. Questions are deduplicated by normalized content hash, restricted to 10 options and at most 400 tokens, stratified over 14 subjects; the final pool has 1500 questions and the development pool 599, with no hash overlap between pools or with the demonstration source. The 24 configurations are indexed as (wording $\times$ 3 + demonstration setting) $\times$ 2 + format, with demonstration settings 0-shot and two 3-shot sets from the validation split. Configuration labels are randomly permuted per replication. Aggregate weights are 0.4 synthetic and 0.6 real. The interval score uses $\alpha=0.10$ and a worst case of 20.



\textbf{Compute.} Evaluator-recorded wall-clock time per seed (250 episodes, covering reporter calls and scoring) averaged $6.2$\,s, about $50$\,s over the eight sealed seeds. No GPU or API was used in this study.


\subsection{Per-case detail}
Table~\ref{tab:suppcase} gives seed-level spread for all nine cases and Table~\ref{tab:suppbase} the Bonferroni and resampling coverage and width.
\begin{table}[h]
\centering
\caption{Per-case interval score (mean $\pm$ s.d.\ over eight seeds), width and signed bias for EB-IRT and the naive reporter. Naive width is replayed from the evaluator's code.}
\label{tab:suppcase}
\footnotesize
\setlength{\tabcolsep}{4pt}


\begin{tabular}{lcccccc}
\toprule
Case & IS EB-IRT & IS naive & Width EB-IRT & Width naive & Bias EB-IRT & Bias naive \\
\midrule
P1 & 0.150$\pm$0.009 & 0.264$\pm$0.074 & 0.140 & 0.125 & $-$0.002$\pm$0.010 & 0.049$\pm$0.010 \\
P2 & 0.155$\pm$0.006 & 0.300$\pm$0.033 & 0.150 & 0.125 & 0.013$\pm$0.005 & 0.054$\pm$0.005 \\
P3 & 0.116$\pm$0.015 & 0.155$\pm$0.050 & 0.101 & 0.088 & 0.009$\pm$0.007 & 0.022$\pm$0.006 \\
P4 & 0.156$\pm$0.027 & 0.161$\pm$0.032 & 0.121 & 0.088 & 0.031$\pm$0.004 & 0.025$\pm$0.004 \\
P5 & 0.192$\pm$0.012 & 0.303$\pm$0.059 & 0.187 & 0.167 & 0.016$\pm$0.008 & 0.051$\pm$0.010 \\
P6 & 0.096$\pm$0.014 & 0.096$\pm$0.011 & 0.065 & 0.050 & 0.011$\pm$0.003 & 0.009$\pm$0.003 \\
N1 & 0.128$\pm$0.004 & 0.354$\pm$0.068 & 0.125 & 0.127 & 0.017$\pm$0.004 & 0.067$\pm$0.005 \\
N2 & 0.111$\pm$0.018 & 0.218$\pm$0.035 & 0.089 & 0.087 & 0.017$\pm$0.003 & 0.034$\pm$0.002 \\
Z1 & 0.020$\pm$0.000 & 0.026$\pm$0.000 & 0.020 & 0.026 & 0.000$\pm$0.000 & 0.000$\pm$0.000 \\
\bottomrule
\end{tabular}
\end{table}
\begin{table}[h]
\centering
\caption{Bonferroni-Wilson and resampling reporters per case: interval score (mean $\pm$ s.d.\ over eight seeds), and replayed coverage and width.}
\label{tab:suppbase}
\footnotesize
\setlength{\tabcolsep}{4pt}


\begin{tabular}{lcccccc}
\toprule
Case & IS Bonf. & IS Resamp. & Cov.\ Bonf. & Cov.\ Resamp. & Width Bonf. & Width Resamp. \\
\midrule
P1 & 0.224$\pm$0.004 & 0.164$\pm$0.020 & 0.98 & 0.90 & 0.221 & 0.127 \\
P2 & 0.225$\pm$0.006 & 0.592$\pm$0.131 & 0.98 & 0.44 & 0.221 & 0.127 \\
P3 & 0.161$\pm$0.009 & 0.109$\pm$0.023 & 0.95 & 0.86 & 0.153 & 0.082 \\
P4 & 0.165$\pm$0.016 & 0.258$\pm$0.058 & 0.95 & 0.61 & 0.153 & 0.075 \\
P5 & 0.295$\pm$0.021 & 0.174$\pm$0.031 & 0.96 & 0.93 & 0.284 & 0.147 \\
P6 & 0.096$\pm$0.008 & 0.092$\pm$0.014 & 0.95 & 0.79 & 0.088 & 0.049 \\
N1 & 0.231$\pm$0.007 & 0.140$\pm$0.014 & 0.97 & 0.95 & 0.224 & 0.127 \\
N2 & 0.168$\pm$0.013 & 0.102$\pm$0.012 & 0.93 & 0.90 & 0.151 & 0.079 \\
Z1 & 0.059$\pm$0.000 & 0.026$\pm$0.000 & 1.00 & 1.00 & 0.059 & 0.026 \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Reproducibility}
All numbers come from the sealed final record and the derived files in \texttt{analysis/}. \texttt{final\_per\_case.py} derives per-case means, seed standard deviations and paired differences from the recorded episodes; \texttt{reconstruct\_baselines.py} replays the evaluator's worlds and baselines (requires NumPy) and checks them against the recorded values; \texttt{search\_variants.py} produces Table~\ref{tab:variants}; \texttt{kappa\_values.py} produces Table~\ref{tab:kappa}; \texttt{make\_tables.py} writes Tables~\ref{tab:aggregate}, \ref{tab:cases}, \ref{tab:variants}, \ref{tab:kappa}, \ref{tab:suppcase} and \ref{tab:suppbase}; \texttt{make\_figures.py} writes Figures~\ref{fig:perCase} and \ref{fig:biascov}. Package versions and total script runtime were not recorded in the evidence trail; the only recorded timing is the evaluator's per-seed duration. Seeds are those listed above.

\subsection{LLM Usage}
Large language models were used as research and writing assistants in this study: to propose and implement the reporter variants, to analyse the evaluation records, and to draft and edit this manuscript. All numerical results come from the evaluator's records and the scripts listed above; the authors of record are responsible for the content.
```
