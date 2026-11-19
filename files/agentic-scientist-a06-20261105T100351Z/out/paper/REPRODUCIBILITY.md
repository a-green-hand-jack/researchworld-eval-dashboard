# Reproduction guide

## Evidence and scientific scope

The manuscript analyzes the completed, immutable `paper_data.json.final_evaluation`, independently of the development-selection record. The final status is completed and qualified; this is not a superiority test. No alternative allocation has a scored development evaluation. Missing scores do not establish inferior performance. No scientific experiment was executed during manuscript preparation.

The known-truth simulation and the real-model benchmark conditions are distinct evidence families, not distinct independent benchmark datasets. The record has five seeds, each with eight conditions. Audit agreement is not population MSE or validated population coverage.

@evidence[[paper_data.json#/final_evaluation]]
@evidence[[paper_data.json#/downstream_study]]

## Regenerate paper artifacts without model calls

Use a private environment outside the manuscript directory:

```sh
python3 -m venv /tmp/report-paper-tools
/tmp/report-paper-tools/bin/pip install numpy==2.5.4 matplotlib==3.11.2 requests==2.34.2 jsonschema==4.26.0 PyMuPDF==2.1
/tmp/report-paper-tools/bin/python build_artifacts.py
python3 build_claims.py
```

These are the versions actually used for paper-step plotting and inspection. They are not asserted to be the scientific-evaluation environment. Matplotlib uses its deterministic noninteractive backend and does not resample experiment outcomes. Plotting and summarization took seconds locally; no cross-machine runtime guarantee is implied.

The official ICLR 2026 files `iclr2026_conference.sty` and `iclr2026_conference.bst` are included. They were obtained directly from `https://github.com/ICLR/Master-Template/tree/master/iclr2026`. The supplied historical evaluator resource templates for another year remain frozen resource inputs only; the manuscript does not use them.

```sh
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
python3 finalize_artifacts.py
```

The overview renderer failed, as recorded in `figures/reporting_overview.prompts.json` and `concept_figure_run.log`; the retained image is a title-only placeholder, not a rendered conceptual diagram. `build_artifacts.py` never overwrites an existing overview and respects `.concept_figure_complete`; it does not generate a substitute conceptual diagram. Quantitative PDFs remain vector sharp and have 300-DPI PNG companions.

## Table and figure mapping

| Manuscript object | Generator | Outputs |
| --- | --- | --- |
| Selection/reporting overview | Title-only placeholder from `build_artifacts.py`; `generate-concept-figure` failed, with failure log retained | `figures/reporting_overview.png`, `.prompts.json` |
| Reporting error figure | `build_artifacts.py` | `figures/reporting_error_comparison.pdf`, `.png` |
| Selected-minus-fixed audit figure | `build_artifacts.py` | `figures/real_audit_accuracy_difference.pdf`, `.png` |
| All-comparator table | `build_artifacts.py` | `tables/main_results.tex` |
| Synthetic regime table | `build_artifacts.py` | `tables/synthetic_regimes.tex` |
| Complete seed table | `build_artifacts.py` | `tables/seed_results.tex`; the identical table is embedded directly in `paper.tex` because the supplementary-source validator forbids imported TeX |
| Condition/seed results | `build_artifacts.py` | `analysis/condition_results.csv` |
| All retained synthetic regime metrics and supplied marginal MSE standard errors | `build_artifacts.py` | `analysis/regime_results.csv` |
| Derived means and paired interval data | `build_artifacts.py` | `analysis/summary.json` |
| Claim mapping | `build_claims.py` | `claims_grounding.json` |

@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]

Means give seeds equal weight, and synthetic means give regimes equal weight. No paired method-difference standard error is fabricated from marginal MSE standard errors. Real observations are finite audits; shared-pool samples and bootstrap intervals are not treated as independent replications.

## Scientific code, data, and inference reproduction

Readable evaluated policy source and its entrypoint specification are preserved under `source_evidence/downstream/program/`. The baseline policy has identical source under `source_evidence/downstream/baseline/`. The readable final evaluator is `source_evidence/evaluate_final.py`; its SHA256 equals the final record's evaluator SHA256. A hash alone does not support implementation claims; inspect the cited source locations in the manuscript and claim mapping.

The supplied scientific dependency specification is `source_evidence/requirements.txt`:

```text
numpy==2.2.6
pyarrow==19.0.1
torch==2.6.0
transformers==4.51.3
safetensors==0.5.3
scipy==1.15.3
matplotlib==3.10.3
```

The runtime manifest specifies CPython 3.12 on Linux x86_64, CPU float32 model inference, float64 statistics, native process isolation, and deterministic execution. An independently retained inventory of actually loaded scientific packages was not supplied. Native isolation requires the Linux mechanisms documented by the evaluator; an arbitrary desktop or container may not satisfy them.

The included `source_evidence/resources/` snapshots retain the exact final question pool, split and synthetic manifests, smoke subset, runtime checksums, and frozen evaluator template resources. The final pool has 4096 questions. The preparation manifest records normalization and overlap checks, 11711 unique groups, and allocation seed 732091. The normalization/preparation utility itself was not supplied, so reconstituting identical pools from a fresh raw-data download is **not** claimed; use the provided exact snapshots for bitwise reproduction.

MMLU-Pro source: `https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro`, revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`. The task describes the dataset card as MIT. A raw snapshot can be obtained with Hugging Face Hub's `snapshot_download(..., repo_type="dataset", revision=...)`, but it is not a substitute for the retained pool and allocation manifest. Public questions may have been present in model pretraining.

Model: `HuggingFaceTB/SmolLM2-135M-Instruct`, revision `12fd25f77366fa6b3b4b768ec3050bf629380bac`. Model weights are not duplicated into the manuscript directory. Download the pinned model into a private reproduction resource tree:

```sh
python3 -m venv /tmp/report-evaluation
/tmp/report-evaluation/bin/pip install -r source_evidence/requirements.txt
mkdir -p /tmp/report-reproduction/resources/final
cp -R source_evidence/resources/. /tmp/report-reproduction/resources/final/
/tmp/report-evaluation/bin/python -c 'from huggingface_hub import snapshot_download; snapshot_download(repo_id="HuggingFaceTB/SmolLM2-135M-Instruct", revision="12fd25f77366fa6b3b4b768ec3050bf629380bac", local_dir="/tmp/report-reproduction/resources/final/model")'
TASK_SOURCE_DIR=/tmp/report-reproduction /tmp/report-evaluation/bin/python source_evidence/evaluate_final.py \
  --program_path "$PWD/source_evidence/downstream/program/src/program.py" \
  --results_dir /tmp/report-reproduction/output
```

These are future reproduction commands, **not executions performed for this paper**. The evaluator verifies all resource checksums, including frozen auxiliary template files; changing them invalidates exact reproduction. It runs seeds `1009, 2027, 3037, 4051, 5059`, question counts 64 and 256, prompt counts 1 and 16, four synthetic regimes, and 1024 matrices per regime. It reserves 512 audit questions in each real condition. The answer worker fixes its tensor RNG seed to zero; the bootstrap RNG uses evaluation seed plus 76531 with 200 draws.

@evidence[[source_evidence/evaluate_final.py#L899]]
@evidence[[source_evidence/resources/runtime_manifest.json]]
@evidence[[source_evidence/resources/split_manifest.json]]

The supplied seed durations range from 1871.14 to 3077.38 seconds, summing to 12236.48 seconds (3.40 hours). This is reported wall duration, not CPU-hours, energy, tokens, or a guarantee about a fresh uncached run. The evaluator's full-run wall allowance is 43200 seconds. The frozen small model and CPU constraints limit comparison with the task's broader budget. Actual token totals and a complete end-to-end compute ledger were not retained.

@evidence[[analysis/summary.json#/episode_durations_seconds]]
@evidence[[source_evidence/evaluate_final.py#L30]]

## Validation and provenance

```sh
python3 .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
python3 .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
```

Figure schema, planned density limits, rendered page geometry, exact source digest, and literal manuscript language are also checked by `validate_local.py`. The packaged figure CLI imports an unavailable orchestrator module in this container, so local validation uses its canonical JSON schema and explicitly checks the strategy budgets. The packaged compile-input validator rejects a system TeX configuration symlink crossing between two individually approved system roots. Local validation preserves the original recorder, records the symlink mapping, and validates an additional canonical-path recorder for exactly the same existing input files; it does not change TeX inputs or the validator. Rendered Supplementary Information is checked separately by the supplied CLI.

Reference consultation was restricted to fixed permitted starters and known foundational originals. `prepare_references.py` retrieves metadata/abstracts without topical exploration or citation traversal; `complete_reference_consultation.py` records original-document consultation where publisher metadata lacked an abstract. The bibliography contains only the 25 cited records, with per-record consultation extent. Abstract-only consultation is not represented as full-text reading. In one lookup, an incorrectly remembered arXiv identifier returned an unrelated mathematical article; it was rejected and the intended cross-validation paper was resolved by exact DOI before citation. No known prohibited-study encounter occurred. No result from an inaccessible or unrelated record was used.
