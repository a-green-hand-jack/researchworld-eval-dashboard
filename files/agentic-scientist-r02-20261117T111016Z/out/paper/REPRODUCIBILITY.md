# Reproduction and evidence guide

## Scope
The manuscript analyzes retained final-evaluation measurements in `paper_data.json` without rerunning the research evaluation. `final_evaluation` is independent of development records; its outcome is completed and qualified. This does not establish superiority or validity under shift. No `downstream_study` is present. All available task results concern one continuous-composition task with six synthetic conditions; no cross-task or real-data evidence exists.

## Evaluated code and resources
- `source_evidence/selected_model.py`: verbatim archived selected entrypoint, including all fitting and selection code.
- `source_evidence/selected_spec.toml`: verbatim entrypoint specification.
- `source_evidence/evaluate_final.py`: verbatim evaluator with synthetic generator, calibration, baselines, controls and bootstrap definitions.
- `source_evidence/data_manifest.json`: frozen final synthetic-data provenance, including sample counts and array/row hashes.
- `task/resources/final/`: the existing frozen NPZ arrays used by the evaluator.
- `source_evidence/requirements.txt`: NumPy 1.26.4, matching the historical evaluator requirement. CPython 3.11 or 3.12 is required.

The synthetic responses have no downloaded dataset or pretrained weights. There is no third-party data version or data-license condition; the generator version is `composition-v1`. Native research re-execution requires Linux Landlock ABI >=3, libseccomp.so.2, the process-isolation and CPU/memory allowances in `task/task_contract.json`, and the frozen resources. The analysis and manuscript do not bypass those checks.

For a supported native environment, the canonical full research evaluation command is:

```sh
python -m venv /tmp/composition-evaluation
/tmp/composition-evaluation/bin/pip install -r source_evidence/requirements.txt
TASK_SOURCE_DIR="$PWD/task" /tmp/composition-evaluation/bin/python source_evidence/evaluate_final.py \
  --program_path "$PWD/source_evidence/selected_model.py" --results_dir /tmp/composition-final-reproduction
```

This command is provided for reproduction, **not executed during manuscript preparation**. Existing records contain per-seed evaluation durations summing to 137.31 seconds; these are not a full end-to-end wall-clock estimate for another machine. The evaluator's declared wall-clock cap is 3600 seconds.
<!-- @evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]] -->
<!-- @evidence[[source_evidence/evaluate_final.py#WALL_SECONDS]] --> Hardware timing portability is unmeasured. Final seeds are 1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049. Each condition has training/calibration/test sizes 1024/512/2048; alpha values are .05/.10/.20. Source and frozen manifest specify every generator substream and coefficient.

## Retained-data analysis and figures
All auxiliary package environments are outside the manuscript directory:

```sh
python -m venv /tmp/paper-tools
/tmp/paper-tools/bin/pip install -r analysis/requirements.txt
/tmp/paper-tools/bin/python build_analysis.py
/tmp/paper-tools/bin/python build_claims.py
```

The actual analysis environment versions are recorded in `analysis/environment.json`; these are not asserted to be the historical research environment. The original numerical study requires its separate pinned NumPy environment. `build_analysis.py` reads all measurements from the final evidence, never the development scores. Its additional descriptive intervals use 20000 joint seed-block draws at seed 20261117. Stored paired intervals are copied once from the duplicated evaluator uncertainty object; they are not recomputed as independent observations.

| Paper artifact | Producer | Inputs |
| --- | --- | --- |
| Main method summary table | `build_analysis.py` -> `analysis/main_table.tex` | Final per-seed method records |
| Full coverage table | `build_analysis.py` -> `analysis/coverage_table.tex` | Same retained records |
| Complete paired comparison tables | `build_analysis.py` -> `analysis/complete_comparisons.tex` | Deduplicated final uncertainty object |
| Coverage figure | `build_analysis.py` -> `figures/coverage_by_regime.pdf` | Per-seed scaled-ILR coverage |
| Paired utility/mass figure | `build_analysis.py` -> `figures/paired_region_tradeoffs.pdf` | Stored simplex-baseline paired intervals |
| Supplementary group figure | `build_analysis.py` -> `figures/feature_group_reliability.pdf` | Final sign-of-x0 group records |
| Conceptual overview | Orchestrator-owned `generate-concept-figure` workflow | Strategy and manuscript, no invented measurements |
| Claim map | `build_claims.py` -> `claims_grounding.json` | Registry, readable implementation evidence, derived summaries, references |

Each quantitative PDF also has a PNG preview and an adjacent provenance sidecar. The overview PNG and empty prompt-log stub are intentional pre-orchestration placeholders. Its reusable placeholder code skips creation if a render marker or nonempty prompt log exists, and never overwrites an existing image. The final synchronous concept render is owned by the surrounding workflow, not by `build_analysis.py`.

## References and access safeguards
`retrieve_exact_references.py` retrieves only named foundational works or direct known arXiv identifiers; it does not perform a joint conformal/composition literature search, traverse citation networks, or look for the prohibited related study. `literature/` records actual consulted abstracts and publisher excerpts. The manuscript cites only the 26 retained entries in `references.bib`; `references_provenance.json` records access scope. Initial identifier and DOI mismatches returned unrelated bibliographic material, which was discarded rather than cited. No prohibited study was identified or used, and no citation-network traversal was performed. Abstract consultation supports only broad background descriptions, not unverified theorem details. The split-conformal rank argument is given directly in the text. The additional comparator-family citation was checked against Section 2.3 and Appendix A.1 Algorithms S1/S2 of the directly retrieved Fan and Sesia source; excerpts are retained at `literature/FanSesia2025.json`.

The initially supplied bibliography contained unrelated clinical/application hits and was not used as scientific support. Several exact-title retrievals returned wrong articles or reprint versions; these were rejected, corrected against original metadata, or replaced. A mistyped arXiv identifier returned an unrelated metabolic-network title/abstract, which was discarded. No prohibited study was identified, intentionally sought, or knowingly read, and no citation links were followed. The scientific records and claims were not altered to make validation pass.

## Build and validation
```sh
python .codex/skills/validate-paper/scripts/validate_tex_refs.py --tex paper.tex --bib references.bib
/tmp/paper-tools/bin/python .codex/skills/validate-paper/scripts/validate_figures.py --paper-dir .
python .codex/skills/write-paper-standalone/scripts/validate_claims.py \
  --paper-data paper_data.json --references references_provenance.json \
  --bib references.bib --claims claims_grounding.json --paper-dir .
bash .codex/skills/scientific-evidence/scripts/scientific_evidence.sh verify --root-dir .
bash .codex/skills/validate-paper/scripts/compile_latex.sh paper.tex
```

The manuscript uses the official ICLR 2026 style from `ICLR/Master-Template/iclr2026`, preserving the supplied format's 5.5-inch single-column text area, anonymous review block, and unchanged type geometry. Supplementary Information is embedded after the references, including the LLM-use disclosure. This workspace required private Poppler utilities for PDF extraction. Any environment-specific canonical compilation limitation and independent rendered-page checks are recorded in the validation report rather than concealed.
