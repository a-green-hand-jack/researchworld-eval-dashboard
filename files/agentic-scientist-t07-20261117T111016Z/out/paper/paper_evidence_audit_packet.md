# Agentic evidence audit packet

- generated_at: `2026-11-17T14:49:22.612477+00:00`
- paper_dir: `work/results/t07/codex/20261117_111440/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261117_132510-paper_evidence_audit_round_2-6matuxv4/workspace`

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
    "anchored_references": 87,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 190,
    "resolved_references": 148,
    "total_references": 235
  },
  "ok": true,
  "pdf_path": "work/results/t07/codex/20261117_111440/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 87,
    "dangling_references": 0,
    "manifests_checked": 18,
    "resolved_references": 148,
    "total_references": 235
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "Final comparison: MAE 3.90 pp, RMSE 4.84 pp, Spearman 0.816, Kendall 0.672 for the frozen package; baseline MAEs IRT 5.91, uniform 10.52, prior 8.34, anchors 15.67 pp.",
      "evidence_refs": [
        "paper_data.json#/final_evaluation/metrics"
      ],
      "source_ids": [
        "final.metric.mae",
        "final.metric.rmse",
        "final.metric.spearman",
        "final.metric.kendall",
        "final.metric.irt_mae",
        "final.metric.uniform_mae",
        "final.metric.prior_mae",
        "final.metric.anchor_mae"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Nine final matrices, seeds 1009/2003/3001, budgets 5/10/25; 81 non-replay normal cells. Normal BBH replay excluded. Final and development results remain separate.",
      "evidence_refs": [
        "analysis/paper_statistics.json#/cell_count"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Development cases ARC-Challenge, IFEval, Commonsense, and GSM are not pooled into final results.",
      "evidence_refs": [
        "paper_data.json#/best_correct/evaluation_evidence/episodes"
      ],
      "source_ids": [
        "result.top_program_01"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Final evaluation completed and qualified; no failed normal cells recorded. This does not establish generality or an unrecorded gate diagnosis.",
      "evidence_refs": [
        "paper_data.json#/final_evaluation",
        "analysis/paper_statistics.json#/uncertainty"
      ],
      "source_ids": [
        "final.qualification.status",
        "final.qualification.outcome",
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Table 1 equal-cell aggregate, selected: {\"mae\": 0.03899160553529307, \"rmse\": 0.04837892636321264, \"spearman\": 0.8158480130897703, \"kendall\": 0.6715966634525838}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/aggregate/selected"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.mae",
        "final.metric.rmse",
        "final.metric.spearman",
        "final.metric.kendall"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Table 1 equal-cell aggregate, irt_mae: {\"mae\": 0.059112232152967646, \"rmse\": 0.07299152437230297, \"spearman\": 0.602771109366078, \"kendall\": 0.4912660259879461}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/aggregate/irt_mae"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.irt_mae"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Table 1 equal-cell aggregate, uniform_mae: {\"mae\": 0.10520541810011626, \"rmse\": 0.1289158814140679, \"spearman\": 0.6038423271049155, \"kendall\": 0.49382422014991234}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/aggregate/uniform_mae"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.uniform_mae"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Table 1 equal-cell aggregate, prior_mae: {\"mae\": 0.08335016635136305, \"rmse\": 0.10082993485201375, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508152}; constant-prior rank correlations omitted as undefined, not interpreted.",
      "evidence_refs": [
        "analysis/paper_statistics.json#/aggregate/prior_mae"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.prior_mae"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Table 1 equal-cell aggregate, anchor_mae: {\"mae\": 0.15674229873896958, \"rmse\": 0.1836370607479899, \"spearman\": 0.43676442124186665, \"kendall\": 0.34629093193194244}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/aggregate/anchor_mae"
      ],
      "source_ids": [
        "final.evidence.episodes",
        "final.metric.anchor_mae"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Paired aggregate difference and conditional 95% interval versus anchor_mae: {\"candidate_minus_baseline_mae\": -0.11775069320367655, \"lower_95\": -0.13019745821672318, \"upper_95\": -0.10715691965628014}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/uncertainty/comparisons/anchor_mae"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Paired aggregate difference and conditional 95% interval versus irt_mae: {\"candidate_minus_baseline_mae\": -0.02012062661767458, \"lower_95\": -0.02570984836073398, \"upper_95\": -0.014632649205711504}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/uncertainty/comparisons/irt_mae"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Paired aggregate difference and conditional 95% interval versus prior_mae: {\"candidate_minus_baseline_mae\": -0.04435856081606998, \"lower_95\": -0.0584542588406073, \"upper_95\": -0.032429878882884206}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/uncertainty/comparisons/prior_mae"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Paired aggregate difference and conditional 95% interval versus uniform_mae: {\"candidate_minus_baseline_mae\": -0.0662138125648232, \"lower_95\": -0.07118833982860809, \"upper_95\": -0.06124024345684073}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/uncertainty/comparisons/uniform_mae"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [
        "Efron1979",
        "Efron1987"
      ],
      "claim": "200 paired lineage-block percentile draws, within-benchmark resampling, budgets/seeds retained, equal benchmark weights; repeated uncertainty object is used only once. Bootstrap seed 1729. No benchmark resampling or source refitting.",
      "evidence_refs": [
        "source_evidence/evaluator/evaluate_final.py#L1065",
        "analysis/paper_statistics.json#/uncertainty"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Budget 5, equal benchmark/seed averages: {\"selected\": {\"mae\": 0.04669374761569296, \"rmse\": 0.05758408482094327, \"spearman\": 0.7630155669581268, \"kendall\": 0.6143869823064319}, \"irt_mae\": {\"mae\": 0.07315970206711758, \"rmse\": 0.0887636204334073, \"spearman\": 0.4714617903376189, \"kendall\": 0.38192622460899556}, \"uniform_mae\": {\"mae\": 0.14719149418258548, \"rmse\": 0.17994987958153988, \"spearman\": 0.47608277221402845, \"kendall\": 0.3903942891829132}, \"prior_mae\": {\"mae\": 0.08335016635136305, \"rmse\": 0.10082993485201375, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508153}, \"anchor_mae\": {\"mae\": 0.1964588286829245, \"rmse\": 0.22484769024244858, \"spearman\": 0.39127705812954644, \"kendall\": 0.3165076071594208}}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/by_budget/5"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Budget 10, equal benchmark/seed averages: {\"selected\": {\"mae\": 0.03949342241707047, \"rmse\": 0.04911604765122082, \"spearman\": 0.8024100310134182, \"kendall\": 0.6614950149898136}, \"irt_mae\": {\"mae\": 0.05882589257102038, \"rmse\": 0.07376317150653507, \"spearman\": 0.6389191814413949, \"kendall\": 0.5125701429530953}, \"uniform_mae\": {\"mae\": 0.10079623396372099, \"rmse\": 0.12397663067918117, \"spearman\": 0.6351567179012955, \"kendall\": 0.5105130287587952}, \"prior_mae\": {\"mae\": 0.08335016635136305, \"rmse\": 0.10082993485201375, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508153}, \"anchor_mae\": {\"mae\": 0.15711556648068295, \"rmse\": 0.18527285656620768, \"spearman\": 0.43538732108965195, \"kendall\": 0.3449749289282738}}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/by_budget/10"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Budget 25, equal benchmark/seed averages: {\"selected\": {\"mae\": 0.030787646573115786, \"rmse\": 0.03843664661747383, \"spearman\": 0.8821184412977663, \"kendall\": 0.7389079930615062}, \"irt_mae\": {\"mae\": 0.045351101820764975, \"rmse\": 0.05644778117696654, \"spearman\": 0.69793235631922, \"kendall\": 0.5793017104017475}, \"uniform_mae\": {\"mae\": 0.06762852615404231, \"rmse\": 0.0828211339814826, \"spearman\": 0.7002874911994219, \"kendall\": 0.5805653425080287}, \"prior_mae\": {\"mae\": 0.08335016635136305, \"rmse\": 0.10082993485201375, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508153}, \"anchor_mae\": {\"mae\": 0.11665250105330134, \"rmse\": 0.14079063543531334, \"spearman\": 0.48362888450640146, \"kendall\": 0.3773902597081327}}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/by_budget/25"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Seed 1009, equal benchmark/budget averages: {\"selected\": {\"mae\": 0.0381560393886576, \"rmse\": 0.046744015815091494, \"spearman\": 0.8238183222495606, \"kendall\": 0.6776889673808946}, \"irt_mae\": {\"mae\": 0.057241025797026605, \"rmse\": 0.0711998533138959, \"spearman\": 0.5897114115868115, \"kendall\": 0.4804776522726319}, \"uniform_mae\": {\"mae\": 0.09771174966096459, \"rmse\": 0.12299700607101784, \"spearman\": 0.5907855084254345, \"kendall\": 0.48139745011499546}, \"prior_mae\": {\"mae\": 0.08335016635136307, \"rmse\": 0.10082993485201373, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508153}, \"anchor_mae\": {\"mae\": 0.15674229873896958, \"rmse\": 0.18363706074798986, \"spearman\": 0.43676442124186665, \"kendall\": 0.3462909319319425}}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/by_seed/1009"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Seed 2003, equal benchmark/budget averages: {\"selected\": {\"mae\": 0.04005928471900295, \"rmse\": 0.0494074745238824, \"spearman\": 0.814828264548178, \"kendall\": 0.6689046606377388}, \"irt_mae\": {\"mae\": 0.06353185365094442, \"rmse\": 0.07757126992884943, \"spearman\": 0.5729559053372506, \"kendall\": 0.455887179045493}, \"uniform_mae\": {\"mae\": 0.1129040617792329, \"rmse\": 0.13683233816242268, \"spearman\": 0.571177423822154, \"kendall\": 0.4587904576346685}, \"prior_mae\": {\"mae\": 0.08335016635136307, \"rmse\": 0.10082993485201373, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508153}, \"anchor_mae\": {\"mae\": 0.15674229873896958, \"rmse\": 0.18363706074798986, \"spearman\": 0.43676442124186665, \"kendall\": 0.3462909319319425}}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/by_seed/2003"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Seed 3001, equal benchmark/budget averages: {\"selected\": {\"mae\": 0.03875949249821865, \"rmse\": 0.04898528875066401, \"spearman\": 0.8088974524715722, \"kendall\": 0.6681963623391184}, \"irt_mae\": {\"mae\": 0.05656381701093191, \"rmse\": 0.07020344987416358, \"spearman\": 0.6456460111741718, \"kendall\": 0.5374332466457133}, \"uniform_mae\": {\"mae\": 0.10500044286015128, \"rmse\": 0.12691830000876309, \"spearman\": 0.6495640490671576, \"kendall\": 0.5412847527000731}, \"prior_mae\": {\"mae\": 0.08335016635136307, \"rmse\": 0.10082993485201373, \"spearman\": -0.7679107677181501, \"kendall\": -0.7696394679508153}, \"anchor_mae\": {\"mae\": 0.15674229873896958, \"rmse\": 0.18363706074798986, \"spearman\": 0.43676442124186665, \"kendall\": 0.3462909319319425}}",
      "evidence_refs": [
        "analysis/paper_statistics.json#/by_seed/3001"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "bbh, complete seed-averaged benchmark-budget MAEs and diagnostic rankings: {\"5\": {\"selected\": {\"mae\": 0.03691685773695346, \"rmse\": 0.048130582871789264, \"spearman\": 0.903835473189852, \"kendall\": 0.7537686839818513}, \"irt_mae\": {\"mae\": 0.09159315587074934, \"rmse\": 0.11323809370173521, \"spearman\": 0.4888551632901541, \"kendall\": 0.36032436850064165}, \"uniform_mae\": {\"mae\": 0.19066675532825947, \"rmse\": 0.23496800291657807, \"spearman\": 0.4868540460662063, \"kendall\": 0.3634292465793772}, \"prior_mae\": {\"mae\": 0.09981012776618164, \"rmse\": 0.11728730985580836, \"spearman\": 0.00453529479790034, \"kendall\": 0.003733006833947207}, \"anchor_mae\": {\"mae\": 0.20159465646943206, \"rmse\": 0.22322535856417455, \"spearman\": 0.6462645686960894, \"kendall\": 0.45987205307244455}}, \"10\": {\"selected\": {\"mae\": 0.027197010295446567, \"rmse\": 0.03667168410258444, \"spearman\": 0.9226494360312806, \"kendall\": 0.7748246480082046}, \"irt_mae\": {\"mae\": 0.07131212931903973, \"rmse\": 0.09173677801435783, \"spearman\": 0.7254410752246644, \"kendall\": 0.5543588818344568}, \"uniform_mae\": {\"mae\": 0.12659191170226514, \"rmse\": 0.1580740435362966, \"spearman\": 0.7345272023822907, \"kendall\": 0.5658950919911208}, \"prior_mae\": {\"mae\": 0.09981012776618164, \"rmse\": 0.11728730985580836, \"spearman\": 0.00453529479790034, \"kendall\": 0.003733006833947207}, \"anchor_mae\": {\"mae\": 0.19047195890017013, \"rmse\": 0.21055134145731777, \"spearman\": 0.5831054739740975, \"kendall\": 0.40464043915216247}}, \"25\": {\"selected\": {\"mae\": 0.02175026992255258, \"rmse\": 0.0271779555599929, \"spearman\": 0.9557868291806549, \"kendall\": 0.8329936209870282

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
  "count": 25,
  "generated_at": "2026-11-17T14:16:30.449847+00:00",
  "queries": [
    "Direct supplied or foundational identifier: 2309.08638",
    "Direct supplied or foundational identifier: 2402.14992",
    "Direct supplied or foundational identifier: 2407.12844",
    "Direct supplied or foundational identifier: 2409.03563",
    "Direct supplied or foundational identifier: 2410.05952",
    "Direct supplied or foundational identifier: 2601.13885",
    "Direct supplied or foundational identifier: 2406.01574",
    "Direct supplied or foundational identifier: 2211.09110",
    "Direct supplied or foundational identifier: 2412.06745",
    "Direct supplied or foundational identifier: 2210.09261",
    "Direct supplied or foundational identifier: 2311.12022",
    "Direct supplied or foundational identifier: 2310.16049",
    "Direct supplied or foundational identifier: 2103.03874",
    "Direct supplied or foundational identifier: 2009.13081",
    "Direct supplied or foundational identifier: 2009.03300",
    "Direct supplied or foundational identifier: 2308.11462",
    "Direct supplied or foundational identifier: 1506.02629",
    "Direct supplied or foundational identifier: 2006.10256",
    "Direct supplied or foundational identifier: 1907.10121",
    "Direct foundational DOI: 10.1080/00401706.1970.10488634",
    "Direct foundational DOI: 10.1214/aoms/1177729442",
    "Direct foundational DOI: 10.1214/aos/1176344552",
    "Direct foundational DOI: 10.1080/01621459.1987.10478410",
    "Direct foundational DOI: 10.1109/MCSE.2007.55",
    "Direct known foundational article"
  ],
  "references": [
    {
      "abstract": "Abstract: Modern language models often exhibit powerful but brittle behavior, leading to the development of larger and more diverse benchmarks to reliably assess their behavior. Here, we suggest that model performance can be benchmarked and elucidated with much smaller evaluation sets. We first show that in six popular language classification benchmarks, model confidence in the correct class on many pairs of points is strongly correlated across models. We build upon this phenomenon to propose Anchor Point Selection, a technique to select small subsets of datasets that capture model behavior across the entire dataset. Anchor points reliably rank models: across 87 diverse language model-prompt pairs, evaluating models using 1-30 anchor points outperforms uniform sampling and other baselines at accurately ranking models. Moreover, just several anchor points can be used to estimate model per-class predictions on all other points in a dataset with low mean absolute error, sufficient for gauging where the model is likely to fail. Lastly, we present Anchor Point Maps for visualizing these insights and facilitating comparisons of the performance of different models on various regions within the dataset distribution.",
      "authors": [
        "Vivek, Rajan",
        "Ethayarajh, Kawin",
        "Yang, Diyi",
        "Kiela, Douwe"
      ],
      "citation_key": "Vivek2024",
      "consultation_scope": "abstract and bibliographic metadata",
      "consulted_path": "literature_evidence/Vivek2024.html",
      "id": "ref.arxiv.2309.08638",
      "paper_id": "arXiv:2309.08638",
      "query": "Direct supplied or foundational identifier: 2309.08638",
      "retrieved_at": "2026-11-17T14:16:30.449847+00:00",
      "source_url": "https://arxiv.org/abs/2309.08638",
      "title": "Anchor Points: Benchmarking Models with Much Fewer Examples",
      "year": 2023
    },
    {
      "abstract": "Abstract: The versatility of large language models (LLMs) led to the creation of diverse benchmarks that thoroughly test a variety of language models' abilities. These benchmarks consist of tens of thousands of examples making evaluation of LLMs very expensive. In this paper, we investigate strategies to reduce the number of evaluations needed to assess the performance of an LLM on several key benchmarks. For example, we show that to accurately estimate the performance of an LLM on MMLU, a popular multiple-choice QA benchmark consisting of 14K examples, it is sufficient to evaluate this LLM on 100 curated examples. We release evaluation tools and tiny versions of popular benchmarks: Open LLM Leaderboard, MMLU, HELM, and AlpacaEval 2.0. Our empirical analysis demonstrates that these tools and tiny benchmarks are sufficient to reliably and efficiently reproduce the original evaluation results.",
      "authors": [
        "Polo, Felipe Maia",
        "Weber, Lucas",
        "Choshen, Leshem",
        "Sun, Yuekai",
        "Xu, Gongjun",
        "Yurochkin, Mikhail"
      ],
      "citation_key": "Polo2024",
      "consultation_scope": "abstract and bibliographic metadata",
      "consulted_path": "literature_evidence/Polo2024.html",
      "id": "ref.arxiv.2402.14992",
      "paper_id": "arXiv:2402.14992",
      "query": "Direct supplied or foundational identifier: 2402.14992",
      "retrieved_at": "2026-11-17T14:16:30.449847+00:00",
      "source_url": "https://arxiv.org/abs/2402.14992",
      "title": "tinyBenchmarks: evaluating LLMs with fewer examples",
      "year": 2024
    },
    {
      "abstract": "Abstract: Large Language Models (LLMs) vary in their abilities on a range of tasks. Initiatives such as the Open LLM Leaderboard aim to quantify these differences with several large benchmarks (sets of test items to which an LLM can respond either correctly or incorrectly). However, high correlations within and between benchmark scores suggest that (1) there exists a small set of common underlying abilities that these benchmarks measure, and (2) items tap into redundant information and the benchmarks may thus be considerably compressed. We use data from n > 5000 LLMs to identify the most informative items of six benchmarks, ARC, GSM8K, HellaSwag, MMLU, TruthfulQA and WinoGrande (with d = 28,632 items in total). From them we distill a sparse benchmark, metabench, that has less than 3% of the original size of all six benchmarks combined. This new sparse benchmark goes beyond point scores by yielding estimators of the underlying benchmark-specific abilities. We show that these estimators (1) can be used to reconstruct each original individual benchmark score with, on average, 1.24% root mean square error (RMSE), (2) reconstruct the original total score with 0.58% RMSE, and (3) have a single underlying common factor whose Spearman correlation with the total score is r = 0.94.",
      "authors": [
        "Kipnis, Alex",
        "Voudouris, Konstantinos",
        "Buschoff, Luca M. Schulze",
        "Schulz, Eric"
      ],
      "citation_key": "Kipnis2025",
      "consultation_scope": "abstract and bibliographic metadata",
      "consulted_path": "literature_evidence/Kipnis2025.html",
      "id": "ref.arxiv.2407.12844",
      "paper_id": "arXiv:2407.12844",
      "query": "Direct supplied or foundational identifier: 2407.12844",
      "retrieved_at": "2026-11-17T14:16:30.449847+00:00",
      "source_url": "https://arxiv.org/abs/2407.12844",
      "title": "metabench -- A Sparse Benchmark of Reasoning and Knowledge in Large Language Models",
      "year": 2024
    },
    {
      "abstract": "Abstract: Predicting the performance of LLMs on individual task instances is essential to ensure their reliability in high-stakes applications. To do so, a possibility is to evaluate the considered LLM on a set of task instances and train an assessor to predict its performance based on features of the instances. However, this approach requires evaluating each new LLM on a sufficiently large set of task instances to train an assessor specific to it. In this work, we leverage the evaluation results of previously tested LLMs to reduce the number of evaluations required to predict the performance of a new LLM. In practice, we propose to test the new LLM on a small set of reference instances and train a generic assessor which predicts the performance of the LLM on an instance based on the performance of the former on the reference set and features of the instance of interest. We conduct empirical studies on HELM-Lite and KindsOfReasoning, a collection of existing reasoning datasets that we introduce, where we evaluate all instruction-fine-tuned OpenAI models until the January 2024 version of GPT4. When predicting performance on instances with the same distribution as those used to train the generic assessor, we find this achieves performance comparable to the LLM-specific assessors trained on the full set of instances. Additionally, we find that randomly selecting the reference instances performs as well as some advanced selection methods we tested. For out of distribution, however, no clear winner emerges and the overall performance is worse, suggesting that the inherent predictability of LLMs is low.",
      "authors": [
        "Pacchiardi, Lorenzo",
        "Cheke, Lucy G.",
        "Hern\u00e1ndez-Orallo, Jos\u00e9"
      ],
      "citation_key": "Pacchiardi2024",
      "consultation_scope": "abstract and bibliographic metadata",
      "consulted_path": "literature_evidence/Pacchiardi2024.html",
      "id": "ref.arxiv.2409.03563",
      "paper_id": "arXiv:2409.03563",
      "query": "Direct supplied or foundational identifier: 2409.03563",
      "retrieved_at": "2026-11-17T14:16:30.449847+00:00",
      "source_url": "https://arxiv.org/abs/2409.03563",
      "title": "100 instances is all you need: predicting the success of a new LLM on unseen data by testing on a few instances",
      "year": 2024
    },
    {
      "abstract": "Abstract: As large language models (LLMs) become increasingly versatile, numerous large scale benchmarks have been developed to thoroughly assess their capabilities. These benchmarks typically consist of diverse datasets and prompts to evaluate different aspects of LLM performance. However, comprehensive evaluations on hundreds or thousands of prompts incur tremendous costs in terms of computation, money, and time. In this work, we investigate strategies to improve evaluation efficiency by selecting a subset of examples from each benchmark using a learned policy. Our approach models the dependencies across test examples, allowing accurate prediction of the evaluation outcomes for the remaining examples based on the outcomes of the selected ones. Consequently, we only need to acquire the actual evaluation outcomes for the selected subset. We rigorously explore various subset selection policies and introduce a novel RL-based policy that leverages the captured dependencies. Empirical results demonstrate that our approach significantly reduces the number of evaluation prompts required while maintaining accurate performance estimates compared to previous methods.",
      "authors": [
        "Li, Yang",
        "Ma, Jie",
        "Ballesteros, Miguel",
        "Benajiba, Yassine",
        "Horwood, Graham"
      ],
      "citation_key": "Li2025",
      "consultation_scope": "abstract and bibliographic metadata",
      "consulted_path": "literature_evidence/Li2025.html",
      "id": "ref.arxiv.2410.05952",
      "paper_id": "arXiv:2410.05952",
      "query": "Direct supplied or foundational identifier: 2410.05952",
      "retrieved_at": "2026-11-17T14:16:30.449847+00:00",
      "source_url": "https://arxiv.org/abs/2410.05952",
      "title": "Active Evaluation Acquisition for Efficient LLM Benchmarking",
      "year": 2024
    },
    {
      "abstract": "Abstract: Computerized Adaptive Testing (CAT) has proven effective for efficient LLM evaluation on multiple-choice benchmarks, but modern LLM evaluation increasingly relies on generation tasks where outputs are scored continuously rather than marked correct/incorrect. We present a principled extension of IRT-based adaptive testing to continuous bounded scores (ROUGE, BLEU, LLM-as-a-Judge) by replacing the Bernoulli response distribution with a heteroskedastic normal distribution. Building on this, we introduce an uncertainty aware ranker with adaptive stopping criteria that achieves reliable model ranking while testing as few items and as cheaply as possible. We validate our method on five benchmarks spanning n-gram-based, embedding-based, and LLM-as-judge metrics. Our method improves ranking correlation by 0.13 $\\tau$ over random sampling and has 99% accuracy on confident predictions while using 2% of the items after a one-time calibration step.",
      "authors": [
        "Balk\u0131r, Esma",
        "Pernthaller, Alice",
        "Basaldella, Marco",
        "Hern\u00e1ndez-Orallo, Jos\u00e9",
        "Collier, Nigel"
      ],
      "citation_key": "Balkir2026",
      "consultation_scope": "abstract and bibliographic metadata",
      "consulted_path": "literature_evidence/Balkir2026.html",
      "id": "ref.arxiv.2601.13885",
      "paper_id": "arXiv:2601.13885",
      "query": "Direct supplied or foundational identifier: 2601.13885",
      "retrieved_at": "2026-11-17T14:16:30.449847+00:00",
      "source_url": "https://arxiv.org/abs/2601.13885",
      "title": "Confident Rankings with Fewer Items: Adaptive LLM Evaluation with Continuous Scores",
      "year": 2026
    },
    {
      "abstract": "Abstract: In the age of large-scale language models, benchmarks like the Massive Multitask Language Understanding (MMLU) have been pivotal in pushing the boundaries of what AI can achieve in language comprehension and reasoning across diverse domains. However, as models continue to improve, their performance on these benchmarks has begun to plateau, making it increasingly difficult to discern differences in model capabilities. This paper introduces MMLU-Pro, an enhanced dataset designed to extend the mostly knowledge-driven MMLU benchmark by integrating more challenging, reasoning-focused questions and expanding the choice set from four to ten options. Additionally, MMLU-Pro eliminates the trivial and noisy questions in MMLU. Our experimental results show that MMLU-Pro not only raises the challenge,

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


\usepackage{iclr2026_conference,times}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,booktabs,graphicx,url,hyperref}
\usepackage{subcaption}
\title{Score-Targeted Subsets for Predicting LLM Benchmark Accuracy}
\author{}
\newcommand{\clip}{\operatorname{clip}_{[0,1]}}
\newcommand{\sigmoid}{\operatorname{sigmoid}}

\begin{document}
\maketitle

\begin{abstract}
Historical item-level evaluations offer a way to estimate a language model's benchmark accuracy without evaluating every item. We examine a frozen subset-and-decoder package that targets covariance with full-benchmark accuracy, rather than item representativeness alone. Its source-trained, nested query path is shared across target models; a source-selected decoder maps observed responses to estimated full scores. Recorded held-out evaluations cover nine benchmark matrices, three seeds, and budgets of 5, 10, and 25 items. The package attains mean absolute error of 3.90 percentage points, compared with 5.91 for a local item-response estimator and 10.52 for uniform sampling. A paired lineage-block interval for its error difference from local item response is $[-2.57,-1.46]$ percentage points, conditional on these benchmarks. However, the comparison reverses on several benchmark--budget combinations, including every evaluated budget on HELM MATH. These results support an average package-level advantage within the frozen snapshot, not universal superiority, isolated component effects, or guaranteed transfer to new model families.



\end{abstract}

\section{Introduction}
Evaluating a language model throughout training or across prompting configurations repeatedly measures an entire benchmark, even when only its aggregate accuracy is needed. Historical evaluations contain more information than a list of aggregate scores: each item supplies a response pattern across source models. Such patterns can identify items whose outcomes are informative about an unseen model's full score. The practical question is not merely whether a benchmark can be compressed, but what should be preserved by the compression and how failures should be detected.

An item subset that represents typical response patterns need not be the subset that best predicts the mean. Some diverse items may contribute little information about differences in full accuracy; conversely, strongly correlated items can be redundant once another item has been observed. This motivates a score-directed criterion: select an item by its remaining covariance with the full score, relative to its conditional variance. A decoder can then use the complete observed response vector, rather than interpreting the queried fraction as an ordinary miniature test.

We study this principle through a frozen acquisition-and-decoding package and paired local comparators. The source-trained query path is common to all target models, while the predicted score depends on each target's answers. This is nonadaptive item selection with respect to target responses. It is not a target-specific testing policy, and it does not require item text or target-model identity at inference. The readable implementation also contains a source-selected nonlinear decoding option, but the retained evaluation does not establish which decoder branch was active for each case. Our scientific object is therefore the complete evaluated package, not a claimed nonlinear mechanism.

The contributions are deliberately bounded. We describe the score-directed acquisition objective and compatible score decoding in the supplied source counterpart. We reconcile the recorded held-out predictions with aggregate accuracy and lineage-level ranking metrics, using budget-matched local baselines. Finally, we show where the aggregate advantage breaks down and distinguish fixed-benchmark uncertainty from evidence about unseen benchmarks. No controlled component ablations are available, so no part of the comparison identifies the isolated benefit of acquisition, linear decoding, or nonlinear residual correction.

Across the retained evaluation, lower average error coexists with unfavorable comparisons on HELM MATH, LegalBench, and MedQA at particular budgets. Those reversals are central evidence, not exceptions to be removed. A useful compact evaluator must be assessed both as an estimator of absolute accuracy and as a ranking device, with its source dependence and uncertainty made explicit.


\begin{figure}[t]
\centering
\includegraphics[width=\textwidth,height=2in,keepaspectratio]{figures/score_prediction_overview.png}
\caption{Estimation setting and information boundary. Source response matrices determine a shared score-directed item path and source-selected decoder. Only the target responses at the queried items enter prediction; retained full-benchmark target scores are used for evaluation. The optional decoder branch is not independently attested per case.}
\label{fig:overview}
\end{figure}

\section{Related Work}
\paragraph{Compact benchmark evaluation.}
Anchor Points uses correlations in model responses to construct small representative evaluation sets \citep{Vivek2024}. tinyBenchmarks studies curated subsets and score estimation across established evaluation suites \citep{Polo2024}; metabench compresses reasoning and knowledge tests using informative items and ability estimates \citep{Kipnis2025}. These works motivate source-response reuse, but their reported results are not experimental baselines here. Our anchor and item-response comparators are the specific local implementations described below, not reproductions of every feature of those systems.

Supervised assessors can predict a new model's performance from its responses on reference instances and features of the instance to be predicted \citep{Pacchiardi2024}. Our setting instead predicts the aggregate score directly from binary response histories, without using item-text features. Learned acquisition policies offer another route to efficient evaluation \citep{Li2025}. In contrast, the item path considered here is fixed from source data before target responses arrive. Adaptive evaluation with continuous bounded scores \citep{Balkir2026} addresses a broader observation model and stopping problem; our evidence is restricted to fixed-budget binary matrices. ONEBench studies aggregation over heterogeneous, incomplete evaluations \citep{Ghosh2024}, whereas the present target is a retained benchmark's arithmetic mean.

\paragraph{Targeted design and regularization.}
Selecting measurements for a particular linear functional, rather than estimating all parameters equally well, is a classical experimental-design distinction \citep{Elfving1952}. The score-directed criterion below is an empirical, regularized covariance construction, not a claim to solve that general design problem optimally. Ridge regularization stabilizes regression when observations are correlated \citep{Hoerl1970}. Here both the acquisition criterion and decoder depend on source-derived covariance, making source-to-target stability an empirical assumption rather than a consequence of regularization.

\paragraph{Evaluation discipline.}
Model selection can overfit its own validation criterion \citep{Cawley2010}, and repeated adaptive reuse of evaluation data requires care \citep{Dwork2015}. We consequently separate development feedback from the recorded held-out comparison. Bootstrap uncertainty \citep{Efron1979} is reported under the evaluator's actual resampling unit, not as a distribution-free certificate. None of these methodological connections turns the observed comparison into evidence of universal benchmark predictability.

\section{Method}
\subsection{Problem and Estimation Target}
For one benchmark, let $X\in\{0,1\}^{M\times N}$ contain source-model responses on $N$ retained item columns. A target model has response vector $y\in\{0,1\}^{N}$ and full accuracy
\begin{equation}
s(y)=\frac{1}{N}\sum_{j=1}^{N}y_j.
\label{eq:target}
\end{equation}
Only responses on a subset $Q_k$, of size $k$, are made available to the estimator. The output is $\hat s(y_{Q_k};X)\in[0,1]$. Historical source responses can be used in fitting and tuning; unqueried target responses and full target scores cannot. The target is the mean over retained columns, not a claim to recover an unreconciled original benchmark or a differently weighted official leaderboard score.



Source rows have nonnegative weights $w_m$ summing to unity. The supplied protocol gives each metadata-defined source lineage equal total weight and distributes that weight equally among its rows. Item-content groups constrain selection: at most one item from any group is queried. However, all retained columns, including their multiplicities, remain in Equation~\ref{eq:target}. Thus query uniqueness and score weighting are distinct operations. The same nested path $Q_5\subset Q_{10}\subset Q_{25}$ serves all targets within a fitted case.



\subsection{Score-Directed Shared Acquisition}
Define the weighted item means $\mu_j=\sum_m w_mX_{mj}$, source full scores $s_m=N^{-1}\sum_jX_{mj}$, and weighted score mean $\bar s=\sum_mw_ms_m$. Let
\begin{equation}
Z_{mj}=\sqrt{w_m}(X_{mj}-\mu_j),\quad
u_m=\sqrt{w_m}(s_m-\bar s),\quad C=Z^\top Z,\quad c=Z^\top u.
\label{eq:covariance}
\end{equation}
The vector $c$ targets full accuracy explicitly. A high item variance alone does not imply a high score covariance; a high marginal covariance can also become redundant after other items are selected.


For regularization $\lambda>0$, a partial subset $Q$ has regularized score information $c_Q^\top(C_{QQ}+\lambda I)^{-1}c_Q$. A Schur-complement expansion yields the incremental criterion
\begin{equation}
g(j\mid Q)=
\frac{\left[c_j-C_{jQ}(C_{QQ}+\lambda I)^{-1}c_Q\right]^2}
{C_{jj}+\lambda-C_{jQ}(C_{QQ}+\lambda I)^{-1}C_{Qj}}.
\label{eq:gain}
\end{equation}
The readable selector greedily adds the legal item maximizing this quantity, masking every item in an already queried content group. Empty-set terms vanish. This construction optimizes a source empirical linear-prediction surrogate; it neither guarantees target MAE reduction nor proves that the greedy subset is globally optimal. Ridge regularization also changes the acquisition ranking, not merely the final regression fit.


The rationale is to prefer responses that explain residual variation in the quantity actually being estimated. In contrast, response-space coverage can emphasize diversity without accounting for whether that diversity changes the full mean. This is a design hypothesis: the available comparison changes the decoder as well as the query path, so it cannot establish that Equation~\ref{eq:gain} alone explains the measured advantage.

\subsection{All-Observation Score Decoding}
For observed history $z=y_Q$, the linear decoder uses
\begin{align}
\beta_Q&=(C_{QQ}+\lambda I)^{-1}c_Q,\\
\hat s_{\mathrm{ridge}}(z)&=\bar s+(z-\mu_Q)^\top\beta_Q,\qquad
\hat s_{\mathrm{offset}}(z)=\bar s+\frac{1}{|Q|}\sum_{j\in Q}(z_j-\mu_j),\\
\hat s_L(z)&=\clip\left[\alpha\hat s_{\mathrm{ridge}}(z)+(1-\alpha)\hat s_{\mathrm{offset}}(z)\right].
\label{eq:linear}
\end{align}
The offset term corrects the source score mean using the target's average deviation from source item means. Every queried answer contributes to decoding; identical answer histories map to the same prediction. With no observations, the fallback is the source score mean. Clipping bounds predictions but does not supply confidence intervals or unbiasedness.


The supplied implementation also admits an optional decoder that infers a regularized scalar log-odds shift from queried answers, averages its predicted probabilities over retained items, and adds a source-fitted residual ridge correction. It can blend this estimate with Equation~\ref{eq:linear}, including a purely linear fallback. Its residual features and fitted shifts use the same query prefix during training and inference. Supplementary Information gives the equations. Since no per-case branch selections or component ablations are attested, we do not label the measured gain a nonlinear-decoder effect.



\subsection{Source-Only Selection of Settings}
Settings are selected with lineage-disjoint source folds. Within each fold, item statistics and the acquisition path are refitted on fitting rows, and accuracy estimates are assessed on held-out source lineages. Loss averages absolute errors over the evaluation prefixes, then gives held-out lineages equal weight. The optional decoder adds an outer source split that refits the linear selector and its tuning within the fitting partition. No target full score is supplied for these choices.



The source counterpart is inspectable, but the retained final source-tree digest does not itself prove byte identity with that available tree. We therefore distinguish an implementation-grounded description of the supplied counterpart from the directly attested final predictions. This boundary is particularly important for settings or conditional branches absent from the measurement records. The empirical conclusions below require the recorded predictions, not an assumption about which optional branch produced them.



\section{Experimental Protocol}
\subsection{Data, Splits, and Budget Matching}
The recorded final evaluation covers nine binary benchmark matrices. The leaderboard-derived group contains BBH \citep{Suzgun2022}, GPQA \citep{Rein2023}, MMLU-Pro \citep{Wang2024}, MuSR \citep{Sprague2023}, and a MATH subset \citep{Hendrycks2021}. The HELM-derived group \citep{Liang2023} contains LegalBench \citep{Guha2023}, MATH, MedQA \citep{Jin2020}, and MMLU \citep{Hendrycks2020}. These are the supplied retained matrices, not newly collected LLM outputs. Distinguishing leaderboard MATH from HELM MATH is essential because they are separate evaluation cases.


Development feedback concerned ARC-Challenge, IFEval, Commonsense, and GSM matrices; it is not pooled with the final metrics. The frozen package is refitted from the source rows of each final benchmark. Hence this is evaluation across held-out benchmark cases with per-benchmark source fitting, not transfer of a single fixed set of coefficients across tasks. No additional evaluated task family is supplied beyond this benchmark-prediction setting.


The frozen resource manifests describe model-lineage separation and conservative item-content reconciliation across development and final data. Anonymous group identifiers, rather than model names or item text, reach the estimator. Known aliases and declared base-model relations guide grouping; undocumented derivatives can remain related across partitions. Common-stem normalization likewise does not establish semantic or pretraining disjointness. These are metadata-based safeguards, not proof of independent source and target populations.



Evaluation uses seeds 1009, 2003, and 3001 and cumulative query budgets 5, 10, and 25. This yields 81 non-replay benchmark--budget--seed cells. Each reset discards fitted state. A repeated normal BBH record checks deterministic replay but is excluded from performance averages. Identical-history and duplicated-target checks assess prediction consistency; additional perturbed observations are reported separately, not counted as ordinary performance measurements.



\subsection{Compared Estimators}
All nonzero-cost estimators use the same reported item budget, but not necessarily the same items or fitting cost. The \textbf{source prior} returns the weighted source mean and uses no target answers. \textbf{Uniform sampling} selects a random prefix of content-group representatives and scales observed outcomes by each group's retained-column mass. Its clipped, group-mass-weighted estimate is not simply an unweighted mean when group sizes differ. \textbf{Local anchors} constructs normalized source response embeddings, chooses representatives by a farthest-point rule, assigns all retained items to selected representatives, and uses assignment masses to weight their target outcomes. This is a local anchor estimator rather than an exact published Anchor Points reproduction.



\textbf{Local IRT} uses a logistic ability--difficulty model with regularized ability fitting. It shares the uniform baseline's item path, estimates target ability from the queried answers, and averages predicted probabilities across retained items. Its source-fitted difficulties and implementation details are specified in Supplementary Information. The \textbf{score-targeted package} changes both selection and decoding. Accordingly its comparison with IRT is a package comparison at matched observation budgets, not a selector-only or decoder-only ablation. None of the local comparators establishes a state-of-the-art comparison with the full published systems.


\subsection{Metrics and Conditional Uncertainty}
Within each cell, each target lineage receives equal total weight, distributed equally among its models. MAE is the resulting weighted absolute error, and RMSE is the square root of weighted squared error. Ranking metrics are Spearman correlation and Kendall's $\tau_b$ between lineage-mean predictions and lineage-mean true scores, not correlations over individual rows. Aggregate metrics average cells equally, giving each benchmark, budget, and seed equal weight. In particular, aggregate RMSE is a mean of cell RMSEs, not a pooled squared-error statistic.



The evaluator supplies paired percentile intervals from 200 lineage-block bootstrap draws. Within a benchmark, lineage blocks retain their predictions across budgets and seeds; benchmarks retain equal weights. The same aggregate uncertainty object is repeated in the outer seed records and is used only once. These intervals condition on the fixed cases and stored fitting outcomes. They do not resample benchmarks, refit source data, quantify future-family transfer, or provide individual-target prediction intervals. They are the recorded percentile procedure, not higher-order corrected intervals \citep{Efron1987}. No failed normal cells are recorded. The evaluator's completion and qualification outcome are both affirmative; that procedural result does not certify scientific generality.




\section{Results}
\subsection{Average Accuracy and Ranking}
Table~\ref{tab:main} reports the frozen final comparison. The score-targeted package has MAE 3.90 percentage points versus 5.91 for local IRT, the strongest recorded aggregate baseline by MAE. Uniform sampling, the source prior, and local anchors have MAE 10.52, 8.34, and 15.67 percentage points, respectively. The package's RMSE is 4.84 percentage points, compared with 7.30 for local IRT. These are averages under the stated weighting, not a guarantee for every target or benchmark.



\begin{table}[t]
\centering
\caption{Equal-cell averages over the retained final cases. Error units are percentage points (pp); rank correlations use lineage means. Only the source prior uses no target answers. Baseline RMSE and correlations are reconstructed from the recorded prediction arrays; a constant prior cannot provide a meaningful ranking, so its correlations are omitted.}
\label{tab:main}
\input{tables/aggregate.tex}

\end{table}

The mean Spearman correlation is 0.816 for the package, versus 0.603 for local IRT; the corresponding Kendall values are 0.672 and 0.491. Uniform sampling has similar aggregate ranking correlations to local IRT despite substantially higher score error. Thus absolute accuracy estimation and ordering are empirically distinct objectives. Our MAE uncertainty analysis should not be read as a significance test for the differences in either ranking metric. Nor does lineage-level correlation establish that every pair of closely matched individual models is reliably ordered.


\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/paired_error_comparison.pdf}
\caption{Paired aggregate MAE differences with the recorded 95\% lineage-block percentile intervals. Negative values favor the score-targeted package. Budgets and seeds remain within each lineage block, and benchmarks are not resampled. All intervals are conditional on the fixed benchmark collection.}
\label{fig:paired}

\end{figure}

Figure~\ref{fig:paired} quantifies the aggregate comparisons without discarding their pairing. The package-minus-IRT MAE difference is $-2.01$ percentage points, with interval $[-2.57,-1.46]$. The corresponding differences are $-6.62$ against uniform sampling, $-4.44$ against the prior, and $-11.78$ against local anchors; each recorded interval lies below zero. This is evidence for an average error reduction within the fixed evaluation. It does not estimate the probability that a newly chosen benchmark would favor the package.


\subsection{Budget Dependence and Seed Consistency}
Averaging over benchmarks and seeds, package MAE decreases from 4.67 percentage points at 5 items to 3.95 at 10 and 3.08 at 25. Local IRT decreases from 7.32 to 5.88 and 4.54, respectively. Package Spearman correlation rises from 0.763 to 0.802 and 0.882 across these budgets. Supplementary Figure~\ref{fig:budget} shows the paired budget profiles alongside the other nonconstant estimators. These are measurements at nested subsets, not a claim of monotonic improvement for each benchmark or every fitted subset.


The package's aggregate MAEs for the three recorded seeds are 3.816, 4.006, and 3.876 percentage points. Its error is lower than the aggregate local IRT error for each seed. This descriptive consistency is useful, but the seeds reuse the same frozen source and target splits; they are not independent samples of future benchmark environments. Source-prior and deterministic anchor predictions also do not become independent replications merely because their values appear in multiple seed records.


\subsection{Where the Comparison Reverses}
Figure~\ref{fig:reversals} shows benchmark--budget differences from local IRT, averaging the recorded seeds. On each leaderboard-derived matrix, the package has lower MAE at every evaluated budget. The HELM-derived matrices are mixed: LegalBench favors IRT at 5 and 25 items, HELM MATH favors IRT at all budgets, and MedQA favors IRT at 10 and 25 items. MMLU favors the package across these budgets. These are descriptive cell means; no cell-specific confidence intervals or multiplicity-adjusted tests are supplied.



\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/case_budget_reversals.pdf}
\caption{Benchmark-specific package-minus-local-IRT MAE, averaged over seeds. Shapes distinguish query budgets. Left of zero favors the package; right favors IRT. The shared horizontal scale preserves both the larger leaderboard advantages and the HELM reversals. Panels separate matrix provenance, not independently randomized treatment groups. No benchmark-specific intervals are inferred from the aggregate interval.}
\label{fig:reversals}

\end{figure}

The HELM MATH contrast is substantial enough to matter to the interpretation: at 5 items the package's MAE is 11.63 percentage points, compared with 9.53 for IRT; at 25 items the respective values are 6.19 and 5.61. MedQA is also nonmonotonic for the package: its MAE increases from 6.68 at 5 items to 7.47 at 10, before falling to 5.54 at 25. Additional observations therefore do not ensure lower realized error under a changed regression prefix. We do not diagnose these reversals as saturation, lineage shift, or decoder activation: the retained evidence does not isolate those causes.



The contrast between matrix groups is likewise not a causal ecosystem effect. Dataset composition, model populations, item reconciliation, and source-target relationships change together. The results support a heterogeneous estimator comparison, not a claim that leaderboard provenance is intrinsically easier to predict. Reporting only the aggregate would conceal meaningful local failures; reporting only the failures would conceal the paired aggregate advantage.

\subsection{Observation Perturbations and Attribution Limits}
When all queried target answers are replaced by zeros, recorded MAE is 21.58 percentage points. Independently rotating each source row's item order while preserving its row mean gives MAE 6.26 percentage points. Both exceed the ordinary-condition 3.90. These interventions are consistent with the package using answer histories and aligned source responses. They do not prove absence of leakage, identify a causal component, or establish that a particular nonlinear module contributes. The all-zero intervention changes observation content rather than measuring real target behavior, and row rotations change the training representation rather than a single decoder component.





No controlled selector/decoder cross-comparison, curve-only decoder result, or residual-only decoder result is available. The most defensible conclusion is therefore that the complete frozen package outperforms the recorded local baselines on average under this protocol. Component attribution remains an unresolved experimental question, even though the readable implementation makes such comparisons possible in future work.

\section{Discussion and Limitations}
\paragraph{Prediction is not benchmark replacement.}
A compact estimate is useful when the target is aggregate accuracy under an already specified evaluation distribution. It cannot recover which unqueried examples failed, measure new capabilities absent from the benchmark, or certify rare-event reliability. HELM explicitly motivates evaluation beyond a single accuracy number \citep{Liang2023}; compressing accuracy must not be presented as compressing all of those desiderata. The present binary-response setting also excludes continuous quality scores and adaptive stopping rules. At deployment, choosing an estimator because its aggregate mean is better should not remove the need to check benchmark-specific failures.

\paragraph{Source dependence and residual uncertainty.}
Score-directed selection benefits only if source covariance is informative for target models. Lineage-aware weighting prevents a heavily represented known family from dominating the empirical objective, but cannot repair missing or incorrect ancestry metadata. Similarly, content normalization reduces known duplication without proving semantic independence or excluding pretraining contamination. The bootstrap retains the source fit and benchmark list, so it does not quantify uncertainty from these choices. In particular, the interval excluding zero is compatible with the local reversals and with worse performance on an unmeasured future model family.

\paragraph{What the comparisons do and do not control.}
Observation counts are matched, whereas selected items, decoding assumptions, hyperparameter search structure, and fitting work are not. Thus lower package MAE is useful practical evidence but not an isolated test of score covariance versus response clustering. The local IRT and anchor baselines are transparent reference estimators, not exhaustive implementations of published alternatives. Broader comparisons, source-population shifts, and controlled acquisition--decoder combinations remain necessary before a claim of general methodological superiority would be justified.

\paragraph{Provenance and reproducibility.}
The final evaluation is recorded as completed and qualified, independently of development selection. We preserve that outcome without treating it as a statistical theorem or asserting unrecorded qualification diagnostics. Candidate-reported diagnostics remain unverified; source inspection supports the documented counterpart, while exact byte identity with the evaluated source tree is not independently established. All reported analysis is regenerated from retained evaluator predictions, with machine-readable claim mappings and provenance sidecars. Neither the estimator nor the evaluator was rerun during manuscript preparation. This distinction prevents analysis reconstruction from being mistaken for a fresh independent replication.





\section{Conclusion}
Source response matrices can support compact full-score estimation by directing item acquisition toward the aggregate quantity of interest and decoding the complete queried history. In the frozen evaluation studied here, the score-targeted package has lower average accuracy-prediction error than the recorded local estimators, together with stronger average lineage-level ranking correlations. Paired uncertainty supports the average MAE comparison only conditional on the retained benchmark collection.

The limits are equally consequential. HELM MATH, LegalBench, and MedQA contain unfavorable comparisons; increasing the query budget is not uniformly beneficial in every case. The evidence does not identify whether acquisition, linear regression, or an optional nonlinear decoder is responsible for the aggregate improvement. Metadata-based separation and procedural qualification do not establish unrestricted transfer or absence of undocumented relationships. The appropriate next scientific tests are controlled acquisition--decoder comparisons and genuinely shifted source-target populations, not a stronger superiority claim from the same aggregate. Compact evaluation should therefore be treated as a calibrated, source-dependent prediction problem r

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}

\subsection{Optional Decoder and Prefix-Matched Residuals}
The supplied readable counterpart constructs item logits $\ell_j=\log(\tilde\mu_j/(1-\tilde\mu_j))$, with item means clipped to $[10^{-4},1-10^{-4}]$. For a queried response vector $z$, it infers a scalar shift
\begin{equation}
\delta(z)=\arg\min_d\left\{\sum_{j\in Q}\left[\log(1+e^{\ell_j+d})-z_j(\ell_j+d)\right]+\frac{\eta}{2}d^2\right\}.
\end{equation}
It predicts a full-score curve $f(d)=N^{-1}\sum_j\sigmoid(\ell_j+d)$. For every source row, the shift is inferred using only its queried prefix, not its full response vector. Define query residuals $r_{mj}=X_{mj}-\sigmoid(\ell_j+\delta(X_{mQ}))$ and score residuals $t_m=s_m-f(\delta(X_{mQ}))$. Weighted centering gives $\bar r,\bar t$, and residual ridge coefficients
\begin{equation}
b=(R_c^\top W R_c+\lambda_r I)^{-1}R_c^\top W(t-\bar t).
\end{equation}
The target estimate is $f(\delta(z))+\bar t+(r(z)-\bar r)^\top b$, blended with the linear decoder and clipped. This residual term is supervised score correction, not a randomized audit or a finite-population unbiasedness correction.



The evaluator requests a fitting allowance of 200 and a settings cap of 4; these are interface allowances, not attested optimization-work counters. In the readable counterpart, the linear candidate list under that cap is $(\lambda,\alpha)\in\{(0.05,1),(0.01,1),(0.2,1),(0.05,0.5)\}$. The optional decoder's capped list comprises the linear fallback and $(\eta,\lambda_r,\gamma)\in\{(1,0.05,0.5),(1,0.05,1),(0.1,0.05,0.5)\}$, where $\gamma$ is the nonlinear blend weight. The wider uncapped list in the source is not the evaluated allowance. Source validation uses two folds and the 5/10/25 prefixes. Shift fitting uses a bounded Newton/bisection update, with at most 64 iterations and shifts bounded to $[-20,20]$. These details describe the source counterpart, not evidence that any particular setting was selected in a final case.





\subsection{Local Baseline Definitions}
Let $G$ be the number of item-content groups and $a_g$ the fraction of retained columns in group $g$. For a uniform sample of distinct group representatives, the implemented estimate is $\clip[(G/k)\sum_{j\in Q_k}a_{g(j)}y_j]$. Unequal group masses can therefore produce estimates outside the unit interval before clipping. The source prior is $\bar s$, independent of the target observations. Anchor embeddings center each item response vector using its weighted source item mean, multiply coordinates by $\sqrt{w_m}$, and normalize their lengths. Selection starts near the embedding mean, proceeds by farthest-point coverage among group representatives, and uses maximum inner product for assigning all columns to selected anchors. Assignment frequencies determine prediction weights.



Local IRT initializes difficulty from clipped weighted item means in $[0.005,0.995]$ and performs 200 alternating source updates of ability and difficulty with logistic probabilities and regularization. The ability origin is recentered by its weighted source mean. Target fitting holds difficulties fixed and uses 40 regularized ability updates from the uniformly queried items. Target prediction averages logistic probabilities over the retained item population. The source means inform initialization, but the fitted difficulty vector is not merely the negative initial logit after the source updates.


\subsection{Complete Benchmark--Budget Accuracy Results}
Table~\ref{tab:cases} gives seed-averaged errors for every final benchmark and budget, including all unfavorable package comparisons with IRT. The accompanying machine-readable file contains each seed separately and all reconstructed metrics. No absent cell is treated as a measured loss; the retained final records contain no failed normal cells. The protocol specifies fixed worst-case contributions for unavailable evaluations, but that rule is not invoked by this table.



\begin{table}[ht]
\centering
\caption{MAE in percentage points, averaged over the recorded seeds. All cases and budgets are retained.}
\label{tab:cases}


\begin{tabular}{lrrrrrr}
\toprule
Benchmark & Items & Package & IRT & Uniform & Prior & Anchors\\
\midrule
BBH & 5 & 3.69 & 9.16 & 19.07 & 9.98 & 20.16 \\
BBH & 10 & 2.72 & 7.13 & 12.66 & 9.98 & 19.05 \\
BBH & 25 & 2.18 & 5.10 & 6.85 & 9.98 & 15.52 \\
GPQA & 5 & 1.80 & 7.07 & 14.75 & 3.03 & 15.45 \\
GPQA & 10 & 1.68 & 6.15 & 9.89 & 3.03 & 10.32 \\
GPQA & 25 & 1.26 & 5.73 & 7.20 & 3.03 & 6.60 \\
MMLU-Pro & 5 & 4.06 & 8.36 & 15.02 & 11.37 & 23.01 \\
MMLU-Pro & 10 & 3.04 & 6.61 & 10.93 & 11.37 & 21.75 \\
MMLU-Pro & 25 & 2.32 & 4.70 & 6.03 & 11.37 & 20.67 \\
MuSR & 5 & 2.07 & 6.40 & 20.94 & 2.99 & 37.07 \\
MuSR & 10 & 1.82 & 5.07 & 13.76 & 2.99 & 19.89 \\
MuSR & 25 & 1.60 & 4.98 & 10.15 & 2.99 & 10.81 \\
Leaderboard MATH & 5 & 1.86 & 3.72 & 4.45 & 4.33 & 3.93 \\
Leaderboard MATH & 10 & 1.60 & 3.34 & 3.95 & 4.33 & 3.80 \\
Leaderboard MATH & 25 & 1.11 & 2.60 & 2.31 & 4.33 & 2.75 \\
LegalBench & 5 & 5.66 & 5.52 & 12.41 & 7.04 & 12.79 \\
LegalBench & 10 & 4.73 & 5.07 & 7.93 & 7.04 & 11.01 \\
LegalBench & 25 & 4.47 & 4.38 & 6.94 & 7.04 & 8.80 \\
HELM MATH & 5 & 11.63 & 9.53 & 15.15 & 17.14 & 27.42 \\
HELM MATH & 10 & 8.92 & 7.59 & 12.33 & 17.14 & 25.07 \\
HELM MATH & 25 & 6.19 & 5.61 & 6.66 & 17.14 & 20.86 \\
MedQA & 5 & 6.68 & 8.21 & 9.81 & 11.67 & 22.63 \\
MedQA & 10 & 7.47 & 6.56 & 10.96 & 11.67 & 20.71 \\
MedQA & 25 & 5.54 & 4.51 & 10.00 & 11.67 & 12.36 \\
MMLU & 5 & 4.58 & 7.88 & 20.88 & 7.47 & 14.34 \\
MMLU & 10 & 3.56 & 5.43 & 8.30 & 7.47 & 9.81 \\
MMLU & 25 & 3.05 & 3.20 & 4.74 & 7.47 & 6.62 \\
\bottomrule
\end{tabular}


\end{table}

\begin{figure}[ht]
\centering
\includegraphics[width=\textwidth]{figures/budget_sensitivity.pdf}
\caption{Budget sensitivity, averaging over the same retained benchmarks and seeds. Top: absolute score error. Bottom: lineage-level Spearman correlation. Lines connect query budgets on nested paths, not an optimization history. The constant source prior is omitted from both panels to keep the common four-method legend readable.}
\label{fig:budget}

\end{figure}

\subsection{Paired Uncertainty, Seeds, and Controls}
For a given benchmark, errors are first averaged within each target lineage over its rows, query budgets, and seeds. The difference between package and comparator is formed before resampling. Lineage identifiers are sampled with replacement within each benchmark, and the sampled means are averaged with equal benchmark weights. The stored 200 draws give the 2.5th and 97.5th percentiles. Bootstrap randomness uses seed 1729. The four comparator intervals share this procedure, but are not presented as simultaneous confidence intervals. Repeating the same stored uncertainty object in seed records adds no information.



\begin{table}[ht]
\centering
\caption{Descriptive seed variation for the package, with equal benchmark and budget weights. Error units are percentage points. These seeds do not change the frozen data partitions.}
\label{tab:seeds}


\begin{tabular}{rrrrr}
\toprule
Seed & MAE & RMSE & Spearman & Kendall\\
\midrule
1009 & 3.816 & 4.674 & 0.8238 & 0.6777 \\
2003 & 4.006 & 4.941 & 0.8148 & 0.6689 \\
3001 & 3.876 & 4.899 & 0.8089 & 0.6682 \\
\bottomrule
\end{tabular}


\end{table}

The source prior produces identical predictions across target rows. A meaningful rank correlation is therefore undefined. The evaluator uses a negative sentinel for exact degeneracy, but floating-point differences in averages of identical values can also defeat that exact-equality test. We omit the prior's ranking outputs rather than interpreting such implementation artifacts as negative predictive association. The package and nonconstant comparator correlations in Table~\ref{tab:main} are reconstructed using the recorded lineage-mean convention.



In the all-zero condition, queried values are overwritten without changing full-score references. In the rotated-source condition, each source row receives an independently drawn nonzero cyclic item shift, preserving row scores but breaking aligned item-response structure. A duplicate target with the same queried history checks row-position invariance; the normal BBH replay checks repeatability. Passing these checks constrains observed behavior, not all possible leakage or validity threats.



\subsection{Reproduction and Evidence Boundaries}
The retained matrices originate from the supplied benchmark-prediction data snapshot at commit \texttt{55faff496947789f94e6b5908c77cbc3e84f81ad}. The frozen manifests preserve retained column indices, model rows, content normalization, lineage policy, and resource hashes. Raw upstream matrices alone do not reproduce the frozen splits without this metadata. The attached reproduction guide separates deterministic reconstruction of manuscript artifacts from an optional fresh evaluation, which was not run for this paper. It also documents the input resources required by the original evaluator rather than suggesting they can be recovered from scalar metrics.



Inspectability is provided by \path{source_evidence/selected/src/surrogate.py} (weighted statistics, acquisition, linear decoder, and tuning), \path{source_evidence/selected/src/nonlinear_decoder.py} (optional decoder and nested source fitting), and \path{source_evidence/selected/src/program.py} (observation interface). Locations are indexed in \path{source_evidence/LOCATIONS.md}; byte hashes and source-identity limitations are recorded in \path{source_evidence/inventory.json}. The evaluator definitions are in \path{source_evidence/evaluator/evaluate_final.py}. Hashes identify artifacts but are not substitutes for inspecting their content.

Numerical postprocessing uses NumPy \citep{Harris2020} and SciPy \citep{Virtanen2020}; plots use Matplotlib \citep{Hunter2007}. The analysis script reads the immutable evidence registry, excludes replay, reconciles aggregate metrics, and exports tables, vector PDF plots, PNG previews, and provenance sidecars. The conceptual figure is separately prepared from the manuscript's information-flow description, not from synthetic results. Literature consultation used direct permitted identifiers and abstracts, with no citation-network expansion. Inaccessible classical sources were not cited on metadata alone. No prohibited-study encounter was identified during this writing step; unsuccessful direct links are documented in the reproduction guide.

\subsection{LLM Usage}
LLM assistance was used to propose research designs, edit estimator implementations, plan reference queries, inspect supplied code and evaluator artifacts, synthesize the manuscript framing, write the LaTeX and plotting scripts, and check evidence links. The present manuscript step consulted directly retrieved literature abstracts and performed deterministic postprocessing of recorded predictions; it did not execute new model evaluations or component ablations. The conceptual overview is prepared through an automated diagram workflow. Evaluator-produced measurements are distinguished from LLM-generated interpretation and source descriptions. No independent human review or verification is claimed.
```
