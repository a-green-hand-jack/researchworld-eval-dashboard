# Agentic evidence audit packet

- generated_at: `2026-11-07T05:56:18.872368+00:00`
- paper_dir: `work/results/t10/codex/20261107_014149/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261107_044409-paper_evidence_audit_round_3-70zui7xv/workspace`

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
    "anchored_references": 70,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 80,
    "resolved_references": 47,
    "total_references": 117
  },
  "ok": true,
  "pdf_path": "work/results/t10/codex/20261107_014149/paper/paper.pdf"
}
```

## scientific-evidence verification summary

```json
{
  "available": true,
  "dangling_preview": [],
  "summary": {
    "anchored_references": 70,
    "dangling_references": 0,
    "manifests_checked": 14,
    "resolved_references": 47,
    "total_references": 117
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "The sealed record contains 256 repetitions, 7 paired conditions per repetition, and seeds 1001\u20131256.",
      "evidence_refs": [
        "paper_data.json#/final_evaluation/evaluation_evidence/episodes"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1 has the recorded truth(s) [0.35333333333333333].",
      "evidence_refs": [
        "analysis_results.json#/cases/0/truths"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, candidate: empirical coverage 0.9375, pointwise exact-binomial 95% limits [0.9004864688995705, 0.9638572392101775]; mean width 0.14182978478950226; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/methods/candidate",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, ppi_plus_plus_mean: empirical coverage 0.9453125, pointwise exact-binomial 95% limits [0.9099452021659431, 0.9697828246470755]; mean width 0.13959873973837972; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/methods/ppi_plus_plus_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, prediction_powered_mean: empirical coverage 0.9453125, pointwise exact-binomial 95% limits [0.9099452021659431, 0.9697828246470755]; mean width 0.1405280149459788; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/methods/prediction_powered_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, labeled_only_asymptotic_mean: empirical coverage 0.9296875, pointwise exact-binomial 95% limits [0.8911506533267348, 0.9577987580697637]; mean width 0.16486419259480717; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/methods/labeled_only_asymptotic_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, labeled_only_exact_binomial: empirical coverage 0.94921875, pointwise exact-binomial 95% limits [0.9147278740435402, 0.9726874749946139]; mean width 0.1710390034312684; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/methods/labeled_only_exact_binomial",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, score-control minus ppi_plus_plus_mean mean-width difference 0.002231045051122553, pointwise paired-t 95% limits [0.0016312079639663308, 0.002830882138278775].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/differences/ppi_plus_plus_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, score-control minus prediction_powered_mean mean-width difference 0.0013017698435234747, pointwise paired-t 95% limits [0.0006900711901725142, 0.0019134684968744352].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/differences/prediction_powered_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, score-control minus labeled_only_asymptotic_mean mean-width difference -0.023034407805304913, pointwise paired-t 95% limits [-0.02416861903242587, -0.021900196578183956].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/differences/labeled_only_asymptotic_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C1, score-control minus labeled_only_exact_binomial mean-width difference -0.02920921864176612, pointwise paired-t 95% limits [-0.03034122810837431, -0.028077209175157932].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/0/differences/labeled_only_exact_binomial",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2 has the recorded truth(s) [0.35333333333333333].",
      "evidence_refs": [
        "analysis_results.json#/cases/1/truths"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, candidate: empirical coverage 0.94140625, pointwise exact-binomial 95% limits [0.9051991415444257, 0.9668381679733287]; mean width 0.0697702159925469; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/methods/candidate",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, ppi_plus_plus_mean: empirical coverage 0.94140625, pointwise exact-binomial 95% limits [0.9051991415444257, 0.9668381679733287]; mean width 0.07007194859410643; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/methods/ppi_plus_plus_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, prediction_powered_mean: empirical coverage 0.94140625, pointwise exact-binomial 95% limits [0.9051991415444257, 0.9668381679733287]; mean width 0.07041467422210129; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/methods/prediction_powered_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, labeled_only_asymptotic_mean: empirical coverage 0.93359375, pointwise exact-binomial 95% limits [0.8958044309384742, 0.9608432005610229]; mean width 0.08266351878895006; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/methods/labeled_only_asymptotic_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, labeled_only_exact_binomial: empirical coverage 0.94921875, pointwise exact-binomial 95% limits [0.9147278740435402, 0.9726874749946139]; mean width 0.0844207588520158; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/methods/labeled_only_exact_binomial",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, score-control minus ppi_plus_plus_mean mean-width difference -0.00030173260155952255, pointwise paired-t 95% limits [-0.0004003584986522063, -0.0002031067044668388].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/differences/ppi_plus_plus_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, score-control minus prediction_powered_mean mean-width difference -0.0006444582295543812, pointwise paired-t 95% limits [-0.0007421531914902672, -0.0005467632676184953].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/differences/prediction_powered_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, score-control minus labeled_only_asymptotic_mean mean-width difference -0.012893302796403145, pointwise paired-t 95% limits [-0.01314292436908393, -0.01264368122372236].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/differences/labeled_only_asymptotic_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C2, score-control minus labeled_only_exact_binomial mean-width difference -0.014650542859468891, pointwise paired-t 95% limits [-0.014900022759040066, -0.014401062959897716].",
      "derivation": "Paired endpoint width differences over repetitions; t critical value with R-1 degrees of freedom; no multiple-comparison adjustment.",
      "evidence_refs": [
        "analysis_results.json#/cases/1/differences/labeled_only_exact_binomial",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C3 has the recorded truth(s) [0.5].",
      "evidence_refs": [
        "analysis_results.json#/cases/2/truths"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C3, candidate: empirical coverage 0.95703125, pointwise exact-binomial 95% limits [0.9244190662295707, 0.9783579593956968]; mean width 0.1543715486486784; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/2/methods/candidate",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C3, ppi_plus_plus_mean: empirical coverage 0.95703125, pointwise exact-binomial 95% limits [0.9244190662295707, 0.9783579593956968]; mean width 0.1509424492661709; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs": [
        "analysis_results.json#/cases/2/methods/ppi_plus_plus_mean",
        "scripts/build_artifacts.py"
      ],
      "source_ids": [
        "final.evidence.episodes"
      ]
    },
    {
      "citation_keys": [],
      "claim": "C3, prediction_powered_mean: empirical coverage 0.9609375, pointwise exact-binomial 95% limits [0.9293377140998709, 0.9811117242805399]; mean width 0.15224192469242806; zero-width intervals 0.",
      "derivation": "Coverage from closed recorded endpoints; width upper-lower; binomial inversion over repetitions. Assumes repeated-sampling model for inferential interpretation.",
      "evidence_refs

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
  "grounding_source_count": 18,
  "paper_profile": "standalone",
  "totals": {
    "attempts": 3,
    "correct_programs": 1,
    "evaluated_programs": 1,
    "ideas": 3
  }
}
```

## references provenance summary

```json
{
  "count": 25,
  "generated_at": "2026-11-07T05:29:17.302340+00:00",
  "queries": [
    "Exact permitted starter identifiers and pre-screened historical DOI lookups; no citation network traversal"
  ],
  "references": [
    {
      "abstract_available": true,
      "citation_key": "AgrestiCoull1998",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/AgrestiCoull1998.json",
      "id": "ref.doi.10.1080/00031305.1998.10480550",
      "paper_id": "10.1080/00031305.1998.10480550",
      "query": "Exact DOI 10.1080/00031305.1998.10480550",
      "retrieved_at": "2026-11-07T05:06:58.186566+00:00",
      "source_url": "https://api.crossref.org/works/10.1080%2F00031305.1998.10480550",
      "title": "Approximate is Better than \u201cExact\u201d for Interval Estimation of Binomial Proportions",
      "venue": "The American Statistician",
      "year": 1998
    },
    {
      "abstract_available": true,
      "citation_key": "Angelopoulos2023PPI",
      "consultation_scope": "Selected primary PDF pages",
      "consulted_text_path": "literature/Angelopoulos2023PPI_consulted.txt",
      "id": "ref.doi.10.1126/science.adi6000",
      "paper_id": "10.1126/science.adi6000",
      "query": "Exact DOI 10.1126/science.adi6000",
      "retrieved_at": "2026-11-07T05:04:30.849053+00:00",
      "source_url": "https://api.crossref.org/works/10.1126%2Fscience.adi6000",
      "title": "Prediction-powered inference",
      "venue": "Science",
      "year": 2023
    },
    {
      "citation_key": "Angelopoulos2023PPIpp",
      "consultation_scope": "Selected primary PDF pages",
      "consulted_text_path": "literature/Angelopoulos2023PPIpp_consulted.txt",
      "id": "ref.arxiv.2311.01453",
      "paper_id": "2311.01453",
      "query": "Exact permitted arXiv identifier 2311.01453",
      "source_url": "https://arxiv.org/abs/2311.01453",
      "title": "PPI++: Efficient Prediction-Powered Inference",
      "venue": "arXiv",
      "year": 2023
    },
    {
      "abstract_available": false,
      "citation_key": "Audibert2009",
      "consultation_scope": "HAL abstract for the exact historical work",
      "consulted_text_path": "literature/Audibert2009_consulted.json",
      "id": "ref.doi.10.1016/j.tcs.2009.01.016",
      "paper_id": "10.1016/j.tcs.2009.01.016",
      "query": "Exact DOI 10.1016/j.tcs.2009.01.016",
      "retrieved_at": "2026-11-07T05:07:02.145352+00:00",
      "source_url": "https://api.crossref.org/works/10.1016%2Fj.tcs.2009.01.016",
      "title": "Exploration\u2013exploitation tradeoff using variance estimates in multi-armed bandits",
      "venue": "Theoretical Computer Science",
      "year": 2009
    },
    {
      "abstract_available": true,
      "citation_key": "BenjaminiHochberg1995",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/BenjaminiHochberg1995.json",
      "id": "ref.doi.10.1111/j.2517-6161.1995.tb02031.x",
      "paper_id": "10.1111/j.2517-6161.1995.tb02031.x",
      "query": "Exact DOI 10.1111/j.2517-6161.1995.tb02031.x",
      "retrieved_at": "2026-11-07T05:07:07.138089+00:00",
      "source_url": "https://api.crossref.org/works/10.1111%2Fj.2517-6161.1995.tb02031.x",
      "title": "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing",
      "venue": "Journal of the Royal Statistical Society Series B: Statistical Methodology",
      "year": 1995
    },
    {
      "abstract_available": true,
      "citation_key": "BlythStill1983",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/BlythStill1983.json",
      "id": "ref.doi.10.1080/01621459.1983.10477938",
      "paper_id": "10.1080/01621459.1983.10477938",
      "query": "Exact DOI 10.1080/01621459.1983.10477938",
      "retrieved_at": "2026-11-07T05:23:25.602603+00:00",
      "source_url": "https://api.crossref.org/works/10.1080%2F01621459.1983.10477938",
      "title": "Binomial Confidence Intervals",
      "venue": "Journal of the American Statistical Association",
      "year": 1983
    },
    {
      "abstract_available": true,
      "citation_key": "BrownCaiDasGupta2001",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/BrownCaiDasGupta2001.json",
      "id": "ref.doi.10.1214/ss/1009213286",
      "paper_id": "10.1214/ss/1009213286",
      "query": "Exact DOI 10.1214/ss/1009213286",
      "retrieved_at": "2026-11-07T05:04:31.505743+00:00",
      "source_url": "https://api.crossref.org/works/10.1214%2Fss%2F1009213286",
      "title": "Interval Estimation for a Binomial Proportion",
      "venue": "Statistical Science",
      "year": 2001
    },
    {
      "abstract_available": true,
      "citation_key": "Chernozhukov2018DML",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/Chernozhukov2018DML.json",
      "id": "ref.doi.10.1111/ectj.12097",
      "paper_id": "10.1111/ectj.12097",
      "query": "Exact DOI 10.1111/ectj.12097",
      "retrieved_at": "2026-11-07T05:06:56.000799+00:00",
      "source_url": "https://api.crossref.org/works/10.1111%2Fectj.12097",
      "title": "Double/debiased machine learning for treatment and structural parameters",
      "venue": "The Econometrics Journal",
      "year": 2018
    },
    {
      "abstract_available": true,
      "citation_key": "DevilleSarndal1992",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/DevilleSarndal1992.json",
      "id": "ref.doi.10.1080/01621459.1992.10475217",
      "paper_id": "10.1080/01621459.1992.10475217",
      "query": "Exact DOI 10.1080/01621459.1992.10475217",
      "retrieved_at": "2026-11-07T05:04:33.883481+00:00",
      "source_url": "https://api.crossref.org/works/10.1080%2F01621459.1992.10475217",
      "title": "Calibration Estimators in Survey Sampling",
      "venue": "Journal of the American Statistical Association",
      "year": 1992
    },
    {
      "abstract_available": true,
      "citation_key": "Efron1979",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/Efron1979.json",
      "id": "ref.doi.10.1214/aos/1176344552",
      "paper_id": "10.1214/aos/1176344552",
      "query": "Exact DOI 10.1214/aos/1176344552",
      "retrieved_at": "2026-11-07T05:07:03.539550+00:00",
      "source_url": "https://api.crossref.org/works/10.1214%2Faos%2F1176344552",
      "title": "Bootstrap Methods: Another Look at the Jackknife",
      "venue": "The Annals of Statistics",
      "year": 1979
    },
    {
      "abstract_available": true,
      "citation_key": "EfronStein1981",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/EfronStein1981.json",
      "id": "ref.doi.10.1214/aos/1176345462",
      "paper_id": "10.1214/aos/1176345462",
      "query": "Exact DOI 10.1214/aos/1176345462",
      "retrieved_at": "2026-11-07T05:04:32.226146+00:00",
      "source_url": "https://api.crossref.org/works/10.1214%2Faos%2F1176345462",
      "title": "The Jackknife Estimate of Variance",
      "venue": "The Annals of Statistics",
      "year": 1981
    },
    {
      "abstract_available": false,
      "citation_key": "EfronTibshirani1993",
      "consultation_scope": "Publisher synopsis",
      "consulted_text_path": "literature/EfronTibshirani1993_consulted_excerpt.json",
      "id": "ref.doi.10.1007/978-1-4899-4541-9",
      "paper_id": "10.1007/978-1-4899-4541-9",
      "query": "Exact DOI 10.1007/978-1-4899-4541-9",
      "retrieved_at": "2026-11-07T05:13:24.694063+00:00",
      "source_url": "https://api.crossref.org/works/10.1007%2F978-1-4899-4541-9",
      "title": "An Introduction to the Bootstrap",
      "venue": "",
      "year": 1993
    },
    {
      "abstract_available": false,
      "citation_key": "Glasserman2004",
      "consultation_scope": "Publisher synopsis",
      "consulted_text_path": "literature/Glasserman2004_consulted.json",
      "id": "ref.doi.10.1007/978-0-387-21617-1",
      "paper_id": "10.1007/978-0-387-21617-1",
      "query": "Exact DOI 10.1007/978-0-387-21617-1",
      "retrieved_at": "2026-11-07T05:04:33.150475+00:00",
      "source_url": "https://api.crossref.org/works/10.1007%2F978-0-387-21617-1",
      "title": "Monte Carlo Methods in Financial Engineering",
      "venue": "Stochastic Modelling and Applied Probability",
      "year": 2003
    },
    {
      "abstract_available": true,
      "citation_key": "Golub1979GCV",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/Golub1979GCV.json",
      "id": "ref.doi.10.1080/00401706.1979.10489751",
      "paper_id": "10.1080/00401706.1979.10489751",
      "query": "Exact DOI 10.1080/00401706.1979.10489751",
      "retrieved_at": "2026-11-07T05:04:32.593481+00:00",
      "source_url": "https://api.crossref.org/works/10.1080%2F00401706.1979.10489751",
      "title": "Generalized Cross-Validation as a Method for Choosing a Good Ridge Parameter",
      "venue": "Technometrics",
      "year": 1979
    },
    {
      "abstract_available": false,
      "citation_key": "Hastie2009",
      "consultation_scope": "Publisher synopsis; full text unavailable",
      "consulted_text_path": "literature/Hastie2009_consulted.json",
      "id": "ref.doi.10.1007/978-0-387-84858-7",
      "paper_id": "10.1007/978-0-387-84858-7",
      "query": "Exact DOI 10.1007/978-0-387-84858-7",
      "retrieved_at": "2026-11-07T05:04:33.195357+00:00",
      "source_url": "https://api.crossref.org/works/10.1007%2F978-0-387-84858-7",
      "title": "The Elements of Statistical Learning",
      "venue": "Springer Series in Statistics",
      "year": 2009
    },
    {
      "abstract_available": true,
      "citation_key": "Hoeffding1963",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/Hoeffding1963.json",
      "id": "ref.doi.10.1080/01621459.1963.10500830",
      "paper_id": "10.1080/01621459.1963.10500830",
      "query": "Exact DOI 10.1080/01621459.1963.10500830",
      "retrieved_at": "2026-11-07T05:07:00.060449+00:00",
      "source_url": "https://api.crossref.org/works/10.1080%2F01621459.1963.10500830",
      "title": "Probability Inequalities for Sums of Bounded Random Variables",
      "venue": "Journal of the American Statistical Association",
      "year": 1963
    },
    {
      "abstract_available": true,
      "citation_key": "HoerlKennard1970",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/HoerlKennard1970.json",
      "id": "ref.doi.10.1080/00401706.1970.10488634",
      "paper_id": "10.1080/00401706.1970.10488634",
      "query": "Exact DOI 10.1080/00401706.1970.10488634",
      "retrieved_at": "2026-11-07T05:04:32.616413+00:00",
      "source_url": "https://api.crossref.org/works/10.1080%2F00401706.1970.10488634",
      "title": "Ridge Regression: Biased Estimation for Nonorthogonal Problems",
      "venue": "Technometrics",
      "year": 1970
    },
    {
      "abstract_available": true,
      "citation_key": "LittleRubin2019",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/LittleRubin2019.json",
      "id": "ref.doi.10.1002/9781119013563",
      "paper_id": "10.1002/9781119013563",
      "query": "Exact DOI 10.1002/9781119013563",
      "retrieved_at": "2026-11-07T05:04:33.767133+00:00",
      "source_url": "https://api.crossref.org/works/10.1002%2F9781119013563",
      "title": "Statistical Analysis with Missing Data",
      "venue": "Wiley Series in Probability and Statistics",
      "year": 2002
    },
    {
      "citation_key": "MaurerPontil2009",
      "consultation_scope": "Primary PDF pages including empirical-Bernstein theorem",
      "consulted_text_path": "literature/MaurerPontil2009_consulted.txt",
      "id": "ref.arxiv.0907.3740",
      "paper_id": "0907.3740",
      "query": "Exact permitted arXiv identifier 0907.3740",
      "source_url": "https://arxiv.org/abs/0907.3740",
      "title": "Empirical Bernstein Bounds and Sample Variance Penalization",
      "venue": "arXiv",
      "year": 2009
    },
    {
      "abstract_available": true,
      "citation_key": "Newcombe1998",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/Newcombe1998.json",
      "id": "ref.doi.10.1002/(sici)1097-0258(19980430)17:8<857::aid-sim777>3.0.co;2-e",
      "paper_id": "10.1002/(sici)1097-0258(19980430)17:8<857::aid-sim777>3.0.co;2-e",
      "query": "Exact DOI 10.1002/(sici)1097-0258(19980430)17:8<857::aid-sim777>3.0.co;2-e",
      "retrieved_at": "2026-11-07T05:23:22.603644+00:00",
      "source_url": "https://api.crossref.org/works/10.1002%2F%28sici%291097-0258%2819980430%2917%3A8%3C857%3A%3Aaid-sim777%3E3.0.co%3B2-e",
      "title": "Two-sided confidence intervals for the single proportion: comparison of seven methods",
      "venue": "Statistics in Medicine",
      "year": 1998
    },
    {
      "abstract_available": true,
      "citation_key": "Robinson1988",
      "consultation_scope": "Abstract, not full paper",
      "consulted_text_path": "literature/Robinson1988.json",
      "id": "ref.doi.10.2307/1912705",
      "paper_id": "10.2307/1912705",
      "query": "Exact DOI 10.2307/1912705",
      "retrieved_at": "2026-11-07T05:04:35.061935+00:00",
      "source_url": "https://api.crossref.org/works/10.2307%2F1912705",
      "title": "Root-N-Consistent Semiparametric Regression",
      "venue": "Econometrica",
      "year": 1988
    },
    {
      "abstract_available": false,
      "citation_key": "Sarndal1992",
      "consultation_scope": "Book synopsis",
      "consulted_text_path": "literature/Sarndal1992_consulted_excerpt.json",
      "id": "ref.doi.10.1007/978-1-4612-4378-6",
      "paper_id": "10.1007/978-1-4612-4378-6",
      "query": "Exact DOI 10.1007/978-1-4612-4378-6

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
\usepackage{amsmath,amssymb,booktabs,graphicx,subcaption,longtable}
\usepackage{hyperref,url}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Var}{\operatorname{Var}}
\newcommand{\clip}{\operatorname{clip}}
\title{Frozen-Score Controls for Mean Inference:\\Width Gains and Coverage Limitations}
\author{}

\begin{document}
\maketitle

\begin{abstract}
Can confidence intervals become narrower when labels, unlabeled observations, and the predictor are unchanged? We examine inference-side calibration of frozen scores for a binary population mean, using paired interval records from seven evaluation conditions and 256 repetitions per condition. The associated implementation fits honest, regularized score controls and returns a stabilized asymptotic interval; its bounded finite-sample construction is separate and unmeasured. Relative to the evaluated PPI++ comparator, mean width decreases in only one condition, by 0.000302, and increases in the other six. In the condition with population mean 0.0068, PPI++ coverage is 0.551 and 115 intervals collapse, whereas score-control coverage is 0.930 without collapse. However, the score-control width difference from exact-binomial inference is inconclusive, and pooled empirical coverage of 0.943 does not establish nominal validity. These results support condition-specific comparisons, not uniformly shorter valid intervals. Missing condition generators, sample-size metadata, and a matched calibration ablation limit reproducibility and mechanistic attribution.



\end{abstract}

\section{Introduction}
Scientific inference increasingly uses a small collection of expensive gold-standard labels together with predictions available on a larger collection of observations. The scientific target is often simpler than individual prediction: a prevalence, an average response, or another population summary. Prediction-powered inference uses labels to correct prediction error rather than treating machine predictions as truth \citep{Angelopoulos2023PPI}. This distinction matters when the predictor is useful but imperfect. It also motivates a constrained question: once the observations and predictor are fixed, is there still room to improve the uncertainty attached to the population mean?

The constraint excludes acquiring labels, enlarging the unlabeled sample, or replacing the prediction model. It does not exclude fitting an inference-side transformation of its scalar output. A nonlinear transformation might make the score a better control variate for the outcome. Yet estimating this transformation consumes statistical information, and an interval can become shorter simply because its uncertainty calculation is inadequate. Thus, width alone cannot answer the question. Any efficiency claim must distinguish information extraction from estimation noise and must confront repeated-sampling coverage.

We study \emph{honest frozen-score controls}: complementary labeled subsets fit a small regularized calibration family, while held-out labels correct its errors. A fixed-control variance identity explains the potential benefit of approximating the conditional outcome mean given the score. It also identifies a boundary on what calibration can accomplish: it cannot recover information absent from the frozen score. The evaluated interval uses a stabilized asymptotic variance approximation. A distinct bounded construction clarifies what a finite-sample argument would require, but its empirical efficiency is not observed here.

Our central empirical finding is limited and asymmetric. Among seven conditions, only C2 has a negative paired mean-width difference relative to the evaluated PPI++ interval; the remaining six differences are positive. A low-prevalence condition exposes severe undercoverage and collapsed intervals for two asymptotic comparators. The score-control interval avoids these observed collapses but does not establish nominal coverage or an advantage over exact inference. These are comparisons of recorded intervals, not a causal test of nonlinear calibration.


The contributions are threefold: separating fixed-score efficiency potential from inference assumptions; a complete paired comparison retaining favorable and unfavorable conditions; and a failure analysis distinguishing non-collapse, narrowness, and validity. Missing generators and controlled ablations remain explicit limitations rather than being filled with inferred mechanisms.

\begin{figure}[t]
\centering
\begin{minipage}[c][1.8in][c]{\textwidth}
\centering
\includegraphics[width=\textwidth,height=1.8in,keepaspectratio]{figures/frozen_score_overview.png}
\end{minipage}
\caption{Inference with unchanged observations and a frozen predictor. Complementary labeled folds fit score-only controls; held-out residual correction targets the population mean. The evaluated stabilized asymptotic interval and the separate, unmeasured bounded safety construction must not be conflated. No new labels or predictor training are part of this comparison.}
\label{fig:overview}

\end{figure}

\section{Related Work}
\paragraph{Prediction-assisted estimation.}
PPI supplies the central correction principle: combine predictions with a labeled estimate of their error \citep{Angelopoulos2023PPI}. PPI++ adapts the contribution of predictions to improve statistical and computational efficiency under its assumptions \citep{Angelopoulos2023PPIpp}. Our empirical baseline is the \emph{evaluated PPI++ comparator}, not a claim about every implementation or theoretical formulation of PPI++. Classical control variates likewise exploit correlated auxiliary quantities to reduce Monte Carlo variance \citep{Glasserman2004}. Survey calibration and model-assisted estimation use auxiliary information in a related spirit \citep{DevilleSarndal1992,Sarndal1992}; their finite-population targets should not be silently substituted for the superpopulation target studied here. Missing-data theory provides additional context for assumptions connecting observed and unobserved outcomes \citep{LittleRubin2019}.

\paragraph{Fitted controls and sample separation.}
Residualization with estimated functions is familiar in semiparametric inference \citep{Robinson1988,VanDerVaart1998}. Double/debiased machine learning combines orthogonal corrections with sample separation to control nuisance-estimation effects \citep{Chernozhukov2018DML}. We use complementary training folds, but do not infer finite-sample validity from that structural similarity. Ridge regularization \citep{HoerlKennard1970}, generalized cross-validation \citep{Golub1979GCV}, and cross-validatory prediction assessment \citep{Stone1974} motivate the archived calibration choices. A small linear-spline dictionary is a standard approximation device \citep{Hastie2009}, not evidence that the dictionary matches the unknown conditional mean in these conditions.

\paragraph{Intervals near the boundary.}
Exact binomial inversion \citep{BlythStill1983}, score-based intervals \citep{Newcombe1998}, adjusted approximations \citep{AgrestiCoull1998}, and analyses of erratic Wald coverage \citep{BrownCaiDasGupta2001} motivate retaining an exact reference rather than comparing only against a normal approximation. A Wilson-style adjustment to a fitted-control estimator is not the binomial Wilson procedure. For bounded observations, concentration inequalities \citep{Hoeffding1963} and empirical-Bernstein bounds \citep{MaurerPontil2009} offer another route, at potentially substantial width cost. Variance-sensitive concentration also appears in sequential allocation \citep{Audibert2009}; no active allocation is used here. The relevant distinction is between an assumption-dependent coverage argument and an observed coverage estimate, not between a favorable and unfavorable average width.

\section{Method}
\subsection{Target, Constraints, and the Efficiency Question}
Let $(Y_i,S_i)_{i=1}^n$ denote labeled observations, where $Y_i\in\{0,1\}$ and $S_i=f(X_i)\in[0,1]$. The unlabeled observations contribute scores $(S_j^U)_{j=1}^N$. The predictor $f$ is fixed. The target is
\begin{equation}
\mu=\E[Y],\qquad
\Pr\{\mu\in I\}\geq 1-\alpha,
\label{eq:target}
\end{equation}
with interval width $|I|$ as the efficiency criterion. The nominal level in the recorded interface is $1-\alpha=0.95$. The method receives only labeled outcomes and labeled/unlabeled scores, not a population truth or condition identity.


For the analysis of estimators, assume independent iid labeled pairs and iid unlabeled scores from the same population, with the predictor frozen independently of the inference labels. These are explicit statistical assumptions, not facts established by the unidentified condition generators. ``Fixed inputs'' means that compared methods have the same observations within a repetition. It does not mean conditioning away all repeated-sampling randomness, nor does it change the target to the realized mean of an observed finite pool. Different targets require different coverage arguments.

The practical question is whether a fitted transformation of $S$ can reduce width \emph{without losing the coverage requirement}. We do not optimize the reported width over the observed repetitions. Instead, we compare the sealed interval outputs and retain coverage and width as separate outcomes. This prevents interpreting a narrow but under-covering interval as an efficiency solution.

\subsection{Design Rationale: What a Frozen Score Can Offer}
For a fixed square-integrable control $g$, write $\rho=N/(n+N)$ and consider
\begin{equation}
\widehat\mu_g=\overline{Y-\rho g(S)}_L+\rho\overline{g(S)}_U,
\quad
\Var(\widehat\mu_g)=\frac{\Var(Y-\rho g(S))}{n}
+\frac{\rho^2\Var(g(S))}{N}.
\label{eq:fixed}
\end{equation}
Equal score distributions in the labeled and unlabeled samples ensure cancellation of the control's expectation. There is no requirement that $g$ itself predict the outcome without bias. The finite-$N$ factor recognizes uncertainty in the unlabeled average rather than treating it as a known population moment.

Let $m(S)=\E[Y\mid S]$. Expanding the variance in Equation~\ref{eq:fixed} gives
\begin{align}
\Var(\widehat\mu_m)&=\frac{\E[\Var(Y\mid S)]}{n}
+\frac{\Var(m(S))}{n+N},\label{eq:oracle}\\
\Var(\widehat\mu_g)-\Var(\widehat\mu_m)
&=\frac{\rho}{n}\Var\{g(S)-m(S)\}.\label{eq:excess}
\end{align}

The identity describes a population oracle among fixed controls, up to additive constants. It suggests a rationale for nonlinear calibration when the score--outcome relationship departs from an affine function. It is not a claim that the finite fitted dictionary attains this oracle. Nor is a variance identity automatically a confidence-interval theorem for a data-adaptive control. Constant or uninformative scores offer no auxiliary variance reduction in this calculation; labels still determine the irreducible outcome-noise term.

\subsection{Archived Honest Calibration Construction}
The inspectable implementation associated with the selected method uses two labeled folds and two unlabeled folds from independent permutations initialized by the repetition seed. For labeled fold $L_k$, the opposite labeled fold fits $g_{-k}$. Its intercept, feature centering, feature scaling, spline knots, and regularization choice all use that training fold only. Neither held-out scores nor unlabeled scores tune the calibration. After fitting, evaluated controls are clipped to $[0,1]$.



The family includes an intercept, a ridge affine function, and linear splines with training-score quantile knots. Up to three quartile knots become available at training size 16; up to seven quantile knots become available at size 64. The ridge penalties are $\{0.001,0.01,0.1,1,10\}$. Training-only GCV chooses a fit relative to the constant candidate. Constant-score or very small training samples retain the intercept. These choices specify the archived code, not measured hyperparameter sensitivities.


The fold estimate and aggregate estimate are
\begin{equation}
\widehat\mu_k=\overline{Y-\rho g_{-k}(S)}_{L_k}
+\rho\overline{g_{-k}(S)}_{U_k},\qquad
\widehat\mu=\sum_{k=1}^{2}w_k\widehat\mu_k,\quad w_k=|L_k|/n.
\label{eq:fold}
\end{equation}

Training separation prevents an observation's label from fitting its own control. It does not make the fitted folds unconditionally independent: a label held out in one fold trains the other fold's control. The implementation retains all held-out residuals and unlabeled control values for a pooled variance approximation. It also contains an affine-only matched function, but no measured affine-versus-spline ablation is available. Therefore, the empirical comparison concerns the complete interval construction.

\subsection{Returned Interval and Separate Safety Construction}
Let $R_i=Y_i-\rho g_{-k(i)}(S_i)$ and $Q_j=\rho g_{-k(j)}(S_j^U)$. The archived asymptotic calculation is
\begin{equation}
\widehat V=\frac{s_R^2}{n}+\frac{s_Q^2}{N},\quad
a=\frac{z_{1-\alpha/2}^2}{n},\quad
c=\frac{\widehat\mu+a/2}{1+a},\quad
r=\frac{z_{1-\alpha/2}\sqrt{\widehat V+z_{1-\alpha/2}^2/(4n^2)}}{1+a}.
\label{eq:stabilized}
\end{equation}
The endpoints are $\clip(c-r,0,1)$ and $\clip(c+r,0,1)$. This boundary stabilization supplies a positive radius when the empirical variance vanishes, but it does not prove coverage for a fitted-control estimator. The pooled variance also approximates unequal fold weights when sample sizes are odd. For $n<16$, a sample-size-only rule instead returns a labeled-only Clopper--Pearson interval. This branch does not confer exact validity on the other sample sizes.



The same source computes a distinct empirical-Bernstein interval by bounding each held-out residual mean and unlabeled control mean. Conditional on training, their ranges are $[-\rho,1]$ and $[0,\rho]$. Componentwise bounds, a union bound, and the same fixed nonnegative fold weights give a finite-sample argument under the iid assumptions. Crucially, these endpoints are not returned by the primary interface, compared with the asymptotic endpoints, or selected by their widths. No coverage or width measurement for that safety construction is available. Supplementary Information supplies its argument and the fixed-control variance derivation.


\section{Experimental Protocol and Evidence Scope}
\subsection{Paired Records and Comparators}
The completed sealed evaluation contains 256 seeded repetitions, with seven conditions in each repetition. We denote the conditions C1--C7, preserving their recorded identities. Every record supplies the truth, the score-control endpoints, and endpoints for evaluated PPI++, PPI, labeled-only asymptotic mean inference, labeled-only exact-binomial inference, and a full-range sanity interval. The inferential tables include all five nontrivial methods; $[0,1]$ is retained as a sanity reference rather than an efficiency headline. No scored repetition or unfavorable condition is removed.


The records omit condition generators, dataset names, per-condition $n,N$, raw scores, and label arrays. Recorded truths do not identify calibration nonlinearity, distribution shift, or predictor quality. All conditions are included, but no separately named transfer task is evidenced. These are evaluation-condition comparisons, not established cross-domain generalization.

Comparator versions and internal fitting details are unavailable; conclusions apply to the supplied endpoints. The archived calibration source and entrypoint are readable, but a separate final source tree is unavailable for file-by-file identity verification. Source-level method descriptions are therefore distinguished from sealed numerical results: neither a hash nor method-family alignment proves exact implementation identity.

\subsection{Uncertainty and Reporting Rules}
For each condition and method, we recompute width as upper minus lower and coverage as inclusion of the recorded truth in the closed interval. Coverage uncertainty is a pointwise equal-tailed exact-binomial interval for the repetition count. For a comparator $b$, define the paired difference
\begin{equation}
D_r=|I_{\mathrm{control},r}|-|I_{b,r}|,\qquad
\overline D\ \pm\ t_{0.975,R-1}\,s_D/\sqrt R.
\label{eq:paired}
\end{equation}
Here $R$ is the number of repetitions. Negative differences mean narrower recorded intervals, not better coverage. The paired-$t$ interval summarizes mean differences; unlike exact-binomial coverage limits, it is approximate \citep{Student1908}. The calculations reproduce the supplied condition summaries to numerical precision and use their endpoint records rather than repeatedly counting summaries attached only to the initial record.



These intervals assume a repeated-sampling interpretation that distinct seeds alone do not verify. They are pointwise, not simultaneous. Multiplicity changes the question \citep{BenjaminiHochberg1995}; no multiple-testing procedure or familywise gain claim is made. All comparisons are retained regardless of sign. Conditions within a seed may share randomness, so pooled coverage is descriptive, not a binomial estimate from independent condition--repetition pairs.

The sealed evaluation is recorded as completed and qualified. That procedural outcome does not certify exact nominal coverage, independence assumptions, adaptivity controls, or source identity. Candidate diagnostics are explicitly marked unverified in the evidence. No missing diagnostic is interpreted as a passed statistical test. Development scores and unscored alternatives are not used as scientific comparisons, and no new evaluation is run for this paper.




\section{Results}
\subsection{Width Gains Depend on the Comparator and Condition}
Tables~\ref{tab:coverage} and \ref{tab:width} retain every condition and inferential comparator. Figure~\ref{fig:comparison} places coverage next to paired differences so that apparent efficiency is not detached from uncertainty. In C2, the score-control mean width is $0.069770$, compared with $0.070072$ for evaluated PPI++. The paired difference is $-0.000302$, with pointwise 95\% interval $[-0.000400,-0.000203]$. This is a small but resolved mean-width difference within that comparison. Both methods have empirical coverage $0.941406$, with exact-binomial interval $[0.905199,0.966838]$. Equal marginal coverage estimates do not show that they cover on the same repetitions or establish equal coverage probabilities.


\begin{table}[t]
\centering
\caption{Empirical coverage. Every condition has 256 repetitions and nominal coverage 0.95. Pointwise uncertainty is plotted in Figure~\ref{fig:comparison} and fully tabulated in Supplementary Information. The low coverage of evaluated PPI++ and labeled normal inference in C5 remains visible.}
\label{tab:coverage}
\small
\begin{tabular}{lrrrrr}
\toprule
\input{tables/coverage.tex}
\end{tabular}

\end{table}

\begin{table}[t]
\centering
\caption{Mean interval width on the population-mean scale. Smaller values are not automatically preferable when coverage differs. PPI++ is slightly wider than score control only in C2; the exact-binomial comparison in C5 is unresolved by paired uncertainty.}
\label{tab:width}
\small
\begin{tabular}{lrrrrr}
\toprule
\input{tables/width.tex}
\end{tabular}

\end{table}

The other six score-control-minus-PPI++ differences are positive, with pointwise intervals excluding zero. They range from $0.000537$ in C6 to $0.022702$ in C5. Thus, the isolated gain cannot support a claim of broadly shorter intervals than evaluated PPI++. Nor can results against a weaker comparator substitute for that comparison: score control is narrower than labeled normal inference in C1--C3, but wider in C4--C7. The widening in C5 has a different scientific interpretation from the small differences elsewhere because the normal comparator severely undercovers there.


Against the exact-binomial comparator, score-control mean widths are smaller in C1--C4 and C6--C7, with negative pointwise paired intervals. This comparison is informative about width cost but not a transfer of exact coverage: exact-binomial coverage lies near nominal in those conditions, whereas the score-control construction remains asymptotic. The exact reference is especially important when assessing whether narrowness has been bought by approximation. It is not merely an intentionally weak baseline to be displaced.


\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/coverage_width_comparison.pdf}
\caption{Coverage and paired width differences across all conditions. (a,c) Empirical coverage with pointwise 95\% exact-binomial limits; dashed lines indicate nominal coverage. (b,d) Score-control minus comparator mean widths with paired-$t$ limits; negative values mean narrower. Colors identify the comparator in width panels and the interval method in coverage panels. Coverage and width scales differ between rows. PPI is retained in the tables and Figure~\ref{fig:rare}. No interval here is multiplicity-adjusted.}
\label{fig:comparison}

\end{figure}

\subsection{Coverage Estimates Do Not Establish Nominal Validity}
Score-control coverage ranges from $0.929688$ in C5 to $0.957031$ in C3. The pooled recorded coverage is $0.942522$, and the pooled mean width is $0.129888$. These aggregates describe the evaluated mix of conditions, not a population of application domains. They cannot replace the condition-specific comparisons, and we do not attach an independence-based binomial interval to the pooled figure.




All score-control pointwise coverage intervals include the nominal level. This is evidence of limited resolution, not a proof that nominal coverage holds. In particular, the interval for C5 is $[0.891151,0.957799]$, which is compatible with material undercoverage. Stabilization and the absence of collapsed intervals do not close this gap. Conversely, these finite records do not diagnose a specific adaptivity or implementation failure. Missing generator and gate diagnostics remain unknown rather than being classified as either validity failures or harmless performance losses.


\subsection{Low-Prevalence Failure Analysis}
C5 has recorded truth $\mu=0.0068$. Evaluated PPI++ and labeled normal intervals each cover in $0.550781$ of repetitions, with pointwise limits $[0.487609,0.612764]$. Each has 115 zero-width intervals. Score control has no zero-width intervals and coverage $0.929688$; evaluated PPI has two collapsed intervals and coverage $0.941406$. Exact-binomial coverage is $0.996094$, with limits $[0.978429,0.999901]$.


Figure~\ref{fig:rare} shows the width distribution rather than only a ratio to the narrow comparator. The mass at zero and low coverage invalidate an interpretation of the PPI++ mean width as a stand-alone efficiency achievement in this condition. They do not, by themselves, identify every internal cause of a coverage miss. Boundary stabilization is a plausible source-level reason to expect fewer mechanical collapses, but the final records lack a matched stabilization ablation and a separately verified source snapshot.

The score-control and exact-binomial mean widths are $0.038898$ and $0.038945$, respectively. Their paired difference is $-0.000047$, with interval $[-0.000321,0.000227]$. Therefore, the records do not resolve a width advantage over exact inference in the condition where severe asymptotic undercoverage is most visible. The exact interval also has higher observed coverage. These observations defeat a simple ``repair collapse while becoming narrower'' interpretation.


\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/rare_outcome_diagnostic.pdf}
\caption{C5 rare-outcome diagnostic, using all 256 endpoint records. (a) Empirical CDFs retain the mass at zero on a linear width axis. (b) Collapsed-interval counts. Labeled normal inference, omitted from this four-method display, also has 115 zero-width intervals. The associated coverage values appear in Table~\ref{tab:coverage}. Avoiding collapse does not establish nominal coverage or superiority to exact-binomial inference.}
\label{fig:rare}

\end{figure}

\section{Discussion and Limitations}
\paragraph{A possibility result is not an empirical guarantee.}
Equation~\ref{eq:excess} identifies why frozen-score transformation can help: it can reduce the discrepancy between a control and the conditional outcome mean without modifying the predictor. But the empirical evidence shows that this opportunity need not overcome fitting noise, fold effects, and interval stabilization. Even a genuinely favorable variance calculation would not establish coverage for the returned interval. The separate bounded construction makes this distinction explicit rather than retrospectively assigning its guarantee to an asymptotic output.

\paragraph{No isolated attribution to nonlinear calibration.}
The observed method differs from its comparators in calibration, sample separation, weighting, variance estimation, and boundary handling. There is no executed matched affine-only comparison, no observed oracle frontier, and no measured safety-track interval. Consequently, the C2 result is evidence about whole evaluated configurations. It cannot establish that splines caused the gain or that cross-fitting improved width. The unavailable controlled comparisons are missing evidence, not measured negative results.

\paragraph{Sampling and source provenance restrict interpretation.}
The iid common-population assumptions are central to both correction and the safety argument. The archive does not identify whether each generator satisfies them, whether sampling masks are independent, or whether population truths were constructed analytically or from a finite external pool. We retain the stipulated population target and recorded truths, while avoiding a stronger certification of the sampling design. Likewise, source hashes preserve provenance, but readable method-family alignment does not establish byte-level identity with the sealed executable. This limits attribution without erasing the recorded endpoint comparison.

\paragraph{Reproducibility is partial, not end-to-end.}
The included extraction script reproduces the numerical tables, plotted uncertainty, and width distributions from the read-only evidence registry. It does not recreate the unknown generators or rerun the original evaluation. The source archive and seeds document what is available, but missing $n,N$, data versions, and final implementation snapshot prevent an honest claim of full experimental reproducibility. There are no measured named-dataset results, verified transfer results, or robustness analyses beyond the recorded conditions. These omissions materially limit external validity.

\paragraph{Practical interpretation.}
For fixed-input comparisons, assess coverage before interpreting width. Paired differences remain meaningful when comparator widths vanish, and exact inference supplies an important boundary reference. Selecting an interval after observing its realized width requires its own coverage argument. Here, these principles reveal a modest local gain and substantial comparator dependence, not a generally preferable interval. They motivate controlled follow-up rather than a deployment recommendation.

\section{Conclusion}
Frozen labels, unlabeled observations, and predictions do not mathematically eliminate all room for more efficient mean inference. A score-only control can exploit a better approximation to the conditional outcome mean; the fixed-control variance identity specifies this opportunity and the information it cannot recover. Whether a fitted procedure converts that opportunity into \emph{valid, narrower intervals} is a separate empirical and theoretical question.

The paired records provide a bounded answer. Score control is slightly narrower than evaluated PPI++ in C2, but wider in the other six conditions. In the low-prevalence condition it avoids observed collapsed intervals and has much higher coverage than two asymptotic comparators, yet its width advantage over exact-binomial inference is unresolved and nominal validity remains unestablished. Missing calibration ablations prevent a component-level interpretation, and missing generation metadata prevent reconstruction of the complete study. The defensible conclusion is therefore condition-specific: inference-side flexibility may change width, but this evidence does not establish a uniformly shorter, statistically valid replacement for existing intervals under fixed inputs.


\clearpage
\bibliography{references}
\bibliographystyle{iclr2026_conference}

\clearpage
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}
\subsection{Complete Paired Interval Comparisons}
\label{sec:complete}
The following tables retain every evaluated inferential comparator and condition. Widths use the recorded endpoint difference; a zero-width count is an exact equality diagnostic, not an indicator that the true population mean is known. Coverage limits use equal-tailed binomial inversion across repetitions. The paired mean-difference limits use Equation~\ref{eq:paired}. No threshold-based filtering or multiplicity adjustment is applied. Uncertainty about the repetition sampling design also applies to these limits.


\begin{longtable}{llrrr}
\caption{Complete marginal interval summaries. Limits in brackets are pointwise 95\% coverage intervals; $Z$ is the count of zero-width intervals.}\label{tab:complete}\\
\toprule
Condition & Method & Coverage [limits] & Mean width & $Z$\\
\midrule
\endfirsthead
\toprule
Condition & Method & Coverage [limits] & Mean width & $Z$\\
\midrule
\endhead

C1 & Score control & 0.938 [0.900, 0.964] & 0.14183 & 0 \\
C1 & PPI++ & 0.945 [0.910, 0.970] & 0.13960 & 0 \\
C1 & PPI & 0.945 [0.910, 0.970] & 0.14053 & 0 \\
C1 & Label normal & 0.930 [0.891, 0.958] & 0.16486 & 0 \\
C1 & Exact binomial & 0.949 [0.915, 0.973] & 0.17104 & 0 \\
\midrule
C2 & Score control & 0.941 [0.905, 0.967] & 0.06977 & 0 \\
C2 & PPI++ & 0.941 [0.905, 0.967] & 0.07007 & 0 \\
C2 & PPI & 0.941 [0.905, 0.967] & 0.07041 & 0 \\
C2 & Label normal & 0.934 [0.896, 0.961] & 0.08266 & 0 \\
C2 & Exact binomial & 0.949 [0.915, 0.973] & 0.08442 & 0 \\
\midrule
C3 & Score control & 0.957 [0.924, 0.978] & 0.15437 & 0 \\
C3 & PPI++ & 0.957 [0.924, 0.978] & 0.15094 & 0 \\
C3 & PPI & 0.961 [0.929, 0.981] & 0.15224 & 0 \\
C3 & Label normal & 0.930 [0.891, 0.958] & 0.17257 & 0 \\
C3 & Exact binomial & 0.953 [0.920, 0.976] & 0.17859 & 0 \\
\midrule
C4 & Score control & 0.945 [0.910, 0.970] & 0.17167 & 0 \\
C4 & PPI++ & 0.941 [0.905, 0.967] & 0.16922 & 0 \\
C4 & PPI & 0.965 [0.934, 0.984] & 0.19605 & 0 \\
C4 & Label normal & 0.941 [0.905, 0.967] & 0.16962 & 0 \\
C4 & Exact binomial & 0.949 [0.915, 0.973] & 0.17570 & 0 \\
\midrule
C5 & Score control & 0.930 [0.891, 0.958] & 0.03890 & 0 \\
C5 & PPI++ & 0.551 [0.488, 0.613] & 0.01620 & 115 \\
C5 & PPI & 0.941 [0.905, 0.967] & 0.05742 & 2 \\
C5 & Label normal & 0.551 [0.488, 0.613] & 0.01633 & 115 \\
C5 & Exact binomial & 0.996 [0.978, 1.000] & 0.03894 & 0 \\
\midrule
C6 & Score control & 0.945 [0.910, 0.970] & 0.16540 & 0 \\
C6 & PPI++ & 0.930 [0.891, 0.958] & 0.16486 & 0 \\
C6 & PPI & 0.930 [0.891, 0.958] & 0.16486 & 0 \\
C6 & Label normal & 0.930 [0.891, 0.958] & 0.16486 & 0 \\
C6 & Exact binomial & 0.949 [0.915, 0.973] & 0.17104 & 0 \\
\midrule
C7 & Score control & 0.941 [0.905, 0.967] & 0.16727 & 0 \\
C7 & PPI++ & 0.934 [0.896, 0.961] & 0.16459 & 0 \\
C7 & PPI & 0.988 [0.966, 0.998] & 0.19287 & 0 \\
C7 & Label normal & 0.930 [0.891, 0.958] & 0.16486 & 0 \\
C7 & Exact binomial & 0.949 [0.915, 0.973] & 0.17104 & 0 \\
\midrule
\bottomrule
\end{longtable}

\begin{longtable}{llrr}
\caption{Paired score-control minus comparator width differences. Negative values indicate narrower recorded intervals, not a coverage-adjusted advantage.}\label{tab:paired}\\
\toprule
Condition & Comparator & Mean difference & Pointwise 95\% limits\\
\midrule
\endfirsthead
\toprule
Condition & Comparator & Mean difference & Pointwise 95\% limits\\
\midrule
\endhead

C1 & PPI++ & +0.002231 & [+0.001631, +0.002831] \\
C1 & PPI & +0.001302 & [+0.000690, +0.001913] \\
C1 & Label normal & -0.023034 & [-0.024169, -0.021900] \\
C1 & Exact binomial & -0.029209 & [-0.030341, -0.028077] \\
\midrule
C2 & PPI++ & -0.000302 & [-0.000400, -0.000203] \\
C2 & PPI & -0.000644 & [-0.000742, -0.000547] \\
C2 & Label normal & -0.012893 & [-0.013143, -0.012644] \\
C2 & Exact binomial & -0.014651 & [-0.014900, -0.014401] \\
\midrule
C3 & PPI++ & +0.003429 & [+0.002896, +0.003962] \\
C3 & PPI & +0.002130 & [+0.001550, +0.002710] \\
C3 & Label normal & -0.018195 & [-0.019163, -0.017227] \\
C3 & Exact binomial & -0.024218 & [-0.025186, -0.023250] \\
\midrule
C4 & PPI++ & +0.002452 & [+0.001972, +0.002933] \\
C4 & PPI & -0.024381 & [-0.025514, -0.023247] \\
C4 & Label normal & +0.002056 & [+0.001575, +0.002537] \\
C4 & Exact binomial & -0.004025 & [-0.004505, -0.003544] \\
\midrule
C5 & PPI++ & +0.022702 & [+0.021895, +0.023508] \\
C5 & PPI & -0.018525 & [-0.021644, -0.015407] \\
C5 & Label normal & +0.022565 & [+0.021741, +0.023389] \\
C5 & Exact binomial & -0.000047 & [-0.000321, +0.000227] \\
\midrule
C6 & PPI++ & +0.000537 & [+0.000179, +0.000894] \\
C6 & PPI & +0.000537 & [+0.000179, +0.000894] \\
C6 & Label normal & +0.000537 & [+0.000179, +0.000894] \\
C6 & Exact binomial & -0.005638 & [-0.005995, -0.005281] \\
\midrule
C7 & PPI++ & +0.002681 & [+0.002112, +0.003251] \\
C7 & PPI & -0.025593 & [-0.026689, -0.024498] \\
C7 & Label normal & +0.002409 & [+0.001840, +0.002978] \\
C7 & Exact binomial & -0.003766 & [-0.004334, -0.003197] \\
\midrule
\bottomrule
\end{longtable}

The full-range interval is $[0,1]$ in the records and covers the recorded binary-mean truths. It is a check on the endpoint/target convention, not a competitive width baseline. Raw width ratios can be dominated by zero or near-zero denominators in C5. We therefore do not interpret the retained pooled ratio as a multiplicative efficiency advantage, and do not infer how any denominator regularization was implemented.



\subsection{Calibration and Interval Implementation}
\label{sec:implementation}
Readable source copies are supplied under \path{source_evidence/calibration/}. The entrypoint specification declares \path{program.py}; the functions below describe that archive. The final evaluation's recorded source-tree hash is not independently reconstructed from these copies. Thus, these locations substantiate source-level choices, not a stronger assertion that every sealed endpoint came from an identical file tree.

\paragraph{Training-only model choice.}
The basis contains the raw score and positive-part hinges $(S-\kappa)_+$. The training outcome mean supplies the intercept. Each feature is centered and scaled on the training fold; standard deviations are floored at $10^{-8}$. For a training count $m$, a penalty $\lambda$ solves
\begin{equation}
\widehat\beta_\lambda=(Z^\top Z/m+\lambda I)^{-1}Z^\top(Y-\overline Y)/m.
\end{equation}
The effective degrees of freedom are $d=1+\operatorname{tr}\{(Z^\top Z/m+\lambda I)^{-1}Z^\top Z/m\}$. The GCV denominator is $\max(1-d/m,1/m)^2$. This score selects among the available basis/penalty pairs and the constant fit \citep{HoerlKennard1970,Golub1979GCV}. The smallest training size for nonconstant fitting is four; score range below $10^{-12}$ keeps the intercept. None of these thresholds is a measured tuning optimum.


\paragraph{Randomization and output.}
The reset seed initializes the local random generator used for permutations. State is cleared between repetitions; labels are not pooled across them. Only the predefined outcome and score arrays enter inference. The interface reports an estimate and bounded endpoints, not calibration diagnostics. In the exact small-$n$ branch, beta quantiles implement equal-tailed binomial inversion. Otherwise the reported point estimate is the clipped corrected mean, while the interval center is $c$ from Equation~\ref{eq:stabilized}. These need not be identical. The stabilization is not an exact Wilson interval, even though its algebra resembles score-based boundary adjustments \citep{Newcombe1998,AgrestiCoull1998}.


\paragraph{Unmeasured functions.}
The archive exposes \texttt{fit\_affine\_calibrator} and an internal affine option with the same clipping and penalty grid but no hinges. The reporting helper also defines an oracle variance calculation. Neither function supplies an executed controlled comparison in the sealed evidence. The preparation note's statement that experiments had not yet been run describes preparation time; it does not negate the subsequently supplied endpoint records. Conversely, later records do not supply missing affine or bounded-track results.



\subsection{Fixed-Control Variance and Separate Safety Argument}
\label{sec:theory}
\paragraph{Variance decomposition.}
Assume the iid sampling model from the main text, $n,N$ fixed, and a fixed square-integrable $g$. Write $Y=m(S)+\varepsilon$, where $\E[\varepsilon\mid S]=0$. Independence between the labeled and unlabeled samples gives Equation~\ref{eq:fixed}. Let $h=g-m$. Orthogonality of $\varepsilon$ and score functions yields
\begin{align}
\Var(Y-\rho g)&=\E[\Var(Y\mid S)]+\Var\{(1-\rho)m-\rho h\},\\
\Var(g)&=\Var(m+h).
\end{align}
The cross term cancels because $(1-\rho)/n=\rho/N$. The remaining coefficients are
\begin{equation}
\frac{(1-\rho)^2}{n}+\frac{\rho^2}{N}=\frac{1}{n+N},\qquad
\rho^2\left(\frac1n+\frac1N\right)=\frac{\rho}{n}.
\end{equation}
This proves Equations~\ref{eq:oracle}--\ref{eq:excess}. Additive constants in $g$ cancel from the estimator, consistent with the variance rather than uncentered squared-error excess. If $\Pi_{\mathrm{aff}}m$ is the $L^2$ projection onto unrestricted affine functions of $S$, including an intercept, the oracle reduction relative to the best such affine control is
\begin{equation}
\frac{N}{n(n+N)}\E\bigl[(m-\Pi_{\mathrm{aff}}m)^2\bigr].
\end{equation}
The projection residual has mean zero. Constant scores reduce the affine space to constants. This calculation concerns unrestricted population controls; the clipped, regularized fitted affine family is not that same class. No recorded condition is shown to attain this reduction.



\paragraph{Why fitted-control inference requires more.}
For fixed $g$, elementary variance algebra suffices. For estimated $g_{-k}$, conditional sample separation preserves the correction's expectation under the iid model, but unconditional covariances across folds remain. First-order inference requires additional control of fitted-function error and variance estimation, as emphasized more generally in semiparametric theory \citep{Robinson1988,VanDerVaart1998,Chernozhukov2018DML}. The archive does not establish the required rates for its finite dictionary/GCV rule in each condition. The Efron--Stein perspective also emphasizes accounting for estimator sensitivity rather than treating fitted components as fixed \citep{EfronStein1981}. We use no such inequality to certify the returned interval.

\paragraph{Bounded safety construction.}
For a held-out component sample $A_1,\ldots,A_m$ with known range length $B$, the archived radius is
\begin{equation}
b(A,\delta)=\min\left\{B,\sqrt{\frac{2s_A^2\log(4/\delta)}{m}}
+\frac{7B\log(4/\delta)}{3(m-1)}\right\},\qquad m\geq2.
\label{eq:eb}
\end{equation}
For a singleton, it uses $B$. This is a conservative two-sided empirical-Bernstein form \citep{MaurerPontil2009}; known boundedness, as in classical concentration arguments \citep{Hoeffding1963}, is essential. Capping at $B$ cannot invalidate a bound because both the sample and population means lie in the support interval. The variance-sensitive term can be useful, but the additive range term can make the interval substantially wider than an asymptotic one. Related variance-aware bounds are studied in other settings \citep{Audibert2009}; those sequential results are not empirical evidence here.


For $K=2$ folds, each residual mean and each unlabeled control mean receives error probability $\delta=\alpha/(2K)$. Conditional on the opposite labeled training sample, the residuals have support $[-\rho,1]$ and the unlabeled controls have support $[0,\rho]$. Their expectations sum to $\mu$. A union bound across the $2K$ component events therefore controls the probability of any failure by $\alpha$, without requiring independence across the fitted folds. On this joint event, each fold interval contains $\mu$; averaging lower and upper endpoints using fixed nonnegative weights summing to one preserves containment. Intersecting with $[0,1]$ preserves containment of a binary mean. The implementation replaces an empty numerical intersection by the full range.


This is a coverage argument for the separate construction under the stated sampling and support assumptions. It is not an empirical coverage estimate, a width comparison, or a theorem for Equation~\ref{eq:stabilized}. No width-dependent choice between the two constructions is justified by the union bound as implemented.

\subsection{Evidence Extraction and Reproducibility Boundaries}
\label{sec:reproduce}
\paragraph{Inputs and deterministic outputs.}
The read-only \path{paper_data.json} is the primary numerical input. The script \path{scripts/build_artifacts.py} reads the final endpoint records, checks paired differences against the supplied summaries, and writes \path{analysis_results.json}, the tables under \path{tables/}, and both quantitative figure groups under \path{figures/}. Each quantitative figure is exported as vector PDF and 300-DPI PNG, with an adjacent provenance sidecar recording its inputs. The overview figure is separately prepared from the method description and is not a quantitative result plot.


The recorded repetition seeds are 1001--1256. Truths are $0.353333\ldots$ in C1, C2, C6, and C7; $0.5$ in C3; $0.41$ in C4; and $0.0068$ in C5. These are record values, not recovered generation parameters. No condition-specific sample sizes, datasets, data licenses, or original data-download instructions can be reconstructed from the staged evidence. An end-to-end runner would require these missing inputs; the archived \path{study.py} is a collection of reporting helpers, not such a runner.




\paragraph{Uncertainty choices and unperformed analyses.}
The paired-$t$ limits describe repeated width differences under their usual sampling approximation. We did not run a bootstrap, a jackknife, a sensitivity sweep, or a new evaluation. Bootstrap references describe alternative distribution-estimation tools \citep{Efron1979,EfronTibshirani1993}, not analyses performed for this paper. Recomputing interval summaries from archived records cannot repair an unknown sampling mechanism. The included source manifest records local file hashes and distinguishes them from the final evaluator's source-tree identifiers.

\paragraph{Environment and commands.}
The reproduction guide records the exact paper-analysis package versions, a CPU-only command for regenerating the tables and plots, and the validation commands. These are the environment versions used for manuscript extraction, not recovered versions of the sealed evaluation environment. No evaluation runtime is inferred from the plot-generation runtime. No prohibited literature was intentionally searched or consulted: citation remediation used exact permitted starter works and pre-screened historical foundations, without citation-network traversal. Rejected DOI/title mismatches are recorded as retrieval errors, not used as references.

\paragraph{Qualification and auditing.}
The independently read final record reports a completed evaluation and a qualified outcome. Its retained endpoint measurements remain the scientific evidence. The acceptance outcome is not interpreted as a guarantee of validity, superiority, or successful source verification. Candidate diagnostics remain unverified; gate-specific causes not supplied in the evidence are unknown. The claim map separately records qualification sources, endpoint sources, readable implementation locations, and literature provenance.




\subsection{LLM Usage}
LLM-based assistance was used for research-direction proposals, preparation of candidate implementations, reference-query planning, manuscript framing and drafting, deterministic analysis-script construction, and evidence/format checks. The supplied evaluation records, not LLM estimates, provide the empirical observations. No additional scientific evaluation was performed during manuscript preparation. Automated source inspection and claim checks are not independent statistical verification. No claim of human review or manual experimental replication is made. The manuscript's limitations, including missing controlled comparisons and generation metadata, are retained rather than filled with inferred results.
```
