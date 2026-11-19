# Agentic evidence audit packet

- generated_at: `2026-11-17T14:48:45.649458+00:00`
- paper_dir: `work/results/r02/codex/20261117_111421/.paper_evidence_audit_workspaces-1000/agentic-evidence-audit-1000-20261117_130005-paper_evidence_audit-euml8qva/workspace`

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
    "anchored_references": 69,
    "bundle_present": true,
    "checked": true,
    "dangling_references": 0,
    "paper_token_count": 112,
    "resolved_references": 85,
    "total_references": 154
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
    "anchored_references": 69,
    "dangling_references": 1,
    "manifests_checked": 17,
    "resolved_references": 84,
    "total_references": 154
  }
}
```

## claims_grounding excerpt

```json
{
  "claims": [
    {
      "citation_keys": [],
      "claim": "The independent final evaluation completed, was qualified, and reports successful specified checks; qualification is not a superiority or shifted-validity result.",
      "source_ids": [
        "final.qualification.status",
        "final.qualification.outcome",
        "final.qualification.correct",
        "final.metric.control_check_pass_rate"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The final study comprises eight seeds, six conditions (logistic-normal IID, Dirichlet IID, shifted Dirichlet at K=3 and 8), and alpha=0.05,0.10,0.20. All recorded cases are complete.",
      "evidence_locator": "/final_evaluation/evaluation_evidence/episodes",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:37",
        "source_evidence/data_manifest.json"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Final seeds are 1009,1013,1019,1021,1031,1033,1039,1049; train/calibration/test sizes are 1024/512/2048 with six covariates.",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "source_evidence/data_manifest.json",
        "source_evidence/evaluate_final.py:727"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Positive observed continuous compositions, not categorical labels or latent probabilities, are the response. The fixed Helmert ILR basis has K-1 coordinates.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:37"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The design uses intercept, raw features, squares, sines and x0*x1. Center and log-residual ridge penalties are 1 and 10; intercept penalty is 1e-8; residual floor is .02.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:98"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Centers are clipped to [-100,100] and positive base and corrected scales to [1e-4,100]. The base log-residual fit uses in-sample residuals; correction moments are cross-fitted.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:114"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Three-fold training permutations use random seed 0. Moment features use standard deviation floor 1e-8; standardized residuals use scale floor 1e-4; queries are batched in 128 rows.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:109"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Local moments average squared standardized ILR residuals over K-1 coordinates, Gaussian-smooth them over standardized covariates, and shrink the ratio toward 1 by prior mass.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:133"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Moment ratios are clipped to [.25,4]; a common row-scalar multiplies all ILR scales, preserving their within-row ratios. The correction blends are 0,.5,1; bandwidths .5*sqrt(6),sqrt(6); prior masses 10,50.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:172"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Nested three-fold training selection uses swapped pseudo-calibration/evaluation halves; the row-weighted alpha-averaged log arithmetic mean ILR-box volume is minimized, with smaller blend breaking ties.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:275"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The selector uses exact finite ranks, Gaussian-loss fallback for unavailable ranks or invalid radii/objectives, and a neutral tiny-sample fallback. Realized fallback frequencies and selected settings are not retained.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:188"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Global constant scale multiplication cancels its conformal radius, apart from clipping. At alpha .05, 18 internal calibration observations are insufficient for a finite rank; 19 suffice. Numerical invariance assertions are source checks, not a scientific ablation.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:237"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Independent final calibration uses ceil((m+1)*(1-alpha)) order statistic with infinity when unavailable, and closed membership. It is not selected on calibration labels.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:836"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The unscaled ILR comparator sets scales to one at the same center. Simplex max uses a joint coordinate maximum. Bonferroni calibrates K simplex coordinates at alpha/K, not ILR coordinates.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:857"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Mass is uniform-simplex probability content estimated at 128 test contexts using 1024 shared Dirichlet(1) probes; utility equals (1-mass)*max(0,1-absolute_coverage_error/(1-alpha)). Errors are absolute before averaging.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:727"
      ]
    },
    {
      "citation_keys": [],
      "claim": "IID covariates are uniform on [-1.5,1.5]^6, logistic-normal noise standard deviation is .25, Dirichlet concentration is 4+35/(1+exp(2*x0)), and gamma coordinates are floored at 1e-12 before closure.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:727"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The fixed mean is .7*sin(XW)+.3*x0*cos(j), with W[l,j]=sin(l*(K-1)+j+1)/3. Shift changes only test X to clipped N(.8,1) in [-2.5,3], changing covariate support as well as frequency.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:727"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Independent random streams use SeedSequence([seed,case,split,202611]); reference split index is 3. Frozen resources are checked for numeric row-content disjointness, positivity, closure and hashes.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:727"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Per-context mass resolution is 1/1024. Zero hits have a one-sided .95 upper bound 1-.05**(1/1024)=.00292124, not zero mass. Averaged plugin context standard errors do not quantify joint mass uncertainty.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:905"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The evaluator resamples seed blocks 20000 times using RNG seed 62845. Paired utility intervals have optional tail probability .05/(2*54); volume intervals are unadjusted. Repeated uncertainty summaries are deduplicated.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:1036"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Constant-input queries use training-mean features; nonidentity permutations rotate calibration and test rows separately. Whole-simplex and zero-radius references are degenerate metric controls, not useful calibrated baselines.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:929"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The evaluated environment requires CPython 3.11 or 3.12 and NumPy 1.26.4 with native Linux isolation. No external dataset is downloaded for the synthetic study.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01"
      ],
      "supporting_artifacts": [
        "source_evidence/evaluate_final.py:1186"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The matched final evidence does not contain a selector-only Gaussian-versus-rank comparison or an original-initializer comparison. The earlier configurations are development evidence, not final ablations.",
      "source_ids": [
        "final.evidence.episodes",
        "result.top_program_01",
        "result.top_program_02",
        "result.top_program_03"
      ],
      "supporting_artifacts": [
        "source_evidence/selected_model.py:275",
        "source_evidence/development_gaussian.py:185",
        "source_evidence/development_joint.py:152",
        "paper_data.json"
      ]
    },
    {
      "citation_keys": [],
      "claim": "IID and shifted scaled-ILR absolute coverage errors are 0.013562011718750005 and 0.13034261067708333, respectively.",
      "source_ids": [
        "final.metric.iid_coverage_error",
        "final.metric.shift_coverage_error"
      ]
    },
    {
      "citation_keys": [],
      "claim": "The scaled-ILR mean utility is 0.661819668104677, mass 0.3034934467739529, and aggregate utility gap to the strongest standard comparator is 0.011594669497844157.",
      "source_ids": [
        "final.metric.final_score",
        "final.metric.mean_volume",
        "final.metric.baseline_utility_gap"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Main summary table, scaled_ilr: {\"iid_error\": 0.013562011718750005, \"shift_error\": 0.13034261067708333, \"mass\": 0.3034934467739529, \"utility\": 0.6618196681046769, \"utility_ci95\": [0.6541870135283389, 0.6702210518782714]}",
      "evidence_locator": "analysis/summary.json#/methods/scaled_ilr",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "analysis/summary.json",
        "build_analysis.py"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Main summary table, unscaled_ilr: {\"iid_error\": 0.011428833007812512, \"shift_error\": 0.21623942057291665, \"mass\": 0.33818605211046004, \"utility\": 0.6046676445264709, \"utility_ci95\": [0.5979837051081343, 0.6106757253591186]}",
      "evidence_locator": "analysis/summary.json#/methods/unscaled_ilr",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "analysis/summary.json",
        "build_analysis.py"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Main summary table, simplex_linf: {\"iid_error\": 0.011170450846354164, \"shift_error\": 0.19736938476562502, \"mass\": 0.29170094596015084, \"utility\": 0.6502249986068328, \"utility_ci95\": [0.6438168744995187, 0.656831114206901]}",
      "evidence_locator": "analysis/summary.json#/methods/simplex_linf",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "analysis/summary.json",
        "build_analysis.py"
      ]
    },
    {
      "citation_keys": [],
      "claim": "Main summary table, bonferroni: {\"iid_error\": 0.02037251790364582, \"shift_error\": 0.16195882161458333, \"mass\": 0.3192414707607693, \"utility\": 0.629594813617563, \"utility_ci95\": [0.6223210736029817, 0.6367253124148236]}",
      "evidence_locator": "analysis/summary.json#/methods/bonferroni",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "analysis/summary.json",
        "build_analysis.py"
      ]
    },
    {
      "citation_keys": [],
      "claim": "New retained-data descriptive paired aggregate utility contrast, scaled ILR minus unscaled_ilr: {\"mean\": 0.05715202357820612, \"ci95\": [0.05093218763917902, 0.06416155229759228]}",
      "evidence_locator": "analysis/summary.json#/paired_overall/unscaled_ilr",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts": [
        "analysis/summary.json",
        "build_analysis.py"
      ]
    },
    {
      "citation_keys": [],
      "claim": "New retained-data descriptive paired aggregate utility contrast, scaled ILR minus simplex_linf: {\"mean\": 0.01159466949784424, \"ci95\": [0.004737770703221511, 0.017943424925238635]}",
      "evidence_locator": "analysis/summary.json#/paired_overall/simplex_linf",
      "source_ids": [
        "final.evidence.episodes"
      ],
      "supporting_artifacts":

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
  "grounding_source_count": 23,
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
  "campaign_results_dir": "work/results/r02/codex/20261117_111421/investigation",
  "count": 26,
  "generated_at": "2026-11-17T14:24:21.314151+00:00",
  "queries": [
    "Algorithmic Learning in a Random World",
    "Inductive Confidence Machines for Regression",
    "Distribution-Free Predictive Inference for Regression",
    "Predictive inference with the jackknife+",
    "Conformal Prediction Under Covariate Shift",
    "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification",
    "Conformalized Quantile Regression",
    "A comparison of some conformal quantile regression methods",
    "Selection and Aggregation of Conformal Prediction Sets",
    "Conditional validity of inductive conformal predictors",
    "Distribution-free prediction bands for non-parametric regression",
    "Localized conformal prediction: A generalized inference framework for conformal prediction",
    "Flexible Distribution-Free Conditional Predictive Bands Using Density Estimators",
    "The limits of distribution-free conditional predictive inference",
    "Adaptive Conformal Inference Under Distribution Shift",
    "The Statistical Analysis of Compositional Data",
    "Logistic-normal distributions: Some properties and uses",
    "Isometric Logratio Transformations for Compositional Data Analysis",
    "Modeling and Analysis of Compositional Data",
    "Ridge Regression: Biased Estimation for Nonorthogonal Problems",
    "On Estimating Regression",
    "Conformal prediction beyond exchangeability",
    "Bootstrap Methods: Another Look at the Jackknife",
    "Interval Estimation for a Binomial Proportion",
    "Bootstrap Methods and their Application",
    "multivariate split conformal rectangular prediction regions maximum standardized absolute residual score"
  ],
  "reference_query_plan": {},
  "reference_query_plans": [],
  "references": [
    {
      "citation_key": "Vovk2005",
      "id": "ref.Vovk2005",
      "paper_id": "doi:10.1007/b106715",
      "query": "Algorithmic Learning in a Random World",
      "read_artifact": "literature/Vovk2005.html",
      "read_scope": "Publisher abstract or book overview read; saved HTML. No references or related-article links followed.",
      "source_url": "https://api.crossref.org/works?query.title=Algorithmic+Learning+in+a+Random+World&rows=1",
      "title": "Algorithmic Learning in a Random World",
      "year": 2005
    },
    {
      "citation_key": "Papadopoulos2002",
      "id": "ref.Papadopoulos2002",
      "paper_id": "doi:10.1007/3-540-36755-1_29",
      "query": "Inductive Confidence Machines for Regression",
      "read_artifact": "literature/Papadopoulos2002.html",
      "read_scope": "Publisher abstract or book overview read; saved HTML. No references or related-article links followed.",
      "source_url": "https://api.crossref.org/works?query.title=Inductive+Confidence+Machines+for+Regression&rows=1",
      "title": "Inductive Confidence Machines for Regression",
      "year": 2002
    },
    {
      "citation_key": "Lei2018",
      "id": "ref.Lei2018",
      "paper_id": "arxiv:1604.04173",
      "query": "Distribution-Free Predictive Inference for Regression",
      "read_artifact": "literature/Lei2018.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/1604.04173",
      "title": "Distribution-Free Predictive Inference For Regression",
      "year": 2016
    },
    {
      "citation_key": "Barber2021Jackknife",
      "id": "ref.Barber2021Jackknife",
      "paper_id": "arxiv:1905.02928",
      "query": "Predictive inference with the jackknife+",
      "read_artifact": "literature/Barber2021Jackknife.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/1905.02928",
      "title": "Predictive inference with the jackknife+",
      "year": 2019
    },
    {
      "citation_key": "Tibshirani2019",
      "id": "ref.Tibshirani2019",
      "paper_id": "arxiv:1904.06019",
      "query": "Conformal Prediction Under Covariate Shift",
      "read_artifact": "literature/Tibshirani2019.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/1904.06019",
      "title": "Conformal Prediction Under Covariate Shift",
      "year": 2019
    },
    {
      "citation_key": "Angelopoulos2021",
      "id": "ref.Angelopoulos2021",
      "paper_id": "arxiv:2107.07511",
      "query": "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification",
      "read_artifact": "literature/Angelopoulos2021.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/2107.07511",
      "title": "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification",
      "year": 2021
    },
    {
      "citation_key": "Romano2019",
      "id": "ref.Romano2019",
      "paper_id": "arxiv:1905.03222",
      "query": "Conformalized Quantile Regression",
      "read_artifact": "literature/Romano2019.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/1905.03222",
      "title": "Conformalized Quantile Regression",
      "year": 2019
    },
    {
      "citation_key": "Sesia2020",
      "id": "ref.Sesia2020",
      "paper_id": "arxiv:1909.05433",
      "query": "A comparison of some conformal quantile regression methods",
      "read_artifact": "literature/Sesia2020.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/1909.05433",
      "title": "A comparison of some conformal quantile regression methods",
      "year": 2019
    },
    {
      "citation_key": "Yang2024",
      "id": "ref.Yang2024",
      "paper_id": "doi:10.1080/01621459.2024.2344700",
      "query": "Selection and Aggregation of Conformal Prediction Sets",
      "read_artifact": "literature/Yang2024.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works?query.title=Selection+and+Aggregation+of+Conformal+Prediction+Sets&rows=1",
      "title": "Selection and Aggregation of Conformal Prediction Sets",
      "year": 2024
    },
    {
      "citation_key": "Vovk2012",
      "id": "ref.Vovk2012",
      "paper_id": "doi:10.1007/s10994-013-5355-6",
      "query": "Conditional validity of inductive conformal predictors",
      "read_artifact": "literature/Vovk2012.html",
      "read_scope": "Publisher abstract or book overview read; saved HTML. No references or related-article links followed.",
      "source_url": "https://api.crossref.org/works?query.title=Conditional+validity+of+inductive+conformal+predictors&rows=1",
      "title": "Conditional validity of inductive conformal predictors",
      "year": 2013
    },
    {
      "citation_key": "Lei2014",
      "id": "ref.Lei2014",
      "paper_id": "doi:10.1111/rssb.12021",
      "query": "Distribution-free prediction bands for non-parametric regression",
      "read_artifact": "literature/Lei2014.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works?query.title=Distribution-free+prediction+bands+for+non-parametric+regression&rows=1",
      "title": "Distribution-free Prediction Bands for Non-parametric Regression",
      "year": 2014
    },
    {
      "citation_key": "Guan2023",
      "id": "ref.Guan2023",
      "paper_id": "doi:10.1093/biomet/asac040",
      "query": "Localized conformal prediction: A generalized inference framework for conformal prediction",
      "read_artifact": "literature/Guan2023.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works?query.title=Localized+conformal+prediction%3A+A+generalized+inference+framework+for+conformal+prediction&rows=1",
      "title": "Localized conformal prediction: a generalized inference framework for conformal prediction",
      "year": 2023
    },
    {
      "citation_key": "Izbicki2020",
      "id": "ref.Izbicki2020",
      "paper_id": "pmlr:v108/izbicki20a",
      "query": "Flexible Distribution-Free Conditional Predictive Bands Using Density Estimators",
      "read_artifact": "literature/Izbicki2020.json",
      "read_scope": "Official proceedings abstract, metadata, and BibTeX; no citation links followed.",
      "source_url": "https://proceedings.mlr.press/v108/izbicki20a.html",
      "title": "Flexible Distribution-Free Conditional Predictive Bands Using Density Estimators",
      "year": 2020
    },
    {
      "citation_key": "Barber2021Limits",
      "id": "ref.Barber2021Limits",
      "paper_id": "arxiv:1903.04684",
      "query": "The limits of distribution-free conditional predictive inference",
      "read_artifact": "literature/Barber2021Limits.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/1903.04684",
      "title": "The limits of distribution-free conditional predictive inference",
      "year": 2019
    },
    {
      "citation_key": "Gibbs2021",
      "id": "ref.Gibbs2021",
      "paper_id": "arxiv:2106.00170",
      "query": "Adaptive Conformal Inference Under Distribution Shift",
      "read_artifact": "literature/Gibbs2021.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/2106.00170",
      "title": "Adaptive Conformal Inference Under Distribution Shift",
      "year": 2021
    },
    {
      "citation_key": "Aitchison1982",
      "id": "ref.Aitchison1982",
      "paper_id": "doi:10.1111/j.2517-6161.1982.tb01195.x",
      "query": "The Statistical Analysis of Compositional Data",
      "read_artifact": "literature/Aitchison1982.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works/10.1111/j.2517-6161.1982.tb01195.x",
      "title": "The Statistical Analysis of Compositional Data",
      "year": 1982
    },
    {
      "citation_key": "Aitchison1980",
      "id": "ref.Aitchison1980",
      "paper_id": "doi:10.2307/2335470",
      "query": "Logistic-normal distributions: Some properties and uses",
      "read_artifact": "literature/Aitchison1980.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works?query.title=Logistic-normal+distributions%3A+Some+properties+and+uses&rows=1",
      "title": "Logistic-Normal Distributions: Some Properties and Uses",
      "year": 1980
    },
    {
      "citation_key": "Egozcue2003",
      "id": "ref.Egozcue2003",
      "paper_id": "doi:10.1023/a:1023818214614",
      "query": "Isometric Logratio Transformations for Compositional Data Analysis",
      "read_artifact": "literature/Egozcue2003.html",
      "read_scope": "Publisher abstract or book overview read; saved HTML. No references or related-article links followed.",
      "source_url": "https://api.crossref.org/works?query.title=Isometric+Logratio+Transformations+for+Compositional+Data+Analysis&rows=1",
      "title": "Isometric Logratio Transformations for Compositional Data Analysis",
      "year": 2003
    },
    {
      "citation_key": "Pawlowsky2015",
      "id": "ref.Pawlowsky2015",
      "paper_id": "doi:10.1002/9781119003144",
      "query": "Modeling and Analysis of Compositional Data",
      "read_artifact": "literature/Pawlowsky2015-excerpt.pdf",
      "read_scope": "Publisher book excerpt, introduction pages 1 and 2, read; no references followed.",
      "source_url": "https://api.crossref.org/works/10.1002/9781119003144",
      "title": "Modelling and Analysis of Compositional Data",
      "year": 2015
    },
    {
      "citation_key": "Hoerl1970",
      "id": "ref.Hoerl1970",
      "paper_id": "doi:10.1080/00401706.1970.10488634",
      "query": "Ridge Regression: Biased Estimation for Nonorthogonal Problems",
      "read_artifact": "literature/Hoerl1970.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works/10.1080/00401706.1970.10488634",
      "title": "Ridge Regression: Biased Estimation for Nonorthogonal Problems",
      "year": 1970
    },
    {
      "citation_key": "Nadaraya1964",
      "id": "ref.Nadaraya1964",
      "paper_id": "doi:10.1137/1109020",
      "query": "On Estimating Regression",
      "read_artifact": "literature/Nadaraya1964.json",
      "read_scope": "Exact-title bibliographic record and abstract when available. Citation network not accessed.",
      "source_url": "https://api.crossref.org/works?query.title=On+Estimating+Regression&rows=1",
      "title": "On Estimating Regression",
      "year": 1964
    },
    {
      "citation_key": "Barber2023Beyond",
      "id": "ref.Barber2023Beyond",
      "paper_id": "arxiv:2202.13415",
      "query": "Conformal prediction beyond exchangeability",
      "read_artifact": "literature/Barber2023Beyond.json",
      "read_scope": "Title, authors, abstract only; no references or citation links followed.",
      "source_url": "https://arxiv.org/abs/2202.13415",
      "title": "Conformal prediction beyond exchangeability",
      "year"

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
\usepackage{amsmath,amssymb,booktabs,graphicx,subcaption}
\usepackage{hyperref,url}
\title{Scale-Adaptive Conformal Regions:\\Reliability and Limits on the Simplex}
\author{}
\newcommand{\R}{\mathbb{R}}
\newcommand{\simplex}{\Delta^{K-1}_{\circ}}
\newcommand{\clip}{\operatorname{clip}}
\begin{document}
\maketitle

\begin{abstract}
Prediction regions for compositional responses must account for both the simplex constraint and variation in predictive uncertainty. We study whether scale-adaptive split-conformal regions in isometric-logratio coordinates improve reliability and efficiency together. A frozen training-only procedure combines ridge centers, local residual-moment scaling, and nested rank-based selection; independent calibration determines the final regions. Across logistic-normal, Dirichlet, and shifted-Dirichlet settings at two dimensions and eight held-out seeds, the results are condition-dependent. Mean absolute coverage error is 0.0136 under IID sampling but 0.1303 under shift. Aggregate utility exceeds the strongest standard comparator by 0.0116, with a descriptive paired 95\% seed-bootstrap interval of [0.0047, 0.0179], yet mean uniform-simplex region mass is larger: 0.3035 versus 0.2917. Gains concentrate in higher-dimensional IID Dirichlet responses, whereas shifted comparisons favor the simplex-coordinate baseline. These findings support separating observed-response coverage, reference-measure efficiency, and distributional assumptions rather than interpreting an aggregate utility gain as uniform dominance or conditional validity.


\end{abstract}

\section{Introduction}
Compositional predictions arise whenever the response is a nonnegative vector constrained to sum to one. A region around such a prediction should respect the constraint, cover the relevant future observation, and remain informative. These requirements are distinct. A small region in transformed coordinates need not occupy little of the simplex; a marginally calibrated region need not be reliable within a feature-defined population; and reliable IID behavior need not persist after a change in covariate distribution. The target itself also matters: uncertainty for an observed continuous composition is not the same problem as a set of possible class labels or a confidence region for an unobserved probability vector.

Split conformal prediction supplies a natural starting point because its marginal coverage guarantee separates fitting a predictive score from calibrating its threshold \citep{Papadopoulos2002,Lei2018,Angelopoulos2021}. Compositional geometry nevertheless leaves important evaluation choices. Logratio representations remove the sum constraint but change how region size is measured \citep{Aitchison1982,Egozcue2003}. Heteroscedastic scaling can redistribute widths without altering the calibration rule. Consequently, judging a region construction requires more than a single coverage number or a single transformed-space volume.

We ask: \emph{how do training-only scale-adaptive logratio regions trade observed-composition coverage against uniform-simplex reference mass, relative to alternatives sharing the same fitted center?} We evaluate one fixed construction rather than claiming a comprehensive comparison of conformal methods. Its scale correction uses local moments of cross-fitted standardized residuals, with a neutral option and nested training-only selection. The final calibration sample is not used to choose that correction. The comparison includes unscaled logratio regions, a joint simplex-coordinate maximum-residual region, and coordinatewise Bonferroni regions.

The empirical answer is not uniform improvement. The scale-adaptive construction has higher aggregate utility but larger aggregate simplex mass than the simplex-coordinate baseline. The most favorable contrast occurs for IID Dirichlet responses in the larger dimension; shifted conditions provide clear adverse comparisons. Thus the useful contribution is a bounded evaluation of a specified configuration and its failure modes, not a new distribution-free guarantee. 

Our contributions are: (i) an inspectable training-only scale-adaptation specification with independent finite-rank calibration; (ii) a paired synthetic assessment separating coverage, reference mass, and their utility summary; and (iii) a seed-level uncertainty analysis that retains unfavorable condition-specific comparisons and distinguishes scaling effects from untested selector-specific explanations. The scope is strictly positive continuous responses under the stated generators. Structural zeros, latent probability recovery, real-data performance, and universal geometric preferences are outside the evidence.

\begin{figure}[t]
\centering
\includegraphics[width=.98\textwidth,height=1.6in,keepaspectratio]{figures/composition_reliability_overview.png}
\caption{Study overview. Training data determine centers and local scales, including internal rank-based selection. A separate calibration sample determines conformal thresholds. Evaluation distinguishes membership of observed compositions from mass under a uniform-simplex reference distribution; neither estimand establishes conditional or shifted validity.}
\label{fig:overview}


\end{figure}

\section{Related Work}
\paragraph{Calibration and adaptation.}
The conformal framework provides finite-sample predictive coverage under exchangeability \citep{Vovk2005}; inductive constructions separate model fitting and calibration \citep{Papadopoulos2002}. Regression studies compare the statistical and computational behavior of full and split conformal inference \citep{Lei2018}, while jackknife+ uses leave-one-out predictions to account for fitting variability \citep{Barber2021Jackknife}. Here the calibration procedure is ordinary split conformal: internal cross-fitting estimates scale information but is not jackknife+ calibration. Locally adaptive intervals have been developed through quantile regression \citep{Romano2019,Sesia2020}, conditional density estimation \citep{Lei2014,Izbicki2020}, and localized conformal constructions \citep{Guan2023}. These motivate adaptation without establishing that our particular scalar correction is optimal. Selection and aggregation raise a separate issue from calibrating one fixed score \citep{Yang2024}; our fitting choices are confined to training data.

\paragraph{What coverage does not imply.}
Conditional validity requires care even for inductive predictors \citep{Vovk2012}. Distribution-free conditional predictive inference has fundamental limits \citep{Barber2021Limits}, so pooled coverage should not be promoted to a feature-conditional guarantee. Under covariate shift, weighted conformal methods use covariate likelihood ratios \citep{Tibshirani2019}; broader departures from exchangeability require their own analysis \citep{Barber2023Beyond}. Adaptive conformal inference instead studies an online coverage-frequency target \citep{Gibbs2021}. These extensions are not implemented here. Our shifted evaluation is a stress test of a fixed, unweighted calibration rule, not a comparison with shift-aware methods.

\paragraph{Composition and statistical measurement.}
Compositional analysis treats ratios and the simplex as central objects \citep{Aitchison1982,Pawlowsky2015}; logistic-normal distributions provide transformed-normal models on that space \citep{Aitchison1980}. Isometric logratio (ILR) coordinates give an orthonormal representation \citep{Egozcue2003}, but orthonormality in logratio geometry does not preserve uniform-simplex mass. Our centers use ridge regression \citep{Hoerl1970}, and the scale correction is a shrunk kernel regression of residual moments in the spirit of \citet{Nadaraya1964}. Uncertainty reporting uses resampling across independent seed blocks \citep{Efron1979,Davison1997} and distinguishes those intervals from within-sample Wilson coverage intervals \citep{Brown2001}. The contribution is the resulting controlled audit, not a claim to originate any of these ingredients.

\section{Prediction Regions and Evaluation Targets}
\label{sec:regions}
\subsection{Problem setup and calibration}
Let $X\in\R^6$ and $Y\in\simplex=\{y\in(0,1)^K:\sum_k y_k=1\}$. We predict a region $C_\alpha(X)$ for an independent \emph{observed response} $Y$, at target coverage $1-\alpha$. No class label or latent multinomial parameter is evaluated. A fixed Helmert matrix $B\in\R^{K\times(K-1)}$ satisfies $B^\top B=I$ and $B^\top\mathbf 1=0$; the representation is
\begin{equation}
 z(y)=B^\top\log y,\qquad h(z)=\operatorname{softmax}(Bz).
\end{equation}
Fitted center $\widehat\mu(x)\in\R^{K-1}$ and positive scales $\widehat s_j(x)$ define the nonconformity score
\begin{equation}
 A(x,y)=\max_{1\leq j<K}\frac{|z_j(y)-\widehat\mu_j(x)|}{\widehat s_j(x)}.
 \label{eq:score}
\end{equation}


Given $m$ independent calibration scores, use the $r$th smallest score with $r=\lceil(m+1)(1-\alpha)\rceil$, or $+\infty$ if $r>m$. The region consists of positive compositions satisfying $A(x,y)\leq q_\alpha$. It is an axis-aligned box in the fixed ILR basis, mapped back to the simplex; it is not a full-covariance ellipsoid. The finite-rank rule, including its infinite-threshold case, is owned by the evaluation code rather than the fitted predictor. 

Conditional on the training data, exchangeable calibration and test scores give $\Pr\{Y\in C_\alpha(X)\}\geq1-\alpha$ by the standard conformal rank argument \citep{Lei2018}. Ties are handled conservatively by the non-strict membership inequality. This is a statement about a random calibration sample and future response, not a guarantee for every realized test set, every fixed feature vector, or every group. Training-only adaptation leaves this argument intact because the final calibration responses do not enter score selection. The argument does not apply unchanged to our shifted test sample.

\subsection{Reliability, mass, and utility}
For each fitted instance, empirical coverage $\widehat c_\alpha$ is the fraction of test responses inside the region. Reliability error is $e_\alpha=|\widehat c_\alpha-(1-\alpha)|$, treating overcoverage and undercoverage symmetrically. Efficiency is the normalized uniform-simplex reference mass
\begin{equation}
 M_\alpha=\mathbb E_{X_{\rm test}}\Pr_{V\sim\operatorname{Dirichlet}(\mathbf1)}
 \{V\in C_\alpha(X_{\rm test})\}.
 \label{eq:mass}
\end{equation}
The implementation estimates this probability with shared probes and test contexts, not by integrating ILR-box volume. Thus $M_\alpha\in[0,1]$ is dimension-normalized simplex volume, not probability content under the response law. We use ``mass'' to keep the reference distribution explicit. Small mass alone does not establish informative calibrated prediction. 

The supplied utility combines the two empirical quantities:
\begin{equation}
 U_\alpha=(1-\widehat M_\alpha)
 \max\left\{0,1-\frac{e_\alpha}{1-\alpha}\right\}.
 \label{eq:utility}
\end{equation}
It rewards small regions and penalizes coverage error but is not a coverage constraint. A method can improve $U_\alpha$ by trading mass against error; its ordering need not agree with either component. We therefore report all components and treat utility as a supplied descriptive summary, not a proof of scientific superiority. Overall utility averages conditions and nominal levels equally. IID and shifted errors are averaged separately, after taking absolute deviations within each seed, condition, and level. Taking the absolute value after averaging coverage would produce a different estimand. 

\subsection{Compared region constructions}
\textbf{Scaled ILR} uses Eq.~\eqref{eq:score} with the fitted scales described below. \textbf{Unscaled ILR} retains exactly the same center and basis but sets every scale to one; it removes the entire scaling package, not only the local correction. \textbf{Simplex max} maps the common center through $h$ and calibrates $\max_k|y_k-h_k(\widehat\mu(x))|$. \textbf{Bonferroni} calibrates separate absolute residuals in each simplex coordinate at miscoverage $\alpha/K$ and intersects the resulting intervals with the simplex. The latter is a simultaneous-coordinate baseline, not a collection of independently claimed marginal intervals. The unscaled joint-maximum and coordinatewise Bonferroni constructions are also described in multivariate conformal prediction \citep{FanSesia2025}; here, both are intersected with the simplex. All thresholds use their own appropriate calibration residuals from the same calibration split. 


These comparisons hold center predictions fixed while changing the residual geometry or scaling. The unscaled comparison can support conclusions about the complete scaling construction within this evaluation. It cannot identify the effect of local smoothing, cross-fitting, shrinkage, or the selector individually. The simplex comparison additionally changes coordinates, so any observed contrast is a comparison between region constructions rather than a causal estimate for one isolated component.

\section{Method: Training-Only Scale Adaptation}
\label{sec:method}
\subsection{Rationale and base fits}
The design hypothesis is that feature-dependent residual variability makes constant-width ILR regions inefficient, and that a bounded, shrunk correction may allocate widths more usefully. The counter-hypothesis is equally important: a correction selected using a transformed-space size objective may not reduce simplex mass, especially under extrapolation. The study evaluates these possibilities through paired region comparisons, not through a claim of optimal scale estimation.

The design vector is $\phi(x)=(1,x,x^{\odot2},\sin x,x_0x_1)$, with coordinatewise squares and sine terms. Ridge regression of $z(Y)$ on $\phi(X)$ uses penalty 1. A second ridge fit, with penalty 10, predicts $\log\max(|z_j(Y)-\widehat\mu_j(X)|,0.02)$ from the same design. These base-scale residuals are in-sample; cross-fitting is used for the subsequent moment correction, not retroactively for the base log-residual fit. The intercept penalty is $10^{-8}$. Predicted centers are clipped to $[-100,100]$ and base scales to $[10^{-4},100]$. These are numerical bounds, not distributional assumptions. 

\subsection{Local residual moments and bounded shrinkage}
Deterministic three-fold cross-fitting within training data yields held-out centers $\widehat\mu^{(-i)}$ and base scales $\widehat s^{0,(-i)}$. For each training row define
\begin{equation}
 v_i=\frac{1}{K-1}\sum_{j=1}^{K-1}
 \left(\frac{z_j(Y_i)-\widehat\mu_j^{(-i)}(X_i)}{\widehat s_j^{0,(-i)}(X_i)}\right)^2.
\end{equation}
Training-only feature means and standard deviations standardize the covariates. With standardized distance $d_i(x)$, Gaussian weights $w_i(x)=\exp\{-d_i(x)^2/(2b^2)\}$ yield
\begin{equation}
 R(x)=\frac{\sum_iw_i(x)v_i+\lambda}{\sum_iw_i(x)+\lambda},\qquad
 a(x)=\exp\!\left\{\frac{\beta}{2}\log\clip(R(x),1/4,4)\right\}.
 \label{eq:correction}
\end{equation}
The final scales are $\widehat s_j(x)=a(x)\widehat s^0_j(x)$, with a common row-scalar further bounded to respect the allowed scale range. Shrinkage returns $R(x)$ toward one when kernel support is weak; $\beta=0$ is the neutral correction. The scalar leaves relative ILR-coordinate scales unchanged at a given $x$. It does not learn new directions or correlations. 

\subsection{Nested rank-based selection}
The finite family uses $\beta\in\{0,0.5,1\}$, $b\in\{0.5\sqrt6,\sqrt6\}$, and $\lambda\in\{10,50\}$. For each of three outer training folds, the remaining rows fit both the base model and an inner cross-fitted moment table. The held-out fold is split into two halves, used in both orientations as pseudo-calibration and evaluation data. Each pseudo-calibration half gives a finite-rank radius $q_{f,\alpha}$ at the same three miscoverage levels used for reporting. The selector minimizes the evaluation-row-weighted, level-averaged objective
\begin{equation}
 L(\theta)=\sum_f\frac{|E_f|}{n_{\rm train}}\frac{1}{|\mathcal A|}
 \sum_{\alpha\in\mathcal A}\log\left[
 \frac1{|E_f|}\sum_{i\in E_f}(2q_{f,\alpha})^{K-1}
 \prod_{j=1}^{K-1}\widehat s_{f,j,\theta}(X_i)\right],
 \label{eq:selection}
\end{equation}
where $f$ indexes both orientations and $\mathcal A=\{0.05,0.10,0.20\}$. The logarithm is applied to arithmetic mean box volume, evaluated stably, not to each row before averaging. Ties favor smaller $\beta$. The selected correction is refitted using a full training moment table. 

Crucially, Eq.~\eqref{eq:selection} measures \emph{ILR-coordinate box volume}. The nonlinear inverse map does not have a constant simplex-volume Jacobian, so this is not Eq.~\eqref{eq:mass}. A uniform multiplicative rescaling of all scales cancels against its conformal radius in the absence of clipping; improvement must come from changing allocation across inputs or coordinates, not merely multiplying all widths by a constant. The supplement derives this algebraic check. Neither property establishes that the selected correction improves the final mass or coverage.

Unavailable finite ranks, nonpositive radii, or nonfinite objectives trigger a training-only Gaussian-loss selector over the same scale family; very small samples use a neutral correction. These are source-defined fallbacks. The retained results do not record how often each fallback was used or which setting was selected in each fit. We do not infer those frequencies from aggregate performance. Independent final calibration remains unchanged in every branch. 

\section{Experimental Design and Uncertainty}
\label{sec:design}
\subsection{Synthetic conditions and held-out protocol}
The available evidence covers one continuous-composition task, with six conditions: logistic-normal IID, Dirichlet IID, and shifted Dirichlet, each at $K\in\{3,8\}$. Every condition uses six covariates, 1,024 training observations, 512 calibration observations, and 2,048 test observations. The held-out seeds are 1009, 1013, 1019, 1021, 1031, 1033, 1039, and 1049, with $\alpha\in\{0.05,0.10,0.20\}$. Each seed is a joint repeated unit containing all conditions and nominal levels, not eighteen independent replications. All recorded condition evaluations are complete. 


For IID samples, $X$ is uniform on $[-1.5,1.5]^6$. Let $W$ be the fixed sinusoidal coefficient matrix specified in the supplement, and define
\begin{equation}
 \eta_j(x)=0.7\sin((x^\top W)_j)+0.3x_0\cos j,
 \qquad j=0,\ldots,K-2.
\end{equation}
Logistic-normal responses are $h(\eta(X)+\epsilon)$ with independent Gaussian coordinates of standard deviation 0.25. The Dirichlet construction uses parameter vector $\tau(x)h(\eta(x))$, with $\tau(x)=4+35/(1+\exp(2x_0))$. The generator draws gamma coordinates, floors them at $10^{-12}$, and closes the vector to sum to one. The evaluated law is this numerically floored distribution, not an unfloored boundary model. 

Shifted conditions change only the test covariate law: coordinates are drawn from $N(0.8,1)$ and clipped to $[-2.5,3]$. Training and calibration remain IID uniform, and the conditional response recipe is unchanged. This changes both feature frequencies and support. In particular, part of the test distribution lies outside training support; ordinary likelihood-ratio weighting cannot by itself recover information there. The comparison therefore probes a demanding shift, not an overlap-controlled weighting scenario. Its mechanisms are not separately manipulated.

The evaluated scale-adaptive configuration is frozen for the held-out analysis. Development configuration scores are not pooled with held-out measurements, and we do not compare an original initializer without matched final evidence. The evaluator reports completed qualification and passing information/state controls. This establishes completion of its specified checks, not population superiority or shift validity. Missing selector-specific ablations remain missing evidence rather than measured failures. 



\subsection{Paired measurements and uncertainty}
Every method sees the same train/calibration/test data within a seed and condition. Mass uses 128 randomly selected test contexts and a shared set of 1,024 uniform-simplex probes. Pairing the contexts and probes reduces avoidable comparison noise, although it does not remove Monte Carlo error. One hit per context changes its mass estimate by $1/1024$. A zero-hit context has the reported one-sided 95\% binomial upper bound $1-0.05^{1/1024}=0.00292$; zero hits do not establish zero region mass. 

The retained evaluator supplies paired percentile bootstrap intervals for method differences, resampling the eight seeds with 20,000 draws. Its identical cross-seed uncertainty object is repeated inside seed wrappers; we deduplicate it rather than treating these copies as new data. Utility comparisons additionally include endpoints using tail probability $0.05/(2\cdot54)$ for the 54 case-by-level-by-baseline contrasts. We retain these adjusted endpoints in the supplement, but finite-bootstrap extreme quantiles with few seed blocks are descriptive and not exact familywise certificates. Mass intervals have no corresponding multiplicity adjustment. 

For the coverage curves, overall utility intervals, and feature-group mean coverage, we derive additional descriptive percentile intervals by jointly resampling seed blocks, preserving all condition and level records within a draw. The saved analysis uses 20,000 draws and bootstrap seed 20261117. These are analyses of retained measurements, not additional experiments. Per-seed Wilson intervals characterize test-membership sampling for one fitted/calibrated instance; we neither average their endpoints nor substitute them for cross-seed uncertainty. No confidence interval here captures arbitrary generator changes or adaptation to the held-out findings. 

\section{Reliability--Efficiency Results}
\label{sec:results}
\subsection{Near-target IID behavior does not survive the shift}
Figure~\ref{fig:coverage} shows the scale-adaptive construction across all nominal levels. The IID curves lie close to their targets, but not every estimated deviation is negligible. At nominal coverage 0.90, logistic-normal coverage is 0.8965 for $K=3$ and 0.8986 for $K=8$; IID Dirichlet coverage is 0.8912 and 0.8951. At nominal 0.80, IID Dirichlet coverage for $K=8$ is 0.7850 with a descriptive interval [0.7773, 0.7927]. Thus the average IID error should not be read as exact calibration in every condition. The standard finite-sample guarantee is marginal over calibration randomness, not an equality for a finite collection of realized fits. 

\begin{figure}[t]
\centering
\includegraphics[width=.98\textwidth]{figures/coverage_by_regime.pdf}
\caption{Observed-composition coverage for scaled ILR. Left: $K=3$; right: $K=8$. Whiskers are descriptive 95\% seed-block bootstrap intervals derived from retained observations. The truncated vertical axis highlights departures from the dashed nominal-coverage reference. IID behavior is close to target; the shifted Dirichlet deficit is substantial at every level. Lines connect nominal levels, not time.}
\label{fig:coverage}

\end{figure}

The shifted deficit is larger and consistent across levels. At nominal 0.90, mean coverage falls to 0.7858 [0.7647, 0.8112] for $K=3$ and 0.7399 [0.7096, 0.7739] for $K=8$. At nominal 0.80, the corresponding means are 0.6880 and 0.6239. Mean absolute error across seed-condition-level records increases from 0.0136 in IID conditions to 0.1303 under shift. This is evidence against interpreting training-only scale adaptation as a shift-robust calibration procedure. It is not evidence that conformal prediction failed under its exchangeability assumptions: those assumptions are absent in this test regime. 


\subsection{Aggregate utility and simplex mass favor different readings}
Table~\ref{tab:main} reports all standard comparators. Scaled ILR has mean utility 0.6618, compared with 0.6502 for simplex max, 0.6296 for Bonferroni, and 0.6047 for unscaled ILR. Its paired aggregate utility advantage over simplex max is 0.0116 [0.0047, 0.0179]. Nevertheless, its mean simplex mass is 0.3035 rather than 0.2917 for simplex max. The favorable utility contrast therefore does not mean the scale-adaptive regions are smaller on average. 


\begin{table}[t]
\centering\small
\caption{Held-out mean errors, normalized simplex mass, and utility. Errors are absolute deviations computed before averaging. Utility intervals are descriptive joint seed-block bootstrap intervals from our retained-data analysis. Smaller error and mass are favorable; larger utility is favorable.}
\label{tab:main}
\input{analysis/main_table.tex}

\end{table}

The same table also prevents an overly favorable reliability interpretation. Both unscaled ILR and simplex max have slightly smaller aggregate IID errors than scaled ILR, whereas all three have larger shifted errors. Bonferroni has IID error 0.0204 and shifted error 0.1620. The scale-adaptive construction reduces aggregate mass relative to unscaled ILR, from 0.3382 to 0.3035, and improves utility by 0.0572 [0.0509, 0.0642]. This is evidence about the full scaling package at the common center, not a measured gain attributable specifically to rank selection. 


\subsection{Condition-specific comparisons rule out uniform dominance}
Figure~\ref{fig:paired} compares scaled ILR with simplex max. Positive utility differences and negative mass differences have different favorable directions, shown in separate columns. The largest favorable contrasts occur for IID Dirichlet responses at $K=8$. At $\alpha=0.10$, utility increases by 0.1962 [0.1741, 0.2168], while mass decreases by 0.2024 with interval [$-0.2254$,$-0.1800$]. All reported nominal levels in that condition favor scaled ILR on both quantities. This localized pattern is stronger than the small aggregate utility difference, but it does not identify which part of the scaling construction is responsible. 

\begin{figure}[t]
\centering
\includegraphics[width=.98\textwidth]{figures/paired_region_tradeoffs.pdf}
\caption{Scaled ILR minus simplex max, with evaluator-supplied paired descriptive 95\% seed-bootstrap intervals. Rows distinguish $K$; columns distinguish utility (positive favors scaled ILR) and uniform-simplex mass (negative means smaller). All nominal levels are shown. LN denotes logistic-normal; Dir denotes Dirichlet. Shifted conditions reverse the favorable IID Dirichlet pattern.}
\label{fig:paired}

\end{figure}

The contrasts are not uniformly favorable even without shift. For IID Dirichlet $K=3$ at $\alpha=0.20$, utility is lower by 0.0323 [$-0.0451$,$-0.0199$], and mass is larger by 0.0261. Several logistic-normal contrasts are small, with descriptive intervals including zero. These results reject a blanket preference for scaled ILR across response laws, dimensions, and target levels. 


Every shifted utility contrast against simplex max is negative, and every shifted mass contrast is positive. At $\alpha=0.10$, utility differences are $-0.0732$ [$-0.0858$,$-0.0591$] for $K=3$ and $-0.0765$ [$-0.1032$,$-0.0492$] for $K=8$. Corresponding mass increases are 0.1281 and 0.1639. Importantly, scaled ILR still has the smaller aggregate shifted coverage error: its adverse shifted utility comparison cannot be summarized as worse coverage alone. The larger regions offset that reliability advantage under the supplied utility. 


\subsection{Controls and what they identify}
The evaluator checks reset behavior, constant inputs, permuted inputs, and a zero-radius point-copy control. All recorded checks pass. Constant-input and permuted-input comparisons disrupt access to predictive features at query time; they are information controls, not training-time component removals. Likewise, whole-simplex and zero-radius endpoints check the meaning of mass and coverage but cannot recommend a useful predictive region. Feature-group coverage by the sign of $x_0$ is reported in the supplement to expose heterogeneity without claiming groupwise calibration. No group-specific threshold is fitted. 


\section{Discussion and Limitations}
\paragraph{What the positive comparisons establish.}
At the evaluated center and data budget, the scaling package can improve utility and reduce simplex mass relative to removing scaling. It also provides large paired gains against simplex max in the higher-dimensional IID Dirichlet condition. These are valid configuration-level comparisons, with matched data and reported seed variation. They are not evidence that every constituent is needed, nor that the rank-based objective is preferable to Gaussian-loss selection. The final measurements contain no matched selector-only comparison. Development configurations change multiple choices and use a different evidence split, so their scores cannot fill that gap.

\paragraph{Why the negative comparisons matter.}
The mismatch between the selection objective and the evaluation reference measure is an explicit limitation of the construction. The result is compatible with that mismatch, but does not isolate it as the cause of unfavorable mass differences. The shift also jointly changes support, feature frequencies, and the frequency of high-variability responses. Its adverse coverage cannot be attributed solely to extrapolation, scale misspecificati

[truncated after 30000 chars]
```

## supplementary information excerpt

```tex
\appendix
\section{Supplementary Information}
\label{sec:supplement}

\subsection{Detailed selection specification and algebraic checks}
The archived implementation is \texttt{source\_evidence/selected\_model.py}; the evaluated entrypoint declaration is retained in \texttt{source\_evidence/selected\_spec.toml}. Basis and design construction appear at lines 89--107; base fitting and moment tables at lines 114--152; smoothing and bounded scale correction at lines 154--185; Gaussian-loss fallback at lines 188--234; and rank-based selection at lines 237--352. These readable implementations, rather than a hash or a previous assessment, support the concrete method description. 

Each call to the deterministic fold constructor permutes the relevant training indices with NumPy random seed 0 and splits them into three parts. Feature standard deviations in moment tables are bounded below by $10^{-8}$, standardized residual scales by $10^{-4}$, and kernel queries are processed in batches of 128. Neutral settings share predictions even when their redundant bandwidth or prior parameters differ. The method caches moment-ratio evaluations for repeated bandwidth/prior pairs. The selector's outer pseudo-calibration halves and evaluation halves are disjoint from one another and from the rows fitting their models. Internal folds overlap across fits and must not be counted as independent scientific replications. 

To check global-scale invariance, replace $s(x)$ by $c\,s(x)$ for constant $c>0$, ignoring numerical clipping. Every calibration score is divided by $c$, so its order-statistic radius becomes $q_\alpha/c$. The resulting coordinate half-width is $(q_\alpha/c)(c\,s_j(x))=q_\alpha s_j(x)$. Its ILR-box volume is unchanged:
\begin{equation}
 (2q_\alpha/c)^{K-1}\prod_{j=1}^{K-1}c\,s_j(x)
 =(2q_\alpha)^{K-1}\prod_{j=1}^{K-1}s_j(x).
\end{equation}
The source includes a numerical assertion for this cancellation away from clipping bounds. This is an algebraic implementation check, not an independently measured ablation. For the inner rank rule at $\alpha=0.05$, 18 pseudo-calibration observations cannot give a finite rank while 19 can. A zero radius is rejected by the selector, although a zero threshold is meaningful for the evaluator's deliberately degenerate point control. No realized fallback count is available. 

\subsection{Generator, target, and reproducibility specification}
The generator is archived in \texttt{source\_evidence/evaluate\_final.py}, lines 701--760. With zero-based indices, $W_{\ell j}=\sin(\ell(K-1)+j+1)/3$, $\ell=0,\ldots,5$. In the Helmert basis, column $j-1$ has its first $j$ entries $1/\sqrt{j(j+1)}$, entry $j$ equal to $-j/\sqrt{j(j+1)}$, and remaining entries zero. These conventions fix both the generated response and the fitted-coordinate interpretation. 

Training, calibration, test, and reference-probe random streams are separated using \texttt{SeedSequence([seed, case\_index, split\_index, 202611])}; the reference stream has split index 3. The manifest stores array and row provenance and the evaluator checks normalized float64 hashes, positive responses, closure, feature shapes, and split-content disjointness. The retained manifest is \texttt{source\_evidence/data\_manifest.json}; hashes identify the retained data but do not establish substantive methodological properties. The response is always the observed continuous vector; no latent target or categorical observation is substituted. 

\textbf{Environment and commands.} The evaluated implementation requires CPython 3.11 or 3.12 and NumPy 1.26.4, uses CPU computation, and has no downloaded dataset, pretrained model, or external data license requirement. The native evaluator additionally requires Linux process-isolation facilities documented in \texttt{source\_evidence/task\_contract.json}; a portable re-execution should not silently bypass those controls. \texttt{REPRODUCIBILITY.md} records the evaluator command, complete retained-data analysis commands, and artifact mappings. The plotting environment used here is recorded separately in \texttt{analysis/environment.json}; it is not represented as the historical evaluation environment. Runtime is not estimated from plotting time, and the final evaluation was not rerun during manuscript preparation. 



\subsection{Complete condition-level results and paired comparisons}
The following tables retain every condition, nominal level, and standard baseline. Utility and mass differences are always scaled ILR minus the named comparator. The 95\% paired intervals and adjusted utility endpoints are copied from the deduplicated evaluator uncertainty record, while the coverage intervals are newly derived from existing seed-level observations. Adjusted utility endpoints do not apply to mass or feature-group coverage. Rounding is for display only; machine-readable values remain in \texttt{analysis/summary.json}. 

\begin{table}[p]
\centering\small
\caption{Scaled-ILR results by condition. Coverage intervals resample seed blocks; mass and utility are empirical means.}
\begin{tabular}{llrrrr}
\toprule
Condition & $\alpha$ & Coverage & 95\% interval & Mass & Utility \\
\midrule
LN K3 & 0.05 & 0.9491 & [0.9432,0.9558] & 0.1308 & 0.8620 \\
LN K3 & 0.10 & 0.8965 & [0.8906,0.9020] & 0.0976 & 0.8955 \\
LN K3 & 0.20 & 0.7930 & [0.7815,0.8054] & 0.0676 & 0.9127 \\
LN K8 & 0.05 & 0.9475 & [0.9407,0.9555] & 0.0035 & 0.9874 \\
LN K8 & 0.10 & 0.8986 & [0.8882,0.9106] & 0.0018 & 0.9829 \\
LN K8 & 0.20 & 0.7997 & [0.7852,0.8162] & 0.0009 & 0.9748 \\
Dir K3 & 0.05 & 0.9481 & [0.9396,0.9541] & 0.3980 & 0.5977 \\
Dir K3 & 0.10 & 0.8912 & [0.8693,0.9072] & 0.3141 & 0.6707 \\
Dir K3 & 0.20 & 0.7967 & [0.7758,0.8149] & 0.2324 & 0.7473 \\
Dir K8 & 0.05 & 0.9485 & [0.9387,0.9572] & 0.5627 & 0.4320 \\
Dir K8 & 0.10 & 0.8951 & [0.8841,0.9072] & 0.4462 & 0.5441 \\
Dir K8 & 0.20 & 0.7850 & [0.7773,0.7927] & 0.3165 & 0.6703 \\
Shift K3 & 0.05 & 0.8563 & [0.8323,0.8832] & 0.4909 & 0.4577 \\
Shift K3 & 0.10 & 0.7858 & [0.7647,0.8112] & 0.4042 & 0.5192 \\
Shift K3 & 0.20 & 0.6880 & [0.6633,0.7163] & 0.3142 & 0.5885 \\
Shift K8 & 0.05 & 0.8240 & [0.8009,0.8492] & 0.6622 & 0.2920 \\
Shift K8 & 0.10 & 0.7399 & [0.7096,0.7739] & 0.5668 & 0.3540 \\
Shift K8 & 0.20 & 0.6239 & [0.5877,0.6634] & 0.4528 & 0.4238 \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[p]
\centering\scriptsize
\caption{Scaled ILR minus Unscaled ILR. Descriptive paired 95\% intervals and adjusted utility endpoints are supplied by the evaluator. Mass intervals are unadjusted.}
\begin{tabular}{llrrrrr}
\toprule
Condition & $\alpha$ & $\Delta U$ & 95\% interval & Adjusted interval & $\Delta M$ & 95\% interval \\
\midrule
LN K3 & 0.05 & -0.003 & [-0.007,+0.002] & [-0.009,+0.006] & +0.002 & [-0.001,+0.005] \\
LN K3 & 0.10 & -0.005 & [-0.009,-0.001] & [-0.011,+0.002] & +0.003 & [+0.000,+0.005] \\
LN K3 & 0.20 & -0.006 & [-0.012,+0.001] & [-0.016,+0.005] & +0.001 & [+0.000,+0.001] \\
LN K8 & 0.05 & +0.001 & [-0.003,+0.006] & [-0.006,+0.010] & +0.001 & [+0.000,+0.001] \\
LN K8 & 0.10 & +0.001 & [-0.008,+0.010] & [-0.012,+0.017] & +0.000 & [+0.000,+0.000] \\
LN K8 & 0.20 & +0.004 & [-0.009,+0.018] & [-0.016,+0.027] & +0.000 & [+0.000,+0.000] \\
Dir K3 & 0.05 & +0.119 & [+0.094,+0.145] & [+0.081,+0.159] & -0.117 & [-0.141,-0.096] \\
Dir K3 & 0.10 & +0.031 & [+0.018,+0.043] & [+0.010,+0.050] & -0.041 & [-0.056,-0.026] \\
Dir K3 & 0.20 & -0.026 & [-0.036,-0.015] & [-0.040,-0.008] & +0.019 & [+0.009,+0.029] \\
Dir K8 & 0.05 & +0.367 & [+0.334,+0.406] & [+0.323,+0.433] & -0.372 & [-0.413,-0.337] \\
Dir K8 & 0.10 & +0.300 & [+0.287,+0.315] & [+0.280,+0.326] & -0.306 & [-0.325,-0.289] \\
Dir K8 & 0.20 & +0.107 & [+0.100,+0.115] & [+0.095,+0.119] & -0.111 & [-0.123,-0.098] \\
Shift K3 & 0.05 & -0.025 & [-0.046,-0.005] & [-0.059,+0.007] & +0.052 & [+0.019,+0.088] \\
Shift K3 & 0.10 & -0.033 & [-0.043,-0.021] & [-0.050,-0.014] & +0.100 & [+0.078,+0.124] \\
Shift K3 & 0.20 & +0.016 & [-0.004,+0.034] & [-0.020,+0.044] & +0.129 & [+0.110,+0.150] \\
Shift K8 & 0.05 & +0.139 & [+0.106,+0.179] & [+0.095,+0.203] & -0.148 & [-0.200,-0.106] \\
Shift K8 & 0.10 & +0.049 & [+0.020,+0.088] & [+0.010,+0.121] & -0.008 & [-0.064,+0.040] \\
Shift K8 & 0.20 & -0.007 & [-0.024,+0.019] & [-0.028,+0.041] & +0.172 & [+0.108,+0.226] \\
\bottomrule
\end{tabular}
\end{table}
\begin{table}[p]
\centering\scriptsize
\caption{Scaled ILR minus Simplex max. Descriptive paired 95\% intervals and adjusted utility endpoints are supplied by the evaluator. Mass intervals are unadjusted.}
\begin{tabular}{llrrrrr}
\toprule
Condition & $\alpha$ & $\Delta U$ & 95\% interval & Adjusted interval & $\Delta M$ & 95\% interval \\
\midrule
LN K3 & 0.05 & +0.017 & [+0.006,+0.028] & [+0.003,+0.036] & -0.017 & [-0.025,-0.010] \\
LN K3 & 0.10 & +0.014 & [+0.009,+0.019] & [+0.005,+0.022] & -0.010 & [-0.014,-0.005] \\
LN K3 & 0.20 & +0.007 & [-0.003,+0.015] & [-0.009,+0.019] & -0.004 & [-0.007,-0.002] \\
LN K8 & 0.05 & +0.018 & [+0.012,+0.022] & [+0.008,+0.024] & -0.021 & [-0.024,-0.019] \\
LN K8 & 0.10 & +0.006 & [-0.001,+0.012] & [-0.008,+0.015] & -0.007 & [-0.009,-0.006] \\
LN K8 & 0.20 & -0.001 & [-0.010,+0.007] & [-0.015,+0.012] & -0.002 & [-0.003,-0.002] \\
Dir K3 & 0.05 & +0.038 & [+0.017,+0.061] & [+0.004,+0.074] & -0.040 & [-0.066,-0.015] \\
Dir K3 & 0.10 & -0.006 & [-0.022,+0.012] & [-0.032,+0.022] & -0.001 & [-0.023,+0.022] \\
Dir K3 & 0.20 & -0.032 & [-0.045,-0.020] & [-0.053,-0.013] & +0.026 & [+0.017,+0.036] \\
Dir K8 & 0.05 & +0.234 & [+0.189,+0.278] & [+0.159,+0.303] & -0.237 & [-0.283,-0.192] \\
Dir K8 & 0.10 & +0.196 & [+0.174,+0.217] & [+0.158,+0.229] & -0.202 & [-0.225,-0.180] \\
Dir K8 & 0.20 & +0.077 & [+0.062,+0.094] & [+0.056,+0.104] & -0.082 & [-0.098,-0.066] \\
Shift K3 & 0.05 & -0.079 & [-0.094,-0.067] & [-0.104,-0.063] & +0.095 & [+0.071,+0.125] \\
Shift K3 & 0.10 & -0.073 & [-0.086,-0.059] & [-0.090,-0.049] & +0.128 & [+0.107,+0.152] \\
Shift K3 & 0.20 & -0.035 & [-0.052,-0.016] & [-0.059,-0.003] & +0.124 & [+0.101,+0.147] \\
Shift K8 & 0.05 & -0.037 & [-0.073,-0.004] & [-0.096,+0.012] & +0.068 & [+0.019,+0.124] \\
Shift K8 & 0.10 & -0.077 & [-0.103,-0.049] & [-0.118,-0.031] & +0.164 & [+0.114,+0.216] \\
Shift K8 & 0.20 & -0.058 & [-0.074,-0.040] & [-0.081,-0.025] & +0.232 & [+0.189,+0.273] \\
\bottomrule
\end{tabular}
\end{table}
\begin{table}[p]
\centering\scriptsize
\caption{Scaled ILR minus Bonferroni. Descriptive paired 95\% intervals and adjusted utility endpoints are supplied by the evaluator. Mass intervals are unadjusted.}
\begin{tabular}{llrrrrr}
\toprule
Condition & $\alpha$ & $\Delta U$ & 95\% interval & Adjusted interval & $\Delta M$ & 95\% interval \\
\midrule
LN K3 & 0.05 & +0.031 & [+0.021,+0.043] & [+0.018,+0.050] & -0.027 & [-0.034,-0.021] \\
LN K3 & 0.10 & +0.029 & [+0.023,+0.038] & [+0.021,+0.046] & -0.021 & [-0.026,-0.016] \\
LN K3 & 0.20 & +0.046 & [+0.027,+0.066] & [+0.016,+0.077] & -0.018 & [-0.022,-0.014] \\
LN K8 & 0.05 & +0.026 & [+0.021,+0.032] & [+0.018,+0.036] & -0.026 & [-0.031,-0.021] \\
LN K8 & 0.10 & +0.007 & [-0.004,+0.018] & [-0.013,+0.023] & -0.010 & [-0.012,-0.008] \\
LN K8 & 0.20 & +0.015 & [+0.006,+0.025] & [+0.002,+0.031] & -0.003 & [-0.004,-0.003] \\
Dir K3 & 0.05 & +0.087 & [+0.064,+0.106] & [+0.047,+0.115] & -0.085 & [-0.101,-0.064] \\
Dir K3 & 0.10 & +0.043 & [+0.022,+0.064] & [+0.011,+0.078] & -0.044 & [-0.063,-0.027] \\
Dir K3 & 0.20 & +0.042 & [+0.024,+0.057] & [+0.012,+0.066] & -0.018 & [-0.027,-0.008] \\
Dir K8 & 0.05 & +0.246 & [+0.207,+0.285] & [+0.182,+0.308] & -0.250 & [-0.291,-0.211] \\
Dir K8 & 0.10 & +0.216 & [+0.192,+0.242] & [+0.178,+0.259] & -0.222 & [-0.250,-0.197] \\
Dir K8 & 0.20 & +0.146 & [+0.131,+0.160] & [+0.118,+0.169] & -0.139 & [-0.155,-0.126] \\
Shift K3 & 0.05 & -0.055 & [-0.074,-0.040] & [-0.088,-0.035] & +0.051 & [+0.019,+0.092] \\
Shift K3 & 0.10 & -0.072 & [-0.085,-0.058] & [-0.092,-0.047] & +0.084 & [+0.060,+0.109] \\
Shift K3 & 0.20 & -0.064 & [-0.081,-0.046] & [-0.088,-0.033] & +0.084 & [+0.059,+0.108] \\
Shift K8 & 0.05 & -0.023 & [-0.060,+0.009] & [-0.083,+0.020] & +0.047 & [-0.004,+0.104] \\
Shift K8 & 0.10 & -0.066 & [-0.092,-0.040] & [-0.106,-0.022] & +0.130 & [+0.081,+0.184] \\
Shift K8 & 0.20 & -0.073 & [-0.088,-0.055] & [-0.094,-0.040] & +0.186 & [+0.140,+0.230] \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Feature-group reliability and information controls}
The two observable audit groups are $x_0>0$ and $x_0\leq0$. They are defined by an input, not by a realized response, and do not create group-specific calibration thresholds. Figure~\ref{fig:groups} reports mean group coverage at nominal 0.90, with joint seed-block intervals. Each seed contributes its group fraction, rather than pooling all test rows as independent repeated fits. Group sample counts and per-seed Wilson intervals are retained in the final evidence. The visual comparison is descriptive and not a test of full conditional validity. 

\begin{figure}[ht]
\centering
\includegraphics[width=.98\textwidth]{figures/feature_group_reliability.pdf}
\caption{Feature-group coverage of scaled ILR at nominal 0.90. Whiskers are descriptive seed-block 95\% bootstrap intervals; the dashed line marks the target, not a groupwise guarantee. Both dimensions retain the shifted reliability deficit. These audit groups are not used for Mondrian calibration.}
\label{fig:groups}

\end{figure}

The constant-input control replaces each query feature vector by the training-feature mean before prediction. The permuted-input control rotates calibration rows and test rows separately, disrupting feature-response alignment without transferring labels. The constant-center reference uses the training mean in ILR coordinates and unit scales. These controls change information available at prediction time or the center itself; they are not interchangeable with the matched-center unscaled comparison. The evaluator supplies feature-control paired utility intervals in the retained uncertainty object. We do not use passing controls as evidence that every scientific validity threat has been excluded. 

\subsection{Reference-mass resolution and degenerate controls}
Uniform-simplex probes are shared across test contexts and methods within each condition/seed. The per-context reported standard-error diagnostic is $\sqrt{\widehat p(1-\widehat p)/1024}$; the evaluator averages this diagnostic across contexts. It is not a valid replacement for a joint uncertainty calculation because the same probes are reused. At zero hits, the plugin diagnostic vanishes even though the one-sided binomial upper bound is positive. Reporting a zero mass estimate must therefore not be converted into a claim of zero geometric volume. This distinction is especially relevant for small high-dimensional regions. 

The whole-simplex construction has unit reference mass and covers every observed composition; its utility is zero because the efficiency factor vanishes. The zero-radius reference tests equality with a fitted point, not recovery of the original observation. These endpoints check that metric behavior is interpretable, but do not supply an efficiency comparison among useful calibrated sets. No separate integration over simplex faces or boundary strata is present. All measured mass refers to the full-dimensional uniform-simplex reference distribution. 

\subsection{Evidence provenance and comparison scope}
The independent final record reports completion, qualification, and successful specified checks. Qualification facts are grounded in the final qualification fields, independently of any development summary; they do not strengthen the statistical claims. The manuscript retains the shifted deficits and unfavorable region-size comparisons despite that outcome. The original initializer has no matched held-out result in this bundle, so no final comparison with it is reported. 



Development evidence also contains a joint center/scale configuration and a Gaussian-selected local-moment configuration, archived in \texttt{source\_evidence/development\_joint.py} (line 152) and \texttt{source\_evidence/development\_gaussian.py} (line 185). They are provenance context, not final selector ablations: their scores are development measurements, not held-out measurements of the same controlled intervention. The main text consequently reports neither development-score margins nor a selector-specific causal advantage. Proposed alternative geometries, groupwise calibration, and latent-target diagnostics are not treated as completed measurements. Missing experiments remain limitations, not negative outcomes. 

\subsection{LLM Usage}
Language models assisted hypothesis formulation, training-only method design, implementation preparation, reference-query planning, synthesis of retained measurements, manuscript drafting, and construction of plotting and validation scripts. The manuscript-writing assistant inspected archived implementations and final records, generated figures from existing measurements, and retrieved exact foundational references for the cited background. It did not generate new scientific evaluation episodes. The overview figure is prepared through an automated concept-figure workflow; quantitative plots are deterministic visualizations of retained records. No model-generated number is used as an empirical result. No human-supervision procedure or independent replication is asserted beyond the documented checks. The process logs are retained for audit without identifying authors.
```
