# Reproduction and evidence guide

## Scope and files

This manuscript analyzes retained evaluator outputs; manuscript preparation did not run a new model evaluation. `paper_data.json` is the read-only numerical registry. `claims_grounding.json` maps manuscript claims to its stable source identifiers and to bibliographic provenance. Additional `implementation_evidence` entries identify readable source locations, not merely hashes. `source_evidence/manifest.json` records the exact copied source files and hashes. The final evaluation is completed and qualified, but the scientific coverage/volume failures remain in the main paper.

The study is entirely synthetic. There is no downloaded real dataset, account requirement, or third-party dataset-license acceptance. Frozen resource files and their generation details are copied into `reproduction/resources/final/` and `reproduction/resources/search/`. `reproduction/inventory.json` records checked hashes; `package_reproduction.py` makes these exact source copies without running an evaluation. The original `task` link is not required to replay the packaged final corpus. Do not treat public seed labels as sufficient to regenerate the corpus: private per-resource entropy is used and the frozen NPZ arrays are necessary for exact replay.

## Environment

The evaluated scientific dependency is `numpy==2.2.6`, as recorded in `source_evidence/requirements.txt`. The evaluated implementations are Python and standard-library code plus NumPy. The evaluator additionally requires Linux CPU-affinity/resource limits and its Landlock/seccomp isolation facilities. The original historical Python patch version and exact hardware were not retained in the evidence registry; manuscript construction uses the environment recorded in `paper_environment.json`, without claiming it was the historical evaluation environment.

For figures/tables and PDF inspection, install packages from `requirements-paper.txt` into a private environment outside this manuscript directory. A working TeX Live installation, BibTeX, and Poppler `pdftotext` are needed for compilation/validation. Do not put package trees in the manuscript workspace.

```sh
python3 -m venv /tmp/composition-paper-env
/tmp/composition-paper-env/bin/pip install -r requirements-paper.txt
/tmp/composition-paper-env/bin/python build_artifacts.py
/tmp/composition-paper-env/bin/python enrich_joint_region.py
/tmp/composition-paper-env/bin/python build_claims.py
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```

The plotting script preserves an orchestrator-rendered overview when `.concept_figure_complete` exists or a nonempty overview prompt log is present. It never overwrites that rendered asset. Before orchestration the overview PNG is a compile-safe pending placeholder; the finished overview is supplied synchronously by the outer workflow, not claimed as a finished diagram by this writing step.

The bounded citation-enrichment script reads the archived abstract and method source in `literature/Henderson2024/`, records the inspected construction, and idempotently retains one additional joint-region reference. It does not search the literature or run an experiment. The cited preprint was submitted in 2024; the inspected version is the June 2025 revision. This literature comparator is not an evaluated baseline. If rebuilding the foundational bibliography with `finalize_references.py`, rerun `enrich_joint_region.py` afterward.

## Scientific replay (not performed during writing)

Use the distributed final evaluator and selected source, not a rewritten approximation:

```sh
python3 -m venv /tmp/composition-eval-env
/tmp/composition-eval-env/bin/pip install -r source_evidence/requirements.txt
TASK_SOURCE_DIR="$PWD/reproduction" /tmp/composition-eval-env/bin/python source_evidence/evaluate_final.py \
  --program_path "$PWD/source_evidence/adaptive.py" \
  --results_dir /tmp/composition-replay
```

The evaluator copies the source directory into an isolated process. For minimal replay packaging, copy `source_evidence/adaptive.py` alone into a clean temporary source directory and use that path if the full source-evidence directory exceeds the evaluator's file limits. Preserve the original final NPZ files with matching manifest hashes. This replay command is documented from the inspected CLI and is not asserted to have been rerun here. Seed labels, counts and all other settings are read from the frozen evaluator/resource manifests.

Observed retained per-seed episode duration totals span 6.46–7.59 seconds. These are not full end-to-end timings, installation timings or hardware-specific forecasts. No new wall-time estimate is fabricated. Figure construction and literature lookup are separate from those measured durations.

## Output map

| Manuscript object | Construction | Inputs |
|---|---|---|
| Overview | Outer `generate-concept-figure` workflow | `paper_strategy.json`, finished `paper.tex` |
| Condition comparison | `build_artifacts.py` | final episode coverage and volume |
| Sign-stratum comparison | `build_artifacts.py` | C2/C4 final episode sign-mask rates |
| Auxiliary configuration comparison | `build_artifacts.py` | three development configurations' episode records |
| Condition-mean table | `build_artifacts.py` → `tables/condition_means.tex` | final episodes |
| Complete seed table | `build_artifacts.py` → `tables/seed_results.tex` | final episodes including Wilson intervals and MC SE |
| Aggregate contrast table | `paper.tex` | registered final metrics and released paired bootstrap intervals |
| Operational-check table | `paper.tex` | final episode checks and independent qualification fields |

`derived/complete_results.json` preserves per-anchor volumes, all sign-mask rates, radii/ranks, point errors and paired integration errors. Empty constant-input negative-sign masks keep their original zero encodings and are separately flagged as empty, never treated as measured zero coverage. `derived/summary.json` contains deterministic means and sample SDs across retained seeds, not newly simulated results. `derived/search_comparison.json` is strictly development-data evidence. All quantitative plots have PDF and 300-DPI PNG outputs, and LaTeX uses the vector PDF. Adjacent provenance sidecars point to actual source files.

## Literature independence and reading scope

No broad task-identifying query or citation chaining was performed during manuscript writing. A supplied bibliography containing many application-specific compositional citations was replaced with direct-identifier lookups of foundational methodology. Original metadata, official arXiv abstracts and selected downloaded papers are under `literature/`; `reading.json`, `reading_report.txt`, and `references_provenance.json` state the actual scope of inspection. Selected conformal papers were inspected through their opening methodological pages; other entries were read at metadata/abstract level, not asserted to have undergone full-text review. Publisher access failures are retained rather than hidden. This is not a novelty certification or systematic review.

No prohibited-source encounter was identified during this manuscript-writing step. This statement does not certify unobserved earlier retrieval. If a later reader encounters prohibited material, stop reading it and append the URL, location and extent of exposure to the log rather than using it.

## Verification

Use the staged `validate-paper` scripts for source/citation checks, claim/provenance checks, figure schema/readability checks, compilation and visible Supplementary Information checks. Use the `scientific-evidence` verifier for dangling-reference checks. `validation_report.json` records the performed checks and any environmental limitation; it must not be interpreted as a substitute for a human scientific review. No private-entropy generation, new component ablation or missing gate diagnostic is inferred from a passing artifact check.
