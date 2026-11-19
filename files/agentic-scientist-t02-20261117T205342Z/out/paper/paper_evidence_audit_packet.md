# Agentic evidence audit packet

- generated_at: `2026-11-18T02:10:25.984235+00:00`
- paper_dir: `work/results/t02/codex/20261117_205843/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261118_004833-paper_evidence_audit_round_4-4s7w_0us/workspace`

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
    "anchored_references": 97,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 158,
    "resolved_references": 108,
    "total_references": 205
  },
  "ok": true,
  "pdf_path": "work/results/t02/codex/20261117_205843/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 97,
    "dangling_references": 0,
    "manifests_checked": 17,
    "resolved_references": 108,
    "total_references": 205
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "On addition, mean final held-out CE is 339.459 without decay versus 8.390 with decay at width 16, and 89.877 versus 8.627 at width 256. Loss differences do not establish generalization events or a mechanism.",
      "derived_artifact": "analysis/derived_results.json#/records",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The three-seed mean initial parameter norms are 6.288, 7.383, and 10.904 at widths 16, 64, and 256. Initial norms coincide across operation/decay arms at fixed width and seed, but widths are not norm-matched.",
      "derived_artifact": "analysis/derived_results.json#/records",
      "source_files": [
        "source_evidence/evaluate_final.py:825"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The final factorial contains addition and subtraction modulo 97, widths 16, 64, and 256, decay 0 and 1, and initialization seeds 1009, 2027, and 3037, for 36 completed records.",
      "evidence_locator": "/final_evaluation/evaluation_evidence/episodes/*/solution/*/case",
      "source_files": [
        "source_evidence/evaluate_final.py:656",
        "source_evidence/evaluate_final.py:789"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.completion_fraction"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Thirty records attain sustained memorization and zero attain sustained generalization by 20,000 updates; none of the 30 fitted records has an observed delayed-generalization event.",
      "evidence_locator": "/final_evaluation/evaluation_evidence/episodes/*/solution/*/observations/{memorization,generalization,delayed}",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.delayed_fraction"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Each operation enumerates 9409 pairs and retains 4705 in the final partition, with 1411 training and 3294 held-out examples; approximately 30% of the final subset and 15% of the full universe train the network.",
      "derivation": "Read p=97 in evaluated source; count retained resource examples by split; compute p squared and split fractions. Episode parameter counts and traces identify the evaluated family.",
      "source_files": [
        "source_evidence/evaluate_final.py:588",
        "source_evidence/resources/final/benchmark.json"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The input concatenates two one-hot vectors into 194 dimensions; the classifier has a ReLU hidden layer of width w, biases in both linear layers, and 97 output logits, with 292w+97 parameters.",
      "evidence_locator": "/final_evaluation/evaluation_evidence/episodes/*/solution/*/observations/trace/*/parameter_count",
      "source_files": [
        "source_evidence/evaluate_final.py:802",
        "source_evidence/evaluate_final.py:828"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Widths 16, 64, and 256 have 4769, 18785, and 74849 trainable parameters, respectively, and use default PyTorch linear initialization without logit-scale matching.",
      "source_files": [
        "source_evidence/evaluate_final.py:825"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Loshchilov2017DecoupledWD"
      ],
      "claim": "Training uses full-batch cross-entropy and AdamW with shared constant learning rate 0.01, decay 0 or 1, betas 0.9 and 0.999, epsilon 1e-8, and no bias-specific parameter groups.",
      "source_files": [
        "source_evidence/evaluate_final.py:842",
        "source_evidence/controller/src/program.py:46"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The protocol runs 20000 updates per condition with measurements at initialization and every 500 updates, using deterministic algorithms and a single compute/interoperation thread; each condition resets training state.",
      "source_files": [
        "source_evidence/evaluate_final.py:789",
        "source_evidence/evaluate_final.py:962"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The original neural-training dependencies are numpy==2.1.3 and torch==2.5.1+cpu.",
      "source_files": [
        "source_evidence/requirements.txt"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Memorization requires at least 99% training accuracy for three consecutive checkpoints, and generalization requires at least 95% held-out accuracy for three consecutive checkpoints; event timestamps are window starts.",
      "source_files": [
        "source_evidence/evaluate_final.py:721"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Late-window accuracies average the final five checkpoints, covering updates 18000 through 20000, independently of the sustained-event test.",
      "derived_artifact": "analysis/derived_results.json",
      "source_files": [
        "source_evidence/evaluate_final.py:738"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Without decay all widths memorize: width 16 at 1000 to 1500 updates and widths 64 and 256 at 500 updates across operations and seeds. The exact twelve condition rows and seed times appear in the main event table.",
      "derived_artifact": "tables/events.tex",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "With positive decay all six width-16 records fail to memorize by the horizon, whereas all width-64 and width-256 records memorize at 500 updates.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "All zero-decay late-window training accuracies average 100%; with positive decay width-16 means are 56.664% for addition and 55.625% for subtraction, while all wider conditions average 100%.",
      "derived_artifact": "analysis/derived_results.json#/conditions",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Zero-decay width-16 held-out seed means and sample standard deviations are 0.482 +/- 0.061% for addition and 0.407 +/- 0.006% for subtraction; width-64 means are 0.047% and 0.026%; width-256 late-window accuracy is zero in every seed.",
      "derived_artifact": "analysis/derived_results.json#/conditions",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Positive-decay held-out means for widths 16,64,256 are 0.219%,0.091%,0.091% on addition and 0.178%,0.053%,0.117% on subtraction; these low values do not support a common monotone width trend.",
      "derived_artifact": "analysis/derived_results.json#/conditions",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The overall late-window held-out mean is 0.142515%, averaging all 36 conditions equally rather than filtering on fitting attainment.",
      "derived_artifact": "analysis/derived_results.json#/overall_heldout_percent",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.combined_score"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Mode, lookup-fallback, deranged-alignment, and initialized-network reference means are respectively 0.865209%,0.865209%,0.949201%,1.050732%; the trained-minus-reference mean gap is -0.790073 percentage points.",
      "derived_artifact": "analysis/derived_results.json#/control_means_percent",
      "source_files": [
        "source_evidence/evaluate_final.py:805",
        "source_evidence/evaluate_final.py:831"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.control_gap"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The lookup and mode references coincide because held-out input pairs are disjoint from the training lookup; deranged alignment is not independently randomized-label training.",
      "source_files": [
        "source_evidence/evaluate_final.py:831",
        "source_evidence/resources/final/benchmark.json"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The lag substitutes H for unobserved generalization, uses H-T_M for observed memorization with unobserved generalization, and assigns H when memorization is not observed.",
      "source_files": [
        "source_evidence/evaluate_final.py:735"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.restricted_mean_lag"
      ]
    },
    {
      "citation_keys": [],
      "claim": "At positive decay, width-16 capped lag is 20000 and width-256 capped lag is 19500; every paired seed contrast is 500, with the supplied interval [500,500]. This is not an observed generalization-time contrast.",
      "source_files": [
        "source_evidence/evaluate_final.py:746"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.width_lag_contrast",
        "final.metric.width_lag_ci_low",
        "final.metric.width_lag_ci_high"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Zero-decay operation-averaged seed contrasts are -750,-500,-500, with mean -583.333; the difference of mean contrasts across decay arms is 1083.333 updates.",
      "derived_artifact": "analysis/derived_results.json#/paired_contrasts",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.decay_interaction"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The mean capped lag over all records is 19486.111 updates, not a mean uncensored grokking delay.",
      "source_ids": [
        "final.metric.restricted_mean_lag",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The supplied interval uses the sample standard deviation of three paired contrasts and multiplier 4.30265273/sqrt(3), clipped to [-H,H]; its degeneracy follows from zero contrast variation.",
      "source_files": [
        "source_evidence/evaluate_final.py:762"
      ],
      "source_ids": [
        "final.metric.width_lag_ci_low",
        "final.metric.width_lag_ci_high",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The supplementary table preserves all 36 records' event times, capped lags, and final-five-checkpoint accuracies; the diagnostic table averages final-checkpoint training CE, held-out CE, and parameter norm over the three seeds for each condition.",
      "derived_artifacts": [
        "tables/full_observations.tex",
        "tables/diagnostics.tex"
      ],
      "source_files": [
        "build_artifacts.py",
        "source_evidence/evaluate_final.py:805"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The three stored seed-evaluation durations, each covering its condition grid, are 786.393,777.546,786.875 seconds; they are observations, not portable runtime guarantees.",
      "evidence_locator": "/final_evaluation/evaluation_evidence/episodes/*/duration_seconds",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The independent final qualification sources report completed, qualified, and true; this acceptance does not establish generalization or a neural mechanism. The retained diagnostics-trust designation is unverified.",
      "evidence_locator": "/final_evaluation/evaluation_evidence/candidate_diagnostics_trust",
      "source_ids": [
        "final.qualification.status",
        "final.qualification.outcome",
        "final.qualification.correct",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "No matched final-plane comparison to the original lower-rate recipe is retained; development scores are not used as final results, and no cross-task transfer, random-label training, initial-logit calibration, circuit measurement, or generalization-time equivalence is claimed.",
      "source_files": [
        "source_evidence/controller/src/EXPERIMENT_SCOPE.md",
        "source_evidence/controller/src/program.py",
        "source_evidence/evaluate_final.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The final evaluator and observation-file hashes match their final metadata; hashes identify supplied artifacts rather than prove implementation substance.",
      "source_files": [
        "source_evidence/evaluate_final.py",
        "source_evidence/evaluation_evidence.json",
        "source_evidence/final_manifest.json"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.qualification.status"
      ]
    },
    {
      "citation_keys": [
        "Power2022GrokkingGB"
      ],
      "claim": "Grokking can produce held-out improvement long after training-set fitting on small algorithmic datasets, with dataset size affecting optimization requirements.",
      "source_files": [
        "literature/2201.02177.txt"
      ],
      "source_ids": [
        "ref.arxiv.2201.02177"
      ]
    },
    {
      "citation_keys": [
        "Loshchilov2017DecoupledW

[truncated after 14000 chars]
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
  "grounding_source_count": 24,
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
  "count": 8,
  "minimum_reference_count_unmet": true,
  "references": [
    {
      "citation_key": "Power2022GrokkingGB",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.2201.02177",
      "local_path": "literature/2201.02177.txt",
      "retrieved_at": "2026-11-18T01:07:41.124179+00:00",
      "sha256": "cd194c0c4b642426139a4c97e071baf3ad391bd1275866e6c8e1b3c5162dbf1b",
      "source_url": "https://arxiv.org/abs/2201.02177",
      "title": "Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets",
      "year": 2022
    },
    {
      "citation_key": "Loshchilov2017DecoupledWD",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.1711.05101",
      "local_path": "literature/1711.05101.txt",
      "retrieved_at": "2026-11-18T01:07:41.468786+00:00",
      "sha256": "bbf032f0fe2fd9cd13d77a067f7cea1b2c66c6c99e30b2c5bf92ac6cc97c2609",
      "source_url": "https://arxiv.org/abs/1711.05101",
      "title": "Decoupled Weight Decay Regularization",
      "year": 2017
    },
    {
      "citation_key": "Liu2023Omnigrok",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.2210.01117",
      "local_path": "literature/2210.01117.txt",
      "retrieved_at": "2026-11-18T01:07:41.833789+00:00",
      "sha256": "4976cfeed9c4c0b623d2537bb31f06add0a8553b48331913e9ca7f7575249338",
      "source_url": "https://arxiv.org/abs/2210.01117",
      "title": "Omnigrok: Grokking Beyond Algorithmic Data",
      "year": 2022
    },
    {
      "citation_key": "Varma2023ExplainingGT",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.2309.02390",
      "local_path": "literature/2309.02390.txt",
      "retrieved_at": "2026-11-18T01:07:42.191166+00:00",
      "sha256": "1614bfd7e02e2431fd8240370539984c359f06f2083a82ff55d198cd1a20fec7",
      "source_url": "https://arxiv.org/abs/2309.02390",
      "title": "Explaining grokking through circuit efficiency",
      "year": 2023
    },
    {
      "citation_key": "Kumar2024LazyRich",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.2310.06110",
      "local_path": "literature/2310.06110.txt",
      "retrieved_at": "2026-11-18T01:07:42.625760+00:00",
      "sha256": "79ce2458cbe1dd11fdf16754f877a36c61a857d9fe267bac6f6b9d95946d6973",
      "source_url": "https://arxiv.org/abs/2310.06110",
      "title": "Grokking as the Transition from Lazy to Rich Training Dynamics",
      "year": 2023
    },
    {
      "citation_key": "Davies2023Unifying",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.2303.06173",
      "local_path": "literature/2303.06173.txt",
      "retrieved_at": "2026-11-18T01:07:43.039474+00:00",
      "sha256": "dc265f7bdc98afd9c965f0230fc33156eabde59d300ad6a10f0b9a136d67bbce",
      "source_url": "https://arxiv.org/abs/2303.06173",
      "title": "Unifying Grokking and Double Descent",
      "year": 2023
    },
    {
      "citation_key": "Nakkiran2020DoubleDescent",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.1912.02292",
      "local_path": "literature/1912.02292.txt",
      "retrieved_at": "2026-11-18T01:07:43.387651+00:00",
      "sha256": "357a0c40b0bfb75ec0d3a1ee6243ffe396440b8aeb8f6d2561f529b203177b7d",
      "source_url": "https://arxiv.org/abs/1912.02292",
      "title": "Deep Double Descent: Where Bigger Models and More Data Hurt",
      "year": 2019
    },
    {
      "citation_key": "Zhang2017Rethinking",
      "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
      "id": "ref.arxiv.1611.03530",
      "local_path": "literature/1611.03530.txt",
      "retrieved_at": "2026-11-18T01:07:43.750416+00:00",
      "sha256": "db65bbba35fc87f990238c93d236e367c86054fc8b04cedef5a301689146de3d",
      "source_url": "https://arxiv.org/abs/1611.03530",
      "title": "Understanding deep learning requires rethinking generalization",
      "year": 2016
    }
  ],
  "safety_boundary": "Only the eight exact identities approved by paper_strategy and the task starter list"
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
\usepackage{amsmath,amssymb,booktabs,longtable,graphicx,subcaption}
\usepackage{hyperref,url}
\title{Memorization Without Observed Grokking Across MLP Widths}
\author{}
\newcommand{\TM}{T_{\mathrm{M}}}
\newcommand{\TG}{T_{\mathrm{G}}}
\newcommand{\LH}{L_H}

\begin{document}
\maketitle

\begin{abstract}
Does increasing model size change delayed generalization, or only the speed of fitting the training data? We study this distinction in full-batch ReLU multilayer perceptrons on modular addition and subtraction. A fixed learning-rate protocol crosses three hidden widths with two AdamW weight-decay settings and three initialization seeds, producing 36 completed training records. Memorization and generalization are defined by separate sustained accuracy thresholds. Within 20,000 updates, 30 records attain memorization but none attains generalization. Wider networks fit earlier without decay and fit where the narrowest networks fail with positive decay; these differences do not establish faster grokking. An audit of the reported endpoint-substituted lag shows that its positive 500-update width contrast, including a degenerate seed interval, follows from fitting times and censoring rather than observed generalization. The evidence supports a finite-horizon separation between width-dependent fitting and unobserved generalization, while leaving the eventual dependence of grokking time on model size unidentified.


\end{abstract}

\section{Introduction}

Small algorithmic datasets offer an unusually transparent setting for investigating generalization: the target rule is known, every possible input can be enumerated, and training performance can be separated from performance on unseen inputs. Yet fitting such data need not reveal when a network learns the underlying operation. Grokking names the striking case in which generalization emerges long after the training data have been fitted \citep{Power2022GrokkingGB}. This separation raises a basic question about scale: does a larger network change the arrival of generalization, or simply change the point from which the delay is measured?

The distinction matters because a delay is a difference between event times. Earlier memorization can increase a measured delay even if generalization is unchanged. Conversely, replacing an unobserved generalization event with the training endpoint can produce an apparently precise contrast without any generalization event having occurred. A study of model size therefore needs to report fitting, generalization, and non-attainment separately, rather than infer one from another. Training accuracy alone is particularly inadequate as a proxy for learning an algorithm; the broader distinction between finite-sample fitting and useful generalization is well established \citep{Zhang2017Rethinking}.

We examine a controlled width-by-decay grid for a single fixed optimization recipe on addition and subtraction modulo 97. The models are one-hidden-layer ReLU networks with concatenated one-hot inputs. Hidden width varies over 16, 64, and 256; all other architectural choices are fixed. Two decay settings and three initialization seeds give 36 training records. Our working explanation is deliberately limited: width may remove a fitting bottleneck without making generalization observable within the same computational horizon. A stronger claim, that width changes an eventual generalization clock, requires events that this study does not observe.




The results make this separation concrete. All wider networks attain sustained memorization at the first noninitial checkpoint. Narrow networks fit later without decay and do not attain memorization with positive decay. Nevertheless, no condition reaches sustained held-out accuracy of 95\% within 20,000 updates. Thus, the observed size dependence is a fitting result, not an estimate of the size dependence of grokking time.


Our contributions are an explicit finite-horizon width comparison across related modular operations, a complete seed-level account of fitting and generalization non-attainment, and an algebraic audit of an endpoint-substituted lag statistic. We show why a nonzero width contrast and a zero-width seed interval can coexist with no observed generalization. These findings delimit what the evaluated configuration establishes; they neither rule out later grokking nor choose among proposed neural mechanisms.



\begin{figure}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/study_overview.png}
  \caption{Study design and observation boundary. Addition and subtraction modulo 97 are evaluated under a shared fixed-rate MLP protocol crossing three hidden widths, two weight-decay settings, and three initialization seeds. Memorization requires training accuracy of at least 99\%; generalization requires held-out accuracy of at least 95\%, each for three consecutive checkpoints. Non-attainment at 20,000 updates is not a measured generalization delay. The diagram summarizes the design, not a proposed neural circuit.}
  \label{fig:overview}
  
  
\end{figure}

\section{Related Work}

\paragraph{Grokking and candidate explanations.}
\citet{Power2022GrokkingGB} establish delayed generalization on small algorithmically generated datasets and describe its dependence on dataset size. Our experiment uses this setting to distinguish finite-budget fitting from generalization-event timing; it is not a replication of a particular delayed-generalization trajectory. \citet{Liu2023Omnigrok} relate grokking to training and test loss landscapes as a function of weight norm and demonstrate its presence beyond algorithmic data. \citet{Varma2023ExplainingGT} propose competition between faster memorizing solutions and more norm-efficient generalizing solutions. \citet{Kumar2024LazyRich} analyze a transition from lazy to feature-learning dynamics, including a two-layer polynomial-regression setting. These explanations motivate keeping optimization, regularization, and representation effects distinct. Our recorded norms and losses do not measure circuit efficiency or a lazy-to-rich transition, and cannot discriminate these accounts.

\paragraph{Capacity and generalization need not move together.}
\citet{Zhang2017Rethinking} demonstrate that fitting training labels and explaining generalization are different problems. \citet{Nakkiran2020DoubleDescent} show that increasing model size or training duration need not yield monotone test performance. \citet{Davies2023Unifying} propose a common pattern-learning-speed perspective on grokking and double descent, including variation in capacity. This context cautions against treating a width effect on training accuracy as sufficient evidence about held-out learning. Our grid is too sparse, and its accuracies too uniformly low, to establish a double-descent curve or a general capacity law.

\paragraph{Regularization and the role of the learning rate.}
AdamW decouples weight decay from the loss-gradient update \citep{Loshchilov2017DecoupledWD}. However, its per-update parameter shrinkage still depends on the learning rate used in that update. We therefore compare decay arms under one shared constant rate rather than interpret a change in the learning-rate recipe as a clean intervention on decay alone. The literature discussion is restricted to exact, permitted starter sources; we make no exhaustive priority or novelty claim from this restricted coverage.

\section{Method}
\label{sec:method}

\subsection{Problem, Data, and Evaluation Target}

For a pair $(a,b)\in\{0,\ldots,p-1\}^2$, the target is either $(a+b)\bmod p$ or $(a-b)\bmod p$, with $p=97$. Each operation has $p^2=9,409$ possible ordered pairs. The final evaluation uses a deterministic subset of 4,705 pairs for each operation, with 1,411 training pairs and 3,294 held-out pairs. Thus the training set is approximately 30\% of the retained subset, not 30\% of the entire operation table; it covers approximately 15\% of all possible inputs. Addition and subtraction use independently constructed operation-specific partitions.




The partition is reproducible without downloading data. Each input and operation are encoded in canonical JSON, normalized, and hashed. Sorting the hashes separates the development subset from the final subset. A second hash ordering with a fixed training prefix assigns the training portion within the final subset. The split is fixed across initialization seeds and widths. Consequently, seed variability measures training-initialization variability on a fixed split, not uncertainty over fresh data partitions. The held-out set is used for recording performance, not for gradient updates. Appendix~\ref{app:construction} specifies the construction and readable source locations.



We report both operations rather than treating subtraction as an unseen transfer task. Each network is independently trained from scratch on its own operation. The shared architecture and optimization recipe permit a condition-specific replication of the width comparison, but not a claim of cross-task representation transfer.



\subsection{Working Explanation and Falsifiable Predictions}

The working explanation separates \emph{fitting capacity under the chosen optimizer} from \emph{learning a held-out algorithm}. Increasing width can make the finite training table easier to fit without supplying evidence that the network acquires the arithmetic rule. In a regularized setting, the fitting requirement may become more demanding, so that the narrowest network no longer attains the same training criterion even though wider networks do. This is an explanation of operational fitting behavior, not a claim that parameter count alone determines representational capacity.

The corresponding finite-horizon predictions are explicit. At fixed decay, wider networks should attain the training criterion no later than the narrowest model, or attain it where the narrowest does not. If increased width is sufficient to reveal delayed generalization in this protocol, at least one wider condition should additionally cross the held-out criterion within the budget. The former prediction can be checked using fitting events; the latter can be falsified for this particular horizon. An eventual equality, ordering, or equivalence of generalization times cannot be tested unless those times are observed or otherwise bounded more informatively. These are interpretive predictions for the retained design, not a claim of preregistration or an independent confirmatory test.

\subsection{Width and Decay Comparisons}

The input vector is $x=[e_a;e_b]\in\mathbb{R}^{194}$, a concatenation of two one-hot encodings. The classifier is
\begin{equation}
 f_\theta(a,b)=W_2\operatorname{ReLU}(W_1x+b_1)+b_2\in\mathbb{R}^{97}.
\end{equation}
The hidden width $w\in\{16,64,256\}$ gives $292w+97$ trainable parameters: 4,769, 18,785, and 74,849, respectively. Both linear layers have biases. The implementation uses the default PyTorch linear-layer initialization without a width-specific logit-scale calibration. Therefore, the comparison holds the layer family fixed but does not isolate width from all initialization-scale effects.



Each condition minimizes full-batch cross-entropy with AdamW. The fixed learning rate is $\eta=0.01$ throughout training; weight decay is $\lambda\in\{0,1\}$, with optimizer coefficients $(0.9,0.999)$ and numerical constant $10^{-8}$. All model parameters are passed to the same optimizer without separate bias exclusions. The recipe controller exposes only a bounded open-loop schedule and receives no training metrics. Its evaluated constant-rate setting is identical across operations, widths, decays, and seeds. The frozen controller and evaluator, rather than proposal descriptions, define the implemented method.



For constant $\eta$, the multiplicative shrinkage contribution of AdamW alone is $(1-\eta\lambda)^t$ after $t$ updates. This algebra explains why changing a learning-rate recipe would change both gradient updates and accumulated shrinkage. It does not predict the norm or accuracy of the trained network, whose gradient contributions are not removed. We do not compare the fixed recipe empirically against the original lower-rate configuration because no matched final evaluation of that configuration is retained. Nor do we reinterpret development scores as final-task measurements.



\subsection{Training Protocol and Sustained Events}

The evaluation crosses two operations, three widths, two decay values, and seeds 1009, 2027, and 3037. Training runs for $H=20,000$ full-batch updates, with an initial measurement and measurements every 500 updates. The worker uses deterministic PyTorch algorithms, one compute thread, and one interoperation thread. Each condition resets the model and optimizer; no weights are transferred between conditions. The environment specifies NumPy 2.1.3 and PyTorch 2.5.1+cpu. Source evidence, dependencies, and output-to-script mappings are included with the supplementary material.




Let $A_{\mathrm{tr}}(t)$ and $A_{\mathrm{ho}}(t)$ denote checkpoint accuracies. We define $\TM$ as the first checkpoint whose training accuracy and next two checkpoint accuracies all reach 99\%. Likewise, $\TG$ uses a held-out threshold of 95\%. A recorded crossing is timestamped at the start of the sustained sequence, although it is confirmed only after observing the following checkpoints. Events near the endpoint without sufficient confirming measurements do not satisfy the rule. These operational event times are checkpoint-resolved, not continuous measurements of the underlying transition.



Late-window accuracy averages the final five checkpoints, from 18,000 through 20,000 updates. It is a descriptive endpoint summary and is not interchangeable with either sustained-event criterion. We preserve all completed records, including fitting failures and held-out non-attainment. All 36 records complete, so the results contain neither missing trajectories nor a denominator restricted to fitting-capable models. No new training is performed for this paper; the figures and tables recompute summaries from the sealed final observations.



\subsection{Capped Lag and Statistical Reporting}
\label{sec:lag}

To audit the retained lag summary, we reproduce its exact definition:
\begin{equation}
\LH=\begin{cases}
H,&\TM\text{ unobserved},\\
\max\{0,\min(\TG,H)-\TM\},&\TM\text{ observed},
\end{cases}
\label{eq:lag}
\end{equation}
where an unobserved $\TG$ is replaced by $H$. This is an administratively capped statistic, not an uncensored grokking time. In particular, assigning $H$ when memorization is unobserved does not define a genuine post-memorization waiting time. When memorization is observed but generalization is not, $H-\TM$ is the observed waiting period without an attained event.


For seed $s$ and decay $\lambda$, the paired extreme-width contrast averages over operations:
\begin{equation}
D_s(\lambda)=\frac{1}{2}\sum_{o\in\{+, -\}}
\big[\LH(o,16,\lambda,s)-\LH(o,256,\lambda,s)\big].
\label{eq:contrast}
\end{equation}
We reproduce the supplied mean and Student-$t$ interval across the three paired seed contrasts, as well as the difference of mean contrasts between decay arms. All individual seeds are shown in the plots, and descriptive means and sample standard deviations are used where appropriate. The checkpoints, operations, and decay arms are not treated as independent replications. With no generalization events, we do not estimate a distribution of eventual generalization times or infer a population event probability from the pooled 36 conditions.



\section{Results}

\subsection{Width Changes Fitting, but Generalization Is Not Observed}

Table~\ref{tab:events} reports every condition's seed-specific memorization times. With zero decay, all networks memorize: width 16 reaches the sustained criterion at 1,000--1,500 updates, whereas widths 64 and 256 do so at 500 updates in both operations and every seed. The wider conditions are indistinguishable at this checkpoint resolution. Their common event timestamp means they satisfy the rule from the first noninitial checkpoint onward, not that their underlying fitting transitions occur at exactly the same update.


Positive decay changes the narrowest condition qualitatively. All six width-16 records fail to attain sustained memorization by the horizon; every width-64 and width-256 record still attains it at 500 updates. Across the entire grid, 30 of 36 records memorize, but no record attains sustained generalization. There are therefore no observed delayed-generalization events, including among the 30 fitting-capable records. The completed evaluation supports a negative finite-horizon result, rather than a comparison of observed grokking times.



\begin{table}[t]
  \centering
  \small
  \input{tables/events.tex}
  \caption{Sustained memorization times in updates, with generalization attainment shown separately. A dash denotes no sustained memorization by 20,000 updates, not a missing or unfinished record. The final column counts observed sustained generalization events across the three seeds. Every condition has a complete trajectory.}
  \label{tab:events}
  
\end{table}

Figure~\ref{fig:outcomes} complements the event table with late-window accuracies. Without decay, all training accuracies average 100\%. With positive decay, the width-16 averages are 56.664\% for addition and 55.625\% for subtraction; all wider conditions average 100\%. Thus the narrow-model non-attainment is not merely a transient miss of a threshold close to perfect fitting. It is accompanied by much lower training accuracy in the recorded late window.



\begin{figure}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/width_decay_outcomes.pdf}
  \caption{Late-window fitting and held-out accuracy separate sharply. Panels (a,b) show training accuracy; (c,d) show held-out accuracy, with a separate shared scale for each row. Values average the final five checkpoints. Colors encode decay; circles, squares, and triangles identify seeds 1009, 2027, and 3037, respectively. Short horizontal bars are condition means, not uncertainty intervals. The training axis is restricted to expose the narrow positive-decay fitting deficit; held-out accuracy remains far below the sustained generalization threshold in every condition.}
  \label{fig:outcomes}
  
\end{figure}

\subsection{Held-Out Accuracy Does Not Track Earlier Fitting}

The zero-decay width-16 models have mean late-window held-out accuracies of $0.482\pm0.061$\% for addition and $0.407\pm0.006$\% for subtraction, where the uncertainty shown is the sample standard deviation across initialization seeds. At width 64 these means fall to 0.047\% and 0.026\%, respectively; at width 256 they are zero in all seeds. These measurements contradict a monotone improvement in endpoint accuracy with width for this decay arm. They do not establish a general law that larger models generalize worse.



With positive decay, mean held-out accuracies for widths 16, 64, and 256 are 0.219\%, 0.091\%, and 0.091\% on addition, and 0.178\%, 0.053\%, and 0.117\% on subtraction. The variation is not a common monotone width trend across arms. More importantly, none of these small differences approaches the generalization criterion. The evidence supports a distinction between fitting attainment and useful held-out learning, not a superiority claim for a particular width. Full seed values appear in the supplement rather than being hidden behind condition averages.



The mean late-window held-out accuracy over all conditions is 0.142515\%. The stored reference predictors average 0.865209\% for a training-label-mode predictor, 0.865209\% for a lookup-with-mode-fallback predictor, 0.949201\% for label-deranged prediction alignment, and 1.050732\% for the initialized network. The trained networks' mean gap to these four references is $-0.790073$ percentage points. This is a descriptive comparison to these particular references, not a test against independent random-label training. The lookup reference necessarily duplicates the mode predictor on disjoint held-out input pairs, so the reference average does not represent four independent controls.




\subsection{Loss and Norm Diagnostics Qualify the Accuracy Comparison}

Endpoint loss provides a complementary view of the poor held-out predictions. On addition at width 16, mean final-checkpoint held-out cross-entropy is 339.459 without decay and 8.390 with positive decay. At width 256, the corresponding values are 89.877 and 8.627. Thus, a decay setting can substantially reduce held-out cross-entropy without producing sustained generalization, and its ranking by loss need not match its ranking by top-one accuracy. These are comparisons between the evaluated configurations, not evidence that reduced loss must precede an eventual transition. The full endpoint table is provided in the supplement.



The initial parameter norm also differs across widths: averaging the three seeds gives 6.288, 7.383, and 10.904 for widths 16, 64, and 256. These norms are the same across operations and decay arms at a fixed width and seed, because initialization is reset before each condition. This check supports comparability of decay arms at initialization while making clear that widths are not norm-matched. An initial norm difference is not itself a difference in functional logit scale, and neither quantity establishes a particular learning regime. The retained diagnostics therefore sharpen the implementation boundary without resolving the mechanism.



\subsection{A Precise Capped-Lag Contrast Without Generalization Events}

Figure~\ref{fig:censoring} shows the capped statistic rather than labeling it as observed delay. Since all generalization events are unobserved, every fitted record has $\LH=H-\TM$. Under positive decay, width 16 receives the special non-memorization value 20,000, while width 256 receives $20,000-500=19,500$. Their paired contrast is therefore 500 updates for every seed and both operations. The supplied three-seed interval is $[500,500]$ updates because these recorded contrasts have zero sample variation. Its degeneracy reflects the endpoint rule and checkpoint-aligned fitting events, not precise knowledge of generalization time.





\begin{figure}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/censoring_audit.pdf}
  \caption{Administrative endpoint substitution determines the displayed lag. Circles denote addition and squares subtraction; horizontal bars are condition means. Filled symbols indicate observed memorization; hollow symbols indicate memorization non-attainment. All generalization events are unobserved. The focused vertical range does not begin at zero. In panel (a), earlier fitting at larger widths increases $H-\TM$. In panel (b), the hollow width-16 observations instead receive the special value $H$, creating a positive narrow-minus-wide contrast without any observed generalization event.}
  \label{fig:censoring}
  
\end{figure}

Without decay, the three operation-averaged narrow-minus-wide contrasts are $-750$, $-500$, and $-500$ updates, averaging $-583.333$. Here every model memorizes, and the wider models have \emph{larger} capped lags precisely because they fit earlier. The difference between the decay-arm mean contrasts is 1,083.333 updates. The overall capped-lag mean is 19,486.111 updates. Neither quantity estimates a difference in observed grokking times. A sign change across arms is possible simply because the special rule for missing memorization replaces the ordinary post-fitting waiting period.




This audit also limits the working explanation. The fitting prediction is borne out within the measured grid. The proposition that wider networks suffice to reveal delayed generalization within this budget is not supported. However, the data cannot establish equal eventual generalization times across widths, nor that any of the fitted models will ever generalize. Administrative censoring preserves a finite observation window; it does not manufacture the missing event.

\section{Discussion and Limitations}

\paragraph{What the width comparison identifies.}
The cleanest result is conditional: under the same representation, optimizer recipe, data partition, and update budget, changing width changes fitting behavior without yielding a generalization event. The decay comparison likewise identifies differences between evaluated configurations, not an isolated mechanism of representational capacity. Default initialization, parameterization, and optimization interact with width. A claim that width alone changes the efficiency of a memorizing circuit would require additional measurements and controls that are not present.

\paragraph{Why this is not a generalization-time law.}
The sustained definition prevents a transient checkpoint excursion from being reported as stable attainment, but its temporal resolution is limited and its required confirmation shortens the window for detectable late events. Extending training could change the qualitative outcome. Conversely, continued low held-out accuracy could persist without contradiction. The retained trajectories give neither outcome. The capped statistic is useful only when read alongside the two event indicators; reporting it alone would erase the distinction between failing to fit and fitting without generalization.

\paragraph{Mechanistic explanations remain open.}
There are no independently trained random-label controls, matched initial logit-scale interventions, norm-matched comparisons, circuit decompositions, or kernel/feature-learning measurements. Weight norm and loss are recorded, but they do not identify which of the candidate explanations in related work applies. In particular, the absence of an observed transition does not show that norm efficiency, lazy-to-rich learning, or a delayed representation change is absent. Nor can the poor endpoint accuracy identify a unique failure cause. We therefore do not attribute the result to an unmeasured circuit or diagnose an adaptivity or validity failure from performance alone.



\paragraph{Update budget is not compute matching.}
All conditions receive the same number of full-batch optimizer updates and the same checkpoint schedule, making the event comparison interpretable in update units. Equal updates do not imply equal arithmetic work or equal wall-clock cost across widths. The retained timing fields summarize seed-level evaluations rather than isolated, hardware-controlled per-width throughput. Consequently, earlier fitting in update units is not a measured speedup per CPU second or a resource-efficiency claim. The study also fixes one learning-rate recipe instead of tuning a separate optimum for each width. Its negative generalization result applies to that shared recipe, not to the best achievable performance of every model size.



\paragraph{Coverage and uncertainty.}
The empirical scope is one modulus, one input representation, one hidden-layer family, three widths, two decay values, three initialization seeds, and a fixed split per operation. The operations are closely related, not a representative distribution of algorithmic tasks. The small seed count limits uncertainty assessment; the paired interval pertains only to the implemented capped summary and does not incorporate split variation or hyperparameter selection. We do not pool checkpoint measurements into extra replications, infer confidence from overlapping seed markers, or interpret a zero-width interval as robustness across unseen settings. Reusing a seed aligns the random-number initialization procedure, but differently shaped networks do not have identical initial functions. Likewise, the two operations share an algebraic family while having different fixed input partitions. Pairing improves the definition of a conditional comparison; it does not turn those observations into independent draws from a broad population of models or tasks.


\paragraph{Configuration and evidence boundaries.}
The final factorial evaluates one fixed learning-rate recipe. The absence of a matched final result for the original lower-rate configuration precludes a final-baseline improvement claim. The recorded final evaluation completed and was accepted under its specified criteria. That acceptance certifies neither generalization nor a neural mechanism, and the retained metadata does not provide a comprehensive integrity or adaptivity audit. Claims are therefore tied to inspectable evaluator observations and readable implementation snapshots rather than to acceptance labels or hashes alone.





\section{Conclusion}

Model size can change the onset and attainability of training-set fitting without producing an observed generalization transition. In the evaluated modular addition and subtraction grid, wider fixed-rate ReLU networks memorize earlier without decay and overcome the narrowest models' fitting deficit with positive decay. Nevertheless, none of the 36 complete records reaches sustained generalization by 20,000 updates. The supported conclusion is a finite-horizon separation between fitting and held-out learning, not a claim that scale accelerates, prevents, or leaves unchanged eventual grokking.


An endpoint-s

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}

\subsection{Data Construction and Implementation Evidence}
\label{app:construction}

The source bundle contains the evaluator that owns training, the evaluated learning-rate controller, the retained final data partition, dependencies, and final observation records. The relevant locations are listed below so that implementation claims can be checked directly, rather than inferred from provenance hashes.
\begin{itemize}
\item \texttt{source\_evidence/evaluate\_final.py:588}: canonical input encoding, normalization, hash ordering, partition selection, and operation labels.
\item \texttt{source\_evidence/evaluate\_final.py:721}: sustained-event extraction and endpoint substitution; line 746 defines paired aggregation and its interval.
\item \texttt{source\_evidence/evaluate\_final.py:789}: deterministic training worker; line 802 constructs features; line 828 defines the network; line 846 constructs AdamW; line 858 begins full-batch optimization.
\item \texttt{source\_evidence/controller/src/program.py:46}: reset, shared recipe, and schedule responses. The specification identifies the entrypoint within the adjacent source directory.
\end{itemize}



For each operation, enumerate all ordered pairs and construct the JSON object with keys \texttt{operation}, \texttt{p}, \texttt{a}, and \texttt{b} in that order, using compact separators. Apply NFKC normalization and whitespace canonicalization, then SHA-256. Sort tuples of the digest and input integers. The final partition retains the portion starting at integer index $\lfloor p^2/2\rfloor$. Reorder it by the SHA-256 digest of the string \texttt{train-v1:} concatenated with the original hex digest. The first $\lfloor 0.3n\rfloor$ entries train the model and the remainder are held out. The stored resource is \texttt{source\_evidence/resources/final/benchmark.json}. No external dataset, account, or license-controlled data is needed.



The evaluator file and observation-file hashes match their counterparts in the final metadata. These checks establish consistency of the supplied artifacts, not the substantive correctness of every implementation claim. The readable source establishes the architecture and measurements. The final evidence registry retains an unverified diagnostics-trust designation; the paper does not upgrade that designation to an independent audit result.




\subsection{Complete Seed-Level Observations}

The following table includes all completed conditions. Train and held-out accuracies average the final five checkpoints. Generalization is unobserved in every row; the $\LH$ column is therefore a capped statistic, not an observed grokking time. All values are regenerated from retained final records by \texttt{build\_artifacts.py}. The main event table retains the evidence necessary for the central conclusion; this expanded view preserves seed variation and endpoint magnitudes.

\begingroup
\small

\begin{longtable}{llrrrrrr}
\toprule
Op. & $\lambda$ & Width & Seed & $T_M$ & $L_H$ & Train (\%) & Held-out (\%) \\
\midrule\endhead
add. & 0 & 16 & 1009 & 1500 & 18500 & 100.000 & 0.474 \\
add. & 0 & 16 & 2027 & 1000 & 19000 & 100.000 & 0.425 \\
add. & 0 & 16 & 3037 & 1000 & 19000 & 100.000 & 0.546 \\
add. & 0 & 64 & 1009 & 500 & 19500 & 100.000 & 0.043 \\
add. & 0 & 64 & 2027 & 500 & 19500 & 100.000 & 0.079 \\
add. & 0 & 64 & 3037 & 500 & 19500 & 100.000 & 0.018 \\
add. & 0 & 256 & 1009 & 500 & 19500 & 100.000 & 0.000 \\
add. & 0 & 256 & 2027 & 500 & 19500 & 100.000 & 0.000 \\
add. & 0 & 256 & 3037 & 500 & 19500 & 100.000 & 0.000 \\
add. & 1 & 16 & 1009 & \textemdash & 20000 & 57.094 & 0.200 \\
add. & 1 & 16 & 2027 & \textemdash & 20000 & 57.293 & 0.249 \\
add. & 1 & 16 & 3037 & \textemdash & 20000 & 55.606 & 0.206 \\
add. & 1 & 64 & 1009 & 500 & 19500 & 100.000 & 0.091 \\
add. & 1 & 64 & 2027 & 500 & 19500 & 100.000 & 0.079 \\
add. & 1 & 64 & 3037 & 500 & 19500 & 100.000 & 0.103 \\
add. & 1 & 256 & 1009 & 500 & 19500 & 100.000 & 0.061 \\
add. & 1 & 256 & 2027 & 500 & 19500 & 100.000 & 0.109 \\
add. & 1 & 256 & 3037 & 500 & 19500 & 100.000 & 0.103 \\
sub. & 0 & 16 & 1009 & 1000 & 19000 & 100.000 & 0.407 \\
sub. & 0 & 16 & 2027 & 1000 & 19000 & 100.000 & 0.413 \\
sub. & 0 & 16 & 3037 & 1000 & 19000 & 100.000 & 0.401 \\
sub. & 0 & 64 & 1009 & 500 & 19500 & 100.000 & 0.030 \\
sub. & 0 & 64 & 2027 & 500 & 19500 & 100.000 & 0.000 \\
sub. & 0 & 64 & 3037 & 500 & 19500 & 100.000 & 0.049 \\
sub. & 0 & 256 & 1009 & 500 & 19500 & 100.000 & 0.000 \\
sub. & 0 & 256 & 2027 & 500 & 19500 & 100.000 & 0.000 \\
sub. & 0 & 256 & 3037 & 500 & 19500 & 100.000 & 0.000 \\
sub. & 1 & 16 & 1009 & \textemdash & 20000 & 55.507 & 0.206 \\
sub. & 1 & 16 & 2027 & \textemdash & 20000 & 54.642 & 0.194 \\
sub. & 1 & 16 & 3037 & \textemdash & 20000 & 56.726 & 0.134 \\
sub. & 1 & 64 & 1009 & 500 & 19500 & 100.000 & 0.055 \\
sub. & 1 & 64 & 2027 & 500 & 19500 & 100.000 & 0.079 \\
sub. & 1 & 64 & 3037 & 500 & 19500 & 100.000 & 0.024 \\
sub. & 1 & 256 & 1009 & 500 & 19500 & 100.000 & 0.115 \\
sub. & 1 & 256 & 2027 & 500 & 19500 & 100.000 & 0.061 \\
sub. & 1 & 256 & 3037 & 500 & 19500 & 100.000 & 0.176 \\
\bottomrule
\end{longtable}
\endgroup

\subsection{Reference Predictors and Descriptive Diagnostics}

The training-label-mode reference predicts the most frequent training label. The lookup reference uses an exact input-pair lookup with that mode as its fallback. Because no held-out input pair occurs in training, every held-out prediction uses the fallback. These references coincide by construction; their equality is not evidence of two independent baselines agreeing. The initialized-network reference is a frozen copy of the same initialized classifier. The deranged-alignment reference permutes current model logits across held-out examples so that their paired labels differ; it does not train another network on randomized labels. Its value can change as the trained logits change. These definitions are implemented at \texttt{source\_evidence/evaluate\_final.py:805} and \texttt{source\_evidence/evaluate\_final.py:831}.


Table~\ref{tab:diagnostics} reports endpoint cross-entropy and Euclidean parameter norm averaged over seeds. These are final-checkpoint quantities, not late-window averages, and they are descriptive only. In particular, large held-out loss does not quantify a memorizing circuit's efficiency or identify an eventual generalization pathway. The norm includes all trainable weights and biases, exactly as in the evaluator.


\begin{table}[h]
\centering
\small

\begin{tabular}{llrrrr}
\toprule
Op. & $\lambda$ & Width & Train CE & Held-out CE & Weight norm \\
\midrule
Addition & 0 & 16 & 4.08e-07 & 339 & 477 \\
Addition & 0 & 64 & 1.03e-07 & 55.6 & 224 \\
Addition & 0 & 256 & 4.3e-06 & 89.9 & 375 \\
Addition & 1 & 16 & 1.88 & 8.39 & 57.2 \\
Addition & 1 & 64 & 0.00183 & 13.3 & 106 \\
Addition & 1 & 256 & 1.36e-05 & 8.63 & 113 \\
Subtraction & 0 & 16 & 4.25e-07 & 358 & 485 \\
Subtraction & 0 & 64 & 1.05e-07 & 55.8 & 224 \\
Subtraction & 0 & 256 & 4.75e-06 & 91.1 & 375 \\
Subtraction & 1 & 16 & 1.93 & 8.14 & 56.2 \\
Subtraction & 1 & 64 & 0.0019 & 13.3 & 106 \\
Subtraction & 1 & 256 & 1.37e-05 & 8.29 & 113 \\
\bottomrule
\end{tabular}
\caption{Final-checkpoint diagnostics, averaged over the three initialization seeds. CE denotes cross-entropy. No causal mechanism is inferred from these summaries.}
\label{tab:diagnostics}

\end{table}

\subsection{Capped-Lag Calculation and Reproduction Map}

The event extractor scans possible three-checkpoint windows in increasing time order. It returns the first window's start if every accuracy exceeds the corresponding threshold, and returns no event otherwise. Applying Equation~\ref{eq:lag} to these outputs reproduces the stored per-record lag. The final comparison uses the paired, operation-averaged $D_s(1)$ values of Equation~\ref{eq:contrast}. For three seeds, the supplied interval is
\begin{equation}
\left[\overline D-4.30265273\,s_D/\sqrt{3},\;
\overline D+4.30265273\,s_D/\sqrt{3}\right],
\end{equation}
clipped to the range $[-H,H]$. Here $s_D$ is the sample standard deviation across the three seed contrasts. Since all positive-decay contrasts equal 500, $s_D=0$. This interval construction is applied to the capped statistic only. It supplies no interval for an unobserved generalization event.




The original training environment pins \texttt{numpy==2.1.3} and \texttt{torch==2.5.1+cpu}. The plotting environment and exact commands are recorded in \texttt{REPRODUCIBILITY.md}; \texttt{analysis/plotting\_requirements.txt} records the versions used for this manuscript. Running \texttt{python build\_artifacts.py} replays only analysis of stored measurements, not neural training. It produces the event table, complete observation table, diagnostic table, both quantitative figures, and \texttt{analysis/derived\_results.json}. The overview is supplied separately by the figure-rendering workflow. Its placeholder is not an empirical result.




The stored durations for the three seed evaluations are 786.393, 777.546, and 786.875 seconds; each seed includes the full condition grid. They describe the retained execution, not a portable runtime guarantee. The evaluator relies on an external RPC execution context for the controller. The standalone training command for that broker is not part of the supplied bundle, so we do not present the evaluator's command-line flags as a complete independent reproduction command. The code and data define the neural computation, while fully replaying the original execution wrapper requires that additional infrastructure. No training or final evaluation is rerun in preparing this manuscript.



\subsection{Literature Access Boundary}

Only exact starter-literature identities approved by the reference plan are cited. Their titles, authors, and abstracts were retrieved directly from their arXiv pages and saved in \texttt{literature/}. Citation graphs, recommendations, broad topic searches, and the prohibited target literature were not used. Existing retrieval metadata included off-target entries, which were not used as substantive sources. No prohibited paper was identified or intentionally consulted, and no claim of an exhaustive literature review is made. The bibliography is limited to the consulted approved sources rather than padded with unrelated metadata.



\subsection{LLM Usage}

LLMs contributed to research proposal generation, the bounded learning-rate-controller implementation, reference-query planning, selection of the finite-horizon framing, analysis-code construction, manuscript drafting, and grounding checks. The retained controller documentation distinguishes the broader proposed controls from the much narrower implemented interface. Neural training, checkpoints, and final numerical measurements were produced by the evaluator-owned training computation, not supplied by narrative generation. The present writing step reuses those measurements and does not create new experimental outcomes. The paper does not claim undocumented human review or an independent mechanistic validation. These roles are documented by the controller scope note, the reference plan, the writing strategy, and the analysis source included in the artifact bundle.
```
