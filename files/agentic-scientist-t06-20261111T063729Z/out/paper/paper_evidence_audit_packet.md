# Agentic evidence audit packet

- generated_at: `2026-11-11T08:53:50.743259+00:00`
- paper_dir: `work/results/t06/claude/20261111_064241/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261111_075327-paper_evidence_audit_round_8-kjlnme54/workspace`

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
    "anchored_references": 45,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 61,
    "resolved_references": 23,
    "total_references": 68
  },
  "ok": true,
  "pdf_path": "work/results/t06/claude/20261111_064241/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 45,
    "dangling_references": 0,
    "manifests_checked": 6,
    "resolved_references": 23,
    "total_references": 68
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "claim": "Held-out crowd table has 135,630 rows, 52 models, cap 2,713; NBA table has 12,900 rows, 30 teams, cap 258.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Held-out crowd table built from 135,634 raw rows after removing 2 content-overlap rows and 2 rare-participant rows (652 prompt-only overlaps kept); source: derived/task_meta/final_meta.json (copy, name lists removed).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Development tables: Arena 55k 57,477 rows, 64 models (cap 1,150 derived); MT-Bench human 3,355 rows, 6 models (cap 68 derived); sizes from derived/task_meta/search_meta.json (copy, name lists removed).",
      "source_ids": [
        "study.search_score"
      ]
    },
    {
      "claim": "Recorded removal budgets of the studied configuration: crowd top 62, crowd mid 4 rows; NBA top 62, NBA mid 8 rows; all four flipped within the cap.",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.flip_rate"
      ]
    },
    {
      "claim": "Budgets as percent of all comparisons (derived k/N): 0.046%, 0.003%, 0.48%, 0.062%.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Both held-out episodes (seeds 21 and 22) returned identical per-case budgets; the studied configuration's recorded durations were 4.45 s and 4.51 s per episode (hardware not recorded).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Held-out family scores 0.988 (crowd) and 0.864 (sports); overall 0.926; mean k/cap 0.074; flip rate 1.0.",
      "source_ids": [
        "final.metric.combined_score",
        "final.metric.score_crowd",
        "final.metric.score_sports",
        "final.metric.mean_budget_fraction",
        "final.metric.flip_rate"
      ]
    },
    {
      "claim": "Random-removal reference score 0.041 and influence-only reference score 0.926; the latter equals the held-out overall score.",
      "source_ids": [
        "final.metric.reference_random_score",
        "final.metric.reference_influence_score",
        "final.metric.combined_score"
      ]
    },
    {
      "claim": "Random removal flipped 0/20 draws for F1, F3, F4 and 6/20 for F2 (and 7/20 for control F5, 0/20 for F6).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "The evaluator-recorded influence-only reference (B2) budgets equal the studied configuration's in all four real cases and both permutation controls (62, 4, 62, 8; 2, 10); B2's construction is unverified and no conclusion depends on it.",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.reference_influence_score"
      ]
    },
    {
      "claim": "Opponent-targeted (B3) budgets: 650, 6, 88, 12 rows for F1 to F4 (ratios to studied 10.5, 1.5, 1.4, 1.5).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Top-pair share ratio sports/crowd is 10.5 and mid-pair ratio is 21.0; the top-pair ratio equals the table-size ratio 135,630/12,900.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Mean comparisons per participant (2N/M) are 5,217 (crowd) and 860 (sports); 62 rows are 1.2% and 7.2% of that (about 6x); mid budgets 0.077% and 0.93% (about 12x); sports has the larger share under both normalisers (10.5x and 21.0x under k/N).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Sports top-pair budget uses 24% of its 258-row cap.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Empty-set control flips no case; cross-table copy control recorded 0 flips in 2 trials; no inference is drawn from the copy control because its construction is not documented.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Permutation controls: moved fraction 0.660 vs expected 0.662 (crowd), 0.498 vs 0.500 (sports); rating-spread ratios 0.088 and 0.160; non-vacuous.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Permuted top pairs flipped with 2 rows (crowd) and 10 rows (sports) versus 62 on real tables; control gap +0.112.",
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.control_gap_permuted_minus_real"
      ]
    },
    {
      "claim": "Held-out evaluation status completed with outcome qualified and success indicator true; qualification gate criteria are not recorded in the evidence, so qualified is not read as certifying controls or validity; candidate diagnostics unverified and unused.",
      "source_ids": [
        "final.qualification.outcome",
        "final.qualification.status",
        "final.qualification.correct",
        "study.final.outcome",
        "study.final.status"
      ]
    },
    {
      "claim": "Investigation found no winner: three search configurations were scored (3 of 3, 0 unscored), each 0.4993 equal to the starting baseline 0.4993, difference 0.0; selection kind non-winner candidate.",
      "source_ids": [
        "study.search_score",
        "study.baseline_score",
        "study.search_score_delta",
        "study.attempts.scored",
        "study.attempts.total",
        "study.attempts.unscored",
        "study.investigation_outcome",
        "study.selection_kind",
        "result.total_attempts"
      ]
    },
    {
      "claim": "The starting baseline was not run on held-out tables; selected configuration equals the baseline's development score.",
      "source_ids": [
        "study.baseline_score",
        "study.search_score_delta"
      ]
    },
    {
      "citation_keys": [
        "Davidson1970OnET",
        "Davidson1977OnET",
        "Davidson1969MultivariatePC",
        "Causeur2005A2E",
        "Stern2011ModeratedPC",
        "Fageot2023GeneralizedBM",
        "Yan2025InferenceIA",
        "Yan2011GROUPEDSP",
        "Leonard1977AnAB",
        "Hussain2013BayesianIO",
        "Rizvi2026BayesianBF",
        "Butler2004TheEO",
        "Bong2021GeneralizedRF",
        "Varin2024TractableRR",
        "Vojnovi\u01072019ConvergenceRO",
        "Sawadogo2019CombiningMA",
        "Genest1999DerivingPF",
        "Selby2024PageRankAT"
      ],
      "claim": "Bradley-Terry model extensions and estimation literature described at title level (ties, order effects, multivariate, Bayesian, existence of MLE, ridge, computation).",
      "source_ids": [
        "ref.s2.3833525afb515fbf56c616b5ae5470247fc38fa5",
        "ref.s2.14b981837cc0ff653984dc44f5ae40d75a2dc938",
        "ref.s2.67d7d2cbe825822f53d16390b2fba0cd26e4a77d",
        "ref.s2.41cd421312e118caeae3f9259300550be21ea91d",
        "ref.s2.d154f6fdbc6c4458145446ab36feca0e8bb0e469",
        "ref.s2.0319308b37b124ebcfa7d88634907d87375be312",
        "ref.s2.595cd2c1e717ec18b915eacc339732f044337db9",
        "ref.s2.e9d18b11ac4797ec4e2f560b1299178e6f482393",
        "ref.s2.ca395eb7b408588749c363ff47ee158229f29c40",
        "ref.s2.0b482611ef884eae8cc1289080fb84adf19d1823",
        "ref.s2.78d49965ef1d4b47d7f0b08eb9d07d343c86f7af",
        "ref.s2.99e111177a8190622d05b23eb8c6f4ddbd6fc9b5",
        "ref.s2.53e22ad9fa53da0a1652a3fac2dc2735a55c67e4",
        "ref.s2.6fda8855b563b013548549f0a830f2e6fb3eaa7c",
        "ref.s2.039f6e7cc449919600d5e89edc35ae08681bd6a8",
        "ref.s2.5cc3e0888db681a30b4eaf6a2b0c2af7bf589f48",
        "ref.s2.9516a4bc5976cac7d08e29cc902f8909a9dbc86a",
        "ref.s2.fc41d586e02577360af0ae8a5141a5495b3d15ff"
      ]
    },
    {
      "citation_keys": [
        "Simons1999AsymptoticsWT",
        "Gao2021UncertaintyQI",
        "Makur2024MinimaxHT",
        "Morel-Balbi2025EstimationOP",
        "Li2021ThePO",
        "Defresne2025PreferenceEF"
      ],
      "claim": "Sampling-based uncertainty for BT scores and ranks, and growing-parameter asymptotics, are studied in cited work (title-level description).",
      "source_ids": [
        "ref.s2.c8b7881fa0b8f19d275ef66fd79deccd3ccac133",
        "ref.s2.b65b46292745d2301a8464eb8c50fe716086fd1e",
        "ref.s2.7c12004f442c5d7a8baa1e2fc3e38d0459077059",
        "ref.s2.930c1f02b32baa6e47106b7549a156f2eaebc8af",
        "ref.s2.ae7dcf7d85c044ea973d009fe3abb1ecd2511c70",
        "ref.s2.7c541c85ed942f67beb9629358997df6c51c94eb"
      ]
    },
    {
      "citation_keys": [
        "Broderick2020AnAF"
      ],
      "claim": "Broderick et al. propose a finite-sample robustness metric for when dropping a little data changes conclusions.",
      "source_ids": [
        "ref.s2.f4c5a3ee3ca4435f558b2ec248eb0afb501d8f12"
      ]
    },
    {
      "citation_keys": [
        "https://doi.org/10.48550/arxiv.2403.04132"
      ],
      "claim": "Chatbot Arena is a crowd-vote platform that aggregates pairwise preferences into rankings.",
      "source_ids": [
        "ref.openalex.W4392616695"
      ]
    },
    {
      "citation_keys": [
        "https://doi.org/10.48550/arxiv.1703.04730"
      ],
      "claim": "Influence-function analysis of removing a training point motivates the Newton-step row ordering.",
      "source_ids": [
        "ref.openalex.W2597603852"
      ]
    },
    {
      "citation_keys": [
        "https://doi.org/10.48550/arxiv.2501.17858"
      ],
      "claim": "Prior work (title level) studies vote-rigging strategies against Chatbot Arena and their effect on model rankings; our deletion-only setting is not compared numerically and no claim is made about which manipulations that work allows.",
      "source_ids": [
        "ref.openalex.W4406975857"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Evaluator source for comparators B1-B3 and the controls is not staged; only recorded outcomes (flip counts, budgets, moved fractions, spread ratios, copy flips) are reported and construction details are not claimed. B2 is not asserted to equal any step of the studied configuration.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Broderick2020AnAF"
      ],
      "claim": "Broderick et al. is described only as proposing a finite-sample robustness metric for when dropping a little data changes conclusions; no further characterisation is made.",
      "source_ids": [
        "ref.s2.f4c5a3ee3ca4435f558b2ec248eb0afb501d8f12"
      ]
    },
    {
      "claim": "The studied configuration's recorded top-pair budgets are the same number of rows (62) for crowd and sports tables; caps differ (2,713 vs 258); true minima are not established.",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "claim": "Random removal flipped the crowd mid pair in 6 of 20 draws; this suggests but does not establish a small rating gap (gaps not recorded).",
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The evidence registry records only total scores (0.4993) and per-episode runtimes (about 1.3 s, 2.0 s, 114 s) for the three development configurations; no per-family, per-case or per-comparator development breakdown is recorded, so no claim is made about whether MT-Bench pairs flip.",
      "source_ids": [
        "result.best_correct_score",
        "result.top_program_01",
        "result.top_program_02",
        "result.top_program_03",
        "study.search_score",
        "study.baseline_score"
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
  "downstream_study": {
    "attempt_counts": {
      "scored": 3,
      "total": 3,
      "unscored": 0
    },
    "baseline_program_dir": "work/results/t06/claude/20261111_064241/investigation/.baseline-seed-t46skijp/program_0",
    "baseline_score": 0.4993478260869565,
    "baseline_tree_sha256": "b11a7cee5ae6158c4d71c2217289afdfd49bc6143627d4c689541d79c202160d",
    "combined_score": 0.4993478260869565,
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
    "program_dir": "work/results/t06/claude/20261111_064241/downstream/program",
    "program_tree_sha256": "ac63c67bfd21b0f901315a0a27dc3f6407b9623dc6438a2a00f29a86d41b4520",
    "search_score_delta": 0.0,
    "selection_kind": "non_winner_candidate",
    "source_attempt_id": "c01_influence_rank_flip_budgets_attempt_01",
    "source_evidence": {
      "baseline": "source_evidence/downstream/baseline",
      "program": "source_evidence/downstream/program"
    },
    "source_program_dir": "work/results/t06/claude/20261111_064241/investigation/ideas/01_influence_based_rank_flip_budgets_across_evaluation_designs/program_1",
    "source_tree_sha256": "d3b3da4bfd57caf501df2af56630cb4c8c78a0705ddf30ac68c85cdf3f5bd9eb"
  },
  "final_evaluation": {
    "correct": true,
    "outcome": "qualified",
    "status": "completed"
  },
  "grounding_source_count": 33,
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
  "campaign_results_dir": "work/results/t06/claude/20261111_064241/investigation",
  "count": 52,
  "generated_at": "2026-11-11T08:10:58.646994+00:00",
  "queries": [
    "Bradley-Terry model paired comparisons maximum likelihood estimation ranking",
    "approximate maximum influence perturbation dropping small fraction of data robustness",
    "understanding black-box predictions influence functions",
    "Chatbot Arena open platform evaluating LLMs human preference",
    "judging LLM-as-a-judge MT-Bench human expert pairwise judgments",
    "improving model ranking Chatbot Arena vote rigging",
    "leaderboard illusion Chatbot Arena evaluation practices sampling private testing",
    "adversarial manipulation robustness rank aggregation from pairwise comparisons",
    "Elo rating system relation to Bradley-Terry sports game outcomes",
    "statistical inference uncertainty ranking from pairwise comparisons confidence intervals bootstrap",
    "Chatbot Arena open platform for evaluating LLMs by human preference",
    "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena human pairwise judgments",
    "Understanding black-box predictions via influence functions",
    "Cook's distance case deletion diagnostics one-step approximation logistic regression",
    "adversarial vote manipulation of LLM arena leaderboard rankings",
    "robustness of rankings from pairwise comparisons to adversarial or corrupted comparisons"
  ],
  "reference_query_plan": {
    "architectural_shifts": [],
    "benchmarks": [
      "Chatbot Arena human preference battles (55k / 140k)",
      "MT-Bench human expert judgments"
    ],
    "central_topic": "Citation gaps in a paper on minimal removal sets (verified by exact Bradley-Terry refit) that flip adjacent-pair rankings of pairwise-comparison leaderboards: the Chatbot Arena / MT-Bench data and platforms, influence-function and case-deletion diagnostics behind the first-order removal ranking, and manipulation or corruption of crowd-vote and pairwise-comparison rankings.",
    "comparators": [
      "influence-only row removal (B2 comparator)",
      "adversarial manipulation and vote rigging of crowd-vote leaderboards",
      "robustness of pairwise-comparison rankings to corrupted comparisons"
    ],
    "core_methods": [
      "first-order (one-step Newton) influence of deleting a row on the Bradley-Terry score gap, with leave-one-out leverage correction",
      "case-deletion diagnostics (Cook's distance style) for logistic-type likelihoods"
    ],
    "forbidden_query_patterns": [
      "generic optimization or benchmarking surveys",
      "scientific method or paper-writing phrasing",
      "chronology of cycles, attempts or search history",
      "internal score names such as combined_score or rubric",
      "titles, authors or results of the withheld published paper on this research question, or pages citing it",
      "unrelated LLM architecture or training queries",
      "further Bradley-Terry extensions, existence/consistency or uncertainty theory already covered by the bibliography"
    ],
    "queries": [
      {
        "category": "benchmark_context",
        "query": "Chatbot Arena open platform for evaluating LLMs by human preference",
        "rationale": "Target arena-leaderboard-context (Introduction, Data): the opening claim that Bradley-Terry leaderboards are used to choose and announce models, and the Arena 55k/140k data, have no platform citation."
      },
      {
        "category": "benchmark_context",
        "query": "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena human pairwise judgments",
        "rationale": "Target arena-leaderboard-context (Data): the MT-Bench human expert judgments and the Arena human-preference data release are used without citing the dataset paper."
      },
      {
        "category": "core_method",
        "query": "Understanding black-box predictions via influence functions",
        "rationale": "Target influence-deletion-method (Problem Setup and Method): the Newton-step influence formula for deleting row i is the core of the studied configuration and currently cites only Broderick et al."
      },
      {
        "category": "baseline_comparator",
        "query": "Cook's distance case deletion diagnostics one-step approximation logistic regression",
        "rationale": "Target influence-deletion-method: the leverage-corrected leave-one-out approximation and the B2 influence-only comparator follow classical deletion diagnostics for likelihood models, which the draft states without support."
      },
      {
        "category": "result_driven_theme",
        "query": "adversarial vote manipulation of LLM arena leaderboard rankings",
        "rationale": "Target manipulation-positioning (Related Work, Introduction, Discussion): the removal budget is motivated through deliberate action and rigging, and the draft currently disclaims positioning against this work."
      },
      {
        "category": "baseline_comparator",
        "query": "robustness of rankings from pairwise comparisons to adversarial or corrupted comparisons",
        "rationale": "Target manipulation-positioning: gives one or two general comparator citations on how few corrupted comparisons change a pairwise-derived ranking, replacing the Scope-of-the-bibliography disclaimer."
      }
    ],
    "result_driven_themes": [
      "small removal fractions flip crowd-vote leaderboard ranks, motivating positioning against deliberate manipulation work"
    ],
    "status": "ready"
  },
  "reference_query_plans": [
    {
      "architectural_shifts": [
        "row-level influence greedy to cell-aggregated weighted refits",
        "myopic first-order search to relaxed implicit-gradient / LP-based target-rating search with exact rounding and fallback"
      ],
      "benchmarks": [
        "Chatbot Arena human preference (55k / 140k)",
        "MT-Bench human expert and GPT-4 judgments",
        "NBA historical Elo game records",
        "LLM-judge judgments on Arena battles"
      ],
      "central_topic": "Minimal removal sets (verified by exact Bradley-Terry refit) that flip pairwise-comparison leaderboard rankings, and how the budget differs between crowd-vote (Chatbot Arena), expert/LLM-judge (MT-Bench) and sports (NBA Elo) comparison data.",
      "comparators": [
        "random-removal baseline",
        "permuted/shuffled-outcome control",
        "influence-function and AMIP-style dropping-data robustness metrics",
        "vote-rigging and adversarial manipulation of crowdsourced leaderboards",
        "bootstrap/confidence-interval based ranking uncertainty"
      ],
      "core_methods": [
        "Bradley-Terry maximum-likelihood fitting on pairwise outcome counts",
        "first-order influence / approximate maximum influence perturbation for data-dropping robustness",
        "greedy removal search with exact-refit verification, prefix bisection and swap polish",
        "cell-aggregated (pair-count) weighted refits with relaxed removal search",
        "stationarity-LP over target ratings for minimal removal sets"
      ],
      "forbidden_query_patterns": [
        "generic optimization or benchmarking surveys",
        "scientific method or paper-writing phrasing",
        "chronology of cycles, attempts or search history",
        "internal score names such as combined_score or rubric",
        "titles, authors or results of the withheld published paper on this research question, or pages citing it",
        "unrelated LLM architecture or training queries"
      ],
      "queries": [
        {
          "category": "core_method",
          "query": "Bradley-Terry model paired comparisons maximum likelihood estimation ranking",
          "rationale": "Defines the scoring model refit exactly in every flip-budget verification; needs the original model paper and standard MLE/fitting references."
        },
        {
          "category": "core_method",
          "query": "approximate maximum influence perturbation dropping small fraction of data robustness",
          "rationale": "Closest methodological antecedent: first-order influence to find a small data subset whose removal changes a conclusion, which the greedy search re-linearises and verifies exactly."
        },
        {
          "category": "baseline_comparator",
          "query": "understanding black-box predictions influence functions",
          "rationale": "Source of the influence-function machinery underlying the greedy removal ranking; reviewers will expect it as the first-order comparator."
        },
        {
          "category": "benchmark_context",
          "query": "Chatbot Arena open platform evaluating LLMs human preference",
          "rationale": "Describes the crowd-vote data (55k/140k battles) and the Bradley-Terry ranking pipeline being stress-tested."
        },
        {
          "category": "benchmark_context",
          "query": "judging LLM-as-a-judge MT-Bench human expert pairwise judgments",
          "rationale": "Provides the expert-judgment and GPT-4 judge comparison data, the small contrasting evaluation design with only a few models."
        },
        {
          "category": "result_driven_theme",
          "query": "improving model ranking Chatbot Arena vote rigging",
          "rationale": "Adversarial manipulation of crowd votes is the deliberate-perturbation counterpart to the minimal-removal flip budgets reported."
        },
        {
          "category": "result_driven_theme",
          "query": "leaderboard illusion Chatbot Arena evaluation practices sampling private testing",
          "rationale": "Documents data-access and sampling asymmetries that affect the same leaderboard, relevant for interpreting small flip budgets as fragility."
        },
        {
          "category": "baseline_comparator",
          "query": "adversarial manipulation robustness rank aggregation from pairwise comparisons",
          "rationale": "Comparator literature on how few corrupted comparisons can change rankings from pairwise data, framing the removal-search results beyond LLM leaderboards."
        },
        {
          "category": "benchmark_context",
          "query": "Elo rating system relation to Bradley-Terry sports game outcomes",
          "rationale": "Connects the NBA Elo game-record data (sports evaluation design) to Bradley-Terry-type fitting, needed to justify cross-design comparison."
        },
        {
          "category": "result_driven_theme",
          "query": "statistical inference uncertainty ranking from pairwise comparisons confidence intervals bootstrap",
          "rationale": "Flip budgets are interpreted against sampling noise (gap-to-noise); needs the ranking-uncertainty literature that leaderboard confidence intervals rely on."
        }
      ],
      "result_driven_themes": [
        "large crowd-vote tables flip with a tiny removal fraction while the small expert-judgment table resisted flipping within the removal cap in the search phase",
        "influence-guided removal is far tighter than random removal, and permuted-outcome controls need larger budgets than real data",
        "three search variants tied on the search-stage score, so the exact-refit-verified greedy is already near the achievable budget on the large crowd table",
        "flip budget depends on the score gap relative to noise and on the evaluation design"
      ],
      "status": "ready"
    },
    {
      "architectural_shifts": [],
      "benchmarks": [
        "Chatbot Arena human preference battles (55k / 140k)",
        "MT-Bench human expert judgments"
      ],
      "central_topic": "Citation gaps in a paper on minimal removal sets (verified by exact Bradley-Terry refit) that flip adjacent-pair rankings of pairwise-comparison leaderboards: the Chatbot Arena / MT-Bench data and platforms, influence-function and case-deletion diagnostics behind the first-order removal ranking, and manipulation or corruption of crowd-vote and pairwise-comparison rankings.",
      "comparators": [
        "influence-only row removal (B2 comparator)",
        "adversarial manipulation and vote rigging of crowd-vote leaderboards",
        "robustness of pairwise-comparison rankings to corrupted comparisons"
      ],
      "core_methods": [
        "first-order (one-step Newton) influence of deleting a row on the Bradley-Terry score gap, with leave-one-out leverage correction",
        "case-deletion diagnostics (Cook's distance style) for logistic-type likelihoods"
      ],
      "forbidden_query_patterns": [
        "generic optimization or benchmarking surveys",
        "scientific method or paper-writing phrasing",
        "chronology of cycles, attempts or search history",
        "internal score names such as combined_score or rubric",
        "titles, authors or results of the withheld published paper on this research question, or pages citing it",
        "unrelated LLM architecture or training queries",
        "further Bradley-Terry extensions, existence/consistency or uncertainty theory already covered by the bibliography"
      ],
      "queries": [
        {
          "category": "benchmark_context",
          "query": "Chatbot Arena open platform for evaluating LLMs by human preference",
          "rationale": "Target arena-leaderboard-context (Introduction, Data): the opening claim that Bradley-Terry leaderboards are used to choose and announce models, and the Arena 55k/140k data, have no platform citation."
        },
        {
          "category": "benchmark_context",
          "query": "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena human pairwise judgments",
          "rationale": "Target arena-leaderboard-context (Data): the MT-Bench human expert judgments and the Arena human-preference data release are used without citing the dataset

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

\newcommand{\kcap}{k_{\mathrm{cap}}}
\newcommand{\hi}{h}
\newcommand{\lo}{\ell}

\title{How Few Comparisons Flip a Bradley--Terry Leaderboard Pair? Recorded Removal Budgets on Crowd-Vote and Sports Data}
\author{}

\begin{document}
\maketitle

\begin{abstract}
Public leaderboards built from pairwise comparisons fit a Bradley--Terry model and publish a ranking, yet how many comparisons must change before a ranking reverses is rarely measured. We study the smallest set of deleted comparisons, within a cap of 2\% of all rows, that reverses the point-estimate order of one adjacent pair under a ridge-regularised Bradley--Terry refit, as recorded by the task's evaluator. We measure it on a crowd-vote table (Chatbot Arena, 135,630 comparisons) and an NBA game table (12,900 comparisons). Recorded budgets are small: 62 and 4 rows for the top and mid pairs of the crowd table (at most 0.046\% of comparisons) and 62 and 8 rows for the sports table (0.48\% and 0.062\%). Mid-table pairs are cheaper than top pairs, and random deletion flips the top pairs in 0 of 20 draws. However, the evaluator's recorded influence-only reference (whose construction we could not verify) matched the studied configuration's budget in all six held-out cases, so no measured reduction relative to that reference is observed; the crowd-versus-sports contrast is confounded with table size, participants and era. No expert-judgment design was measured on held-out data, and the development stage records only aggregate scores, so we make no claim about expert annotation. All findings are descriptive: four cases, two designs, one rating model.
\end{abstract}

\section{Introduction}
Leaderboards that aggregate ``which of A and B is better'' judgments into Bradley--Terry (BT) ratings are used to choose models, to announce releases, and to compare research systems; Chatbot Arena is a prominent crowd-vote example \citep{https://doi.org/10.48550/arxiv.2403.04132}. The BT model and its many extensions are decades old \citep{Davidson1970OnET,Davidson1969MultivariatePC,Leonard1977AnAB}, and the statistical properties of its estimates under sampling noise are increasingly well understood \citep{Simons1999AsymptoticsWT,Gao2021UncertaintyQI,Li2021ThePO}. What is less often reported is a complementary, \emph{combinatorial} question: how much of the underlying comparison table has to change, whether through noise or deliberate action, before a published rank order reverses?

We make this question operational. Given a comparison table and one adjacent pair of rated participants, the \emph{removal budget} is the smallest number of rows whose deletion makes an exact refit of the same BT objective rank the lower participant above the upper one. Deletion is a deliberately weak perturbation (no inserted or relabelled votes), closely related to the ``dropping a little data'' robustness question of \citet{Broderick2020AnAF}. The evaluator records, for each returned set, its size $k$ and a flip indicator; we could not inspect how it verifies them, so we read a recorded budget as an upper bound on the true minimum (a smaller set might exist) and rely on the evaluator's records rather than on an independent check.

\paragraph{Research question.} Under a BT refit as defined by the task's metric (a ridge-penalised fit with ties as half wins; the penalty value we use below is the one we understand the task to specify), what is the smallest removal set within a cap of $2\%$ of all rows that reverses an adjacent top-of-table pair or an adjacent mid-table pair, and does this budget differ between a crowd-vote table and a sports-results table when both are measured by one evaluator-recorded protocol?

\paragraph{What we do.} We measure recorded removal budgets on two held-out tables of real data: a deduplicated Chatbot Arena crowd-vote table and an NBA game-results table. We compare the studied search configuration, which orders rows by first-order influence on the rating gap and then refines the set with re-linearised greedy batches and a local polish, against three evaluator-owned comparators (random removal, first-order influence only, and opponent-targeted removal) and three validity controls (empty set, label permutation, cross-table copy). A separate pair of development tables, including a six-model expert-judgment table, is used to compare search configurations and is reported separately; only their aggregate scores are recorded.

\paragraph{What we find.} (i) Recorded budgets are small in all four held-out cases (4 to 62 of 135,630 crowd rows; 8 to 62 of 12,900 NBA rows), and mid pairs are cheaper than top pairs in both tables. (ii) As a share of comparisons the sports budgets are about 10 and 21 times larger, but the two top-pair budgets are the same number of rows (62), so this contrast largely reflects table size and is confounded with participants and era. (iii) The evaluator's recorded influence-only reference matched the studied configuration's budget in every held-out case; we could not verify how that reference is constructed, and the studied configuration's recorded budgets equal that reference's in all six held-out cases, so no measured reduction relative to it is observed. (iv) The development stage records only aggregate scores, with no per-family or per-case breakdown, so the evidence says nothing about whether pairs in the six-model expert-judgment table flip; no expert design was measured on held-out data.

\paragraph{Contributions.} (1) A precisely specified removal-budget protocol with comparators and controls, whose recorded budgets are upper bounds on the true minimum; the evaluator's verification procedure was not inspectable. (2) Measured budgets for four held-out cases on two evaluation designs, with the crowd-versus-sports contrast and its confounds spelled out. (3) A negative result: the evaluator's recorded influence-only reference, whose construction is unverified, matches the studied configuration's budget in every held-out case. (4) An explicit scope statement: the claims concern the declared cases only, not confidence-interval-based rank changes, adversarial insertion or vote rigging, other rating models, or causal effects of evaluation design.

\section{Related Work}
\paragraph{Bradley--Terry models and their estimation.} The BT model has been extended to ties and within-pair order effects \citep{Davidson1970OnET,Davidson1977OnET}, to multivariate and two-dimensional comparisons \citep{Davidson1969MultivariatePC,Causeur2005A2E}, to continuous outcomes and generalised score estimation \citep{Stern2011ModeratedPC,Fageot2023GeneralizedBM}, to covariates and sparse grouped designs \citep{Yan2025InferenceIA,Yan2011GROUPEDSP}, and to Bayesian formulations \citep{Leonard1977AnAB,Hussain2013BayesianIO,Rizvi2026BayesianBF}. Conditions for existence of the maximum likelihood estimate and its consistency are studied by \citet{Butler2004TheEO} and \citet{Bong2021GeneralizedRF}, and ridge-penalised fitting is analysed by \citet{Varin2024TractableRR}. Computation and links to priority derivation and PageRank are treated by \citet{Vojnović2019ConvergenceRO,Sawadogo2019CombiningMA,Genest1999DerivingPF,Selby2024PageRankAT}. We use none of these extensions: the task's metric, as we understand it, fixes a plain ridge-penalised BT objective in which a tie counts as half a win, a convention that differs from explicit tie models such as that of \citet{Davidson1970OnET}. The ridge term keeps every refit well defined after rows are removed.

\paragraph{Uncertainty and rank inference.} Sampling-based uncertainty for BT scores and ranks is the subject of \citet{Gao2021UncertaintyQI}, \citet{Makur2024MinimaxHT} (hypothesis testing), \citet{Morel-Balbi2025EstimationOP} (partial rankings from sparse, noisy comparisons) and \citet{Li2021ThePO} (estimation error under general comparison graphs). These works ask how sampling variability limits what a ranking can resolve. We instead fix the observed table and ask how few of its rows determine the order of one adjacent pair. This is a statement about a single realised data set, not about a population, and we report no confidence-interval-based rank events.

\paragraph{Data-dropping robustness.} \citet{Broderick2020AnAF} propose an automatic finite-sample metric for when removing a small fraction of data changes a statistical conclusion, for statistical conclusions. Our setting is a specific instance in spirit: the conclusion is the order of one adjacent pair under a BT fit, and the dropped fraction is capped at $2\%$. The studied configuration accepts a removal set only after its own exact refit reverses the pair. \citet{Defresne2025PreferenceEF} use maximum-likelihood preference models for active elicitation, a different goal from auditing a fixed table.

\paragraph{Manipulation of crowd-vote leaderboards.} \citet{https://doi.org/10.48550/arxiv.2501.17858} study vote-rigging strategies against Chatbot Arena and their effect on model rankings. Our setting is a deletion-only perturbation with no adversary model, and we do not compare numbers with that work. Influence-based analysis of single training points is the tool behind our row ordering \citep{https://doi.org/10.48550/arxiv.1703.04730}. Work on other evaluation practices of arena-style platforms, and on MT-Bench-style model-judge evaluation, is relevant background that is not in our reference set, and we make no claim of novelty relative to it.

\section{Problem Setup and Method}
\subsection{Bradley--Terry leaderboards and the removal budget}
A comparison table has $N$ rows $(a_i,b_i,y_i)$ over $M$ participants, where $y_i\in\{\text{$a$ wins},\text{$b$ wins},\text{tie}\}$ is encoded as a score $s_i\in\{1,0,\tfrac12\}$. For ratings $\theta\in\mathbb{R}^M$ and $d_i=\theta_{a_i}-\theta_{b_i}$ the fit minimises
\begin{equation}
L(\theta)=\sum_{i=1}^{N}\Big[\log\!\big(1+e^{d_i}\big)-s_i d_i\Big]+\tfrac{\lambda}{2}\lVert\theta\rVert^2,\qquad \lambda=0.01\ \text{(as we understand the task's metric)},
\label{eq:bt}
\end{equation}
and participants are ranked by $\theta$. Let $\hi$ be ranked directly above $\lo$. For a removal set $R\subseteq\{1,\dots,N\}$ let $\theta^{(-R)}$ be the exact minimiser of Eq.~\eqref{eq:bt} on the remaining rows. The pair \emph{flips} if $\theta^{(-R)}_{\lo}>\theta^{(-R)}_{\hi}$. With cap $\kcap=\lceil 0.02N\rceil$, the \emph{removal budget} is
\begin{equation}
k^\star=\min\{|R|:\ |R|\le\kcap,\ \text{pair flips under }R\},
\end{equation}
and a search procedure is scored by $1-k/\kcap$ if it returns a flipping set of size $k\le\kcap$ and $0$ otherwise. Because the score is linear in $k$, a score near $1$ means a budget far below the cap. We report budgets in two units: rows, and percent of all $N$ comparisons (derived as $k/N$). The evaluator's ``budget fraction'' metric is $k/\kcap$, a fraction of the allowance and not of the table.

Two kinds of target are used: a \emph{top} pair and a \emph{mid} pair of adjacent ranks in the full-table fit. We take the top pair to be ranks 1 and 2 and the mid pair to be ranks $\lfloor M/2\rfloor$ and $\lfloor M/2\rfloor+1$; this rule, like the value of $\lambda$ above, is our reading of the task description and could not be checked against evaluator source, which is not staged. A flip here is a reversal of the \emph{point-estimate} order; no confidence-interval rank event is considered.

\subsection{Why influence ordering should help, and what we test}
Deleting row $i$ perturbs the stationarity condition by $-\nabla\ell_i$, so a Newton step predicts the change of the gap $g=\theta_{\hi}-\theta_{\lo}$ as, in the manner of influence-function analyses of the effect of removing a training point \citep{https://doi.org/10.48550/arxiv.1703.04730},
\begin{equation}
\Delta_i\;\approx\;\frac{(p_i-s_i)\,(v_{a_i}-v_{b_i})}{1-w_i\,q_i},\qquad v=H^{-1}(e_{\hi}-e_{\lo}),
\label{eq:infl}
\end{equation}
where $p_i=\sigma(d_i)$, $w_i=p_i(1-p_i)$, $H$ is the Hessian of Eq.~\eqref{eq:bt} (including the ridge), and $q_i=x_i^\top H^{-1}x_i$ with $x_i=e_{a_i}-e_{b_i}$ gives the leave-one-out leverage correction. Rows with the most negative $\Delta_i$ close the gap fastest to first order. Our use of this approximation differs from a pure influence analysis in that it only orders candidate rows, and every set is then checked by the candidate's own exact refit. Eq.~\eqref{eq:infl} is a linearisation, so we ask whether re-linearising and polishing an influence order reduces the budget relative to the evaluator's influence-only reference.

\subsection{Studied configuration}
The studied configuration (source in the staged evidence for the selected candidate) fits BT by damped Newton iterations with backtracking and an analytic gradient and dense Hessian, and then proceeds in three steps. (a) It ranks rows by Eq.~\eqref{eq:infl} at the full-table fit and finds, by bisection over prefixes of that order with an exact refit at each probe, the smallest prefix of at most $\kcap$ rows that flips the pair. (b) It runs a re-linearised greedy search: after each batch of removals it refits, recomputes Eq.~\eqref{eq:infl} on the remaining rows, and removes a batch of $\lceil 0.6\,n_{\mathrm{lin}}\rceil$ rows, where $n_{\mathrm{lin}}$ is the number of rows the linearised gains need to close the current gap; once the pair flips it bisects over prefixes of the insertion order. (c) It polishes the best set by drop-and-readd local search: it drops the least useful quarter of the incumbent set (halving that fraction after a failure, for at most 14 rounds), refills greedily under a strictly smaller size limit, and keeps any strictly smaller set that its own refit confirms. A set is accepted only if its own exact refit separates $\theta_{\lo}$ above $\theta_{\hi}$ by a margin of $10^{-5}$; the evaluator records a budget for the returned set, and we could not inspect how it verifies it. Search stops at 60\% of the allotted deadline. Bisection over prefixes assumes that longer prefixes flip once shorter ones do; this is not guaranteed, so the returned $k$ is an upper bound on the minimum and minimality is not claimed.

\subsection{Comparators and validity controls}\label{sec:method_comp}
The evaluator reports three comparators for each case, scored with the same rule as the studied configuration: \textbf{B1}, random removal (20 random orders per case; we report how many flip within the cap); \textbf{B2}, an influence-only removal, which the evaluator exposes as its ``influence reference''; and \textbf{B3}, an opponent-targeted removal. The evaluator source is not part of the staged evidence, so we do not independently verify how B1--B3 are constructed. We rely on their recorded outcomes (flip counts and budgets) and on the names under which they are recorded. B2's construction is therefore unverified; in particular we do not assert that it equals step (a) above, and we draw no conclusion that depends on that reading. B3 is described by the evaluator only as an opponent-targeted removal.

Three controls are recorded alongside the cases: an \emph{empty removal set}, which should not flip any case; a \emph{label-permutation} control on the top pair of each table, for which the evaluator records the fraction of moved labels against its expectation, the rating-spread ratio relative to the real fit, and a non-vacuity indicator; and a \emph{cross-table copy} control, for which it records the number of flips over its trials. We report only these recorded outcomes. The evidence does not state the thresholds or construction details behind the non-vacuity indicator or the copy control, and we make no claim about them.

\subsection{Why these definitions}
The perturbation scale and the cross-dataset comparison are choices, so we state the reasons for them. \emph{Deletion only:} every remaining row is a genuine observation, so a flip cannot be blamed on fabricated data, and each deletion set is in principle checkable by refitting. Insertion, relabelling and vote rigging would require an adversary model that we do not specify. \emph{Adjacent pairs:} if a removal set puts $\lo$ above $\hi$ and the original ranking placed other participants between them, then at least one adjacent pair in that chain must also have reversed. The smallest budget over adjacent pairs therefore lower-bounds the budget of any non-adjacent reversal, and adjacent pairs are the cheapest rank events. \emph{Top and mid:} the top pair is the position that leaderboards publicise, and the mid pair probes a typical interior position. \emph{A 2\% cap:} it fixes a common tolerance for how much of a table noise or an actor could plausibly alter and makes scores comparable across tables of different size. It is a convention, not an estimate of any real process, and we did not vary it; all held-out budgets sit well below it except the sports top pair, which uses 24\% of its allowance. 

\section{Experimental Protocol}
\subsection{Data}\label{sec:data}
Table~\ref{tab:data} lists the tables. The search procedure receives rows as integer participant indices with a coded outcome; names are not visible to it in the inspected candidate source. The held-out crowd table is the Chatbot Arena 140k preference release (data from the platform of \citealp{https://doi.org/10.48550/arxiv.2403.04132}) after content-hash deduplication against the development tables: from 135,634 raw rows, 2 were removed for content overlap with development data (a further 652 rows are listed in the evaluator metadata as prompt-only overlaps and were kept) and 2 rows of participants with fewer than 100 rows were dropped, leaving 135,630 rows over 52 models. The sports table holds NBA game results from 2006 to 2015 with 12,900 comparisons over 30 teams. The development tables are the Chatbot Arena 55k release (57,477 rows, 64 models) and the MT-Bench human-judgment table (3,355 rows, 6 models), the latter standing in for expert annotation. Dataset versions and licences are not recorded in the evidence we hold and are therefore not reported here. Model-judge data were not used.

\begin{table}[t]
\centering
\caption{Comparison tables. Caps are $\lceil 0.02N\rceil$ (derived). Held-out tables were never used to choose a search configuration; development tables were.}
\label{tab:data}
\small
\begin{tabular}{llllrrr}
\toprule
Use & Design & Table & Rows $N$ & Participants & Cap $\kcap$\\
\midrule
Held-out & crowd votes & Arena 140k (deduplicated) & 135,630 & 52 models & 2,713\\
Held-out & sports & NBA 2006--2015 & 12,900 & 30 teams & 258\\
Development & crowd votes & Arena 55k & 57,477 & 64 models & 1,150\\
Development & expert judgments & MT-Bench human & 3,355 & 6 models & 68\\
\bottomrule
\end{tabular}



\end{table}

\subsection{Cases, seeds and reported uncertainty}
Each table contributes two cases, a top pair and a mid pair, giving four held-out cases (crowd: F1 top, F2 mid; sports: F3 top, F4 mid) plus two permutation controls (F5, F6) on the top pairs. The held-out evaluation ran two seeded episodes (seeds 21 and 22); the development evaluation ran two (seeds 11 and 12). A family score is the mean of the case scores within a design, and the overall score is the mean of the two family scores. Uncertainty is limited by design: there are two episodes, B1 has 20 random draws per case, and the two held-out episodes returned identical per-case budgets. We therefore report no confidence intervals or significance tests, and nothing here is a population-level interval over data sets.

\subsection{Evaluation scopes and qualification}
Search configurations were scored on the development tables, and one frozen configuration was then evaluated in a single sealed held-out evaluation. We keep the two scopes in separate tables and sections and never combine their scores. No search configuration exceeded the starting baseline on the development tables (Section~\ref{sec:dev}), so the frozen selection is not a winner; it is one of three configurations with identical development scores. Its held-out evaluation completed and was recorded as qualified, with a true success indicator. The evidence does not record which gate criteria the qualification decision covers, so we read it only as a statement that the sealed evaluation ran to completion and was recorded as qualified; we do not read it as certifying controls or validity. The control outcomes in Section~\ref{sec:controls} are separate observations taken from the recorded episodes. Qualification is not evidence of superiority over the starting baseline, which was not run on the held-out tables, and it does not extend the findings beyond the declared cases.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/protocol_overview.png}
\caption{Protocol overview (schematic). A comparison table is fit with a ridge-penalised Bradley--Terry model; a target adjacent pair (top or mid) is selected; a removal search proposes at most $2\%$ of rows; the task's metric, as we understand it, records the budget $k$ and score $1-k/\kcap$ for the returned set. The evaluator box, its refit step and the ``search again'' arrow depict this metric as we understand it, not an inspected implementation; the only refit we could inspect is the candidate's own. Random, influence-only and opponent-targeted removal serve as comparators; empty-set, label-permutation and cross-table copy runs serve as controls. Development tables (Arena 55k, MT-Bench human) and held-out tables (Arena 140k deduplicated, NBA) are kept separate.}
\label{fig:overview}
\end{figure}

\section{Results}
\subsection{Held-out removal budgets}
Table~\ref{tab:cases} and Figure~\ref{fig:main} give the recorded budgets of the studied configuration on the four held-out cases. All four flipped within the cap (flip rate 1.0), and every one used a small share of its allowance: the family scores are 0.988 for crowd votes and 0.864 for sports, the overall score is 0.926, and the mean of $k/\kcap$ over the four cases is 0.074. 
In the crowd table, deleting 62 of 135,630 rows (0.046\%) reverses the top pair and 4 rows (0.003\%) reverse the mid pair. In the sports table, 62 of 12,900 rows (0.48\%) reverse the top pair and 8 rows (0.062\%) reverse the mid pair. 
The two episodes (seeds 21 and 22) produced identical budgets in every case, so we observe no episode-to-episode variation; with two episodes this is a consistency check on the search procedure, not an estimate of sampling variability. Supplement Table~\ref{tab:agg} lists the aggregate held-out metrics next to the comparator references.


\begin{table}[t]
\centering
\caption{Held-out removal budgets. $k$ is the recorded number of removed rows; percentages are $k/N$ (derived). B1 reports how many of 20 random orders flipped within the cap; B2 and B3 report the recorded budget of each comparator. The studied configuration and B2 coincide in every case.}
\label{tab:cases}
\small
\begin{tabular}{llrrrrrr}
\toprule
Case & Pair & $N$ & $\kcap$ & Studied $k$ (\% of $N$) & B1 flips & B2 $k$ & B3 $k$\\
\midrule
F1 & crowd, top & 135,630 & 2,713 & 62 (0.046\%) & 0/20 & 62 & 650\\
F2 & crowd, mid & 135,630 & 2,713 & 4 (0.003\%) & 6/20 & 4 & 6\\
F3 & NBA, top & 12,900 & 258 & 62 (0.48\%) & 0/20 & 62 & 88\\
F4 & NBA, mid & 12,900 & 258 & 8 (0.062\%) & 0/20 & 8 & 12\\
\bottomrule
\end{tabular}

\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/main_budget_by_case.pdf}
\caption{Recorded removal budget as a percent of all comparisons (log scale) for the studied configuration, influence-only removal (B2) and opponent-targeted removal (B3), with the 2\% cap shown. Numbers above bars are rows removed. Bars for the studied configuration and B2 coincide in all four cases. Below each category, the number of random orders (of 20) that flipped within the cap.}
\label{fig:main}
\end{figure}

\subsection{Top pairs versus mid pairs}
In both tables the mid pair is cheaper than the top pair: 4 versus 62 rows in the crowd table and 8 versus 62 rows in the sports table. Random removal is informative here: it never flips a top pair (0 of 20 draws, in either table) or the sports mid pair, but flips the crowd mid pair in 6 of 20 draws, while an influence-ordered set needs only 4 rows. This suggests, but does not establish, a small rating gap for the crowd mid pair. The registry does not record rating gaps, so we do not test whether smaller gaps explain this ordering.

\subsection{Crowd votes versus sports: a contrast with confounds}\label{sec:contrast}
As a share of comparisons the sports budgets are larger: the top-pair budget is 10.5 times and the mid-pair budget 21.0 times the crowd value (derived from $k/N$). 
The top-pair ratio is exactly the ratio of table sizes, $135{,}630/12{,}900=10.5$, because both top-pair budgets are 62 rows. The mid pairs differ by 4 versus 8 rows. Hence the per-share contrast is largely a denominator effect for the top pairs: the studied configuration's upper bounds are the same number of rows (62) for both. True minima, and so relative fragility in rows, are not established, and the caps differ (2,713 versus 258). The designs also differ in participants (52 models versus 30 teams), era, outcome granularity, the tie structure, and the match graph. The choice of normaliser also matters. Dividing instead by the mean number of comparisons a participant appears in ($2N/M$, derived: 5,217 for the crowd table and 860 for the sports table) shrinks the contrast but does not remove it: the 62-row top-pair budget is 1.2\% of a crowd participant's comparisons and 7.2\% of a team's (about 6 times), and the mid-pair budgets are 0.077\% and 0.93\% (about 12 times), against 10.5 and 21.0 times under $k/N$. 
Neither normaliser is privileged: the share of the table suits a perturbation of a fixed fraction of all votes, the share of a participant's comparisons is closer to the evidence behind its rating. Both views give the same qualitative picture (small budgets, mid cheaper than top, sports the larger share), differing in the size of the ratio. We cannot separate these factors with two tables, and we therefore do not attribute the contrast to evaluation design. What the data do support is narrower: under one recorded protocol, one adjacent top pair in each of two specific tables is recorded as reversed by deleting 62 rows.

\subsection{Studied configuration versus the influence-only reference}
The studied configuration's budget equals that of B2 in all four held-out cases and in both permutation controls (Table~\ref{tab:cases}, Supplement Table~\ref{tab:full}), and the overall held-out score 0.926 equals the evaluator's reference score for B2 to the reported precision. 
On these cases the studied configuration therefore shows no measured reduction relative to the evaluator's influence-only reference. Because the construction of that reference is not verified (Section~\ref{sec:method_comp}), we do not conclude that a static influence ranking alone suffices, nor that the re-linearisation, leverage correction and polish contributed nothing; we conclude only that the recorded budgets coincide. On the development tables only total scores are recorded (Section~\ref{sec:dev}); no per-family, per-case or per-comparator development breakdown is recorded, so no development comparison with an influence-only reference is possible. Opponent-targeted removal needs more rows in all four cases: 650 versus 62, 6 versus 4, 88 versus 62 and 12 versus 8. The gap is large only for the crowd top pair (10.5 times), and modest elsewhere (1.4 to 1.5 times). Random removal's mean overall score is 0.041, against 0.926 for B2. 

We did not run the starting baseline on the held-out tables, so we make no statement about how it would compare with the studied configuration there.

\subsection{Controls}\label{sec:controls}
The empty removal set flipped no case, and the cross-table copy control recorded 0 flips in 2 trials; we draw no further inference from the copy control because its construction is not documented. The permutation controls were recorded as non-vacuous by the evaluator (Figure~\ref{fig:controls}b): the fraction of moved labels was 0.660 against an expected 0.662 for the crowd table and 0.498 against 0.500 for the sports table, and the rating spread fell to 0.088 and 0.160 of the real value. 
The top pair of a permuted table flipped after only 2 rows (crowd) and 10 rows (sports), compared with 62 rows on the real tables (Figure~\ref{fig:controls}a); the mean score difference between permuted and real top pairs is $+0.112$. 
With outcomes shuffled the ratings collapse together and a handful of rows reorders them. This does not show that real ranks are robust in any absolute sense, and the permuted tables are a lower reference, not a model of noise or manipulation.

\begin{figure}[t]
\centering
\includegraphics[width=0.9\textwidth]{figures/controls_permutation.pdf}
\caption{Label-permutation controls on the held-out tables. (a) Recorded top-pair budget in rows (log scale) on the real table and on the label-permuted table. (b) Rating spread of the permuted fit relative to the real fit; the evaluator records both permutations as non-vacuous.}
\la

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}

\subsection{Full per-case results including controls}
Table~\ref{tab:full} lists all six held-out cases. The two seeded episodes (21 and 22) returned identical values in every cell. Evaluator-recorded durations per seeded episode were 4.45 s and 4.51 s.

\begin{table}[h]
\centering
\caption{All held-out cases. F5 and F6 are label-permutation controls of F1 and F3. Scores are $1-k/\kcap$. B1 score is the mean over 20 random orders, with zero for a non-flipping order. Percent columns are $k/N$ (derived).}
\label{tab:full}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrrrrrrrrr}
\toprule
Case & $N$ & $\kcap$ & $k$ & \% & Score & B1 flips & B1 score & B2 $k$ & B3 $k$ & B3 score\\
\midrule
F1 & 135,630 & 2,713 & 62 & 0.0457 & 0.977 & 0/20 & 0.000 & 62 & 650 & 0.760\\
F2 & 135,630 & 2,713 & 4 & 0.0029 & 0.999 & 6/20 & 0.164 & 4 & 6 & 0.998\\
F3 & 12,900 & 258 & 62 & 0.481 & 0.760 & 0/20 & 0.000 & 62 & 88 & 0.659\\
F4 & 12,900 & 258 & 8 & 0.062 & 0.969 & 0/20 & 0.000 & 8 & 12 & 0.953\\
F5 & 135,630 & 2,713 & 2 & 0.0015 & 0.999 & 7/20 & 0.251 & 2 & 2 & 0.999\\
F6 & 12,900 & 258 & 10 & 0.078 & 0.961 & 0/20 & 0.000 & 10 & 10 & 0.961\\
\bottomrule
\end{tabular}

\end{table}

\begin{table}[h]
\centering
\caption{Aggregate held-out metrics (budget-saving score $1-k/\kcap$, averaged over cases within a design, then over designs; the four real cases plus controls enter only through the control gap). Reference columns are the evaluator's score for random removal (B1) and influence-only removal (B2) aggregated the same way.}
\label{tab:agg}
\small
\begin{tabular}{lr}
\toprule
Metric & Value\\
\midrule
Overall score (studied configuration) & 0.926\\
\quad crowd family (F1, F2) & 0.988\\
\quad sports family (F3, F4) & 0.864\\
Reference score, random removal (B1) & 0.041\\
Reference score, influence only (B2) & 0.926\\
Flip rate over real cases & 1.0\\
Mean $k/\kcap$ over real cases & 0.074\\
Control gap (permuted minus real, mean score) & $+0.112$\\
\bottomrule
\end{tabular}

\end{table}

\subsection{Controls and qualification details}
The empty-set control did not flip any case. The cross-table copy control recorded 0 flips in 2 trials; its construction is not documented in the staged evidence. The permutation controls report a moved-label fraction of 0.6601 (expected 0.6615) and a rating-spread ratio of 0.0882 for F5, and 0.4981 (expected 0.5000) and 0.1598 for F6, both recorded as non-vacuous by the evaluator. The mean score difference between permuted and real top pairs is $+0.112$. 
The held-out evaluation completed with outcome qualified, and the recorded success indicator is true. The evidence does not record the gate criteria behind this outcome, so we do not interpret it as certifying that controls passed or that the evaluation is valid beyond the cases reported. 
Diagnostics volunteered by the candidate during evaluation are marked unverified by the evaluator and were not used for any number in this paper. Every reported budget is the evaluator's recorded value for the returned set; we could not inspect how the evaluator verifies it, and the only inspectable refit is the candidate's own.

\subsection{Development tables: additional detail}
The evidence registry records, for each of the three development configurations, a total score (0.4993) and per-episode runtimes, and for the starting baseline a total score (0.4993). No sub-scores, flip rates, comparator references or control gaps are recorded for the development stage, so none are reported here. Search scores and held-out scores belong to different evaluation scopes and tables and should not be compared. All three development configurations were scored (3 of 3, 0 unscored), so there is no missing development evidence. 

\subsection{Algorithmic specification of the studied configuration}
The Newton fit uses analytic gradient $\nabla L=\sum_i (p_i-s_i)(e_{a_i}-e_{b_i})+\lambda\theta$ and Hessian $H=\sum_i w_i\,x_ix_i^\top+\lambda I$, with step halving until the objective stops increasing (at most 60 iterations, gradient tolerance $10^{-9}$). Eq.~\eqref{eq:infl} floors the leverage denominator $1-w_iq_i$ at $10^{-3}$. Step (b) uses a shrink factor $0.6$ and stops when the removed set reaches the current size limit. Step (c) begins at a drop fraction of $0.25$ and halves it after each failure. Refits inside the re-linearised greedy loop are warm-started from the previous solution; prefix-bisection probes and polish refits start from the full-table fit. The candidate's own acceptance test uses a margin of $10^{-5}$ on its own fit; how the evaluator's fit and acceptance test are implemented is not documented in the staged evidence. The candidate source reads the table as integer participant indices with a coded outcome, so model names are not used by it. Source: the selected candidate's \texttt{src/program.py} in the staged evidence. A further file in that directory (\texttt{datasets\_offline.py}) holds loaders for offline analysis, was not imported by the evaluated code, and was not executed; we make no claim from it.

\subsection{Data provenance and reproduction}
Raw data are not redistributed, and we do not report dataset commits or licences because no staged artifact records them; readers should take these from the dataset hosts. The held-out tables are prepared by the evaluator; the evaluator metadata records the content-overlap removals and prompt-only overlaps reported in Section~\ref{sec:data}, and we have no further documentation of its preparation or checking procedure. The figures are built by \texttt{scripts/derive\_final\_stats.py} (derived percentages and ratios from the evaluator's recorded episodes) and \texttt{scripts/build\_figures.py} (Figures~\ref{fig:main} and~\ref{fig:controls}); Figure~\ref{fig:overview} is a schematic with no quantitative content. Tables~\ref{tab:cases} and~\ref{tab:full} are filled from \texttt{derived/final\_stats.json}. The seeds are 11 and 12 (development) and 21 and 22 (held-out); The recorded held-out evaluation episodes of the studied configuration took 4.45 s and 4.51 s each; the hardware is not recorded. We were not able to give independent timing for a full reproduction from raw data.

\subsection{LLM Usage}
Large language models were used throughout this work. The search configurations and their code, the analysis scripts, and the text of this manuscript were produced with an LLM-based research assistant operating inside an automated pipeline; the manuscript reports the recorded development scores and the recorded held-out evaluation of one frozen selection. The assistant also drafted the related-work discussion from a small retrieved bibliography. The quantitative figures and the case, aggregate and development-score tables are derived by script from the recorded evaluator outputs. No claim in the paper relies on an LLM's unverified recollection of the literature; related work is described only at the level of the cited titles.

\subsection{Extended limitations}
Four held-out cases on two designs, two identical episodes and twenty random draws are the entire basis for the held-out claims. The development side adds one expert table of six participants, for which no breakdown is recorded. We did not run exhaustive or exact optimisation on any table, so we cannot say how far the recorded budgets are from the minimum. We did not examine whether the reversed pairs are statistically distinguishable under sampling uncertainty, which would be the natural reading of an adjacent-pair flip for a practitioner. The bibliography available for this submission includes one work on vote rigging and one on influence functions but lacks the MT-Bench paper, classical case-deletion diagnostics and work on arena-platform practices beyond the platform description, so positioning relative to those lines is incomplete.
```
